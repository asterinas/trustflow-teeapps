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

#include "include/grpcpp/grpcpp.h"

#include "kuscia/proto/api/v1alpha1/datamesh/domaindata.grpc.pb.h"
#include "kuscia/proto/api/v1alpha1/datamesh/domaindatasource.grpc.pb.h"

namespace teeapps {
namespace kuscia {
class KusciaClient {
 public:
  static KusciaClient& GetInstance(const std::string& datamesh_endpoint) {
    static KusciaClient instance(datamesh_endpoint);
    return instance;
  }

  ::kuscia::proto::api::v1alpha1::datamesh::DomainData QueryDomainData(
      const std::string& domain_data_id) const;

  ::kuscia::proto::api::v1alpha1::datamesh::DomainDataSource
  QueryDomainDataSource(const std::string& datasource_id) const;

  std::string CreateDomainData(
      const ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data)
      const;

 private:
  explicit KusciaClient(const std::string& datamesh_endpoint);
  KusciaClient(const KusciaClient&) = delete;
  const KusciaClient& operator=(const KusciaClient&) = delete;

 private:
  std::unique_ptr<
      ::kuscia::proto::api::v1alpha1::datamesh::DomainDataService::Stub>
      domain_data_stub_;
  std::unique_ptr<
      ::kuscia::proto::api::v1alpha1::datamesh::DomainDataSourceService::Stub>
      domain_data_source_stub_;
};

}  // namespace kuscia
}  // namespace teeapps