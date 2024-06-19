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
from secretflow.spec.v1 import data_pb2
from teeapps.biz.woe_substitution.woe_substitution import run_woe_substitution

TEST_CONFIG_JSON = """
{
  "component_name": "woe_substitution",
  "inputs": [
    {
      "data_path": "teeapps/biz/testdata/test5.csv",
      "schema": {
        "ids": [],
        "features": ["AT", "V", "AP", "RH", "PE"],
        "labels": ["RE"],
        "id_types": [],
        "feature_types": ["float", "float", "float", "float", "float"],
        "label_types": ["float"]
      }
    },
    {
      "data_path": "teeapps/biz/testdata/woe_rules.json"
    }
  ],
  "outputs": [
    {
      "data_path": "output.csv",
      "data_schema_path": "output_schema.json"
    }
  ]
}
"""

TEST_OUTPUT_PATH = "output.csv"
TEST_OUTPUT_SCHEMA_PATH = "output_schema.json"


class UnitTests(unittest.TestCase):
    def test_woe(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        # run
        run_woe_substitution(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(os.path.exists(TEST_OUTPUT_SCHEMA_PATH))

        # check output result
        with open(TEST_OUTPUT_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        self.assertEqual(rows[1][0], "-1.540445040947149")

        with open(TEST_OUTPUT_SCHEMA_PATH, "r") as schema_f:
            schema_json = schema_f.read()
        schema = data_pb2.TableSchema()
        json_format.Parse(schema_json, schema)


if __name__ == "__main__":
    unittest.main()
