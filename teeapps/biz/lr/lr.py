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
import numpy as np
import pandas
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge

from teeapps.biz.common import common

COMPONENT_NAME = "lr_train"

MAX_ITER = "max_iter"
REG_TYPE = "reg_type"
L2_NORM = "l2_norm"
TOL = "tol"
PENALTY = "penalty"

LINEAR = "linear"
LOGISTIC = "logistic"

IDS = "ids"
LABEL = "label"


def run_lr(task_config: dict):
    logging.info("Running lr...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(inputs[0])

    # labels in schema can be multiple, but eval target label is unique(in params)
    ids = inputs[0][IDS]
    labels = inputs[0][LABEL]
    assert len(labels) == 1, f"{COMPONENT_NAME} should have only 1 labels column"

    features = inputs[0][common.SCHEMA][common.FEATURES]
    features = [feature for feature in features if feature not in ids + labels]

    X = df[features]
    Y = pandas.to_numeric(df[labels[0]], errors="coerce")

    # train model
    logging.info("Training model...")
    if task_config[REG_TYPE] == LINEAR:
        model = Ridge(
            alpha=task_config[L2_NORM],
            tol=task_config[TOL],
            max_iter=task_config[MAX_ITER],
        )
    elif task_config[REG_TYPE] == LOGISTIC:
        c = (
            float("inf")
            if task_config[L2_NORM] == 0.0
            else 1 / np.double(task_config[L2_NORM])
        )
        model = LogisticRegression(
            tol=task_config[TOL],
            C=c,
            max_iter=task_config[MAX_ITER],
            penalty=task_config[PENALTY],
        )
    else:
        raise RuntimeError(f"unsupported regression_type: {task_config[REG_TYPE]}")

    model.fit(X, Y.values.ravel())

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
        run_lr(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 lr.py config`. Before launching the subprocess, the app framework will 
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
