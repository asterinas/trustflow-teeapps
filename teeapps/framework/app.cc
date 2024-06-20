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

#include "teeapps/framework/app.h"

#include <filesystem>

#include "absl/strings/str_split.h"
#include "cppcodec/base64_rfc4648.hpp"
#include "spdlog/spdlog.h"
#include "yacl/crypto/hash/hash_utils.h"
#include "yacl/crypto/key_utils.h"

#include "teeapps/component/component_list.h"
#include "teeapps/framework/constants.h"
#include "teeapps/framework/subprocess.h"
#include "teeapps/kuscia/kuscia_task_config.h"
#include "teeapps/local/local_task_config.h"
#include "teeapps/utils/crypto_util.h"
#include "teeapps/utils/data_uri_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"
#include "teeapps/utils/output_dist_data_util.h"
#include "teeapps/utils/ra_util.h"
#include "teeapps/utils/task_config_util.h"

namespace teeapps {
namespace framework {

namespace {
const std::unordered_map<std::string, std::string> kTeeappsSubjectMap = {
    {"C", "CN"},       {"ST", "HZ"},         {"L", "HZ"},
    {"O", "AntGroup"}, {"OU", "SecretFlow"}, {"CN", "TeeApps"}};

constexpr uint8_t kKeyBytes = 32;
constexpr uint32_t kRsaBitLength = 3072;
constexpr uint32_t kCertDays = 365;

// python path
constexpr char kPyPath[] = "/home/teeapp/python/bin/python3";
constexpr char kOcclumPyPath[] = "/bin/python3";

std::string GenCmd(const std::string& component_name, const std::string& plat) {
  const auto py_name = teeapps::component::comp_py_map.find(component_name);
  YACL_ENFORCE(py_name != teeapps::component::comp_py_map.end(),
               "can not find py_name for {}", component_name);
  if (plat == teeapps::framework::kPlatSim ||
      plat == teeapps::framework::kPlatTdx ||
      plat == teeapps::framework::kPlatCsv) {
    return fmt::format("{},/home/teeapp/{}/teeapps/biz/{}", kPyPath, plat,
                       py_name->second);
  } else if (plat == teeapps::framework::kPlatSgx) {
    return fmt::format("{},/{}", kOcclumPyPath, py_name->second);
  } else {
    YACL_THROW("plat {} not support", plat);
  }
}

}  // namespace

App::App(const std::string& plat, const std::string& app_mode,
         const std::string& entry_task_config_path,
         const std::string& data_mesh_endpoint, const bool enable_capsule_tls) {
  YACL_ENFORCE(plat == teeapps::framework::kPlatSim ||
                   plat == teeapps::framework::kPlatSgx ||
                   plat == teeapps::framework::kPlatTdx ||
                   plat == teeapps::framework::kPlatCsv,
               "plat {} not support", plat);
  plat_ = plat;
  YACL_ENFORCE(app_mode == teeapps::framework::kAppModeKuscia ||
                   app_mode == teeapps::framework::kAppModeLocal,
               "app mode {} not support", app_mode);
  app_mode_ = app_mode;
  if (app_mode_ == teeapps::framework::kAppModeKuscia) {
    SPDLOG_INFO("Start parsing Kuscia Task Config...");
    const auto kuscia_task_config = teeapps::kuscia::KusciaTaskConfig(
        entry_task_config_path, data_mesh_endpoint);

    node_eval_param_ = std::move(kuscia_task_config.node_eval_param());
    storage_config_ = std::move(kuscia_task_config.storage_config());
    tee_task_config_ = std::move(kuscia_task_config.tee_task_config());
    SPDLOG_INFO("Parsing Kuscia Task Config succeed");
  } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
    SPDLOG_INFO("Start parsing Local Task Config...");
    const auto local_task_config =
        teeapps::local::LocalTaskConfig(entry_task_config_path);

    node_eval_param_ = std::move(local_task_config.node_eval_param());
    tee_task_config_ = std::move(local_task_config.tee_task_config());
    SPDLOG_INFO("Parsing Local Task Config succeed");
  } else {
    YACL_THROW("app mode {} not support", app_mode_);
  }

  const auto comp_def =
      teeapps::component::COMP_DEF_MAP.find(teeapps::component::GenCompFullName(
          node_eval_param_.domain(), node_eval_param_.name(),
          node_eval_param_.version()));
  YACL_ENFORCE(
      comp_def != teeapps::component::COMP_DEF_MAP.end(),
      "can not find corresponding Component definition in COMP_DEF_MAP");
  component_def_ = comp_def->second;

  auto [pk_buf, sk_buf] = yacl::crypto::GenRsaKeyPairToPemBuf(kRsaBitLength);

