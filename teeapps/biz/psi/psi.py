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
import logging
import math
import os
import sys
from concurrent import futures

import pandas
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.common import common

COMPONENT_NAME = "psi"

KEY = "key"

DEFAULT_FILE_SIZE_LIMIT_IN_BYTES = 200 * 1024 * 1024


def run_psi_part(file_list: list, inputs: dict, join_keys: list) -> pandas.DataFrame:
    logging.info("Joining input data...")

    # read left dataframe
    left_df = common.gen_data_frame(inputs[0], file_list[0])
    col_type = ",".join(f"{col}:{left_df[col].dtype}" for col in left_df.columns)
    logging.info(f"Left dataframe's column types are {col_type}")

    # join right df one by one
    for i in range(1, len(inputs)):
        # read right dataframe
        right_df = common.gen_data_frame(inputs[i], file_list[i])
        col_type = ",".join(f"{col}:{right_df[col].dtype}" for col in right_df.columns)
        logging.info(f"Right dataframe's column types are {col_type}")

        assert len(join_keys[0]) == len(
            join_keys[i]
        ), "Join keys should be the same size"

        left_df = left_df.merge(right_df, left_on=join_keys[0], right_on=join_keys[i])
        key_type = ",".join(f"{col}:{left_df[col].dtype}" for col in left_df.columns)
        logging.info(f"Joined dataframe's column types are {key_type}")

    return left_df


# Todo(jimi): for TEE, psi may not be a good name, rename later
def run_psi(task_config: dict) -> None:
    logging.info("Running psi...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]
    assert 1 < len(inputs) <= 10, f"{COMPONENT_NAME} should have [2,10] inputs"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # eg.[["id", "name"], ["ID", "NAME"]]
    join_keys = [input[KEY] for input in inputs]

    # merge and store input schema
    merged_schema = data_pb2.TableSchema()
    for input in inputs:
        common.append_table_schema(merged_schema, input[common.SCHEMA])

    files_size = [os.path.getsize(input[common.DATA_PATH]) for input in inputs]

    file_num = math.ceil(max(files_size) / DEFAULT_FILE_SIZE_LIMIT_IN_BYTES)

    logging.info(f"Inputs can be split into {file_num} files")

    # split bigfile into small files
    with futures.ThreadPoolExecutor() as executor:
        small_files = list(
            executor.map(
                lambda x: common.split_bigfile_into_smallfiles(*x),
                [
                    (inputs[index], join_keys[index], file_num)
                    for index in range(len(inputs))
                ],
            )
        )

    # deal every small file
    # dump output
    logging.info("Dumping part output...")
    output_path = outputs[0][common.DATA_PATH]
    if os.path.exists(output_path):
        os.remove(output_path)
    # df is used to get data schema
    df = pandas.DataFrame()
    has_head = False

    # task executor parallelly
    with futures.ThreadPoolExecutor() as executor:
        df_list = list(
            executor.map(
                lambda x: run_psi_part(*x),
                [
                    (
                        [files[index] for files in small_files],
                        inputs,
                        join_keys,
                    )
                    for index in range(file_num)
                ],
            )
        )

    # delete small files
    with futures.ThreadPoolExecutor() as executor:
        executor.map(
            os.remove,
            [file for files in small_files if len(files) > 1 for file in files],
        )

    logging.info("Dumping output dataframe...")
    # get task result parallelly
    for part_df in df_list:
        df = part_df
        df.to_csv(output_path, index=False, mode="a", header=not has_head)
        has_head = True if not has_head else has_head

    logging.info("Dumping output schema...")
    # gen output TableSchema
    output_schema = common.gen_output_schema(df, merged_schema)
    schema_json = json_format.MessageToJson(output_schema)
    with open(outputs[0][common.DATA_SCHEMA_PATH], "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    task_config_path = sys.argv[1]
    logging.info("Reading task config file...")
    with open(task_config_path, "r") as task_config_f:
        task_config = json.load(task_config_f)
        logging.debug(f"Configurations: {task_config}")
        run_psi(task_config)


"""
This app is expected to be launched by app framework via running a subprocess 
`python3 psi.py config`. Before launching the subprocess, the app framework will 
firstly generate a config file which is a json file containing all the required 
parameters and is serialized from the task.proto. Currently we do not handle any 
errors/exceptions in this file as the outer app framework will capture the stderr 
and stdout.
"""
if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
