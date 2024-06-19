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

import joblib
from google.protobuf import json_format

from teeapps.biz.lr.lr import run_lr

TEST_CONFIG_JSON = """
{
  "component_name": "lr_train",
  "max_iter": 100,
  "reg_type": "logistic",
  "l2_norm": 1.0,
  "tol": 1e-4,
  "penalty": "l2",
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
      "data_path": "lr.model"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "lr.model"


class UnitTests(unittest.TestCase):
    def test_lr(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_lr(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))


if __name__ == "__main__":
    unittest.main()
