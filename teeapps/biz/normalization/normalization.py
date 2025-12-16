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

import pandas as pd
import pyarrow as pa
import pyarrow.csv as csv
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from sklearn.preprocessing import MaxAbsScaler, MinMaxScaler, StandardScaler
from teeapps.biz.common import common

COMPONENT_NAME = "normalization"
STRATEGY = "strategies"
ALLOWED_STRATEGY_LIST = ["standard", "max_abs", "min_max"]
DISALLOWED_COL_TYPES = ["bool", "str"]
KEY = "cols"


def run_normalization(task_config: dict):
    logging.info("Running normalization...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1
    assert len(outputs) == 1
    assert len(inputs[0][KEY]) >= 1

    col_names = inputs[0][KEY]
    col_types = common.get_col_types(inputs[0], col_names)

    for col_name, col_type in zip(col_names, col_types):
        if col_type in DISALLOWED_COL_TYPES:
            raise ValueError(
                f"type of {col_name} is {col_type}, which is not allowed since it is one of {DISALLOWED_COL_TYPES}."
            )

    strategies = task_config[STRATEGY]
    if len(strategies) != 1 and len(strategies) != len(col_names):
        raise ValueError(
            f"number of {STRATEGY} is not correct since it should be one or match the cnt of {KEY}."
        )

    for s in strategies:
        if s not in ALLOWED_STRATEGY_LIST:
            raise ValueError(
                f"strategy {s} is not allowed, it must be one of {ALLOWED_STRATEGY_LIST}."
            )

    input_file_path = inputs[0][common.DATA_PATH]
    output_file_path = outputs[0][common.DATA_PATH]

    if len(strategies) == 1:
        strategies = strategies * len(col_names)

    scalers = []

    for s in strategies:
        if s == "standard":
            scalers.append(StandardScaler())
        elif s == "max_abs":
            scalers.append(MaxAbsScaler())
        elif s == "min_max":
            scalers.append(MinMaxScaler())
        else:
            raise RuntimeError(f"unknown strategy: {s}.")

    with csv.open_csv(input_file_path) as reader:
        for chunk in reader:
            df_chunk = chunk.to_pandas()

            for col_name, scaler in zip(col_names, scalers):
                scaler.partial_fit(df_chunk[[col_name]])

    with csv.open_csv(input_file_path) as reader:
        sink = None
        for chunk in reader:

            df_chunk = chunk.to_pandas()

            for col_name, scaler in zip(col_names, scalers):
                df_chunk[[col_name]] = scaler.transform(df_chunk[[col_name]])

            table = pa.Table.from_pandas(df_chunk)

            if sink is None:
                options = csv.WriteOptions(include_header=True)
                sink = sink = pa.OSFile(output_file_path, "wb")
            else:
                options = csv.WriteOptions(include_header=False)

            csv.write_csv(table, sink, write_options=options)
        if sink is not None:
            sink.close()

    # gen output TableSchema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, inputs[0][common.SCHEMA])

    # modify types.
    for i in range(len(output_schema.ids)):
        if output_schema.ids[i] in col_names:
            output_schema.id_types[i] = "float64"

    for i in range(len(output_schema.features)):
        if output_schema.features[i] in col_names:
            output_schema.feature_types[i] = "float64"

    for i in range(len(output_schema.labels)):
        if output_schema.labels[i] in col_names:
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
        run_normalization(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
