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

#include "teeapps/utils/crypto_util.h"

#include <filesystem>

#include "gtest/gtest.h"
#include "yacl/io/stream/file_io.h"

#include "teeapps/utils/io_util.h"

namespace teeapps {
namespace utils {

namespace {

constexpr uint8_t kKeyExample[16] = {0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE,
                                     0xD2, 0xA6, 0xAB, 0xF7, 0x15, 0x88,
                                     0x09, 0xCF, 0x4F, 0x3C};

std::vector<uint8_t> kPlaintextExample = {
    0x6B, 0xC1, 0xBE, 0xE2, 0x2E, 0x40, 0x9F, 0x96, 0xE9, 0x3D, 0x7E,
    0x11, 0x73, 0x93, 0x17, 0x2A, 0xAE, 0x2D, 0x8A, 0x57, 0x1E, 0x03,
    0xAC, 0x9C, 0x9E, 0xB7, 0x6F, 0xAC, 0x45, 0xAF, 0x8E, 0x51, 0x30,
    0xC8, 0x1C, 0x46, 0xA3, 0x5C, 0xE4, 0x11, 0xE5, 0xFB, 0xC1, 0x19,
    0x1A, 0x0A, 0x52, 0xEF, 0xF6, 0x9F, 0x24, 0x45, 0xDF, 0x4F, 0x9B,
    0x17, 0xAD, 0x2B, 0x41, 0x7B, 0xE6, 0x6C, 0x37, 0x10};

constexpr char kSourceFilename[] = "source.dat";
constexpr char kDestFilename[] = "dest.dat";
constexpr char kEncryptionFilename[] = "encryption.dat";
constexpr char kDecryptionFilename[] = "decryption.dat";

}  // namespace

TEST(CryptoUtilTest, EncryptFile_shouldOk) {
  // write source file
  EXPECT_TRUE(!std::filesystem::exists(kSourceFilename));
  utils::WriteFile(kSourceFilename, kPlaintextExample);
  EXPECT_TRUE(std::filesystem::exists(kSourceFilename));

  // encrypt source file
  EXPECT_TRUE(!std::filesystem::exists(kEncryptionFilename));
  EXPECT_NO_THROW(
      EncryptFile(kSourceFilename, kEncryptionFilename, kKeyExample));
  EXPECT_TRUE(std::filesystem::exists(kEncryptionFilename));
}

TEST(CryptoUtilTest, DecryptFile_shouldOk) {
  // decrypt encryption file
  EXPECT_TRUE(!std::filesystem::exists(kDecryptionFilename));
  EXPECT_NO_THROW(
      DecryptFile(kEncryptionFilename, kDecryptionFilename, kKeyExample));
  EXPECT_TRUE(std::filesystem::exists(kDecryptionFilename));

  // read encryption file and compare
  std::string decrypted_data = utils::ReadFile(kDecryptionFilename);
  std::vector<uint8_t> decrypted_vec(decrypted_data.begin(),
                                     decrypted_data.end());
  EXPECT_EQ(kPlaintextExample, decrypted_vec);
}

TEST(CryptoUtilTest, InplaceEncryptFile_shouldOk) {
  // encrypt source file
  EXPECT_NO_THROW(EncryptFile(kSourceFilename, kKeyExample));
  // read encryption file and compare
  std::string decrypted_data = utils::ReadFile(kSourceFilename);
  std::vector<uint8_t> decrypted_vec(decrypted_data.begin(),
                                     decrypted_data.end());
  EXPECT_NE(kPlaintextExample, decrypted_vec);
}

TEST(CryptoUtilTest, InplaceDecryptFile_shouldOk) {
  // decrypt encryption file
  EXPECT_NO_THROW(DecryptFile(kSourceFilename, kKeyExample));
  // read encryption file and compare
  std::string decrypted_data = utils::ReadFile(kSourceFilename);
  std::vector<uint8_t> decrypted_vec(decrypted_data.begin(),
                                     decrypted_data.end());
  EXPECT_EQ(kPlaintextExample, decrypted_vec);
}

TEST(CryptoUtilTest, AppendFile_shouldOk) {
  std::filesystem::remove(kSourceFilename);
  std::filesystem::remove(kDestFilename);
  // write source file
  EXPECT_TRUE(!std::filesystem::exists(kSourceFilename));
  utils::WriteFile(kSourceFilename, "world");
  EXPECT_TRUE(std::filesystem::exists(kSourceFilename));
  // write dest file
  EXPECT_TRUE(!std::filesystem::exists(kDestFilename));
  utils::WriteFile(kDestFilename, "hello");
  EXPECT_TRUE(std::filesystem::exists(kDestFilename));

  utils::AppendFile(kSourceFilename, kDestFilename);
  EXPECT_EQ("helloworld\n", utils::ReadFile(kDestFilename));
}

}  // namespace utils
}  // namespace teeapps
