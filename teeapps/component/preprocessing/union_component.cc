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

#include "union_component.h"

namespace teeapps::component {

void UnionComponent::Init() {
  AddIo(IoType::INPUT, "input1", "Table from party 1",
        {DistDataType::INDIVIDUAL_TABLE});
  AddIo(IoType::INPUT, "input2", "Table from party 2",
        {DistDataType::INDIVIDUAL_TABLE});
  AddIo(IoType::OUTPUT, "union_output", "Output table",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace teeapps::component
