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
import sys

from google.protobuf import json_format
from sklearn.model_selection import train_test_split

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import dataset_split_pb2


def run_dataset_split(config_json: str):
    logging.info("Running dataset split...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_DATASET_SPLIT"
    ), "App type is not 'OP_DATASET_SPLIT'"
    assert len(task_config.inputs) == 1, "Dataset split should has only 1 input"
    assert len(task_config.outputs) == 2, "Dataset split should has only 2 output"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(task_config.inputs[0])
    params = dataset_split_pb2.DatasetSplitParams()
    task_config.params.Unpack(params)

    train_set_count = int(df.shape[0] * params.training_data_ratio)
    assert train_set_count >= 1, "Train set count should more than 1"

    random_state = None
    if params.should_fix_random:
        random_state = params.random_state
    dataset_train, dataset_test = train_test_split(
        df,
        train_size=params.training_data_ratio,
        random_state=random_state,
        shuffle=params.shuffle,
    )
    # dump output
    logging.info("Dumping output data...")
    train_output_path = task_config.outputs[0].data_path
    test_output_path = task_config.outputs[1].data_path
    dataset_train.to_csv(train_output_path, index=False)
    dataset_test.to_csv(test_output_path, index=False)
    # dump output schema
    schema = task_config.inputs[0].schema
    schema = common.gen_output_schema(dataset_train, schema)
    schema_json = json_format.MessageToJson(schema)
    # two dataset is the same schema
    with open(task_config.outputs[0].data_schema_path, "w") as schema_f:
        schema_f.write(schema_json)
    with open(task_config.outputs[1].data_schema_path, "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_dataset_split(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 dataset_split.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
