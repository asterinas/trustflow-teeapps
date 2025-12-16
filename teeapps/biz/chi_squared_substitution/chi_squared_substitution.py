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
from secretflow.spec.v1 import data_pb2
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab, Table
from teeapps.biz.common import common

CHUNK_SIZE = 1024 * 1024
COMPONENT_NAME = "chi_squared_substitution"


def run_chi_squared_substitution(task_config: dict):
    logging.info("Running chi squared frequency substitution...")

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 2, f"{COMPONENT_NAME} should have only 2 input"
    assert len(outputs) == 2, f"{COMPONENT_NAME} should have only 2 output"

    with open(inputs[1][common.DATA_PATH], "r") as rules_f:
        rules = json.load(rules_f)

    label = rules["label"]
    label_type = common.get_col_types(inputs[0], [label])[0]

    bin_edges = {}
    for k, v in rules["edges"].items():
        bin_edges[k] = np.array(v)

    global_good_count = 0
    global_bad_count = 0
    bin_counts = {
        col: {i: {"good": 0, "bad": 0} for i in range(len(edge) - 1)}
        for col, edge in bin_edges.items()
    }
    positive_label = rules["positive_label"]

    positive_label_val = pd.Series(
        [positive_label], dtype=common.sf_to_pd_type(label_type)
    )[0]

    first_chunk = True
    for chunk in pd.read_csv(
        inputs[0][common.DATA_PATH],
        chunksize=CHUNK_SIZE,
    ):
        for k, v in bin_edges.items():
            chunk[k] = pd.cut(
                chunk[k],
                bins=v,
                labels=False,
                include_lowest=True,
            )

            for bin_label in range(len(v) - 1):
                bin_data = chunk[chunk[k] == bin_label]
                good_count = (bin_data[label] != positive_label_val).sum()
                bad_count = (bin_data[label] == positive_label_val).sum()

                bin_counts[k][bin_label]["good"] += good_count
                bin_counts[k][bin_label]["bad"] += bad_count

        global_good_count += (chunk[label] != positive_label_val).sum()
        global_bad_count += (chunk[label] == positive_label_val).sum()

        if first_chunk:
            chunk.to_csv(
                outputs[0][common.DATA_PATH],
                index=False,
                mode="w",
                header=True,
            )
            first_chunk = False
        else:
            chunk.to_csv(
                outputs[0][common.DATA_PATH],
                index=False,
                mode="a",
                header=False,
            )

    woe_dict = {}
    for column, bins in bin_counts.items():
        woe_dict[column] = {}
        for bin_label, counts in bins.items():
            good_dist = (
                counts["good"] / global_good_count if global_good_count != 0 else 0
            )
            bad_dist = counts["bad"] / global_bad_count if global_bad_count != 0 else 0
            woe = (
                np.log(good_dist / bad_dist) if good_dist != 0 and bad_dist != 0 else 0
            )
            woe_dict[column][bin_label] = woe

    # gen output TableSchema
    output_schema = data_pb2.TableSchema()
    common.append_table_schema(output_schema, inputs[0][common.SCHEMA])

    for i in range(len(output_schema.features)):
        if output_schema.features[i] in bin_edges:
            output_schema.feature_types[i] = "int"

    schema_json = json_format.MessageToJson(output_schema)
    with open(outputs[0][common.DATA_SCHEMA_PATH], "w") as schema_f:
        schema_f.write(schema_json)

    report_pb = Report(
        name="chi squared substitution report",
        tabs=[
            Tab(
                name="woe",
                divs=[
                    Div(
                        name=column,
                        children=[
                            Div.Child(
                                type="table",
                                table=Table(
                                    headers=[
                                        Table.HeaderItem(name="bin_label", type="str"),
                                        Table.HeaderItem(
                                            name="woe_value", type="float"
                                        ),
                                    ],
                                    rows=[
                                        Table.Row(
                                            items=[
                                                Attribute(s=str(k)),
                                                Attribute(f=v),
                                            ]
                                        )
                                        for k, v in woe_values.items()
                                    ],
                                ),
                            )
                        ],
                    )
                    for column, woe_values in woe_dict.items()
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
        run_chi_squared_substitution(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
