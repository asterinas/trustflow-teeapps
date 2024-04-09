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

#include <memory>

#include "spdlog/spdlog.h"

#include "teeapps/component/component.h"
#include "teeapps/component/eval_param_reader.h"
#include "teeapps/framework/capsule_manager_client.h"
#include "teeapps/utils/crypto_util.h"
#include "teeapps/utils/json2pb.h"

#include "secretflow/spec/v1/evaluation.pb.h"
#include "secretflow/spec/v1/report.pb.h"
#include "secretflowapis/v2/sdc/capsule_manager/capsule_manager.pb.h"
#include "secretflowapis/v2/teeapps/task_config.pb.h"
#include "teeapps/proto/task.pb.h"

namespace teeapps {
namespace framework {

class App {
 public:
  explicit App(const std::string& plat, const std::string& app_mode,
               const std::string& entrey_task_config_path,
               const std::string& data_mesh_endpoint,
               const bool enable_capsule_tls);
  void Run();

 private:
  void GetInputDataKeys(
      std::unordered_map<std::string, std::string>& data_keys_map) const;
  void ProcessInput(
      const std::unordered_map<std::string, std::string>& data_keys_map) const;
  void ProcessOutput();

  void PreProcess();
  void ExecCmd();
  void PostProcess();

 private:
  std::string plat_;
  std::string app_mode_;
  std::string private_key_;
  std::string cert_;
  std::string cmd_;
  std::unique_ptr<CapsuleManagerClient> capsule_manager_client_;

  // from kuscia or other task input configs
  secretflow::spec::v1::NodeEvalParam node_eval_param_;
  secretflow::spec::v1::StorageConfig storage_config_;
  secretflow::spec::v1::ComponentDef component_def_;
  secretflowapis::v2::teeapps::TaskConfig tee_task_config_;

  // task result
  bool task_succeed_ = true;
  std::string task_process_err_;
  std::string task_execution_err_;
};

}  // namespace framework
}  // namespace teeapps