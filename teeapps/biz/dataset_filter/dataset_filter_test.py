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
import os
import unittest

from google.protobuf import json_format
from teeapps.biz.dataset_filter.dataset_filter import run_dataset_filter

from secretflow.spec.v1 import data_pb2

TEST_CONFIG_JSON = """
{
  "appType": "OP_DATASET_FILTER",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.DatasetFilterParams",
    "drop_features": ["SALARY", "NAME"]
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test4.csv",
      "schema": {
        "ids": ["ID"],
        "features": ["NAME", "AGE", "ADDRESS", "SALARY"],
        "id_types": ["float"],
        "feature_types": ["str", "float", "str", "float"]
      }
    }
  ],
  "outputs": [
    {
      "dataPath": "output.csv",
      "dataSchemaPath": "output_schema.json"
    }
  ]
}
"""

TEST_OUTPUT_COLUMNS = [
    "ID",
    "AGE",
    "ADDRESS",
]

TEST_OUTPUT_IDS = ["ID"]
TEST_OUTPUT_FEATURES = ["AGE", "ADDRESS"]
TEST_OUTPUT_LABELS = []
TEST_OUTPUT_ID_TYPES = ["float64"]
TEST_OUTPUT_FEATURE_TYPES = ["float64", "str"]
TEST_OUTPUT_LABEL_TYPES = []

TEST_OUTPUT_PATH = "output.csv"
TEST_OUTPUT_SCHEMA_PATH = "output_schema.json"
TEST_OUTPUT_REPORT_PATH = "task.report"


class UnitTests(unittest.TestCase):
    def test_dataset_filter(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # run
        run_dataset_filter(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(os.path.exists(TEST_OUTPUT_SCHEMA_PATH))

        # check output[0] data
        with open(TEST_OUTPUT_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        self.assertListEqual(rows[0], TEST_OUTPUT_COLUMNS)

        # check output schema
        with open(TEST_OUTPUT_SCHEMA_PATH, "r") as schema_f:
            schema_json = schema_f.read()
        schema = data_pb2.TableSchema()
        json_format.Parse(schema_json, schema)
        self.assertListEqual(list(schema.ids), TEST_OUTPUT_IDS)
        self.assertListEqual(list(schema.features), TEST_OUTPUT_FEATURES)
        self.assertListEqual(list(schema.labels), TEST_OUTPUT_LABELS)
        self.assertListEqual(list(schema.id_types), TEST_OUTPUT_ID_TYPES)
        self.assertListEqual(list(schema.feature_types), TEST_OUTPUT_FEATURE_TYPES)
        self.assertListEqual(list(schema.label_types), TEST_OUTPUT_LABEL_TYPES)


if __name__ == "__main__":
    unittest.main()
