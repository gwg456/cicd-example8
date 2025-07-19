# 🔍 MySQL 数据库变更监控系统

## 📋 项目概述

这是一个**完全基于 MySQL Binary Log** 的数据库变更监控系统，专注于：
- **实时监控**: 通过解析Binary Log实现零延迟的变更检测
- **精确指定**: 支持精确指定要监控的数据库和表
- **完整记录**: 记录所有INSERT、UPDATE、DELETE和DDL操作
- **智能告警**: 基于规则的灵活告警机制

## 🎯 核心特性

### 🚀 基于 Binary Log 的优势
- ✅ **零性能影响**: 不在应用层添加任何代码，对业务无影响
- ✅ **实时监控**: 直接读取Binary Log，毫秒级变更检测
- ✅ **完整记录**: 捕获所有数据变更，包括存储过程、触发器等
- ✅ **断点续传**: 支持从指定位置恢复监控，不遗漏任何变更
- ✅ **事务完整性**: 保证事务级别的数据一致性

### 📊 监控功能
- 🔄 **DML监控**: INSERT、UPDATE、DELETE操作实时跟踪
- 🏗️ **DDL监控**: CREATE、ALTER、DROP等结构变更监控
- 📈 **统计分析**: 变更频率、热点表分析
- 🎯 **精确过滤**: 支持数据库、表级别的精确监控
- 🔍 **数据对比**: 记录变更前后的完整数据

### 🔔 告警系统
- 📧 **邮件告警**: 详细的变更报告邮件通知
- 🌐 **Webhook集成**: 支持自定义API回调
- 📱 **批量告警**: 大量变更的批量通知
- 📊 **汇总报告**: 定期变更统计报告

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MySQL 数据库服务器                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   数据库 A       │    │   数据库 B       │    │   数据库 C       │  │
│  │  • users        │    │  • orders       │    │  • products     │  │
│  │  • profiles     │    │  • payments     │    │  • inventory    │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                │                                     │
│                         ┌─────────────────┐                         │
│                         │   Binary Log    │                         │
│                         │  • mysql-bin.001│                         │
│                         │  • mysql-bin.002│                         │
│                         │  • ...          │                         │
│                         └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ (实时读取)
┌─────────────────────────────────────────────────────────────────────┐
│                      变更监控系统                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ Binlog Collector│───▶│ Change Analyzer │───▶│ Alert Manager   │  │
│  │ • 实时解析       │    │ • 变更分类       │    │ • 邮件告警       │  │
│  │ • 过滤处理       │    │ • 数据对比       │    │ • Webhook       │  │
│  │ • 断点续传       │    │ • 规则匹配       │    │ • 批量通知       │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                │                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ Change Storage  │◀───│ Statistics      │───▶│ Web Dashboard   │  │
│  │ • SQLite/MySQL  │    │ • 实时统计       │    │ • 实时监控       │  │
│  │ • 历史记录       │    │ • 趋势分析       │    │ • 历史查询       │  │
│  │ • 索引优化       │    │ • 热点检测       │    │ • 报表生成       │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
```bash
- MySQL 5.7+ 或 8.0+
- Python 3.7+
- 磁盘空间: 5GB+ (用于Binary Log和变更数据存储)
- 内存: 2GB+
```

### 一键安装
```bash
# 1. 下载项目
git clone https://github.com/your-repo/mysql-change-monitor.git
cd mysql-change-monitor

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 配置MySQL (需要root权限)
sudo ./scripts/setup_mysql.sh

# 4. 配置监控目标
cp config/monitor.conf.example config/monitor.conf
vim config/monitor.conf

# 5. 启动监控
python monitor.py
```

### MySQL配置详解

系统**完全基于MySQL Binary Log**，需要确保以下配置：

```ini
# MySQL配置文件 (/etc/mysql/mysql.conf.d/mysqld.cnf)

# 启用Binary Log
log-bin = mysql-bin

# 使用ROW格式（重要！）
binlog_format = ROW

# 设置唯一的server-id
server-id = 1

# 其他优化配置
expire_logs_days = 7
max_binlog_size = 1073741824
sync_binlog = 1
```

**为什么选择ROW格式？**
- **完整记录**: 记录每行数据的完整变更
- **精确监控**: 可以获取变更前后的具体数据
- **安全可靠**: 不受SQL语句复杂性影响
- **便于分析**: 易于解析和处理

## 🔧 配置说明

### 基础配置
```yaml
# config/monitor.conf
mysql:
  host: localhost
  port: 3306
  user: change_monitor
  password: "ChangeMonitor2024!"

# 精确指定监控目标
monitoring:
  mode: whitelist              # 白名单模式
  databases: 
    - production_db
    - user_db
  target_tables:
    - "production_db.users"     # 用户表
    - "production_db.orders"    # 订单表
    - "production_db.payments"  # 支付表
    - "user_db.profiles"        # 用户资料表

# Binary Log收集器配置
collectors:
  binary_log:
    enabled: true
    server_id: 100              # 唯一标识
    resume_stream: true         # 断点续传
    blocking: true              # 阻塞模式确保不丢失
```

