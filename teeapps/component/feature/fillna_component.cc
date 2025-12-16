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

#include "fillna_component.h"

namespace teeapps::component {

void FillnaComponent::Init() {
  AddIo(IoType::INPUT, "fillna_input", "Input table",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("col", "Column to fillna.", 1, 1)});
  AddAttr<std::string>(
      "strategy",
      "The strategy to fill NA. For string cols, only mode and constant "
      "options are allowed. If constant is selected, the corresponding "
      "constant value should be provided as well.",
      false, false, std::vector<std::string>{"constant"},
      std::vector<std::string>{"constant", "max", "min", "mode", "median",
                               "mean"});

  AddAttr<float>(
      "constant_float",
      "Only valid when selected col is float and strategy is constant.", false,
      true, std::vector<float>{0.0});

  AddAttr<int64_t>(
      "constant_int64",
      "Only valid when selected col is int64 and strategy is constant.", false,
      true, std::vector<int64_t>{0});

  AddAttr<bool>(
      "constant_bool",
      "Only valid when selected col is bool and strategy is constant.", false,
      true, std::vector<bool>{false});

  AddAttr<std::string>(
      "constant_str",
      "Only valid when selected col is str and strategy is constant.", false,
      true, std::vector<std::string>{""});

  AddIo(IoType::OUTPUT, "fillna_output", "Output table",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace teeapps::component
