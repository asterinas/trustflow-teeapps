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

namespace teeapps {
namespace framework {
// plat
constexpr char kPlatSim[] = "sim";
constexpr char kPlatSgx[] = "sgx";
constexpr char kPlatTdx[] = "tdx";
constexpr char kPlatCsv[] = "csv";

// app mode
constexpr char kAppModeLocal[] = "local";
constexpr char kAppModeKuscia[] = "kuscia";

// task files path
constexpr char kTaskBaseDir[] = "/home/teeapp/task";
constexpr char kTaskConfigPath[] = "/home/teeapp/task/task_config.json";

}  // namespace framework
}  // namespace teeapps