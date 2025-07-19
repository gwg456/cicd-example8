# 🔥 Flink CDC 数据变更分析解决方案

## 📋 项目概述

基于 **Apache Flink CDC** 的实时数据变更分析系统，专门用于监控和分析指定表的增删改操作，提供强大的流处理能力和精确一次的数据保证。

### 🎯 核心特性
- ✅ **实时 CDC 流处理**: 基于 Flink CDC 的低延迟数据捕获
- ✅ **精确一次保证**: Flink Checkpoint 机制确保数据一致性
- ✅ **指定表监控**: 灵活配置监控数据库和表
- ✅ **流式数据处理**: 支持复杂的流式计算和聚合
- ✅ **多种数据源**: 支持 MySQL、PostgreSQL、MongoDB 等
- ✅ **多种数据汇**: 支持 Kafka、Elasticsearch、ClickHouse 等

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据源层                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   MySQL 5.7+    │    │ PostgreSQL 11+  │    │ MongoDB 4+  │  │
│  │   (用户表)       │    │   (订单表)       │    │  (日志表)   │  │
│  │   (商品表)       │    │   (支付表)       │    │  (事件表)   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (CDC 实时捕获)
┌─────────────────────────────────────────────────────────────────┐
│                     Flink CDC 处理层                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   CDC Source    │───▶│  数据处理 Job    │───▶│   Sink 层   │  │
│  │ • MySQL CDC     │    │ • 数据过滤       │    │ • Kafka     │  │
│  │ • PG CDC        │    │ • 数据转换       │    │ • ES        │  │
│  │ • Mongo CDC     │    │ • 数据聚合       │    │ • MySQL     │  │
│  │ • 断点续传       │    │ • 状态管理       │    │ • ClickHouse│  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                               │                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │  Checkpoint     │    │   State Backend │    │ 监控告警     │  │
│  │ • 状态快照       │    │ • RocksDB       │    │ • Metrics   │  │
│  │ • 故障恢复       │    │ • Memory        │    │ • Alerts    │  │
│  │ • 一致性保证     │    │ • HDFS          │    │ • Dashboard │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (实时输出)
┌─────────────────────────────────────────────────────────────────┐
│                        数据消费层                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   实时 API      │    │   数据分析       │    │  业务应用   │  │
│  │ • REST API      │    │ • Grafana       │    │ • 同步任务  │  │
│  │ • GraphQL       │    │ • Kibana        │    │ • 告警系统  │  │
│  │ • WebSocket     │    │ • ClickHouse    │    │ • 数据湖   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
```bash
- Apache Flink 1.17+
- Java 11+
- Maven 3.6+
- MySQL 5.7+ (启用 binlog)
- Kafka 2.8+ (可选)
- Elasticsearch 7.15+ (可选)
```

### MySQL CDC 配置
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

# 启用GTID (推荐)
gtid_mode=ON
enforce_gtid_consistency=ON
```

### 快速部署
```bash
# 1. 克隆项目
git clone flink-cdc-analyzer
cd flink-cdc-analyzer

# 2. 编译项目
mvn clean package -DskipTests

# 3. 启动 Flink 集群
./bin/start-cluster.sh

# 4. 提交作业
./bin/flink run -d \
  target/flink-cdc-analyzer-1.0.jar \
  --config-file conf/application.yaml

