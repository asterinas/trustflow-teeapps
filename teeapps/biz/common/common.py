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


import csv
import logging
from typing import Literal

import pandas
from secretflow.spec.v1 import data_pb2

COMPONENT_NAME = "component_name"
INPUTS = "inputs"
OUTPUTS = "outputs"
DATA_PATH = "data_path"
DATA_SCHEMA_PATH = "data_schema_path"
SCHEMA = "schema"
IDS = "ids"
FEATURES = "features"
LABELS = "labels"
ID_TYPES = "id_types"
FEATURE_TYPES = "feature_types"
LABEL_TYPES = "label_types"

TABLE_SCHEMA_STRING_TYPE = "str"
TABLE_SCHEMA_FLOAT_DEFAULT_TYPE = "float64"
TABLE_SCHEMA_BOOL_TYPE = "bool"
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
    elif sf_type == TABLE_SCHEMA_BOOL_TYPE:
        return "bool"
    return "object"


def pd_type_to_sf(pd_dtype: str) -> str:
    if pd_dtype == "object":
        return "str"
    else:
        return pd_dtype


def append_table_schema(dst_schema: data_pb2.TableSchema, src_schema: dict) -> None:
    dst_schema.ids.extend(src_schema[IDS])
    dst_schema.features.extend(src_schema[FEATURES])
    dst_schema.labels.extend(src_schema[LABELS])
    dst_schema.id_types.extend(src_schema[ID_TYPES])
    dst_schema.feature_types.extend(src_schema[FEATURE_TYPES])
    dst_schema.label_types.extend(src_schema[LABEL_TYPES])


def get_cols_in_schema(schema: dict) -> list:
    cols = []
    cols.extend(list(schema[IDS]))
    cols.extend(list(schema[FEATURES]))
    cols.extend(list(schema[LABELS]))
    return cols


def get_dialect(csv_file):
    with open(csv_file, "r", newline="") as file:
        sample = file.readline() + file.readline()
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            logging.warn(
                "Can not determine dialect with csv sniffer. Use default excel dialect instead."
            )
            dialect = csv.excel()
    return dialect


def get_col_names(task_input: dict, delimiter: str, file_path: str = None) -> list:
    data_path = file_path if file_path else task_input[DATA_PATH]
    assert data_path, "Data path is empty."

    df = pandas.read_csv(data_path, delimiter=delimiter, nrows=0)
    return df.columns.to_list()


def get_col_types(task_input: dict, col_names: list) -> list:
    col_types = []
    for col_name in col_names:
        if col_name in task_input[SCHEMA][IDS]:
            col_types.append(
                task_input[SCHEMA][ID_TYPES][
                    list(task_input[SCHEMA][IDS]).index(col_name)
                ]
            )
        elif col_name in task_input[SCHEMA][FEATURES]:
            col_types.append(
                task_input[SCHEMA][FEATURE_TYPES][
                    list(task_input[SCHEMA][FEATURES]).index(col_name)
                ]
            )
        elif col_name in task_input[SCHEMA][LABELS]:
            col_types.append(
                task_input[SCHEMA][LABEL_TYPES][
                    list(task_input[SCHEMA][LABELS]).index(col_name)
                ]
            )
        else:
            raise RuntimeError(f"{col_name} not found in schema")
    return col_types


# only used by format_file_schema
def col_type_to_float(task_input: dict, col_name: str) -> None:
    if col_name in task_input[SCHEMA][IDS]:
        task_input[SCHEMA][ID_TYPES][
            list(task_input[SCHEMA][IDS]).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    elif col_name in task_input[SCHEMA][FEATURES]:
        task_input[SCHEMA][FEATURE_TYPES][
            list(task_input[SCHEMA][FEATURES]).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    elif col_name in task_input[SCHEMA][LABELS]:
        task_input[SCHEMA][LABEL_TYPES][
            list(task_input[SCHEMA][LABELS]).index(col_name)
        ] = TABLE_SCHEMA_FLOAT_DEFAULT_TYPE
    else:
        raise RuntimeError(f"{col_name} not found in schema")


def gen_data_frame(
    task_input: dict,
    file_path: str = None,
    usecols: list = None,
) -> pandas.DataFrame:
    data_path = file_path if file_path else task_input[DATA_PATH]
    assert data_path, "Data path is empty."

    dialect = get_dialect(data_path)

    col_names = get_col_names(task_input, dialect.delimiter, data_path)
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
        delimiter=dialect.delimiter,
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
            raise RuntimeError(f"{col} not found in schema")
    return output_schema


def split_bigfile_into_smallfiles(
    task_input: dict,
    join_key: list,
    file_num: int,
) -> list:
    data_path = task_input[DATA_PATH]
    assert data_path, "Data path is empty."
    if file_num == 1:
        return [data_path]

    # split big file into small files
    file_names = [data_path + "_" + str(index) for index in range(file_num)]
    file_handles = [open(filename, "w") for filename in file_names]

    dialect = get_dialect(data_path)

    col_names = get_col_names(task_input, dialect.delimiter, data_path)
    join_key_idx = [i for i in range(len(col_names)) if col_names[i] in join_key]

    # write header to every small files
    header = dialect.lineterminator.join(col_names) + dialect.lineterminator
    [handle.write(header) for handle in file_handles]

    with open(data_path, "r", newline="") as csv_file:
        reader = csv.reader(
            csv_file, delimiter=dialect.delimiter, lineterminator=dialect.lineterminator
        )
        # skip header
        next(reader)
        for row in reader:
            file_index = (
                hash(dialect.lineterminator.join([row[idx] for idx in join_key_idx]))
                % file_num
            )
            file_handles[file_index].write(
                dialect.lineterminator.join(row) + dialect.lineterminator
            )

    [handle.close() for handle in file_handles]
    return file_names
