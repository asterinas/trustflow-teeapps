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

#include "teeapps/kuscia/kuscia_task_config.h"

#include "cppcodec/base64_rfc4648.hpp"
#include "rapidjson/document.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include "yacl/base/exception.h"

#include "teeapps/utils/crypto_util.h"
#include "teeapps/utils/data_uri_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"
#include "teeapps/utils/output_dist_data_util.h"

namespace teeapps {
namespace kuscia {

namespace {
constexpr char kTaskInputConfig[] = "task_input_config";
constexpr char kTeeTaskConfig[] = "tee_task_config";

constexpr char kDistData[] = "dist_data";

constexpr char kStorageTypeLocalFs[] = "local_fs";

constexpr char kConcatDelimiter[] = ".";

const rapidjson::Value& GetValueByKey(const rapidjson::Document& doc,
                                      const std::string& key) {
  YACL_ENFORCE(doc.HasMember(key.c_str()), "doc has no member {}", key);

  return doc[key.c_str()];
}

void GetJsonStrFromJsonValue(const rapidjson::Value& json_value,
                             std::string& json_str) {
  rapidjson::StringBuffer buffer;
  rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
  json_value.Accept(writer);
  json_str = buffer.GetString();
}

inline std::string GenKusciaInputUri(const std::string& data_id,
                                     const std::string& relative_uri) {
  return fmt::format("kuscia://input/?id={}&&uri={}", data_id, relative_uri);
}

}  // namespace

KusciaTaskConfig::KusciaTaskConfig(const std::string& kuscia_task_config_path,
                                   const std::string& data_mesh_endpoint) {
  SetFromFile(kuscia_task_config_path);
  FillFromDataMesh(data_mesh_endpoint);
}

void KusciaTaskConfig::SetFromJson(const std::string& kuscia_task_config_json) {
  rapidjson::Document doc;
  doc.Parse(kuscia_task_config_json.c_str());
  YACL_ENFORCE(!doc.HasParseError(), "failed to parse kuscia_task_config_json");

  rapidjson::Document sub_doc;
  sub_doc.Parse(GetValueByKey(doc, kTaskInputConfig).GetString());

  std::string tee_task_config_str;
  GetJsonStrFromJsonValue(GetValueByKey(sub_doc, kTeeTaskConfig),
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
    yacl::crypto::RsaVerifier::CreateFromCertPem(
        tee_task_config_.task_initiator_certs(0))
        ->Verify(tee_task_config_.task_initiator_id() + kConcatDelimiter +
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

void KusciaTaskConfig::SetFromFile(const std::string& kuscia_task_config_path) {
  const std::string kuscia_task_config_json =
      teeapps::utils::ReadFile(kuscia_task_config_path);
  SetFromJson(kuscia_task_config_json);
}

// Step 1: Complete inputs in node_eval_param and get data_source_id from
// datamesh Step 2: Complete output_uris in node_eval_param Step 3: Get
// storage_config from datamesh
void KusciaTaskConfig::FillFromDataMesh(const std::string& data_mesh_endpoint) {
  const auto& kuscia_client =
      teeapps::kuscia::KusciaClient::GetInstance(data_mesh_endpoint);
  std::string datasource_id;
  for (int i = 0; i < node_eval_param_.inputs_size(); i++) {
    const auto& input = node_eval_param_.inputs(i);
    std::string input_id;
    teeapps::utils::ParseDmInputUri(input.data_refs(0).uri(), input_id);
    const auto domain_data = kuscia_client.QueryDomainData(input_id);
    if (i == 0) {
      datasource_id = domain_data.datasource_id();
    } else {
      YACL_ENFORCE(
          datasource_id == domain_data.datasource_id(),
          "data_source_id not equal in kuscia_task_config:{} and datamesh{}",
          datasource_id, domain_data.datasource_id());
    }
    const auto dist_data_in_attr = domain_data.attributes().find(kDistData);
    secretflow::spec::v1::DistData dist_data;
    if (dist_data_in_attr != domain_data.attributes().end()) {
      JSON2PB(dist_data_in_attr->second, &dist_data);
    } else {
      teeapps::utils::ConvertDomainData2DistData(domain_data, dist_data);
    }
    dist_data.mutable_data_refs(0)->set_uri(
        GenKusciaInputUri(input_id, dist_data.data_refs(0).uri()));
    *(node_eval_param_.mutable_inputs(i)) = std::move(dist_data);
  }
  const auto domain_datasource =
      kuscia_client.QueryDomainDataSource(datasource_id);
  storage_config_.set_type(kStorageTypeLocalFs);
  secretflow::spec::v1::StorageConfig::LocalFSConfig local_fs_config;
  local_fs_config.set_wd(domain_datasource.info().localfs().path());
  *(storage_config_.mutable_local_fs()) = std::move(local_fs_config);
}

}  // namespace kuscia
}  // namespace teeapps