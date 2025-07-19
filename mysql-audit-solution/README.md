# 🔍 MySQL社区版生产环境审计解决方案

## 📋 项目概述

基于 **MariaDB Audit Plugin** 的MySQL社区版审计解决方案，专门针对指定表进行精确审计监控。

### 🎯 核心特性
- ✅ **指定表审计**: 精确监控指定的敏感表
- ✅ **高性能**: 最小化对数据库性能的影响
- ✅ **实时监控**: 基于日志的实时审计事件检测
- ✅ **智能告警**: 异常操作自动告警
- ✅ **日志管理**: 自动轮转和归档

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        MySQL 数据库                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   用户表         │    │   订单表         │    │   支付表     │  │
│  │   users         │    │   orders        │    │   payments  │  │
│  │   (审计目标)     │    │   (审计目标)     │    │   (审计目标) │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                               │                                 │
│                    ┌─────────────────────┐                     │
│                    │ MariaDB Audit Plugin │                     │
│                    │ • 表级过滤          │                     │
│                    │ • 操作类型过滤       │                     │
│                    │ • 用户过滤          │                     │
│                    └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (写入审计日志)
┌─────────────────────────────────────────────────────────────────┐
│                     审计日志处理系统                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ 日志收集器       │───▶│ 事件分析器       │───▶│ 告警系统     │  │
│  │ • 实时监控       │    │ • 规则匹配       │    │ • 邮件告警   │  │
│  │ • 日志解析       │    │ • 异常检测       │    │ • 短信通知   │  │
│  │ • 格式转换       │    │ • 统计分析       │    │ • Webhook   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                               │                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ Web 控制台       │◀───│ 数据存储        │───▶│ 报表生成     │  │
│  │ • 实时监控       │    │ • 事件存储       │    │ • 统计报表   │  │
│  │ • 历史查询       │    │ • 索引优化       │    │ • 趋势分析   │  │
│  │ • 规则管理       │    │ • 数据归档       │    │ • 合规报告   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速部署

### 环境要求
```bash
- MySQL 5.7+ 或 8.0+
- Linux 系统 (CentOS/Ubuntu)
- Python 3.7+
- 磁盘空间: 10GB+ (用于审计日志存储)
- 内存: 4GB+
```

### 一键安装
```bash
# 1. 下载项目
git clone https://github.com/your-repo/mysql-audit-solution.git
cd mysql-audit-solution

# 2. 运行安装脚本
sudo ./scripts/install.sh

# 3. 配置审计目标
vim config/audit_tables.conf

# 4. 启动审计服务
sudo systemctl start mysql-audit
sudo systemctl enable mysql-audit
```

## 📁 项目结构

```
mysql-audit-solution/
├── 📄 README.md                    # 项目说明
├── 📄 requirements.txt             # Python依赖
├── 📁 config/                      # 配置文件
│   ├── audit_tables.conf          # 审计表配置
│   ├── mysql.conf                 # MySQL配置
│   └── alerts.conf                # 告警配置
├── 📁 scripts/                     # 安装脚本
│   ├── install.sh                 # 一键安装脚本
│   ├── setup_plugin.sh            # 插件安装
│   └── configure_audit.sh         # 审计配置
├── 📁 src/                         # 源代码
│   ├── audit_monitor.py           # 主监控程序
│   ├── log_parser.py              # 日志解析器
│   ├── rule_engine.py             # 规则引擎
│   ├── alert_manager.py           # 告警管理
│   └── web_dashboard.py           # Web控制台
├── 📁 plugins/                     # 插件文件
│   └── server_audit.so            # MariaDB审计插件
├── 📁 sql/                         # SQL脚本
│   ├── init_audit_db.sql          # 初始化审计数据库
│   └── audit_tables.sql           # 审计表结构
└── 📁 systemd/                     # 系统服务
    └── mysql-audit.service        # 系统服务配置
```

## 🔧 配置说明

