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

#include "biclassification_component.h"

namespace teeapps {
namespace component {

void BiclassificationComponent::Init() {
  AddAttr<int64_t>("bucket_num", "Number of buckets.", false, true,
                   std::vector<int64_t>{10}, std::nullopt, 1, std::nullopt,
                   true, std::nullopt);
  AddAttr<int64_t>("min_item_cnt_per_bucket",
                   "Min item cnt per bucket. If any bucket doesn't meet the "
                   "requirement, error raises. For security reasons, we "
                   "require this parameter to be at least 2.",
                   false, true, std::vector<int64_t>{2}, std::nullopt, 2,
                   std::nullopt, true, std::nullopt);

  AddIo(IoType::INPUT, "predictions", "Input table with predictions",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("label", "The real value column name", 1, 1),
            TableColParam("score", "The score value column name", 1, 1)});
  AddIo(IoType::OUTPUT, "reports", "Output report.", {DistDataType::REPORT});
}

}  // namespace component
}  // namespace teeapps
