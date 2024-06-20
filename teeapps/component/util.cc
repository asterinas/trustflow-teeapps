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

#include "util.h"

namespace teeapps {
namespace component {

bool check_io_def(const secretflow::spec::v1::IoDef* io_def) {
  const auto& allowed_types = DistDataType::get_all_types();
  for (const auto& type : io_def->types()) {
    if (allowed_types.find(type) == allowed_types.end()) {
      return false;
    }
  }
  return true;
}

bool check_attr_type(const secretflow::spec::v1::AttrType& attr_type) {
  return attr_type == secretflow::spec::v1::AttrType::AT_FLOAT ||
         attr_type == secretflow::spec::v1::AttrType::AT_FLOATS ||
         attr_type == secretflow::spec::v1::AttrType::AT_INT ||
         attr_type == secretflow::spec::v1::AttrType::AT_INTS ||
         attr_type == secretflow::spec::v1::AttrType::AT_STRING ||
         attr_type == secretflow::spec::v1::AttrType::AT_STRINGS ||
         attr_type == secretflow::spec::v1::AttrType::AT_BOOL ||
         attr_type == secretflow::spec::v1::AttrType::AT_BOOLS;
}

bool check_table_attr_col_cnt(
    const secretflow::spec::v1::Attribute& value,
    const secretflow::spec::v1::IoDef::TableAttrDef& definition) {
  int cnt = value.ss_size();
  if (definition.col_min_cnt_inclusive() &&
      cnt < definition.col_min_cnt_inclusive()) {
    return false;
  }
  if (definition.col_max_cnt_inclusive() and
      cnt > definition.col_max_cnt_inclusive()) {
    return false;
  }
  return true;
}

bool check_allowed_values(
    const secretflow::spec::v1::Attribute& value,
    const secretflow::spec::v1::AttributeDef& definition) {
  // for float
  if (definition.type() == secretflow::spec::v1::AttrType::AT_FLOAT) {
    if (definition.atomic().allowed_values().fs_size() == 0) {
      return true;
    }
    for (const auto& f : definition.atomic().allowed_values().fs()) {
      if (is_equal(f, value.f())) {
        return true;
      }
    }
    return false;
  }
  // for int
  if (definition.type() == secretflow::spec::v1::AttrType::AT_INT) {
    if (definition.atomic().allowed_values().i64s_size() == 0) {
      return true;
    }
    return std::find(definition.atomic().allowed_values().i64s().begin(),
                     definition.atomic().allowed_values().i64s().end(),
                     value.i64()) !=
           definition.atomic().allowed_values().i64s().end();
  }
  // for string
  if (definition.type() == secretflow::spec::v1::AttrType::AT_STRING) {
    if (definition.atomic().allowed_values().ss_size() == 0) {
      return true;
    }
    return std::find(definition.atomic().allowed_values().ss().begin(),
                     definition.atomic().allowed_values().ss().end(),
                     value.s()) !=
           definition.atomic().allowed_values().ss().end();
  }
  // default
  return true;
}

bool check_lower_bound(const secretflow::spec::v1::Attribute& value,
                       const secretflow::spec::v1::AttributeDef& definition) {
  if (!definition.atomic().has_lower_bound()) {
    return true;
  }
  // for float
  if (definition.type() == secretflow::spec::v1::AttrType::AT_FLOAT) {
    return value.f() > definition.atomic().lower_bound().f() ||
           (definition.atomic().lower_bound_inclusive() &&
            is_equal(value.f(), definition.atomic().lower_bound().f()));
  }
  // for int
  if (definition.type() == secretflow::spec::v1::AttrType::AT_INT) {
    return value.i64() > definition.atomic().lower_bound().i64() ||
           (definition.atomic().lower_bound_inclusive() &&
            is_equal(value.i64(), definition.atomic().lower_bound().i64()));
  }
  // default
  return true;
}

bool check_upper_bound(const secretflow::spec::v1::Attribute& value,
                       const secretflow::spec::v1::AttributeDef& definition) {
  if (!definition.atomic().has_upper_bound()) {
    return true;
  }
  // for float
  if (definition.type() == secretflow::spec::v1::AttrType::AT_FLOAT) {
    return value.f() < definition.atomic().upper_bound().f() ||
           (definition.atomic().upper_bound_inclusive() &&
            is_equal(value.f(), definition.atomic().upper_bound().f()));
  }
  // for int
  if (definition.type() == secretflow::spec::v1::AttrType::AT_INT) {
    return value.i64() < definition.atomic().upper_bound().i64() ||
           (definition.atomic().upper_bound_inclusive() &&
            is_equal(value.i64(), definition.atomic().upper_bound().i64()));
  }
  // default
  return true;
}

std::string string_join(const std::vector<std::string>& strings,
                        const std::string& delim) {
  if (strings.empty()) {
    return std::string();
  }

  return std::accumulate(
      strings.begin() + 1, strings.end(), strings[0],
      [&delim](std::string x, std::string y) { return x + delim + y; });
}

void write_to_file(const std::string& message_str,
                   const std::string& filename) {
  std::ofstream ofs(filename, std::ios::out);
  ofs << message_str;
  ofs.close();
}

std::string read_from_file(const std::string& filename) {
  std::ifstream ifs(filename, std::ios::in);
  std::stringstream ss;
  ss << ifs.rdbuf();
  ifs.close();
  return ss.str();
}

}  // namespace component
}  // namespace teeapps
