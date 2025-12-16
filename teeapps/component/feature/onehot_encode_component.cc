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

#include "onehot_encode_component.h"

namespace teeapps {
namespace component {

void OnehotEncodeComponent::Init() {
  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("cols", "which cols should be binned.", 1)});
  AddIo(IoType::OUTPUT, "onehot_encode_role", "Output One Hot encode rule.",
        {DistDataType::ONEHOT_ENCODE_RULE});
}

}  // namespace component
}  // namespace teeapps
