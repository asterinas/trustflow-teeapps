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
import logging
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from time import perf_counter
from typing import Dict, List, Tuple

import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2

from teeapps.biz.common import common

COMPONENT_NAME = "psi"

KEY = "key"

DEFAULT_FILE_SIZE_LIMIT_IN_BYTES = 200 * 1024 * 1024


class CSVColumnManager:
    @staticmethod
    def get_header_map(file_path: str) -> Tuple[List[str], Dict[str, List[int]]]:
        """获取列名映射表和重复列名统计"""
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)

        name_indices = defaultdict(list)
        for idx, name in enumerate(header):
            name_indices[name.strip().lower()].append(idx)

        return header, name_indices

    @staticmethod
    def resolve_column_names(
        names: List[str], name_indices: Dict[str, List[int]], file_path: str
    ) -> List[int]:
        """将列名解析为索引，处理各种异常情况"""
        resolved = []
        for name in names:
            normalized = name.strip().lower()
            indices = name_indices.get(normalized, [])

            if not indices:
                raise ValueError(f"列名 '{name}' 在文件 {file_path} 中不存在")
            if len(indices) > 1:
                raise ValueError(
                    f"列名 '{name}' 在文件 {file_path} 中存在多个（索引：{indices}）"
                )

            resolved.append(indices[0])
        return resolved


class CSVFullMergeProcessor:
    def __init__(
        self,
        file1: str,
        file2: str,
        keys1: List[str],
        keys2: List[str],
        output: str = "merged.csv",
    ):
        self.file1 = file1
        self.file2 = file2
        self.keys1 = keys1
        self.keys2 = keys2
        self.output = output

        # 解析文件结构
        self.header1, self.key_indices1 = self._resolve_columns(file1, keys1)
        self.header2, self.key_indices2 = self._resolve_columns(file2, keys2)

        # 计算第二个文件的非键列索引
        self.non_key_indices2 = [
            idx for idx in range(len(self.header2)) if idx not in self.key_indices2
        ]

    def _resolve_columns(
        self, file_path: str, key_names: List[str]
    ) -> Tuple[List[str], List[int]]:
        """解析文件列结构"""
        header, name_indices = CSVColumnManager.get_header_map(file_path)
        resolved_indices = CSVColumnManager.resolve_column_names(
            key_names, name_indices, file_path
        )
        return header, resolved_indices

    def _build_sort_command(
        self, input_file: str, key_indices: List[int], output_file: str
    ) -> str:
        """构建多键排序命令"""
        sort_keys = " ".join([f"-k{idx+1},{idx+1}" for idx in key_indices])
        return (
            f"(head -n 1 {input_file} && "
            f"tail -n +2 {input_file} | "
            f"grep -v '^[[:space:]]*$' | "
            f"sort -t, {sort_keys}  --parallel=8 --buffer-size=1G --stable ) > {output_file}"
        )

    def _sort_file(
        self, input_file: str, sorted_file: str, key_indices: List[int]
    ) -> str:
        """执行排序并返回排序后文件路径"""
        # sorted_file = f"sorted_{input_file}"
        cmd = self._build_sort_command(input_file, key_indices, sorted_file)

        try:
            subprocess.run(cmd, shell=True, check=True, executable="/bin/bash")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"文件 {input_file} 排序失败: {e}")

    def _compare_rows(self, row1: List[str], row2: List[str]) -> int:
        """比较两个行的键值"""
        for key_idx1, key_idx2 in zip(self.key_indices1, self.key_indices2):
            val1 = row1[key_idx1] if key_idx1 < len(row1) else ""
            val2 = row2[key_idx2] if key_idx2 < len(row2) else ""

            if val1 < val2:
                return -1
            elif val1 > val2:
                return 1
        return 0

    def merge(self):
        """执行合并流程"""
        # 并行排序两个文件

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=True
        ) as temp_sorted_file1, tempfile.NamedTemporaryFile(
            mode="w+", delete=True
        ) as temp_sorted_file2:

            ps1 = perf_counter()

            self._sort_file(self.file1, temp_sorted_file1.name, self.key_indices1)

            ps2 = perf_counter()

            print(f"排序耗时1：{ps2 - ps1} 秒")
            self._sort_file(self.file2, temp_sorted_file2.name, self.key_indices2)

            ps3 = perf_counter()

            print(f"排序耗时2：{ps3 - ps2} 秒")

            # 执行归并合并
            with open(temp_sorted_file1.name) as f1, open(
                temp_sorted_file2.name
            ) as f2, open(self.output, "w", newline="") as out:

                writer = csv.writer(out)
                reader1, reader2 = csv.reader(f1), csv.reader(f2)

                # 构建合并后的标题行
                combined_header = self.header1 + [
                    self.header2[i] for i in self.non_key_indices2
                ]
                writer.writerow(combined_header)

                # 跳过原始标题行
                next(reader1)
                next(reader2)

                def read_next_non_empty(reader):
                    while True:
                        row = next(reader, None)
                        if row is None:
                            return None
                        # 跳过空行（空列表或只包含空字符串的行如 [，，，，]）
                        if row and any(cell.strip() for cell in row):
                            return row

                # 初始化指针
                row1 = read_next_non_empty(reader1)
                row2 = read_next_non_empty(reader2)

                while row1 and row2:
                    cmp = self._compare_rows(row1, row2)

                    if cmp == 0:
                        # 合并第一个文件全列和第二个文件非键列
                        merged_row = row1 + [row2[i] for i in self.non_key_indices2]
                        writer.writerow(merged_row)
                        row1 = read_next_non_empty(reader1)
                        row2 = read_next_non_empty(reader2)
                    elif cmp < 0:
                        row1 = read_next_non_empty(reader1)
                    else:
                        row2 = read_next_non_empty(reader2)


# Todo(jimi): for TEE, psi may not be a good name, rename later
def run_psi(task_config: dict) -> None:
    logging.info("Running psi...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]
    assert len(inputs) == 2, f"{COMPONENT_NAME} should have 2 inputs"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    # eg.[["id", "name"], ["ID", "NAME"]]
    join_keys = [input[KEY] for input in inputs]

    output_path = outputs[0][common.DATA_PATH]
    if os.path.exists(output_path):
        os.remove(output_path)

    merger = CSVFullMergeProcessor(
        file1=inputs[0][common.DATA_PATH],
        file2=inputs[1][common.DATA_PATH],
        keys1=join_keys[0],  # 第一个文件的键列
        keys2=join_keys[1],  # 第二个文件的键列
        output=output_path,
    )

    merger.merge()

    # merge and store input schema
    merged_schema = data_pb2.TableSchema()
    for input in inputs:
        common.append_table_schema(merged_schema, input[common.SCHEMA])

    logging.info("Dumping output schema...")

    # gen output TableSchema
    df = pd.read_csv(output_path, nrows=5)

    output_schema = common.gen_output_schema(df, merged_schema, False, True)
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
