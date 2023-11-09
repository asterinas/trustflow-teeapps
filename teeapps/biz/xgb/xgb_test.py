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


import os
import unittest

from google.protobuf import json_format
from teeapps.biz.xgb.xgb import run_xgb

TEST_CONFIG_JSON = """
{
  "appType": "OP_XGB",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.XgbHyperParams",
    "num_boost_round": 10,
    "max_depth": 5,
    "max_leaves": 0,
    "seed": 42,
    "learning_rate": 0.3,
    "lambda": 1.0,
    "gamma": 0,
    "colsample_bytree": 1.0,
    "base_score": 0.5,
    "min_child_weight": 1,
    "objective": "binary:logistic",
    "alpha": 0,
    "subsample": 1.0,
    "max_bin": 10,
    "tree_method": "auto",
    "booster": "gbtree"
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
        "label_types":[
          "int64"
        ]
      }
    }
  ],
  "outputs": [
    {
      "dataPath": "model.dat"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "model.dat"


class UnitTests(unittest.TestCase):
    def test_xgb(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_xgb(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))


if __name__ == "__main__":
    unittest.main()
