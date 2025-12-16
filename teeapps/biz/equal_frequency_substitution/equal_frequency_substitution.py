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

import numpy as np
import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.common import common

CHUNK_SIZE = 1024 * 1024
COMPONENT_NAME = "equal_frequency_substitution"


def run_equal_frequency_substitution(task_config: dict):
    logging.info("Running equal frequency substitution...")

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 2, f"{COMPONENT_NAME} should have only 2 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1  output"

    with open(inputs[1][common.DATA_PATH], "r") as rules_f:
        rules = json.load(rules_f)

    bin_edges = {}
    for k, v in rules["edges"].items():
        bin_edges[k] = np.array(v)

    first_chunk = True
    for chunk in pd.read_csv(
        inputs[0][common.DATA_PATH],
        chunksize=CHUNK_SIZE,
    ):
        for k, v in bin_edges.items():
            chunk[k] = pd.cut(
                chunk[k],
                bins=v,
                labels=False,
                include_lowest=True,
            )

        if first_chunk:
            chunk.to_csv(
                outputs[0][common.DATA_PATH],
                index=False,
                mode="w",
                header=True,
            )
            first_chunk = False
        else:
            chunk.to_csv(
                outputs[0][common.DATA_PATH],
                index=False,
                mode="a",
                header=False,
            )

    # gen output TableSchema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, inputs[0][common.SCHEMA])

    for i in range(len(output_schema.features)):
        if output_schema.features[i] in bin_edges:
            output_schema.feature_types[i] = "int"

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
        run_equal_frequency_substitution(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
