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

#include "equal_frequency_binning_component.h"

namespace teeapps {
namespace component {

void EqualFrequencyBinningComponent::Init() {
  AddAttr<int64_t>("bin_num", "Bin counts for one feature.", false, true,
                   std::vector<int64_t>{10}, std::nullopt, 0, std::nullopt,
                   false, std::nullopt);

  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{TableColParam(
            "feature_selects", "which features should be binned.", 1)});
  AddIo(IoType::OUTPUT, "equal_frequency_binning_rule",
        "Output equal frequency binning rule.",
        {DistDataType::EQUAL_FREQUENCY_BINNING_RULE});
  AddIo(IoType::OUTPUT, "report", "Equal width frequency report.",
        {DistDataType::REPORT});
}

}  // namespace component
}  // namespace teeapps
