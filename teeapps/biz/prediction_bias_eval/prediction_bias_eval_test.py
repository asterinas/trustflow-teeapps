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


import os
import unittest

from google.protobuf import json_format
from teeapps.biz.prediction_bias_eval.prediction_bias_eval import (
    run_prediction_bias_eval,
)

from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

TEST_CONFIG_JSON = """
{
  "appType": "OP_PREDICTION_BIAS_EVALUATION",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.PredictionBiasEvalParams",
    "label_field_name": "y",
    "score_field_name": "score",
    "bucket_num": 10,
    "min_item_cnt_per_bucket": 2,
    "bucket_method": "equal_width"
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test6.csv",
      "schema": {
        "labels": ["score", "y"],
        "label_types": ["float", "float"]
      }
    }
  ],
  "outputs": [
    {
      "data_path": "task.report"
    }
  ]
}
"""

TEST_OUTPUT_REPORT_PATH = "task.report"


class UnitTests(unittest.TestCase):
    def test_biclassifier_evaluation(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # run
        run_prediction_bias_eval(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # check output report
        with open(TEST_OUTPUT_REPORT_PATH, "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)


if __name__ == "__main__":
    unittest.main()
