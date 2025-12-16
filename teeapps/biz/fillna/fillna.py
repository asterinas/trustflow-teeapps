# Copyright 2024 Ant Group Co., Ltd.
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

import json
import logging
import sys
from collections import Counter

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as csv
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.common import common

COMPONENT_NAME = "fillna"
KEY = "col"
STRATEGY = "strategy"
ALLOWED_STRATEGY = ["constant", "max", "min", "mode", "median", "mean"]
ALLOWED_STRATEGY_FOR_STR = ["constant", "mode"]
CONSTANT_FLOAT = "constant_float"
CONSTANT_INT64 = "constant_int64"
CONSTANT_BOOL = "constant_bool"
CONSTANT_STR = "constant_str"


parse_options = csv.ParseOptions(
    delimiter=",",  # 指定分隔符，默认为逗号
    quote_char='"',  # 用于包围字符串的引号字符
)

convert_options = csv.ConvertOptions(
    strings_can_be_null=True,  # 允许字符串列中有 NULL 值
    null_values=["NA", "null", "N/A", ""],  # 指定 CSV 中的 NA 表示
)


def fillna_with_constant(
    input_file_path: str, output_file_path: str, col_name: str, constant_val
):
    with csv.open_csv(
        input_file_path,
        parse_options=parse_options,
        convert_options=convert_options,
    ) as reader:
        writer = None
        for batch in reader:
            data = batch.column(col_name)
            filled_data = pc.if_else(pc.is_null(data), constant_val, data)
            batch = batch.set_column(
                batch.schema.get_field_index(col_name),
                col_name,
                filled_data,
            )
            if writer is None:
                writer = csv.CSVWriter(output_file_path, batch.schema)

            writer.write_batch(batch)

        if writer is not None:
            writer.close()


def get_global_max_for_column(filename, column_name, chunk_size=1024 * 1024):
    reader = csv.open_csv(
        filename,
        read_options=csv.ReadOptions(block_size=chunk_size),
        parse_options=parse_options,
        convert_options=convert_options,
    )
    global_max = None

    for chunk in reader:
        df = chunk.to_pandas()
        if column_name in df.columns:
            chunk_max = df[column_name].max()
            if pd.notna(chunk_max) and (global_max is None or chunk_max > global_max):
                global_max = chunk_max

    return global_max


def get_global_min_for_column(filename, column_name, chunk_size=1024 * 1024):
    reader = csv.open_csv(
        filename,
        read_options=csv.ReadOptions(block_size=chunk_size),
        parse_options=parse_options,
        convert_options=convert_options,
    )
    global_min = None

    for chunk in reader:
        df = chunk.to_pandas()
        if column_name in df.columns:
            chunk_min = df[column_name].min()
            if pd.notna(chunk_min) and (global_min is None or chunk_min < global_min):
                global_min = chunk_min

    return global_min


# FIXME(junfeng): not suitable for large files.
# Replace with external sort.
def get_global_mode_for_column(filename, column_name, chunk_size=1024 * 1024):
    reader = csv.open_csv(
        filename,
        read_options=csv.ReadOptions(block_size=chunk_size),
        parse_options=parse_options,
        convert_options=convert_options,
    )
    value_counter = Counter()

    for chunk in reader:
        df = chunk.to_pandas()
        if column_name in df.columns:
            value_counter.update(df[column_name].dropna().values)

    if value_counter:
        global_mode = value_counter.most_common(1)[0][0]
    else:
        global_mode = None

    return global_mode


# FIXME(junfeng): not suitable for large files.
# Replace with external sort.
def get_global_median_for_column(filename, column_name, chunk_size=1024 * 1024):
    reader = csv.open_csv(
        filename,
        read_options=csv.ReadOptions(block_size=chunk_size),
        parse_options=parse_options,
        convert_options=convert_options,
    )
    values = []

    for chunk in reader:
        df = chunk.to_pandas()
        if column_name in df.columns:
            values.extend(df[column_name].dropna().tolist())

    if values:
        return np.median(values)
    else:
        return None


def get_global_mean_for_column(filename, column_name, chunk_size=1024 * 1024):
    reader = csv.open_csv(
        filename,
        read_options=csv.ReadOptions(block_size=chunk_size),
        parse_options=parse_options,
        convert_options=convert_options,
    )
    total_sum = 0.0
    total_count = 0

    for chunk in reader:
        df = chunk.to_pandas()
        if column_name in df.columns:
            non_null_values = df[column_name].dropna()
            total_sum += non_null_values.sum()
            total_count += non_null_values.count()

    if total_count > 0:
        return total_sum / total_count
    else:
        return None


def run_fillna(task_config: dict):
    logging.info("Running fillna...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1
    assert len(outputs) == 1
    assert len(inputs[0][KEY]) == 1

    col_name = inputs[0][KEY][0]
    col_type = common.get_col_types(inputs[0], [col_name])[0]
    strategy = task_config[STRATEGY]
    assert strategy in ALLOWED_STRATEGY

    input_file_path = inputs[0][common.DATA_PATH]
    output_file_path = outputs[0][common.DATA_PATH]

    if col_type == "str" and strategy not in ALLOWED_STRATEGY_FOR_STR:
        raise ValueError(
            f"strategy {strategy} is not allowed. At this moment, we only allow these stragey for str: {ALLOWED_STRATEGY_FOR_STR}."
        )

    if strategy == "constant":
        if col_type == "float":
            constant_val = task_config[CONSTANT_FLOAT]
        elif col_type == "int64":
            constant_val = task_config[CONSTANT_INT64]
        elif col_type == "bool":
            constant_val = task_config[CONSTANT_BOOL]
        elif col_type == "str":
            constant_val = task_config[CONSTANT_STR]
        else:
            raise RuntimeError(f"unexpected col type: {col_type}.")

        global_const = constant_val

    elif strategy == "max":
        global_const = get_global_max_for_column(input_file_path, col_name)

    elif strategy == "min":
        global_const = get_global_min_for_column(input_file_path, col_name)

    elif strategy == "mode":
        global_const = get_global_mode_for_column(input_file_path, col_name)

    elif strategy == "median":
        global_const = get_global_median_for_column(input_file_path, col_name)

    elif strategy == "mean":
        global_const = get_global_mean_for_column(input_file_path, col_name)

    else:
        raise ValueError(f"unexpected strategy: {strategy}.")

    if global_const is None:
        raise RuntimeError(
            f"global_const is none, please check the data of col {col_name}."
        )

    fillna_with_constant(
        input_file_path,
        output_file_path,
        col_name,
        global_const,
    )

    # gen output TableSchema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, inputs[0][common.SCHEMA])

    if strategy == "mean":
        for i in range(len(output_schema.ids)):
            if output_schema.ids[i] == col_name:
                output_schema.id_types[i] = "float64"

        for i in range(len(output_schema.features)):
            if output_schema.features[i] == col_name:
                output_schema.feature_types[i] = "float64"

        for i in range(len(output_schema.labels)):
            if output_schema.labels[i] == col_name:
                output_schema.label_types[i] = "float64"

    schema_json = json_format.MessageToJson(output_schema)
    with open(outputs[0][common.DATA_SCHEMA_PATH], "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_fillna(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
