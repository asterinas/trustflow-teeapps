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

class PredictionBiasComponent : public Component {
 private:
  void Init();

  explicit PredictionBiasComponent(
      const std::string& name = "prediction_bias_eval",
      const std::string& domain = "ml.eval",
      const std::string& version = "0.0.1",
      const std::string& desc =
          "Calculate prediction bias, ie. average of predictions - average of "
          "labels.")
      : Component(name, domain, version, desc) {
    Init();
  }
  ~PredictionBiasComponent() {}
  PredictionBiasComponent(const PredictionBiasComponent&) = delete;
  const PredictionBiasComponent& operator=(const PredictionBiasComponent&) =
      delete;

 public:
  static PredictionBiasComponent& GetInstance() {
    static PredictionBiasComponent instance;
    return instance;
  }
};

}  // namespace component
}  // namespace teeapps
