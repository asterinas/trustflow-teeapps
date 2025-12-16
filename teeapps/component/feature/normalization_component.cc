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

#include "normalization_component.h"

namespace teeapps::component {

void NormalizationComponent::Init() {
  AddIo(IoType::INPUT, "normalization_input", "Input table",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("cols",
                          "Column(s) to normalize. Only numeric column(s) are "
                          "allowed. ",
                          1)});
  AddAttr<std::string>(
      "strategies",
      "The strategy to normalize. standard: Standardize features by removing "
      "the mean and scaling to unit variance. max_abs: "
      "Scale each feature by its maximum absolute value. min_max: "
      "Transform features by scaling each feature to a given range.",
      true, false, std::vector<std::string>{"standard"},
      std::vector<std::string>{"standard", "max_abs", "min_max"});

  AddIo(IoType::OUTPUT, "normalization_output", "Output table",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace teeapps::component
