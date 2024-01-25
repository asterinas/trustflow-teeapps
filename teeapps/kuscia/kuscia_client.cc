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

#include "teeapps/kuscia/kuscia_client.h"

#include <cstdlib>

#include "gflags/gflags.h"
#include "include/grpcpp/security/credentials.h"
#include "include/grpcpp/security/tls_credentials_options.h"
#include "yacl/base/exception.h"

#include "teeapps/utils/io_util.h"

namespace teeapps {
namespace kuscia {

namespace {
constexpr uint32_t kGrpcMaxMsgSizeMb = 1024;
constexpr uint32_t kGrpcTimeoutMs = 5 * 1000;

constexpr char kClientCertPathEnv[] = "CLIENT_CERT_FILE";
constexpr char kClientKeyPathEnv[] = "CLIENT_PRIVATE_KEY_FILE";
constexpr char kCaCertPathEnv[] = "TRUSTED_CA_FILE";
}  // namespace

KusciaClient::KusciaClient(const std::string& datamesh_endpoint) {
  ::grpc::ChannelArguments chan_args;
  chan_args.SetMaxReceiveMessageSize(kGrpcMaxMsgSizeMb * 1024 * 1024);
  chan_args.SetGrpclbFallbackTimeout(kGrpcTimeoutMs);

  const char* cert_path = std::getenv(kClientCertPathEnv);
  YACL_ENFORCE(cert_path != nullptr, "{} env variable not set ",
               kClientCertPathEnv);
  const char* key_path = std::getenv(kClientKeyPathEnv);
  YACL_ENFORCE(key_path != nullptr, "{} env variable not set ",
               kClientKeyPathEnv);
  const char* ca_cert_path = std::getenv(kCaCertPathEnv);
  YACL_ENFORCE(ca_cert_path != nullptr, "{} env variable not set ",
               kCaCertPathEnv);

  ::grpc::SslCredentialsOptions ssl_opts;
  ssl_opts.pem_cert_chain = teeapps::utils::ReadFile(cert_path);
  ssl_opts.pem_private_key = teeapps::utils::ReadFile(key_path);
  ssl_opts.pem_root_certs = teeapps::utils::ReadFile(ca_cert_path);
  const auto creds = ::grpc::SslCredentials(ssl_opts);
  const auto chan =
      ::grpc::CreateCustomChannel(datamesh_endpoint, creds, chan_args);

  domain_data_stub_ =
      ::kuscia::proto::api::v1alpha1::datamesh::DomainDataService::NewStub(
          chan);
  domain_data_source_stub_ = ::kuscia::proto::api::v1alpha1::datamesh::
      DomainDataSourceService::NewStub(chan);
}

::kuscia::proto::api::v1alpha1::datamesh::DomainData
KusciaClient::QueryDomainData(const std::string& domain_data_id) const {
  ::kuscia::proto::api::v1alpha1::datamesh::QueryDomainDataRequest request;
  ::kuscia::proto::api::v1alpha1::datamesh::QueryDomainDataResponse response;

  request.set_domaindata_id(domain_data_id);
  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);

  const auto status =
      domain_data_stub_->QueryDomainData(&context, request, &response);
  YACL_ENFORCE(status.ok(),
               "Calling QueryDomainData failed, error code: {}, message: {}",
               status.error_code(), status.error_message());
  YACL_ENFORCE(response.status().code() == 0,
               "Call service failed, error code: {}, message: {}",
               response.status().code(), response.status().message());

  return response.data();
}

::kuscia::proto::api::v1alpha1::datamesh::DomainDataSource
KusciaClient::QueryDomainDataSource(const std::string& datasource_id) const {
  ::kuscia::proto::api::v1alpha1::datamesh::QueryDomainDataSourceRequest
      request;
  ::kuscia::proto::api::v1alpha1::datamesh::QueryDomainDataSourceResponse
      response;

  request.set_datasource_id(datasource_id);
  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);

  const auto status = domain_data_source_stub_->QueryDomainDataSource(
      &context, request, &response);
  YACL_ENFORCE(
      status.ok(),
      "Calling QueryDomainDataSource failed, error code: {}, message: {}",
      status.error_code(), status.error_message());
  YACL_ENFORCE(response.status().code() == 0,
               "Call service failed, error code: {}, message: {}",
               response.status().code(), response.status().message());

  return response.data();
}

std::string KusciaClient::CreateDomainData(
    const ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data)
    const {
  ::kuscia::proto::api::v1alpha1::datamesh::CreateDomainDataRequest request;
  ::kuscia::proto::api::v1alpha1::datamesh::CreateDomainDataResponse response;

  request.set_domaindata_id(domain_data.domaindata_id());
  request.set_name(domain_data.name());
  request.set_type(domain_data.type());
  request.set_datasource_id(domain_data.datasource_id());
  request.set_relative_uri(domain_data.relative_uri());
  *(request.mutable_attributes()) = domain_data.attributes();
  *(request.mutable_columns()) = domain_data.columns();
  request.set_vendor(domain_data.vendor());

  ::grpc::ClientContext context;
  const auto deadline = std::chrono::system_clock::now() +
                        std::chrono::milliseconds(kGrpcTimeoutMs);
  context.set_deadline(deadline);

  const auto status =
      domain_data_stub_->CreateDomainData(&context, request, &response);

  YACL_ENFORCE(status.ok(),
               "Calling CreateDomainData failed, error code: {}, message: {}",
               status.error_code(), status.error_message());
  YACL_ENFORCE(response.status().code() == 0,
               "Call service failed, error code: {}, message: {}",
               response.status().code(), response.status().message());
  return response.data().domaindata_id();
}

}  // namespace kuscia
}  // namespace teeapps