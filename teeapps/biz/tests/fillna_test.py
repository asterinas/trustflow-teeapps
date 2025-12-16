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
from teeapps.biz.fillna.fillna import run_fillna


class UnitTests(unittest.TestCase):
    def test_str_constant(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "a"
            ]
        }
    ],
    "strategy": "constant",
    "constant_str": "haha",
    "outputs": [
        {
            "data_path": "test_str_constant_output.csv",
            "data_schema_path": "test_str_constant_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_str_constant_output.csv"))
        self.assertTrue(not os.path.exists("test_str_constant_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_str_constant_output.csv"))
        self.assertTrue(os.path.exists("test_str_constant_output_schema.json"))

        df = pd.read_csv("test_str_constant_output.csv", usecols=["a"])
        print(df["a"].tolist())
        self.assertListEqual(df["a"].tolist(), ["haha", "a", "b", "haha", "c"])

        absolute_path = os.path.abspath("test_str_constant_output.csv")
        print("Absolute path:", absolute_path)

    def test_int_max(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "b"
            ]
        }
    ],
    "strategy": "max",
    "outputs": [
        {
            "data_path": "test_int_max_output.csv",
            "data_schema_path": "test_int_max_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_int_max_output.csv"))
        self.assertTrue(not os.path.exists("test_int_max_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_int_max_output.csv"))
        self.assertTrue(os.path.exists("test_int_max_output_schema.json"))

        df = pd.read_csv("test_int_max_output.csv")
        self.assertListEqual(df["b"].tolist(), [1, 3, 2, 3, 3])

        absolute_path = os.path.abspath("test_int_max_output.csv")
        print("Absolute path:", absolute_path)

    def test_float_min(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "c"
            ]
        }
    ],
    "strategy": "min",
    "outputs": [
        {
            "data_path": "test_float_min_output.csv",
            "data_schema_path": "test_float_min_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_float_min_output.csv"))
        self.assertTrue(not os.path.exists("test_float_min_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_float_min_output.csv"))
        self.assertTrue(os.path.exists("test_float_min_output_schema.json"))

        df = pd.read_csv("test_float_min_output.csv")
        self.assertListEqual(df["c"].tolist(), [0.3, 1.2, -2.3, -2.3, 10.0])

        absolute_path = os.path.abspath("test_float_min_output.csv")
        print("Absolute path:", absolute_path)

    def test_bool_mode(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "d"
            ]
        }
    ],
    "strategy": "mode",
    "outputs": [
        {
            "data_path": "test_bool_mode_output.csv",
            "data_schema_path": "test_bool_mode_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_bool_mode_output.csv"))
        self.assertTrue(not os.path.exists("test_bool_mode_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_bool_mode_output.csv"))
        self.assertTrue(os.path.exists("test_bool_mode_output_schema.json"))

        df = pd.read_csv("test_bool_mode_output.csv")
        self.assertListEqual(df["d"].tolist(), [False, True, False, False, False])

        absolute_path = os.path.abspath("test_bool_mode_output.csv")
        print("Absolute path:", absolute_path)

    def test_int_median(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "b"
            ]
        }
    ],
    "strategy": "median",
    "outputs": [
        {
            "data_path": "test_int_median_output.csv",
            "data_schema_path": "test_int_median_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_int_median_output.csv"))
        self.assertTrue(not os.path.exists("test_int_median_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_int_median_output.csv"))
        self.assertTrue(os.path.exists("test_int_median_output_schema.json"))

        df = pd.read_csv("test_int_median_output.csv")
        self.assertListEqual(df["b"].tolist(), [1, 2, 2, 2, 3])

        absolute_path = os.path.abspath("test_int_median_output.csv")
        print("Absolute path:", absolute_path)

    def test_int_mean(self):
        config_json = """
{
    "component_name": "fillna",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/fillna_testdata.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "a",
                    "b",
                    "c",
                    "d"
                ],
                "labels": [],
                "id_types": [
                    "int64"
                ],
                "feature_types": [
                    "str",
                    "int64",
                    "float",
                    "bool"
                ],
                "label_types": []
            },
            "col": [
                "id"
            ]
        }
    ],
    "strategy": "constant",
    "constant_int64": 0,
    "outputs": [
        {
            "data_path": "test_int_mean_output.csv",
            "data_schema_path": "test_int_mean_output_schema.json"
        }
    ]
}
        """
        # before
        self.assertTrue(not os.path.exists("test_int_mean_output.csv"))
        self.assertTrue(not os.path.exists("test_int_mean_output_schema.json"))
        # run
        run_fillna(json.loads(config_json))
        # after
        self.assertTrue(os.path.exists("test_int_mean_output.csv"))
        self.assertTrue(os.path.exists("test_int_mean_output_schema.json"))

        # df = pd.read_csv("test_int_mean_output.csv")
        # self.assertListEqual(df["b"].tolist(), [1, 2, 2, 2, 3])

        absolute_path = os.path.abspath("test_int_mean_output.csv")
        print("Absolute path:", absolute_path)


if __name__ == "__main__":
    unittest.main()
