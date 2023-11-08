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
from teeapps.biz.woe_binning.woe_binning import run_woe_binning
from teeapps.proto.params import woe_binning_pb2


TEST_CONFIG_JSON = """
{
  "appType": "OP_WOE_BINNING",
  "params": {
    "@type": "type.googleapis.com/teeapps.params.WoeBinningParams",
    "positive_label": "1",
    "feature_binning_confs": [{
      "binning_method": "quantile",
      "n_divide": 10
    }],
    "feature_selects": [
      "AT", "V", "AP", "RH"
    ]
  },
  "inputs": [
    {
      "dataPath": "teeapps/biz/testdata/test5.csv",
      "schema": {
        "ids": [],
        "features": ["AT", "V", "AP", "RH", "PE"],
        "labels": ["RE"],
        "id_types": [],
        "feature_types": ["float", "float", "float", "float", "float"],
        "label_types": ["float"]
      }
    }
  ],
  "outputs": [
    {
      "dataPath": "woe_rule.json"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "woe_rule.json"


class UnitTests(unittest.TestCase):
    def test_woe(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        run_woe_binning(TEST_CONFIG_JSON)
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))

        with open(TEST_OUTPUT_PATH, "r") as output_f:
            output_json = output_f.read()

        rule = woe_binning_pb2.WoeBinningRule()
        json_format.Parse(output_json, rule)


if __name__ == "__main__":
    unittest.main()
