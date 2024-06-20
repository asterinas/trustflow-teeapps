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

#include "teeapps/utils/output_dist_data_util.h"

#include "yacl/base/exception.h"

#include "teeapps/component/util.h"
#include "teeapps/framework/constants.h"
#include "teeapps/utils/data_uri_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"
#include "teeapps/utils/task_config_util.h"

#include "secretflow/spec/v1/report.pb.h"

namespace teeapps {
namespace utils {

namespace {

constexpr char kDistData[] = "dist_data";

// DistData type keywords
constexpr char kTable[] = "table";
constexpr char kModel[] = "model";
constexpr char kRule[] = "rule";
constexpr char kReport[] = "report";
constexpr char kTeeapps[] = "teeapps";

// DomainData Column comment
constexpr char kCommentId[] = "id";
constexpr char kCommentFeature[] = "feature";
constexpr char kCommentLabel[] = "label";

constexpr char kSource[] = "source";
constexpr char kSourceTee[] = "tee";

}  // namespace

std::string DistDataType2DomainDataType(const std::string& dist_data_type) {
  if (dist_data_type.find(kTable) != std::string::npos) {
    return kTable;
  } else if (dist_data_type.find(kModel) != std::string::npos) {
    return kModel;
  } else if (dist_data_type.find(kRule) != std::string::npos) {
    return kRule;
  } else if (dist_data_type.find(kReport) != std::string::npos) {
    return kReport;
  } else {
    YACL_THROW("can not convert DistData type {} to DomainData type",
               dist_data_type);
  }
}

void AddDataColFromSchema(
    const secretflow::spec::v1::TableSchema& schema,
    std::vector<::kuscia::proto::api::v1alpha1::DataColumn>& data_cols) {
  for (int i = 0; i < schema.ids_size(); i++) {
    ::kuscia::proto::api::v1alpha1::DataColumn data_col;
    data_col.set_name(schema.ids(i));
    data_col.set_type(schema.id_types(i));
    data_col.set_comment(kCommentId);
    data_cols.emplace_back(data_col);
  }
  for (int i = 0; i < schema.features_size(); i++) {
    ::kuscia::proto::api::v1alpha1::DataColumn data_col;
    data_col.set_name(schema.features(i));
    data_col.set_type(schema.feature_types(i));
    data_col.set_comment(kCommentFeature);
    data_cols.emplace_back(data_col);
  }
  for (int i = 0; i < schema.labels_size(); i++) {
    ::kuscia::proto::api::v1alpha1::DataColumn data_col;
    data_col.set_name(schema.labels(i));
    data_col.set_type(schema.label_types(i));
    data_col.set_comment(kCommentLabel);
    data_cols.emplace_back(data_col);
  }
}

void GetDataColsFromDistData(
    const secretflow::spec::v1::DistData& dist_data,
    std::vector<::kuscia::proto::api::v1alpha1::DataColumn>& data_cols) {
  if (dist_data.type() == teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
    secretflow::spec::v1::IndividualTable individual_table;
    dist_data.meta().UnpackTo(&individual_table);
    YACL_ENFORCE(dist_data.data_refs_size() == 1,
                 "individual_table data_refs' size should be 1, got {}",
                 dist_data.data_refs_size());
    const auto& schema = individual_table.schema();
    AddDataColFromSchema(schema, data_cols);
  } else {
    YACL_THROW("Unsupported dist data type {}", dist_data.type());
  }
}

// dist_data represent output in NodeEvalResult
void ConvertDistData2DomainData(
    const std::string& domain_data_id,
    const secretflow::spec::v1::DistData& dist_data,
    const std::string& output_uri, const std::string& data_source_id,
    ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data) {
  domain_data.set_domaindata_id(domain_data_id);
  domain_data.set_name(dist_data.name());
  domain_data.set_type(DistDataType2DomainDataType(dist_data.type()));
  domain_data.set_relative_uri(output_uri);
  domain_data.set_datasource_id(data_source_id);
  domain_data.mutable_attributes()->insert({kSource, kSourceTee});
  domain_data.set_vendor(kTeeapps);

  ::google::protobuf::util::JsonPrintOptions options;
  options.preserve_proto_field_names = false;
  options.always_print_primitive_fields = true;

  std::string dist_data_json;
  PB2JSON(dist_data, &dist_data_json, options);
  domain_data.mutable_attributes()->insert({kDistData, dist_data_json});
  if (dist_data.type() == teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
    std::vector<::kuscia::proto::api::v1alpha1::DataColumn> data_cols;
    GetDataColsFromDistData(dist_data, data_cols);
    domain_data.mutable_columns()->Add(data_cols.begin(), data_cols.end());
  }
}

void ConvertDomainData2DistData(
    const ::kuscia::proto::api::v1alpha1::datamesh::DomainData& domain_data,
    secretflow::spec::v1::DistData& dist_data) {
  SPDLOG_WARN(
      "Kuscia adapter has to deduce dist data from domain data at this moment");

  YACL_ENFORCE(domain_data.type() == kTable,
               "Only table can convert to dist data");

  dist_data.set_name(domain_data.name());
  dist_data.set_type(teeapps::component::DistDataType::INDIVIDUAL_TABLE);

  secretflow::spec::v1::IndividualTable meta;
  for (auto& col : domain_data.columns()) {
    if (col.comment() == kCommentId) {
      meta.mutable_schema()->add_ids(col.name());
      meta.mutable_schema()->add_id_types(col.type());
    } else if (col.comment() == kCommentLabel) {
      meta.mutable_schema()->add_labels(col.name());
      meta.mutable_schema()->add_label_types(col.type());
    } else {
      meta.mutable_schema()->add_features(col.name());
      meta.mutable_schema()->add_feature_types(col.type());
    }
  }
  dist_data.mutable_meta()->PackFrom(std::move(meta));

  secretflow::spec::v1::DistData::DataRef data_ref;
  data_ref.set_uri(domain_data.relative_uri());
  dist_data.mutable_data_refs()->Add(std::move(data_ref));
}

void FillOutputDistData(
    std::vector<secretflow::spec::v1::DistData>& dist_datas,
    const secretflow::spec::v1::NodeEvalParam& node_eval_param,
    const secretflow::spec::v1::ComponentDef& component_def) {
  YACL_ENFORCE(
      dist_datas.size() == static_cast<size_t>(component_def.outputs_size()),
      "output size should be {}, got {}", component_def.outputs_size(),
      dist_datas.size());
  for (int i = 0; i < component_def.outputs_size(); i++) {
    auto& dist_data = dist_datas.at(i);
    dist_data.set_name(component_def.outputs(i).name());
    dist_data.set_type(component_def.outputs(i).types(0));

    // individual table/model/rule/report only has one data_ref
    auto data_ref = dist_data.add_data_refs();
    std::string _, output_id, output_uri;
    teeapps::utils::ParseDmOutputUri(node_eval_param.output_uris(i), _,
                                     output_id, output_uri);
    data_ref->set_uri(output_uri);
    if (dist_data.type() ==
        teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
      const std::string output_schema_path =
          teeapps::utils::GenSchemaPath(output_id);
      const std::string output_schema_str =
          teeapps::utils::ReadFile(output_schema_path);
      secretflow::spec::v1::TableSchema table_schema;
      JSON2PB(output_schema_str, &table_schema);
      secretflow::spec::v1::IndividualTable individual_table;
      *(individual_table.mutable_schema()) = std::move(table_schema);
      dist_data.mutable_meta()->PackFrom(std::move(individual_table));
    } else if (dist_data.type() == teeapps::component::DistDataType::REPORT) {
      const std::string comp_report_str =
          teeapps::utils::ReadFile(teeapps::utils::GenDataPath(output_id));
      secretflow::spec::v1::Report comp_report;
      JSON2PB(comp_report_str, &comp_report);
      dist_data.mutable_meta()->PackFrom(std::move(comp_report));
    } else if (dist_data.type() == teeapps::component::DistDataType::LR_MODEL ||
               dist_data.type() ==
                   teeapps::component::DistDataType::XGB_MODEL ||
               dist_data.type() ==
                   teeapps::component::DistDataType::WOE_RUNNING_RULE) {
      // meta be empty for models or rules
    } else {
      YACL_THROW(
          "DistDataType {} not support for teeapps output dist data filler",
          dist_data.type());
    }
  }
}

}  // namespace utils
}  // namespace teeapps