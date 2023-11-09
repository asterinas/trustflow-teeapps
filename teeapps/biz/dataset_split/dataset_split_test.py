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
from teeapps.biz.dataset_split.dataset_split import run_dataset_split

from secretflow.spec.v1 import data_pb2


TEST_CONFIG_JSON = """
{
  "appType": "OP_DATASET_SPLIT",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.DatasetSplitParams",
    "training_data_ratio": 0.8,
    "should_fix_random": true,
    "random_state": 1,
    "shuffle": true
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test4.csv",
      "schema": {
        "ids": ["ID", "NAME"],
        "features": ["AGE", "ADDRESS", "SALARY"],
        "id_types": ["int", "str"],
        "feature_types": ["float", "str", "float"]
      }
    }
  ],
  "outputs": [
    {
      "dataPath": "train_output.csv",
      "dataSchemaPath": "train_output_schema.json"
    },
    {
      "dataPath": "test_output.csv",
      "dataSchemaPath": "test_output_schema.json"
    }
  ]
}
"""

TEST_OUTPUT_VALUES = [
    "1",
    "Paul",
    "3.0",
    "California",
    "20000.0",
]

TEST_OUTPUT_IDS = ["ID", "NAME"]
TEST_OUTPUT_FEATURES = ["AGE", "ADDRESS", "SALARY"]
TEST_OUTPUT_LABELS = []
TEST_OUTPUT_ID_TYPES = ["int64", "str"]
TEST_OUTPUT_FEATURE_TYPES = ["float64", "str", "float64"]
TEST_OUTPUT_LABEL_TYPES = []

TEST_OUTPUT_PATH = "train_output.csv"
TEST_OUTPUT_SCHEMA_PATH = "train_output_schema.json"
TEST_OUTPUT_REPORT_PATH = "task.report"


class UnitTests(unittest.TestCase):
    def test_dataset_split(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # run
        run_dataset_split(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        # check output data
        with open(TEST_OUTPUT_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        self.assertListEqual(rows[2], TEST_OUTPUT_VALUES)
        # contain column names
        self.assertEqual(len(rows), 4)
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
