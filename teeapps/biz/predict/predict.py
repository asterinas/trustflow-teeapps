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
from google.protobuf import json_format
from lightgbm import LGBMClassifier, LGBMRegressor
from secretflow.spec.v1 import data_pb2
from sklearn.linear_model import LogisticRegression, Ridge
from xgboost import XGBClassifier, XGBRegressor

from teeapps.biz.common import common

COMPONENT_NAMES = ["xgb_predict", "lr_predict", "lgbm_predict"]

PRED_NAME = "pred_name"
SAVE_LABEL = "save_label"
LABEL_NAME = "label_name"
SAVE_ID = "save_id"
ID_NAME = "id_name"
COL_NAMES = "col_names"

IDS = "ids"
LABEL = "label"


def run_predict(task_config: dict):
    logging.info("Running predict...")

    assert (
        task_config[common.COMPONENT_NAME] in COMPONENT_NAMES
    ), f"Component name should be in {COMPONENT_NAMES}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 2, "Predict should have only 2 input"
    assert len(outputs) == 1, "Predict should have only 1 output"

    # deal input data
    logging.info("Dealing input data...")
    # get test data
    df = common.gen_data_frame(inputs[0])

    # load model
    logging.info("Loading model...")
    model = joblib.load(inputs[1][common.DATA_PATH])

    logging.info("Model predicting...")
    # check model type
    if isinstance(model, (XGBClassifier, LogisticRegression)):
        predict_data = df[model.feature_names_in_]
        # prob list, only get index=1, which means positive probability
        predict_result = pandas.DataFrame(
            [round(x, 6) for x in model.predict_proba(predict_data)[:, 1]],
            columns=[task_config[PRED_NAME]],
        )
    elif isinstance(model, (XGBRegressor, Ridge)):
        predict_data = df[model.feature_names_in_]
        predict_result = pandas.DataFrame(
            [round(x, 6) for x in model.predict(predict_data)],
            columns=[task_config[PRED_NAME]],
        )
    elif isinstance(model, LGBMClassifier):
        predict_data = df[model.origin_feature_name_]
        predict_result = pandas.DataFrame(
            [round(x, 6) for x in model.predict_proba(predict_data)[:, 1]],
            columns=[task_config[PRED_NAME]],
        )
    elif isinstance(model, LGBMRegressor):
        predict_data = df[model.origin_feature_name_]
        predict_result = pandas.DataFrame(
            [round(x, 6) for x in model.predict(predict_data)],
            columns=[task_config[PRED_NAME]],
        )
    else:
        raise RuntimeError(f"Unsupported model type: {type(model)}")

    result_list = [predict_result]
    ids = (
        inputs[0][IDS]
        if len(inputs[0][IDS]) > 0
        else inputs[0][common.SCHEMA][common.IDS]
    )
    labels = (
        inputs[0][LABEL]
        if len(inputs[0][LABEL]) > 0
        else inputs[0][common.SCHEMA][common.LABELS]
    )
    features = inputs[0][common.SCHEMA][common.FEATURES]

    # output data
    if task_config[SAVE_ID] == True:
        assert len(ids) > 0, "ID should not empty when save_id is true."
        result_list.append(df[[ids[0]]].rename(columns={ids[0]: task_config[ID_NAME]}))
    if task_config[SAVE_LABEL] == True:
        assert len(labels) > 0, "Label should not empty when save_label is true."
        result_list.append(
            df[[labels[0]]].rename(columns={labels[0]: task_config[LABEL_NAME]})
        )
    if len(task_config[COL_NAMES]) > 0:
        result_list.append(df[task_config[COL_NAMES]])
    result = pandas.concat(result_list, axis=1)
    # dump data
    logging.info("Dumping data...")
    output_path = outputs[0][common.DATA_PATH]
    result.to_csv(output_path, index=False)
    # dump output schema
    # set default type TABLE_SCHEMA_STRING_TYPE
    schema = data_pb2.TableSchema()
    schema.labels.append(task_config[PRED_NAME])
    schema.label_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    if task_config[SAVE_ID] == True:
        schema.ids.append(task_config[ID_NAME])
        schema.id_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    if task_config[SAVE_LABEL]:
        schema.labels.append(task_config[LABEL_NAME])
        schema.label_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    if len(task_config[COL_NAMES]) > 0:
        schema.features.extend(task_config[COL_NAMES])
        schema.feature_types.extend(
            [common.TABLE_SCHEMA_STRING_TYPE for _ in task_config[COL_NAMES]]
        )
    else:
        schema.features.extend(features)
        schema.feature_types.extend([common.TABLE_SCHEMA_STRING_TYPE for _ in features])
    schema = common.gen_output_schema(result, schema)
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
        run_predict(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 predict.py config`. Before launching the subprocess, the app framework will 
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
