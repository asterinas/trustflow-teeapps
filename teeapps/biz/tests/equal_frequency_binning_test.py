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

from teeapps.biz.equal_frequency_binning.equal_frequency_binning import (
    run_equal_frequency_binning,
)
from teeapps.biz.equal_frequency_substitution.equal_frequency_substitution import (
    run_equal_frequency_substitution,
)


class UnitTests(unittest.TestCase):
    def test_works(self):
        encode_task_json = """
{
    "component_name": "equal_frequency_binning",
    "bin_num": 4,
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/equal_frequency_binning_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "value"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "int"
                ],
                "label_types": []
            },
            "feature_selects": [
                "value"
            ]
        }
    ],
    "outputs": [
        {
            "data_path": "equal_frequency_binning_rules.json"
        },
        {
            "data_path": "equal_frequency_binning_report.json"
        }
    ]
}
        """

        # before
        self.assertTrue(not os.path.exists("equal_frequency_binning_rules.json"))
        self.assertTrue(not os.path.exists("equal_frequency_binning_report.json"))
        # run
        run_equal_frequency_binning(json.loads(encode_task_json))
        # after
        self.assertTrue(os.path.exists("equal_frequency_binning_rules.json"))
        self.assertTrue(os.path.exists("equal_frequency_binning_report.json"))

        absolute_path = os.path.abspath("equal_frequency_binning_rules.json")
        print("Absolute path:", absolute_path)

        sub_task_json = """
{
    "component_name": "equal_frequency_substitution",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/equal_frequency_binning_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "value"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "int"
                ],
                "label_types": []
            },
            "feature_selects": [
                "value"
            ]
        },
        {
            "data_path": "equal_frequency_binning_rules.json"
        }
    ],
    "outputs": [
        {
            "data_path": "equal_frequency_binning_output.csv",
            "data_schema_path": "equal_frequency_binning_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("equal_frequency_binning_output.csv"))
        self.assertTrue(
            not os.path.exists("equal_frequency_binning_output_schema.json")
        )
        # run
        run_equal_frequency_substitution(json.loads(sub_task_json))
        # after
        self.assertTrue(os.path.exists("equal_frequency_binning_output.csv"))
        self.assertTrue(os.path.exists("equal_frequency_binning_output_schema.json"))

        absolute_path = os.path.abspath("equal_frequency_binning_output.csv")
        print("Absolute path:", absolute_path)

        target_column = "value"

        with open(
            "equal_frequency_binning_output.csv", newline="", encoding="utf-8"
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            actual_values = [int(row[target_column]) for row in reader]

        self.assertListEqual(
            actual_values,
            [0, 0, 1, 2, 3],
        )


if __name__ == "__main__":
    unittest.main()
