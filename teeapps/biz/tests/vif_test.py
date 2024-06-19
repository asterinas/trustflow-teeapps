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
import os
import unittest

from google.protobuf import json_format
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab

from teeapps.biz.vif.vif import run_vif


class UnitTests(unittest.TestCase):
    def test_vif(self):
        # before
        self.assertTrue(not os.path.exists("vif.report"))

        config = """
        {
          "component_name": "vif",
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
              "feature_selects":[]
            }
          ],
          "outputs": [
            {
              "data_path": "vif.report"
            }
          ]
        }
        """

        # run
        run_vif(json.loads(config))
        # after
        self.assertTrue(os.path.exists("vif.report"))
        # check output report
        with open("vif.report", "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)
        self.assertEqual(len(report.tabs[0].divs[0].children[0].descriptions.items), 2)
        self.assertEqual(
            report.tabs[0].divs[0].children[0].descriptions.items[0].value.f,
            4.199999809265137,
        )

    def test_stats_vif_none_value(self):
        # before
        config = """
        {
          "component_name": "vif",
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
              "feature_selects":[]
            }
          ],
          "outputs": [
            {
              "data_path": "vif.report"
            }
          ]
        }
        """

        # run
        with self.assertRaises(AssertionError):
            run_vif(json.loads(config))


if __name__ == "__main__":
    unittest.main()