  auto pk = yacl::crypto::LoadKeyFromBuf(yacl::ByteContainerView(pk_buf));
  auto sk = yacl::crypto::LoadKeyFromBuf(yacl::ByteContainerView(sk_buf));
  auto cert = yacl::crypto::MakeX509Cert(pk, sk, kTeeappsSubjectMap, kCertDays,
                                         yacl::crypto::HashAlgorithm::SHA256);
  auto cert_buf = yacl::crypto::ExportX509CertToBuf(cert);

  private_key_ = std::string(sk_buf.data<char>(), sk_buf.size());
  cert_ = std::string(cert_buf.data<char>(), cert_buf.size());

  SPDLOG_INFO("Gen teeapps private key and certificate success");

  capsule_manager_client_ = std::make_unique<CapsuleManagerClient>(
      tee_task_config_.capsule_manager_endpoint(), enable_capsule_tls);

  SPDLOG_INFO("Create Capsule Manager Client success");
}

void App::Run() {
  try {
    PreProcess();
    ExecCmd();
    PostProcess();
  } catch (const std::exception& e) {
    SPDLOG_ERROR("Running TEE application failed, error message: {}", e.what());
    std::string err_detail =
        fmt::format("task process error: {}\n task execution error: {}",
                    task_process_err_, task_execution_err_);
    YACL_THROW("Exiting application with exception {}", err_detail);
  } catch (const std::string& e_str) {
    YACL_THROW("Exiting application with exception {}", e_str);
  }
}

void App::GetInputDataKeys(
    std::unordered_map<std::string, std::string>& data_keys_map) const {
  secretflowapis::v2::sdc::capsule_manager::ResourceRequest resource_request;
  resource_request.set_initiator_party_id(tee_task_config_.task_initiator_id());
  resource_request.set_op_name(node_eval_param_.name());
  resource_request.set_scope(tee_task_config_.scope());

  for (const auto& input : node_eval_param_.inputs()) {
    YACL_ENFORCE(
        input.type() != teeapps::component::DistDataType::VERTICAL_TABLE,
        "teeapps will not deal with vertical table");
    if (input.type() == teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
      // Individual Table
      secretflow::spec::v1::IndividualTable individual_table;
      input.meta().UnpackTo(&individual_table);
      YACL_ENFORCE(input.data_refs_size() == 1,
                   "individual_table data_refs' size should be 1, got {}",
                   input.data_refs_size());
      secretflowapis::v2::sdc::capsule_manager::ResourceRequest::Resource
          resource;
      const auto& data_ref = input.data_refs(0);
      const auto& schema = individual_table.schema();
      std::string input_id, _;
      if (app_mode_ == teeapps::framework::kAppModeKuscia) {
        teeapps::utils::ParseKusciaInputUri(data_ref.uri(), input_id, _);
      } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
        teeapps::utils::ParseLocalInputUri(data_ref.uri(), input_id, _);
      } else {
        YACL_THROW("app mode {} not support", app_mode_);
      }
      resource.set_resource_uri(input_id);
      resource.mutable_columns()->Add(schema.ids().begin(), schema.ids().end());
      resource.mutable_columns()->Add(schema.features().begin(),
                                      schema.features().end());
      resource.mutable_columns()->Add(schema.labels().begin(),
                                      schema.labels().end());
      // TODO set op attrs from component in json format
      *(resource_request.add_resources()) = std::move(resource);
    } else {
      // sf.model.* sf.rule.* sf.report ...
      secretflowapis::v2::sdc::capsule_manager::ResourceRequest::Resource
          resource;
      std::string input_id, _;
      if (app_mode_ == teeapps::framework::kAppModeKuscia) {
        teeapps::utils::ParseKusciaInputUri(input.data_refs(0).uri(), input_id,
                                            _);
      } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
        teeapps::utils::ParseLocalInputUri(input.data_refs(0).uri(), input_id,
                                           _);
      } else {
        YACL_THROW("app mode {} not support", app_mode_);
      }
      resource.set_resource_uri(input_id);
      // TODO set op attrs from component in json format
      *(resource_request.add_resources()) = std::move(resource);
    }
  }
  // TODO add env and global attrs

  SPDLOG_INFO("Try to get Ra Cert from Capsule Manager");
  capsule_manager_client_->GetRaCert();
  SPDLOG_INFO("Got Ra Cert");
  SPDLOG_INFO("Try to get data keys from Capsule Manager");
  auto data_keys = capsule_manager_client_->GetDataKeys(
      plat_, cert_, private_key_, resource_request);
  for (const auto& data_key : data_keys) {
    // data_key.resource_uri() represents {data_uuid} in capsule manager
    data_keys_map.emplace(data_key.resource_uri(), data_key.data_key_b64());
  }
  SPDLOG_INFO("Got data keys");
}

