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
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab, Table
from sklearn import metrics

from teeapps.biz.common import common

COMPONENT_NAME = "biclassification_eval"

BUCKET_NUM = "bucket_num"
MIN_ITEM_CNT_PER_BUCKET = "min_item_cnt_per_bucket"
LABEL = "label"
SCORE = "score"

HEAD_FPR_THRESHOLDS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2]

# eq_bin_report
START_VALUE = "start_value"
END_VALUE = "end_value"
POSITIVE = "positive"
NEGATIVE = "negative"
TOTAL = "total"
PRECISION = "precision"
RECALL = "recall"
FALSE_POSITIVE_RATE = "false_positive_rate"
F1_SCORE = "f1_score"
LIFT = "lift"
DISTRIBUTION_OF_POSITIVE = "distribution_of_positive"
DISTRIBUTION_OF_NEGATIVE = "distribution_of_negative"
CUMULATIVE_PERCENT_OF_POSITIVE = "cumulative_percent_of_positive"
CUMULATIVE_PERCENT_OF_NEGATIVE = "cumulative_percent_of_negative"
TOTAL_CUMULATIVE_PERCENT = "total_cumulative_percent"
KS = "ks"
AVG_SCORE = "avg_score"

# summary_report
TOTAL_SAMPLES = "total_samples"
POSITIVE_SAMPLES = "positive_samples"
NEGATIVE_SAMPLES = "negative_samples"
AUC = "auc"

# head_report
FPR = "fpr"
PRECISION = "precision"
RECALL = "recall"
THRESHOLD = "threshold"


def make_eq_bin_report_div(
    equal_bin_reports: list,
) -> Div:
    headers, rows = [], []
    headers = [
        Table.HeaderItem(
            name=START_VALUE,
            type="float",
        ),
        Table.HeaderItem(
            name=END_VALUE,
            type="float",
        ),
        Table.HeaderItem(
            name=POSITIVE,
            type="int",
        ),
        Table.HeaderItem(
            name=NEGATIVE,
            type="int",
        ),
        Table.HeaderItem(
            name=TOTAL,
            type="int",
        ),
        Table.HeaderItem(
            name=PRECISION,
            type="float",
        ),
        Table.HeaderItem(
            name=RECALL,
            type="float",
        ),
        Table.HeaderItem(
            name=FALSE_POSITIVE_RATE,
            type="float",
        ),
        Table.HeaderItem(
            name=F1_SCORE,
            type="float",
        ),
        Table.HeaderItem(
            name=LIFT,
            type="float",
        ),
        Table.HeaderItem(
            name=DISTRIBUTION_OF_POSITIVE,
            type="float",
        ),
        Table.HeaderItem(
            name=DISTRIBUTION_OF_NEGATIVE,
            type="float",
        ),
        Table.HeaderItem(
            name=CUMULATIVE_PERCENT_OF_POSITIVE,
            type="float",
        ),
        Table.HeaderItem(
            name=CUMULATIVE_PERCENT_OF_NEGATIVE,
            type="float",
        ),
        Table.HeaderItem(
            name=TOTAL_CUMULATIVE_PERCENT,
            type="float",
        ),
        Table.HeaderItem(
            name=KS,
            type="float",
        ),
        Table.HeaderItem(
            name=AVG_SCORE,
            type="float",
        ),
    ]
    for idx, bin_report in enumerate(equal_bin_reports):
        rows.append(
            Table.Row(
                name=f"bin_{idx}",
                items=[
                    Attribute(f=bin_report[START_VALUE]),
                    Attribute(f=bin_report[END_VALUE]),
                    Attribute(i64=int(bin_report[POSITIVE])),
                    Attribute(i64=int(bin_report[NEGATIVE])),
                    Attribute(i64=int(bin_report[TOTAL])),
                    Attribute(f=bin_report[PRECISION]),
                    Attribute(f=bin_report[RECALL]),
                    Attribute(f=bin_report[FPR]),
                    Attribute(f=bin_report[F1_SCORE]),
                    Attribute(f=bin_report[LIFT]),
                    Attribute(f=bin_report[DISTRIBUTION_OF_POSITIVE]),
                    Attribute(f=bin_report[DISTRIBUTION_OF_NEGATIVE]),
                    Attribute(f=bin_report[CUMULATIVE_PERCENT_OF_POSITIVE]),
                    Attribute(f=bin_report[CUMULATIVE_PERCENT_OF_NEGATIVE]),
                    Attribute(f=bin_report[TOTAL_CUMULATIVE_PERCENT]),
                    Attribute(f=bin_report[KS]),
                    Attribute(f=bin_report[AVG_SCORE]),
                ],
            )
        )
    return Div(
        name="",
        desc="",
        children=[
            Div.Child(
                type="table",
                table=Table(
                    name="",
                    desc="",
                    headers=headers,
                    rows=rows,
                ),
            ),
        ],
    )


