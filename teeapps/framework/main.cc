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

#include "gflags/gflags.h"
#include "spdlog/spdlog.h"

#include "teeapps/framework/app.h"
#include "teeapps/utils/crypto_util.h"
#include "teeapps/utils/log.h"

DEFINE_string(plat, "sim", "platform. sim/sgx/tdx/csv");
DEFINE_string(app_mode, "local", "app mode, local or kuscia");
DEFINE_string(entry_task_config_path, "", "entry task config path");
DEFINE_string(data_mesh_endpoint, "", "data mesh endpoint");

// capsule manager tls config
DEFINE_bool(enable_capsule_tls, true,
            "enable tls connection with capsule manager");

// log config
DEFINE_string(app_log_path, "/host/logs/app.log", "App log path");
DEFINE_string(monitor_log_path, "/host/logs/monitor.log", "Monitor log path");
DEFINE_string(log_level, "info", "log level");
DEFINE_bool(enable_console_logger, false,
            "Whether logging to stdout while logging to file");

int main(int argc, char* argv[]) {
  try {
    gflags::ParseCommandLineFlags(&argc, &argv, true);

    teeapps::utils::LogOptions log_opts(FLAGS_app_log_path,
                                        FLAGS_monitor_log_path, FLAGS_log_level,
                                        FLAGS_enable_console_logger);
    teeapps::utils::Setup(log_opts);

    teeapps::framework::App app(
        FLAGS_plat, FLAGS_app_mode, FLAGS_entry_task_config_path,
        FLAGS_data_mesh_endpoint, FLAGS_enable_capsule_tls);

    app.Run();
  } catch (const std::exception& e) {
    SPDLOG_ERROR("{}", e.what());
    return -1;
  }
  return 0;
}