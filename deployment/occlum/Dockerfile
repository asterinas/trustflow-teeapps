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

FROM secretflow/trustflow-dev-occlum-ubuntu22.04:latest as builder


WORKDIR /home/admin/dev

COPY .bazelrc .bazelversion BUILD.bazel WORKSPACE ./
COPY teeapps ./teeapps
COPY integration_test ./integration_test
COPY bazel ./bazel
COPY deployment/occlum/Occlum.json ./deployment/occlum/Occlum.json
COPY deployment/occlum/python.yaml ./deployment/occlum/python.yaml
COPY scripts/build_occlum.sh ./scripts/build_occlum.sh

RUN bash ./scripts/build_occlum.sh

FROM secretflow/trustflow-release-occlum-ubuntu22.04:latest

# for occlum build, we need to install following pkgs
RUN apt update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y \
    build-essential \
    rsync \
    libfuse2 \
    && apt clean 

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

WORKDIR /home/teeapp/occlum/occlum_instance