def make_summary_report_div(summary_report: dict) -> Div:
    return Div(
        name="",
        desc="",
        children=[
            Div.Child(
                type="descriptions",
                descriptions=Descriptions(
                    name="",
                    desc="",
                    items=[
                        Descriptions.Item(
                            name=TOTAL_SAMPLES,
                            type="int",
                            value=Attribute(i64=int(summary_report[TOTAL_SAMPLES])),
                        ),
                        Descriptions.Item(
                            name=POSITIVE_SAMPLES,
                            type="int",
                            value=Attribute(i64=int(summary_report[POSITIVE_SAMPLES])),
                        ),
                        Descriptions.Item(
                            name=NEGATIVE_SAMPLES,
                            type="int",
                            value=Attribute(i64=int(summary_report[NEGATIVE_SAMPLES])),
                        ),
                        Descriptions.Item(
                            name=AUC,
                            type="float",
                            value=Attribute(f=summary_report[AUC]),
                        ),
                        Descriptions.Item(
                            name=KS,
                            type="float",
                            value=Attribute(f=summary_report[KS]),
                        ),
                        Descriptions.Item(
                            name=F1_SCORE,
                            type="float",
                            value=Attribute(f=summary_report[F1_SCORE]),
                        ),
                    ],
                ),
            ),
        ],
    )


def make_head_report_div(head_reports: list) -> Div:
    headers = [
        Table.HeaderItem(
            name=THRESHOLD,
            type="float",
        ),
        Table.HeaderItem(
            name=FPR,
            type="float",
        ),
        Table.HeaderItem(
            name=PRECISION,
            type="float",
        ),
        Table.HeaderItem(
            name=RECALL,
            type="float",
        ),
    ]
    rows = []
    for idx, report in enumerate(head_reports):
        rows.append(
            Table.Row(
                name=f"case_{idx}",
                items=[
                    Attribute(f=report[THRESHOLD]),
                    Attribute(f=report[FPR]),
                    Attribute(f=report[PRECISION]),
                    Attribute(f=report[RECALL]),
                ],
            )
        )
    return Div(
        name="",
        desc="",
        children=[
            Div.Child(
                type="table",
                table=Table(
                    name="",
                    desc="",
                    headers=headers,
                    rows=rows,
                ),
            ),
        ],
    )


def init_bin_report() -> dict:
    report = dict()
    report[POSITIVE] = 0
    report[NEGATIVE] = 0
    report[TOTAL] = 0
    report[START_VALUE] = 0
    report[END_VALUE] = 0
    report[PRECISION] = 0
    report[RECALL] = 0
    report[FPR] = 0
    report[F1_SCORE] = 0
    report[LIFT] = 0
    report[DISTRIBUTION_OF_POSITIVE] = 0
    report[DISTRIBUTION_OF_NEGATIVE] = 0
    report[CUMULATIVE_PERCENT_OF_POSITIVE] = 0
    report[CUMULATIVE_PERCENT_OF_NEGATIVE] = 0
    report[TOTAL_CUMULATIVE_PERCENT] = 0
    report[KS] = 0
    report[AVG_SCORE] = 0

    return report


