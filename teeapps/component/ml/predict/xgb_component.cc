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

namespace teeapps {
namespace component {

void XgbPredComponent::Init() {
  AddAttr<std::string>("pred_name", "Column name for predictions.", false, true,
                       std::vector<std::string>{"pred"});
  AddAttr<bool>(
      "save_label",
      "Whether or not to save real label column into output pred table. "
      "If true, input feature_dataset must contain label column.",
      false, true, std::vector<bool>{false});
  AddAttr<std::string>("label_name", "Column name for label.", false, true,
                       std::vector<std::string>{"label"});
  AddAttr<bool>("save_id",
                "Whether to save id column into output pred table. "
                "If true, input feature_dataset must contain id column.",
                false, true, std::vector<bool>{false});
  AddAttr<std::string>("id_name", "Column name for id.", false, true,
                       std::vector<std::string>{"id"});
  AddAttr<std::string>(
      "col_names", "Extra column names into output pred table.", true, true);

  AddIo(IoType::INPUT, "feature_dataset", "Input feature dataset.",
        {DistDataType::INDIVIDUAL_TABLE},
        std::vector<TableColParam>{
            TableColParam("ids", "Id columns.", std::nullopt, 1),
            TableColParam("label", "Label column.", std::nullopt, 1)});
  AddIo(IoType::INPUT, "model", "Input model.", {DistDataType::XGB_MODEL});
  AddIo(IoType::OUTPUT, "pred", "Output prediction.",
        {DistDataType::INDIVIDUAL_TABLE});
}

}  // namespace component
}  // namespace teeapps
