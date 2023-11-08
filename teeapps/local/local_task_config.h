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

#include "secretflow/spec/v1/evaluation.pb.h"
#include "secretflowapis/v2/teeapps/task_config.pb.h"

namespace teeapps {
namespace local {

class LocalTaskConfig {
 public:
  explicit LocalTaskConfig(const std::string& local_task_config_path);

  const secretflow::spec::v1::NodeEvalParam& node_eval_param() const {
    return node_eval_param_;
  }

  const secretflowapis::v2::teeapps::TaskConfig& tee_task_config() const {
    return tee_task_config_;
  }

 private:
  void SetFromJson(const std::string& local_task_config_json);
  void SetFromFile(const std::string& local_task_config_path);

 private:
  secretflow::spec::v1::NodeEvalParam node_eval_param_;
  secretflowapis::v2::teeapps::TaskConfig tee_task_config_;
};

}  // namespace local
}  // namespace teeapps