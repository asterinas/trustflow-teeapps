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

import pandas
from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

from teeapps.biz.common import common

COMPONENT_NAME = "table_statistics"


def table_statistics(table: pandas.DataFrame) -> pandas.DataFrame:
    """Get table statistics for a pandas.DataFrame or VDataFrame.

    Args:
        pandas.DataFrame
    Returns:
        table_statistics: pandas.DataFrame
            including each column's datatype, total_count, count, count_na, min, max,
            var, std, sem, skewness, kurtosis, q1, q2, q3, moment_2, moment_3, moment_4,
            central_moment_2, central_moment_3, central_moment_4, sum, sum_2, sum_3 and sum_4.

            moment_2 means E[X^2].

            central_moment_2 means E[(X - mean(X))^2].

            sum_2 means sum(X^2).
    """
    assert isinstance(table, pandas.DataFrame), "table must be a pandas.DataFrame"
    index = table.columns
    result = pandas.DataFrame(index=index)
    result["datatype"] = [
        "str" if d_type == "object" else d_type for d_type in table.dtypes
    ]
    result["total_count"] = table.shape[0]
    result["count(non-NA count)"] = table.count()
    result["count_na(NA count)"] = table.isna().sum()
    result["na_ratio"] = table.isna().sum() / table.shape[0]
    result["min"] = table.min(numeric_only=True)
    result["max"] = table.max(numeric_only=True)
    result["mean"] = table.mean(numeric_only=True)
    result["var(variance)"] = table.var(numeric_only=True)
    result["std(standard deviation)"] = table.std(numeric_only=True)
    result["sem(standard error)"] = table.sem(numeric_only=True)
    result["skew"] = table.skew(numeric_only=True)
    result["kurtosis"] = table.kurtosis(numeric_only=True)
    result["q1(first quartile)"] = table.quantile(0.25, numeric_only=True)
    result["q2(second quartile, median)"] = table.quantile(0.5, numeric_only=True)
    result["q3(third quartile)"] = table.quantile(0.75, numeric_only=True)
    result["moment_2"] = table.select_dtypes("number").pow(2).mean(numeric_only=True)
    result["moment_3"] = table.select_dtypes("number").pow(3).mean(numeric_only=True)
    result["moment_4"] = table.select_dtypes("number").pow(4).mean(numeric_only=True)
    result["central_moment_2"] = (
        table.subtract(result["mean"])
        .select_dtypes("number")
        .pow(2)
        .mean(numeric_only=True)
    )
    result["central_moment_3"] = (
        table.subtract(result["mean"])
        .select_dtypes("number")
        .pow(3)
        .mean(numeric_only=True)
    )
    result["central_moment_4"] = (
        table.subtract(result["mean"])
        .select_dtypes("number")
        .pow(4)
        .mean(numeric_only=True)
    )
    result["sum"] = table.sum(numeric_only=True)
    result["sum_2"] = table.select_dtypes("number").pow(2).sum(numeric_only=True)
    result["sum_3"] = table.select_dtypes("number").pow(3).sum(numeric_only=True)
    result["sum_4"] = table.select_dtypes("number").pow(4).sum(numeric_only=True)
    return result


def run_table_statistics(task_config: dict):
    logging.info("Running table_statistics...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 inputs"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 outputs"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(
        inputs[0], usecols=inputs[0][common.SCHEMA][common.FEATURES]
    )
    stats = table_statistics(df)

    headers = [Table.HeaderItem(name=col, desc="", type="str") for col in stats.columns]

    rows = [
        Table.Row(
            name=rol_name,
            items=[Attribute(s=str(stat_row[stat])) for stat in stats.columns],
        )
        for rol_name, stat_row in stats.iterrows()
    ]

    stats_table = Table(headers=headers, rows=rows)
    report = Report(
        name="table statistics",
        desc="",
        tabs=[
            Tab(
                divs=[
                    Div(
                        children=[
                            Div.Child(
                                type="table",
                                table=stats_table,
                            )
                        ],
                    )
                ],
            )
        ],
    )

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
        run_table_statistics(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 table_statistics.py config`. Before launching the subprocess, the app framework will 
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