def fill_bin_report(
    y_true: np.ndarray,
    score: np.ndarray,
    total_pos_cnt: int,
    total_neg_cnt: int,
    start: int,
    end: int,
    min_item_cnt_per_bucket: int,
    report: dict,
):
    """
    index >= start, the label is 1
    index < start, the label is 0
    when calculate interval [x, y]
    start = x, end = y + 1
    """
    if end <= start:
        return
    if (end - start) < min_item_cnt_per_bucket:
        raise RuntimeError(
            (
                f"One bin doesn't meet min_item_cnt_per_bucket requirement. "
                f"Items num = {end-start}, min_item_cnt_per_bucket={min_item_cnt_per_bucket}"
            )
        )
    # prepare data
    total_cnt = total_pos_cnt + total_neg_cnt
    y_pred = np.array([(1 if i >= start else 0) for i in range(total_cnt)])
    fp = sum(1 for i in range(total_cnt) if y_true[i] == 0 and y_pred[i] == 1)
    cumu_pos_cnt = np.sum(y_true[start:] == 1)
    cumu_neg_cnt = np.sum(y_true[start:] == 0)
    score_sum = sum(score[start:end])

    # fill report
    report[POSITIVE] = np.sum(y_true[start:end] == 1)
    report[NEGATIVE] = np.sum(y_true[start:end] == 0)
    report[TOTAL] = end - start
    report[START_VALUE] = score[start]
    report[END_VALUE] = score[end - 1]
    report[PRECISION] = metrics.precision_score(y_true, y_pred)
    report[RECALL] = metrics.recall_score(y_true, y_pred)
    report[FPR] = -1 if total_neg_cnt == 0 else fp / total_neg_cnt
    report[F1_SCORE] = metrics.f1_score(y_true, y_pred)
    report[LIFT] = (
        -1 if total_pos_cnt == 0 else report[PRECISION] * total_cnt / total_pos_cnt
    )
    report[DISTRIBUTION_OF_POSITIVE] = (
        -1 if total_pos_cnt == 0 else report[POSITIVE] / total_pos_cnt
    )
    report[DISTRIBUTION_OF_NEGATIVE] = (
        -1 if total_neg_cnt == 0 else report[NEGATIVE] / total_neg_cnt
    )
    report[CUMULATIVE_PERCENT_OF_POSITIVE] = (
        -1 if total_pos_cnt == 0 else cumu_pos_cnt / total_pos_cnt
    )
    report[CUMULATIVE_PERCENT_OF_NEGATIVE] = (
        -1 if total_neg_cnt == 0 else cumu_neg_cnt / total_neg_cnt
    )
    report[TOTAL_CUMULATIVE_PERCENT] = (cumu_pos_cnt + cumu_neg_cnt) / total_cnt
    report[KS] = (
        report[CUMULATIVE_PERCENT_OF_POSITIVE] - report[CUMULATIVE_PERCENT_OF_NEGATIVE]
    )
    report[AVG_SCORE] = score_sum / report[TOTAL]


