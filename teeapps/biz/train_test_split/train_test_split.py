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


import json
import logging
import sys

from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from sklearn.model_selection import train_test_split
from teeapps.biz.common import common

COMPONENT_NAME = "train_test_split"

TRAIN_SIZE = "train_size"
FIX_RANDOM = "fix_random"
RANDOM_STATE = "random_state"
SHUFFLE = "shuffle"


def run_train_test_split(task_config: dict):
    logging.info("Running train test split...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 2, f"{COMPONENT_NAME} should have only 2 output"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(inputs[0])

    train_set_count = int(df.shape[0] * task_config[TRAIN_SIZE])
    assert (
        train_set_count >= 1
    ), f"Train set count should be greater than or equal to 1, but got {train_set_count}"

    dataset_train, dataset_test = train_test_split(
        df,
        train_size=task_config[TRAIN_SIZE],
        random_state=task_config[RANDOM_STATE] if task_config[RANDOM_STATE] else None,
        shuffle=task_config[SHUFFLE],
    )
    # dump output
    logging.info("Dumping output data...")
    train_output_path = outputs[0][common.DATA_PATH]
    test_output_path = outputs[1][common.DATA_PATH]
    dataset_train.to_csv(train_output_path, index=False)
    dataset_test.to_csv(test_output_path, index=False)
    # dump output schema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, inputs[0][common.SCHEMA])
    output_schema = common.gen_output_schema(dataset_train, output_schema)
    schema_json = json_format.MessageToJson(output_schema)
    # two dataset is the same schema
    with open(outputs[0][common.DATA_SCHEMA_PATH], "w") as schema_f:
        schema_f.write(schema_json)
    with open(outputs[1][common.DATA_SCHEMA_PATH], "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_train_test_split(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 train_test_split.py config`. Before launching the subprocess, the app framework will 
firstly generate a config file which is a json file containing all the required 
parameters and is serialized from the task.proto. Currently we do not handle any 
errors/exceptions in this file as the outer app framework will capture the stderr 
and stdout.
"""
if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
