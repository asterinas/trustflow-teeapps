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
#include "spdlog/spdlog.h"

#include "teeapps/component/eval_param_reader.h"
#include "teeapps/framework/constants.h"

namespace teeapps {
namespace utils {

inline std::string GenDataPath(const std::string& data_uri) {
  return fmt::format("{}/{}.dat", teeapps::framework::kTaskBaseDir, data_uri);
}

inline std::string GenTmpEncDataPath(const std::string& data_uri) {
  return fmt::format("{}/{}.encrypted.tmp", teeapps::framework::kTaskBaseDir,
                     data_uri);
}

inline std::string GenTmpDecDataPath(const std::string& data_uri) {
  return fmt::format("{}/{}.decrypted.tmp", teeapps::framework::kTaskBaseDir,
                     data_uri);
}

inline std::string GenSchemaPath(const std::string& data_uri) {
  return fmt::format("{}/{}.schema", teeapps::framework::kTaskBaseDir,
                     data_uri);
}

void GenAndDumpTaskConfig(
    const std::string& app_mode,
    const secretflow::spec::v1::ComponentDef& component_def,
    const teeapps::component::EvalParamReader& eval_param_reader);

}  // namespace utils
}  // namespace teeapps