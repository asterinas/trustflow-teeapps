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
from teeapps.biz.lr.lr import run_lr
from teeapps.proto.params import lr_hyper_params_pb2
import joblib


TEST_CONFIG_JSON = """
{
  "appType": "OP_LR",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.LrHyperParams",
    "regression_type": "logistic",
    "max_iter": 100,
    "l2_norm": 1.0,
    "tol": 0.0001,
    "penalty": "l2"
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
    }
  ],
  "outputs": [
    {
      "dataPath": "output.pkl",
      "dataSchemaPath": "output_schema.json"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "output.pkl"

TEST_OUTPUT_VALUE = [
    0.2139465994363956,
    0.19650825387437637,
    0.012937520624820096,
    -0.299530984420093,
]


class UnitTests(unittest.TestCase):
    def test_lr(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_lr(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))

        model = joblib.load(TEST_OUTPUT_PATH)
        self.assertListEqual(TEST_OUTPUT_VALUE, model.coef_.tolist()[0])


if __name__ == "__main__":
    unittest.main()
