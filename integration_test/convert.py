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


from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import json
import base64

import click


def sha256(input: bytes) -> bytes:
    h = hashes.Hash(hashes.SHA256())
    h.update(input)
    return h.finalize()


@click.command()
@click.option("--cert_path", type=click.STRING, required=True)
@click.option("--prikey_path", type=click.STRING, required=True)
@click.option("--task_config_path", type=click.STRING, required=True)
@click.option("--scope", type=click.STRING, required=True)
@click.option("--capsule_manager_endpoint", type=click.STRING, required=True)
@click.option("--tee_task_config_path", type=click.STRING, required=True)
def convert_to_tee_task_config(
    cert_path,
    prikey_path,
    task_config_path,
    scope,
    capsule_manager_endpoint,
    tee_task_config_path,
) -> None:
    # 读取x509证书
    with open(cert_path, "rb") as file:
        cert_data = file.read()
    # 解析证书
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    # 获取公钥
    public_key = cert.public_key()

    # 读取私钥文件
    with open(prikey_path, "rb") as file:
        private_key_data = file.read()
    private_key = serialization.load_pem_private_key(
        private_key_data, password=None, backend=default_backend()
    )

    # 处理json文件
    with open(task_config_path, "r") as file:
        origin_json = json.load(file)
    tee_task_config = {}
    party_id = (
        base64.b32encode(
            sha256(
                public_key.public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
        )
        .decode("utf-8")
        .rstrip("=")
    )
    tee_task_config["task_initiator_id"] = party_id

    tee_task_config["task_initiator_certs"] = [cert_data.decode("utf-8")]

    tee_task_config["scope"] = scope

    node_eval_param_json = json.dumps(origin_json["sf_node_eval_param"])
    node_eval_param_json_b64 = base64.b64encode(
        node_eval_param_json.encode("utf-8")
    ).decode("utf-8")
    tee_task_config["task_body"] = node_eval_param_json_b64

    sign_content = (
        tee_task_config["task_initiator_id"]
        + "."
        + tee_task_config["scope"]
        + "."
        + tee_task_config["task_body"]
    )
    # 使用私钥进行签名
    signature = private_key.sign(
        sign_content.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    tee_task_config["signature"] = signature_b64
    tee_task_config["sign_algorithm"] = "RS256"
    tee_task_config["capsule_manager_endpoint"] = capsule_manager_endpoint

    # 转换成task_json
    task_json = {}
    task_json["task_input_config"] = {}
    task_json["task_input_config"]["tee_task_config"] = tee_task_config

    # 将JSON对象保存到文件
    with open(tee_task_config_path, "w") as file:
        json.dump(task_json, file, indent=2)


if __name__ == "__main__":
    convert_to_tee_task_config()
