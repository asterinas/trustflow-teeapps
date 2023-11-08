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
set -e

BLUE='\033[1;34m'
NC='\033[0m'

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
workspace_dir="$script_dir"

target_dir="/home/teeapp"
python_dir="$target_dir/python-occlum"

mkdir -p $target_dir/task

bazel --output_base=target build -c opt --define tee_type=sgx2 //teeapps/...
rm -rf $target_dir/occlum
mkdir -p $target_dir/occlum

cd $target_dir/occlum
mkdir -p teeapps/biz

# copy biz algorithms
for folder in $workspace_dir/teeapps/biz/*; do
  if [ -d "$folder" ]; then
    folder_name=$(basename "$folder")
    if [ $folder_name == "testdata" ]; then
      continue
    fi
    cp $folder/*.py teeapps/biz/
  fi
done

cd $target_dir/occlum/teeapps/biz
# Note: secretflow and teeapps/proto can copy from any biz dir
cp -rL $workspace_dir/bazel-bin/teeapps/biz/psi/psi.runfiles/sf_spec/secretflow ./
# copy common
mkdir -p teeapps/biz/common/
cp $workspace_dir/teeapps/biz/common/common.py teeapps/biz/common/
cp -rL $workspace_dir/bazel-bin/teeapps/biz/psi/psi.runfiles/teeapps/teeapps/proto teeapps/

cd $target_dir/occlum

# Initailize occlum workspace
[ -d occlum_instance ] || occlum new occlum_instance

[ -d $python_dir ] || conda create --prefix $python_dir -y python=3.8.10 pandas protobuf scikit-learn xgboost statsmodels
if [ ! -d $python_dir ]; then
  echo "Error: cannot stat '$python_dir' directory"
  exit 1
fi

cd occlum_instance
copy_bom -f $workspace_dir/python.yaml --root image --include-dir /opt/occlum/etc/template

mkdir -p image/bin/
cp $workspace_dir/bazel-bin/teeapps/framework/main image/bin/main
mkdir -p image/etc/kubetee
mkdir -p logs
cp $workspace_dir/deployment/conf/unified_attestation.json image/etc/kubetee/unified_attestation.json

# Copy glibc so to image.
mkdir -p image/opt/occlum/glibc/lib/
cp /opt/occlum/glibc/lib/libdl*.so* image/opt/occlum/glibc/lib/
cp /opt/occlum/glibc/lib/librt*.so* image/opt/occlum/glibc/lib/

#DNS
cp /opt/occlum/glibc/lib/libnss_dns.so.2 \
  /opt/occlum/glibc/lib/libnss_files.so.2 \
  /opt/occlum/glibc/lib/libresolv.so.2 \
  image/opt/occlum/glibc/lib/

cp $workspace_dir/Occlum.json .

mkdir -p certs

# test dataset
mkdir -p testdata/breast_cancer
mkdir -p integration_test
cp $workspace_dir/integration_test/* integration_test/