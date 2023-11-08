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

FROM secretflow/occlum:0.29.5-ubuntu20.04

LABEL maintainer="secretflow-contact@service.alipay.com"

USER root:root
ENV TZ=Asia/Shanghai


RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak
COPY sources.list /etc/apt/sources.list
RUN apt clean && apt update && apt install -y ninja-build && apt install -y ssh && apt install -y python3 python3-pip && rm -f /etc/ssh/ssh_host_*

RUN python3 -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip cache purge

RUN pip install pandas xgboost statsmodels scikit-learn sklearn2pmml

RUN mkdir -p ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# install bazel
RUN apt install npm -y && npm install -g @bazel/bazelisk

# install golang
RUN apt install golang -y


# change dash to bash as default shell
RUN ln -sf /usr/bin/bash /bin/sh

# install conda
RUN apt install wget -y && wget -O /tmp/Miniconda3-latest-Linux-x86_64.sh http://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash /tmp/Miniconda3-latest-Linux-x86_64.sh -b && ln -sf /root/miniconda3/bin/conda /usr/bin/conda
COPY .condarc /root/.condarc

# update gcc and g++ to 11
RUN apt install -y software-properties-common
RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test
RUN sed -i "s/ppa.launchpad.net/launchpad.proxy.ustclug.org/g" /etc/apt/sources.list.d/*.list
RUN sed -ri 's#(.*http)(://launchpad.proxy.ustclug.org.*)#\1s\2#g' /etc/apt/sources.list /etc/apt/sources.list.d/*.list
RUN apt purge -y gcc-9 g++-9
RUN apt update && apt install gcc-11 g++-11 nasm openjdk-11-jdk -y && \
  ln -s /usr/bin/gcc-11 /usr/bin/gcc && \
  ln -s /usr/bin/g++-11 /usr/bin/g++

# run as root for now
WORKDIR /home/admin/
