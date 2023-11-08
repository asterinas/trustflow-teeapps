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
import joblib

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import predict_pb2
from secretflow.spec.v1 import data_pb2


def run_predict(config_json: str):
    logging.info("Running predict...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_PREDICT", "App type is not 'OP_PREDICT'"
    assert len(task_config.inputs) == 2, "Predict should has only 2 input"
    assert len(task_config.outputs) == 1, "Predict should has only 1 output"
    assert (
        len(task_config.inputs[0].schema.ids) <= 1
    ), "Predict should has at most 1 ids"
    assert (
        len(task_config.inputs[0].schema.labels) <= 1
    ), "Predict should has at most 1 labels"

    # deal input data
    logging.info("Dealing input data...")
    # params
    params = predict_pb2.PredictionParams()
    task_config.params.Unpack(params)
    output_control = params.output_control
    # get test data
    df = common.gen_data_frame(task_config.inputs[0])
    ids = task_config.inputs[0].schema.ids[:]
    labels = task_config.inputs[0].schema.labels[:]
    features = task_config.inputs[0].schema.features[:]
    # load model
    logging.info("Loading model...")
    model = joblib.load(task_config.inputs[1].data_path)
    predict_data = df[model.feature_names_in_]
    # predict data
    logging.info("Model predicting...")
    # prob list, only get index=1
    prob_result = pandas.DataFrame(
        [round(x, 6) for x in model.predict_proba(predict_data)[:, 1]],
        columns=[output_control.score_field_name],
    )
    result_list = [prob_result]
    # output data
    if output_control.output_label == True and (len(labels) >= 1):
        label_field_name = (
            output_control.label_field_name
            if len(output_control.label_field_name) > 0
            else labels[0]
        )
        result_list.append(df[labels].rename(columns={labels[0]: label_field_name}))
    if output_control.output_id == True and (len(ids) >= 1):
        id_column_name = (
            output_control.id_field_name
            if len(output_control.id_field_name) > 0
            else ids[0]
        )
        result_list.append(df[ids].rename(columns={ids[0]: id_column_name}))
    result_list.append(df[output_control.col_names[:]])
    result = pandas.concat(result_list, axis=1)
    # dump data
    logging.info("Dumping data...")
    output_path = task_config.outputs[0].data_path
    result.to_csv(output_path, index=False)
    # dump output schema
    # set default type TABLE_SCHEMA_STRING_TYPE
    schema = data_pb2.TableSchema()
    if output_control.output_id:
        schema.ids.append(output_control.id_field_name)
        schema.id_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    schema.labels.append(output_control.score_field_name)
    schema.label_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    if output_control.output_label:
        schema.labels.append(output_control.label_field_name)
        schema.label_types.append(common.TABLE_SCHEMA_STRING_TYPE)
    if len(output_control.col_names) > 0:
        schema.features.extend(output_control.col_names)
        schema.feature_types.extend(
            [common.TABLE_SCHEMA_STRING_TYPE for _ in output_control.col_names]
        )
    else:
        schema.features.extend(features)
        schema.feature_types.extend([common.TABLE_SCHEMA_STRING_TYPE for _ in features])
    schema = common.gen_output_schema(result, schema)
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
        run_predict(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 predict.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
