#!/bin/bash
#
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
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOCKER=docker
project=teeapps

OCCLUM_DEV_IMAGE=secretflow/trustflow-dev-occlum-ubuntu22.04:latest
DEV_IMAGE=secretflow/trustflow-dev-ubuntu22.04:latest

SGX2_ENCLAVE_TREE_DEVICE="/dev/sgx/enclave"
SGX2_PROVISION_TREE_DEVICE="/dev/sgx/provision"

SGX2_ENCLAVE_DEVICE="/dev/sgx_enclave"
SGX2_PROVISION_DEVICE="/dev/sgx_provision"

TDX_DEVICE="/dev/tdx_guest"

CSV_DEVICE="/dev/csv-guest"

DOCKER_DEVICE_FLAGS=""
if [ -e "$SGX2_ENCLAVE_TREE_DEVICE" ] && [ -e "$SGX2_PROVISION_TREE_DEVICE" ]; then
DEV_IMAGE=${OCCLUM_DEV_IMAGE}
DOCKER_DEVICE_FLAGS="-v $SGX2_ENCLAVE_TREE_DEVICE:$SGX2_ENCLAVE_TREE_DEVICE -v $SGX2_PROVISION_TREE_DEVICE:$SGX2_PROVISION_TREE_DEVICE"
elif [ -e "$SGX2_ENCLAVE_DEVICE" ] && [ -e "$SGX2_PROVISION_DEVICE" ]; then
DEV_IMAGE=${OCCLUM_DEV_IMAGE}
DOCKER_DEVICE_FLAGS="-v $SGX2_ENCLAVE_DEVICE:$SGX2_ENCLAVE_DEVICE -v $SGX2_PROVISION_DEVICE:$SGX2_PROVISION_DEVICE"
elif [ -e "$TDX_DEVICE" ]; then
DOCKER_DEVICE_FLAGS="-v $TDX_DEVICE:$TDX_DEVICE"
elif [ -e "$CSV_DEVICE" ]; then
DOCKER_DEVICE_FLAGS="-v $CSV_DEVICE:$CSV_DEVICE"
fi

if [[ $1 == 'enter' ]]; then
    $DOCKER exec -it ${project}-build-ubuntu-$(whoami) bash
else
    $DOCKER run --name ${project}-build-ubuntu-$(whoami) -td \
        --network=host \
        $DOCKER_DEVICE_FLAGS \
        -v $DIR:$DIR \
        -v ${HOME}/${USER}-${project}-bazel-cache-test:/root/.cache/bazel \
        -w $DIR \
        --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        --cap-add=NET_ADMIN \
        --privileged=true \
        ${DEV_IMAGE}
fi
