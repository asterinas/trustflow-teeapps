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

#include "eval_param_reader.h"

namespace teeapps {
namespace component {

void EvalParamReader::Preprocess() {
  if (instance_->domain() != definition_->domain()) {
    throw string_format(
        "domain inst: %s def\
                        : % s does not match\
                                  .",
        instance_->domain(), definition_->domain());
  }
  if (instance_->name() != definition_->name()) {
    throw string_format(
        "name inst: %s\
                        def\
                        : % s does not match\
                                  .",
        instance_->name(), definition_->name());
  }
  if (instance_->version() != definition_->version()) {
    throw string_format(
        "version inst: %s\
                        def\
                        : % s does not match\
                                  .",
        instance_->version(), definition_->version());
  }
  if (instance_->attr_paths_size() != instance_->attrs_size()) {
    throw string_format(
        "attr size inst: %d\
                        def\
                        : % d does not match\
                                  .",
        instance_->attr_paths_size(), definition_->attrs_size());
  }
  // construct kv map
  for (int i = 0; i < instance_->attr_paths_size(); ++i) {
    if (instance_attrs_.count(instance_->attr_paths(i))) {
      throw string_format("attr %s is duplicate in node def.",
                          instance_->attr_paths(i));
    }
    if (!instance_->attrs(i).is_na()) {
      instance_attrs_[instance_->attr_paths(i)] = instance_->attrs(i);
    }
  }
  // attribute
  for (const auto& attr : definition_->attrs()) {
    if (!check_attr_type(attr.type())) {
      throw string_format("attr type %d not supported.", attr.type());
    }
    std::vector<std::string> paths{attr.prefixes().begin(),
                                   attr.prefixes().end()};
    paths.emplace_back(attr.name());
    std::string full_name = string_join(paths, "/");
    if (!instance_attrs_.count(full_name)) {
      if (!attr.atomic().is_optional()) {
        throw string_format("attr %s is not optional and not set.", full_name);
      }
      instance_attrs_[full_name] = attr.atomic().default_value();
    }

    if (!check_allowed_values(instance_attrs_[full_name], attr)) {
      throw string_format("attr %s: check_allowed_values failed.", full_name);
    }
    if (!check_lower_bound(instance_attrs_[full_name], attr)) {
      throw string_format("attr %s: check_lower_bound failed.", full_name);
    }
    if (!check_upper_bound(instance_attrs_[full_name], attr)) {
      throw string_format("attr %s: check_upper_bound failed.", full_name);
    }

    // instance_attrs_[full_name] =
    //     get_value(self.instance_attrs_[full_name], attr.type)
  }

  // input
  if (instance_->inputs_size() != definition_->inputs_size()) {
    throw "number of input does not match.";
  }
  for (int i = 0; i < instance_->inputs_size(); ++i) {
    const auto& input_instance = instance_->inputs(i);
    const auto& input_def = definition_->inputs(i);
    if (instance_inputs_.count(input_def.name())) {
      throw string_format("input %s is duplicate.", input_def.name());
    }
    if (input_def.types_size() &&
        std::find(input_def.types().begin(), input_def.types().end(),
                  input_instance.type()) == input_def.types().end()) {
      throw string_format(
          "type of input %s is wrong, \
              got %s,\
          expect % s ",
          input_def.name(), input_instance.type(),
          string_join({input_def.types().begin(), input_def.types().end()},
                      ","));
    }
    instance_inputs_[input_def.name()] = input_instance;

    for (const auto& input_attr : input_def.attrs()) {
      if (input_attr.extra_attrs_size()) {
        throw "extra attribute is unsupported at this moment.";
      }

      std::string full_name =
          string_join({"input", input_def.name(), input_attr.name()}, "/");
      if (!instance_attrs_.count(full_name)) {
        instance_attrs_[full_name] = secretflow::spec::v1::Attribute();
      }
      if (!check_table_attr_col_cnt(instance_attrs_[full_name], input_attr)) {
        throw string_format("input attr %s check_table_attr_col_cnt fails.",
                            full_name);
      }
      // instance_attrs_[full_name] =
      //     get_value(instance_attrs_[full_name], AttrType.AT_STRINGS);
    }
  }

  // output
  if (instance_->output_uris_size() != definition_->outputs_size()) {
    throw "number of output does not match.";
  }
  for (int i = 0; i < instance_->output_uris_size(); ++i) {
    const auto& output_prefix = instance_->output_uris(i);
    const auto& output_def = definition_->outputs(i);
    if (instance_outputs_.count(output_def.name())) {
      throw string_format("output %s is duplicate.", output_def.name());
    }
    instance_outputs_[output_def.name()] = output_prefix;
  }
}

}  // namespace component
}  // namespace  teeapps
