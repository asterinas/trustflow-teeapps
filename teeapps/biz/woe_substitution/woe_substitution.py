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

import numpy as np
import pandas as pd
from google.protobuf import json_format

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import woe_binning_pb2
from secretflow.spec.v1 import data_pb2


def run_woe_substitution(config_json: str):
    logging.info("Running woe substitution...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_WOE_SUBSTITUTION"
    ), "App type is not 'OP_WOE_SUBSTITUTION'"
    assert len(task_config.inputs) == 2, "WOE substitution should has only 2 input"
    assert len(task_config.outputs) == 1, "WOE substitution should has only 1  output"
    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(task_config.inputs[0])

    features = task_config.inputs[0].schema.features[:]
    rules = woe_binning_pb2.WoeBinningRule()
    with open(task_config.inputs[1].data_path, "r") as rules_f:
        rules_json = rules_f.read()

    json_format.Parse(rules_json, rules)

    for rule in rules.rules:
        if rule.feature in features:
            edges = [x.right for x in rule.bins]
            woes = [x.woe for x in rule.bins]

            def func(x):
                if pd.isna(x):
                    return rule.else_bin.woe
                else:
                    index = np.searchsorted(edges, x, side="left")
                    return woes[min(index, len(woes) - 1)]

            df[rule.feature] = df[rule.feature].apply(func)

    # dump output
    logging.info("Dumping output...")
    df.to_csv(task_config.outputs[0].data_path, index=False)

    logging.info("Dumping output schema...")
    schema = data_pb2.TableSchema()
    schema.CopyFrom(task_config.inputs[0].schema)
    schema = common.gen_output_schema(df, schema)
    schema_json = json_format.MessageToJson(schema)
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
        run_woe_substitution(config_json)


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
