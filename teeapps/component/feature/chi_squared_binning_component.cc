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

#include "chi_squared_binning_component.h"

namespace teeapps {
namespace component {

void ChiSquaredBinningComponent::Init() {
  AddAttr<int64_t>(
      "max_bin_num",
      "Max bin counts for one feature. If provided, threshold will be ignored.",
      false, true, std::vector<int64_t>{10}, std::nullopt, 0, std::nullopt,
      false, std::nullopt);

  AddAttr<float>("threshold",
                 "threshold to merge neighbouring groups. If provided, "
                 "max_bin_num will be ignored.",
                 false, true, std::vector<float>{3.841}, std::nullopt, 0,
                 std::nullopt, false, std::nullopt);

  AddAttr<std::string>("positive_label",
                       "Which value represent positive value in label.", false,
                       true, std::vector<std::string>{"1"});

  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("feature_selects", "which features should be binned.",
                          1),
            TableColParam("label", "Label column.", 1, 1)});
  AddIo(IoType::OUTPUT, "chi_squared_binning_rule",
        "Output chi_squared binning rule.",
        {DistDataType::CHI_SQUARED_BINNING_RULE});
  AddIo(IoType::OUTPUT, "report", "Chi_squared binning report.",
        {DistDataType::REPORT});
}

}  // namespace component
}  // namespace teeapps
