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
from teeapps.proto.params import woe_binning_pb2


def binning(
    df, feature, label, pos_label, bins, binning_method
) -> [
    woe_binning_pb2.WoeBinningReport.VariableBinningResult,
    woe_binning_pb2.WoeBinningRule.Rule,
]:
    if binning_method == "quantile":
        out = pandas.qcut(x=df[feature], q=bins, duplicates="drop")
    elif binning_method == "bucket":
        out = pandas.cut(x=df[feature], bins=bins, duplicates="drop")
    else:
        raise Exception(f"unsupported binning_method {binning_method}")

    label_filed = df[label]

    if label_filed.dtype == "float64":
        label_filed = label_filed.astype(np.int64)

    count = len(out.values.categories)
    # add else category if exist `nan` field
    has_nan = df[feature].isnull().values.any()
    if has_nan:
        out = out.values.add_categories("else")
        out = out.fillna("else")
        categories = out.categories
    else:
        categories = out.values.categories

    ret = pandas.crosstab(index=out, columns=label_filed, dropna=False)
    ret.columns = ret.columns.astype(str)
    ret["total"] = ret.sum(axis=1)
    ret["pos"] = ret.get(pos_label, 0)
    ret["neg"] = ret["total"] - ret["pos"]

    # just keep consistent with nebula
    # to avoid `np.log(ret["pos_rate"] / ret["neg_rate"])` is -np.inf:
    # all the zeros in ret["pos"] will be filled with 0.5, so as ret["neg"]
    ret["pos_rate"] = ret["pos"].astype("float64")
    ret["neg_rate"] = ret["neg"].astype("float64")
    ret.loc[(ret["pos_rate"] < 1), "pos_rate"] = 0.5
    ret.loc[(ret["neg_rate"] < 1), "neg_rate"] = 0.5
    ret["pos_rate"] = (ret["pos_rate"]) / ret["pos"].sum()
    ret["neg_rate"] = (ret["neg_rate"]) / ret["neg"].sum()

    ret["woe"] = np.log(ret["pos_rate"] / ret["neg_rate"])
    ret["iv"] = (ret["pos_rate"] - ret["neg_rate"]) * ret["woe"]
    ret["cat"] = categories
    iv = ret["iv"].sum()

    result = woe_binning_pb2.WoeBinningReport.VariableBinningResult()
    rule = woe_binning_pb2.WoeBinningRule.Rule()
    result.feature = feature
    result.bin_count = count
    result.iv = iv
    rule.feature = feature
    # else bin used to store abnormal case
    else_bin = rule.else_bin

    for _, row in ret.iterrows():
        # report
        bin = result.bins.add()
        bin.label = str(row["cat"])
        bin.woe = row["woe"]
        bin.iv = row["iv"]
        bin.total_count = row["total"]
        bin.positive_count = row["pos"]
        # rule
        if row["cat"] != "else":
            rule_bin = rule.bins.add()
            rule_bin.right = row["cat"].right
            rule_bin.woe = row["woe"]
        else:
            else_bin.woe = row["woe"]

    # if not contain NaN, result only add else bin with all other fields filled with 0
    if not has_nan:
        bin = result.bins.add()
        bin.label = "else"

    return result, rule


def run_woe_binning(config_json: str):
    logging.info("Running woe binning...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_WOE_BINNING", "App type is not 'OP_WOE_BINNING'"
    assert len(task_config.inputs) == 1, "WOE binning should has only 1 input"
    assert len(task_config.outputs) == 1, "WOE binning should has only 1  output"
    assert (
        len(task_config.inputs[0].schema.features) > 0
    ), "features should not be empty"
    # deal input data
    logging.info("Dealing input data...")
    df = common.gen_data_frame(task_config.inputs[0])
    params = woe_binning_pb2.WoeBinningParams()
    task_config.params.Unpack(params)

    feature_selects = params.feature_selects[:]
    labels = task_config.inputs[0].schema.labels[:]

    feature_binning_confs = []
    if len(params.feature_binning_confs) == 1:
        for feature in feature_selects:
            conf = woe_binning_pb2.WoeBinningParams.FeatureBinningConf()
            conf.CopyFrom(params.feature_binning_confs[0])
            conf.feature = feature
            feature_binning_confs.append(conf)
    else:
        feature_binning_confs = params.feature_binning_confs
    assert len(feature_binning_confs) == len(
        feature_selects
    ), "length of feature_binning_confs should be 1 or equal to the length of feature_selects"

    report = woe_binning_pb2.WoeBinningReport()
    rules = woe_binning_pb2.WoeBinningRule()
    for feature_binning_conf in feature_binning_confs:
        ret, rule = binning(
            df,
            feature_binning_conf.feature,
            labels[0],
            params.positive_label,
            feature_binning_conf.n_divide,
            feature_binning_conf.binning_method,
        )
        report.variable_ivs.append(ret)
        rules.rules.append(rule)

    rule_json = json_format.MessageToJson(
        rules,
        preserving_proto_field_name=True,
        including_default_value_fields=True,
        indent=0,
    )
    with open(task_config.outputs[0].data_path, "w") as rule_f:
        rule_f.write(rule_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_woe_binning(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 woe_bining.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
