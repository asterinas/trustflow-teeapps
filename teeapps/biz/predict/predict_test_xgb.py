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
      "col_names": [
        "Slope"
      ]
    }
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test3.csv",
      "schema": {
        "ids": [
          "Id"
        ],
        "features": [
          "Elevation",
          "Aspect",
          "Slope",
          "Horizontal_Distance_To_Hydrology",
          "Vertical_Distance_To_Hydrology",
          "Horizontal_Distance_To_Roadways",
          "Hillshade_9am",
          "Hillshade_Noon",
          "Hillshade_3pm",
          "Horizontal_Distance_To_Fire_Points",
          "Wilderness_Area1",
          "Wilderness_Area2",
          "Wilderness_Area3",
          "Wilderness_Area4",
          "Soil_Type1",
          "Soil_Type2",
          "Soil_Type3",
          "Soil_Type4",
          "Soil_Type5",
          "Soil_Type6",
          "Soil_Type7",
          "Soil_Type8",
          "Soil_Type9",
          "Soil_Type10",
          "Soil_Type11",
          "Soil_Type12",
          "Soil_Type13",
          "Soil_Type14",
          "Soil_Type15",
          "Soil_Type16",
          "Soil_Type17",
          "Soil_Type18",
          "Soil_Type19",
          "Soil_Type20",
          "Soil_Type21",
          "Soil_Type22",
          "Soil_Type23",
          "Soil_Type24",
          "Soil_Type25",
          "Soil_Type26",
          "Soil_Type27",
          "Soil_Type28",
          "Soil_Type29",
          "Soil_Type30",
          "Soil_Type31",
          "Soil_Type32",
          "Soil_Type33",
          "Soil_Type34",
          "Soil_Type35",
          "Soil_Type36",
          "Soil_Type37",
          "Soil_Type38",
          "Soil_Type39",
          "Soil_Type40"
        ],
        "labels": [
          "Cover_Type"
        ],
        "id_types": [
          "int64"
        ],
        "feature_types": [
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64",
          "int64"
        ],
        "label_types": [
          "int64"
        ]
      }
    },
    {
      "dataPath": "teeapps/biz/testdata/xgb.pkl"
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

TEST_OUTPUT_IDS = ["ID"]
TEST_OUTPUT_FEATURES = ["Slope"]
TEST_OUTPUT_LABELS = ["predict", "label"]
TEST_OUTPUT_ID_TYPES = ["int64"]
TEST_OUTPUT_FEATURE_TYPES = ["int64"]
TEST_OUTPUT_LABEL_TYPES = ["float32", "int64"]


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
        self.assertEqual(len(rows), 15121)

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
