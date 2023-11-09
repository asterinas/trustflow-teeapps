# 集成测试

## 示例

### 安装requirement
```
pip install -r requirement.txt
```

### 将任务配置的json转成tee_task_config
```
python convert.py --cert_path carol.crt --prikey_path carol.key --task_config_path psi.json --scope default --capsule_manager_endpoint 127.0.0.1:8888 --tee_task_config_path psi_task.json
```

### 进入occlum_instance目录运行psi
```
cd /home/teeapp/occlum/occlum_instance/
occlum run /bin/main --entry_task_config_path=/host/integration_test/psi_task.json
```
