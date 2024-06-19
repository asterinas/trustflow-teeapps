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

from teeapps.biz.xgb.xgb import run_xgb

TEST_CONFIG_JSON = """
{
  "component_name": "xgb_train",
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
  "booster": "gbtree",
  "inputs": [
    {
      "data_path": "teeapps/biz/testdata/breast_cancer/breast_cancer.csv",
      "schema": {
        "ids": [
          "id"
        ],
        "features": [
          "mean radius",
          "mean texture",
          "mean perimeter",
          "mean area",
          "mean smoothness",
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
          "float",
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
      "ids": ["id"],
      "label": ["target"]
    }
  ],
  "outputs": [
    {
      "data_path": "xgb.model"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "xgb.model"


class UnitTests(unittest.TestCase):
    def test_xgb(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_xgb(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))


if __name__ == "__main__":
    unittest.main()
