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

#include "train_test_split_component.h"

namespace teeapps {
namespace component {

void TrainTestSplitComponent::Init() {
  AddAttr<float>("train_size",
                 "Proportion of the dataset to include in the train subset.",
                 false, true, std::vector<float>{0.75}, std::nullopt, 0.0, 1.0,
                 false, false);
  AddAttr<bool>("fix_random", "Whether to fix random.", false, true,
                std::vector<bool>{true});
  AddAttr<int64_t>("random_state", "Specify the random seed of the shuffling.",
                   false, true, std::vector<int64_t>{1024}, std::nullopt, 0,
                   std::nullopt, false, std::nullopt);
  AddAttr<bool>("shuffle", "Whether to shuffle the data before splitting.",
                false, true, std::vector<bool>{true});

  AddIo(IoType::INPUT, "input_data", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE});
  AddIo(IoType::OUTPUT, "train", "Output train dataset.",
        {DistDataType::INDIVIDUAL_TABLE});
  AddIo(IoType::OUTPUT, "test", "Output test dataset.",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace component
}  // namespace teeapps
