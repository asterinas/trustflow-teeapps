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

#include "../../component.h"

namespace teeapps {
namespace component {

class BiclassificationComponent : public Component {
 private:
  void Init();

  explicit BiclassificationComponent(
      const std::string& name = "biclassification_eval",
      const std::string& domain = "ml.eval",
      const std::string& version = "0.0.1",
      const std::string& desc =
          "Statistics evaluation for a bi-classification model on a dataset.\n"
          "1. summary_report: SummaryReport\n"
          "2. eq_frequent_bin_report: List[EqBinReport]\n"
          "3. eq_range_bin_report: List[EqBinReport]\n"
          "4. head_report: List[PrReport]\n"
          "reports for fpr = 0.001, 0.005, 0.01, 0.05, 0.1, 0.2")
      : Component(name, domain, version, desc) {
    Init();
  }
  ~BiclassificationComponent() {}
  BiclassificationComponent(const BiclassificationComponent&) = delete;
  const BiclassificationComponent& operator=(const BiclassificationComponent&) =
      delete;

 public:
  static BiclassificationComponent& GetInstance() {
    static BiclassificationComponent instance;
    return instance;
  }
};

}  // namespace component
}  // namespace teeapps
