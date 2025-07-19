# 🔍 MySQL Binlog 数据分析解决方案

## 📋 项目概述

基于 **MySQL Binary Log (binlog)** 的实时数据变更分析系统，专门用于监控和分析指定表的增删改操作。

### 🎯 核心特性
- ✅ **实时binlog解析**: 监听MySQL binlog变更事件
- ✅ **指定表过滤**: 精确监控特定数据库和表
- ✅ **增删改跟踪**: 详细记录INSERT/UPDATE/DELETE操作
- ✅ **数据变更对比**: 记录变更前后的数据差异
- ✅ **高性能处理**: 异步处理和批量分析
- ✅ **多种存储**: 支持MySQL、ES、ClickHouse存储

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        MySQL 主库                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   用户表         │    │   订单表         │    │   商品表     │  │
│  │   users         │    │   orders        │    │   products  │  │
│  │   (监控目标)     │    │   (监控目标)     │    │   (监控目标) │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                               │                                 │
│                    ┌─────────────────────┐                     │
│                    │    Binary Log       │                     │
│                    │  • ROW格式记录      │                     │
│                    │  • 完整数据变更     │                     │
│                    │  • 事务信息         │                     │
│                    └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (实时读取)
┌─────────────────────────────────────────────────────────────────┐
│                     Binlog 分析系统                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ Binlog 读取器    │───▶│ 事件解析器       │───▶│ 数据处理器   │  │
│  │ • 连接MySQL      │    │ • 解析ROW事件    │    │ • 表过滤     │  │
│  │ • 读取binlog     │    │ • 提取变更数据   │    │ • 数据对比   │  │
│  │ • 断点续传       │    │ • 事务分组       │    │ • 格式转换   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                               │                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ 查询接口        │◀───│ 存储引擎        │───▶│ 分析报表     │  │
│  │ • REST API      │    │ • MySQL存储      │    │ • 变更统计   │  │
│  │ • GraphQL       │    │ • ES全文检索     │    │ • 趋势分析   │  │
│  │ • Web界面       │    │ • ClickHouse     │    │ • 实时监控   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
```bash
- MySQL 5.7+ 或 8.0+ (启用binlog)
- Python 3.7+
- Redis (可选，用于缓存)
- Elasticsearch (可选，用于全文检索)
```

### MySQL Binlog 配置
```ini
# my.cnf 配置
[mysqld]
# 启用binlog
log-bin=mysql-bin
binlog-format=ROW
binlog-row-image=FULL

# 设置server-id
server-id=1

# binlog保留时间
binlog_expire_logs_seconds=604800  # 7天
```

### 快速安装
```bash
# 1. 克隆项目
git clone mysql-binlog-analyzer
cd mysql-binlog-analyzer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置连接
cp config/config.example.yaml config/config.yaml
vim config/config.yaml

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动分析器
python src/main.py
```

## 📁 项目结构

```
mysql-binlog-analyzer/
├── 📄 README.md                    # 项目说明
├── 📄 requirements.txt             # Python依赖
├── 📁 config/                      # 配置文件
│   ├── config.yaml                # 主配置文件
│   ├── tables.yaml                # 监控表配置
│   └── logging.yaml               # 日志配置
├── 📁 src/                         # 源代码
│   ├── main.py                    # 主程序入口
│   ├── binlog_reader.py           # Binlog读取器
│   ├── event_parser.py            # 事件解析器
│   ├── data_processor.py          # 数据处理器
│   ├── storage/                   # 存储模块
│   │   ├── mysql_storage.py       # MySQL存储
│   │   ├── es_storage.py          # Elasticsearch存储
│   │   └── clickhouse_storage.py  # ClickHouse存储
│   ├── api/                       # API接口
│   │   ├── rest_api.py            # REST API
│   │   ├── query_service.py       # 查询服务
│   │   └── web_ui.py              # Web界面
│   └── utils/                     # 工具模块
│       ├── mysql_helper.py        # MySQL工具
│       ├── cache.py               # 缓存工具
│       └── logger.py              # 日志工具
├── 📁 scripts/                     # 脚本工具
│   ├── init_db.py                 # 数据库初始化
│   ├── backfill.py                # 历史数据回填
│   └── monitor.py                 # 监控脚本
├── 📁 sql/                         # SQL脚本
│   ├── schema.sql                 # 表结构
│   └── indexes.sql                # 索引优化
└── 📁 tests/                       # 测试用例
    ├── test_binlog_reader.py      # 测试用例
    └── test_event_parser.py       # 测试用例
```

## 🔧 配置说明

