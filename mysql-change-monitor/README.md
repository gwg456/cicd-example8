# 🔍 MySQL 数据库更改监控系统

## 📋 项目概述

这是一个专门监控MySQL数据库更改的轻量级解决方案，专注于：
- **数据变更监控**: 实时跟踪INSERT、UPDATE、DELETE操作
- **结构变更监控**: 监控DDL操作（CREATE、ALTER、DROP）
- **用户权限变更**: 跟踪用户权限的增删改
- **实时告警**: 重要变更的即时通知

## 🎯 核心功能

### 数据变更监控
- ✅ **INSERT监控**: 新数据插入跟踪
- ✅ **UPDATE监控**: 数据修改前后对比
- ✅ **DELETE监控**: 数据删除记录
- ✅ **批量操作**: 大批量数据变更检测

### 结构变更监控
- ✅ **表结构变更**: CREATE/ALTER/DROP TABLE
- ✅ **索引变更**: 索引的创建和删除
- ✅ **存储过程**: 存储过程和函数变更
- ✅ **视图变更**: 视图的创建和修改

### 权限变更监控
- ✅ **用户管理**: CREATE/DROP USER
- ✅ **权限授予**: GRANT操作
- ✅ **权限撤销**: REVOKE操作
- ✅ **角色变更**: 用户角色修改

## 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MySQL 数据库   │───▶│   变更收集器      │───▶│   变更分析器     │
│                 │    │                  │    │                 │
│ • Binary Log    │    │ • Binlog解析     │    │ • 变更分类       │
│ • General Log   │    │ • DDL监控        │    │ • 影响评估       │
│ • Performance   │    │ • 实时采集       │    │ • 风险判断       │
│   Schema        │    │ • 过滤处理       │    │ • 告警触发       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web 监控界面   │◀───│   变更存储       │───▶│   告警通知      │
│                 │    │                  │    │                 │
│ • 实时监控       │    │ • 变更历史       │    │ • 邮件告警       │
│ • 历史查询       │    │ • 统计分析       │    │ • 微信/钉钉     │
│ • 报表生成       │    │ • 数据保留       │    │ • 短信通知       │
│ • 规则配置       │    │ • 备份恢复       │    │ • Webhook       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 环境要求
```bash
- MySQL 5.7+ 或 8.0+
- Python 3.7+
- 磁盘空间: 5GB+ (用于日志存储)
- 内存: 2GB+
```

### 安装部署
```bash
# 1. 克隆项目
git clone https://github.com/your-repo/mysql-change-monitor.git
cd mysql-change-monitor

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置MySQL
sudo ./scripts/setup_mysql.sh

# 4. 启动监控
python monitor.py

# 5. 访问Web界面
http://localhost:8080
```

## 📁 项目结构

```
mysql-change-monitor/
├── 📄 README.md                    # 项目说明
├── 📄 requirements.txt             # Python依赖
├── 📄 monitor.py                   # 主程序入口
├── 📁 config/                      # 配置文件
│   ├── monitor.conf               # 主配置
│   └── tables.conf                # 监控表配置
├── 📁 src/                         # 源代码
│   ├── collectors/                # 数据收集器
│   │   ├── binlog_collector.py   # Binary Log收集器
│   │   └── ddl_collector.py      # DDL操作收集器
│   ├── analyzers/                 # 变更分析器
│   │   ├── change_analyzer.py    # 变更分析
│   │   └── impact_analyzer.py    # 影响分析
│   ├── storage/                   # 数据存储
│   │   └── change_storage.py     # 变更存储
│   ├── alerts/                    # 告警系统
│   │   ├── email_alert.py        # 邮件告警
│   │   └── webhook_alert.py      # Webhook告警
│   └── web/                       # Web界面
│       ├── app.py                # Flask应用
│       ├── templates/            # HTML模板
│       └── static/               # 静态资源
├── 📁 scripts/                     # 管理脚本
│   ├── setup_mysql.sh            # MySQL配置脚本
│   └── start_monitor.sh          # 启动脚本
└── 📁 docs/                        # 文档
    ├── install.md                # 安装指南
    ├── config.md                 # 配置说明
    └── api.md                    # API文档
```

## 🔧 配置说明

