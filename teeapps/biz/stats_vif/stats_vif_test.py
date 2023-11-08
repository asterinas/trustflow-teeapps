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


import json
import os
import unittest

from google.protobuf import json_format
from teeapps.biz.stats_vif.stats_vif import run_stats_vif
from teeapps.proto.params import vif_params_pb2
from secretflow.spec.v1.component_pb2 import Attribute
from secretflow.spec.v1.report_pb2 import Descriptions, Div, Report, Tab

TEST_OUTPUT_REPORT_PATH = "task.report"


class UnitTests(unittest.TestCase):
    def test_stats_vif(self):
        # before
        self.assertTrue(not os.path.exists(TEST_OUTPUT_REPORT_PATH))

        config = {
            "app_type": "OP_STATS_VIF",
            "params": {
                "@type": "type.googleapis.com/teeapps.params.VifParams",
                "feature_selects": ["SALARY", "AGE"],
            },
            "inputs": [
                {
                    "data_path": "teeapps/biz/testdata/dataset1/data.csv",
                    "schema": {
                        "ids": ["ID", "NAME"],
                        "features": ["AGE", "ADDRESS", "SALARY"],
                        "id_types": ["int32", "str"],
                        "feature_types": ["float", "str", "float"],
                    },
                }
            ],
            "outputs": [{"data_path": TEST_OUTPUT_REPORT_PATH}],
        }

        # run
        run_stats_vif(json.dumps(config))
        # after
        self.assertTrue(os.path.exists(TEST_OUTPUT_REPORT_PATH))
        # check output report
        with open(TEST_OUTPUT_REPORT_PATH, "r") as report_f:
            report_json = report_f.read()
        report = Report()
        json_format.Parse(report_json, report)
        self.assertEqual(len(report.tabs[0].divs[0].children[0].descriptions.items), 2)
        self.assertEqual(
            report.tabs[0].divs[0].children[0].descriptions.items[0].value.f,
            4.199999809265137,
        )

    def test_stats_vif_none_value(self):
        # before
        config = {
            "app_type": "OP_STATS_VIF",
            "params": {
                "@type": "type.googleapis.com/teeapps.params.VifParams",
                "feature_selects": ["SALARY", "AGE"],
            },
            "inputs": [
                {
                    "data_path": "teeapps/biz/testdata/dataset1/data_with_none.csv",
                    "schema": {
                        "ids": ["ID", "NAME"],
                        "features": ["AGE", "ADDRESS", "SALARY"],
                        "id_types": ["int32", "str"],
                        "feature_types": ["float", "str", "float"],
                    },
                }
            ],
            "outputs": [{"data_path": TEST_OUTPUT_REPORT_PATH}],
        }

        # run
        with self.assertRaises(AssertionError):
            run_stats_vif(json.dumps(config))


if __name__ == "__main__":
    unittest.main()
