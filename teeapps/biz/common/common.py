# Copyright 2023 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import math
import os
import sys
from typing import Literal

import pandas

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from secretflow.spec.v1 import data_pb2

DEFAULT_FILE_SIZE_LIMIT_IN_BYTES = 1024 * 1000 * 500
TABLE_SCHEMA_STRING_TYPE = "str"
TABLE_SCHEMA_FLOAT_DEFAULT_TYPE = "float64"
TABLE_SCHEMA_FLOAT_TYPE_LIST = ["float16", "float32", "float64", "float"]
TABLE_SCHEMA_INT_TYPE_LIST = [
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "int",
]


def is_str_numberic(s: str) -> bool:
    try:
        val = float(s)
    except:
        return False
    return True


def sf_to_pd_type(
    sf_type: Literal[
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "float16",
        "float32",
        "float64",
        "bool",
        "int",
        "float",
        "str",
    ]
) -> Literal["float64", "int64", "bool", "object"]:
    if sf_type in TABLE_SCHEMA_INT_TYPE_LIST:
        return "int64"
    elif sf_type in TABLE_SCHEMA_FLOAT_TYPE_LIST:
        return "float64"
    elif sf_type in ["bool"]:
        return "bool"
    return "object"


def pd_type_to_sf(pd_dtype: str) -> str:
    if pd_dtype == "object":
        return "str"
    else:
        return pd_dtype


def append_table_schema(
    schema: data_pb2.TableSchema, task_input: task_pb2.TaskConfig.Input
) -> None:
    schema.ids.extend(task_input.schema.ids)
    schema.features.extend(task_input.schema.features)
    schema.labels.extend(task_input.schema.labels)
    schema.id_types.extend(task_input.schema.id_types)
    schema.feature_types.extend(task_input.schema.feature_types)
    schema.label_types.extend(task_input.schema.label_types)


def get_cols_in_schema(schema: data_pb2.TableSchema) -> list:
    cols = []
    cols.extend(list(schema.ids))
    cols.extend(list(schema.features))
    cols.extend(list(schema.labels))
    return cols


def get_col_names(task_input: task_pb2.TaskConfig.Input, file_path: str = None) -> list:
    data_path = file_path if file_path is not None else task_input.data_path
    with open(data_path, "r") as reader:
        line = reader.readline()
        return line.strip("\n ").split(",")


def get_col_types(task_input: task_pb2.TaskConfig.Input, col_names: list) -> list:
    col_types = []
    for col_name in col_names:
        if col_name in task_input.schema.ids:
            col_types.append(
                task_input.schema.id_types[list(task_input.schema.ids).index(col_name)]
            )
        elif col_name in task_input.schema.features:
            col_types.append(
                task_input.schema.feature_types[
                    list(task_input.schema.features).index(col_name)
                ]
            )
        elif col_name in task_input.schema.labels:
            col_types.append(
                task_input.schema.label_types[
                    list(task_input.schema.labels).index(col_name)
                ]
            )
        else:
            raise Exception(f"{col_name} not found in schema")
    return col_types


