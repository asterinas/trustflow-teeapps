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

#include "teeapps/utils/data_uri_util.h"

#include <regex>

#include "yacl/base/exception.h"

namespace teeapps {
namespace utils {

namespace {

constexpr char kId[] = "id";
constexpr char kDataSourceId[] = "datasource_id";
constexpr char kUri[] = "uri";
constexpr char kParamsDelimiter[] = "?";

}  // namespace

void ParseUriParams(const std::string& uri, httplib::Params& params) {
  const auto pos = uri.find(kParamsDelimiter);
  YACL_ENFORCE(pos != std::string::npos, "can not find ? in uri: {}", uri);

  httplib::detail::parse_query_text(uri.substr(pos + 1), params);
}

void ParseDmInputUri(const std::string& uri, std::string& input_id) {
  httplib::Params params;
  ParseUriParams(uri, params);
  const auto input_id_iter = params.find(kId);
  YACL_ENFORCE(input_id_iter != params.end(), "can not find {} in {}", kId,
               uri);

  input_id = input_id_iter->second;
}

void ParseDmOutputUri(const std::string& uri, std::string& data_source_id,
                      std::string& output_id, std::string& output_uri) {
  httplib::Params params;
  ParseUriParams(uri, params);
  const auto data_source_id_iter = params.find(kDataSourceId);
  YACL_ENFORCE(data_source_id_iter != params.end(), "can not find {} in {}",
               kDataSourceId, uri);
  const auto id_iter = params.find(kId);
  YACL_ENFORCE(id_iter != params.end(), "can not find {} in {}", kId, uri);
  const auto uri_iter = params.find(kUri);
  YACL_ENFORCE(uri_iter != params.end(), "can not find {} in {}", kUri, uri);

  data_source_id = data_source_id_iter->second;
  output_id = id_iter->second;
  output_uri = uri_iter->second;
}

void ParseKusciaInputUri(const std::string& uri, std::string& input_id,
                         std::string& input_uri) {
  httplib::Params params;
  ParseUriParams(uri, params);
  const auto id_iter = params.find(kId);
  YACL_ENFORCE(id_iter != params.end(), "can not find {} in {}", kId, uri);
  const auto uri_iter = params.find(kUri);
  YACL_ENFORCE(uri_iter != params.end(), "can not find {} in {}", kUri, uri);

  input_id = id_iter->second;
  input_uri = uri_iter->second;
}

void ParseLocalInputUri(const std::string& uri, std::string& input_id,
                        std::string& input_uri) {
  httplib::Params params;
  ParseUriParams(uri, params);
  const auto id_iter = params.find(kId);
  YACL_ENFORCE(id_iter != params.end(), "can not find {} in {}", kId, uri);
  const auto uri_iter = params.find(kUri);
  YACL_ENFORCE(uri_iter != params.end(), "can not find {} in {}", kUri, uri);

  input_id = id_iter->second;
  input_uri = uri_iter->second;
}

void ParseLocalOutputUri(const std::string& uri, std::string& output_id,
                         std::string& output_uri) {
  httplib::Params params;
  ParseUriParams(uri, params);
  const auto id_iter = params.find(kId);
  YACL_ENFORCE(id_iter != params.end(), "can not find {} in {}", kId, uri);
  const auto uri_iter = params.find(kUri);
  YACL_ENFORCE(uri_iter != params.end(), "can not find {} in {}", kUri, uri);

  output_id = id_iter->second;
  output_uri = uri_iter->second;
}

}  // namespace utils
}  // namespace teeapps