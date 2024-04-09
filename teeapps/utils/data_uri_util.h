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

#define CPPHTTPLIB_OPENSSL_SUPPORT
#include "httplib.h"

namespace teeapps {
namespace utils {

void ParseUriParams(const std::string& uri, httplib::Params& params);

void ParseDmInputUri(const std::string& uri, std::string& input_id);

void ParseDmOutputUri(const std::string& uri, std::string& data_source_id,
                      std::string& output_id, std::string& output_uri);

void ParseKusciaInputUri(const std::string& uri, std::string& input_id,
                         std::string& input_uri);

void ParseLocalInputUri(const std::string& uri, std::string& input_id,
                        std::string& input_uri);

void ParseLocalOutputUri(const std::string& uri, std::string& output_id,
                         std::string& output_uri);
}  // namespace utils
}  // namespace teeapps