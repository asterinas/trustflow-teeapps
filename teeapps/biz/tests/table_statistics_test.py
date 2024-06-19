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
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Div, Report, Tab, Table

from teeapps.biz.table_statistics.table_statistics import run_table_statistics

TEST_CONFIG_JSON = """
{
  "component_name": "table_statistics",
  "inputs": [
    {
      "data_path": "teeapps/biz/testdata/test4.csv",
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
      "data_path": "table_statistics.report"
    }
  ]
}
"""


class UnitTests(unittest.TestCase):
    def test_table_statistics(self):
        # before
        self.assertTrue(not os.path.exists("table_statistics.report"))
        # run
        run_table_statistics(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists("table_statistics.report"))
        # check output report
        with open("table_statistics.report", "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)
        row0 = report.tabs[0].divs[0].children[0].table.rows[0]
        self.assertEqual(row0.name, "AGE")
        self.assertEqual(row0.items[0].s, "float64")
        self.assertEqual(row0.items[1].s, "4")
        self.assertEqual(row0.items[2].s, "4")


if __name__ == "__main__":
    unittest.main()
