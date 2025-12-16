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
import math
import sys

import pandas as pd
from teeapps.biz.common import common

COMPONENT_NAME = "onehot_encode"
COLS = "cols"

CHUNK_SIZE = 1024 * 1024


def run_onehot_encode(task_config: dict):
    logging.info("Running one hot encode...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input."
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output."
    cols = inputs[0][COLS]
    assert len(cols) > 0, "selected cols should not be empty."

    rule = {}
    for c in cols:
        rule[c] = set()

    for chunk in pd.read_csv(inputs[0][common.DATA_PATH], chunksize=CHUNK_SIZE):
        for c in cols:
            rule[c].update(chunk[c].unique())

    def custom_sort(val):
        # 判断是否为 NaN
        if isinstance(val, float) and math.isnan(val):
            return (1, "")  # 将 NaN 放在最后
        else:
            return (0, val)  # 正常字符串排序

    for c in cols:
        rule[c] = list(sorted(rule[c], key=custom_sort))

    with open(outputs[0][common.DATA_PATH], "w") as rule_f:
        json.dump(rule, rule_f)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_onehot_encode(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