### 基础配置
```yaml
# config/monitor.conf
mysql:
  host: localhost
  port: 3306
  user: change_monitor
  password: "your_password"
  database: mysql

monitoring:
  # 监控的数据库列表
  databases: [production, staging]
  
  # 监控的表列表 (支持通配符)
  tables: ["users", "orders", "products*"]
  
  # 排除的表
  exclude_tables: ["logs", "temp_*"]

alerts:
  # 重要表变更立即告警
  critical_tables: [users, orders]
  
  # 大批量操作告警阈值
  bulk_threshold: 1000
  
  # 告警通道
  channels: [email, webhook]
```

### 监控规则
```json
{
  "rules": [
    {
      "name": "用户表变更",
      "table": "users",
      "operations": ["INSERT", "UPDATE", "DELETE"],
      "alert": true,
      "priority": "high"
    },
    {
      "name": "订单删除",
      "table": "orders",
      "operations": ["DELETE"],
      "alert": true,
      "priority": "critical"
    },
    {
      "name": "结构变更",
      "type": "DDL",
      "operations": ["CREATE", "ALTER", "DROP"],
      "alert": true,
      "priority": "high"
    }
  ]
}
```

## 📊 监控界面

### 实时监控面板
- **变更统计**: 实时显示各类变更数量
- **活跃表格**: 最近变更最频繁的表
- **操作分布**: INSERT/UPDATE/DELETE比例
- **时间趋势**: 变更频率时间分布图

### 变更历史查询
- **时间范围**: 灵活的时间段筛选
- **表过滤**: 按表名筛选变更记录
- **操作类型**: 按操作类型筛选
- **用户过滤**: 按执行用户筛选

### 告警管理
- **告警规则**: 自定义告警条件
- **告警历史**: 查看历史告警记录
- **通知设置**: 配置告警接收方式
- **静默设置**: 临时关闭特定告警

## 🔔 告警功能

### 告警类型
1. **数据变更告警**
   - 重要表的数据修改
   - 大批量数据操作
   - 敏感字段变更

2. **结构变更告警**
   - 表结构修改
   - 索引变更
   - 权限变更

3. **异常操作告警**
   - 非工作时间操作
   - 异常用户操作
   - 可疑操作模式

### 告警通道
- **📧 邮件通知**: 详细的变更报告
- **📱 即时消息**: 微信/钉钉快速通知
- **📞 短信告警**: 紧急情况短信通知
- **🌐 Webhook**: 自定义API回调

## 📈 使用示例

### 基本使用
```python
from mysql_change_monitor import ChangeMonitor

# 创建监控实例
monitor = ChangeMonitor(config_file='config/monitor.conf')

# 启动监控
monitor.start()

# 查询变更记录
changes = monitor.get_changes(
    start_time='2024-01-01 00:00:00',
    end_time='2024-01-02 00:00:00',
    table='users'
)

# 获取实时统计
stats = monitor.get_stats()
print(f"今日变更: {stats['today_changes']}")
```

### Web API调用
```bash
# 获取变更统计
curl http://localhost:8080/api/stats

# 查询变更记录
curl "http://localhost:8080/api/changes?table=users&limit=100"

# 获取告警信息
curl http://localhost:8080/api/alerts
```

## 🛡️ 安全特性

### 数据保护
- **最小权限**: 监控用户仅有必要的读取权限
- **加密存储**: 敏感配置信息加密存储
- **访问控制**: Web界面登录认证
- **数据脱敏**: 敏感数据自动脱敏显示

### 完整性保障
- **变更校验**: 确保监控数据完整性
- **断点续传**: 服务重启后自动恢复监控
- **故障恢复**: 自动处理连接异常
- **数据备份**: 定期备份监控数据

## 🚀 高级功能

### 智能分析
- **变更趋势**: 分析数据变更趋势
- **异常检测**: 识别异常变更模式
- **影响评估**: 评估变更对系统的影响
- **性能影响**: 分析变更对性能的影响

### 集成扩展
- **Grafana集成**: 可视化监控面板
- **Prometheus**: 监控指标导出
- **ELK集成**: 日志分析和搜索
- **API接口**: 丰富的RESTful API

## 📞 技术支持

- **在线文档**: 详细的使用说明和API文档
- **示例代码**: 丰富的配置和使用示例
- **社区支持**: GitHub Issues和讨论区
- **技术咨询**: 专业的技术支持服务

---

🎯 **专注数据库变更监控，让每一个变更都在掌控之中！**