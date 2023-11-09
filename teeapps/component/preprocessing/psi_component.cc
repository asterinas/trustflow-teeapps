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

#include "psi_component.h"

namespace teeapps {
namespace component {

void PsiComponent::Init() {
  AddIo(IoType::INPUT, "input1", "Individual table for party 1",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("key", "Column(s) used to join.", 1)});
  AddIo(IoType::INPUT, "input2", "Individual table for party 2",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("key", "Column(s) used to join.", 1)});
  AddIo(IoType::OUTPUT, "psi_output", "Output table",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace component
}  // namespace teeapps
