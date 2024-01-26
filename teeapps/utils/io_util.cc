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

#include "teeapps/utils/io_util.h"

#include <fstream>

#include "yacl/base/byte_container_view.h"
#include "yacl/io/stream/file_io.h"

namespace teeapps {
namespace utils {

namespace {
constexpr int kMaxBufferSize = 1024 * 1024;  // 1MB

using UniqueFile = std::unique_ptr<FILE, decltype(&std::fclose)>;

}  // namespace

std::string ReadFile(const std::string& file_path) {
  yacl::io::FileInputStream in(file_path);
  std::string content;
  content.resize(in.GetLength());
  in.Read(content.data(), content.size());
  in.Close();
  return content;
}

void WriteFile(const std::string& file_path, yacl::ByteContainerView content) {
  yacl::io::FileOutputStream out(file_path);
  out.Write(content.data(), content.size());
  out.Close();
}

void CopyFile(const std::string& src_file_path,
              const std::string& dst_file_path) {
  auto source =
      UniqueFile(std::fopen(src_file_path.data(), "rb"), &std::fclose);
  auto dest = UniqueFile(std::fopen(dst_file_path.data(), "wb"), &std::fclose);

  YACL_ENFORCE(source != nullptr && source.get() != nullptr,
               "Failed to open {}", src_file_path);
  YACL_ENFORCE(dest != nullptr && source.get() != nullptr, "Failed to open {}",
               dst_file_path);

  uint8_t buf[kMaxBufferSize];
  size_t bytes_read;
  while ((bytes_read = std::fread(buf, sizeof(uint8_t), kMaxBufferSize,
                                  source.get())) > 0) {
    YACL_ENFORCE_EQ(std::fwrite(buf, sizeof(uint8_t), bytes_read, dest.get()),
                    bytes_read, "Failed to write to {} when copying from {}",
                    dst_file_path, src_file_path);
  }
}

void MergeVerticalCsv(const std::string& left_file_path,
                      const std::string& right_file_path,
                      const std::string& dest_file_path) {
  yacl::io::FileInputStream left_in(left_file_path);
  yacl::io::FileInputStream right_in(right_file_path);
  yacl::io::FileOutputStream out(dest_file_path, false);

  std::string left_line;
  std::string right_line;
  while (!left_in.Eof() && !right_in.Eof()) {
    left_in.GetLine(&left_line, '\n');
    right_in.GetLine(&right_line, '\n');
    out.Write(left_line + "," + right_line + "\n");
  }
}

}  // namespace utils
}  // namespace teeapps