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


import csv
import json
import os
import unittest

from google.protobuf import json_format
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table
from teeapps.biz.multiclass_classification_eval.multiclass_classification_eval import (
    run_multiclass_classification_eval,
)


class UnitTests(unittest.TestCase):
    def test_works(self):
        config_json = """
        {
            "component_name": "multiclass_classification_eval",
            "inputs": [
                {
                    "data_path": "teeapps/biz/testdata/multiclass_classification_eval_testdata.csv",
                    "schema": {
                        "ids":[],
                        "features": [
                            "y_predict_a",
                            "y_predict_b",
                            "y_predict_c"
                        ],
                        "labels": [
                            "y_true"
                        ],
                        "id_types": [],
                        "feature_types": [
                            "float",
                            "float",
                            "float"
                        ],
                        "label_types": [
                            "str"
                        ]
                    },
                    "label": [
                        "y_true"
                    ],
                    "scores": [
                        "y_predict_a",
                        "y_predict_b",
                        "y_predict_c"
                    ]
                }
            ],
            "classes": [
                "a",
                "b",
                "c"
            ],
            "outputs": [
                {
                    "data_path": "multiclass_classification_eval_report.json"
                }
            ]
        }
        """

        # before
        self.assertTrue(
            not os.path.exists("multiclass_classification_eval_report.json")
        )
        # run
        run_multiclass_classification_eval(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("multiclass_classification_eval_report.json"))
        # check output report
        with open("multiclass_classification_eval_report.json", "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)

        print(report)


if __name__ == "__main__":
    unittest.main()
