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

from teeapps.biz.chi_squared_binning.chi_squared_binning import run_chi_squared_binning
from teeapps.biz.chi_squared_substitution.chi_squared_substitution import (
    run_chi_squared_substitution,
)


class UnitTests(unittest.TestCase):
    def test_works(self):
        encode_task_json = """
{
    "component_name": "chi_squared_binning",
    "max_bin_num": 2,
    "positive_label": "1",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/chi_squared_binning_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "feature"
                ],
                "labels": [
                    "label"
                ],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "int"
                ],
                "label_types": [
                    "int"
                ]
            },
            "feature_selects": [
                "feature"
            ],
            "label": [
                "label"
            ]
        }
    ],
    "outputs": [
        {
            "data_path": "chi_squared_binning_rules.json"
        },
        {
            "data_path": "chi_squared_binning_report.json"
        }
    ]
}
        """

        # before
        self.assertTrue(not os.path.exists("chi_squared_binning_rules.json"))
        self.assertTrue(not os.path.exists("chi_squared_binning_report.json"))
        # run
        run_chi_squared_binning(json.loads(encode_task_json))
        # after
        self.assertTrue(os.path.exists("chi_squared_binning_rules.json"))
        self.assertTrue(os.path.exists("chi_squared_binning_report.json"))

        absolute_path = os.path.abspath("chi_squared_binning_rules.json")
        print("Absolute path:", absolute_path)

        sub_task_json = """
{
    "component_name": "chi_squared_substitution",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/chi_squared_binning_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "feature"
                ],
                "labels": [
                    "label"
                ],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "int"
                ],
                "label_types": [
                    "int"
                ]
            }
        },
        {
            "data_path": "chi_squared_binning_rules.json"
        }
    ],
    "outputs": [
        {
            "data_path": "chi_squared_substitution_output.csv",
            "data_schema_path": "chi_squared_substitution_output_schema.json"
        },
        {
            "data_path": "chi_squared_substitution_report.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("chi_squared_substitution_output.csv"))
        self.assertTrue(
            not os.path.exists("chi_squared_substitution_output_schema.json")
        )
        # run
        run_chi_squared_substitution(json.loads(sub_task_json))
        # after
        self.assertTrue(os.path.exists("chi_squared_substitution_output.csv"))
        self.assertTrue(os.path.exists("chi_squared_substitution_output_schema.json"))

        absolute_path = os.path.abspath("chi_squared_substitution_output.csv")
        print("Absolute path:", absolute_path)

        with open(
            "chi_squared_substitution_output.csv", newline="", encoding="utf-8"
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            actual_values = [int(row["feature"]) for row in reader]

        self.assertListEqual(
            actual_values,
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        )


if __name__ == "__main__":
    unittest.main()
