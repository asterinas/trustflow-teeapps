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

import joblib
import lightgbm as lgb
import pandas

from teeapps.biz.common import common

COMPONENT_NAME = "lgbm_train"

IDS = "ids"
LABEL = "label"

N_ESTIMATORS = "n_estimators"
OBJECTIVE = "objective"
BOOSTING_TYPE = "boosting_type"
LEARNING_RATE = "learning_rate"
NUM_LEAVES = "num_leaves"

REGRESSION = "regression"
BINARY = "binary"


def run_lgbm(task_config: dict):
    logging.info("Running lgbm training...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # get train data
    logging.info("Loading training data...")
    df = common.gen_data_frame(inputs[0])

    # labels in schema can be multiple, but eval target label is unique(in params)
    ids = inputs[0][IDS]
    labels = inputs[0][LABEL]
    assert len(labels) == 1, f"{COMPONENT_NAME} should have only 1 labels column"

    features = inputs[0][common.SCHEMA][common.FEATURES]
    features = [feature for feature in features if feature not in ids + labels]

    X = df[features]
    Y = pandas.to_numeric(df[labels[0]], errors="coerce")

    param = {
        N_ESTIMATORS: task_config[N_ESTIMATORS],
        OBJECTIVE: task_config[OBJECTIVE],
        BOOSTING_TYPE: task_config[BOOSTING_TYPE],
        LEARNING_RATE: task_config[LEARNING_RATE],
        NUM_LEAVES: task_config[NUM_LEAVES],
    }

    if param[OBJECTIVE] == REGRESSION:
        model = lgb.LGBMRegressor(**param)
    elif param[OBJECTIVE] == BINARY:
        model = lgb.LGBMClassifier(**param)
    else:
        raise RuntimeError(f"unsupported objective function: {param[OBJECTIVE]}")

    # train model
    model.fit(X, Y)

    logging.info("Setting origin feature_name in model...")
    model.origin_feature_name_ = features

    # dump model
    logging.info("Dumping model...")
    model_data_path = outputs[0][common.DATA_PATH]
    joblib.dump(model, model_data_path)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_lgbm(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 lgbm.py config`. Before launching the subprocess, the app framework will 
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
