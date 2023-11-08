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

#include "kuscia/proto/api/v1alpha1/datamesh/domaindata.pb.h"
#include "secretflow/spec/v1/component.pb.h"
#include "secretflow/spec/v1/data.pb.h"
#include "secretflow/spec/v1/evaluation.pb.h"

namespace teeapps {
namespace utils {

void FillOutputDistData(
    std::vector<secretflow::spec::v1::DistData>& dist_datas,
    const secretflow::spec::v1::NodeEvalParam& node_eval_param,
    const secretflow::spec::v1::ComponentDef& component_def);

void ConvertDistData2DomainData(
    const std::string& domain_data_id,
    const secretflow::spec::v1::DistData& dist_data,
    const std::string& output_uri, const std::string& data_source_id,
    ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data);

void ConvertDomainData2DistData(
    const ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data,
    secretflow::spec::v1::DistData& dist_data);
}  // namespace utils
}  // namespace teeapps
