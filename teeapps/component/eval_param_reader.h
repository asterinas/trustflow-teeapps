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

#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "util.h"

#include "secretflow/spec/v1/component.pb.h"
#include "secretflow/spec/v1/data.pb.h"
#include "secretflow/spec/v1/evaluation.pb.h"

namespace teeapps {
namespace component {

class EvalParamReader {
 private:
  const secretflow::spec::v1::NodeEvalParam* instance_;
  const secretflow::spec::v1::ComponentDef* definition_;
  std::map<std::string, secretflow::spec::v1::Attribute> instance_attrs_;
  std::map<std::string, secretflow::spec::v1::DistData> instance_inputs_;
  std::map<std::string, std::string> instance_outputs_;

 public:
  const secretflow::spec::v1::Attribute& GetAttr(
      const std::string& name) const {
    if (!instance_attrs_.count(name)) {
      throw string_format("attr %s does not exist.", name);
    }
    return instance_attrs_.at(name);
  }

  const secretflow::spec::v1::DistData& GetInput(
      const std::string& name) const {
    if (!instance_inputs_.count(name)) {
      throw string_format("input %s does not exist.", name);
    }
    return instance_inputs_.at(name);
  }

  const secretflow::spec::v1::Attribute& GetInputAttrs(
      const std::string& input_name, const std::string& attr_name) const {
    std::string full_name = string_join({"input", input_name, attr_name}, "/");
    if (!instance_attrs_.count(full_name)) {
      throw string_format("input attr %s does not exist.", full_name);
    }
    return instance_attrs_.at(full_name);
  }

  const std::string& GetOutputUri(const std::string& name) const {
    if (!instance_outputs_.count(name)) {
      throw string_format("output %s does not exist.", name);
    }
    return instance_outputs_.at(name);
  }

 public:
  explicit EvalParamReader(const secretflow::spec::v1::NodeEvalParam* instance,
                           const secretflow::spec::v1::ComponentDef* definition)
      : instance_(instance), definition_(definition) {
    Preprocess();
  }
  void Preprocess();
};

}  // namespace component
}  // namespace teeapps