# 5. 启动 API 服务
java -jar target/api-server-1.0.jar
```

## 📁 项目结构

```
flink-cdc-analyzer/
├── 📄 README.md                           # 项目说明
├── 📄 pom.xml                             # Maven配置
├── 📁 conf/                               # 配置文件
│   ├── application.yaml                   # 主配置文件
│   ├── flink-conf.yaml                    # Flink配置
│   └── log4j2.xml                         # 日志配置
├── 📁 src/main/java/                      # Java源代码
│   └── com/analytics/flinkcdc/
│       ├── 📁 source/                     # CDC数据源
│       │   ├── MysqlCdcSource.java        # MySQL CDC源
│       │   ├── PostgresCdcSource.java    # PostgreSQL CDC源
│       │   └── MongoCdcSource.java        # MongoDB CDC源
│       ├── 📁 processor/                  # 数据处理器
│       │   ├── DataFilterProcessor.java  # 数据过滤
│       │   ├── DataTransformProcessor.java # 数据转换
│       │   └── DataAggregateProcessor.java # 数据聚合
│       ├── 📁 sink/                       # 数据汇
│       │   ├── KafkaSink.java            # Kafka输出
│       │   ├── ElasticsearchSink.java    # ES输出
│       │   ├── MysqlSink.java            # MySQL输出
│       │   └── ClickHouseSink.java       # ClickHouse输出
│       ├── 📁 model/                      # 数据模型
│       │   ├── ChangeEvent.java          # 变更事件
│       │   ├── TableConfig.java          # 表配置
│       │   └── ProcessorConfig.java      # 处理器配置
│       ├── 📁 util/                       # 工具类
│       │   ├── ConfigUtil.java           # 配置工具
│       │   ├── JsonUtil.java             # JSON工具
│       │   └── TimeUtil.java             # 时间工具
│       └── 📁 job/                        # Flink作业
│           ├── MysqlCdcJob.java          # MySQL CDC作业
│           ├── MultiSourceCdcJob.java    # 多源CDC作业
│           └── RealTimeAnalyticsJob.java # 实时分析作业
├── 📁 src/main/resources/                 # 资源文件
│   ├── META-INF/services/                # SPI配置
│   └── sql/                              # SQL脚本
├── 📁 api-server/                         # API服务器
│   └── src/main/java/
│       └── com/analytics/api/
│           ├── ApiServer.java            # API服务主类
│           ├── controller/               # 控制器
│           ├── service/                  # 服务层
│           └── model/                    # 数据模型
├── 📁 web-ui/                            # Web界面
│   ├── src/                              # 前端源码
│   ├── public/                           # 静态资源
│   └── package.json                      # Node.js配置
└── 📁 docs/                              # 文档
    ├── deployment.md                     # 部署文档
    ├── configuration.md                  # 配置文档
    └── api.md                           # API文档
```

## 🔧 配置说明

### 主配置文件
```yaml
# conf/application.yaml
flink:
  # Flink 集群配置
  cluster:
    job_manager: "localhost:8081"
    parallelism: 4
    checkpoint_interval: 5000
    checkpoint_mode: "EXACTLY_ONCE"
    
  # 状态后端配置
  state_backend:
    type: "rocksdb"  # memory, filesystem, rocksdb
    checkpoint_dir: "hdfs://localhost:9000/flink/checkpoints"
    savepoint_dir: "hdfs://localhost:9000/flink/savepoints"

# MySQL CDC 配置
mysql_cdc:
  # 数据库连接
  connection:
    hostname: "localhost"
    port: 3306
    username: "flink_cdc"
    password: "FlinkCdc2024!"
    
  # CDC 配置
  cdc:
    server_id: "5400-5404"
    server_time_zone: "UTC"
    scan_startup_mode: "initial"  # initial, earliest-offset, latest-offset, specific-offset, timestamp
    
  # 监控表配置
  tables:
    - database: "ecommerce"
      table: "users"
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "username", "email", "phone", "status"]
      sensitive_columns: ["phone", "email"]
      primary_key: ["id"]
      
    - database: "ecommerce"
      table: "orders"
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "user_id", "amount", "status", "created_at"]
      primary_key: ["id"]
      
    - database: "ecommerce"
      table: "products"
      operations: ["INSERT", "UPDATE", "DELETE"]
      track_columns: ["id", "name", "price", "stock", "category_id"]
      primary_key: ["id"]

# PostgreSQL CDC 配置
postgres_cdc:
  connection:
    hostname: "localhost"
    port: 5432
    username: "postgres"
    password: "postgres"
    database: "ecommerce"
    
  cdc:
    slot_name: "flink_cdc_slot"
    decoding_plugin_name: "pgoutput"

# 数据处理配置
processing:
  # 窗口配置
  window:
    type: "tumbling"  # tumbling, sliding, session
    size: "1 minute"
    
  # 水印配置
  watermark:
    max_out_of_orderness: "10 seconds"
    idle_source_timeout: "30 seconds"
    
  # 过滤配置
  filter:
    enable_table_filter: true
    enable_operation_filter: true
    enable_column_filter: true

