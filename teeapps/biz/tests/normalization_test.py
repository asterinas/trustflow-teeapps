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

import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.normalization.normalization import run_normalization


class UnitTests(unittest.TestCase):
    def test_works(self):
        config_json = """
{
    "component_name": "normalization",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/normalization_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "float",
                    "int",
                    "float"
                ],
                "label_types": []
            },
            "cols": [
                "a",
                "b",
                "c"
            ]
        }
    ],
    "strategies": [
        "standard",
        "max_abs",
        "min_max"
    ],
    "outputs": [
        {
            "data_path": "normalization_output.csv",
            "data_schema_path": "normalization_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("normalization_output.csv"))
        self.assertTrue(not os.path.exists("normalization_output_schema.json"))
        # run
        run_normalization(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("normalization_output.csv"))
        self.assertTrue(os.path.exists("normalization_output_schema.json"))

        df = pd.read_csv("normalization_output.csv")

        print(df)

        for x, y in zip(df["a"].tolist(), [-1.224744871391589, 0, 1.224744871391589]):
            self.assertAlmostEqual(x, y)

        for x, y in zip(df["b"].tolist(), [0.500, 0.875, 1.0]):
            self.assertAlmostEqual(x, y)

        for x, y in zip(df["c"].tolist(), [0, 0.4, 1]):
            self.assertAlmostEqual(x, y)

        absolute_path = os.path.abspath("normalization_output.csv")
        print("Absolute path:", absolute_path)


if __name__ == "__main__":
    unittest.main()
