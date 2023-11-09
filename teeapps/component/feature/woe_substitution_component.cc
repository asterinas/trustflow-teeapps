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

#include "woe_substitution_component.h"

namespace teeapps {
namespace component {

void WoeSubstitutionComponent::Init() {
  AddIo(IoType::INPUT, "input_data", "Dataset to be substituted.",
        {DistDataType::INDIVIDUAL_TABLE});
  AddIo(IoType::INPUT, "woe_rule", "WOE substitution rule.",
        {DistDataType::WOE_RUNNING_RULE});
  AddIo(IoType::OUTPUT, "output_data", "Output substituted dataset.",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace component
}  // namespace teeapps
