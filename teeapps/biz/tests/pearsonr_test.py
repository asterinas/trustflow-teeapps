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

from teeapps.biz.pearsonr.pearsonr import run_pearsonr


class UnitTests(unittest.TestCase):
    def test_pearsonr(self):
        # before
        self.assertTrue(not os.path.exists("pearsonr.report"))

        config = """
        {
          "component_name": "pearsonr",
          "inputs": [
            {
              "data_path": "teeapps/biz/testdata/dataset1/data.csv",
              "schema": {
                "ids": ["ID", "NAME"],
                "features": ["AGE", "ADDRESS", "SALARY"],
                "labels": [],
                "id_types": ["int32", "str"],
                "feature_types": ["float", "str", "float"],
                "label_types": []
              },
              "feature_selects": []
            }
          ],
          "outputs": [
            {
              "data_path": "pearsonr.report"
            }
          ]
        }
        """

        # run
        run_pearsonr(json.loads(config))
        # after
        self.assertTrue(os.path.exists("pearsonr.report"))
        # check output report
        with open("pearsonr.report", "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)
        self.assertEqual(
            report.tabs[0].divs[0].children[0].table.rows[1].items[0].f,
            0.8728715777397156,
        )

    def test_pearsonr_none_value(self):
        # before
        config = """
        {
          "component_name": "pearsonr",
          "inputs": [
            {
              "data_path": "teeapps/biz/testdata/dataset1/data_with_none.csv",
              "schema": {
                "ids": ["ID", "NAME"],
                "features": ["AGE", "ADDRESS", "SALARY"],
                "labels": [],
                "id_types": ["int32", "str"],
                "feature_types": ["float", "str", "float"],
                "label_types": []
              },
              "feature_selects": []
            }
          ],
          "outputs": [
            {
              "data_path": "pearsonr.report"
            }
          ]
        }
        """

        # run
        with self.assertRaises(AssertionError):
            run_pearsonr(json.loads(config))


if __name__ == "__main__":
    unittest.main()
