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
from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab, Table
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder, label_binarize
from teeapps.biz.common import common

COMPONENT_NAME = "multiclass_classification_eval"
LABEL = "label"
SCORES = "scores"
CLASSES = "classes"


def run_multiclass_classification_eval(task_config: dict):
    logging.info("Running multiclass_classification_eval...")

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
    scores = inputs[0][SCORES]
    assert len(labels) == 1, f"{COMPONENT_NAME} should have only 1 label column"
    assert len(scores) >= 2, f"{COMPONENT_NAME} should have at least 2 scores column"
    classes = task_config[CLASSES]

    assert len(classes) == len(
        scores
    ), f"The cnt of classes [{len(classes)}] does not match that of scores [{len(scores)}]."

    df = common.gen_data_frame(inputs[0], usecols=labels + scores)

    y_true = df[labels].to_numpy()
    y_score = df[scores].to_numpy()

    label_type = common.get_col_types(inputs[0], labels)[0]

    if label_type == "str":
        logging.info("The label type is str.")
    elif "int" in label_type:
        classes = [int(x) for x in classes]
    else:
        raise RuntimeError(f"unexpected label type: {label_type}.")

    y_true_binarized = label_binarize(y_true, classes=classes)

    auc_ovr = roc_auc_score(y_true_binarized, y_score, multi_class="ovr")
    auc_ovo = roc_auc_score(y_true_binarized, y_score, multi_class="ovo")

    label_encoder = LabelEncoder()
    label_encoder.fit(classes)

    y_pred_indices = np.argmax(y_score, axis=1)
    y_pred = label_encoder.inverse_transform(y_pred_indices)

    accuracy = accuracy_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred, average=None)
    f1 = f1_score(y_true, y_pred, average=None)

    conf_matrix = confusion_matrix(y_true, y_pred)
    ks_values = []
    for i in range(len(classes)):
        true_positive_rate = np.cumsum(conf_matrix[i, :] / sum(conf_matrix[i, :]))
        false_positive_rate = np.cumsum(
            (np.sum(conf_matrix, axis=0) - conf_matrix[i, :])
            / (np.sum(conf_matrix) - np.sum(conf_matrix[i, :]))
        )
        ks_statistic = max(abs(true_positive_rate - false_positive_rate))
        ks_values.append(ks_statistic)

    headers = [
        Table.HeaderItem(
            name="class",
            type="string",
        ),
        Table.HeaderItem(
            name="recall",
            type="float",
        ),
        Table.HeaderItem(
            name="f1",
            type="float",
        ),
        Table.HeaderItem(
            name="ks",
            type="float",
        ),
    ]

    rows = []
    for i, j, m, n in zip(classes, recall, f1, ks_values):
        rows.append(
            Table.Row(
                items=[
                    Attribute(s=str(i)),
                    Attribute(f=j),
                    Attribute(f=m),
                    Attribute(f=n),
                ],
            )
        )

    report = Report(
        name="Multi-class Classification Eval Report",
        desc="",
        tabs=[
            Tab(
                name="",
                desc="",
                divs=[
                    Div(
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
                                            name="AUC (OVR)",
                                            type="float",
                                            value=Attribute(f=auc_ovr),
                                        ),
                                        Descriptions.Item(
                                            name="AUC (OVO)",
                                            type="float",
                                            value=Attribute(f=auc_ovo),
                                        ),
                                        Descriptions.Item(
                                            name="accuracy",
                                            type="float",
                                            value=Attribute(f=accuracy),
                                        ),
                                    ],
                                ),
                            )
                        ],
                    ),
                    Div(
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
                    ),
                ],
            )
        ],
    )

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
        run_multiclass_classification_eval(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