# only used by format_file_schema
def col_type_to_float(task_input: task_pb2.TaskConfig.Input, col_name: str) -> None:
    if col_name in task_input.schema.ids:
        task_input.schema.id_types[
            list(task_input.schema.ids).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    elif col_name in task_input.schema.features:
        task_input.schema.feature_types[
            list(task_input.schema.features).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    elif col_name in task_input.schema.labels:
        task_input.schema.label_types[
            list(task_input.schema.labels).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    else:
        raise Exception(f"{col_name} not found in schema")


def gen_data_frame(
    task_input: task_pb2.TaskConfig.Input,
    file_path: str = None,
    usecols: list = None,
) -> pandas.DataFrame:
    data_path = file_path if file_path is not None else task_input.data_path

    col_names = get_col_names(task_input, data_path)
    col_types = get_col_types(task_input, col_names)
    return pandas.read_csv(
        data_path,
        names=col_names,
        dtype={
            col_name: sf_to_pd_type(col_type)
            for col_name, col_type in zip(col_names, col_types)
        },
        usecols=usecols,
        header=0,
    )


def gen_output_schema(
    df: pandas.DataFrame, schema: data_pb2.TableSchema
) -> data_pb2.TableSchema:
    output_schema = data_pb2.TableSchema()

    for col in df.columns:
        if col in schema.ids:
            output_schema.ids.append(col)
            output_schema.id_types.append(pd_type_to_sf(str(df[col].dtype)))
        elif col in schema.features:
            output_schema.features.append(col)
            output_schema.feature_types.append(pd_type_to_sf(str(df[col].dtype)))
        elif col in schema.labels:
            output_schema.labels.append(col)
            output_schema.label_types.append(pd_type_to_sf(str(df[col].dtype)))
        else:
            raise Exception(f"{col} not found in schema")
    return output_schema


# only fix problem: change str to float if possible
def format_file_schema(task_input: task_pb2.TaskConfig.Input, join_key: list) -> int:
    logging.debug(f"before format_file_schema task input {task_input}")
    data_path = task_input.data_path
    col_names = get_col_names(task_input)
    col_types = get_col_types(task_input, col_names)

    join_fields_size = 0

    can_format_str_to_float = [True for col_name in col_names]
    with open(data_path, "r") as reader:
        # line 1 is col name
        reader.readline()
        while True:
            # judge whether the str represents float
            line = reader.readline()
            if not line:
                break
            values = line.strip("\n ").split(",")
            for index in range(len(values)):
                # if col type is str and actual value is not float,
                # then the col cannot be transfer to float
                if (
                    can_format_str_to_float[index]
                    and col_types[index] == TABLE_SCHEMA_STRING_TYPE
                    and is_str_numberic(values[index]) != True
                ):
                    can_format_str_to_float[index] = False
                if col_names[index] in join_key:
                    join_fields_size = join_fields_size + len(values[index])

    # change origin col type
    for index in range(len(col_names)):
        if (
            can_format_str_to_float[index]
            and col_types[index] == TABLE_SCHEMA_STRING_TYPE
        ):
            # change schema in task_input
            col_type_to_float(task_input, col_names[index])
    logging.debug(f"after format_file_schema task input {task_input}")
    return join_fields_size


def split_bigfile_into_smallfiles(
    task_input: task_pb2.TaskConfig.Input,
    join_key: list,
    file_size_limit_in_bytes: int = None,
    total_file_size_in_bytes: int = None,
) -> list:
    data_path = task_input.data_path
    # calcute small file num
    file_size_limit_in_bytes = (
        DEFAULT_FILE_SIZE_LIMIT_IN_BYTES
        if file_size_limit_in_bytes is None
        else file_size_limit_in_bytes
    )
    file_num = math.ceil(
        (
            os.path.getsize(data_path)
            if total_file_size_in_bytes is None
            else total_file_size_in_bytes
        )
        / file_size_limit_in_bytes
    )
    logging.info(f"{data_path} can be split into {file_num} files")
    if file_num == 1:
        return [data_path]

    # split big file into small files
    file_names = [data_path + "_" + str(index) for index in range(file_num)]
    file_handles = [open(filename, "w") for filename in file_names]
    with open(data_path, "r") as reader:
        # line 1 is col name
        line = reader.readline()
        col_names = line.strip("\n ").split(",")
        col_types = get_col_types(task_input, col_names)
        # write col name into small files
        [handle.write(line) for handle in file_handles]
        while True:
            line = reader.readline()
            if not line:
                break
            values = line.strip("\n ").split(",")
            format_values = []
            for index in range(len(values)):
                if col_names[index] not in join_key:
                    continue
                if col_types[index] in TABLE_SCHEMA_FLOAT_TYPE_LIST:
                    format_values.append(str(float(values[index])))
                else:
                    format_values.append(str(values[index]))
            file_index = hash(",".join(format_values)) % file_num
            file_handles[file_index].write(line)

    [handle.close() for handle in file_handles]
    return file_names


def read_csv_file(
    task_input: task_pb2.TaskConfig.Input,
    join_key: list,
    data_path: str,
    cond_df: pandas.DataFrame,
) -> pandas.DataFrame:
    join_key_index = {join_key[index]: index for index in range(len(join_key))}

    # the order of conf_df.columns is the same as the order of id_fields
    cond_list = cond_df.values

    # only get data in file which value of id fields is in cond_df[id fields]
    data_rows = []
    with open(data_path, "r") as reader:
        # line 1 is col name
        line = reader.readline()
        col_names = line.strip("\n ").split(",")
        col_types = get_col_types(task_input, col_names)
        while True:
            # get value line by line
            line = reader.readline()
            if not line:
                break
            values = line.strip("\n ").split(",")
            cond_values = [None] * len(join_key)
            format_values = []

            for index in range(len(values)):
                if col_types[index] in TABLE_SCHEMA_FLOAT_TYPE_LIST:
                    format_values.append(float(values[index]))
                elif col_types[index] in TABLE_SCHEMA_INT_TYPE_LIST:
                    format_values.append(int(values[index]))
                else:
                    format_values.append(values[index])
                if col_names[index] in join_key:
                    cond_values[join_key_index[col_names[index]]] = format_values[-1]
            if cond_values in cond_list:
                data_rows.append(format_values)

    return pandas.DataFrame(data_rows, columns=col_names)
