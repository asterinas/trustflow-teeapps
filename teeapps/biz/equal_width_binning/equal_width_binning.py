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

import numpy as np
import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab, Table
from teeapps.biz.common import common

COMPONENT_NAME = "equal_width_binning"
FEATURE_SELECTS = "feature_selects"
CHUNK_SIZE = 1024 * 1024
BIN_NUM = "bin_num"


def run_equal_width_binning(task_config: dict):
    logging.info("Running equal width binning...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 2, f"{COMPONENT_NAME} should have only 2 output"
    assert (
        len(inputs[0][common.SCHEMA][common.FEATURES]) > 0
    ), "features should not be empty"

    feature_selects = inputs[0][FEATURE_SELECTS]

    global_min_max = {col: [np.inf, -np.inf] for col in feature_selects}

    for chunk in pd.read_csv(inputs[0][common.DATA_PATH], chunksize=CHUNK_SIZE):
        for column in feature_selects:
            col_min = chunk[column].min()
            col_max = chunk[column].max()
            global_min_max[column][0] = min(global_min_max[column][0], col_min)
            global_min_max[column][1] = max(global_min_max[column][1], col_max)

    # int64 to int, for json dumping.
    for k in global_min_max:
        mm = global_min_max[k]
        global_min_max[k] = [
            common.convert_numpy_to_python(mm[0]),
            common.convert_numpy_to_python(mm[1]),
        ]

    rules = {BIN_NUM: task_config[BIN_NUM], "global_min_max": global_min_max}

    with open(outputs[0][common.DATA_PATH], "w") as rule_f:
        json.dump(rules, rule_f)

    report_pb = Report(
        name="equal width binning report",
        tabs=[
            Tab(
                name="general",
                divs=[
                    Div(
                        children=[
                            Div.Child(
                                type="descriptions",
                                descriptions=Descriptions(
                                    items=[
                                        Descriptions.Item(
                                            name=BIN_NUM,
                                            type="float",
                                            value=Attribute(f=task_config[BIN_NUM]),
                                        )
                                    ],
                                ),
                            )
                        ],
                    )
                ],
            ),
            Tab(
                divs=[
                    Div(
                        children=[
                            Div.Child(
                                type="table",
                                table=Table(
                                    headers=[
                                        Table.HeaderItem(name="feature", type="str"),
                                        Table.HeaderItem(name="min", type="float"),
                                        Table.HeaderItem(name="max", type="float"),
                                    ],
                                    rows=[
                                        Table.Row(
                                            items=[
                                                Attribute(s=k),
                                                Attribute(f=v[0]),
                                                Attribute(f=v[1]),
                                            ]
                                        )
                                        for k, v in rules["global_min_max"].items()
                                    ],
                                ),
                            )
                        ],
                    )
                ],
            ),
        ],
    )

    report_json = json_format.MessageToJson(
        report_pb,
        preserving_proto_field_name=True,
        indent=0,
    )

    with open(outputs[1][common.DATA_PATH], "w") as report_f:
        report_f.write(report_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_equal_width_binning(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
