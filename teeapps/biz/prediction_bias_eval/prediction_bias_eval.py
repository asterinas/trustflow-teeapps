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
from teeapps.proto.params import prediction_bias_eval_pb2
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table
from secretflow.spec.v1.component_pb2 import Attribute

EQUAL_FREQUENCY = "equal_frequency"
EQUAL_WIDTH = "equal_width"


def make_comp_report(
    report: prediction_bias_eval_pb2.PredictionBiasEvalReport,
) -> Report:
    table = Table(
        name="Prediction Bias Table",
        desc="Calculate prediction bias, ie. average of predictions - average of labels.",
        headers=[
            Table.HeaderItem(name="interval", desc="prediction interval", type="str"),
            Table.HeaderItem(
                name="left_endpoint",
                desc="left endpoint of interval",
                type="float",
            ),
            Table.HeaderItem(
                name="left_closed",
                desc="indicate if left endpoint of interval is closed",
                type="bool",
            ),
            Table.HeaderItem(
                name="right_endpoint",
                desc="right endpoint of interval",
                type="float",
            ),
            Table.HeaderItem(
                name="right_closed",
                desc="indicate if right endpoint of interval is closed",
                type="bool",
            ),
            Table.HeaderItem(
                name="is_na",
                desc="indicate if the bucket is empty",
                type="bool",
            ),
            Table.HeaderItem(
                name="avg_prediction",
                desc="average prediction of interval",
                type="float",
            ),
            Table.HeaderItem(
                name="avg_label",
                desc="average label of interval",
                type="float",
            ),
            Table.HeaderItem(
                name="bias",
                desc="prediction bias of interval",
                type="float",
            ),
        ],
    )

    def gen_interval_str(left_endpoint, left_closed, right_endpoint, right_closed):
        return f"{'[' if left_closed else '('}{left_endpoint}, {right_endpoint}{']' if right_closed else ')'}"

    for i, bucket_report in enumerate(report.bucket_reports):
        table.rows.append(
            Table.Row(
                name=str(i),
                items=[
                    Attribute(
                        s=gen_interval_str(
                            bucket_report.left_endpoint,
                            bucket_report.left_closed,
                            bucket_report.right_endpoint,
                            bucket_report.right_closed,
                        )
                    ),
                    Attribute(f=bucket_report.left_endpoint),
                    Attribute(b=bucket_report.left_closed),
                    Attribute(f=bucket_report.right_endpoint),
                    Attribute(b=bucket_report.right_closed),
                    Attribute(b=bucket_report.is_na),
                    Attribute(f=bucket_report.avg_prediction),
                    Attribute(f=bucket_report.avg_label),
                    Attribute(f=bucket_report.bias),
                ],
            )
        )

    return Report(
        name="Prediction Bias Report",
        tabs=[
            Tab(
                divs=[
                    Div(
                        children=[
                            Div.Child(
                                type="table",
                                table=table,
                            )
                        ],
                    )
                ],
            )
        ],
    )


def run_prediction_bias_eval(config_json: str):
    logging.info("Running prediction_bias_eval...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_PREDICTION_BIAS_EVALUATION"
    ), "App type is not 'OP_PREDICTION_BIAS_EVALUATION'"
    assert len(task_config.inputs) == 1, "Prediction_bias_eval should has only 1 input"
    assert (
        len(task_config.outputs) == 1
    ), "Prediction_bias_eval should has only 1 output"

    # labels in schema can be multiple, but eval target label is unique(in params)

    # deal input data
    logging.info("Dealing input data...")
    params = prediction_bias_eval_pb2.PredictionBiasEvalParams()
    task_config.params.Unpack(params)
    label_field = params.label_field_name
    score_field = params.score_field_name
    df = common.gen_data_frame(
        task_config.inputs[0], usecols=[label_field, score_field]
    )
    # sort ascending
    df.sort_values(by=score_field, inplace=True, ignore_index=True)
    df[label_field] = df[label_field].astype("float64")
    y_true = df[label_field].to_numpy()
    df[score_field] = df[score_field].astype("float64")
    score = df[score_field].to_numpy()

    report = prediction_bias_eval_pb2.PredictionBiasEvalReport()
    bins = None
    if params.bucket_method == EQUAL_WIDTH:
        bins = pandas.cut(score, params.bucket_num, duplicates="drop", retbins=True)[1]
    elif params.bucket_method == EQUAL_FREQUENCY:
        bins = pandas.qcut(score, params.bucket_num, duplicates="drop", retbins=True)[1]
    else:
        raise RuntimeError(f"params.bucket_method:{params.bucket_method} not support")

    start = 0
    for idx, thr in enumerate(bins[1:]):
        bucket_report = report.bucket_reports.add()
        end = np.searchsorted(score, thr, side="right")
        cnt = end - start
        if cnt < params.min_item_cnt_per_bucket and cnt > 0:
            raise RuntimeError(
                f"One bin doesn't meet min_item_cnt_per_bucket requirement. \
                Items num = {cnt}, min_item_cnt_per_bucket={params.min_item_cnt_per_bucket}"
            )
        # thr = bins[1:-1][idx] = bins[idx+1]
        bucket_report.left_endpoint = bins[idx]
        bucket_report.left_closed = False
        bucket_report.right_endpoint = thr
        bucket_report.right_closed = True
        if cnt == 0:
            bucket_report.is_na = True
            bucket_report.avg_prediction = 0
            bucket_report.avg_label = 0
            bucket_report.bias = 0
        else:
            avg_prediction = np.average(score[start:end])
            avg_label = np.average(y_true[start:end])
            bucket_report.is_na = False
            bucket_report.avg_prediction = avg_prediction
            bucket_report.avg_label = avg_label
            bucket_report.bias = np.abs(avg_prediction - avg_label)
        start = end

    comp_report = make_comp_report(report)
    # dump report
    logging.info("Dump report...")
    report_json = json_format.MessageToJson(
        comp_report,
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
        run_prediction_bias_eval(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 prediction_bias_eval.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
