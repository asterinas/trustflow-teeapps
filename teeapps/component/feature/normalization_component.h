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

#pragma once

#include "../component.h"

namespace teeapps::component {

class NormalizationComponent : public Component {
 private:
  void Init();

  explicit NormalizationComponent(const std::string& name = "normalization",
                                  const std::string& domain = "feature",
                                  const std::string& version = "0.0.1",
                                  const std::string& desc = "Normalize cols.")
      : Component(name, domain, version, desc) {
    Init();
  }

  ~NormalizationComponent() {}
  NormalizationComponent(const NormalizationComponent&) = delete;
  const NormalizationComponent& operator=(const NormalizationComponent&) =
      delete;

 public:
  static NormalizationComponent& GetInstance() {
    static NormalizationComponent instance;
    return instance;
  }
};

}  // namespace teeapps::component
