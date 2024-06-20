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

import numpy as np
import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.common import common

COMPONENT_NAME = "woe_substitution"

FEATURE = "feature"
BINS = "bins"
RIGHT = "right"
WOE = "woe"
ELSE_BIN = "else_bin"


def run_woe_substitution(task_config: dict):
    logging.info("Running woe substitution...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 2, f"{COMPONENT_NAME} should have only 2 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1  output"
    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(inputs[0])

    features = inputs[0][common.SCHEMA][common.FEATURES]

    with open(inputs[1][common.DATA_PATH], "r") as rules_f:
        rules = json.load(rules_f)

    for rule in rules:
        if rule[FEATURE] in features:
            edges = [x[RIGHT] for x in rule[BINS]]
            woes = [x[WOE] for x in rule[BINS]]

            def func(x):
                if pd.isna(x):
                    return rule[ELSE_BIN][WOE]
                else:
                    index = np.searchsorted(edges, x, side="left")
                    return woes[min(index, len(woes) - 1)]

            df[rule[FEATURE]] = df[rule[FEATURE]].apply(func)

    # dump output
    logging.info("Dumping output...")
    df.to_csv(outputs[0][common.DATA_PATH], index=False)

    logging.info("Dumping output schema...")
    schema = data_pb2.TableSchema()
    common.append_table_schema(schema, inputs[0][common.SCHEMA])
    schema = common.gen_output_schema(df, schema)
    schema_json = json_format.MessageToJson(schema)
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
        run_woe_substitution(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 woe_substitution.py config`. Before launching the subprocess, the app framework will 
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
