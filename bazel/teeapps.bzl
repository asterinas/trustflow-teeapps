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
warpper bazel cc_xx to modify flags.
"""

load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library", "cc_test")
load("@rules_foreign_cc//foreign_cc:defs.bzl", "cmake")

WARNING_FLAGS = [
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wno-unused-parameter",
    "-Wnon-virtual-dtor",
] + select({
    "@bazel_tools//src/conditions:darwin": ["-Wunused-const-variable"],
    "//conditions:default": ["-Wunused-const-variable=1"],
})
DEBUG_FLAGS = ["-O0", "-g"]
RELEASE_FLAGS = ["-O2"]
FAST_FLAGS = ["-O1"]

def _teeapps_copts():
    return select({
        "@teeapps//bazel:teeapps_build_as_release": RELEASE_FLAGS,
        "@teeapps//bazel:teeapps_build_as_debug": DEBUG_FLAGS,
        "@teeapps//bazel:teeapps_build_as_fast": FAST_FLAGS,
        "//conditions:default": FAST_FLAGS,
    }) + WARNING_FLAGS

def teeapps_cmake_external(**attrs):
    if "generate_args" not in attrs:
        attrs["generate_args"] = ["-GNinja"]
    return cmake(**attrs)

def teeapps_cc_binary(
        linkopts = [],
        copts = [],
        deps = [],
        **kargs):
    cc_binary(
        linkopts = linkopts + ["-lm"],
        copts = copts + _teeapps_copts(),
        deps = deps,
        **kargs
    )

def teeapps_cc_library(
        linkopts = [],
        copts = [],
        deps = [],
        **kargs):
    cc_library(
        linkopts = linkopts + ["-ldl"],
        copts = _teeapps_copts() + copts,
        deps = deps + [
            "@com_github_gabime_spdlog//:spdlog",
        ],
        **kargs
    )

def teeapps_cc_test(
        linkopts = [],
        copts = [],
        deps = [],
        linkstatic = True,
        **kwargs):
    cc_test(
        # -lm for tcmalloc
        linkopts = linkopts + ["-lm"],
        copts = _teeapps_copts() + copts,
        deps = deps + [
            "@com_google_googletest//:gtest_main",
        ],
        # static link for tcmalloc
        linkstatic = linkstatic,
        **kwargs
    )

def occlum_cc_library(
        linkopts = [],
        copts = [],
        deps = [],
        **kargs):
    cc_library(
        linkopts = linkopts,
        copts = ["-DENV_TYPE_OCCLUM"] + copts,
        deps = ["@com_github_openssl_openssl//:openssl"] + deps,
        **kargs
    )

def _teeapps_version_file_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.filename)
    ctx.actions.write(
        output = out,
        content = "__version__ = \"{}\"\n".format(ctx.attr.version),
    )
    return [DefaultInfo(files = depset([out]))]

teeapps_version_file = rule(
    implementation = _teeapps_version_file_impl,
    attrs = {
        "version": attr.string(),
        "filename": attr.string(),
    },
)
