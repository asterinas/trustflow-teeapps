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

#include "teeapps/framework/subprocess.h"

#include <fcntl.h>
#include <sys/wait.h>

#include <fstream>

#include "yacl/base/exception.h"

namespace teeapps {
namespace framework {

std::optional<std::string> Subprocess::Launch() {
  // Prepare args for execve()
  const char* exe = nullptr;
  char* const* cmd_line = nullptr;
  char** env = nullptr;

  exe = cmd_.front().c_str();
  std::vector<char*> vec;
  for (auto& v : cmd_) {
    vec.push_back(&v.front());
  }
  vec.push_back(nullptr);
  cmd_line = vec.data();
  env = ::environ;

  // Create pipes for process communication.
  int stdout_pipe[2];
  int stderr_pipe[2];
  YACL_ENFORCE(pipe(stdout_pipe) != -1, "pipe() failed.");
  YACL_ENFORCE(pipe(stderr_pipe) != -1, "pipe() failed.");

  this->pid_ = ::vfork();
  if (pid_ == -1) {
    YACL_THROW("vfork() failed, error msg: {}, code: {}.", strerror(errno),
               errno);
  } else if (pid_ == 0) {
    dup2(stdout_pipe[1], STDOUT_FILENO);
    dup2(stderr_pipe[1], STDERR_FILENO);

    close(stdout_pipe[0]);
    close(stdout_pipe[1]);
    close(stderr_pipe[0]);
    close(stderr_pipe[1]);

    ::execve(exe, cmd_line, env);

    int ignored;
    ignored = write(STDERR_FILENO, exe, strlen(exe));
    const char* message = ": program not found or is not executable\n";
    ignored = write(STDERR_FILENO, message, strlen(message));
    (void)ignored;

    // Must use _exit() rather than exit() to avoid flushing output buffers
    // that will also be flushed by the parent.
    _exit(1);
  }

  // Parent
  close(stdout_pipe[1]);
  close(stderr_pipe[1]);
  child_stdout_ = stdout_pipe[0];
  child_stderr_ = stderr_pipe[0];

  return WaitAndReadOutput();
}

std::optional<std::string> Subprocess::WaitAndReadOutput() {
  while (child_stdout_ != -1 || child_stderr_ != -1) {
    fd_set read_fds;
    FD_ZERO(&read_fds);
    if (child_stdout_ != -1) {
      FD_SET(child_stdout_, &read_fds);
    }
    if (child_stderr_ != -1) {
      FD_SET(child_stderr_, &read_fds);
    }
    int max_fd = std::max(child_stdout_, child_stderr_);
    if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
      if (errno == EINTR) {
        // Interrupted by signal.  Try again.
        continue;
      } else {
        YACL_THROW("select() failed, error msg: {}, code: {}.", strerror(errno),
                   errno);
      }
    }

    if (child_stdout_ != -1 && FD_ISSET(child_stdout_, &read_fds)) {
      char buffer[4096];
      int n = read(child_stdout_, buffer, sizeof(buffer));

      if (n > 0) {
        stdout_data_.append(buffer, n);
      } else {
        // We're done reading.  Close.
        close(child_stdout_);
        child_stdout_ = -1;
      }
    }

    if (child_stderr_ != -1 && FD_ISSET(child_stderr_, &read_fds)) {
      char buffer[4096];
      int n = read(child_stderr_, buffer, sizeof(buffer));

      if (n > 0) {
        stderr_data_.append(buffer, n);
      } else {
        // We're done reading.  Close.
        close(child_stderr_);
        child_stderr_ = -1;
      }
    }
  }

  int status;
  while (waitpid(pid_, &status, 0) == -1) {
    if (errno != EINTR) {
      return fmt::format("waitpid() failed, error msg: {}, code: {}.",
                         strerror(errno), errno);
    }
  }
  if (WIFEXITED(status)) {
    if (WEXITSTATUS(status) != 0) {
      int error_code = WEXITSTATUS(status);
      return fmt::format("Task failed with status code {}.", error_code);
    }
  } else if (WIFSIGNALED(status)) {
    int signal = WTERMSIG(status);
    return fmt::format("Task killed by signal {}.", signal);
  } else {
    return "Neither WEXITSTATUS nor WTERMSIG is true?";
  }
  return {};
}

}  // namespace framework
}  // namespace teeapps