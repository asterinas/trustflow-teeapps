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
import xgboost as xgb
from google.protobuf import json_format
import joblib

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import xgb_hyper_params_pb2


def get_model_param(
    params: xgb_hyper_params_pb2.XgbHyperParams, param_keys: list
) -> dict:
    param = {}
    for key in param_keys:
        if key == "lambda":
            param["reg_lambda"] = getattr(params, key)
        elif key == "alpha":
            param["reg_alpha"] = getattr(params, key)
        elif key == "num_boost_round":
            param["n_estimators"] = getattr(params, key)
        elif key == "seed":
            param["random_state"] = getattr(params, key)
        else:
            param[key] = getattr(params, key)
    logging.info(f"Model params {param}")
    return param


def run_xgb(config_json: str):
    logging.info("Running xgb training...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_XGB", "App type is not 'OP_XGB'"
    assert len(task_config.inputs) == 1, "XGB should has only 1 input"
    assert len(task_config.outputs) == 1, "XGB should has only 1 output"
    assert len(task_config.inputs[0].schema.labels) == 1, "XGB should has only 1 label"

    # get train data
    logging.info("Loading training data...")
    df = common.gen_data_frame(task_config.inputs[0])
    features = task_config.inputs[0].schema.features[:]
    labels = task_config.inputs[0].schema.labels[:]
    X = df[features]
    Y = pandas.to_numeric(df[labels[0]], errors="coerce")

    logging.info("Parsing xgb parameters...")
    params = xgb_hyper_params_pb2.XgbHyperParams()
    task_config.params.Unpack(params)
    param_keys = [
        "num_boost_round",
        "max_depth",
        "max_leaves",
        "seed",
        "learning_rate",
        "lambda",
        "gamma",
        "colsample_bytree",
        "base_score",
        "min_child_weight",
        "alpha",
        "subsample",
        "max_bin",
        "tree_method",
        "booster",
    ]

    # update params, use getattr to avoid python keywords
    target = getattr(params, "objective")
    param = get_model_param(params, param_keys)
    model = None
    if target == "reg:squarederror":
        model = xgb.XGBRegressor(**param, objective="reg:squarederror")
    elif target == "binary:logistic":
        model = xgb.XGBClassifier(**param, objective="binary:logistic")
    else:
        raise Exception(f"unsupported objective function: {target}")

    # train model
    model.fit(X, Y)

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
        run_xgb(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 xgb.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
