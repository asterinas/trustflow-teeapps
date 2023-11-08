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

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import dataset_filter_pb2
from secretflow.spec.v1 import data_pb2


def drop_features_in_schema(schema: data_pb2.TableSchema, drop_features: list) -> None:
    for drop_feature in drop_features:
        if drop_feature in schema.features:
            index = list(schema.features).index(drop_feature)
            del schema.features[index]
            del schema.feature_types[index]


def run_dataset_filter(config_json: str) -> None:
    logging.info("Running dataset_filter...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_DATASET_FILTER"
    ), "App type is not 'OP_DATASET_FILTER'"
    assert len(task_config.inputs) == 1, "Dataset filter should has only 1 input"
    assert len(task_config.outputs) == 1, "Dataset filter should has only 1 output"

    params = dataset_filter_pb2.DatasetFilterParams()
    task_config.params.Unpack(params)

    task_input = task_config.inputs[0]
    output_schema = data_pb2.TableSchema()
    output_schema.CopyFrom(task_input.schema)
    drop_features_in_schema(output_schema, drop_features=list(params.drop_features))

    df = common.gen_data_frame(
        task_input=task_input, usecols=common.get_cols_in_schema(output_schema)
    )
    df.to_csv(task_config.outputs[0].data_path, index=False)

    logging.info("Dumping output schema...")
    output_schema = common.gen_output_schema(df, output_schema)
    schema_json = json_format.MessageToJson(output_schema)
    with open(task_config.outputs[0].data_schema_path, "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_dataset_filter(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 dataset_filter.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
