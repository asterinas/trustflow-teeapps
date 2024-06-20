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
import pandas
from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

from teeapps.biz.common import common

COMPONENT_NAME = "prediction_bias_eval"

BUCKET_NUM = "bucket_num"
MIN_ITEM_CNT_PER_BUCKET = "min_item_cnt_per_bucket"
BUCKET_METHOD = "bucket_method"
LABEL = "label"
SCORE = "score"

EQUAL_FREQUENCY = "equal_frequency"
EQUAL_WIDTH = "equal_width"

LEFT_ENDPOINT = "left_endpoint"
LEFT_CLOSED = "left_closed"
RIGHT_ENDPOINT = "right_endpoint"
RIGHT_CLOSED = "right_closed"
IS_NA = "is_na"
AVG_PREDICTION = "avg_prediction"
AVG_LABEL = "avg_label"
BIAS = "bias"


def make_comp_report(bucket_reports: list) -> Report:
    table = Table(
        name="Prediction Bias Table",
        desc="Calculate prediction bias, ie. average of predictions - average of labels.",
        headers=[
            Table.HeaderItem(name="interval", desc="prediction interval", type="str"),
            Table.HeaderItem(
                name=LEFT_ENDPOINT,
                desc="left endpoint of interval",
                type="float",
            ),
            Table.HeaderItem(
                name=LEFT_CLOSED,
                desc="indicate if left endpoint of interval is closed",
                type="bool",
            ),
            Table.HeaderItem(
                name=RIGHT_ENDPOINT,
                desc="right endpoint of interval",
                type="float",
            ),
            Table.HeaderItem(
                name=RIGHT_CLOSED,
                desc="indicate if right endpoint of interval is closed",
                type="bool",
            ),
            Table.HeaderItem(
                name=IS_NA,
                desc="indicate if the bucket is empty",
                type="bool",
            ),
            Table.HeaderItem(
                name=AVG_PREDICTION,
                desc="average prediction of interval",
                type="float",
            ),
            Table.HeaderItem(
                name=AVG_LABEL,
                desc="average label of interval",
                type="float",
            ),
            Table.HeaderItem(
                name=BIAS,
                desc="prediction bias of interval",
                type="float",
            ),
        ],
    )

    def gen_interval_str(left_endpoint, left_closed, right_endpoint, right_closed):
        return f"{'[' if left_closed else '('}{left_endpoint}, {right_endpoint}{']' if right_closed else ')'}"

    for i, bucket_report in enumerate(bucket_reports):
        table.rows.append(
            Table.Row(
                name=str(i),
                items=[
                    Attribute(
                        s=gen_interval_str(
                            bucket_report[LEFT_ENDPOINT],
                            bucket_report[LEFT_CLOSED],
                            bucket_report[RIGHT_ENDPOINT],
                            bucket_report[RIGHT_CLOSED],
                        )
                    ),
                    Attribute(f=bucket_report[LEFT_ENDPOINT]),
                    Attribute(b=bucket_report[LEFT_CLOSED]),
                    Attribute(f=bucket_report[RIGHT_ENDPOINT]),
                    Attribute(b=bucket_report[RIGHT_CLOSED]),
                    Attribute(b=bucket_report[IS_NA]),
                    Attribute(f=bucket_report[AVG_PREDICTION]),
                    Attribute(f=bucket_report[AVG_LABEL]),
                    Attribute(f=bucket_report[BIAS]),
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


def run_prediction_bias_eval(task_config: dict):
    logging.info("Running prediction_bias_eval...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # labels in schema can be multiple, but eval target label is unique(in params)
    labels = inputs[0][LABEL]
    scores = inputs[0][SCORE]
    assert len(labels) == 1, f"{COMPONENT_NAME} should have only 1 label column"
    assert len(scores) == 1, f"{COMPONENT_NAME} should have only 1 score column"

    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(inputs[0], usecols=[labels[0], scores[0]])
    # sort ascending
    df.sort_values(by=scores[0], inplace=True, ignore_index=True)
    df[labels[0]] = df[labels[0]].astype("float64")
    y_true = df[labels[0]].to_numpy()
    df[scores[0]] = df[scores[0]].astype("float64")
    score = df[scores[0]].to_numpy()

    if task_config[BUCKET_METHOD] == EQUAL_WIDTH:
        bins = pandas.cut(
            score, task_config[BUCKET_NUM], duplicates="drop", retbins=True
        )[1]
    elif task_config[BUCKET_METHOD] == EQUAL_FREQUENCY:
        bins = pandas.qcut(
            score, task_config[BUCKET_NUM], duplicates="drop", retbins=True
        )[1]
    else:
        raise RuntimeError(
            f"params.bucket_method:{task_config[BUCKET_METHOD]} not support"
        )

    # report
    bucket_reports = list()
    start = 0
    for idx, thr in enumerate(bins[1:]):
        bucket_report = dict()
        end = np.searchsorted(score, thr, side="right")
        cnt = end - start
        if cnt < task_config[MIN_ITEM_CNT_PER_BUCKET] and cnt > 0:
            raise RuntimeError(
                f"One bin doesn't meet min_item_cnt_per_bucket requirement. \
                Items num = {cnt}, min_item_cnt_per_bucket={task_config[MIN_ITEM_CNT_PER_BUCKET]}"
            )
        # thr = bins[1:-1][idx] = bins[idx+1]
        bucket_report[LEFT_ENDPOINT] = bins[idx]
        bucket_report[LEFT_CLOSED] = False
        bucket_report[RIGHT_ENDPOINT] = thr
        bucket_report[RIGHT_CLOSED] = True
        if cnt == 0:
            bucket_report[IS_NA] = True
            bucket_report[AVG_PREDICTION] = 0
            bucket_report[AVG_LABEL] = 0
            bucket_report[BIAS] = 0
        else:
            avg_prediction = np.average(score[start:end])
            avg_label = np.average(y_true[start:end])
            bucket_report[IS_NA] = False
            bucket_report[AVG_PREDICTION] = avg_prediction
            bucket_report[AVG_LABEL] = avg_label
            bucket_report[BIAS] = np.abs(avg_prediction - avg_label)
        bucket_reports.append(bucket_report)
        start = end

    comp_report = make_comp_report(bucket_reports)
    # dump report
    logging.info("Dump report...")
    report_json = json_format.MessageToJson(
        comp_report,
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
        run_prediction_bias_eval(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 prediction_bias_eval.py config`. Before launching the subprocess, the app framework will 
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
