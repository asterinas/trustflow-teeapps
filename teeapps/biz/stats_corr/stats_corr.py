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

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import stats_corr_params_pb2
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table


def run_stats_corr(config_json: str):
    logging.info("Running stats_corr...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_STATS_CORR", "App type is not 'OP_STATS_CORR'"
    assert len(task_config.inputs) == 1, "Stats_corr should has only 1 input"
    assert len(task_config.outputs) == 1, "Stats_corr should has only 1 output"

    # deal input data
    logging.info("Dealing input data...")
    params = stats_corr_params_pb2.StatsCorrParams()
    task_config.params.Unpack(params)
    feature_names = params.feature_selects[:]
    if len(feature_names) == 0:
        feature_names = list(task_config.inputs[0].schema.features)
    df = common.gen_data_frame(task_config.inputs[0], usecols=feature_names)
    df = df[feature_names]
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
    with open(task_config.outputs[0].data_path, "w") as report_f:
        report_f.write(report_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_stats_corr(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 stats_corr.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
