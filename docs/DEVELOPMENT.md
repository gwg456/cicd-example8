# 开发指南

本文档提供了Prefect CI/CD示例项目的详细开发指南。

## 📋 目录

- [开发环境设置](#开发环境设置)
- [项目结构](#项目结构)
- [开发工作流](#开发工作流)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)

## 🛠️ 开发环境设置

### 前置要求

- Python 3.12+
- Docker
- Git
- Make (可选)

### 快速开始

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd cicd-example8
   ```

2. **设置虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   # 使用pyproject.toml（推荐）
   pip install -e ".[dev]"
   
   # 或使用传统方式
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件设置你的配置
   ```

5. **安装pre-commit钩子**
   ```bash
   pre-commit install
   ```

### IDE配置

#### VS Code

推荐的扩展：
- Python
- Pylance
- Ruff
- GitLens
- Docker

推荐的设置（`.vscode/settings.json`）：
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm

1. 设置Python解释器为虚拟环境
2. 配置代码风格为Black
3. 启用pytest作为测试运行器
4. 配置Ruff作为代码检查工具

## 📁 项目结构

```
cicd-example8/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── flows.py                  # Prefect流程定义
│   ├── deployment.py             # 部署管理
│   ├── logging_config.py         # 日志配置
│   ├── health.py                 # 健康检查
│   └── metrics.py                # 指标收集
├── tests/                        # 测试代码
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── e2e/                      # 端到端测试
├── tools/                        # 工具脚本
├── scripts/                      # 管理脚本
├── docs/                         # 文档
├── .github/workflows/            # CI/CD配置
├── config.py                     # 配置管理
├── flow.py                       # 主入口
├── pyproject.toml               # 项目配置
├── requirements*.txt            # 依赖文件
└── Dockerfile                   # 容器配置
```

## 🔄 开发工作流

### 1. 功能开发

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **开发代码**
   - 遵循代码规范
   - 编写测试
   - 更新文档

3. **运行测试**
   ```bash
   pytest tests/
   ```

4. **代码检查**
   ```bash
   ruff check .
   mypy src/
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### 2. 测试流程

```bash
# 运行所有测试
pytest

# 运行特定类型的测试
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# 运行覆盖率测试
pytest --cov=src --cov-report=html

# 运行性能测试
pytest -m slow
```

### 3. 本地部署测试

```bash
# 构建Docker镜像
docker build -t cicd-example:dev .

# 运行容器
docker run --rm \
  -e PREFECT_API_URL=http://localhost:4200/api \
  -e DEPLOY_MODE=false \
  cicd-example:dev
```

## 📝 代码规范

### Python代码风格

- 使用Black进行代码格式化
- 使用Ruff进行代码检查
- 使用MyPy进行类型检查
- 遵循PEP 8规范

### 命名约定

- **文件名**: 使用下划线分隔的小写字母
- **类名**: 使用PascalCase
- **函数名**: 使用snake_case
- **常量**: 使用UPPER_CASE
- **私有成员**: 以下划线开头

### 文档字符串

使用Google风格的文档字符串：

```python
def example_function(param1: str, param2: int) -> bool:
    """
    函数的简短描述。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    
    Raises:
        ValueError: 当参数无效时抛出
    """
    pass
```

### 类型注解

所有公共函数和方法都应该有类型注解：

```python
from typing import Dict, List, Optional

def process_data(
    data: List[Dict[str, str]], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """处理数据并返回结果"""
    pass
```

## 🧪 测试指南

### 测试结构

- **单元测试**: 测试单个函数或类
- **集成测试**: 测试组件间的交互
- **端到端测试**: 测试完整的用户场景

### 测试命名

```python
class TestConfigurationManager:
    def test_load_config_from_env_vars(self):
        """测试从环境变量加载配置"""
        pass
    
    def test_validate_required_settings_missing_config(self):
        """测试缺少必需配置时的验证"""
        pass
```

### 使用Fixtures

```python
@pytest.fixture
def mock_config():
    """创建模拟配置对象"""
    return Config(
        prefect_api_url="http://test:4200/api",
        work_pool_name="test-pool"
    )

def test_deployment_with_mock_config(mock_config):
    """使用模拟配置测试部署"""
    pass
```

### 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await some_async_function()
    assert result is not None
```

## 🐛 调试技巧

### 日志调试

```python
from src.logging_config import get_logger

logger = get_logger(__name__)

def debug_function():
    logger.debug("调试信息", extra_data="value")
    logger.info("信息日志")
    logger.error("错误日志", error="error_details")
```

### 使用调试器

```python
import ipdb

def problematic_function():
    ipdb.set_trace()  # 设置断点
    # 你的代码
```

### 性能分析

```python
from src.logging_config import PerformanceLogger

perf_logger = PerformanceLogger(logger)

def performance_critical_function():
    perf_logger.start("operation_name")
    # 你的代码
    duration = perf_logger.end("operation_name")
```

## ⚡ 性能优化

### 1. 异步编程

```python
import asyncio

async def optimized_function():
    # 并行执行多个任务
    tasks = [
        async_task_1(),
        async_task_2(),
        async_task_3()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param):
    # 昂贵的计算
    return result
```

### 3. 批处理

```python
def process_items_in_batches(items, batch_size=100):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
```

## 🔧 常用命令

### Make命令

```bash
make help              # 显示帮助
make install           # 安装依赖
make test              # 运行测试
make lint              # 代码检查
make format            # 代码格式化
make build             # 构建Docker镜像
make deploy            # 部署应用
```

### 依赖管理

```bash
# 安装新依赖
pip install package-name
pip freeze > requirements-lock.txt

# 更新依赖
python scripts/manage_deps.py update-lock

# 检查安全漏洞
python scripts/manage_deps.py check-security
```

### Git工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交代码
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature

# 创建Pull Request
# 在GitHub上创建PR
```

## 📚 参考资源

- [Prefect文档](https://docs.prefect.io/)
- [Python类型注解](https://docs.python.org/3/library/typing.html)
- [pytest文档](https://docs.pytest.org/)
- [Docker最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Git工作流](https://www.atlassian.com/git/tutorials/comparing-workflows)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

请确保：
- 代码通过所有测试
- 遵循代码规范
- 更新相关文档
- 添加适当的测试
