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

#include <unistd.h>

#include <optional>
#include <string>
#include <vector>

// reference:
// https://github.com/protocolbuffers/protobuf/blob/main/src/google/protobuf/compiler/subprocess.cc
namespace teeapps {
namespace framework {

class Subprocess {
 public:
  explicit Subprocess(const std::vector<std::string>& cmd)
      : cmd_(cmd), pid_(-1), child_stdout_(-1), child_stderr_(-1) {}

  Subprocess(const Subprocess&) = delete;
  Subprocess& operator=(const Subprocess&) = delete;

  ~Subprocess() {
    if (child_stdout_ != -1) {
      close(child_stdout_);
    }
    if (child_stderr_ != -1) {
      close(child_stderr_);
    }
  }

  /**
   * @brief Launch a subprocess and read its stdout and stderr.
   * If some errors occur during the execution of subprocess, an error message
   * will be returned.
   *
   * @return std::optional<std::string> err_msg, err_msg.has_value() is true
   * means has errors occur.
   */
  std::optional<std::string> Launch();

  std::string Stdout() { return stdout_data_; }

  std::string Stderr() { return stderr_data_; }

 protected:
  std::optional<std::string> WaitAndReadOutput();

 private:
  std::vector<std::string> cmd_;
  pid_t pid_;
  int child_stdout_;
  int child_stderr_;
  std::string stdout_data_;
  std::string stderr_data_;
};

}  // namespace framework
}  // namespace teeapps
