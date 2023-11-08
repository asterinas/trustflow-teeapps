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

import pandas
import numpy as np
from google.protobuf import json_format
from sklearn.linear_model import Ridge
from sklearn.linear_model import LogisticRegression
from scipy import stats
import joblib

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import lr_hyper_params_pb2


def run_lr(config_json: str):
    logging.info("Running lr...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_LR", "App type is not 'OP_LR'"
    assert len(task_config.inputs) == 1, "Lr should has only 1 input"
    assert len(task_config.outputs) == 1, "Lr should has only 1 output"
    assert len(task_config.inputs[0].schema.labels) == 1, "Lr should has only 1 label"

    # deal input data
    logging.info("Dealing input data...")
    # params
    params = lr_hyper_params_pb2.LrHyperParams()
    task_config.params.Unpack(params)

    df = common.gen_data_frame(task_config.inputs[0])
    features = task_config.inputs[0].schema.features[:]
    labels = task_config.inputs[0].schema.labels[:]
    X = df[features]
    Y = df[labels]

    # train model
    logging.info("Training model...")
    model = None
    if params.regression_type == "linear":
        model = Ridge(alpha=params.l2_norm, tol=params.tol, max_iter=params.max_iter)
    elif params.regression_type == "logistic":
        c = float("inf") if params.l2_norm == 0.0 else 1 / np.double(params.l2_norm)
        model = LogisticRegression(
            tol=params.tol, C=c, max_iter=params.max_iter, penalty=params.penalty
        )
    else:
        raise Exception(f"unsupported regression_type: {params.regression_type}")

    model.fit(X, Y.values.ravel())

    # dump model
    logging.info("Dumping model...")
    model_data_path = task_config.outputs[0].data_path
    joblib.dump(model, model_data_path)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_lr(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 lr.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
