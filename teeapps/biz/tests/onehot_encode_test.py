# Copyright 2024 Ant Group Co., Ltd.
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

from teeapps.biz.onehot_encode.onehot_encode import run_onehot_encode
from teeapps.biz.onehot_substitution.onehot_substitution import run_onehot_substitution


class UnitTests(unittest.TestCase):
    def test_works(self):
        encode_task_json = """
{
    "component_name": "onehot_encode",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/onehot_encode_input.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "性别",
                    "地区"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "str"
                ],
                "label_types": []
            },
            "cols": [
                "性别",
                "地区"
            ]
        }
    ],
    "outputs": [
        {
            "data_path": "onehot_encode_rules.json"
        }
    ]
}
        """

        # before
        self.assertTrue(not os.path.exists("onehot_encode_rules.json"))
        # run
        run_onehot_encode(json.loads(encode_task_json))
        # after
        self.assertTrue(os.path.exists("onehot_encode_rules.json"))

        # absolute_path = os.path.abspath("onehot_encode_rules.json")
        # print("Absolute path:", absolute_path)

        sub_task_json = """
{
    "component_name": "onehot_substitution",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/onehot_encode_input.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "性别",
                    "地区"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "str"
                ],
                "label_types": []
            },
            "cols": [
                "性别",
                "地区"
            ]
        },
        {
            "data_path": "onehot_encode_rules.json"
        }
    ],
    "outputs": [
        {
            "data_path": "onehot_encode_output.csv",
            "data_schema_path": "onehot_encode_output_schema.json"
        }
    ]
}
        """

        # before
        self.assertTrue(not os.path.exists("onehot_encode_output.json"))
        # run
        run_onehot_substitution(json.loads(sub_task_json))
        # after
        self.assertTrue(os.path.exists("onehot_encode_output.csv"))

        # absolute_path = os.path.abspath("onehot_encode_output.csv")
        # print("Absolute path:", absolute_path)

        with open("onehot_encode_output.csv", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]

            # print(rows)
        self.assertListEqual(
            rows[0],
            [
                "id",
                "性别_女",
                "性别_男",
                "性别_nan",
                "地区_东北",
                "地区_华东",
                "地区_华中",
                "地区_华北",
                "地区_华南",
                "地区_西南",
            ],
        )

        self.assertListEqual(
            rows[1],
            [
                "1",
                "False",
                "True",
                "False",
                "False",
                "False",
                "True",
                "False",
                "False",
                "False",
            ],
        )


if __name__ == "__main__":
    unittest.main()
