# Copyright 2023 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

cc_library(
    name = "oss_sdk_external",
    srcs = glob([
        "sdk/src/external/**/*.cpp",
    ]),
    hdrs = glob([
        "sdk/src/external/**/*.h",
    ]),
    includes = [
        "sdk/src/external",
    ],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "oss_sdk",
    srcs = glob([
        "sdk/src/*.cc",
        "sdk/src/**/*.cc",
    ]),
    hdrs = glob([
        "sdk/include/alibabacloud/oss/*.h",
        "sdk/include/alibabacloud/oss/**/*.h",
        "sdk/src/*.h",
        "sdk/src/**/*.h",
    ]),
    includes = [
        "sdk/include",
        "sdk/include/alibabacloud/oss",
        "sdk/src",
    ],
    visibility = ["//visibility:public"],
    deps = [
        ":oss_sdk_external",
        "@com_github_curl//:curl",
        "@com_github_openssl_openssl//:openssl",
    ],
)
