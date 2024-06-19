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

#include <assert.h>

#include <fstream>
#include <iostream>
#include <numeric>
#include <optional>
#include <sstream>

#include "google/protobuf/util/json_util.h"

#include "secretflow/spec/v1/component.pb.h"
#include "secretflow/spec/v1/data.pb.h"
#include "secretflow/spec/v1/evaluation.pb.h"

#define PROTOBUF2JSON(pbmsg, p_jsonstr)                               \
  do {                                                                \
    ::google::protobuf::util::JsonPrintOptions options;               \
    options.preserve_proto_field_names = true;                        \
    using google::protobuf::util::MessageToJsonString;                \
    (p_jsonstr)->clear();                                             \
    auto status = MessageToJsonString((pbmsg), (p_jsonstr), options); \
    assert(status.ok());                                              \
  } while (0)

#define JSON2PROTOBUF(jsonstr, p_pbmsg)                      \
  do {                                                       \
    using google::protobuf::util::JsonStringToMessage;       \
    auto status = JsonStringToMessage((jsonstr), (p_pbmsg)); \
    assert(status.ok());                                     \
  } while (0)

namespace teeapps {
namespace component {

enum IoType { INPUT = 1, OUTPUT = 2 };

struct DistDataType {
  static constexpr char VERTICAL_TABLE[] = "sf.table.vertical_table";
  static constexpr char INDIVIDUAL_TABLE[] = "sf.table.individual";
  static constexpr char LR_MODEL[] = "sf.model.lr";
  static constexpr char XGB_MODEL[] = "sf.model.xgb";
  static constexpr char LGBM_MODEL[] = "sf.model.lgbm";
  static constexpr char WOE_RUNNING_RULE[] = "sf.rule.woe_binning";
  static constexpr char REPORT[] = "sf.report";

  static const std::unordered_set<std::string>& get_all_types() {
    static const std::unordered_set<std::string> types{
        VERTICAL_TABLE, INDIVIDUAL_TABLE, LR_MODEL, XGB_MODEL,
        LGBM_MODEL,     WOE_RUNNING_RULE, REPORT};
    return types;
  }
};

struct TableColParam {
  std::string name;
  std::string desc;
  std::optional<int> col_min_cnt_inclusive = std::nullopt;
  std::optional<int> col_max_cnt_inclusive = std::nullopt;
  TableColParam(const std::string& tname, const std::string& tdesc,
                const std::optional<int>& tcol_min_cnt_inclusive = std::nullopt,
                const std::optional<int>& tcol_max_cnt_inclusive = std::nullopt)
      : name(tname),
        desc(tdesc),
        col_min_cnt_inclusive(tcol_min_cnt_inclusive),
        col_max_cnt_inclusive(tcol_max_cnt_inclusive) {}
};

struct CompEvalContext {
  std::string local_fs_wd;
};

template <typename T>
bool is_equal(const T& t1, const T& t2) {
  return t1 == t2;
};

template <>
inline bool is_equal<float>(const float& t1, const float& t2) {
  return abs(t1 - t2) < std::numeric_limits<float>::epsilon();
};

template <>
inline bool is_equal<double>(const double& t1, const double& t2) {
  return abs(t1 - t2) < std::numeric_limits<double>::epsilon();
};

template <typename T>
secretflow::spec::v1::AttrType get_list_type() {
  return secretflow::spec::v1::AttrType::AT_STRINGS;
};

template <>
inline secretflow::spec::v1::AttrType get_list_type<float>() {
  return secretflow::spec::v1::AttrType::AT_FLOATS;
};

template <>
inline secretflow::spec::v1::AttrType get_list_type<double>() {
  return secretflow::spec::v1::AttrType::AT_FLOATS;
};

template <>
inline secretflow::spec::v1::AttrType get_list_type<int>() {
  return secretflow::spec::v1::AttrType::AT_INTS;
};

template <>
inline secretflow::spec::v1::AttrType get_list_type<int64_t>() {
  return secretflow::spec::v1::AttrType::AT_INTS;
};

template <>
inline secretflow::spec::v1::AttrType get_list_type<bool>() {
  return secretflow::spec::v1::AttrType::AT_BOOLS;
};

template <typename T>
secretflow::spec::v1::AttrType get_single_type() {
  return secretflow::spec::v1::AttrType::AT_STRING;
};

template <>
inline secretflow::spec::v1::AttrType get_single_type<float>() {
  return secretflow::spec::v1::AttrType::AT_FLOAT;
};

template <>
inline secretflow::spec::v1::AttrType get_single_type<double>() {
  return secretflow::spec::v1::AttrType::AT_FLOAT;
};

template <>
inline secretflow::spec::v1::AttrType get_single_type<int>() {
  return secretflow::spec::v1::AttrType::AT_INT;
};

template <>
inline secretflow::spec::v1::AttrType get_single_type<int64_t>() {
  return secretflow::spec::v1::AttrType::AT_INT;
};

template <>
inline secretflow::spec::v1::AttrType get_single_type<bool>() {
  return secretflow::spec::v1::AttrType::AT_BOOL;
};

template <typename T>
void set_list_value(secretflow::spec::v1::Attribute* attr,
                    const std::vector<T>& values) {
  attr->set_is_na(true);
};

template <>
inline void set_list_value<std::string>(
    secretflow::spec::v1::Attribute* attr,
    const std::vector<std::string>& values) {
  attr->mutable_ss()->CopyFrom({values.begin(), values.end()});
};

template <>
inline void set_list_value<float>(secretflow::spec::v1::Attribute* attr,
                                  const std::vector<float>& values) {
  attr->mutable_fs()->CopyFrom({values.begin(), values.end()});
};

template <>
inline void set_list_value<double>(secretflow::spec::v1::Attribute* attr,
                                   const std::vector<double>& values) {
  attr->mutable_fs()->CopyFrom({values.begin(), values.end()});
};

template <>
inline void set_list_value<int>(secretflow::spec::v1::Attribute* attr,
                                const std::vector<int>& values) {
  attr->mutable_i64s()->CopyFrom({values.begin(), values.end()});
};

template <>
inline void set_list_value<int64_t>(secretflow::spec::v1::Attribute* attr,
                                    const std::vector<int64_t>& values) {
  attr->mutable_i64s()->CopyFrom({values.begin(), values.end()});
};

template <>
inline void set_list_value<bool>(secretflow::spec::v1::Attribute* attr,
                                 const std::vector<bool>& values) {
  attr->mutable_bs()->CopyFrom({values.begin(), values.end()});
};

template <typename T>
void set_single_value(secretflow::spec::v1::Attribute* attr, const T& value) {
  attr->set_is_na(true);
};

template <>
inline void set_single_value<std::string>(secretflow::spec::v1::Attribute* attr,
                                          const std::string& value) {
  attr->set_s(value);
};

template <>
inline void set_single_value<float>(secretflow::spec::v1::Attribute* attr,
                                    const float& value) {
  attr->set_f(value);
};

template <>
inline void set_single_value<double>(secretflow::spec::v1::Attribute* attr,
                                     const double& value) {
  attr->set_f(value);
};

template <>
inline void set_single_value<int>(secretflow::spec::v1::Attribute* attr,
                                  const int& value) {
  attr->set_i64(value);
};

template <>
inline void set_single_value<int64_t>(secretflow::spec::v1::Attribute* attr,
                                      const int64_t& value) {
  attr->set_i64(value);
};

template <>
inline void set_single_value<bool>(secretflow::spec::v1::Attribute* attr,
                                   const bool& value) {
  attr->set_b(value);
};

template <typename T, bool is_list>
std::vector<T> get_attr_value(const secretflow::spec::v1::Attribute& value) {
  return std::vector<T>();
};

template <>
inline std::vector<double> get_attr_value<double, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<double>(value.fs().begin(), value.fs().end());
};

template <>
inline std::vector<double> get_attr_value<double, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<double>{value.f()};
};