# 输出配置
sinks:
  # Kafka 输出
  kafka:
    enabled: true
    bootstrap_servers: "localhost:9092"
    topic: "mysql-cdc-events"
    
  # Elasticsearch 输出
  elasticsearch:
    enabled: true
    hosts: ["localhost:9200"]
    index: "mysql-cdc-{date}"
    
  # MySQL 输出
  mysql:
    enabled: true
    url: "jdbc:mysql://localhost:3306/cdc_analytics"
    table: "change_events"
    
  # ClickHouse 输出
  clickhouse:
    enabled: false
    url: "jdbc:clickhouse://localhost:8123/cdc_analytics"
    table: "change_events"

# 监控配置
monitoring:
  # Metrics 配置
  metrics:
    enabled: true
    reporters: ["prometheus"]
    
  # 告警配置
  alerts:
    enabled: true
    webhook_url: "http://localhost:8080/alerts"
```

## 🎯 核心功能

### 1. MySQL CDC 数据捕获
```java
// MySQL CDC Source 配置
public class MysqlCdcSource {
    
    public static SourceFunction<String> createSource(MysqlCdcConfig config) {
        return MySqlSource.<String>builder()
            .hostname(config.getHostname())
            .port(config.getPort())
            .databaseList(config.getDatabases())
            .tableList(config.getTables())
            .username(config.getUsername())
            .password(config.getPassword())
            .serverTimeZone(config.getServerTimeZone())
            .serverId(config.getServerId())
            .startupOptions(StartupOptions.initial())
            .deserializer(new JsonDebeziumDeserializationSchema())
            .build();
    }
}
```

### 2. 数据过滤和转换
```java
// 数据过滤处理器
public class DataFilterProcessor extends ProcessFunction<String, ChangeEvent> {
    
    private final TableConfig tableConfig;
    
    @Override
    public void processElement(String value, Context ctx, Collector<ChangeEvent> out) {
        try {
            // 解析Debezium消息
            JsonNode jsonNode = JsonUtil.parseJson(value);
            
            // 提取表信息
            String database = jsonNode.path("source").path("db").asText();
            String table = jsonNode.path("source").path("table").asText();
            
            // 检查是否为目标表
            if (isTargetTable(database, table)) {
                ChangeEvent event = parseChangeEvent(jsonNode);
                
                // 应用过滤规则
                if (shouldProcess(event)) {
                    out.collect(event);
                }
            }
        } catch (Exception e) {
            log.error("处理数据失败", e);
        }
    }
    
    private boolean isTargetTable(String database, String table) {
        return tableConfig.getTables().stream()
            .anyMatch(t -> t.getDatabase().equals(database) && 
                          t.getTable().equals(table));
    }
}
```

### 3. 实时数据聚合
```java
// 实时统计处理
public class RealTimeAnalyticsJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // 配置检查点
        env.enableCheckpointing(5000);
        env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        
        // MySQL CDC 源
        SourceFunction<String> mysqlSource = MysqlCdcSource.createSource(config);
        
        DataStream<ChangeEvent> changes = env
            .addSource(mysqlSource)
            .process(new DataFilterProcessor(tableConfig))
            .name("CDC Data Filter");
        
        // 实时统计 - 每分钟统计各表操作次数
        DataStream<TableStats> stats = changes
            .keyBy(event -> event.getDatabase() + "." + event.getTable())
            .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
            .aggregate(new OperationCountAggregator())
            .name("Real-time Table Stats");
        
        // 输出到多个Sink
        changes.addSink(new KafkaSink<>(kafkaConfig)).name("Kafka Sink");
        changes.addSink(new ElasticsearchSink<>(esConfig)).name("ES Sink");
        stats.addSink(new MysqlSink<>(mysqlConfig)).name("MySQL Stats Sink");
        
        env.execute("MySQL CDC Real-time Analytics");
    }
}
```

### 4. 多源 CDC 作业
```java
// 多数据源CDC作业
public class MultiSourceCdcJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // MySQL CDC 流
        DataStream<ChangeEvent> mysqlStream = env
            .addSource(MysqlCdcSource.createSource(mysqlConfig))
            .process(new DataFilterProcessor(mysqlTableConfig))
            .map(event -> {
                event.setSource("mysql");
                return event;
            });
        
        // PostgreSQL CDC 流
        DataStream<ChangeEvent> pgStream = env
            .addSource(PostgresCdcSource.createSource(pgConfig))
            .process(new DataFilterProcessor(pgTableConfig))
            .map(event -> {
                event.setSource("postgresql");
                return event;
            });
        
        // 合并多个流
        DataStream<ChangeEvent> unifiedStream = mysqlStream
            .union(pgStream)
            .keyBy(ChangeEvent::getTableKey)
            .process(new UnifiedChangeProcessor())
            .name("Unified Change Stream");
        
        // 统一输出
        unifiedStream.addSink(new KafkaSink<>(kafkaConfig));
        
        env.execute("Multi-Source CDC Job");
    }
}
```

## 📊 API 接口

### REST API 服务
```java
// API 控制器
@RestController
@RequestMapping("/api/v1")
public class ChangeEventController {
    
