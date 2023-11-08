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

#include "lr_component.h"

namespace teeapps {
namespace component {

void LrTrainComponent::Init() {
  AddAttr<int64_t>(
      "max_iter",
      "Maximum number of iterations taken for the solvers to converge.", false,
      true, std::vector<int64_t>{10}, std::nullopt, 1, 10000, true, true);
  AddAttr<std::string>("reg_type", "Regression type", false, true,
                       std::vector<std::string>{"logistic"},
                       std::vector<std::string>{"linear", "logistic"});
  AddAttr<float>("l2_norm", "L2 regularization term.", false, true,
                 std::vector<float>{1.0}, std::nullopt, 0, 1e4, true, false);
  AddAttr<float>("tol", "Tolerance for stopping criteria.", false, true,
                 std::vector<float>{1e-4}, std::nullopt, 0, 1, false, false);
  AddAttr<std::string>(
      "penalty", "The penalty(aka regularization term) to be used.", false,
      true, std::vector<std::string>{"l2"},
      std::vector<std::string>{"l1", "l2", "elasticnet", "None"});

  AddIo(IoType::INPUT, "train_dataset", "Input train dataset.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("ids", "Id columns will not be trained."),
            TableColParam("label", "Label column.", 1, 1)});
  AddIo(IoType::OUTPUT, "output_model", "Output model.",
        {DistDataType::LR_MODEL});
}

}  // namespace component
}  // namespace teeapps
