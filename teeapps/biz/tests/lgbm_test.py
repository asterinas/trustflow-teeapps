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

from teeapps.biz.lgbm.lgbm import run_lgbm

TEST_CONFIG_JSON = """
{
  "component_name": "lgbm_train",
  "n_estimators": 10,
  "objective": "binary",
  "boosting_type": "gbdt",
  "num_leaves": 15,
  "learning_rate": 0.1,
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
      "data_path": "lgbm_bin_class.model"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "lgbm_bin_class.model"


class UnitTests(unittest.TestCase):
    def test_lgbm(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_lgbm(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))


if __name__ == "__main__":
    unittest.main()