template <>
inline std::vector<float> get_attr_value<float, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<float>(value.fs().begin(), value.fs().end());
};

template <>
inline std::vector<float> get_attr_value<float, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<float>{value.f()};
};

template <>
inline std::vector<int> get_attr_value<int, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<int>(value.i64s().begin(), value.i64s().end());
};

template <>
inline std::vector<int> get_attr_value<int, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<int>{(int)value.i64()};
};

template <>
inline std::vector<int64_t> get_attr_value<int64_t, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<int64_t>(value.i64s().begin(), value.i64s().end());
};

template <>
inline std::vector<int64_t> get_attr_value<int64_t, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<int64_t>{value.i64()};
};

template <>
inline std::vector<std::string> get_attr_value<std::string, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<std::string>(value.ss().begin(), value.ss().end());
};

template <>
inline std::vector<std::string> get_attr_value<std::string, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<std::string>{value.s()};
};

template <>
inline std::vector<bool> get_attr_value<bool, true>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<bool>(value.bs().begin(), value.bs().end());
};

template <>
inline std::vector<bool> get_attr_value<bool, false>(
    const secretflow::spec::v1::Attribute& value) {
  return std::vector<bool>{value.b()};
};

template <int T>
struct get_attr_info {
  static const bool is_list = true;
  typedef std::string attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_FLOAT> {
  static const bool is_list = false;
  typedef float attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_FLOATS> {
  static const bool is_list = true;
  typedef float attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_INT> {
  static const bool is_list = false;
  typedef int64_t attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_INTS> {
  static const bool is_list = true;
  typedef int64_t attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_STRING> {
  static const bool is_list = false;
  typedef std::string attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_STRINGS> {
  static const bool is_list = true;
  typedef std::string attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_BOOL> {
  static const bool is_list = false;
  typedef bool attr_type;
};

template <>
struct get_attr_info<secretflow::spec::v1::AttrType::AT_BOOLS> {
  static const bool is_list = true;
  typedef bool attr_type;
};

template <typename... Args>
std::string string_format(const char* format, Args... args) {
  size_t length = std::snprintf(nullptr, 0, format, args...);
  if (length == 0) {
    return "";
  }

  char* buf = new char[length + 1];
  std::snprintf(buf, length + 1, format, args...);

  std::string str(buf);
  delete[] buf;
  return str;
}

bool check_attr_type(const secretflow::spec::v1::AttrType& attr_type);

bool check_io_def(const secretflow::spec::v1::IoDef* io_def);

bool check_table_attr_col_cnt(
    const secretflow::spec::v1::Attribute& value,
    const secretflow::spec::v1::IoDef::TableAttrDef& definition);

bool check_allowed_values(const secretflow::spec::v1::Attribute& value,
                          const secretflow::spec::v1::AttributeDef& definition);

bool check_lower_bound(const secretflow::spec::v1::Attribute& value,
                       const secretflow::spec::v1::AttributeDef& definition);

bool check_upper_bound(const secretflow::spec::v1::Attribute& value,
                       const secretflow::spec::v1::AttributeDef& definition);

std::string string_join(const std::vector<std::string>& strings,
                        const std::string& delim);

void write_to_file(const std::string& message_str, const std::string& filename);

std::string read_from_file(const std::string& filename);

}  // namespace component
}  // namespace teeapps
