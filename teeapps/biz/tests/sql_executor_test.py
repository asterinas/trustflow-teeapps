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
from teeapps.biz.sql_executor.sql_executor import run_sql_executor


class UnitTests(unittest.TestCase):
    def test_works(self):
        task_json = """
{
    "component_name": "sql_executor",
    "inputs": [
        {
            "data_path": "teeapps/biz/testdata/test2.csv",
            "schema": {
                "ids": [
                    "id"
                ],
                "features": [
                    "name",
                    "age",
                    "address",
                    "salary"
                ],
                "labels": [],
                "id_types": [
                    "int"
                ],
                "feature_types": [
                    "str",
                    "int",
                    "str",
                    "float"
                ],
                "label_types": []
            }
        }
    ],
    "statements": "select name, age, salary as payment from input_table where salary > 16000.0;",
    "outputs": [
        {
            "data_path": "sql_executor_output.csv",
            "data_schema_path": "sql_executor_output_schema.json"
        }
    ]
}
        """

        # before
        self.assertTrue(not os.path.exists("sql_executor_output.csv"))
        # run
        run_sql_executor(json.loads(task_json))
        # after
        self.assertTrue(os.path.exists("sql_executor_output.csv"))

        absolute_path = os.path.abspath("sql_executor_output.csv")
        print("Absolute path:", absolute_path)

        with open("sql_executor_output.csv", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]

        self.assertEqual(len(rows), 3)

        self.assertListEqual(
            rows[0],
            [
                "name",
                "age",
                "payment",
            ],
        )

        self.assertListEqual(
            rows[1],
            ["Paul", "13", "20000.0"],
        )

        self.assertListEqual(
            rows[2],
            ["teddy", "5", "20000.0"],
        )


if __name__ == "__main__":
    unittest.main()
