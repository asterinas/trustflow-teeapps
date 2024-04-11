# TeeApps
TeeApps contain a general framework for developing TEE applications and various application implementations used in federated AI/BI.

## Features
- TeeApps support different tee platforms: Intel SGX2, Intel TDX and Hygon Csv. It will be remote attested by [Capsule Manager](https://github.com/secretflow/capsule-manager) who holds the data keys corresponding to encrypted inputs. We also support simulation mode for users who do not have these tee environments.
- TeeApps use secretflow component spec to define inputs, outputs and other attributes.

## Quick Start

### Prepare dataset
Before running TeeApps, you should use [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk) to generate data keys, encrypt datasets and then register data keys and data policies to [Capsule Manager](https://github.com/secretflow/capsule-manager).

Here we will use the open-source breast cancer dataset as an example. The dataset is provided by the University of California, Irvine (UCI). It contains 569 samples. Each sample has an ID and 10 features, making it a typical binary classification dataset.

We have performed vertical partitioning on this dataset: Institution alice has the first 5 features, while Institution bob has the last 5 features and the label column. ([alice.csv](teeapps/biz/testdata/breast_cancer/alice.csv) and [bob.csv](teeapps/biz/testdata/breast_cancer/bob.csv).)
1. Alice generate data keys by [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk)
```sh
cms_util generate-data-key-b64
```
2. Alice encrypt dataset by [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk)
```sh
cms_util encrypt-file --source-file alice.csv --dest-file alice.csv.enc --data-key-b64 xxx
```
3. Alice register data keys and data policies to [Capsule Manager](https://github.com/secretflow/capsule-manager). Please refer to [Capsule Manager](https://github.com/secretflow/capsule-manager) and [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk) for details.

### Run by docker image
The simplest way to run TeeApps is to use official docker image.

We provide two images, one for simulation mode and one for production mode. You can run TeeApps on non-SGX machines in simulation mode, while production mode requires a SGX2 machine.

We suppose you have prepared dataset and got encrypted files: alice.csv.enc, bob.csv.enc.
#### Simulation Mode
1. Pull and run simulation docker
```sh
docker pull secretflow/teeapps-sim-ubuntu22.04:latest

docker run -it --name teeapps-sim --network=host secretflow/teeapps-sim-ubuntu22.04:latest bash
```

2. Copy encrypted file into docker (from host machine)
```sh
docker cp alice.csv.enc teeapps-sim:/host/testdata/breast_cancer/

docker cp bob.csv.enc teeapps-sim:/host/testdata/breast_cancer/
```
3. Generate PSI task config. Suppose carol has access to alice.csv and bob.csv.
```sh
docker cp carol.key teeapps-sim:/host/integration_test/

docker cp carol.crt teeapps-sim:/host/integration_test/

docker exec -it teeapps-sim bash

cd /host/integration_test

pip install -r requirements.txt

#  please replace params
python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path psi_task.json
```
4. Run PSI
```sh
/home/teeapp/sim/teeapps/main --plat=sim --enable_console_logger=true --enable_capsule_tls=false --entry_task_config_path=/host/integration_test/psi_task.json
```
5. Check outputs

Default log path is /host/log/app.log

The output of PSI is a encrypted table. You can skip this step and run other applications with encrypted outputs.

The output path is set in [psi.json](integration_test/psi.json) (/host/testdata/breast_cancer/join_table in this example). You can get data keys and decrypt join_table with [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk). The decryption result will be a table like following:
```sh
id,mean radius,mean texture,mean perimeter,mean area,mean smoothness,mean compactness,mean concavity,mean concave points,mean symmetry,mean fractal dimension,target
842302,17.99,10.38,122.8,1001.0,0.1184,0.2776,0.3001,0.1471,0.2419,0.07871,0
842517,20.57,17.77,132.9,1326.0,0.08474,0.07864,0.0869,0.07017,0.1812,0.05667,0
84300903,19.69,21.25,130.0,1203.0,0.1096,0.1599,0.1974,0.1279,0.2069,0.05999,0
84348301,11.42,20.38,77.58,386.1,0.1425,0.2839,0.2414,0.1052,0.2597,0.09744,0
84358402,20.29,14.34,135.1,1297.0,0.1003,0.1328,0.198,0.1043,0.1809,0.05883,0
843786,12.45,15.7,82.57,477.1,0.1278,0.17,0.1578,0.08089,0.2087,0.07613,0
844359,18.25,19.98,119.6,1040.0,0.09463,0.109,0.1127,0.074,0.1794,0.05742,0
84458202,13.71,20.83,90.2,577.9,0.1189,0.1645,0.09366,0.05985,0.2196,0.07451,0
844981,13.0,21.82,87.5,519.8,0.1273,0.1932,0.1859,0.09353,0.235,0.07389,0
...
```
6. Run Other applications

You can modify task configs or write a new task config by yourself to run other applications. For example, you can split dataset.
```sh
python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path train_test_split.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path train_test_split_task.json

/home/teeapp/sim/teeapps/main --plat=sim --enable_console_logger=true --enable_capsule_tls=false --entry_task_config_path=/host/integration_test/train_test_split_task.json
```

#### SGX Mode(Occlum Mode)
1. Pull and run sgx docker image
```sh
docker pull secretflow/teeapps-sgx-ubuntu22.04:latest

docker run -it --name teeapps-sgx --network=host -v /dev/sgx_enclave:/dev/sgx/enclave -v /dev/sgx_provision:/dev/sgx/provision --privileged=true secretflow/teeapps-sgx-ubuntu22.04:latest bash
```
2. Modify PCCS config

Set real PCCS URL and set use_secure_cert to false in /etc/sgx_default_qcnl.conf.

```
{
  // *** ATTENTION : This file is in JSON format so the keys are case sensitive. Don't change them.

  //PCCS server address
  "pccs_url": "https://localhost:8081/sgx/certification/v3/",

  // To accept insecure HTTPS certificate, set this option to false
  "use_secure_cert": true,

  // You can use the Intel PCS or another PCCS to get quote verification collateral.  Retrieval of PCK
  // Certificates will always use the PCCS described in PCCS_URL.  When COLLATERAL_SERVICE is not defined, both
  // PCK Certs and verification collateral will be retrieved using PCCS_URL
  //"collateral_service": "https://api.trustedservices.intel.com/sgx/certification/v3/",

  // If you use a PCCS service to get the quote verification collateral, you can specify which PCCS API version is to be used.
  // The legacy 3.0 API will return CRLs in HEX encoded DER format and the sgx_ql_qve_collateral_t.version will be set to 3.0, while
  // the new 3.1 API will return raw DER format and the sgx_ql_qve_collateral_t.version will be set to 3.1. The PCCS_API_VERSION
  // setting is ignored if COLLATERAL_SERVICE is set to the Intel PCS. In this case, the PCCS_API_VERSION is forced to be 3.1
  // internally.  Currently, only values of 3.0 and 3.1 are valid.  Note, if you set this to 3.1, the PCCS use to retrieve
  // verification collateral must support the new 3.1 APIs.
  //"pccs_api_version": "3.1",

  // Maximum retry times for QCNL. If RETRY is not defined or set to 0, no retry will be performed.
  // It will first wait one second and then for all forthcoming retries it will double the waiting time.
  // By using RETRY_DELAY you disable this exponential backoff algorithm
  "retry_times": 6,

  // Sleep this amount of seconds before each retry when a transfer has failed with a transient error
  "retry_delay": 10,

  // If LOCAL_PCK_URL is defined, the QCNL will try to retrieve PCK cert chain from LOCAL_PCK_URL first,
  // and failover to PCCS_URL as in legacy mode.
  //"local_pck_url": "http://localhost:8081/sgx/certification/v3/",

  // If LOCAL_PCK_URL is not defined, the QCNL will cache PCK certificates in memory by default.
  // The cached PCK certificates will expire after PCK_CACHE_EXPIRE_HOURS hours.
  "pck_cache_expire_hours": 168

  // You can add custom request headers and parameters to the get certificate API.
  // But the default PCCS implementation just ignores them.
  //,"custom_request_options" : {
  //  "get_cert" : {
  //    "headers": {
  //      "head1": "value1"
  //    },
  //    "params": {
  //      "param1": "value1",
  //      "param2": "value2"
  //    }
  //  }
  //}
}
```

Copy /etc/sgx_default_qcnl.conf to occlum instance image
```
cp /etc/sgx_default_qcnl.conf /home/teeapp/occlum/occlum_instance/image/etc/
```

3. Build

You need a pair of asymmetric key to sign TeeApps in production mode. You can generate use openssl if you do not have.
```sh
openssl genrsa -3 -out private_key.pem 3072

openssl rsa -in private_key.pem -pubout -out public_key.pem
```
Build occlum with your private key.
```sh
cd /home/teeapp/occlum/occlum_instance

occlum build -f --sign-key /path/to/private_key.pem
```

4. Copy encrypted file into docker (on host machine)
```sh
docker cp alice.csv.enc teeapps-sgx:/home/teeapp/occlum/occlum_instance/testdata/breast_cancer/

docker cp bob.csv.enc teeapps-sgx:/home/teeapp/occlum/occlum_instance/testdata/breast_cancer/
```

5. Generate PSI task config. Suppose carol has access to alice.csv and bob.csv.
```sh
docker cp carol.key teeapps-sgx:/home/teeapp/occlum/occlum_instance/integration_test/

docker cp carol.crt teeapps-sgx:/home/teeapp/occlum/occlum_instance/integration_test/

docker exec -it teeapps-sgx bash

cd /home/teeapp/occlum/occlum_instance/integration_test/

pip install -r requirements.txt

#  please replace params
python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path psi_task.json
```

6. Run PSI
```sh
cd /home/teeapp/occlum/occlum_instance

occlum run /bin/main --plat=sgx --enable_console_logger=true --enable_capsule_tls=false --entry_task_config_path=/host/integration_test/psi_task.json
```

7. Check PSI output or run other applications

Default log path is /home/teeapp/occlum/occlum_instance/log/app.log

You can get data keys and decrypt /home/teeapp/occlum/occlum_instance/testdata/breast_cancer/join_table with [Capsule Manager SDK](https://github.com/secretflow/capsule-manager-sdk).

You can also modify task configs or write a new task config by yourself to run other applications with encrypted join_table.

#### TDX Mode
1. Pull and run tdx docker image in a Intel trusted domain(TD VM)
```sh
docker pull secretflow/teeapps-tdx-ubuntu22.04:latest

docker run -it --name teeapps-tdx --network=host -v /dev/tdx_guest:/dev/tdx_guest --privileged=true secretflow/teeapps-tdx-ubuntu22.04:latest bash
```

2. Modify PCCS config
Set real PCCS URL and set use_secure_cert to false in /etc/sgx_default_qcnl.conf. This step is the same as in SGX mode.

3. Copy encrypted file into docker (from host machine)
```sh
docker cp alice.csv.enc teeapps-tdx:/host/testdata/breast_cancer/

docker cp bob.csv.enc teeapps-tdx:/host/testdata/breast_cancer/
```

4. Generate PSI task config. Suppose carol has access to alice.csv and bob.csv.
```sh
docker cp carol.key teeapps-tdx:/host/integration_test/

docker cp carol.crt teeapps-tdx:/host/integration_test/

docker exec -it teeapps-tdx bash

cd /host/integration_test

pip install -r requirements.txt

#  please replace params
python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path psi_task.json
```

5. Run PSI
```sh
/home/teeapp/tdx/teeapps/main --plat=tdx --enable_console_logger=true --enable_capsule_tls=false --entry_task_config_path=/host/integration_test/psi_task.json
```

6. Check outputs or run other applications
Same as in simulation mode

#### CSV Mode
1. Make and install csv-guest driver if your CSV VM does not have /dev/csv-guest

Download https://gitee.com/anolis/hygon-devkit/blob/master/csv/attestation/csv-guest.c and compile with following Makefile:
```makefile
obj-m += csv-guest.o

all:
        make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
        make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

Install this module
```sh
insmod csv-guest.ko
```

2. Pull and run csv docker image in your Hygon CSV VM
```sh
docker pull secretflow/teeapps-csv-ubuntu22.04:latest

docker run -it --name teeapps-csv --network=host -v /dev/csv-guest:/dev/csv-guest --privileged=true secretflow/teeapps-csv-ubuntu22.04:latest bash
```

3. Copy encrypted file into docker (from host machine)
```sh
docker cp alice.csv.enc teeapps-csv:/host/testdata/breast_cancer/

docker cp bob.csv.enc teeapps-csv:/host/testdata/breast_cancer/
```

3. Generate PSI task config. Suppose carol has access to alice.csv and bob.csv.
```sh
docker cp carol.key teeapps-csv:/host/integration_test/

docker cp carol.crt teeapps-csv:/host/integration_test/

docker exec -it teeapps-csv bash

cd /host/integration_test

pip install -r requirements.txt

#  please replace params
python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path psi_task.json
```

4. Run PSI
```sh
/home/teeapp/csv/teeapps/main --plat=csv --enable_console_logger=true --enable_capsule_tls=false --entry_task_config_path=/host/integration_test/psi_task.json
```

5. Check outputs or run other applications
Same as in simulation mode

## Build By Source code

Enter dev docker container
``` sh
# create a dev docker container
bash env.sh

# enter the dev docker container
bash env.sh enter
```

### Simulation Mode
```sh
bash scripts/build_sim.sh
```

### SGX Mode(Occlum Mode)
```sh
bash scripts/build_occlum.sh
```

### TDX Mode
```sh
bash scripts/build_tdx.sh
```

### CSV Mode
```sh
bash scripts/build_csv.sh
```

## Support mTLS

To enable mTLS between TeeApps and Capsule Manager, you should firstly deploy a CA certification, a client certification and a client private key in following path. And then replace capsule-manager endpoint's ip with a domain name. Finally, enable tls in start command.

You may need to add a record in /etc/hosts like:
```
capsule-manager 127.0.0.1
```

### Simulation Mode
```sh
docker cp ca.crt teeapps-sim:/host/certs/ca.crt

docker cp client.crt teeapps-sim:/host/certs/client.crt

docker cp client.key teeapps-sim:/host/certs/client.key

python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint capsule-manager:8888 --tee_task_config_path psi_task.json

/home/teeapp/sim/teeapps/main --plat=sim --enable_console_logger=true --enable_capsule_tls=true --entry_task_config_path=/host/integration_test/psi_task.json
```

### SGX Mode (Occlum Mode)
```sh
docker cp ca.crt teeapps-sgx:/home/teeapp/occlum/occlum_instance/certs/ca.crt

docker cp client.crt teeapps-sgx:/home/teeapp/occlum/occlum_instance/certs/client.crt

docker cp client.key teeapps-sgx:/home/teeapp/occlum/occlum_instance/certs/client.key

python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint capsule-manager:8888 --tee_task_config_path psi_task.json

occlum run /bin/main --plat=sgx --enable_console_logger=true --enable_capsule_tls=true --entry_task_config_path=/host/integration_test/psi_task.json
```


### TDX Mode
```sh
docker cp ca.crt teeapps-tdx:/host/certs/ca.crt

docker cp client.crt teeapps-tdx:/host/certs/client.crt

docker cp client.key teeapps-tdx:/host/certs/client.key

python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint capsule-manager:8888 --tee_task_config_path psi_task.json

/home/teeapp/tdx/teeapps/main --plat=tdx --enable_console_logger=true --enable_capsule_tls=true --entry_task_config_path=/host/integration_test/psi_task.json
```


### CSV Mode
```sh
docker cp ca.crt teeapps-csv:/host/certs/ca.crt

docker cp client.crt teeapps-csv:/host/certs/client.crt

docker cp client.key teeapps-csv:/host/certs/client.key

python3 convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint capsule-manager:8888 --tee_task_config_path psi_task.json

/home/teeapp/csv/teeapps/main --plat=csv --enable_console_logger=true --enable_capsule_tls=true --entry_task_config_path=/host/integration_test/psi_task.json
```