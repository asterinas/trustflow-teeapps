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
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2

from teeapps.biz.common import common

COMPONENT_NAME = "union"


def run_union(task_config: dict) -> None:
    logging.info("Running union...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]
    assert 1 < len(inputs) <= 10, f"{COMPONENT_NAME} should have [2,10] inputs"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # Sanity-check if schemas are the same.
    first_schema = inputs[0][common.SCHEMA]

    for i in range(1, len(inputs)):
        if inputs[i][common.SCHEMA] != first_schema:
            raise RuntimeError(
                f"Schema are not the same. \nThe first schema is {first_schema}. \n The schema of INPUT {i} is {inputs[i][common.SCHEMA]}."
            )

    # write file
    logging.info("Dumping output dataframe...")
    output_path = outputs[0][common.DATA_PATH]
    with open(output_path, "w", newline="") as outfile:
        first_file = True
        for file in inputs:
            for chunk in pd.read_csv(file[common.DATA_PATH], chunksize=10000):
                chunk.to_csv(outfile, header=first_file, index=False)
                first_file = False

    logging.info("Dumping output schema...")
    # gen output TableSchema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, first_schema)
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
        run_union(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
