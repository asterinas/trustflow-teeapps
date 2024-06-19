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

#include "lgbm_component.h"

namespace teeapps {
namespace component {

void LgbmTrainComponent::Init() {
  AddAttr<int64_t>("n_estimators", "Number of boosted trees to fit.", false,
                   true, std::vector<int64_t>{10}, std::nullopt, 1, 1024, true,
                   true);
  AddAttr<std::string>("objective", "Specify the learning objective.", false,
                       true, std::vector<std::string>{"binary"},
                       std::vector<std::string>{"regression", "binary"});
  AddAttr<std::string>("boosting_type", "Boosting type.", false, true,
                       std::vector<std::string>{"gbdt"},
                       std::vector<std::string>{"gbdt", "rf", "dart"});
  AddAttr<float>("learning_rate", "Learning rate.", false, true,
                 std::vector<float>{0.1}, std::nullopt, 0, 1, false, true);
  AddAttr<int64_t>("num_leaves", "Max number of leaves in one tree.", false,
                   true, std::vector<int64_t>{31}, std::nullopt, 2, 1024, true,
                   true);

  AddIo(IoType::INPUT, "train_dataset", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("ids", "Id columns will not be trained."),
            TableColParam("label", "Label column.", 1, 1)});
  AddIo(IoType::OUTPUT, "output_model", "Output model.",
        {DistDataType::LGBM_MODEL});
}

}  // namespace component
}  // namespace teeapps