def run_biclassification_eval(task_config: dict):
    logging.info("Running biclassification_eval...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # labels in schema can be multiple, but eval target label is unique(in params)
    # deal input data
    logging.info("Dealing input data...")
    # params
    labels = inputs[0][LABEL]
    scores = inputs[0][SCORE]
    assert len(labels) == 1, f"{COMPONENT_NAME} should have only 1 label column"
    assert len(scores) == 1, f"{COMPONENT_NAME} should have only 1 score column"

    # get data
    df = common.gen_data_frame(inputs[0], usecols=[labels[0], scores[0]])
    # sort ascending
    df.sort_values(by=scores[0], inplace=True, ignore_index=True)
    df[labels[0]] = df[labels[0]].astype("float64")
    y_true = df[labels[0]].to_numpy()
    df[scores[0]] = df[scores[0]].astype("float64")
    score = df[scores[0]].to_numpy()
    y_pred = np.array([(1 if x >= 0.5 else 0) for x in score])

    # summary report
    summary_report = dict()
    fprs, tprs, thresholds = metrics.roc_curve(y_true, score)
    summary_report[KS] = max(tprs - fprs)
    summary_report[NEGATIVE_SAMPLES] = np.sum(y_true == 0)
    summary_report[POSITIVE_SAMPLES] = np.sum(y_true == 1)
    summary_report[TOTAL_SAMPLES] = len(y_true)
    if (
        max(summary_report[NEGATIVE_SAMPLES], summary_report[POSITIVE_SAMPLES])
        == summary_report[TOTAL_SAMPLES]
    ):
        summary_report[AUC] = -1.0
        logging.warning("The label of input all is 0 or 1")
    else:
        summary_report[AUC] = metrics.roc_auc_score(y_true, score)
    summary_report[F1_SCORE] = metrics.f1_score(y_true, y_pred)

    # head reports
    head_reports = list()
    for target_fpr in HEAD_FPR_THRESHOLDS:
        idx = np.abs(fprs - target_fpr).argmin()
        threshold = thresholds[idx]
        y_pred_threshold = np.array([(1 if x >= threshold else 0) for x in score])
        tn, fp, _, _ = metrics.confusion_matrix(
            y_true=y_true, y_pred=y_pred_threshold
        ).ravel()
        head_report = dict()
        head_report[THRESHOLD] = threshold
        head_report[FPR] = fp / (fp + tn)
        head_report[PRECISION] = metrics.precision_score(y_true, y_pred_threshold)
        head_report[RECALL] = metrics.recall_score(y_true, y_pred_threshold)
        head_reports.append(head_report)

    # eq range bin report
    bins = pandas.cut(score, task_config[BUCKET_NUM], duplicates="drop", retbins=True)[
        1
    ]
    # bins is ascending order, but we calc report must from len - 1 to 0
    # sort flip bins
    bins = np.flip(bins)
    start = len(score)
    eq_range_bin_reports = list()
    for thr in bins[1:-1]:
        eq_range_bin_report = init_bin_report()
        # find index end enforce score[end - 1] < thr
        end = np.searchsorted(score, thr, side="left")
        # start > end, sort reverse it when pass into function
        fill_bin_report(
            y_true,
            score,
            summary_report[POSITIVE_SAMPLES],
            summary_report[NEGATIVE_SAMPLES],
            end,
            start,
            task_config[MIN_ITEM_CNT_PER_BUCKET],
            eq_range_bin_report,
        )
        eq_range_bin_reports.append(eq_range_bin_report)
        start = end
    # last bin
    eq_range_bin_report = init_bin_report()
    fill_bin_report(
        y_true,
        score,
        summary_report[POSITIVE_SAMPLES],
        summary_report[NEGATIVE_SAMPLES],
        0,
        start,
        task_config[MIN_ITEM_CNT_PER_BUCKET],
        eq_range_bin_report,
    )
    eq_range_bin_reports.append(eq_range_bin_report)

    # eq freq bin report
    bins = pandas.qcut(score, task_config[BUCKET_NUM], duplicates="drop", retbins=True)[
        1
    ]
    # bins is ascending order, but we calc report must from len - 1 to 0
    # sort flip bins
    bins = np.flip(bins)
    start = len(score)
    eq_freq_bin_reports = list()
    for thr in bins[1:-1]:
        eq_freq_bin_report = init_bin_report()
        # find index end enforce score[end - 1] < thr
        end = np.searchsorted(score, thr, side="left")
        # start > end, sort reverse it when pass into function
        fill_bin_report(
            y_true,
            score,
            summary_report[POSITIVE_SAMPLES],
            summary_report[NEGATIVE_SAMPLES],
            end,
            start,
            task_config[MIN_ITEM_CNT_PER_BUCKET],
            eq_freq_bin_report,
        )
        eq_freq_bin_reports.append(eq_freq_bin_report)
        start = end
    # last bin
    eq_freq_bin_report = init_bin_report()
    fill_bin_report(
        y_true,
        score,
        summary_report[POSITIVE_SAMPLES],
        summary_report[NEGATIVE_SAMPLES],
        0,
        start,
        task_config[MIN_ITEM_CNT_PER_BUCKET],
        eq_freq_bin_report,
    )
    eq_freq_bin_reports.append(eq_freq_bin_report)

    comp_report = Report(
        name="reports",
        desc="",
        tabs=[
            Tab(
                name="SummaryReport",
                desc="Summary Report for bi-classification evaluation.",
                divs=[make_summary_report_div(summary_report)],
            ),
            Tab(
                name="eq_frequent_bin_report",
                desc="Statistics Report for each bin.",
                divs=[make_eq_bin_report_div(eq_freq_bin_reports)],
            ),
            Tab(
                name="eq_range_bin_report",
                desc="",
                divs=[make_eq_bin_report_div(eq_range_bin_reports)],
            ),
            Tab(
                name="head_report",
                desc="",
                divs=[make_head_report_div(head_reports)],
            ),
        ],
    )
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
        run_biclassification_eval(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 biclassification_eval.py config`. Before launching the subprocess, the app framework will 
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
