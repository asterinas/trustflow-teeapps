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

#include <math.h>
#include <unistd.h>

#include <fstream>
#include <set>
#include <string>
#include <vector>

#include "component_list.h"
#include "rapidjson/document.h"
#include "rapidjson/pointer.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/schema.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"

using namespace teeapps::component;

std::unique_ptr<secretflow::spec::v1::CompListDef> COMP_LIST =
    std::make_unique<secretflow::spec::v1::CompListDef>();
constexpr static char COMP_LIST_NAME[] = "trustedflow";
constexpr static char COMP_LIST_DESC[] = "First-party TrustedFlow components.";
constexpr static char COMP_LIST_VERSION[] = "0.0.1";

constexpr static char COMP_LIST_FILE[] = "teeapps/component/comp_list.json";
constexpr static char ALL_TRANSLATION_FILE[] =
    "teeapps/component/all_translation_cn.json";
constexpr static char TRANSLATION_FILE[] = "teeapps/component/translation.json";

void generate_comp_list() {
  COMP_LIST->set_name(COMP_LIST_NAME);
  COMP_LIST->set_desc(COMP_LIST_DESC);
  COMP_LIST->set_version(COMP_LIST_VERSION);

  // add components
  for (auto it = COMP_DEF_MAP.begin(); it != COMP_DEF_MAP.end(); it++) {
    COMP_LIST->mutable_comps()->Add(
        secretflow::spec::v1::ComponentDef(it->second));
  }
}

void fill_value(rapidjson::Document& doc, const std::string& key,
                const std::vector<std::string>& fill_keys,
                rapidjson::Value& object,
                rapidjson::Document::AllocatorType& allocator) {
  for (const auto& fill_key : fill_keys) {
    if (!doc.HasMember(key.c_str()) || !doc[key.c_str()].IsObject() ||
        !doc[key.c_str()].HasMember(fill_key.c_str()) ||
        !doc[key.c_str()][fill_key.c_str()].IsString()) {
      object.AddMember(
          rapidjson::Value().SetString(fill_key.c_str(), allocator),
          rapidjson::Value().SetString(fill_key.c_str(), allocator), allocator);
    } else {
      object.AddMember(
          rapidjson::Value().SetString(fill_key.c_str(), allocator),
          rapidjson::Value().SetString(
              doc[key.c_str()][fill_key.c_str()].GetString(), allocator),
          allocator);
    }
  }
}

void non_repeated_insert(std::vector<std::string>& vec,
                         const std::string& value) {
  if (std::find(vec.begin(), vec.end(), value) == vec.end()) {
    vec.push_back(value);
  }
}

std::string gettext(
    const std::unique_ptr<secretflow::spec::v1::CompListDef>& comp_list,
    rapidjson::Document& doc) {
  rapidjson::Document fill_doc;
  fill_doc.Parse("{}");
  rapidjson::Document::AllocatorType& allocator = fill_doc.GetAllocator();
  // total header
  rapidjson::Value object(rapidjson::kObjectType);
  fill_value(doc, ".", {comp_list->name(), comp_list->desc()}, object,
             allocator);
  fill_doc.AddMember(".", object, allocator);

  // for every component
  for (const auto& comp : comp_list->comps()) {
    std::string key =
        string_format("%s/%s:%s", comp.domain().c_str(), comp.name().c_str(),
                      comp.version().c_str());
    // get all fill_keys list
    std::vector<std::string> fill_keys;
    non_repeated_insert(fill_keys, comp.domain());
    non_repeated_insert(fill_keys, comp.name());
    non_repeated_insert(fill_keys, comp.desc());
    non_repeated_insert(fill_keys, comp.version());

    for (const auto& attr : comp.attrs()) {
      non_repeated_insert(fill_keys, attr.name());
      non_repeated_insert(fill_keys, attr.desc());
    }

    for (const auto& io : comp.inputs()) {
      non_repeated_insert(fill_keys, io.name());
      non_repeated_insert(fill_keys, io.desc());

      for (const auto& t_attr : io.attrs()) {
        non_repeated_insert(fill_keys, t_attr.name());
        non_repeated_insert(fill_keys, t_attr.desc());

        for (const auto& t_attr_a : t_attr.extra_attrs()) {
          non_repeated_insert(fill_keys, t_attr_a.name());
          non_repeated_insert(fill_keys, t_attr_a.desc());
        }
      }
    }

    for (const auto& io : comp.outputs()) {
      non_repeated_insert(fill_keys, io.name());
      non_repeated_insert(fill_keys, io.desc());

      for (const auto& t_attr : io.attrs()) {
        non_repeated_insert(fill_keys, t_attr.name());
        non_repeated_insert(fill_keys, t_attr.desc());

        for (const auto& t_attr_a : t_attr.extra_attrs()) {
          non_repeated_insert(fill_keys, t_attr_a.name());
          non_repeated_insert(fill_keys, t_attr_a.desc());
        }
      }
    }

    rapidjson::Value object(rapidjson::kObjectType);
    fill_value(doc, key, fill_keys, object, allocator);
    fill_doc.AddMember(rapidjson::Value().SetString(key.c_str(), allocator),
                       object, allocator);
  }

  // convert to string
  rapidjson::StringBuffer str_buffer;
  rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(str_buffer);
  fill_doc.Accept(writer);

  return str_buffer.GetString();
}

int main() {
  try {
    // get all component
    generate_comp_list();

    // write all component into file with format JSON
    std::string message_str;
    PROTOBUF2JSON(*COMP_LIST, &message_str);
    rapidjson::Document format_doc;
    format_doc.Parse(message_str.c_str());
    rapidjson::StringBuffer str_buffer;
    rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(str_buffer);
    format_doc.Accept(writer);
    write_to_file(str_buffer.GetString(), COMP_LIST_FILE);

    // get the translation of components
    std::string archieve_str = read_from_file(ALL_TRANSLATION_FILE);
    rapidjson::Document doc;
    doc.Parse(archieve_str.c_str());
    std::string res = gettext(COMP_LIST, doc);
    write_to_file(res, TRANSLATION_FILE);
  } catch (const std::exception& e) {
    std::cerr << e.what() << std::endl;
    return -1;
  }
}