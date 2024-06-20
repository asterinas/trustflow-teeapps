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
from teeapps.biz.common import common

COMPONENT_NAME = "woe_binning"

BINNING_METHOD = "binning_method"
POSITIVE_LABEL = "positive_label"
BIN_NUM = "bin_num"
FEATURE_SELECTS = "feature_selects"
LABEL = "label"

QUANTILE = "quantile"
BUCKET = "bucket"
NA_CATEGORY = "else"
TOTAL = "total"
POS_COUNT = "pos_count"
NEG_COUNT = "neg_count"
POS_RATE = "pos_rate"
NEG_RATE = "neg_rate"
WOE = "woe"
IV = "iv"
CATEGORY = "category"
FEATURE = "feature"
BIN_COUNT = "bin_count"
BINS = "bins"
RIGHT = "right"
ELSE_BIN = "else_bin"


def binning(df, feature, label, pos_label, bins, binning_method) -> [dict, dict]:
    if binning_method == QUANTILE:
        out = pandas.qcut(x=df[feature], q=bins, duplicates="drop")
    elif binning_method == BUCKET:
        out = pandas.cut(x=df[feature], bins=bins, duplicates="drop")
    else:
        raise RuntimeError(f"unsupported binning_method {binning_method}")

    label_field = df[label]
    # convert pos_label according to label_field type
    pos_label = str(pandas.Series([pos_label], dtype=label_field.dtype)[0])

    bin_count = len(out.cat.categories)
    # add else category if exist `nan` field
    has_nan = df[feature].isnull().values.any()
    if has_nan:
        out = out.cat.add_categories([NA_CATEGORY])
        out = out.fillna(NA_CATEGORY)

    categories = out.cat.categories
    ret = pandas.crosstab(index=out, columns=label_field, dropna=False)
    ret.columns = ret.columns.astype(str)
    ret[TOTAL] = ret.sum(axis=1)
    ret[POS_COUNT] = ret.get(pos_label, 0)
    ret[NEG_COUNT] = ret[TOTAL] - ret[POS_COUNT]

    # just keep consistent with nebula
    # to avoid `np.log(ret[POS_RATE] / ret[NEG_RATE])` is -np.inf:
    # all the zeros in ret[POS_COUNT] will be filled with 0.5, so as ret[NEG_COUNT]
    ret[POS_RATE] = ret[POS_COUNT].astype("float64")
    ret[NEG_RATE] = ret[NEG_COUNT].astype("float64")
    ret.loc[(ret[POS_RATE] < 1), POS_RATE] = 0.5
    ret.loc[(ret[NEG_RATE] < 1), NEG_RATE] = 0.5
    ret[POS_RATE] = (ret[POS_RATE]) / ret[POS_RATE].sum()
    ret[NEG_RATE] = (ret[NEG_RATE]) / ret[NEG_RATE].sum()

    ret[WOE] = np.log(ret[POS_RATE] / ret[NEG_RATE])
    ret[IV] = (ret[POS_RATE] - ret[NEG_RATE]) * ret[WOE]
    ret[CATEGORY] = categories
    iv = ret[IV].sum()

    # output report and rule
    report = dict()
    report[FEATURE] = feature
    report[BIN_COUNT] = bin_count
    report[IV] = iv
    report_bins = list()

    rule = dict()
    rule[FEATURE] = feature
    rule_bins = list()

    for _, row in ret.iterrows():
        # report
        report_bin = dict()
        report_bin[LABEL] = str(row[CATEGORY])
        report_bin[WOE] = row[WOE]
        report_bin[IV] = row[IV]
        report_bin[TOTAL] = row[TOTAL]
        report_bin[POS_COUNT] = row[POS_COUNT]
        report_bins.append(report_bin)
        # rule
        if row[CATEGORY] != NA_CATEGORY:
            rule_bin = dict()
            rule_bin[RIGHT] = row[CATEGORY].right
            rule_bin[WOE] = row[WOE]
            rule_bins.append(rule_bin)
        else:
            rule_else_bin = dict()
            rule_else_bin[WOE] = row[WOE]
            rule[ELSE_BIN] = rule_else_bin

    # if not contain NaN, report only add else bin with all other fields filled with 0
    if not has_nan:
        report_bin = dict()
        report_bin[LABEL] = NA_CATEGORY
        report_bin[WOE] = 0
        report_bin[IV] = 0
        report_bin[TOTAL] = 0
        report_bin[POS_COUNT] = 0
        report_bins.append(report_bin)

    report[BINS] = report_bins
    rule[BINS] = rule_bins

    return report, rule


def run_woe_binning(task_config: dict):
    logging.info("Running woe binning...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"
    assert (
        len(inputs[0][common.SCHEMA][common.FEATURES]) > 0
    ), "features should not be empty"
    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(inputs[0])

    feature_selects = inputs[0][FEATURE_SELECTS]
    labels = inputs[0][common.SCHEMA][common.LABELS]
    assert len(labels) == 1, f"{COMPONENT_NAME} inputs should have only 1 label"

    binning_method = task_config[BINNING_METHOD]
    positive_label = task_config[POSITIVE_LABEL]
    bin_num = task_config[BIN_NUM]

    reports = list()
    rules = list()
    for feature in feature_selects:
        report, rule = binning(
            df,
            feature,
            labels[0],
            positive_label,
            bin_num,
            binning_method,
        )
        reports.append(report)
        rules.append(rule)

    with open(outputs[0][common.DATA_PATH], "w") as rule_f:
        json.dump(rules, rule_f)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_woe_binning(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 woe_bining.py config`. Before launching the subprocess, the app framework will 
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