### 主配置文件
```yaml
# config/config.yaml
mysql:
  # 源数据库配置（读取binlog）
  source:
    host: "localhost"
    port: 3306
    user: "binlog_reader"
    password: "password"
    charset: "utf8mb4"
    
    # Binlog配置
    binlog:
      server_id: 1001  # 唯一server_id
      log_file: ""     # 起始文件，空表示最新
      log_pos: 4       # 起始位置
      auto_position: true
      
  # 存储数据库配置
  storage:
    host: "localhost"
    port: 3306
    user: "storage_user"
    password: "password"
    database: "binlog_analysis"

# 监控表配置
tables:
  target_tables:
    - database: "ecommerce"
      table: "users"
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "username", "email", "status"]
      
    - database: "ecommerce"
      table: "orders" 
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "user_id", "amount", "status"]
      
    - database: "ecommerce"
      table: "products"
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "name", "price", "stock"]

# 处理配置
processing:
  batch_size: 1000
  flush_interval: 5  # 秒
  worker_threads: 4
  
# 存储配置
storage:
  # 主存储
  primary: "mysql"  # mysql, elasticsearch, clickhouse
  
  # 备份存储
  backup: ["elasticsearch"]
  
  # 数据保留
  retention_days: 90
```

### 监控表配置
```yaml
# config/tables.yaml
# 详细的表监控配置
tables:
  ecommerce.users:
    operations: ["INSERT", "UPDATE", "DELETE"]
    track_columns: ["id", "username", "email", "phone", "status", "created_at", "updated_at"]
    sensitive_columns: ["password", "phone"]
    primary_key: "id"
    description: "用户基础信息表"
    
    # 特殊处理规则
    rules:
      - name: "status_change"
        condition: "OLD.status != NEW.status"
        alert: true
        
      - name: "user_deletion"
        condition: "operation = 'DELETE'"
        alert: true
        priority: "high"

  ecommerce.orders:
    operations: ["INSERT", "UPDATE", "DELETE"]
    track_columns: ["id", "user_id", "amount", "status", "created_at"]
    primary_key: "id"
    description: "订单表"
    
    rules:
      - name: "high_amount_order"
        condition: "NEW.amount > 10000"
        alert: true
        
      - name: "order_status_change"
        condition: "OLD.status != NEW.status"
        track: true
```

## 🎯 核心功能

### 1. 实时Binlog解析
```python
# 使用示例
from src.binlog_reader import BinlogReader

reader = BinlogReader(config)
reader.start_reading()

# 处理事件
for event in reader.get_events():
    if event.is_table_event():
        process_table_change(event)
```

### 2. 指定表数据变更追踪
```python
# 查询指定表的变更记录
from src.api.query_service import QueryService

query = QueryService()

# 查询用户表的所有变更
changes = query.get_table_changes(
    database="ecommerce",
    table="users",
    start_time="2024-01-01",
    end_time="2024-01-31"
)

# 查询特定操作
inserts = query.get_operations(
    database="ecommerce", 
    table="orders",
    operation="INSERT",
    limit=100
)
```

### 3. 数据变更对比
```python
# 获取UPDATE操作的变更对比
updates = query.get_update_diffs(
    database="ecommerce",
    table="users", 
    user_id=12345
)

# 结果示例
{
    "change_id": "uuid",
    "timestamp": "2024-01-15 10:30:00",
    "operation": "UPDATE",
    "primary_key": {"id": 12345},
    "changes": {
        "email": {
            "old": "old@email.com",
            "new": "new@email.com"
        },
        "status": {
            "old": "inactive", 
            "new": "active"
        }
    }
}
```

## 📊 API 接口

### REST API
```bash
# 获取表变更统计
GET /api/tables/{database}/{table}/stats
{
    "total_changes": 1500,
    "operations": {
        "INSERT": 800,
        "UPDATE": 600, 
        "DELETE": 100
    },
    "daily_stats": {...}
}

# 查询变更记录
GET /api/tables/{database}/{table}/changes?start_time=2024-01-01&limit=100
[
    {
        "id": "uuid",
        "timestamp": "2024-01-15T10:30:00Z",
        "operation": "UPDATE",
        "primary_key": {"id": 12345},
        "old_data": {...},
        "new_data": {...}
    }
]

# 查询特定记录的变更历史
GET /api/records/{database}/{table}/{primary_key}/history
[
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "operation": "UPDATE",
        "changes": {...}
    }
]
```

