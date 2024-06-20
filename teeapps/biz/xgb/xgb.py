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

import joblib
import pandas
import xgboost as xgb

from teeapps.biz.common import common

COMPONENT_NAME = "xgb_train"
IDS = "ids"
LABEL = "label"

NUM_BOOST_ROUND = "num_boost_round"
MAX_DEPTH = "max_depth"
MAX_LEAVES = "max_leaves"
SEED = "seed"
LEARNING_RATE = "learning_rate"
LAMBDA = "lambda"
GAMMA = "gamma"
COLSAMPLE_BYTREE = "colsample_bytree"
BASE_SCORE = "base_score"
MIN_CHILD_WEIGHT = "min_child_weight"
OBJECTIVE = "objective"
ALPHA = "alpha"
SUBSAMPLE = "subsample"
MAX_BIN = "max_bin"
TREE_METHOD = "tree_method"
BOOSTER = "booster"

REG_SQUAREDERROR = "reg:squarederror"
BINARY_LOGISTIC = "binary:logistic"

REG_LAMBDA = "reg_lambda"
REG_ALPHA = "reg_alpha"
N_ESTIMATORS = "n_estimators"
RANDOM_STATE = "random_state"


def get_model_param(task_config: dict, param_keys: list) -> dict:
    param = dict()
    for key in param_keys:
        if key == LAMBDA:
            param[REG_LAMBDA] = task_config[key]
        elif key == ALPHA:
            param[REG_ALPHA] = task_config[key]
        elif key == NUM_BOOST_ROUND:
            param[N_ESTIMATORS] = task_config[key]
        elif key == SEED:
            param[RANDOM_STATE] = task_config[key]
        else:
            param[key] = task_config[key]
    logging.info(f"Model params {param}")
    return param


def run_xgb(task_config: dict):
    logging.info("Running xgb training...")

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

    logging.info("Parsing xgb parameters...")

    param = {
        N_ESTIMATORS: task_config[NUM_BOOST_ROUND],
        MAX_DEPTH: task_config[MAX_DEPTH],
        MAX_LEAVES: task_config[MAX_LEAVES],
        RANDOM_STATE: task_config[SEED],
        LEARNING_RATE: task_config[LEARNING_RATE],
        REG_LAMBDA: task_config[LAMBDA],
        GAMMA: task_config[GAMMA],
        COLSAMPLE_BYTREE: task_config[COLSAMPLE_BYTREE],
        BASE_SCORE: task_config[BASE_SCORE],
        MIN_CHILD_WEIGHT: task_config[MIN_CHILD_WEIGHT],
        REG_ALPHA: task_config[ALPHA],
        SUBSAMPLE: task_config[SUBSAMPLE],
        MAX_BIN: task_config[MAX_BIN],
        TREE_METHOD: task_config[TREE_METHOD],
        BOOSTER: task_config[BOOSTER],
    }

    target = task_config[OBJECTIVE]
    if target == REG_SQUAREDERROR:
        model = xgb.XGBRegressor(**param, objective=REG_SQUAREDERROR)
    elif target == BINARY_LOGISTIC:
        model = xgb.XGBClassifier(**param, objective=BINARY_LOGISTIC)
    else:
        raise RuntimeError(f"unsupported objective function: {target}")

    # train model
    model.fit(X, Y)

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
        run_xgb(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 xgb.py config`. Before launching the subprocess, the app framework will 
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
