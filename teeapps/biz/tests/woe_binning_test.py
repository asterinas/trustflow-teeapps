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

import teeapps.biz.woe_binning.woe_binning as woe_binning

TEST_CONFIG_JSON = """
{
  "component_name": "woe_binning",
  "binning_method": "quantile",
  "positive_label": "1",
  "bin_num": 3,
  "inputs": [
    {
      "data_path": "teeapps/biz/testdata/test5.csv",
      "schema": {
        "ids": [],
        "features": ["AT", "V", "AP", "RH", "PE"],
        "labels": ["RE"],
        "id_types": [],
        "feature_types": ["float", "float", "float", "float", "float"],
        "label_types": ["bool"]
      },
      "feature_selects":["AT", "V", "AP", "RH"]
    }
  ],
  "outputs": [
    {
      "data_path": "woe_rules.json"
    }
  ]
}
"""


TEST_OUTPUT_PATH = "woe_rules.json"


class UnitTests(unittest.TestCase):
    def test_woe(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_PATH))
        # run
        woe_binning.run_woe_binning(json.loads(TEST_CONFIG_JSON))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_PATH))

        with open(TEST_OUTPUT_PATH, "r") as output_f:
            rules = json.load(output_f)
        self.assertEqual(len(rules), 4)
        self.assertEqual(len(rules[0][woe_binning.BINS]), 3)
        self.assertEqual(rules[0][woe_binning.BINS][0][woe_binning.RIGHT], 14.223)
        self.assertEqual(
            rules[0][woe_binning.BINS][0][woe_binning.WOE], -1.5404450409471488
        )


if __name__ == "__main__":
    unittest.main()