    @Autowired
    private ChangeEventService changeEventService;
    
    // 查询表变更记录
    @GetMapping("/tables/{database}/{table}/changes")
    public ResponseEntity<List<ChangeEvent>> getTableChanges(
            @PathVariable String database,
            @PathVariable String table,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        
        QueryCriteria criteria = QueryCriteria.builder()
            .database(database)
            .table(table)
            .limit(limit)
            .startTime(startTime)
            .endTime(endTime)
            .build();
            
        List<ChangeEvent> changes = changeEventService.queryChanges(criteria);
        return ResponseEntity.ok(changes);
    }
    
    // 获取表统计信息
    @GetMapping("/tables/{database}/{table}/stats")
    public ResponseEntity<TableStats> getTableStats(
            @PathVariable String database,
            @PathVariable String table,
            @RequestParam(defaultValue = "7") int days) {
        
        TableStats stats = changeEventService.getTableStats(database, table, days);
        return ResponseEntity.ok(stats);
    }
    
    // 实时变更流
    @GetMapping("/changes/stream")
    public SseEmitter getChangeStream() {
        return changeEventService.createChangeStream();
    }
}
```

### WebSocket 实时推送
```java
// WebSocket 配置
@Component
public class RealTimeChangeHandler {
    
    @EventListener
    public void handleChangeEvent(ChangeEvent event) {
        // 推送到WebSocket客户端
        messagingTemplate.convertAndSend("/topic/changes", event);
    }
    
    @MessageMapping("/subscribe/table")
    public void subscribeTable(@DestinationVariable String database,
                              @DestinationVariable String table,
                              Principal principal) {
        // 订阅特定表的变更
        subscriptionService.subscribe(principal.getName(), database, table);
    }
}
```

## 🔍 高级功能

### 1. 数据质量监控
```java
// 数据质量检查
public class DataQualityProcessor extends ProcessFunction<ChangeEvent, QualityAlert> {
    
    @Override
    public void processElement(ChangeEvent event, Context ctx, Collector<QualityAlert> out) {
        // 检查数据完整性
        if (hasNullPrimaryKey(event)) {
            out.collect(QualityAlert.builder()
                .type("NULL_PRIMARY_KEY")
                .table(event.getTableKey())
                .timestamp(event.getTimestamp())
                .build());
        }
        
        // 检查数据格式
        if (hasInvalidFormat(event)) {
            out.collect(QualityAlert.builder()
                .type("INVALID_FORMAT")
                .table(event.getTableKey())
                .details(getFormatErrors(event))
                .build());
        }
    }
}
```

### 2. 自定义序列化器
```java
// 自定义Debezium反序列化器
public class CustomDebeziumDeserializationSchema implements DebeziumDeserializationSchema<ChangeEvent> {
    
