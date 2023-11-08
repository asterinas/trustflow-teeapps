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

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository", "new_git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")


SECRETFLOW_GIT = "https://github.com/secretflow"

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
    _com_github_gperftools_gperftools()
    _com_github_grpc_grpc()
    _com_github_rules_proto_grpc()
    _com_github_openssl_openssl()
    _com_github_gabime_spdlog()
    _com_github_fmtlib_fmt()
    _com_github_gflags_gflags()
    _com_github_curl()
    _com_github_httplib()
    _aliyun_oss_cpp_sdk()
    _com_github_rapidjson()
    _com_github_yaml_cpp()
    _com_github_cppcodec()

    maybe(
        git_repository,
        name = "yacl",
        commit = "f933d7ff4caf0d9f7ea84cc3e9f51a9a6ee9eeca",
        remote = "{}/yacl.git".format(SECRETFLOW_GIT),
    )

    maybe(
        new_git_repository,
        name = "sf_apis",
        commit = "47a9d68e3c8c455eaa5c4950593ea8f2b26b7bc1",
        remote = "{}/secure-data-capsule-apis.git".format(SECRETFLOW_GIT),
        build_file = "//bazel:sf_apis.BUILD",
    )

    maybe(
        new_git_repository,
        name = "sf_spec",
        commit = "d8b5860b74fff711b2a693d3da168e7f974a3d2d",
        remote = "{}/spec.git".format(SECRETFLOW_GIT),
        build_file = "//bazel:sf_spec.BUILD",
    )

    maybe(
        new_git_repository,
        name = "kuscia_proto",
        remote = "{}/kuscia.git".format(SECRETFLOW_GIT),
        commit = "f7cf6b86f6520db5fd867cbcd95ce58b340f8692",
        build_file = "//bazel:kuscia.BUILD",
    )

def _com_github_gperftools_gperftools():
    maybe(
        http_archive,
        name = "com_github_gperftools_gperftools",
        type = "tar.gz",
        strip_prefix = "gperftools-2.9.1",
        sha256 = "ea566e528605befb830671e359118c2da718f721c27225cbbc93858c7520fee3",
        urls = [
            "https://github.com/gperftools/gperftools/releases/download/gperftools-2.9.1/gperftools-2.9.1.tar.gz",
        ],
        build_file = "//bazel:gperftools.BUILD",
    )

def _com_github_grpc_grpc():
    maybe(
        http_archive,
        name = "com_github_grpc_grpc",
        sha256 = "e18b16f7976aab9a36c14c38180f042bb0fd196b75c9fd6a20a2b5f934876ad6",
        strip_prefix = "grpc-1.45.2",
        type = "tar.gz",
        patches = ["//bazel:patches/grpc-v1.45.2.patch"],
        patch_args = ["-p1"],
        urls = [
            "https://github.com/grpc/grpc/archive/refs/tags/v1.45.2.tar.gz",
        ],
    )

def _com_github_rules_proto_grpc():
    http_archive(
        name = "rules_proto_grpc",
        type = "tar.gz",
        sha256 = "7954abbb6898830cd10ac9714fbcacf092299fda00ed2baf781172f545120419",
        strip_prefix = "rules_proto_grpc-3.1.1",
        urls = [
            "https://github.com/rules-proto-grpc/rules_proto_grpc/archive/refs/tags/3.1.1.tar.gz",
        ],
    )

def _com_github_openssl_openssl():
    maybe(
        http_archive,
        name = "com_github_openssl_openssl",
        sha256 = "dac036669576e83e8523afdb3971582f8b5d33993a2d6a5af87daa035f529b4f",
        type = "tar.gz",
        strip_prefix = "openssl-OpenSSL_1_1_1l",
        urls = [
            "https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_1_1l.tar.gz",
        ],
        build_file = "//bazel:openssl.BUILD",
    )

def _com_github_gabime_spdlog():
    maybe(
        http_archive,
        name = "com_github_gabime_spdlog",
        strip_prefix = "spdlog-1.9.2",
        type = "tar.gz",
        sha256 = "6fff9215f5cb81760be4cc16d033526d1080427d236e86d70bb02994f85e3d38",
        build_file = "//bazel:spdlog.BUILD",
        urls = [
            "https://github.com/gabime/spdlog/archive/refs/tags/v1.9.2.tar.gz",
        ],
    )

def _com_github_fmtlib_fmt():
    maybe(
        http_archive,
        name = "com_github_fmtlib_fmt",
        strip_prefix = "fmt-8.1.1",
        sha256 = "3d794d3cf67633b34b2771eb9f073bde87e846e0d395d254df7b211ef1ec7346",
        urls = [
            "https://github.com/fmtlib/fmt/archive/refs/tags/8.1.1.tar.gz",
        ],
        build_file = "//bazel:fmtlib.BUILD",
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
        build_file = "//bazel:curl.BUILD",
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
        build_file = "//bazel:httplib.BUILD",
        type = "tar.gz",
        urls = [
            "https://github.com/yhirose/cpp-httplib/archive/refs/tags/v0.11.2.tar.gz",
        ],
    )

def _aliyun_oss_cpp_sdk():
    maybe(
        http_archive,
        name = "com_github_aliyun_oss_cpp_sdk",
        sha256 = "adee3beb0b7b88bfd947eb9dae5e0d22c8b3f315563aab076a7b60c140125f31",
        strip_prefix = "aliyun-oss-cpp-sdk-1.9.0",
        build_file = "//:bazel/oss_sdk.BUILD",
        type = "tar.gz",
        urls = [
            "https://codeload.github.com/aliyun/aliyun-oss-cpp-sdk/tar.gz/1.9.0",
        ],
    )

def _com_github_rapidjson():
    maybe(
        http_archive,
        name = "com_github_rapidjson",
        sha256 = "bf7ced29704a1e696fbccf2a2b4ea068e7774fa37f6d7dd4039d0787f8bed98e",
        strip_prefix = "rapidjson-1.1.0",
        build_file = "//bazel:rapidjson.BUILD",
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
        new_git_repository,
        name = "cppcodec",
        remote = "https://github.com/tplgy/cppcodec.git",
        commit = "9f67d7026d3dee8fc6a0af614d97f9365cee2872",
        patches = ["//bazel:patches/cppcodec.patch"],
        patch_args = ["-p1"],
        build_file = "//bazel:cppcodec.BUILD",
    )
