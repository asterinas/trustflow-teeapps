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

#include "teeapps/framework/capsule_manager_client.h"

#include "cppcodec/base64_url_unpadded.hpp"
#include "spdlog/spdlog.h"
#include "yacl/crypto/hash/hash_utils.h"
#include "yacl/crypto/rand/rand.h"

#include "teeapps/framework/constants.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/ra_util.h"

namespace teeapps {
namespace framework {

namespace {
namespace capsule_manager = ::secretflowapis::v2::sdc::capsule_manager;

constexpr uint8_t kNonceBytes = 16;

constexpr uint32_t kGrpcMaxMsgSizeMb = 1024;
constexpr uint32_t kGrpcTimeoutMs = 5 * 1000;

constexpr char kClientCertPath[] = "/host/certs/client.crt";
constexpr char kClientKeyPath[] = "/host/certs/client.key";
constexpr char kCaCertPath[] = "/host/certs/ca.crt";

inline void VerifySfResponseStatus(const secretflowapis::v2::Status& status) {
  YACL_ENFORCE(status.code() == secretflowapis::v2::Code::OK,
               "Call service failed, error code: {}, message: {}",
               status.code(), status.message());
}

}  // namespace

CapsuleManagerClient::CapsuleManagerClient(
    const std::string& capsule_manager_endpoint,
    const bool enable_capsule_tls) {
  ::grpc::ChannelArguments chan_args;
  chan_args.SetMaxReceiveMessageSize(kGrpcMaxMsgSizeMb * 1024 * 1024);
  chan_args.SetGrpclbFallbackTimeout(kGrpcTimeoutMs);
  if (enable_capsule_tls) {
    ::grpc::SslCredentialsOptions ssl_opts;
    ssl_opts.pem_cert_chain = teeapps::utils::ReadFile(kClientCertPath);
    ssl_opts.pem_private_key = teeapps::utils::ReadFile(kClientKeyPath);
    ssl_opts.pem_root_certs = teeapps::utils::ReadFile(kCaCertPath);
    const auto creds = ::grpc::SslCredentials(ssl_opts);
    capsule_manager_stub_ =
        capsule_manager::CapsuleManager::NewStub(::grpc::CreateCustomChannel(
            capsule_manager_endpoint, creds, chan_args));
  } else {
    capsule_manager_stub_ =
        capsule_manager::CapsuleManager::NewStub(::grpc::CreateCustomChannel(
            capsule_manager_endpoint, ::grpc::InsecureChannelCredentials(),
            chan_args));
  }
}

std::string CapsuleManagerClient::GetRaCert() {
  capsule_manager::GetRaCertRequest request;
  capsule_manager::GetRaCertResponse response;

  const auto nonce = yacl::crypto::RandBytes(kNonceBytes);
  request.set_nonce(cppcodec::base64_url_unpadded::encode(nonce));

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);

  const auto status =
      capsule_manager_stub_->GetRaCert(&context, request, &response);
  YACL_ENFORCE(status.ok(),
               "Calling GetRaCert failed, error code: {}, message: {}",
               static_cast<int>(status.error_code()), status.error_message());

  VerifySfResponseStatus(response.status());

  capsule_manager_cert_ = response.cert();

  return response.cert();
}

std::vector<capsule_manager::DataKey> CapsuleManagerClient::GetDataKeys(
    const std::string& plat, const std::string& cert,
    const std::string& private_key,
    capsule_manager::ResourceRequest& resource_req) const {
  YACL_ENFORCE(capsule_manager_cert_.size() > 0,
               "capsule_manager_cert not found. you should call GetRaCert() "
               "before other capsule_manager's interface");

  // get encrypted data key from capsule manager
  capsule_manager::GetDataKeysRequest request;

  if (plat != teeapps::framework::kPlatSim) {
    SPDLOG_INFO("Serializing resource_req...");
    std::string serialized_resource_req;
    YACL_ENFORCE(resource_req.SerializeToString(&serialized_resource_req),
                 "Serializing resource_req failed");

    SPDLOG_INFO("Generating attestation report...");
    const std::string user_data = cert + "." + serialized_resource_req;
    secretflowapis::v2::sdc::UnifiedAttestationReport attestation_report =
        teeapps::utils::GenRaReport(user_data);

    *request.mutable_attestation_report() = std::move(attestation_report);
  }

  request.set_cert(cert);
  *request.mutable_resource_request() = std::move(resource_req);

  const auto enc_req =
      teeapps::utils::GenEncryptedRequest<capsule_manager::GetDataKeysRequest>(
          request, private_key, cert, capsule_manager_cert_, true,
          teeapps::utils::kRs256, teeapps::utils::kRsaOaep,
          teeapps::utils::kAes128Gcm);
  capsule_manager::EncryptedResponse enc_res;

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);

