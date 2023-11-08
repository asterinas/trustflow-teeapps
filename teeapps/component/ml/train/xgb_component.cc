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

#include "xgb_component.h"

#include <math.h>

namespace teeapps {
namespace component {

void XgbTrainComponent::Init() {
  AddAttr<int64_t>("num_boost_round", "Number of boosting iterations.", false,
                   true, std::vector<int64_t>{10}, std::nullopt, 1, 1024, true,
                   true);
  AddAttr<int64_t>("max_depth", "Maximum depth of a tree.", false, true,
                   std::vector<int64_t>{6}, std::nullopt, 1, 16, true, true);
  AddAttr<int64_t>("max_leaves",
                   "Maximum leaf of a tree. 0 indicates no limit.", false, true,
                   std::vector<int64_t>{0}, std::nullopt, 0, std::pow(2, 15),
                   true, true);
  AddAttr<int64_t>("seed", "Pseudorandom number generator seed.", false, true,
                   std::vector<int64_t>{42}, std::nullopt, 0, std::nullopt,
                   true, std::nullopt);
  AddAttr<float>("learning_rate",
                 "Step size shrinkage used in update to prevent overfitting.",
                 false, true, std::vector<float>{0.3}, std::nullopt, 0, 1,
                 false, true);
  AddAttr<float>("lambda", "L2 regularization term on weights.", false, true,
                 std::vector<float>{1}, std::nullopt, 0, 10000, true, true);
  AddAttr<float>("gamma",
                 "Greater than 0 means pre-pruning enabled. If gain of a node "
                 "is less than this value, it would be pruned.",
                 false, true, std::vector<float>{0}, std::nullopt, 0, 10000,
                 true, true);
  AddAttr<float>("colsample_bytree",
                 "Subsample ratio of columns when constructing each tree.",
                 false, true, std::vector<float>{1}, std::nullopt, 0, 1, false,
                 true);
  AddAttr<float>("base_score",
                 "The initial prediction score of all instances, global bias.",
                 false, true, std::vector<float>{0.5}, std::nullopt, 0, 1,
                 false, false);
  AddAttr<float>("min_child_weight",
                 "Minimum sum of instance weight (hessian) needed in a child. "
                 "If the tree partition step results in a leaf node with the "
                 "sum of instance weight less than min_child_weight, then the "
                 "building process will give up further partitioning",
                 false, true, std::vector<float>{1}, std::nullopt, 0, 1000,
                 true, true);
  AddAttr<std::string>(
      "objective", "Specify the learning objective.", false, true,
      std::vector<std::string>{"binary:logistic"},
      std::vector<std::string>{"reg:squarederror", "binary:logistic"});
  AddAttr<float>("alpha",
                 "L1 regularization term on weights. Increasing this value "
                 "will make model more conservative",
                 false, true, std::vector<float>{0}, std::nullopt, 0, 10000,
                 true, true);
  AddAttr<float>("subsample", "Subsample ratio of the training instance.",
                 false, true, std::vector<float>{1}, std::nullopt, 0, 1, false,
                 true);
  AddAttr<int64_t>(
      "max_bin",
      "Maximum number of discrete bins to bucket continuous features.  Only "
      "used if tree_method is set to hist, approx or gpu_hist.",
      false, true, std::vector<int64_t>{10}, std::nullopt, 0, 254, false,
      false);
  AddAttr<std::string>(
      "tree_method", "The tree construction algorithm used in XGBoost.", false,
      true, std::vector<std::string>{"auto"},
      std::vector<std::string>{"auto", "exact", "approx", "hist"});
  AddAttr<std::string>("booster", "Which booster to use", false, true,
                       std::vector<std::string>{"gbtree"},
                       std::vector<std::string>{"gbtree", "gblinear", "dart"});

  AddIo(IoType::INPUT, "train_dataset", "Input table.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("ids", "Id columns will not be trained."),
            TableColParam("label", "Label column.", 1, 1)});
  AddIo(IoType::OUTPUT, "output_model", "Output model.",
        {DistDataType::XGB_MODEL});
}

}  // namespace component
}  // namespace teeapps
