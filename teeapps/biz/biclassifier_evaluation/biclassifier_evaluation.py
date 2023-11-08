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
from sklearn import metrics

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import biclassifier_evaluation_pb2
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab, Table
from secretflow.spec.v1.component_pb2 import Attribute

HEAD_FPR_THRESHOLDS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2]


def make_eq_bin_report_div(
    equal_bin_reports: biclassifier_evaluation_pb2.BiClassifierEvalReport.EquiBinReport,
) -> Div:
    headers, rows = [], []
    headers = [
        Table.HeaderItem(
            name="start_value",
            type="float",
        ),
        Table.HeaderItem(
            name="end_value",
            type="float",
        ),
        Table.HeaderItem(
            name="positive",
            type="int",
        ),
        Table.HeaderItem(
            name="negative",
            type="int",
        ),
        Table.HeaderItem(
            name="total",
            type="int",
        ),
        Table.HeaderItem(
            name="precision",
            type="float",
        ),
        Table.HeaderItem(
            name="recall",
            type="float",
        ),
        Table.HeaderItem(
            name="false_positive_rate",
            type="float",
        ),
        Table.HeaderItem(
            name="f1_score",
            type="float",
        ),
        Table.HeaderItem(
            name="lift",
            type="float",
        ),
        Table.HeaderItem(
            name="predicted_positive_ratio",
            type="float",
        ),
        Table.HeaderItem(
            name="predicted_negative_ratio",
            type="float",
        ),
        Table.HeaderItem(
            name="cumulative_percent_of_positive",
            type="float",
        ),
        Table.HeaderItem(
            name="cumulative_percent_of_negative",
            type="float",
        ),
        Table.HeaderItem(
            name="total_cumulative_percent",
            type="float",
        ),
        Table.HeaderItem(
            name="ks",
            type="float",
        ),
        Table.HeaderItem(
            name="avg_score",
            type="float",
        ),
    ]
    for idx, bin_report in enumerate(equal_bin_reports):
        rows.append(
            Table.Row(
                name=f"bin_{idx}",
                items=[
                    Attribute(f=bin_report.start_value),
                    Attribute(f=bin_report.end_value),
                    Attribute(i64=int(bin_report.positive)),
                    Attribute(i64=int(bin_report.negative)),
                    Attribute(i64=int(bin_report.total)),
                    Attribute(f=bin_report.precision),
                    Attribute(f=bin_report.recall),
                    Attribute(f=bin_report.fpr),
                    Attribute(f=bin_report.f1_score),
                    Attribute(f=bin_report.lift),
                    Attribute(f=bin_report.distribution_of_positive),
                    Attribute(f=bin_report.distribution_of_negative),
                    Attribute(f=bin_report.cumulative_percent_of_positive),
                    Attribute(f=bin_report.cumulative_percent_of_negative),
                    Attribute(f=bin_report.total_cumulative_percent),
                    Attribute(f=bin_report.ks),
                    Attribute(f=bin_report.avg_score),
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


def make_summary_report_div(
    summary_report: biclassifier_evaluation_pb2.BiClassifierEvalReport.SummaryReport,
) -> Div:
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
                            name="total_samples",
                            type="int",
                            value=Attribute(i64=int(summary_report.total_samples)),
                        ),
                        Descriptions.Item(
                            name="positive_samples",
                            type="int",
                            value=Attribute(i64=int(summary_report.positive_samples)),
                        ),
                        Descriptions.Item(
                            name="negative_samples",
                            type="int",
                            value=Attribute(i64=int(summary_report.negative_samples)),
                        ),
                        Descriptions.Item(
                            name="auc",
                            type="float",
                            value=Attribute(f=summary_report.auc),
                        ),
                        Descriptions.Item(
                            name="ks",
                            type="float",
                            value=Attribute(f=summary_report.ks),
                        ),
                        Descriptions.Item(
                            name="f1_score",
                            type="float",
                            value=Attribute(f=summary_report.f1_score),
                        ),
                    ],
                ),
            ),
        ],
    )


