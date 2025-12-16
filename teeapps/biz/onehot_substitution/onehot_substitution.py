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

COMPONENT_NAME = "onehot_substitution"
CHUNK_SIZE = 1024 * 1024


def run_onehot_substitution(task_config: dict):
    logging.info("Running woe substitution...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 2, f"{COMPONENT_NAME} should have only 2 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    with open(inputs[1][common.DATA_PATH], "r") as rules_f:
        rules = json.load(rules_f)

    with open(outputs[0][common.DATA_PATH], "w") as output_file:
        first_chunk = True

        for chunk in pd.read_csv(inputs[0][common.DATA_PATH], chunksize=CHUNK_SIZE):
            for col, rule in rules.items():
                one_hot = pd.get_dummies(chunk[col], prefix=col)
                for category in rule:
                    if f"{col}_{category}" not in one_hot.columns:
                        one_hot[f"{col}_{category}"] = False

                chunk = chunk.drop(col, axis=1)
                chunk = pd.concat([chunk, one_hot], axis=1)

            if first_chunk:
                chunk.to_csv(output_file, index=False, header=True)
                first_chunk = False
            else:
                chunk.to_csv(output_file, index=False, header=False)

    output_schema = data_pb2.TableSchema()
    input_schema = inputs[0][common.SCHEMA]

    for id, id_type in zip(input_schema["ids"], input_schema["id_types"]):
        if id in rules.keys():
            for x in rules[id]:
                output_schema.ids.append(f"{id}_{x}")
                output_schema.id_types.append("bool")
        else:
            output_schema.ids.append(id)
            output_schema.id_types.append(id_type)

    for feature, feature_type in zip(
        input_schema["features"], input_schema["feature_types"]
    ):
        if feature in rules.keys():
            for x in rules[feature]:
                output_schema.features.append(f"{feature}_{x}")
                output_schema.feature_types.append("bool")
        else:
            output_schema.features.append(feature)
            output_schema.feature_types.append(feature_type)

    for label, label_type in zip(input_schema["labels"], input_schema["label_types"]):
        if label in rules.keys():
            for x in rules[label]:
                output_schema.labels.append(f"{label}_{x}")
                output_schema.label_types.append("bool")
        else:
            output_schema.labels.append(label)
            output_schema.label_types.append(label_type)

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
        run_onehot_substitution(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
