// Copyright 2023 Ant Group Co., Ltd.
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

#include "woe_binning_component.h"

namespace teeapps {
namespace component {

void WoeBinningComponent::Init() {
  AddAttr<std::string>("binning_method",
                       "How to bin features with numeric types: "
                       "quantile\"(equal frequency)/\"bucket\"(equal width)",
                       false, true, std::vector<std::string>{"quantile"},
                       std::vector<std::string>{"quantile", "bucket"});
  AddAttr<std::string>("positive_label",
                       "Which value represent positive value in label.", false,
                       true, std::vector<std::string>{"1"});
  AddAttr<int64_t>("bin_num", "Max bin counts for one features.", false, true,
                   std::vector<int64_t>{10}, std::nullopt, 0, std::nullopt,
                   false, std::nullopt);

  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("feature_selects", "which features should be binned.",
                          1),
            TableColParam("label", "Label column.", 1, 1)});
  AddIo(IoType::OUTPUT, "woe_rule", "Output WOE rule.",
        {DistDataType::WOE_RUNNING_RULE});
}

}  // namespace component
}  // namespace teeapps
