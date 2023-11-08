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
import numpy as np
import sys

import pandas
from google.protobuf import json_format

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table
from secretflow.spec.v1.component_pb2 import Attribute


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


def run_table_statistics(config_json: str):
    logging.info("Running table_statistics...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_TABLE_STATISTICS"
    ), "App type is not 'OP_TABLE_STATISTICS'"
    assert len(task_config.inputs) == 1, "Table_staticstics should has only 1 inputs"
    assert len(task_config.outputs) == 1, "Table_staticstics should has only 1 outputs"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(
        task_config.inputs[0], usecols=task_config.inputs[0].schema.features[:]
    )
    stats = table_statistics(df)

    headers, rows = [], []
    for stat in stats.columns:
        headers.append(Table.HeaderItem(name=stat, desc="", type="str"))

    for rol_name, stat_row in stats.iterrows():
        rows.append(
            Table.Row(
                name=rol_name,
                items=[Attribute(s=str(stat_row[stat])) for stat in stats.columns],
            )
        )
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
    with open(task_config.outputs[0].data_path, "w") as report_f:
        report_f.write(report_json)


def main():
    assert len(sys.argv) == 2, "Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: %s", config_json)
        run_table_statistics(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 table_statistics.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
