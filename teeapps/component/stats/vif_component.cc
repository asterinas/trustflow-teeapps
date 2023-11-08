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

#include "vif_component.h"

namespace teeapps {
namespace component {

void VifComponent::Init() {
  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("feature_selects",
                          "Specify which features to calculate VIF with. If "
                          "empty, all features will be used.")});
  AddIo(IoType::OUTPUT, "report",
        "Output Variance Inflation Factor(VIF) report.",
        {DistDataType::REPORT});
}

}  // namespace component
}  // namespace teeapps
