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
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "eval_param_reader.h"

#include "secretflow/spec/v1/component.pb.h"
#include "secretflow/spec/v1/evaluation.pb.h"

namespace teeapps {
namespace component {

class Component {
 private:
  std::string name_;
  std::string domain_;
  std::string version_;
  std::string desc_;

  std::unique_ptr<secretflow::spec::v1::ComponentDef> definition_;
  std::vector<std::unique_ptr<secretflow::spec::v1::AttributeDef>> attr_decls_;
  std::vector<std::unique_ptr<secretflow::spec::v1::IoDef>> input_decls_;
  std::vector<std::unique_ptr<secretflow::spec::v1::IoDef>> output_decls_;
  std::set<std::string> argnames_;

  const std::vector<std::string> reserved_words_ = {"input", "output"};
  const std::vector<std::string> allowed_storage_types_ = {"local_fs"};

 public:
  bool CheckReservedWords(const std::string& word) {
    return std::find(reserved_words_.begin(), reserved_words_.end(), word) ==
           reserved_words_.end();
  }

  std::string CheckStorage(const secretflow::spec::v1::StorageConfig& storage) {
    if (std::find(allowed_storage_types_.begin(), allowed_storage_types_.end(),
                  storage.type()) == allowed_storage_types_.end()) {
      throw "storage_type is not supported.";
    }
    return storage.local_fs().wd();
  }

  explicit Component(const std::string& name, const std::string& domain = "",
                     const std::string& version = "",
                     const std::string& desc = "")
      : name_(name),
        domain_(domain),
        version_(version),
        desc_(desc),
        definition_(nullptr) {
    attr_decls_.clear();
    input_decls_.clear();
    output_decls_.clear();
  }

  ~Component() {}

  template <typename T>
  void AddAttr(
      const std::string& name, const std::string& desc, bool is_list,
      bool is_optional,
      const std::optional<std::vector<T>>& default_values = std::nullopt,
      const std::optional<std::vector<T>>& allowed_values = std::nullopt,
      const std::optional<T>& lower_bound = std::nullopt,
      const std::optional<T>& upper_bound = std::nullopt,
      const std::optional<bool>& lower_bound_inclusive = std::nullopt,
      const std::optional<bool>& upper_bound_inclusive = std::nullopt,
      const std::optional<int>& list_min_length_inclusive = std::nullopt,
      const std::optional<int>& list_max_length_inclusive = std::nullopt);

  void AddIo(const IoType io_type, const std::string& name,
             const std::string& desc, const std::vector<std::string>& types,
             const std::optional<std::vector<TableColParam>>& col_params =
                 std::nullopt);

  const std::unique_ptr<secretflow::spec::v1::ComponentDef>& Definition();
  void Eval(const secretflow::spec::v1::NodeEvalParam& param,
            const std::optional<secretflow::spec::v1::StorageConfig>&
                storage_config = std::nullopt,
            bool tracer_report = false);
};

}  // namespace component
}  // namespace teeapps
