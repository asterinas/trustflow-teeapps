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

#include "teeapps/utils/ra_util.h"

#include "absl/strings/ascii.h"
#include "absl/strings/escaping.h"
#include "attestation/generation/ua_generation.h"
#include "cppcodec/base64_rfc4648.hpp"
#include "rapidjson/document.h"
#include "sgx_quote.h"
#include "spdlog/spdlog.h"
#include "yacl/crypto/base/hash/hash_utils.h"

namespace teeapps {
namespace utils {

namespace {
constexpr char kB64Quote[] = "b64_quote";
}

kubetee::UnifiedAttestationReport GenKubeteeRaReport(
    yacl::ByteContainerView user_data) {
  auto digest = yacl::crypto::Sha256(user_data);
  kubetee::attestation::UaReportGenerationParameters gen_param;
  gen_param.tee_identity = "1";
  gen_param.report_type = "Passport";
  kubetee::UnifiedAttestationReportParams param;
  param.set_hex_user_data(absl::BytesToHexString(absl::string_view(
      reinterpret_cast<const char*>(digest.data()), digest.size())));
  gen_param.others = param;

  kubetee::UnifiedAttestationReport report;

  TeeErrorCode err = UaGenerateReport(&gen_param, &report);
  YACL_ENFORCE_EQ(err, TEE_SUCCESS,
                  "Generating UAL report failed, error code: {:#x}", err);
  return report;
}

secretflowapis::v2::sdc::UnifiedAttestationReport GenRaReport(
    yacl::ByteContainerView user_data) {
  // generate kubetee::AttestationReport first
  kubetee::UnifiedAttestationReport report = GenKubeteeRaReport(user_data);

  // convert kubetee::AttestationReport to secretflow::AttestationReport
  secretflowapis::v2::sdc::UnifiedAttestationReport attestation_report;
  *attestation_report.mutable_str_report_version() =
      std::move(*(report.mutable_str_report_version()));
  *attestation_report.mutable_str_report_type() =
      std::move(*(report.mutable_str_report_type()));
  *attestation_report.mutable_str_tee_platform() =
      std::move(*(report.mutable_str_tee_platform()));
  *attestation_report.mutable_json_report() =
      std::move(*(report.mutable_json_report()));
  return attestation_report;
}

void GetEnclaveInfo(std::string& mr_signer, std::string& mr_enclave) {
  kubetee::UnifiedAttestationReport report = GenKubeteeRaReport("");
  rapidjson::Document doc;
  doc.Parse(report.json_report().c_str());
  const std::string b64_quote = doc[kB64Quote].GetString();
  std::vector<uint8_t> quote = cppcodec::base64_rfc4648::decode(b64_quote);

  sgx_quote_t* pquote = reinterpret_cast<sgx_quote_t*>((quote.data()));
  const sgx_report_body_t* report_body = &(pquote->report_body);
  // MRSIGNER
  mr_signer = absl::BytesToHexString(absl::string_view(
      reinterpret_cast<const char*>((&(report_body->mr_signer))),
      sizeof(sgx_measurement_t)));
  // MRENCLAVE
  mr_enclave = absl::BytesToHexString(absl::string_view(
      reinterpret_cast<const char*>((&(report_body->mr_enclave))),
      sizeof(sgx_measurement_t)));
}
}  // namespace utils
}  // namespace teeapps
