// Copyright 2024 Ant Group Co., Ltd.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "sql_executor_component.h"

namespace teeapps::component {

void SqlExecutorComponent::Init() {
  AddIo(IoType::INPUT, "sql_executor_input", "Input table",
        {DistDataType::INDIVIDUAL_TABLE});
  AddAttr<std::string>(
      "statements",
      "SQL statements. Only supports sqlite. The table name is fixed to be "
      "input_table. The last statement must be SELECT statement.",
      false, false);

  AddIo(IoType::OUTPUT, "sql_executor_output", "Output table",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace teeapps::component
