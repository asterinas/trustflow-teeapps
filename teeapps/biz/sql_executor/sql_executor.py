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
import logging
import sqlite3
import sys
import tempfile

import pandas as pd
from google.protobuf import json_format
from secretflow.spec.v1 import data_pb2
from teeapps.biz.common import common

COMPONENT_NAME = "sql_executor"
STATEMENTS = "statements"
CHUNK_SIZE = 1024 * 1024
DEFAULT_TABLE = "input_table"


def split_sql_queries(sql_string):
    sql_string = sql_string.strip()

    queries = []

    current_query = []

    in_single_quote = False
    in_double_quote = False

    for char in sql_string:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote

        if char == ";" and not in_single_quote and not in_double_quote:
            current_query.append(char)
            query = "".join(current_query).strip()
            if query:
                queries.append(query)
            current_query = []
        else:
            current_query.append(char)

    if current_query:
        query = "".join(current_query).strip()
        if query:
            queries.append(query)

    return queries


def run_sql_executor(task_config: dict):
    logging.info("Running sql_executor...")

    assert (
        task_config[common.COMPONENT_NAME] == COMPONENT_NAME
    ), f"Component name should be {COMPONENT_NAME}, but got {task_config[common.COMPONENT_NAME]}"

    inputs = task_config[common.INPUTS]
    outputs = task_config[common.OUTPUTS]

    assert len(inputs) == 1, f"{COMPONENT_NAME} should have only 1 input"
    assert len(outputs) == 1, f"{COMPONENT_NAME} should have only 1 output"

    statements = task_config[STATEMENTS]

    sql_queries = split_sql_queries(statements)

    def is_select_query(query):
        query = query.strip().lower()
        return query.startswith("select")

    assert is_select_query(
        sql_queries[-1]
    ), "The last statement must be a SELECT query."

    def infer_sqlite_type(pd_type):
        if pd.api.types.is_integer_dtype(pd_type):
            return "INTEGER"
        elif pd.api.types.is_float_dtype(pd_type):
            return "REAL"
        elif pd.api.types.is_bool_dtype(pd_type):
            return "BOOLEAN"
        else:
            return "TEXT"

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:

        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()

        for chunk in pd.read_csv(inputs[0][common.DATA_PATH], chunksize=CHUNK_SIZE):
            chunk.to_sql(DEFAULT_TABLE, conn, index=False, if_exists="append")

        conn.commit()

        for s in sql_queries:
            cursor.execute(s)

        conn.commit()

        with open(outputs[0][common.DATA_PATH], "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cursor.description])  # 写入列名

            for row in cursor:
                writer.writerow(row)

        conn.close()

        df = pd.read_csv(outputs[0][common.DATA_PATH], nrows=5)
        output_schema = data_pb2.TableSchema()
        common.append_table_schema(output_schema, inputs[0][common.SCHEMA])
        output_schema = common.gen_output_schema(df, output_schema, True)
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
        run_sql_executor(task_config)


if __name__ == "__main__":
    # TODO set log level
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
