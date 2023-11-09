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

#include "teeapps/kuscia/kuscia_client.h"

#include "secretflow/spec/v1/evaluation.pb.h"
#include "secretflowapis/v2/teeapps/task_config.pb.h"

namespace teeapps {
namespace kuscia {

class KusciaTaskConfig {
 public:
  explicit KusciaTaskConfig(const std::string& kuscia_task_config_path,
                            const std::string& data_mesh_endpoint);

  const secretflow::spec::v1::NodeEvalParam& node_eval_param() const {
    return node_eval_param_;
  }

  const secretflow::spec::v1::StorageConfig& storage_config() const {
    return storage_config_;
  }

  const secretflowapis::v2::teeapps::TaskConfig& tee_task_config() const {
    return tee_task_config_;
  }

 private:
  void SetFromJson(const std::string& kuscia_task_config_json);
  void SetFromFile(const std::string& kuscia_task_config_path);
  void FillFromDataMesh(const std::string& data_mesh_endpoint);

 private:
  secretflow::spec::v1::NodeEvalParam node_eval_param_;
  secretflow::spec::v1::StorageConfig storage_config_;
  secretflowapis::v2::teeapps::TaskConfig tee_task_config_;
};

}  // namespace kuscia
}  // namespace teeapps