    @Override
    public void deserialize(SourceRecord record, Collector<ChangeEvent> out) throws Exception {
        // 解析Debezium记录
        Struct value = (Struct) record.value();
        Struct source = value.getStruct("source");
        
        // 构建变更事件
        ChangeEvent event = ChangeEvent.builder()
            .timestamp(Instant.ofEpochMilli((Long) source.get("ts_ms")))
            .database(source.getString("db"))
            .table(source.getString("table"))
            .operation(getOperation(value))
            .before(parseRowData(value.getStruct("before")))
            .after(parseRowData(value.getStruct("after")))
            .build();
            
        out.collect(event);
    }
    
    private String getOperation(Struct value) {
        String op = value.getString("op");
        switch (op) {
            case "c": return "INSERT";
            case "u": return "UPDATE";
            case "d": return "DELETE";
            default: return "UNKNOWN";
        }
    }
}
```

### 3. 状态管理和容错
```java
// 状态化处理器
public class StatefulChangeProcessor extends KeyedProcessFunction<String, ChangeEvent, ChangeEvent> {
    
    private ValueState<ChangeEvent> lastChangeState;
    
    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<ChangeEvent> descriptor = 
            new ValueStateDescriptor<>("lastChange", ChangeEvent.class);
        lastChangeState = getRuntimeContext().getState(descriptor);
    }
    
    @Override
    public void processElement(ChangeEvent event, Context ctx, Collector<ChangeEvent> out) throws Exception {
        ChangeEvent lastChange = lastChangeState.value();
        
        // 去重逻辑
        if (lastChange == null || !isDuplicate(lastChange, event)) {
            lastChangeState.update(event);
            out.collect(event);
        }
        
        // 设置定时器清理过期状态
        ctx.timerService().registerProcessingTimeTimer(
            ctx.timerService().currentProcessingTime() + 3600000); // 1小时后清理
    }
    
    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<ChangeEvent> out) {
        lastChangeState.clear();
    }
}
```

## 📈 监控和告警

### Prometheus 指标集成
```java
// 自定义指标
public class CdcMetrics {
    
    private static final Counter EVENTS_PROCESSED = Counter.build()
        .name("cdc_events_processed_total")
        .help("Total number of CDC events processed")
        .labelNames("database", "table", "operation")
        .register();
        
    private static final Histogram PROCESSING_LATENCY = Histogram.build()
        .name("cdc_processing_latency_seconds")
        .help("CDC event processing latency")
        .register();
    
    public static void recordEvent(String database, String table, String operation) {
        EVENTS_PROCESSED.labels(database, table, operation).inc();
    }
    
    public static void recordLatency(double latencySeconds) {
        PROCESSING_LATENCY.observe(latencySeconds);
    }
}
```

### 告警规则配置
```yaml
# 告警配置
alerts:
  rules:
    - name: "cdc_lag_high"
      condition: "cdc_lag_seconds > 300"
      severity: "warning"
      message: "CDC处理延迟超过5分钟"
      
    - name: "event_processing_error_rate_high"
      condition: "error_rate > 0.05"
      severity: "critical"
      message: "事件处理错误率超过5%"
      
    - name: "checkpoint_failure"
      condition: "checkpoint_failure_count > 3"
      severity: "critical"
      message: "Checkpoint连续失败超过3次"
```

## 💡 使用场景

### 1. 实时数据同步
```java
// 数据同步作业
public class DataSyncJob {
    public static void main(String[] args) throws Exception {
        env.addSource(mysqlCdcSource)
           .process(new DataTransformProcessor())
           .addSink(new ClickHouseSink());
    }
}
```

### 2. 实时业务监控
```java
// 业务指标计算
DataStream<BusinessMetric> metrics = changes
    .filter(event -> "orders".equals(event.getTable()))
    .keyBy(event -> event.getAfter().get("user_id"))
    .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
    .aggregate(new OrderMetricsAggregator());
```

### 3. 数据湖构建
```java
// 数据湖写入
changes.addSink(
    StreamingFileSink.forRowFormat(
        new Path("hdfs://localhost:9000/datalake/cdc/"),
        new SimpleStringEncoder<ChangeEvent>()
    ).build()
);
```

---

🚀 **基于 Flink CDC 的专业级数据变更分析解决方案，提供企业级的实时数据处理能力！**