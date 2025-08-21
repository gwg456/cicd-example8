# 故障排除手册

本文档提供了Prefect CI/CD项目常见问题的解决方案。

## 📋 目录

- [常见问题](#常见问题)
- [部署问题](#部署问题)
- [网络连接问题](#网络连接问题)
- [Docker问题](#docker问题)
- [依赖问题](#依赖问题)
- [性能问题](#性能问题)
- [日志分析](#日志分析)
- [调试工具](#调试工具)

## 🔧 常见问题

### Q1: 导入错误 "ModuleNotFoundError"

**症状**: 运行时出现模块导入错误

**原因**: 
- Python路径配置问题
- 依赖未正确安装
- 虚拟环境未激活

**解决方案**:
```bash
# 1. 检查虚拟环境
which python
pip list

# 2. 重新安装依赖
pip install -e ".[dev]"

# 3. 检查PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 4. 验证安装
python -c "import src.flows; print('Import successful')"
```

### Q2: 配置验证失败

**症状**: "缺少必要的环境变量" 错误

**原因**: 环境变量未正确设置

**解决方案**:
```bash
# 1. 检查当前环境变量
env | grep PREFECT
env | grep DEPLOY

# 2. 复制并编辑配置文件
cp .env.example .env
# 编辑 .env 文件

# 3. 验证配置
python -c "from config import config; print(config.validate_required_settings())"

# 4. 使用make命令验证
make validate
```

### Q3: 测试失败

**症状**: pytest运行失败

**原因**: 
- 测试环境配置问题
- 依赖冲突
- 测试数据问题

**解决方案**:
```bash
# 1. 运行特定测试
pytest tests/unit/test_config.py -v

# 2. 检查测试依赖
pip install pytest pytest-cov pytest-asyncio

# 3. 清理缓存
pytest --cache-clear

# 4. 详细输出
pytest -v -s --tb=long
```

## 🚀 部署问题

### 部署超时

**症状**: 部署过程中出现超时错误

**诊断步骤**:
```bash
# 1. 检查网络连接
curl -v $PREFECT_API_URL/health

# 2. 增加超时时间
export DEPLOYMENT_TIMEOUT=300
export API_TIMEOUT=600

# 3. 检查工作池状态
prefect work-pool ls

# 4. 手动测试部署
python -c "
from src.deployment import DeploymentManager
import asyncio
manager = DeploymentManager()
result = asyncio.run(manager.check_prefect_connection())
print(f'Connection: {result}')
"
```

**解决方案**:
1. 增加超时配置
2. 检查网络连接
3. 验证Prefect服务器状态
4. 使用本地Prefect服务器进行测试

### 工作池不存在

**症状**: "work_pool not found" 错误

**解决方案**:
```bash
# 1. 列出可用工作池
prefect work-pool ls

# 2. 创建新工作池
prefect work-pool create my-docker-pool2 --type docker

# 3. 检查工作池配置
prefect work-pool inspect my-docker-pool2

# 4. 更新环境变量
export WORK_POOL_NAME=existing-pool-name
```

### Docker镜像构建失败

**症状**: Docker构建过程中出现错误

**解决方案**:
```bash
# 1. 检查Dockerfile语法
docker build --no-cache -t test-image .

# 2. 使用详细输出
docker build --progress=plain -t test-image .

# 3. 检查.dockerignore
cat .dockerignore

# 4. 分阶段构建
docker build --target builder -t test-builder .
docker build --target runtime -t test-runtime .
```

## 🌐 网络连接问题

### Prefect API连接失败

**症状**: 无法连接到Prefect API

**诊断命令**:
```bash
# 1. 基本连接测试
ping prefect-server-host
telnet prefect-server-host 4200

# 2. HTTP连接测试
curl -v $PREFECT_API_URL/health
curl -v $PREFECT_API_URL/api/health

# 3. 检查防火墙
sudo ufw status
sudo iptables -L

# 4. 检查DNS解析
nslookup prefect-server-host
dig prefect-server-host
```

**解决方案**:
1. 验证API URL格式
2. 检查防火墙设置
3. 验证网络连接
4. 使用代理或VPN（如果需要）

### 容器网络问题

**症状**: 容器内无法访问外部服务

**解决方案**:
```bash
# 1. 检查容器网络
docker network ls
docker network inspect bridge

# 2. 使用host网络模式
docker run --network host your-image

# 3. 检查容器内网络
docker exec -it container-id ping google.com
docker exec -it container-id nslookup prefect-server

# 4. 添加DNS配置
docker run --dns 8.8.8.8 your-image
```

## 🐳 Docker问题

### 镜像构建慢

**症状**: Docker构建时间过长

**优化方案**:
```bash
# 1. 使用构建缓存
docker build --cache-from your-image:latest .

# 2. 多阶段构建优化
# 在Dockerfile中使用多阶段构建

# 3. 使用.dockerignore
echo "*.pyc" >> .dockerignore
echo "__pycache__" >> .dockerignore

# 4. 使用国内镜像源
# 在Dockerfile中配置镜像源
```

### 容器权限问题

**症状**: 容器内权限不足

**解决方案**:
```bash
# 1. 检查用户权限
docker exec -it container-id whoami
docker exec -it container-id id

# 2. 使用正确的用户
docker run --user 1000:1000 your-image

# 3. 修改文件权限
docker exec -it container-id chmod +x /app/script.sh

# 4. 检查SELinux（如果适用）
getenforce
setsebool -P container_manage_cgroup on
```

## 📦 依赖问题

### 版本冲突

**症状**: 依赖版本冲突错误

**解决方案**:
```bash
# 1. 检查依赖冲突
pip check

# 2. 查看依赖树
pip show package-name
pipdeptree

# 3. 创建新的虚拟环境
python -m venv fresh_venv
source fresh_venv/bin/activate
pip install -e ".[dev]"

# 4. 使用依赖管理脚本
python scripts/manage_deps.py validate
```

### 安装失败

**症状**: pip安装依赖失败

**解决方案**:
```bash
# 1. 更新pip
pip install --upgrade pip

# 2. 清理缓存
pip cache purge

# 3. 使用国内源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package-name

# 4. 安装系统依赖
sudo apt-get update
sudo apt-get install python3-dev build-essential
```

## ⚡ 性能问题

### 流程执行慢

**症状**: Prefect流程执行时间过长

**诊断方法**:
```python
# 1. 添加性能监控
from src.logging_config import PerformanceLogger
from src.metrics import record_execution_time

@record_execution_time("flow_execution")
def your_flow():
    pass

# 2. 检查任务并行度
# 在流程中使用并发执行

# 3. 分析日志
grep "duration" /var/log/prefect.log
```

### 内存使用过高

**症状**: 应用内存占用过高

**解决方案**:
```bash
# 1. 监控内存使用
docker stats container-id
top -p process-id

# 2. 分析内存泄漏
python -m memory_profiler your_script.py

# 3. 优化代码
# 使用生成器而不是列表
# 及时释放大对象
# 使用弱引用

# 4. 调整容器资源限制
docker run --memory=512m your-image
```

## 📊 日志分析

### 查看应用日志

```bash
# 1. 容器日志
docker logs container-id
docker logs -f container-id  # 实时查看

# 2. 应用日志文件
tail -f /var/log/app.log
grep ERROR /var/log/app.log

# 3. 结构化日志查询
# 如果使用JSON格式日志
cat app.log | jq '.level == "ERROR"'

# 4. 日志聚合
# 使用ELK stack或类似工具
```

### 日志级别调整

```bash
# 1. 临时调整
export LOG_LEVEL=DEBUG
python flow.py

# 2. 运行时调整
# 在代码中动态调整日志级别

# 3. 容器中调整
docker run -e LOG_LEVEL=DEBUG your-image
```

## 🛠️ 调试工具

### 健康检查

```bash
# 1. 应用健康检查
curl http://localhost:8080/health

# 2. 手动健康检查
python -c "
import asyncio
from src.health import get_health_status
result = asyncio.run(get_health_status())
print(result)
"

# 3. 组件检查
make test-connection
make validate
```

### 指标监控

```bash
# 1. 查看指标
curl http://localhost:8080/metrics

# 2. 手动收集指标
python -c "
from src.metrics import metrics
print(metrics.get_all_metrics())
"
```

### 交互式调试

```python
# 1. 使用ipdb
import ipdb; ipdb.set_trace()

# 2. 使用pdb
import pdb; pdb.set_trace()

# 3. 远程调试
# 配置IDE的远程调试功能
```

## 🆘 获取帮助

### 内部资源

1. 查看项目文档: `docs/`
2. 运行健康检查: `make check`
3. 查看配置摘要: `make config-summary`
4. 运行诊断脚本: `python scripts/diagnose.py`

### 外部资源

1. [Prefect社区](https://discourse.prefect.io/)
2. [GitHub Issues](https://github.com/PrefectHQ/prefect/issues)
3. [Stack Overflow](https://stackoverflow.com/questions/tagged/prefect)
4. [Docker文档](https://docs.docker.com/)

### 报告问题

创建问题报告时，请包含：

1. **环境信息**:
   ```bash
   python --version
   docker --version
   pip list | grep prefect
   ```

2. **配置信息**:
   ```bash
   make config-summary
   ```

3. **错误日志**:
   ```bash
   # 相关的错误日志和堆栈跟踪
   ```

4. **重现步骤**:
   - 详细的操作步骤
   - 预期结果 vs 实际结果

5. **系统信息**:
   ```bash
   uname -a
   cat /etc/os-release
   ```
