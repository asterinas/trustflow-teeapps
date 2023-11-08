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

#include "teeapps/utils/tool.h"

#include "absl/strings/str_split.h"
#include "rapidjson/pointer.h"
#include "rapidjson/schema.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include "spdlog/spdlog.h"

namespace teeapps {
namespace utils {

rapidjson::Value* JsonProcess::GetValueByPath(const std::string& path) {
  if (path.empty() || path == "/") {
    return static_cast<rapidjson::Value*>(&doc_);
  }
  return rapidjson::GetValueByPointer(doc_, rapidjson::Pointer(path.c_str()));
}

std::string JsonProcess::GetStringByPath(const std::string& path) {
  if (path.empty()) {
    return "";
  }
  rapidjson::Value* pValue = GetValueByPath(path);
  if (pValue == nullptr || !pValue->IsString()) {
    return "";
  }
  return pValue->GetString();
}

// often call only once
std::string JsonProcess::Convert2String() {
  rapidjson::StringBuffer buffer;
  rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
  doc_.Accept(writer);
  return buffer.GetString();
}

// key format: "/params/appType"
int JsonProcess::ReplaceOrAdd(const std::string& key,
                              const std::string& value) {
  if (key.empty() || value.empty()) {
    SPDLOG_INFO("key {} or value {} is empty", key, value);
    return -1;
  }
  rapidjson::Value* pValue = GetValueByPath(key);
  if (pValue == nullptr) {
    SPDLOG_INFO("key {} in json not exist", key);
    return Add(key, value);
  }
  return Replace(key, value);
}

int JsonProcess::Replace(const std::string& key, const std::string& value) {
  rapidjson::Value* pValue = GetValueByPath(key);
  if (pValue == nullptr) {
    SPDLOG_INFO("Replace key {} not exist", key);
    return -1;
  }
  (*pValue).SetString(value.c_str(), alloc_);
  SPDLOG_INFO("Replace key {} value {} success", key, value);
  return 0;
}

int JsonProcess::Add(const std::string& key, const std::string& value) {
  std::vector<std::string_view> keys =
      absl::StrSplit(key, '/', absl::SkipEmpty());
  std::string final_key(keys.back());
  keys.pop_back();
  std::string path_key = fmt::format("/{}", fmt::join(keys, "/"));
  SPDLOG_INFO("Add path_key {} final_key {}", path_key, final_key);

  rapidjson::Value* pValue = GetValueByPath(path_key);
  if (pValue == nullptr || !pValue->IsObject()) {
    SPDLOG_INFO("Add path_key {} not exist or not object", path_key);
    return -1;
  }
  pValue->AddMember(
      rapidjson::Value(final_key.c_str(), final_key.length(), alloc_).Move(),
      rapidjson::Value(value.c_str(), value.length(), alloc_).Move(), alloc_);
  SPDLOG_INFO("Add key {} value {} success", key, value);
  return 0;
}

}  // namespace utils
}  // namespace teeapps
