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

#include "multiclass_classification_eval_component.h"

namespace teeapps {
namespace component {

void MulticlassClassificationEvalComponent::Init() {
  AddIo(IoType::INPUT, "predictions", "Input table with predictions",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam(
                "label",
                "The column of label. The value type must be int or string.", 1,
                1),
            TableColParam("scores",
                          "The column(s) of score. Please make sure the order "
                          "must aligned with that of classes.",
                          2)});
  AddIo(IoType::OUTPUT, "reports", "Output report.", {DistDataType::REPORT});

  AddAttr<std::string>("classes", "All possible classes in labels.", true,
                       false, std::nullopt, std::nullopt, std::nullopt,
                       std::nullopt, std::nullopt, std::nullopt, 2);
}

}  // namespace component
}  // namespace teeapps