// download data, decrypt Data to data path
void App::ProcessInput(
    const std::unordered_map<std::string, std::string>& data_keys_map) const {
  std::filesystem::create_directories(teeapps::framework::kTaskBaseDir);
  for (const auto& input : node_eval_param_.inputs()) {
    // data_path is the local path of decrypted input data(in TaskConfig of
    // teeapps)
    const std::string data_path = teeapps::utils::GenDataPath(input.name());
    YACL_ENFORCE(
        input.type() != teeapps::component::DistDataType::VERTICAL_TABLE,
        "teeapps will not deal with vertical table");
    SPDLOG_INFO("Downloading Individual Table Or Model/Rule and Decryption...");
    std::string input_id, input_uri, file_full_path;
    if (app_mode_ == teeapps::framework::kAppModeKuscia) {
      teeapps::utils::ParseKusciaInputUri(input.data_refs(0).uri(), input_id,
                                          input_uri);
      file_full_path = storage_config_.local_fs().wd() + "/" + input_uri;
    } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
      teeapps::utils::ParseLocalInputUri(input.data_refs(0).uri(), input_id,
                                         input_uri);
      file_full_path = input_uri;
    } else {
      YACL_THROW("app mode {} not support", app_mode_);
    }
    std::string tmp_encryption_path =
        teeapps::utils::GenTmpEncDataPath(input.name());
    std::filesystem::remove(tmp_encryption_path);
    // TODO download data
    std::filesystem::copy(file_full_path, tmp_encryption_path);
    const auto data_key = data_keys_map.find(input_id);
    YACL_ENFORCE(data_key != data_keys_map.end(),
                 "can not find data key correspond input_id:{}", input_id);
    SPDLOG_INFO("Decrypting {} ...", input_uri);
    teeapps::utils::DecryptFile(
        tmp_encryption_path, data_path,
        cppcodec::base64_rfc4648::decode(data_key->second));
    std::filesystem::remove(tmp_encryption_path);
    SPDLOG_INFO("Decrypting {} success", input_uri);
  }
}

