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
#include <vector>

#include "absl/types/span.h"
#include "cppcodec/base64_url_unpadded.hpp"
#include "spdlog/spdlog.h"
#include "yacl/crypto/base/aead/gcm_crypto.h"
#include "yacl/crypto/base/aead/sm4_mac.h"
#include "yacl/crypto/base/asymmetric_rsa_crypto.h"
#include "yacl/crypto/base/asymmetric_sm2_crypto.h"
#include "yacl/crypto/base/asymmetric_util.h"
#include "yacl/crypto/base/hmac_sha256.h"
#include "yacl/crypto/base/rsa_signing.h"
#include "yacl/crypto/base/symmetric_crypto.h"
#include "yacl/crypto/utils/rand.h"

#include "teeapps/utils/json2pb.h"

#include "secretflowapis/v2/sdc/capsule_manager/capsule_manager.pb.h"

namespace teeapps {
namespace utils {

constexpr char kRs256[] = "RS256";
constexpr char kRsaOaep[] = "RSA-OAEP";
constexpr char kAes128Gcm[] = "A128GCM";

constexpr uint8_t kIvBytes = 12;
constexpr uint8_t kMacBytes = 16;
constexpr uint8_t kContentKeyBytes = 16;
const std::string kJwsConcatDelimiter = ".";

// Convert byte array to int
template <typename T>
T Bytes2Int(yacl::ByteContainerView bytes) {
  size_t len = bytes.size();
  YACL_ENFORCE_LE(len, sizeof(T), "Converting bytes to integer overflow");
  T ret = 0;
  // Little-endian
  for (size_t i = 0; i < len; i++) {
    ret = (ret << 8 | bytes[len - i - 1]);
  }
  return ret;
}

// Append source file to dest file
void AppendFile(const std::string& source_path, const std::string& dest_path,
                int discard_lines = 0);
// Inplace file decryption
void DecryptFile(const std::string& file_path,
                 yacl::ByteContainerView data_key);
// Decrypt a ciphertext file at source_path to a plaintext file at dest_path
// with data_key
void DecryptFile(const std::string& source_path, const std::string& dest_path,
                 yacl::ByteContainerView data_key);
// Inplace file encryption
void EncryptFile(const std::string& file_path,
                 yacl::ByteContainerView data_key);
// Encrypt a plaintext file at source_path to a ciphertext file at dest_path
// with data_key
void EncryptFile(const std::string& source_path, const std::string& dest_path,
                 yacl::ByteContainerView data_key);

// Verify a plaintext file's integrity, calculate an hmac of raw data from file
// and compare it with an expected_mac:
//   HMAC(key, data_uuid || partition_id || segment_id || secret_shard_id
//   || raw data)
void VerifyFileIntegrity(const std::string& data_path,
                         yacl::ByteContainerView data_uuid,
                         yacl::ByteContainerView part_id,
                         yacl::ByteContainerView seg_id,
                         yacl::ByteContainerView shard_id,
                         yacl::ByteContainerView key,
                         yacl::ByteContainerView expected_mac);

// Generate segment data mac from local file path, raw data is read from
// data_path
//   HMAC(key, data_uuid || partition_id || segment_id || secret_shard_id
//   || raw data)
std::vector<uint8_t> GenSegmentDataMac(const std::string& data_path,
                                       yacl::ByteContainerView data_uuid,
                                       yacl::ByteContainerView part_id,
                                       yacl::ByteContainerView seg_id,
                                       yacl::ByteContainerView shard_id,
                                       yacl::ByteContainerView key);

// Convert bytes to hex string
std::string Bytes2HexStr(yacl::ByteContainerView bytes);

void X509CertPemToDerBase64(const std::string& pem_cert, std::string& der_cert);

// Generate EncryptedRequest with Jwe inside
// Only support RSA-SHA256 with AES128GCM yet(yacl not support sm2 cert's
// operation)
//  sig_alg = "RS256", key_enc_alg = "RSA-OAEP", content_enc_alg = "A128GCM"
template <typename T>
secretflowapis::v2::sdc::capsule_manager::EncryptedRequest GenEncryptedRequest(
    const T& request, const std::string& private_key, const std::string& cert,
    const std::string& peer_cert, const bool has_signature,
    const std::string& sig_alg, const std::string& key_enc_alg,
    const std::string& content_enc_alg) {
  std::string request_str;
  PB2JSON(request, &request_str);

  secretflowapis::v2::sdc::capsule_manager::EncryptedRequest enc_req;
  secretflowapis::v2::RequestHeader header;
  secretflowapis::v2::sdc::Jwe jwe;

  secretflowapis::v2::sdc::Jwe::JoseHeader jwe_header;
  jwe_header.set_alg(key_enc_alg);
  jwe_header.set_enc(content_enc_alg);
  std::string jwe_header_str;
  PB2JSON(jwe_header, &jwe_header_str);
  jwe.set_protected_header(
      cppcodec::base64_url_unpadded::encode(jwe_header_str));

  // gen content encryption key
  const auto cek = yacl::crypto::RandBytes(kContentKeyBytes);
  jwe.set_encrypted_key(cppcodec::base64_url_unpadded::encode(
      yacl::crypto::RsaEncryptor::CreateFromX509(peer_cert)->Encrypt(cek)));

  const auto iv = yacl::crypto::RandBytes(kIvBytes);
  jwe.set_iv(cppcodec::base64_url_unpadded::encode(iv));

  std::vector<uint8_t> add;
  const auto aad_b64 = cppcodec::base64_url_unpadded::encode(add);
  std::vector<uint8_t> tag(kMacBytes);

  if (has_signature) {
    // gen jws
    secretflowapis::v2::sdc::Jws jws;

    secretflowapis::v2::sdc::Jws::JoseHeader jws_header;
    jws_header.set_alg(sig_alg);
    std::string cert_der;
    X509CertPemToDerBase64(cert, cert_der);
    jws_header.add_x5c(cert_der);
    std::string jws_header_str;
    PB2JSON(jws_header, &jws_header_str);
    jws.set_protected_header(
        cppcodec::base64_url_unpadded::encode(jws_header_str));

    jws.set_payload(cppcodec::base64_url_unpadded::encode(request_str));

    const std::string sign_input =
        jws.protected_header() + kJwsConcatDelimiter + jws.payload();
    const std::vector<uint8_t> sig =
        yacl::crypto::RsaSigner::CreateFromPem(private_key)->Sign(sign_input);
    jws.set_signature(cppcodec::base64_url_unpadded::encode(sig));

    // Jwe(jws)
    std::string jws_str;
    PB2JSON(jws, &jws_str);
    std::vector<uint8_t> cipher(jws_str.size());
    yacl::crypto::Aes128GcmCrypto(cek, iv).Encrypt(jws_str, aad_b64,
                                                   absl::Span<uint8_t>(cipher),
                                                   absl::Span<uint8_t>(tag));

    jwe.set_ciphertext(cppcodec::base64_url_unpadded::encode(cipher));
    jwe.set_tag(cppcodec::base64_url_unpadded::encode(tag));
  } else {
    std::vector<uint8_t> cipher(request_str.size());
    yacl::crypto::Aes128GcmCrypto(cek, iv).Encrypt(request_str, aad_b64,
                                                   absl::Span<uint8_t>(cipher),
                                                   absl::Span<uint8_t>(tag));

    jwe.set_ciphertext(cppcodec::base64_url_unpadded::encode(cipher));
    jwe.set_tag(cppcodec::base64_url_unpadded::encode(tag));
  }
  jwe.set_aad(aad_b64);

  *enc_req.mutable_header() = std::move(header);
  enc_req.set_has_signature(has_signature);
  *enc_req.mutable_message() = std::move(jwe);

  return enc_req;
}

template <typename T>
std::tuple<secretflowapis::v2::Status, T> ParseEncryptedResponse(
    const secretflowapis::v2::sdc::capsule_manager::EncryptedResponse& enc_res,
    const std::string& private_key) {
  T response;
  const auto status = enc_res.status();
  if (status.code() != secretflowapis::v2::Code::OK) {
    return std::make_tuple(status, response);
  }
  const auto jwe = enc_res.message();
  secretflowapis::v2::sdc::Jwe::JoseHeader jwe_header;
  JSON2PB(cppcodec::base64_url_unpadded::decode<std::string>(
              jwe.protected_header()),
          &jwe_header);

  const auto encrypted_key =
      cppcodec::base64_url_unpadded::decode(jwe.encrypted_key());
  const auto iv = cppcodec::base64_url_unpadded::decode(jwe.iv());
  const auto cipher = cppcodec::base64_url_unpadded::decode(jwe.ciphertext());
  const auto tag = cppcodec::base64_url_unpadded::decode(jwe.tag());
  const auto aad = cppcodec::base64_url_unpadded::decode(jwe.aad());

  const auto cek = yacl::crypto::RsaDecryptor::CreateFromPem(private_key)
                       ->Decrypt(encrypted_key);

  std::vector<uint8_t> plain(cipher.size());
  yacl::crypto::Aes128GcmCrypto(cek, iv).Decrypt(cipher, aad, tag,
                                                 absl::Span<uint8_t>(plain));

  JSON2PB(std::string(plain.begin(), plain.end()), &response);

  return std::make_tuple(status, response);
}

bool VerifyX509Cert(const std::string& cert_str,
                    const std::string& parent_cert_str);

}  // namespace utils
}  // namespace teeapps
