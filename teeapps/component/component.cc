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

#include "component.h"

#include <cmath>

namespace teeapps {
namespace component {

template <typename T>
void Component::AddAttr(const std::string& name, const std::string& desc,
                        bool is_list, bool is_optional,
                        const std::optional<std::vector<T>>& default_values,
                        const std::optional<std::vector<T>>& allowed_values,
                        const std::optional<T>& lower_bound,
                        const std::optional<T>& upper_bound,
                        const std::optional<bool>& lower_bound_inclusive,
                        const std::optional<bool>& upper_bound_inclusive,
                        const std::optional<int>& list_min_length_inclusive,
                        const std::optional<int>& list_max_length_inclusive) {
  // check name
  if (!CheckReservedWords(name)) {
    throw string_format("%s is a reserved word.", name);
  }

  {
    // if T is bool type, skip
    if (allowed_values.has_value() &&
        (lower_bound.has_value() || upper_bound.has_value())) {
      throw "allowed_values and bounds could not be set at the same time.";
    }
    // if T is bool type, skip
    if (allowed_values.has_value() && default_values.has_value()) {
      for (const auto& value : default_values.value()) {
        if (std::find(allowed_values.value().begin(),
                      allowed_values.value().end(),
                      value) == allowed_values.value().end()) {
          throw "default_value is not in allowed_values";
        }
      }
    }
    // if T is not number type(egg. string or bool), skip
    if (lower_bound.has_value() && upper_bound.has_value() &&
        lower_bound.value() > upper_bound.value()) {
      throw "lower_bound is greater than upper_bound";
    }

    // if T is not number type(egg. string or bool), skip
    if (default_values.has_value()) {
      if (lower_bound.has_value()) {
        for (const auto& value : default_values.value()) {
          if (!(value > lower_bound.value() ||
                (lower_bound_inclusive.has_value() &&
                 lower_bound_inclusive.value() &&
                 is_equal(value, lower_bound.value())))) {
            throw "default_value fails bound check: lower_bound";
          }
        }
      }
      // if T is not number type(egg. string or bool), skip
      if (upper_bound.has_value()) {
        for (const auto& value : default_values.value()) {
          if (!(value < upper_bound.value() ||
                (upper_bound_inclusive.has_value() &&
                 upper_bound_inclusive.value() &&
                 is_equal(value, upper_bound.value())))) {
            throw "default_value fails bound check: upper_bound";
          }
        }
      }
    }
  }

  //
  if (list_min_length_inclusive.has_value() &&
      list_max_length_inclusive.has_value() &&
      list_min_length_inclusive.value() > list_max_length_inclusive.value()) {
    throw string_format(
        "list_min_length_inclusive [%d] should not be greater than \
        list_max_length_inclusive[%d] ",
        list_min_length_inclusive.value(), list_max_length_inclusive.value());
  }

  //
  secretflow::spec::v1::AttributeDef* attr =
      new secretflow::spec::v1::AttributeDef();
  attr->set_name(name);
  attr->set_desc(desc);
  attr->set_type(is_list ? get_list_type<T>() : get_single_type<T>());

  secretflow::spec::v1::AttributeDef::AtomicAttrDesc* attr_desc =
      attr->mutable_atomic();
  attr_desc->set_is_optional(is_optional);

  if (default_values.has_value() && !default_values.value().empty()) {
    if (is_list) {
      set_list_value<T>(attr_desc->mutable_default_value(),
                        default_values.value());
    } else {
      set_single_value<T>(attr_desc->mutable_default_value(),
                          default_values.value()[0]);
    }
  }

  {
    // if T is bool type, skip
    if (allowed_values.has_value()) {
      set_list_value<T>(attr_desc->mutable_allowed_values(),
                        allowed_values.value());
    }
    // if T is not number type(egg. string or bool), skip
    if (lower_bound.has_value()) {
      attr_desc->set_lower_bound_enabled(true);
      attr_desc->set_lower_bound_inclusive(lower_bound_inclusive.value());
      set_single_value<T>(attr_desc->mutable_lower_bound(),
                          lower_bound.value());
    }
    // if T is not number type(egg. string or bool), skip
    if (upper_bound.has_value()) {
      attr_desc->set_upper_bound_enabled(true);
      attr_desc->set_upper_bound_inclusive(upper_bound_inclusive.value());
      set_single_value<T>(attr_desc->mutable_upper_bound(),
                          upper_bound.value());
    }
  }

  if (is_list) {
    if (list_min_length_inclusive.has_value()) {
      attr_desc->set_list_min_length_inclusive(
          list_min_length_inclusive.value());
    } else {
      attr_desc->set_list_min_length_inclusive(0);
    }

    if (list_max_length_inclusive.has_value()) {
      attr_desc->set_list_max_length_inclusive(
          list_max_length_inclusive.value());
    } else {
      attr_desc->set_list_max_length_inclusive(-1);
    }
  }

  attr_decls_.emplace_back(attr);
}

void Component::AddIo(
    const IoType io_type, const std::string& name, const std::string& desc,
    const std::vector<std::string>& types,
    const std::optional<std::vector<TableColParam>>& col_params) {
  if (!CheckReservedWords(name)) {
    throw string_format("%s is a reserved word.", name);
  }
  secretflow::spec::v1::IoDef* io_def = new secretflow::spec::v1::IoDef();
  io_def->set_name(name);
  io_def->set_desc(desc);
  io_def->mutable_types()->CopyFrom({types.begin(), types.end()});
  //
  if (col_params.has_value()) {
    for (const TableColParam& col_param : col_params.value()) {
      secretflow::spec::v1::IoDef::TableAttrDef* col = io_def->add_attrs();
      col->set_name(col_param.name);
      col->set_desc(col_param.desc);
      if (col_param.col_min_cnt_inclusive.has_value()) {
        col->set_col_min_cnt_inclusive(col_param.col_min_cnt_inclusive.value());
      }
      if (col_param.col_max_cnt_inclusive.has_value()) {
        col->set_col_max_cnt_inclusive(col_param.col_max_cnt_inclusive.value());
      }
    }
  }
  if (!check_io_def(io_def)) {
    throw string_format("IoDef %s: is not a supported DistData types",
                        io_def->name());
  }
  if (io_type == IoType::INPUT) {
    input_decls_.emplace_back(
        std::unique_ptr<secretflow::spec::v1::IoDef>(io_def));
  } else {
    output_decls_.emplace_back(
        std::unique_ptr<secretflow::spec::v1::IoDef>(io_def));
  }
};

const std::unique_ptr<secretflow::spec::v1::ComponentDef>&
Component::Definition() {
  if (nullptr != definition_) {
    return definition_;
  }
  secretflow::spec::v1::ComponentDef* comp_def =
      new secretflow::spec::v1::ComponentDef();
  comp_def->set_domain(domain_);
  comp_def->set_name(name_);
  comp_def->set_desc(desc_);
  comp_def->set_version(version_);

  // assign attr
  for (const auto& attr : attr_decls_) {
    if (argnames_.count(attr->name())) {
      throw string_format("attr %s is duplicate.", attr->name());
    }
    argnames_.insert(attr->name());
    comp_def->add_attrs()->CopyFrom(*attr.get());
  }
  // assign input
  for (const auto& io : input_decls_) {
    if (argnames_.count(io->name())) {
      throw string_format("input %s is duplicate.", io->name());
    }
    argnames_.insert(io->name());
    for (const auto& input_attr : io->attrs()) {
      argnames_.insert(io->name() + "_" + input_attr.name());
    }
    comp_def->add_inputs()->CopyFrom(*io.get());
  }
  // assign output
  for (const auto& io : output_decls_) {
    if (argnames_.count(io->name())) {
      throw string_format("output %s is duplicate.", io->name());
    }
    argnames_.insert(io->name());
    comp_def->add_outputs()->CopyFrom(*io.get());
  }
  definition_ = std::unique_ptr<secretflow::spec::v1::ComponentDef>(comp_def);
  return definition_;
};

void Component::Eval(
    const secretflow::spec::v1::NodeEvalParam& param,
    const std::optional<secretflow::spec::v1::StorageConfig>& storage_config,
    bool tracer_report) {
  const auto& definition = this->Definition();

  CompEvalContext ctx;
  if (storage_config.has_value()) {
    ctx.local_fs_wd = CheckStorage(storage_config.value());
  }

  EvalParamReader reader{&param, definition.get()};
}

template void Component::AddAttr<float>(
    const std::string& name, const std::string& desc, bool is_list,
    bool is_optional,
    const std::optional<std::vector<float>>& default_values = std::nullopt,
    const std::optional<std::vector<float>>& allowed_values = std::nullopt,
    const std::optional<float>& lower_bound = std::nullopt,
    const std::optional<float>& upper_bound = std::nullopt,
    const std::optional<bool>& lower_bound_inclusive = std::nullopt,
    const std::optional<bool>& upper_bound_inclusive = std::nullopt,
    const std::optional<int>& list_min_length_inclusive = std::nullopt,
    const std::optional<int>& list_max_length_inclusive = std::nullopt);

template void Component::AddAttr<int64_t>(
    const std::string& name, const std::string& desc, bool is_list,
    bool is_optional,
    const std::optional<std::vector<int64_t>>& default_values = std::nullopt,
    const std::optional<std::vector<int64_t>>& allowed_values = std::nullopt,
    const std::optional<int64_t>& lower_bound = std::nullopt,
    const std::optional<int64_t>& upper_bound = std::nullopt,
    const std::optional<bool>& lower_bound_inclusive = std::nullopt,
    const std::optional<bool>& upper_bound_inclusive = std::nullopt,
    const std::optional<int>& list_min_length_inclusive = std::nullopt,
    const std::optional<int>& list_max_length_inclusive = std::nullopt);

template void Component::AddAttr<bool>(
    const std::string& name, const std::string& desc, bool is_list,
    bool is_optional,
    const std::optional<std::vector<bool>>& default_values = std::nullopt,
    const std::optional<std::vector<bool>>& allowed_values = std::nullopt,
    const std::optional<bool>& lower_bound = std::nullopt,
    const std::optional<bool>& upper_bound = std::nullopt,
    const std::optional<bool>& lower_bound_inclusive = std::nullopt,
    const std::optional<bool>& upper_bound_inclusive = std::nullopt,
    const std::optional<int>& list_min_length_inclusive = std::nullopt,
    const std::optional<int>& list_max_length_inclusive = std::nullopt);

template void Component::AddAttr<std::string>(
    const std::string& name, const std::string& desc, bool is_list,
    bool is_optional,
    const std::optional<std::vector<std::string>>& default_values =
        std::nullopt,
    const std::optional<std::vector<std::string>>& allowed_values =
        std::nullopt,
    const std::optional<std::string>& lower_bound = std::nullopt,
    const std::optional<std::string>& upper_bound = std::nullopt,
    const std::optional<bool>& lower_bound_inclusive = std::nullopt,
    const std::optional<bool>& upper_bound_inclusive = std::nullopt,
    const std::optional<int>& list_min_length_inclusive = std::nullopt,
    const std::optional<int>& list_max_length_inclusive = std::nullopt);

}  // namespace component
}  // namespace teeapps
