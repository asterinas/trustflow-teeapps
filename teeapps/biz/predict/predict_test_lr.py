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
from teeapps.biz.predict.predict import run_predict

from teeapps.proto.params import predict_pb2
from secretflow.spec.v1 import data_pb2


TEST_CONFIG_JSON = """
{
  "appType": "OP_PREDICT",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.PredictionParams",
    "output_control": {
        "output_id": true,
        "id_field_name": "ID",
        "output_label": true,
        "label_field_name": "label",
        "score_field_name": "predict",
	"col_names" : ["AT"]
    }
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test5.csv",
      "schema": {
        "ids": ["PE"],
        "features": ["AT", "V", "AP", "RH"],
        "labels": ["RE"],
        "id_types": ["float"],
        "feature_types": ["float", "float", "float", "float"],
        "label_types": ["float"]
      }
    },
    {
      "dataPath": "teeapps/biz/testdata/lr.pkl"
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


TEST_OUTPUT_PATH = "output.csv"
TEST_OUTPUT_SCHEMA_PATH = "output_schema.json"

TEST_OUTPUT_VALUES = ["0.999396", "1.0", "445.75", "23.64"]
TEST_OUTPUT_COLUMNS = ["predict", "label", "ID", "AT"]

TEST_OUTPUT_IDS = ["ID"]
TEST_OUTPUT_FEATURES = ["AT"]
TEST_OUTPUT_LABELS = ["predict", "label"]
TEST_OUTPUT_ID_TYPES = ["float64"]
TEST_OUTPUT_FEATURE_TYPES = ["float64"]
TEST_OUTPUT_LABEL_TYPES = ["float64", "float64"]


class UnitTests(unittest.TestCase):
    def test_predict(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(not os.path.exists(TEST_OUTPUT_SCHEMA_PATH))
        # run
        run_predict(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))
        self.assertTrue(os.path.exists(TEST_OUTPUT_SCHEMA_PATH))

        # check output data
        with open(TEST_OUTPUT_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        self.assertEqual(len(rows), 6)
        self.assertListEqual(rows[2], TEST_OUTPUT_VALUES)

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