### GraphQL 接口
```graphql
# 查询表变更
query {
  tableChanges(
    database: "ecommerce"
    table: "users"
    operations: ["UPDATE", "DELETE"]
    limit: 50
  ) {
    id
    timestamp
    operation
    primaryKey
    changes {
      column
      oldValue
      newValue
    }
  }
}

# 聚合查询
query {
  tableStats(
    database: "ecommerce"
    table: "orders"
    timeRange: "7d"
  ) {
    totalChanges
    operationCounts {
      operation
      count
    }
    hourlyDistribution {
      hour
      count
    }
  }
}
```

## 🔍 高级功能

### 1. 实时监控面板
```python
# Web界面实时显示
from src.api.web_ui import WebUI

app = WebUI()
app.run(host="0.0.0.0", port=8080)

# 访问: http://localhost:8080
# 功能:
# - 实时变更流
# - 表操作统计
# - 变更趋势图表
# - 异常检测告警
```

### 2. 数据回填
```python
# 历史数据回填
from src.scripts.backfill import BackfillProcessor

backfill = BackfillProcessor()
backfill.process_historical_data(
    start_binlog_file="mysql-bin.000001",
    start_position=4,
    end_binlog_file="mysql-bin.000010", 
    target_tables=["ecommerce.users", "ecommerce.orders"]
)
```

### 3. 性能优化
```yaml
# 配置优化
performance:
  # 批量处理
  batch_processing:
    enabled: true
    batch_size: 5000
    flush_interval: 10
    
  # 内存优化  
  memory:
    max_events_in_memory: 100000
    gc_threshold: 50000
    
  # 并发处理
  concurrency:
    reader_threads: 2
    processor_threads: 4
    storage_threads: 2
    
  # 缓存配置
  cache:
    enabled: true
    redis_url: "redis://localhost:6379/0"
    cache_ttl: 3600
```

## 📈 监控和告警

### 系统监控
```python
# 监控指标
metrics = {
    "binlog_lag": "当前binlog处理延迟",
    "events_per_second": "每秒处理事件数",
    "storage_queue_size": "存储队列大小", 
    "error_rate": "错误率",
    "memory_usage": "内存使用率"
}

# Prometheus集成
from prometheus_client import Counter, Histogram

events_processed = Counter('binlog_events_processed_total')
processing_time = Histogram('binlog_event_processing_seconds')
```

### 异常告警
```yaml
# 告警配置
alerts:
  # 处理延迟告警
  binlog_lag:
    threshold: 300  # 5分钟
    channels: ["email", "webhook"]
    
  # 错误率告警  
  error_rate:
    threshold: 0.05  # 5%
    window: "5m"
    channels: ["slack"]
    
  # 大批量变更告警
  bulk_operations:
    threshold: 10000
    window: "1m" 
    channels: ["email", "sms"]
```

## 🛡️ 安全和权限

### 数据库权限
```sql
-- 创建binlog读取用户
CREATE USER 'binlog_reader'@'%' IDENTIFIED BY 'strong_password';

-- 授予必要权限
GRANT SELECT ON *.* TO 'binlog_reader'@'%';
GRANT REPLICATION SLAVE ON *.* TO 'binlog_reader'@'%';  
GRANT REPLICATION CLIENT ON *.* TO 'binlog_reader'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 敏感数据处理
```python
# 敏感数据脱敏
from src.utils.data_masking import DataMasker

masker = DataMasker()
masker.add_rule("users.phone", mask_phone)
masker.add_rule("users.email", mask_email)

# 自动脱敏处理
masked_data = masker.mask_sensitive_data(raw_data)
```

## 💡 使用场景

### 1. 数据变更审计
```python
# 查找用户状态变更
status_changes = query.get_changes(
    database="ecommerce",
    table="users",
    column="status",
    start_time="2024-01-01"
)

# 分析结果
for change in status_changes:
    print(f"用户 {change.user_id} 在 {change.timestamp} "
          f"状态从 {change.old_value} 变为 {change.new_value}")
```

### 2. 实时数据同步
```python
# 实时同步到ES
from src.storage.es_storage import ESStorage

es_storage = ESStorage()
for event in binlog_reader.get_events():
    if event.is_target_table():
        es_storage.sync_change(event)
```

### 3. 业务分析
```python
# 订单状态变更分析
order_analytics = query.analyze_order_status_changes(
    time_range="30d",
    group_by="hour"
)

# 用户行为分析
user_activity = query.analyze_user_activity(
    user_ids=[1001, 1002, 1003],
    operations=["INSERT", "UPDATE"]
)
```

---

🎯 **专业级MySQL Binlog数据分析解决方案，实现精确的表级变更追踪和分析！**