### 告警配置
```yaml
alerts:
  # 关键表立即告警
  critical_tables:
    - users
    - orders
    - payments
  
  # 大批量操作阈值
  bulk_threshold: 1000
  
  # 邮件告警
  email:
    enabled: true
    smtp_server: smtp.company.com
    recipients:
      - admin@company.com
      - dba@company.com
```

## 📊 使用示例

### 命令行管理
```bash
# 查看当前监控配置
python scripts/table_manager.py list

# 添加监控表
python scripts/table_manager.py add "mydb.users"

# 批量添加表
echo "mydb.orders" > tables.txt
echo "mydb.products" >> tables.txt
python scripts/table_manager.py batch-add tables.txt

# 应用预设模板
python scripts/table_manager.py template ecommerce
```

### Python API
```python
from mysql_change_monitor import ChangeMonitor

# 创建监控实例
monitor = ChangeMonitor('config/monitor.conf')

# 启动监控
monitor.start()

# 查询变更记录
changes = monitor.get_changes(
    start_time='2024-01-01 00:00:00',
    end_time='2024-01-02 00:00:00',
    table='users',
    operation='UPDATE'
)

# 获取统计信息
stats = monitor.get_stats()
print(f"今日变更: {stats['total_changes']}")
```

### Web API
```bash
# 获取实时统计
curl http://localhost:8080/api/stats

# 查询变更记录
curl "http://localhost:8080/api/changes?table=users&limit=100"

# 获取告警信息
curl http://localhost:8080/api/alerts
```

## 🛡️ Binary Log 安全特性

### 权限最小化
监控用户仅需最小权限：
```sql
-- 必需权限
GRANT REPLICATION SLAVE ON *.* TO 'change_monitor'@'localhost';
GRANT REPLICATION CLIENT ON *.* TO 'change_monitor'@'localhost';
GRANT SELECT ON *.* TO 'change_monitor'@'localhost';
```

### 数据安全
- **只读监控**: 只读取Binary Log，不修改任何数据
- **加密传输**: 支持SSL连接
- **敏感数据脱敏**: 自动脱敏敏感字段
- **访问控制**: Web界面支持认证

### 故障恢复
- **断点续传**: 服务重启后从上次位置继续
- **错误重试**: 自动处理网络异常
- **数据完整性**: 确保不丢失任何变更记录

## 📈 性能优化

### Binary Log 优化
```ini
# 优化Binary Log性能
binlog_cache_size = 32768      # 事务缓存
sync_binlog = 1               # 安全性最高
expire_logs_days = 7          # 自动清理
max_binlog_size = 1GB         # 文件大小限制
```

### 监控优化
- **异步处理**: 多线程异步处理变更事件
- **批量存储**: 批量写入变更记录
- **索引优化**: 数据库索引优化查询性能
- **内存管理**: 合理的内存缓存策略

## 🔍 监控场景

### 数据安全审计
```python
# 监控敏感表的所有变更
target_tables = [
    "user_db.users",           # 用户信息
    "finance_db.accounts",     # 账户信息
    "finance_db.transactions", # 交易记录
]
```

### 业务数据分析
```python
# 分析业务操作频率
stats = monitor.get_stats(days=30)
print(f"订单创建: {stats['order_inserts']}")
print(f"用户更新: {stats['user_updates']}")
```

### 异常检测
```python
# 检测异常删除操作
if change['operation_type'] == 'DELETE' and change['rows_affected'] > 100:
    send_urgent_alert(change)
```

## 📞 技术支持

### Binary Log 相关问题
- **日志过大**: 调整 `expire_logs_days` 和 `max_binlog_size`
- **性能影响**: 优化 `binlog_cache_size` 和 `sync_binlog`
- **磁盘空间**: 监控Binary Log文件大小，及时清理

### 监控系统问题
- **连接中断**: 检查网络和MySQL连接
- **权限错误**: 确认监控用户权限
- **数据丢失**: 检查断点续传配置

### 获取帮助
- 📖 **文档**: 详细的使用说明和配置指南
- 💬 **社区**: GitHub Issues和讨论区
- 🛠️ **支持**: 专业的技术支持服务

---

## 🎯 为什么选择基于 Binary Log？

### 传统方案 vs Binary Log方案

| 特性 | 传统触发器方案 | 应用层监控 | **Binary Log方案** |
|------|----------------|------------|-------------------|
| 性能影响 | 高 | 中等 | **零影响** |
| 部署复杂度 | 高 | 中等 | **低** |
| 数据完整性 | 中等 | 低 | **完整** |
| 实时性 | 好 | 中等 | **毫秒级** |
| 维护成本 | 高 | 中等 | **低** |
| 业务侵入性 | 高 | 高 | **零侵入** |

**🏆 Binary Log方案的绝对优势：**
- ✅ **零业务影响**: 不需要修改应用代码
- ✅ **完整数据捕获**: 捕获所有变更包括管理工具操作
- ✅ **高可靠性**: MySQL原生机制，稳定可靠
- ✅ **易于部署**: 只需配置MySQL和启动监控程序
- ✅ **断点续传**: 天然支持故障恢复

**🎯 专注数据库变更监控，基于Binary Log的最佳实践！**