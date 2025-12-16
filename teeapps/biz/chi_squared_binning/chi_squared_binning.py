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

COMPONENT_NAME = "chi_squared_binning"
MAX_BIN_NUM = "max_bin_num"
THRESHOLD = "threshold"
POSITIVE_LABEL = "positive_label"
FEATURE_SELECTS = "feature_selects"
LABEL = "label"

DEFAULT_THRESHOLD = 3.841


def calculate_chi2(obs, exp):
    return ((obs - exp) ** 2) / exp if exp != 0 else 0


def chi2_binning(
    data, column, target, positive_value, max_bin_num=None, threshold=DEFAULT_THRESHOLD
):
    data = data.sort_values(by=column)
    unique_vals = data[column].unique()
    bins = [[v] for v in unique_vals]

    while max_bin_num is None or len(bins) > max_bin_num:
        chi2_values = []

        for i in range(len(bins) - 1):
            combined_bin = bins[i] + bins[i + 1]
            bin_data = data[data[column].isin(combined_bin)]

            positive_count = (
                bin_data[target]
                .value_counts()
                .get(
                    positive_value,
                    None,
                )
            )
            total_count = len(bin_data)
            expected_count = total_count * (
                data[target]
                .value_counts(normalize=True)
                .get(
                    positive_value,
                    None,
                )
            )

            # 计算卡方值
            chi2 = calculate_chi2(positive_count, expected_count)
            chi2_values.append(chi2)

        min_chi2_index = int(np.argmin(chi2_values))

        if max_bin_num is None and chi2_values[min_chi2_index] > threshold:
            break

        bins[min_chi2_index] += bins[min_chi2_index + 1]
        del bins[min_chi2_index + 1]

    cut_points = [max(b) for b in bins[:-1]]
    cut_points.insert(0, -np.inf)
    cut_points.append(np.inf)

    return cut_points


def run_chi_squared_binning(task_config: dict):
    logging.info("Running chi squared binning...")
    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 2, f"{COMPONENT_NAME} should have only 2 output"
    assert (
        len(inputs[0][common.SCHEMA][common.FEATURES]) > 0
    ), "features should not be empty"

    feature_selects = inputs[0][FEATURE_SELECTS]
    label = inputs[0][LABEL][0]
    label_type = common.get_col_types(inputs[0], [label])[0]

    max_bin_num = task_config.get(MAX_BIN_NUM, None)
    threshold = task_config.get(THRESHOLD, DEFAULT_THRESHOLD)
    positive_label = task_config[POSITIVE_LABEL]

    positive_label_val = pd.Series(
        [positive_label], dtype=common.sf_to_pd_type(label_type)
    )[0]

    cut_points = {}
    sample_data = {col: [] for col in feature_selects}
    sample_data[label] = []
    chunksize = 1024 * 1024
    for chunk in pd.read_csv(inputs[0][common.DATA_PATH], chunksize=chunksize):
        for col in feature_selects:
            sample_data[col].extend(chunk[col].tolist())
        sample_data[label].extend(chunk[label].tolist())

    sample_df = pd.DataFrame(sample_data)
    for column in feature_selects:
        cut_points[column] = chi2_binning(
            sample_df, column, label, positive_label_val, max_bin_num, threshold
        )

    rules = {}
    rules[POSITIVE_LABEL] = positive_label
    rules[LABEL] = label
    rules["edges"] = {}

    for k, v in cut_points.items():
        rules["edges"][k] = [float(x) for x in v]

    with open(outputs[0][common.DATA_PATH], "w") as rule_f:
        json.dump(rules, rule_f)

    report_pb = Report(
        name="chi squared binning report",
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
                                            name=THRESHOLD,
                                            type="float",
                                            value=Attribute(f=threshold),
                                        ),
                                        Descriptions.Item(
                                            name=MAX_BIN_NUM,
                                            type="int",
                                            value=Attribute(i64=max_bin_num),
                                        ),
                                        Descriptions.Item(
                                            name=POSITIVE_LABEL,
                                            type="str",
                                            value=Attribute(s=positive_label),
                                        ),
                                        Descriptions.Item(
                                            name=LABEL,
                                            type="str",
                                            value=Attribute(s=label),
                                        ),
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
                                        Table.HeaderItem(name="edges", type="float"),
                                    ],
                                    rows=[
                                        Table.Row(
                                            items=[
                                                Attribute(s=k),
                                                Attribute(fs=v),
                                            ]
                                        )
                                        for k, v in rules["edges"].items()
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
        run_chi_squared_binning(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