### 审计目标配置
```yaml
# config/audit_tables.conf
audit_config:
  # 指定需要审计的表
  target_tables:
    - database: "production"
      table: "users"
      operations: ["INSERT", "UPDATE", "DELETE"]
      sensitive_fields: ["password", "email", "phone"]
      
    - database: "production" 
      table: "orders"
      operations: ["INSERT", "UPDATE", "DELETE"]
      alert_on_delete: true
      
    - database: "production"
      table: "payments"
      operations: ["INSERT", "UPDATE", "DELETE"] 
      alert_threshold: 100  # 批量操作告警阈值
      
    - database: "finance"
      table: "transactions"
      operations: ["INSERT", "UPDATE", "DELETE"]
      high_priority: true

  # 排除的表（避免审计系统表）
  exclude_tables:
    - "mysql.*"
    - "information_schema.*"
    - "performance_schema.*"
    - "sys.*"
    - "*.logs"
    - "*.cache"

  # 用户过滤
  audit_users:
    include: ["app_user", "admin_user"]
    exclude: ["backup_user", "monitor_user", "replication_user"]

  # 操作过滤
  operations:
    ddl: true      # 审计DDL操作
    dml: true      # 审计DML操作
    dcl: false     # 不审计权限操作
```

### MySQL插件配置
```ini
# my.cnf 中的审计配置
[mysqld]
# 加载审计插件
plugin-load-add=server_audit.so

# 基础配置
server_audit_logging=ON
server_audit_output_type=file
server_audit_file_path=/var/log/mysql/audit.log
server_audit_file_rotate_size=100000000  # 100MB轮转
server_audit_file_rotations=10

# 性能优化配置
server_audit_events=CONNECT,QUERY,TABLE
server_audit_syslog_priority=LOG_INFO

# 指定表审计 - 通过查询过滤实现
server_audit_incl_users=""  # 不在插件层过滤用户
server_audit_excl_users=backup_user,monitor_user,replication_user
```

## 🎯 核心功能

### 1. 指定表精确审计
- ✅ 支持跨数据库表监控
- ✅ 操作类型精确过滤
- ✅ 敏感字段特殊处理
- ✅ 实时告警触发

### 2. 智能日志分析
- ✅ 实时日志解析
- ✅ SQL语句分析
- ✅ 表名提取和匹配
- ✅ 异常操作检测

### 3. 高效告警系统
- ✅ 多级别告警策略
- ✅ 批量操作检测
- ✅ 异常时间检测
- ✅ 多渠道通知

### 4. 完整管理界面
- ✅ 实时监控面板
- ✅ 历史事件查询
- ✅ 统计报表生成
- ✅ 规则配置管理

## 📊 使用示例

### 启动监控
```bash
# 启动审计监控服务
sudo systemctl start mysql-audit

# 查看服务状态
sudo systemctl status mysql-audit

# 查看实时日志
tail -f /var/log/mysql-audit/monitor.log
```

### 配置新的审计表
```bash
# 使用配置工具
python scripts/table_manager.py add \
    --database production \
    --table user_profiles \
    --operations INSERT,UPDATE,DELETE \
    --alert-priority high

# 重新加载配置
sudo systemctl reload mysql-audit
```

### Web控制台访问
```bash
# 访问监控面板
http://localhost:8080/audit-dashboard

# API接口示例
curl http://localhost:8080/api/audit/events?table=users&limit=100
```

## 🛡️ 安全特性

### 权限最小化
- 审计用户仅有必要的读取权限
- 审计日志文件权限严格控制
- Web界面访问认证

### 数据保护
- 敏感字段自动脱敏
- 审计日志加密存储
- 网络传输SSL加密

### 完整性保障
- 审计日志完整性校验
- 防篡改机制
- 备份和恢复策略

## 📈 性能优化

### 插件层优化
```ini
# 减少不必要的审计事件
server_audit_events=QUERY,TABLE  # 不审计连接事件

# 用户过滤减少日志量
server_audit_excl_users=backup,monitor,readonly

# 日志文件优化
server_audit_file_rotate_size=50000000  # 50MB轮转
```

### 应用层优化
- 异步日志处理
- 批量数据库写入
- 内存缓存热点数据
- 索引优化查询性能

## 🔍 监控指标

### 关键指标
- 审计事件总数
- 各表操作频率
- 异常操作统计
- 系统性能影响

### 告警阈值
- 大批量操作: >1000行
- 删除操作: 任何DELETE
- 非工作时间: 22:00-06:00
- 异常用户: 非授权用户

## 💡 最佳实践

### 部署建议
1. **渐进式部署**: 先在测试环境验证
2. **性能测试**: 评估对生产环境的影响
3. **容量规划**: 预估日志存储空间需求
4. **监控报警**: 设置完善的监控体系

### 运维建议
1. **定期维护**: 日志轮转和清理
2. **性能监控**: 关注数据库性能指标
3. **规则调优**: 根据实际情况调整规则
4. **安全审查**: 定期检查审计配置

---

🎯 **专业级MySQL审计解决方案，确保数据安全合规！**