def make_head_report_div(
    head_report: biclassifier_evaluation_pb2.BiClassifierEvalReport.PrReport,
) -> Div:
    headers = [
        Table.HeaderItem(
            name="threshold",
            type="float",
        ),
        Table.HeaderItem(
            name="FPR(False Positive Rate)",
            type="float",
        ),
        Table.HeaderItem(
            name="precision",
            type="float",
        ),
        Table.HeaderItem(
            name="recall",
            type="float",
        ),
    ]
    rows = []
    for idx, report in enumerate(head_report):
        rows.append(
            Table.Row(
                name=f"case_{idx}",
                items=[
                    Attribute(f=report.threshold),
                    Attribute(f=report.fpr),
                    Attribute(f=report.precision),
                    Attribute(f=report.recall),
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


def fill_bin_report(
    y_true: np.ndarray,
    score: np.ndarray,
    total_pos_cnt: int,
    total_neg_cnt: int,
    start: int,
    end: int,
    min_item_cnt_per_bucket: int,
    report: biclassifier_evaluation_pb2.BiClassifierEvalReport.EquiBinReport,
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
            f"One bin doesn't meet min_item_cnt_per_bucket requirement. \
              Items num = {end-start}, min_item_cnt_per_bucket={min_item_cnt_per_bucket}"
        )
    # prepare data
    total_cnt = total_pos_cnt + total_neg_cnt
    y_pred = np.array([(1 if i >= start else 0) for i in range(total_cnt)])
    fp = sum(1 for i in range(total_cnt) if y_true[i] == 0 and y_pred[i] == 1)
    cumu_pos_cnt = np.sum(y_true[start:] == 1)
    cumu_neg_cnt = np.sum(y_true[start:] == 0)
    score_sum = sum(score[start:end])

    # fill report
    report.positive = np.sum(y_true[start:end] == 1)
    report.negative = np.sum(y_true[start:end] == 0)
    report.total = end - start
    report.start_value = score[start]
    report.end_value = score[end - 1]
    report.precision = metrics.precision_score(y_true, y_pred)
    report.recall = metrics.recall_score(y_true, y_pred)
    report.fpr = -1 if total_neg_cnt == 0 else fp / total_neg_cnt
    report.f1_score = metrics.f1_score(y_true, y_pred)
    report.lift = (
        -1 if total_pos_cnt == 0 else report.precision * total_cnt / total_pos_cnt
    )
    report.distribution_of_positive = (
        -1 if total_pos_cnt == 0 else report.positive / total_pos_cnt
    )
    report.distribution_of_negative = (
        -1 if total_neg_cnt == 0 else report.negative / total_neg_cnt
    )
    report.cumulative_percent_of_positive = (
        -1 if total_pos_cnt == 0 else cumu_pos_cnt / total_pos_cnt
    )
    report.cumulative_percent_of_negative = (
        -1 if total_neg_cnt == 0 else cumu_neg_cnt / total_neg_cnt
    )
    report.total_cumulative_percent = (cumu_pos_cnt + cumu_neg_cnt) / total_cnt
    report.ks = (
        report.cumulative_percent_of_positive - report.cumulative_percent_of_negative
    )
    report.avg_score = score_sum / report.total


def run_biclassifier_evaluation(config_json: str):
    logging.info("Running biclassifier_evaluation...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert (
        task_config.app_type == "OP_BICLASSIFIER_EVALUATION"
    ), "App type is not 'OP_BICLASSIFIER_EVALUATION'"
    assert (
        len(task_config.inputs) == 1
    ), "Biclassifier_evaluation should has only 1 input"
    assert (
        len(task_config.outputs) == 1
    ), "Biclassifier_evaluation should has only 1 output"
    # labels in schema can be multiple, but eval target label is unique(in params)

    # deal input data
    logging.info("Dealing input data...")
    # params
    params = biclassifier_evaluation_pb2.BiClassifierEvalParams()
    task_config.params.Unpack(params)
    label_field = params.label_field_name
    score_field = params.score_field_name
    # get data
    df = common.gen_data_frame(
        task_config.inputs[0], usecols=[label_field, score_field]
    )
    # sort ascending
    df.sort_values(by=score_field, inplace=True, ignore_index=True)
    df[label_field] = df[label_field].astype("float64")
    y_true = df[label_field].to_numpy()
    df[score_field] = df[score_field].astype("float64")
    score = df[score_field].to_numpy()
    y_pred = np.array([(1 if x >= 0.5 else 0) for x in score])

    # summary report
    report = biclassifier_evaluation_pb2.BiClassifierEvalReport()
    summary_report = report.summary_report
    fprs, tprs, thresholds = metrics.roc_curve(y_true, score)
    summary_report.ks = max(tprs - fprs)
    summary_report.negative_samples = np.sum(y_true == 0)
    summary_report.positive_samples = np.sum(y_true == 1)
    summary_report.total_samples = len(y_true)
    if (
        max(summary_report.negative_samples, summary_report.positive_samples)
        == summary_report.total_samples
    ):
        summary_report.auc = -1.0
        logging.warning("The label of input all is 0 or 1")
    else:
        summary_report.auc = metrics.roc_auc_score(y_true, score)
    summary_report.f1_score = metrics.f1_score(y_true, y_pred)

    for target_fpr in HEAD_FPR_THRESHOLDS:
        idx = np.abs(fprs - target_fpr).argmin()
        threshold = thresholds[idx]
        y_pred_threshold = np.array([(1 if x >= threshold else 0) for x in score])
        tn, fp, _, _ = metrics.confusion_matrix(
            y_true=y_true, y_pred=y_pred_threshold
        ).ravel()
        head_report = report.head_report.add()
        head_report.threshold = threshold
        head_report.fpr = fp / (fp + tn)
        head_report.precision = metrics.precision_score(y_true, y_pred_threshold)
        head_report.recall = metrics.recall_score(y_true, y_pred_threshold)

    # step bin report
    bins = pandas.cut(score, params.bucket_num, duplicates="drop", retbins=True)[1]
    # bins is ascending order, but we calc report must from len - 1 to 0
    # sort flip bins
    bins = np.flip(bins)
    start = len(score)
    for thr in bins[1:-1]:
        bin_report = report.equi_range_bin_report.add()
        # find index end enforce score[end - 1] < thr
        end = np.searchsorted(score, thr, side="left")
        # start > end, sort reverse it when pass into function
        fill_bin_report(
            y_true,
            score,
            summary_report.positive_samples,
            summary_report.negative_samples,
            end,
            start,
            params.min_item_cnt_per_bucket,
            bin_report,
        )
        start = end
    # last bin
    bin_report = report.equi_range_bin_report.add()
    fill_bin_report(
        y_true,
        score,
        summary_report.positive_samples,
        summary_report.negative_samples,
        0,
        start,
        params.min_item_cnt_per_bucket,
        bin_report,
    )

    # freq bin report
    bins = pandas.qcut(score, params.bucket_num, duplicates="drop", retbins=True)[1]
    # bins is ascending order, but we calc report must from len - 1 to 0
    # sort flip bins
    bins = np.flip(bins)
    start = len(score)
    for thr in bins[1:-1]:
        bin_report = report.equi_frequent_bin_report.add()
        # find index end enforce score[end - 1] < thr
        end = np.searchsorted(score, thr, side="left")
        # start > end, sort reverse it when pass into function
        fill_bin_report(
            y_true,
            score,
            summary_report.positive_samples,
            summary_report.negative_samples,
            end,
            start,
            params.min_item_cnt_per_bucket,
            bin_report,
        )
        start = end
    # last bin
    bin_report = report.equi_frequent_bin_report.add()
    fill_bin_report(
        y_true,
        score,
        summary_report.positive_samples,
        summary_report.negative_samples,
        0,
        start,
        params.min_item_cnt_per_bucket,
        bin_report,
    )

    comp_report = Report(
        name="reports",
        desc="",
        tabs=[
            Tab(
                name="SummaryReport",
                desc="Summary Report for bi-classification evaluation.",
                divs=[make_summary_report_div(report.summary_report)],
            ),
            Tab(
                name="eq_frequent_bin_report",
                desc="Statistics Report for each bin.",
                divs=[make_eq_bin_report_div(report.equi_frequent_bin_report)],
            ),
            Tab(
                name="eq_range_bin_report",
                desc="",
                divs=[make_eq_bin_report_div(report.equi_range_bin_report)],
            ),
            Tab(
                name="head_report",
                desc="",
                divs=[make_head_report_div(report.head_report)],
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
        run_biclassifier_evaluation(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 biclassifier_evaluation.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
