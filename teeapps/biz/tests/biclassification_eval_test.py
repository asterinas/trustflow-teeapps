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


import csv
import json
import os
import unittest

from google.protobuf import json_format
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

from teeapps.biz.biclassification_eval.biclassification_eval import (
    run_biclassification_eval,
)

TEST_CONFIG_JSON = """
{
  "component_name": "biclassification_eval",
  "bucket_num": 10,
  "min_item_cnt_per_bucket": 5,
  "inputs": [
    {
      "data_path": "teeapps/biz/testdata/test6.csv",
      "schema": {
        "ids":[],
        "features": [],
        "labels": ["score", "y"],
        "id_types": [],
        "feature_types": [],
        "label_types": ["float", "float"]
      },
      "label": ["y"],
      "score": ["score"]
    }
  ],
  "outputs": [
    {
      "data_path": "biclass.report"
    }
  ]
}
"""

TEST_OUTPUT_REPORT_PATH = "biclass.report"


class UnitTests(unittest.TestCase):
    def test_biclassification_eval(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # run
        run_biclassification_eval(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # check output report
        with open(TEST_OUTPUT_REPORT_PATH, "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)


if __name__ == "__main__":
    unittest.main()
