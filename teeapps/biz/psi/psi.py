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


import logging
import os
import sys

import pandas
from google.protobuf import json_format
from concurrent import futures

# The following packages will be generated automatically by scripts
# when building occlum workspace
from teeapps.proto import task_pb2
from teeapps.biz.common import common
from teeapps.proto.params import psi_pb2
from secretflow.spec.v1 import data_pb2


def run_psi_part(
    file_list: list, task_config: task_pb2.TaskConfig, join_keys: list
) -> pandas.DataFrame:
    logging.info("Joining input data...")
    # read id field for left
    left_df = common.gen_data_frame(
        task_config.inputs[0], file_list[0], usecols=join_keys[0]
    )
    key_type = ",".join(f"{col}:{left_df[col].dtype}" for col in join_keys[0])
    logging.info(f"KeyTypes are {key_type}")

    # get join value of id field one by one
    for i in range(1, len(task_config.inputs)):
        # read id field for right
        right_df = common.gen_data_frame(
            task_config.inputs[i], file_list[i], usecols=join_keys[i]
        )
        key_type = ",".join(f"{col}:{right_df[col].dtype}" for col in join_keys[i])
        logging.info(f"KeyTypes are {key_type}")
        assert len(join_keys[0]) == len(
            join_keys[i]
        ), "Join keys should be the same size"

        # if left_df.id_fields != right_df.id_fields,
        # then merge will get all id_fields in left_df or in right_df
        # so just get the value for id_fields in left_df
        left_df = left_df.merge(right_df, left_on=join_keys[0], right_on=join_keys[i])[
            join_keys[0]
        ]

    join_idfields_df = left_df
    logging.debug(f"id fields df {join_idfields_df}")
    # join data on columns not in id field
    left_df = common.read_csv_file(
        task_config.inputs[0], join_keys[0], file_list[0], join_idfields_df
    )
    key_type = ",".join(f"{col}:{left_df[col].dtype}" for col in join_keys[0])
    logging.info(f"KeyTypes are {key_type}")

    for i in range(1, len(task_config.inputs)):
        # modify columns name to be the same as id fields
        join_idfields_df.columns = join_keys[i]

        right_df = common.read_csv_file(
            task_config.inputs[i], join_keys[i], file_list[i], join_idfields_df
        )
        key_type = ",".join(f"{col}:{right_df[col].dtype}" for col in join_keys[i])
        logging.info(f"KeyTypes are {key_type}")
        assert len(join_keys[0]) == len(
            join_keys[i]
        ), "Join keys should be the same size"

        left_df = left_df.merge(right_df, left_on=join_keys[0], right_on=join_keys[i])
    return left_df


# Todo(jimi): for TEE, psi may not be a good name, rename later
def run_psi(config_json: str) -> None:
    logging.info("Running psi...")

    task_config = task_pb2.TaskConfig()
    json_format.Parse(config_json, task_config)
    assert task_config.app_type == "OP_PSI", "App type is not 'OP_PSI'"
    assert 1 < len(task_config.inputs) <= 10, "PSI should has [2,10] inputs"
    assert len(task_config.outputs) == 1, "PSI should has only 1 output"

    params = psi_pb2.PsiParams()
    task_config.params.Unpack(params)
    # eg.[["id", "name"], ["ID", "NAME"]]
    join_keys = [list(psi_key.keys) for psi_key in params.psi_keys]

    # merge and store input schema
    merged_schema = data_pb2.TableSchema()
    for input in task_config.inputs:
        common.append_table_schema(merged_schema, input)

    # prepare
    # change col type: str to float if possible
    with futures.ThreadPoolExecutor() as executor:
        file_id_fields_size = list(
            executor.map(common.format_file_schema, task_config.inputs, join_keys)
        )
    # split bigfile into small files
    with futures.ThreadPoolExecutor() as executor:
        small_files = list(
            executor.map(
                lambda x: common.split_bigfile_into_smallfiles(*x),
                [
                    (
                        task_config.inputs[index],
                        join_keys[index],
                        None,
                        file_id_fields_size[index],
                    )
                    for index in range(len(task_config.inputs))
                ],
            )
        )

    small_files_size = min([len(files) for files in small_files])
    logging.info(f"small file batch is {small_files_size}")

    # deal every small file
    # dump output
    logging.info("Dumping part output...")
    output_path = task_config.outputs[0].data_path
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
                    ([files[index] for files in small_files], task_config, join_keys)
                    for index in range(small_files_size)
                ],
            )
        )
    # get task result parallelly
    for part_df in df_list:
        df = part_df
        df.to_csv(output_path, index=False, mode="a", header=not has_head)
        has_head = True if not has_head else has_head

    logging.info("Dumping output schema...")
    # gen output TableSchema
    merged_schema = common.gen_output_schema(df, merged_schema)
    schema_json = json_format.MessageToJson(merged_schema)
    with open(task_config.outputs[0].data_schema_path, "w") as schema_f:
        schema_f.write(schema_json)


def main():
    assert len(sys.argv) == 2, f"Wrong arguments number: {len(sys.argv)}"
    # load task_config json
    config_path = sys.argv[1]
    logging.info("Reading config file...")
    with open(config_path, "r") as config_f:
        config_json = config_f.read()
        logging.debug(f"Configurations: {config_json}")
        run_psi(config_json)


"""
This app is expected to be launched by app framework via running a subprocess
`python3 psi.py config`. Before launching the subprocess, the app framework will
firstly generate a config file which is a json file containing all the required
parameters and is serialized from the task.proto. Currently we do not handle any
errors/exceptions in this file as the outer app framework will capture the stderr
and stdout.
"""
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