// Step 1: Verify node_eval_params with component_def
// Step 2: Generate ResourceRequest and get data keys from
// capsule manager
// Step 3: Download input data from storage(eg. local_fs, minio)
// and decrypt
// Step 4: Convert component to task execution config
void App::PreProcess() {
  SPDLOG_INFO("Starting pre-processing, component {}-{}-{}...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());

  // Step 1 verify node_eval_params with component_def
  const auto eval_param_reader =
      teeapps::component::EvalParamReader(&node_eval_param_, &component_def_);

  // Step 2 generate ResourceRequest and get data keys from capsule manager
  std::unordered_map<std::string, std::string> data_keys_map;
  GetInputDataKeys(data_keys_map);
  // Step 3 download data, decrypt Data to data path
  ProcessInput(data_keys_map);

  // Step 4 convert component instance to task execution config
  teeapps::utils::GenAndDumpTaskConfig(app_mode_, component_def_,
                                       eval_param_reader);

  cmd_ = GenCmd(component_def_.name(), plat_);

  SPDLOG_INFO("Pre-processing, component {}-{}-{} succeed...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());
}

void App::ExecCmd() {
  SPDLOG_INFO("Start executing, component {}-{}-{}...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());
  SPDLOG_INFO("Launch command: {} {}", cmd_,
              teeapps::framework::kTaskConfigPath);
  std::vector<std::string> args = absl::StrSplit(cmd_, ',', absl::SkipEmpty());
  args.emplace_back(teeapps::framework::kTaskConfigPath);
  teeapps::framework::Subprocess subprocess(args);
  auto err_msg = subprocess.Launch();
  SPDLOG_INFO("stdout: \n {}", subprocess.Stdout());
  if (err_msg.has_value()) {
    task_succeed_ = false;
    task_process_err_ = err_msg.value();
    SPDLOG_ERROR("Task process error message: {}", task_process_err_);
  }
  // Note: stderr is not empty doesn't mean that the task is failed as there may
  // be some warnings
  if (!subprocess.Stderr().empty()) {
    task_execution_err_ = subprocess.Stderr();
    SPDLOG_ERROR("Task execution stderr: {}", task_execution_err_);
  }
  YACL_ENFORCE(task_succeed_, "Executing, component {}-{}-{} failed",
               node_eval_param_.domain(), node_eval_param_.name(),
               node_eval_param_.version());
  SPDLOG_INFO("Executing, component {}-{}-{} succeed...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());
}

void App::ProcessOutput() {
  const int output_size = component_def_.outputs_size();
  YACL_ENFORCE(node_eval_param_.output_uris_size() == output_size,
               "output_uris's size {} not match component_def's size {}",
               node_eval_param_.output_uris_size(), output_size);

  if (app_mode_ == teeapps::framework::kAppModeKuscia) {
    std::vector<secretflow::spec::v1::DistData> dist_datas(output_size);
    teeapps::utils::FillOutputDistData(dist_datas, node_eval_param_,
                                       component_def_);
    for (int i = 0; i < output_size; i++) {
      // create domain data
      ::kuscia::proto::api::v1alpha1::datamesh::DomainData domain_data;
      std::string output_datasource_id, output_id, output_uri;
      teeapps::utils::ParseDmOutputUri(node_eval_param_.output_uris(i),
                                       output_datasource_id, output_id,
                                       output_uri);
      teeapps::utils::ConvertDistData2DomainData(
          output_id, dist_datas[i], output_uri, output_datasource_id,
          domain_data);
      const auto& kuscia_client =
          teeapps::kuscia::KusciaClient::GetInstance("");
      kuscia_client.CreateDomainData(domain_data);
      const std::string local_res_path = teeapps::utils::GenDataPath(output_id);
      const std::string output_full_path =
          storage_config_.local_fs().wd() + "/" + output_uri;
      // upload result
      teeapps::utils::CopyFile(local_res_path, output_full_path);
    }
  } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
    for (const auto& uri : node_eval_param_.output_uris()) {
      std::string output_id, output_uri;
      teeapps::utils::ParseLocalOutputUri(uri, output_id, output_uri);
      const std::string local_res_path = teeapps::utils::GenDataPath(output_id);
      const std::string output_full_path = output_uri;
      //  upload result
      teeapps::utils::CopyFile(local_res_path, output_full_path);
    }
  } else {
    YACL_THROW("app mode {} not support", app_mode_);
  }
}

// Step 1: encrypt output data
// Step 2: create data keys
// Step 3: (check and convert teeapps' outputs to DistData in kuscia mode)
// Step 4: upload data, (create domain data in kuscia mode)
void App::PostProcess() {
  SPDLOG_INFO("Start post-processing, component {}-{}-{}...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());
  // delete inputs' decryption result
  for (const auto& input : node_eval_param_.inputs()) {
    std::filesystem::remove(teeapps::utils::GenDataPath(input.name()));
  }
  SPDLOG_INFO("Delete inputs' decryption result success");

  for (int i = 0; i < node_eval_param_.output_uris_size(); i++) {
    // Reports do not need to be encrypted
    if (component_def_.outputs(i).types(0) ==
        teeapps::component::DistDataType::REPORT) {
      continue;
    }
    const auto& uri = node_eval_param_.output_uris(i);
    // Step 1: encrypt output data
    const std::vector<uint8_t> data_key =
        yacl::crypto::RandBytes(kKeyBytes, true);
    std::string data_source_id, output_id, output_uri;
    if (app_mode_ == teeapps::framework::kAppModeKuscia) {
      teeapps::utils::ParseDmOutputUri(uri, data_source_id, output_id,
                                       output_uri);
    } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
      teeapps::utils::ParseLocalOutputUri(uri, output_id, output_uri);
    } else {
      YACL_THROW("app mode {} not support", app_mode_);
    }
    teeapps::utils::EncryptFile(teeapps::utils::GenDataPath(output_id),
                                data_key);
    secretflowapis::v2::sdc::capsule_manager::CreateResultDataKeyRequest::Body
        body;
    body.set_resource_uri(output_id);
    body.set_data_key_b64(cppcodec::base64_rfc4648::encode(data_key));
    body.set_scope(tee_task_config_.scope());
    for (const auto& input : node_eval_param_.inputs()) {
      for (const auto& data_ref : input.data_refs()) {
        std::string input_id, input_uri;
        if (app_mode_ == teeapps::framework::kAppModeKuscia) {
          teeapps::utils::ParseKusciaInputUri(data_ref.uri(), input_id,
                                              input_uri);
        } else if (app_mode_ == teeapps::framework::kAppModeLocal) {
          teeapps::utils::ParseLocalInputUri(data_ref.uri(), input_id,
                                             input_uri);
        } else {
          YACL_THROW("app mode {} not support", app_mode_);
        }
        body.add_ancestor_uuids(input_id);
      }
    }
    capsule_manager_client_->CreateResultDataKey(plat_, cert_, private_key_,
                                                 body);
  }

  // Step 3: (check and convert teeapps' outputs to DistData in kuscia mode)
  // Step 4: upload data, (create domain data in kuscia mode)
  ProcessOutput();

  SPDLOG_INFO("Post-processing, component {}-{}-{} succeed...",
              node_eval_param_.domain(), node_eval_param_.name(),
              node_eval_param_.version());
}

}  // namespace framework
}  // namespace teeapps