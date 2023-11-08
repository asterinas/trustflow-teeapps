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

#include <string>
#include <vector>

#include "rapidjson/document.h"
#include "yacl/base/exception.h"

namespace teeapps {
namespace utils {

class JsonProcess {
 public:
  explicit JsonProcess(const std::string& json_str)
      : alloc_(doc_.GetAllocator()) {
    rapidjson::ParseResult ok = doc_.Parse(json_str.c_str());
    YACL_ENFORCE(
        ok, "Catch Rapidjson error(code={}, offset={}) while parsing json={}",
        ok.Code(), ok.Offset(), json_str);
  }
  // forbid
  JsonProcess(const JsonProcess& rhs) = delete;
  JsonProcess(JsonProcess&& rhs) = delete;
  JsonProcess& operator=(const JsonProcess& rhs) = delete;

  int ReplaceOrAdd(const std::string& key, const std::string& value);
  int Replace(const std::string& key, const std::string& value);
  int Add(const std::string& key, const std::string& value);
  std::string GetStringByPath(const std::string& path);
  std::string Convert2String();

 private:
  rapidjson::Document doc_;
  rapidjson::Document::AllocatorType& alloc_;

  rapidjson::Value* GetValueByPath(const std::string& path);
};

}  // namespace utils
}  // namespace teeapps
