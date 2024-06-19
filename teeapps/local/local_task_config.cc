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

#include "teeapps/local/local_task_config.h"

#include "cppcodec/base64_rfc4648.hpp"
#include "rapidjson/document.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include "yacl/base/exception.h"
#include "yacl/crypto/sign/rsa_signing.h"

#include "teeapps/utils/crypto_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"

namespace teeapps {
namespace local {

namespace {

constexpr char kTaskInputConfig[] = "task_input_config";
constexpr char kTeeTaskConfig[] = "tee_task_config";
constexpr char kConcatDelimiter[] = ".";

const rapidjson::Value& GetValueByKey(const rapidjson::Document& doc,
                                      const std::string& key) {
  YACL_ENFORCE(doc.HasMember(key.c_str()), "doc has no member {}", key);

  return doc[key.c_str()];
}

const rapidjson::Value& GetValueByKey(const rapidjson::Value& value,
                                      const std::string& key) {
  YACL_ENFORCE(value.HasMember(key.c_str()), "value has no member {}", key);
  return value[key.c_str()];
}

void GetJsonStrFromJsonValue(const rapidjson::Value& json_value,
                             std::string& json_str) {
  rapidjson::StringBuffer buffer;
  rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
  json_value.Accept(writer);
  json_str = buffer.GetString();
}
}  // namespace

LocalTaskConfig::LocalTaskConfig(const std::string& local_task_config_path) {
  SetFromFile(local_task_config_path);
}

void LocalTaskConfig::SetFromJson(const std::string& local_task_config_json) {
  rapidjson::Document doc;
  doc.Parse(local_task_config_json.c_str());
  YACL_ENFORCE(!doc.HasParseError(), "failed to parse local_task_config_json");

  const rapidjson::Value& task_input_config =
      GetValueByKey(doc, kTaskInputConfig);

  std::string tee_task_config_str;
  GetJsonStrFromJsonValue(GetValueByKey(task_input_config, kTeeTaskConfig),
                          tee_task_config_str);
  JSON2PB(tee_task_config_str, &tee_task_config_);

  int certs_num = tee_task_config_.task_initiator_certs_size();
  YACL_ENFORCE(certs_num >= 1, "task_initiator_certs empty");
  // verify certs
  if (certs_num > 1) {
    for (int i = certs_num - 1; i > 0; i--) {
      YACL_ENFORCE(teeapps::utils::VerifyX509Cert(
                       tee_task_config_.task_initiator_certs(i - 1),
                       tee_task_config_.task_initiator_certs(i)),
                   "invalid x509 cert. index:{}. content:{}", i - 1,
                   tee_task_config_.task_initiator_certs(i - 1));
    }
  }

  // verify signature
  const auto signature =
      cppcodec::base64_rfc4648::decode(tee_task_config_.signature());
  if (tee_task_config_.sign_algorithm() == teeapps::utils::kRs256) {
    yacl::crypto::RsaVerifier(yacl::crypto::LoadX509CertPublicKeyFromBuf(
                                  tee_task_config_.task_initiator_certs(0)))
        .Verify(tee_task_config_.task_initiator_id() + kConcatDelimiter +
                    tee_task_config_.scope() + kConcatDelimiter +
                    tee_task_config_.task_body(),
                signature);
  } else {
    YACL_THROW("sign_algorithm {} not support",
               tee_task_config_.sign_algorithm());
  }

  const auto task_body_bytes =
      cppcodec::base64_rfc4648::decode(tee_task_config_.task_body());
  JSON2PB(std::string(task_body_bytes.begin(), task_body_bytes.end()),
          &node_eval_param_);
}

void LocalTaskConfig::SetFromFile(const std::string& local_task_config_path) {
  const std::string local_task_config_json =
      teeapps::utils::ReadFile(local_task_config_path);
  SetFromJson(local_task_config_json);
}

}  // namespace local
}  // namespace teeapps