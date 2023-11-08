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

FROM secretflow/teeapps-gcc11-dev:0.1.0b0 as builder


WORKDIR /home/admin/dev

COPY .bazelrc .bazelversion build.sh BUILD.bazel Occlum.json python.yaml WORKSPACE ./
COPY teeapps ./teeapps
COPY integration_test ./integration_test
COPY bazel ./bazel
COPY deployment/conf/unified_attestation.json ./deployment/conf/unified_attestation.json

RUN ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts && bash build.sh

FROM secretflow/occlum:0.29.5-ubuntu20.04

ARG config_templates=""
LABEL kuscia.secretflow.config-templates=$config_templates

ARG deploy_templates=""
LABEL kuscia.secretflow.deploy-templates=$deploy_templates

ARG comp_list=""
LABEL kuscia.secretflow.comp_list=$comp_list

ARG translation=""
LABEL kuscia.secretflow.translation=$translation

COPY --from=builder /home/teeapp/occlum/occlum_instance /home/teeapp/occlum/occlum_instance
COPY --from=builder /home/teeapp/python-occlum /home/teeapp/python-occlum

ENV PATH /home/teeapp/python-occlum/bin:$PATH

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

WORKDIR /home/teeapp/occlum/occlum_instance
