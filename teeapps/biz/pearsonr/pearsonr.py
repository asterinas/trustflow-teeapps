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
from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

from teeapps.biz.common import common

COMPONENT_NAME = "pearsonr"

FEATURE_SELECTS = "feature_selects"


def run_pearsonr(task_config: dict):
    logging.info("Running pearsonr...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # deal input data
    logging.info("Dealing input data...")
    feature_selects = inputs[0][FEATURE_SELECTS]
    if len(feature_selects) == 0:
        feature_selects = list(inputs[0][common.SCHEMA][common.FEATURES])
    df = common.gen_data_frame(inputs[0], usecols=feature_selects)
    assert not df.isnull().values.any(), "Unsupported NaN field."
    # corr will ignore row with missing value
    # corr will ignore columns that not number type
    numerical_features = df.select_dtypes(include=[np.number]).columns.tolist()
    corr_matrix = df.corr(numeric_only=True)
    assert corr_matrix.shape[0] == corr_matrix.shape[1] and corr_matrix.shape[0] == len(
        numerical_features
    )
    # fill report
    corr_table = Table(
        headers=[
            Table.HeaderItem(name=feature, desc="", type="float")
            for feature in numerical_features
        ],
        rows=[
            Table.Row(
                name=numerical_features[r],
                desc="",
                items=[
                    # float round won't work in protobuf, it will always keep the real value
                    # round(value, 6) won't work
                    Attribute(f=999.0 if np.isnan(value) else value)
                    for value in corr_matrix.iloc[r, :]
                ],
            )
            for r in range(corr_matrix.shape[0])
        ],
    )

    report = Report(
        name="corr",
        desc="corr table",
        tabs=[
            Tab(
                divs=[
                    Div(
                        children=[
                            Div.Child(
                                type="table",
                                table=corr_table,
                            )
                        ],
                    )
                ],
            )
        ],
    )
    logging.info("Dumping report...")
    # dump report
    report_json = json_format.MessageToJson(
        report,
        preserving_proto_field_name=True,
        indent=0,
    )
    with open(outputs[0][common.DATA_PATH], "w") as report_f:
        report_f.write(report_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_pearsonr(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 pearsonr.py config`. Before launching the subprocess, the app framework will 
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
