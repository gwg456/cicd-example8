# API 文档

本文档描述了Prefect CI/CD项目的API接口和核心组件。

## 📋 目录

- [核心模块](#核心模块)
- [配置管理](#配置管理)
- [流程定义](#流程定义)
- [部署管理](#部署管理)
- [健康检查](#健康检查)
- [指标收集](#指标收集)
- [日志系统](#日志系统)

## 🏗️ 核心模块

### config.py

配置管理模块，提供统一的配置接口。

#### Config类

```python
class Config:
    """应用配置类"""
    
    # Prefect配置
    prefect_api_url: str
    work_pool_name: str
    
    # Docker配置
    image_repo: str
    image_tag: Optional[str]
    
    # 应用配置
    log_level: str
    environment: str
    deploy_mode: bool
    
    # 调度配置
    schedule_interval: int
    
    # 超时配置
    api_timeout: int
    deployment_timeout: int
```

#### 主要方法

```python
def validate_required_settings(self) -> List[str]:
    """验证必需的配置项"""
    
def get_config_summary(self) -> Dict[str, Any]:
    """获取配置摘要信息"""
    
def print_config_info(self) -> None:
    """打印配置信息到控制台"""
    
@property
def full_image_name(self) -> str:
    """获取完整的镜像名称"""
    
@property
def is_container_env(self) -> bool:
    """检查是否在容器环境中运行"""
    
@property
def is_production(self) -> bool:
    """检查是否为生产环境"""
```

#### 使用示例

```python
from config import config

# 检查配置
missing = config.validate_required_settings()
if missing:
    print(f"缺少配置: {missing}")

# 获取配置信息
summary = config.get_config_summary()
print(summary)
```

## 🌊 流程定义

### src/flows.py

定义Prefect工作流程和任务。

#### 任务函数

```python
@task(name="greeting-task")
def generate_greeting(name: str = "World") -> str:
    """生成问候语的任务"""
    
@task(name="sleep-task")
def sleep_task(duration: int = 20) -> None:
    """休眠任务"""
    
@task(name="process-pdf-task")
def process_pdf(file_path: str = "example.pdf") -> str:
    """模拟处理PDF文件的任务"""
```

#### 流程函数

```python
@flow(name="hello-flow", log_prints=True)
def hello_flow(name: str = "World") -> str:
    """主要的问候流"""
    
@flow(name="health-check-flow")
def health_check_flow() -> Dict[str, Any]:
    """健康检查流"""
    
@flow(name="process-pdf-flow", log_prints=True)
def process_pdf_flow() -> None:
    """处理PDF文件的工作流"""
```

#### 使用示例

```python
from src.flows import hello_flow, health_check_flow

# 执行流程
result = hello_flow("Alice")
print(result)

# 健康检查
health = health_check_flow()
print(health)
```

## 🚀 部署管理

### src/deployment.py

管理Prefect流程的部署。

#### DeploymentManager类

```python
class DeploymentManager:
    """部署管理器"""
    
    def __init__(self):
        """初始化部署管理器"""
        
    async def check_prefect_connection(self) -> bool:
        """检查Prefect API连接"""
        
    def deploy_all(self) -> Dict[str, Any]:
        """部署所有已定义的流"""
        
    def _deploy_flow(self, flow_to_deploy, deployment_config: Dict[str, Any]) -> str:
        """通用部署函数"""
        
    def _generate_image_tag(self) -> str:
        """生成镜像标签"""
        
    def _get_base_env_vars(self) -> Dict[str, str]:
        """获取基础环境变量"""
        
    def _get_docker_job_variables(self) -> Dict[str, Any]:
        """获取Docker作业变量"""
```

#### 使用示例

```python
from src.deployment import DeploymentManager
import asyncio

# 创建部署管理器
manager = DeploymentManager()

# 检查连接
connected = asyncio.run(manager.check_prefect_connection())
print(f"Prefect连接状态: {connected}")

# 部署所有流程
results = manager.deploy_all()
print(results)
```

## 🏥 健康检查

### src/health.py

提供应用程序健康状态检查。

#### HealthCheck基类

```python
class HealthCheck:
    """健康检查基类"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        """初始化健康检查"""
        
    async def check(self) -> Dict[str, Any]:
        """执行健康检查"""
        
    async def _check_impl(self) -> Dict[str, Any]:
        """子类需要实现的具体检查逻辑"""
```

#### 具体健康检查类

```python
class PrefectHealthCheck(HealthCheck):
    """Prefect API健康检查"""
    
class DatabaseHealthCheck(HealthCheck):
    """数据库健康检查"""
    
class DiskSpaceHealthCheck(HealthCheck):
    """磁盘空间健康检查"""
    
class MemoryHealthCheck(HealthCheck):
    """内存使用健康检查"""
    
class ConfigurationHealthCheck(HealthCheck):
    """配置健康检查"""
```

#### HealthChecker管理器

```python
class HealthChecker:
    """健康检查管理器"""
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        
    async def run_check(self, check_name: str) -> Optional[Dict[str, Any]]:
        """运行特定的健康检查"""
        
    def add_check(self, check: HealthCheck) -> None:
        """添加自定义健康检查"""
```

#### 便捷函数

```python
async def get_health_status() -> Dict[str, Any]:
    """获取应用健康状态"""
    
async def get_readiness_status() -> Dict[str, Any]:
    """获取应用就绪状态"""
    
async def get_liveness_status() -> Dict[str, Any]:
    """获取应用存活状态"""
```

#### 使用示例

```python
from src.health import get_health_status, health_checker
import asyncio

# 获取完整健康状态
health = asyncio.run(get_health_status())
print(health)

# 运行特定检查
prefect_health = asyncio.run(health_checker.run_check("prefect_api"))
print(prefect_health)
```

## 📊 指标收集

### src/metrics.py

提供应用程序指标收集功能。

#### 指标类型

```python
class Counter:
    """计数器指标"""
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数"""
        
    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取当前值"""

class Gauge:
    """仪表盘指标"""
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置值"""
        
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加值"""

class Histogram:
    """直方图指标"""
    
    def observe(self, value: float) -> None:
        """记录观察值"""
        
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
```

#### MetricsCollector

```python
class MetricsCollector:
    """指标收集器"""
    
    def counter(self, name: str, description: str = "") -> Counter:
        """获取或创建计数器"""
        
    def gauge(self, name: str, description: str = "") -> Gauge:
        """获取或创建仪表盘"""
        
    def histogram(self, name: str, description: str = "", buckets: Optional[List[float]] = None) -> Histogram:
        """获取或创建直方图"""
        
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        
    def record_flow_execution(self, flow_name: str, duration: float, status: str) -> None:
        """记录流程执行指标"""
        
    def record_deployment(self, flow_name: str, status: str) -> None:
        """记录部署指标"""
```

#### 装饰器

```python
def record_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """装饰器：记录函数执行时间"""
```

#### 使用示例

```python
from src.metrics import metrics, record_execution_time

# 使用计数器
counter = metrics.counter("requests_total", "Total requests")
counter.inc(labels={"method": "GET", "status": "200"})

# 使用仪表盘
gauge = metrics.gauge("active_connections", "Active connections")
gauge.set(42)

# 使用直方图
histogram = metrics.histogram("request_duration_seconds", "Request duration")
histogram.observe(0.5)

# 使用装饰器
@record_execution_time("function_execution")
def my_function():
    pass

# 获取所有指标
all_metrics = metrics.get_all_metrics()
print(all_metrics)
```

## 📝 日志系统

### src/logging_config.py

提供结构化日志配置和记录功能。

#### 配置函数

```python
def configure_logging() -> None:
    """配置结构化日志"""
    
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    
def setup_global_loggers() -> Dict[str, Any]:
    """设置全局日志记录器"""
```

#### 专用日志记录器

```python
class PerformanceLogger:
    """性能日志记录器"""
    
    def start(self, operation: str, **kwargs) -> None:
        """开始性能监控"""
        
    def end(self, operation: str, **kwargs) -> float:
        """结束性能监控并记录耗时"""

class AuditLogger:
    """审计日志记录器"""
    
    def log_deployment(self, flow_name: str, deployment_id: str, status: str, **kwargs) -> None:
        """记录部署事件"""
        
    def log_flow_execution(self, flow_name: str, run_id: str, status: str, **kwargs) -> None:
        """记录流程执行事件"""

class SecurityLogger:
    """安全日志记录器"""
    
    def log_authentication_attempt(self, user: str, success: bool, **kwargs) -> None:
        """记录认证尝试"""
        
    def log_suspicious_activity(self, activity: str, details: Dict[str, Any], **kwargs) -> None:
        """记录可疑活动"""
```

#### 混入类和装饰器

```python
class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的日志记录器"""

def log_execution_time(logger: Optional[structlog.stdlib.BoundLogger] = None):
    """装饰器：记录函数执行时间"""
    
def log_function_call(logger: Optional[structlog.stdlib.BoundLogger] = None):
    """装饰器：记录函数调用"""
```

#### 使用示例

```python
from src.logging_config import get_logger, PerformanceLogger, LoggerMixin

# 基本日志记录
logger = get_logger(__name__)
logger.info("应用启动", version="1.0.0")

# 性能日志
perf_logger = PerformanceLogger(logger)
perf_logger.start("database_query")
# ... 执行操作
perf_logger.end("database_query")

# 使用混入类
class MyClass(LoggerMixin):
    def my_method(self):
        self.logger.info("方法被调用")

# 使用装饰器
@log_execution_time()
def slow_function():
    pass
```

## 🔧 工具函数

### 环境变量解析

```python
def _get_env_bool(name: str, default: bool = False) -> bool:
    """更健壮的布尔环境变量解析"""
```

### 部署入口函数

```python
def deploy_flows() -> Dict[str, Any]:
    """部署流的入口函数"""
```

## 📚 类型定义

项目使用Python类型注解，主要类型包括：

```python
from typing import Dict, List, Optional, Any, Union

# 配置类型
ConfigDict = Dict[str, Any]

# 部署结果类型
DeploymentResult = Dict[str, Union[str, Dict[str, Any]]]

# 健康检查结果类型
HealthCheckResult = Dict[str, Any]

# 指标数据类型
MetricValue = Union[int, float]
MetricLabels = Dict[str, str]
```

## 🚀 快速开始

```python
# 1. 导入必要模块
from config import config
from src.flows import hello_flow
from src.deployment import deploy_flows
from src.health import get_health_status
from src.metrics import metrics

# 2. 检查配置
if config.validate_required_settings():
    print("配置验证失败")
    exit(1)

# 3. 执行流程
result = hello_flow("API User")
print(f"流程结果: {result}")

# 4. 检查健康状态
import asyncio
health = asyncio.run(get_health_status())
print(f"健康状态: {health['status']}")

# 5. 查看指标
metrics_data = metrics.get_all_metrics()
print(f"指标数据: {metrics_data}")
```
