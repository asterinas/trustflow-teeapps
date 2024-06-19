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

#include "teeapps/utils/task_config_util.h"

#include "rapidjson/document.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/stringbuffer.h"
#include "yacl/base/exception.h"

#include "teeapps/component/component_list.h"
#include "teeapps/utils/data_uri_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"

#include "secretflow/spec/v1/data.pb.h"

namespace teeapps {
namespace utils {

namespace {

// inner task json keys
constexpr char kComponentName[] = "component_name";
constexpr char kInputs[] = "inputs";
constexpr char kDataPath[] = "data_path";
constexpr char kDataSchemaPath[] = "data_schema_path";
constexpr char kSchema[] = "schema";
constexpr char kOutputs[] = "outputs";

}  // namespace

void GenAndDumpTaskConfig(
    const std::string& app_mode,
    const secretflow::spec::v1::ComponentDef& component_def,
    const teeapps::component::EvalParamReader& eval_param_reader) {
  // Get attrs and inputs,outputs from eval_param_reader
  rapidjson::StringBuffer task_config_json;
  rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(task_config_json);
  // start inner task_config_json
  writer.StartObject();
  writer.String(kComponentName);
  writer.String(component_def.name().c_str());
  // 1. parse attrs
  for (const auto& attr : component_def.attrs()) {
    writer.String(attr.name().c_str());
    const auto& attr_value = eval_param_reader.GetAttr(attr.name());
    switch (attr.type()) {
      case secretflow::spec::v1::AttrType::AT_FLOAT:
        writer.Double(attr_value.f());
        break;
      case secretflow::spec::v1::AttrType::AT_INT:
        writer.Int(attr_value.i64());
        break;
      case secretflow::spec::v1::AttrType::AT_STRING:
        writer.String(attr_value.s().c_str());
        break;
      case secretflow::spec::v1::AttrType::AT_BOOL:
        writer.Bool(attr_value.b());
        break;
      case secretflow::spec::v1::AttrType::AT_FLOATS:
        writer.StartArray();
        for (auto& f : attr_value.fs()) {
          writer.Double(f);
        }
        writer.EndArray();
        break;
      case secretflow::spec::v1::AttrType::AT_INTS:
        writer.StartArray();
        for (const auto& i64 : attr_value.i64s()) {
          writer.Int64(i64);
        }
        writer.EndArray();
        break;
      case secretflow::spec::v1::AttrType::AT_STRINGS:
        writer.StartArray();
        for (const auto& str : attr_value.ss()) {
          writer.String(str.c_str());
        }
        writer.EndArray();
        break;
      case secretflow::spec::v1::AttrType::AT_BOOLS:
        writer.StartArray();
        for (const auto& b : attr_value.bs()) {
          writer.Bool(b);
        }
        writer.EndArray();
        break;
      default:
        YACL_THROW("UnSupported attr type {}", static_cast<int>(attr.type()));
    }
  }

  // 2. parse inputs
  writer.String(kInputs);
  // start of inputs
  writer.StartArray();
  for (const auto& input_def : component_def.inputs()) {
    // start of an input
    writer.StartObject();
    // Type: DistData. in NodeEvalParam
    const auto& input_dist = eval_param_reader.GetInput(input_def.name());
    // data path should be the decrypted data path
    writer.String(kDataPath);
    writer.String(GenDataPath(input_dist.name()).c_str());

    // teeapps will not deal with vertical table
    YACL_ENFORCE(
        input_dist.type() != teeapps::component::DistDataType::VERTICAL_TABLE,
        "teeapps will not deal with vertical table");
    // if input_dist type is individual table, get the table schema
    if (input_dist.type() ==
        teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
      SPDLOG_INFO("Generating Individual table's schema");
      secretflow::spec::v1::IndividualTable individual_table;
      input_dist.meta().UnpackTo(&individual_table);

      ::google::protobuf::util::JsonPrintOptions options;
      options.preserve_proto_field_names = true;
      options.always_print_primitive_fields = true;

      std::string schema_json;
      PB2JSON(individual_table.schema(), &schema_json, options);
      rapidjson::Document doc;
      doc.Parse(schema_json.c_str());
      YACL_ENFORCE(!doc.HasParseError(), "failed to parse schema_json");

      writer.String(kSchema);
      doc.Accept(writer);
    } else {
      // sf.model.* sf.rule.* sf.report ...
      SPDLOG_INFO("sf.model.* sf.rule.* sf.report do nothing about schema");
    }

    for (const auto& input_def_attr : input_def.attrs()) {
      const auto& input_attr_value = eval_param_reader.GetInputAttrs(
          input_def.name(), input_def_attr.name());
      // input attrs' type should be ss
      writer.String(input_def_attr.name().c_str());
      writer.StartArray();
      for (const auto& value_str : input_attr_value.ss()) {
        writer.String(value_str.c_str());
      }
      writer.EndArray();
    }
    // end of an input
    writer.EndObject();
  }
  // end of inputs
  writer.EndArray();

  // 3. parse outputs
  writer.String(kOutputs);
  // start of outputs
  writer.StartArray();
  for (const auto& output_def : component_def.outputs()) {
    // start of an output
    writer.StartObject();
    // uri may contains schema like
    // "dm://output/datasource_id=(\\w+)&&id=(\\w+)&&uri=(\\w+)"
    const auto& uri = eval_param_reader.GetOutputUri(output_def.name());
    std::string _, output_id;
    if (app_mode == teeapps::framework::kAppModeKuscia) {
      teeapps::utils::ParseDmOutputUri(uri, _, output_id, _);
    } else if (app_mode == teeapps::framework::kAppModeLocal) {
      teeapps::utils::ParseLocalOutputUri(uri, output_id, _);
    } else {
      YACL_THROW("app mode {} not support", app_mode);
    }
    writer.String(kDataPath);
    writer.String(GenDataPath(output_id).c_str());
    writer.String(kDataSchemaPath);
    writer.String(GenSchemaPath(output_id).c_str());

    // end of an output
    writer.EndObject();
  }
  // end of outputs
  writer.EndArray();

  // end of inner task_config_json
  writer.EndObject();

  teeapps::utils::WriteFile(teeapps::framework::kTaskConfigPath,
                            task_config_json.GetString());
  SPDLOG_INFO("Dumping task config json succeed...");
  SPDLOG_DEBUG("Task config json: {}", task_config_json.GetString());
}

}  // namespace utils
}  // namespace teeapps
