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

"""
This module contains build rules for project dependencies.
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

def gen_bazel_version():
    bazel_version_repository(
        name = "bazel_version",
    )

def _store_bazel_version(repository_ctx):
    # for fix grpc compile
    repository_ctx.file("bazel_version.bzl", "bazel_version = \"{}\"".format(native.bazel_version))
    repository_ctx.file("BUILD.bazel", "")

bazel_version_repository = repository_rule(
    implementation = _store_bazel_version,
)

def teeapps_dependencies():
    """This module contains build rules for project dependencies.
    """
    _com_github_trustflow()
    _com_github_grpc_grpc()
    _com_github_rules_proto_grpc()
    _com_github_gflags_gflags()
    _com_github_curl()
    _com_github_httplib()
    _com_github_rapidjson()
    _com_github_yaml_cpp()
    _com_github_cppcodec()
    _com_github_sf_apis()
    _com_github_sf_spec()
    _com_github_kuscia_proto()

def _com_github_trustflow():
    maybe(
        http_archive,
        name = "trustflow",
        sha256 = "cb1f7364aa03ecddfaea13eb8a12769cbf04e1a0225ac29a371e87a88b3c8470",
        strip_prefix = "trustflow-c0414d0bd06ca209933c534942f7dcc8e2aedec5",
        type = "tar.gz",
        urls = [
            "https://github.com/asterinas/trustflow/archive/c0414d0bd06ca209933c534942f7dcc8e2aedec5.tar.gz",
        ],
    )

def _com_github_grpc_grpc():
    maybe(
        http_archive,
        name = "com_github_grpc_grpc",
        sha256 = "fb1ed98eb3555877d55eb2b948caca44bc8601c6704896594de81558639709ef",
        strip_prefix = "grpc-1.50.1",
        type = "tar.gz",
        patch_args = ["-p1"],
        # Set grpc to use local go toolchain
        patches = ["@teeapps//bazel:patches/grpc.patch"],
        urls = [
            "https://github.com/grpc/grpc/archive/refs/tags/v1.50.1.tar.gz",
        ],
    )

def _com_github_rules_proto_grpc():
    maybe(
        http_archive,
        name = "rules_proto_grpc",
        type = "tar.gz",
        sha256 = "7954abbb6898830cd10ac9714fbcacf092299fda00ed2baf781172f545120419",
        strip_prefix = "rules_proto_grpc-3.1.1",
        urls = [
            "https://github.com/rules-proto-grpc/rules_proto_grpc/archive/refs/tags/3.1.1.tar.gz",
        ],
    )

def _com_github_gflags_gflags():
    maybe(
        http_archive,
        name = "com_github_gflags_gflags",
        strip_prefix = "gflags-2.2.2",
        sha256 = "34af2f15cf7367513b352bdcd2493ab14ce43692d2dcd9dfc499492966c64dcf",
        type = "tar.gz",
        urls = [
            "https://github.com/gflags/gflags/archive/v2.2.2.tar.gz",
        ],
    )

def _com_github_curl():
    maybe(
        http_archive,
        name = "com_github_curl",
        build_file = "@teeapps//bazel:curl.BUILD",
        sha256 = "816e41809c043ff285e8c0f06a75a1fa250211bbfb2dc0a037eeef39f1a9e427",
        strip_prefix = "curl-8.4.0",
        urls = [
            "https://github.com/curl/curl/releases/download/curl-8_4_0/curl-8.4.0.tar.gz",
        ],
    )

def _com_github_httplib():
    maybe(
        http_archive,
        name = "com_github_httplib",
        sha256 = "e620d030215733c4831fdc7813d5eb37a6fd599f8192a730662662e1748a741b",
        strip_prefix = "cpp-httplib-0.11.2",
        build_file = "@teeapps//bazel:httplib.BUILD",
        type = "tar.gz",
        urls = [
            "https://github.com/yhirose/cpp-httplib/archive/refs/tags/v0.11.2.tar.gz",
        ],
    )

def _com_github_rapidjson():
    maybe(
        http_archive,
        name = "com_github_rapidjson",
        sha256 = "bf7ced29704a1e696fbccf2a2b4ea068e7774fa37f6d7dd4039d0787f8bed98e",
        strip_prefix = "rapidjson-1.1.0",
        build_file = "@teeapps//bazel:rapidjson.BUILD",
        type = "tar.gz",
        urls = [
            "https://github.com/Tencent/rapidjson/archive/v1.1.0.tar.gz",
        ],
    )

def _com_github_yaml_cpp():
    maybe(
        http_archive,
        name = "com_github_yaml_cpp",
        sha256 = "43e6a9fcb146ad871515f0d0873947e5d497a1c9c60c58cb102a97b47208b7c3",
        strip_prefix = "yaml-cpp-yaml-cpp-0.7.0",
        type = "tar.gz",
        urls = [
            "https://github.com/jbeder/yaml-cpp/archive/refs/tags/yaml-cpp-0.7.0.tar.gz",
        ],
    )

def _com_github_cppcodec():
    maybe(
        http_archive,
        name = "cppcodec",
        build_file = "@teeapps//bazel:cppcodec.BUILD",
        urls = [
            "https://github.com/tplgy/cppcodec/archive/refs/tags/v0.2.tar.gz",
        ],
        strip_prefix = "cppcodec-0.2",
        sha256 = "0edaea2a9d9709d456aa99a1c3e17812ed130f9ef2b5c2d152c230a5cbc5c482",
        patches = ["@teeapps//bazel:patches/cppcodec.patch"],
        patch_args = ["-p1"],
    )

def _com_github_sf_apis():
    maybe(
        http_archive,
        name = "sf_apis",
        urls = [
            "https://github.com/secretflow/secure-data-capsule-apis/archive/47a47f0f0096fdcc2c13c8ba3b86448d2795b829.tar.gz",
        ],
        strip_prefix = "secure-data-capsule-apis-47a47f0f0096fdcc2c13c8ba3b86448d2795b829",
        build_file = "@teeapps//bazel:sf_apis.BUILD",
        sha256 = "c7b52eb51be3b4f1f380b8fb7cdd80a101e59e9471ca01d7b6c3441bd463dc3b",
    )

def _com_github_sf_spec():
    maybe(
        http_archive,
        name = "sf_spec",
        urls = [
            "https://github.com/secretflow/spec/archive/d8b5860b74fff711b2a693d3da168e7f974a3d2d.tar.gz",
        ],
        strip_prefix = "spec-d8b5860b74fff711b2a693d3da168e7f974a3d2d",
        sha256 = "49d02af77de9af23be60299c8dec611a678dbab707a3be3aa7766a8417710c0d",
        build_file = "@teeapps//bazel:sf_spec.BUILD",
    )

def _com_github_kuscia_proto():
    maybe(
        http_archive,
        name = "kuscia_proto",
        urls = [
            "https://github.com/secretflow/kuscia/archive/f7cf6b86f6520db5fd867cbcd95ce58b340f8692.tar.gz",
        ],
        strip_prefix = "kuscia-f7cf6b86f6520db5fd867cbcd95ce58b340f8692",
        sha256 = "bf1e163c0ac888fd3aa0391c6f6532b62937ae6393dce89d2a2d72cb9b049f94",
        build_file = "@teeapps//bazel:kuscia.BUILD",
    )
