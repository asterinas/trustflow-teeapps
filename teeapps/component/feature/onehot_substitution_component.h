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

namespace teeapps {
namespace component {

class OnehotSubstitutionComponent : public Component {
 private:
  void Init();

  explicit OnehotSubstitutionComponent(
      const std::string& name = "onehot_substitution",
      const std::string& domain = "feature",
      const std::string& version = "0.0.1",
      const std::string& desc =
          "Substitute datasets' cols by onehot substitution rules.")
      : Component(name, domain, version, desc) {
    Init();
  }
  ~OnehotSubstitutionComponent() {}
  OnehotSubstitutionComponent(const OnehotSubstitutionComponent&) = delete;
  const OnehotSubstitutionComponent& operator=(
      const OnehotSubstitutionComponent&) = delete;

 public:
  static OnehotSubstitutionComponent& GetInstance() {
    static OnehotSubstitutionComponent instance;
    return instance;
  }
};

}  // namespace component
}  // namespace teeapps