  const auto status =
      capsule_manager_stub_->GetDataKeys(&context, enc_req, &enc_res);
  YACL_ENFORCE(status.ok(),
               "Calling GetDataKeys failed, error code: {}, message: {}",
               static_cast<int>(status.error_code()), status.error_message());
  auto [res_status, response] = teeapps::utils::ParseEncryptedResponse<
      capsule_manager::GetDataKeysResponse>(enc_res, private_key);
  VerifySfResponseStatus(res_status);

  return std::vector<capsule_manager::DataKey>(response.data_keys().begin(),
                                               response.data_keys().end());
}

void CapsuleManagerClient::CreateDataKeys(
    const std::string& cert, const std::string& private_key,
    const capsule_manager::CreateDataKeysRequest& request) const {
  YACL_ENFORCE(capsule_manager_cert_.size() > 0,
               "capsule_manager_cert not found. you should call GetRaCert() "
               "before other capsule_manager's interface");

  const auto enc_req = teeapps::utils::GenEncryptedRequest<
      capsule_manager::CreateDataKeysRequest>(
      request, private_key, cert, capsule_manager_cert_, true,
      teeapps::utils::kRs256, teeapps::utils::kRsaOaep,
      teeapps::utils::kAes128Gcm);
  capsule_manager::EncryptedResponse enc_res;

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);
  const auto status =
      capsule_manager_stub_->CreateDataKeys(&context, enc_req, &enc_res);
  YACL_ENFORCE(status.ok(),
               "Calling CreateDatakeys failed, error code: {}, message: {}",
               static_cast<int>(status.error_code()), status.error_message());
  VerifySfResponseStatus(enc_res.status());
}

void CapsuleManagerClient::CreateDataPolicy(
    const std::string& cert, const std::string& private_key,
    const secretflowapis::v2::sdc::capsule_manager::CreateDataPolicyRequest&
        request) const {
  YACL_ENFORCE(capsule_manager_cert_.size() > 0,
               "capsule_manager_cert not found. you should call GetRaCert() "
               "before other capsule_manager's interface");

  const auto enc_req = teeapps::utils::GenEncryptedRequest<
      capsule_manager::CreateDataPolicyRequest>(
      request, private_key, cert, capsule_manager_cert_, true,
      teeapps::utils::kRs256, teeapps::utils::kRsaOaep,
      teeapps::utils::kAes128Gcm);
  capsule_manager::EncryptedResponse enc_res;

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);
  const auto status =
      capsule_manager_stub_->CreateDataPolicy(&context, enc_req, &enc_res);
  YACL_ENFORCE(status.ok(),
               "Calling CreateDataPolicy failed, error code: {}, message: {}",
               static_cast<int>(status.error_code()), status.error_message());
  VerifySfResponseStatus(enc_res.status());
}

void CapsuleManagerClient::CreateResultDataKey(
    const std::string& plat, const std::string& cert,
    const std::string& private_key,
    secretflowapis::v2::sdc::capsule_manager::CreateResultDataKeyRequest::Body&
        body) const {
  YACL_ENFORCE(capsule_manager_cert_.size() > 0,
               "capsule_manager_cert not found. you should call GetRaCert() "
               "before other capsule_manager's interface");

  capsule_manager::CreateResultDataKeyRequest request;
  if (plat != teeapps::framework::kPlatSim) {
    SPDLOG_INFO("Serializing CreateResultDataKeyRequest body...");
    std::string serialized_body;
    YACL_ENFORCE(body.SerializeToString(&serialized_body),
                 "Serializing CreateResultDataKeyRequest body failed");

    SPDLOG_INFO("Generating attestation report...");
    const std::string user_data = serialized_body;
    secretflowapis::v2::sdc::UnifiedAttestationReport attestation_report =
        teeapps::utils::GenRaReport(user_data);

    *request.mutable_attestation_report() = std::move(attestation_report);
  }

  *request.mutable_body() = std::move(body);

  const auto enc_req = teeapps::utils::GenEncryptedRequest<
      capsule_manager::CreateResultDataKeyRequest>(
      request, private_key, cert, capsule_manager_cert_, true,
      teeapps::utils::kRs256, teeapps::utils::kRsaOaep,
      teeapps::utils::kAes128Gcm);
  capsule_manager::EncryptedResponse enc_res;

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);
  const auto status =
      capsule_manager_stub_->CreateResultDataKey(&context, enc_req, &enc_res);
  YACL_ENFORCE(
      status.ok(),
      "Calling CreateResultDataKey failed, error code: {}, message: {}",
      static_cast<int>(status.error_code()), status.error_message());
  VerifySfResponseStatus(enc_res.status());
}

}  // namespace framework
}  // namespace teeapps
