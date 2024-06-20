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
from teeapps.biz.psi.psi import run_psi

TEST_CONFIG_JSON = """
{
  "component_name": "psi",
  "inputs":[
    {
      "data_path": "teeapps/biz/testdata/breast_cancer/alice.csv",
      "schema": {
        "ids": [
          "id"
        ],
        "features": [
          "mean radius",
          "mean texture",
          "mean perimeter",
          "mean area",
          "mean smoothness"
        ],
        "labels": [],
        "id_types": [
          "int"
        ],
        "feature_types": [
          "float",
          "float",
          "float",
          "float",
          "float"
        ],
        "label_types": []
      },
      "key": [
        "id"
      ]
    },
    {
      "data_path": "teeapps/biz/testdata/breast_cancer/bob.csv",
      "schema": {
        "ids": [
          "id"
        ],
        "features": [
          "mean compactness",
          "mean concavity",
          "mean concave points",
          "mean symmetry",
          "mean fractal dimension"
        ],
        "labels": [
          "target"
        ],
        "id_types": [
          "int"
        ],
        "feature_types": [
          "float",
          "float",
          "float",
          "float",
          "float"
        ],
        "label_types": [
          "bool"
        ]
      },
      "key": [
        "id"
      ] 
    }
  ],
  "outputs":[
    {
      "data_path": "output.csv",
      "data_schema_path": "output_schema.json"
    }
  ]
}
"""

TEST_OUTPUT_COLUMNS = [
    "id",
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean compactness",
    "mean concavity",
    "mean concave points",
    "mean symmetry",
    "mean fractal dimension",
    "target",
]

TEST_OUTPUT_VALUE1 = [
    "842302",
    "17.99",
    "10.38",
    "122.8",
    "1001.0",
    "0.1184",
    "0.2776",
    "0.3001",
    "0.1471",
    "0.2419",
    "0.07871",
    "False",
]

TEST_OUTPUT_IDS = ["id"]
TEST_OUTPUT_FEATURES = [
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean compactness",
    "mean concavity",
    "mean concave points",
    "mean symmetry",
    "mean fractal dimension",
]
TEST_OUTPUT_LABELS = ["target"]
TEST_OUTPUT_ID_TYPES = ["int64"]
TEST_OUTPUT_FEATURE_TYPES = [
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
    "float64",
]
TEST_OUTPUT_LABEL_TYPES = ["bool"]

TEST_OUTPUT_PATH = "output.csv"
TEST_OUTPUT_SCHEMA_PATH = "output_schema.json"


class UnitTests(unittest.TestCase):
    def test_psi(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        # run
        run_psi(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        # check output result
        with open(TEST_OUTPUT_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        self.assertListEqual(rows[0], TEST_OUTPUT_COLUMNS)
        self.assertListEqual(rows[1], TEST_OUTPUT_VALUE1)
        self.assertEqual(len(rows), 570)
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
