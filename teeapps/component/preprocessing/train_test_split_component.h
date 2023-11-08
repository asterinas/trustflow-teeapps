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

#pragma once

#include "../component.h"

namespace teeapps {
namespace component {

class TrainTestSplitComponent : public Component {
 private:
  void Init();

  explicit TrainTestSplitComponent(
      const std::string& name = "train_test_split",
      const std::string& domain = "preprocessing",
      const std::string& version = "0.0.1",
      const std::string& desc =
          "Split datasets into random train and test subsets.\n"
          "- Please check: "
          "https://scikit-learn.org/stable/modules/generated/"
          "sklearn.model_selection.train_test_split.html")
      : Component(name, domain, version, desc) {
    Init();
  }
  ~TrainTestSplitComponent() {}
  TrainTestSplitComponent(const TrainTestSplitComponent&) = delete;
  const TrainTestSplitComponent& operator=(const TrainTestSplitComponent&) =
      delete;

 public:
  static TrainTestSplitComponent& GetInstance() {
    static TrainTestSplitComponent instance;
    return instance;
  }
};

}  // namespace component
}  // namespace teeapps
