package com.analytics.flinkcdc.job;

import com.analytics.flinkcdc.model.ChangeEvent;
import com.analytics.flinkcdc.model.TableConfig;
import com.analytics.flinkcdc.processor.DataFilterProcessor;
import com.analytics.flinkcdc.processor.DataTransformProcessor;
import com.analytics.flinkcdc.sink.KafkaSink;
import com.analytics.flinkcdc.sink.ElasticsearchSink;
import com.analytics.flinkcdc.sink.MysqlSink;
import com.analytics.flinkcdc.util.ConfigUtil;
import com.analytics.flinkcdc.util.JsonUtil;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.CheckpointingMode;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import com.ververica.cdc.connectors.mysql.source.MySqlSource;
import com.ververica.cdc.connectors.mysql.table.StartupOptions;
import com.ververica.cdc.debezium.JsonDebeziumDeserializationSchema;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * MySQL CDC 数据变更捕获作业
 * 
 * 功能特性:
 * 1. 实时捕获MySQL数据变更
 * 2. 过滤和转换数据
 * 3. 输出到多个目标系统
 * 4. 支持精确一次语义
 * 5. 提供监控和告警
 */
public class MysqlCdcJob {
    
    private static final Logger LOG = LoggerFactory.getLogger(MysqlCdcJob.class);
    
    public static void main(String[] args) throws Exception {
        
        // 解析命令行参数
        ParameterTool parameterTool = ParameterTool.fromArgs(args);
        String configFile = parameterTool.get("config-file", "conf/application.yaml");
        
        LOG.info("启动 MySQL CDC Job，配置文件: {}", configFile);
        
        // 加载配置
        Map<String, Object> config = ConfigUtil.loadConfig(configFile);
        
        // 创建执行环境
        StreamExecutionEnvironment env = createExecutionEnvironment(config);
        
        // 构建数据流
        buildDataPipeline(env, config);
        
        // 执行作业
        env.execute("MySQL CDC Real-time Analytics Job");
    }
    
    /**
     * 创建流处理执行环境
     */
    private static StreamExecutionEnvironment createExecutionEnvironment(Map<String, Object> config) {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // 获取Flink配置
        Map<String, Object> flinkConfig = ConfigUtil.getMapValue(config, "flink.cluster");
        
        // 设置并行度
        int parallelism = ConfigUtil.getIntValue(flinkConfig, "parallelism", 4);
        env.setParallelism(parallelism);
        
        // 启用检查点
        int checkpointInterval = ConfigUtil.getIntValue(flinkConfig, "checkpoint_interval", 5000);
        env.enableCheckpointing(checkpointInterval);
        
        // 设置检查点模式
        String checkpointMode = ConfigUtil.getStringValue(flinkConfig, "checkpoint_mode", "EXACTLY_ONCE");
        env.getCheckpointConfig().setCheckpointingMode(
            "EXACTLY_ONCE".equals(checkpointMode) ? 
                CheckpointingMode.EXACTLY_ONCE : CheckpointingMode.AT_LEAST_ONCE
        );
        
        // 设置检查点超时时间
        env.getCheckpointConfig().setCheckpointTimeout(60000); // 60秒
        
        // 设置检查点之间的最小间隔
        env.getCheckpointConfig().setMinPauseBetweenCheckpoints(500);
        
        // 设置并发检查点数量
        env.getCheckpointConfig().setMaxConcurrentCheckpoints(1);
        
        // 启用不对齐检查点
        env.getCheckpointConfig().enableUnalignedCheckpoints(true);
        
        LOG.info("Flink执行环境配置完成: parallelism={}, checkpointInterval={}", 
                parallelism, checkpointInterval);
        
        return env;
    }
    
    /**
     * 构建数据处理管道
     */
    private static void buildDataPipeline(StreamExecutionEnvironment env, Map<String, Object> config) {
        
        // 1. 创建MySQL CDC Source
        MySqlSource<String> mysqlSource = createMysqlCdcSource(config);
        
        // 2. 添加水印策略
        WatermarkStrategy<String> watermarkStrategy = WatermarkStrategy
            .<String>forBoundedOutOfOrderness(Duration.ofSeconds(10))
            .withIdleness(Duration.ofSeconds(30));
        
        // 3. 创建数据流
        DataStream<String> sourceStream = env
            .fromSource(mysqlSource, watermarkStrategy, "MySQL CDC Source")
            .uid("mysql-cdc-source");
        
        // 4. 加载表配置
        TableConfig tableConfig = ConfigUtil.loadTableConfig(config);
        
        // 5. 数据过滤和解析
        DataStream<ChangeEvent> changeStream = sourceStream
            .process(new DataFilterProcessor(tableConfig))
            .name("Data Filter and Parse")
            .uid("data-filter");
        
        // 6. 数据转换和丰富
        DataStream<ChangeEvent> transformedStream = changeStream
            .process(new DataTransformProcessor(tableConfig))
            .name("Data Transform")
            .uid("data-transform");
        
        // 7. 分支输出到不同的Sink
        setupSinks(transformedStream, config);
        
        // 8. 实时统计
        setupRealTimeAnalytics(transformedStream, config);
        
        LOG.info("数据处理管道构建完成");
    }
    
    /**
     * 创建MySQL CDC Source
     */
    private static MySqlSource<String> createMysqlCdcSource(Map<String, Object> config) {
        Map<String, Object> mysqlConfig = ConfigUtil.getMapValue(config, "mysql_cdc");
        Map<String, Object> connection = ConfigUtil.getMapValue(mysqlConfig, "connection");
        Map<String, Object> cdcConfig = ConfigUtil.getMapValue(mysqlConfig, "cdc");
        
        String hostname = ConfigUtil.getStringValue(connection, "hostname");
        int port = ConfigUtil.getIntValue(connection, "port", 3306);
        String username = ConfigUtil.getStringValue(connection, "username");
        String password = ConfigUtil.getStringValue(connection, "password");
        
        String serverId = ConfigUtil.getStringValue(cdcConfig, "server_id", "5400-5404");
        String serverTimeZone = ConfigUtil.getStringValue(cdcConfig, "server_time_zone", "UTC");
        String startupMode = ConfigUtil.getStringValue(cdcConfig, "scan_startup_mode", "initial");
        
        // 构建表列表
        String[] tableList = buildTableList(mysqlConfig);
        String[] databaseList = buildDatabaseList(mysqlConfig);
        
        // 创建启动选项
        StartupOptions startupOptions = getStartupOptions(startupMode);
        
        MySqlSource<String> source = MySqlSource.<String>builder()
            .hostname(hostname)
            .port(port)
            .username(username)
            .password(password)
            .databaseList(databaseList)
            .tableList(tableList)
            .serverTimeZone(serverTimeZone)
            .serverId(serverId)
            .startupOptions(startupOptions)
            .deserializer(new JsonDebeziumDeserializationSchema())
            .build();
        
        LOG.info("MySQL CDC Source创建完成: {}:{}, tables: {}", hostname, port, String.join(",", tableList));
        
        return source;
    }
    
    /**
     * 构建表列表
     */
    private static String[] buildTableList(Map<String, Object> mysqlConfig) {
        return ConfigUtil.getListValue(mysqlConfig, "tables").stream()
            .map(table -> {
                Map<String, Object> tableMap = (Map<String, Object>) table;
                String database = ConfigUtil.getStringValue(tableMap, "database");
                String tableName = ConfigUtil.getStringValue(tableMap, "table");
                return database + "." + tableName;
            })
            .toArray(String[]::new);
    }
    
    /**
     * 构建数据库列表
     */
    private static String[] buildDatabaseList(Map<String, Object> mysqlConfig) {
        return ConfigUtil.getListValue(mysqlConfig, "tables").stream()
            .map(table -> {
                Map<String, Object> tableMap = (Map<String, Object>) table;
                return ConfigUtil.getStringValue(tableMap, "database");
            })
            .distinct()
            .toArray(String[]::new);
    }
    
    /**
     * 获取启动选项
     */
    private static StartupOptions getStartupOptions(String startupMode) {
        switch (startupMode.toLowerCase()) {
            case "initial":
                return StartupOptions.initial();
            case "earliest-offset":
                return StartupOptions.earliest();
            case "latest-offset":
                return StartupOptions.latest();
            default:
                LOG.warn("未知的启动模式: {}, 使用默认initial模式", startupMode);
                return StartupOptions.initial();
        }
    }
    
    /**
     * 设置数据输出Sink
     */
    private static void setupSinks(DataStream<ChangeEvent> stream, Map<String, Object> config) {
        Map<String, Object> sinksConfig = ConfigUtil.getMapValue(config, "sinks");
        
        // Kafka Sink
        Map<String, Object> kafkaConfig = ConfigUtil.getMapValue(sinksConfig, "kafka");
        if (ConfigUtil.getBooleanValue(kafkaConfig, "enabled", false)) {
            stream.addSink(new KafkaSink<>(kafkaConfig))
                  .name("Kafka Sink")
                  .uid("kafka-sink");
            LOG.info("Kafka Sink已启用");
        }
        
        // Elasticsearch Sink
        Map<String, Object> esConfig = ConfigUtil.getMapValue(sinksConfig, "elasticsearch");
        if (ConfigUtil.getBooleanValue(esConfig, "enabled", false)) {
            stream.addSink(new ElasticsearchSink<>(esConfig))
                  .name("Elasticsearch Sink")
                  .uid("elasticsearch-sink");
            LOG.info("Elasticsearch Sink已启用");
        }
        
        // MySQL Sink
        Map<String, Object> mysqlConfig = ConfigUtil.getMapValue(sinksConfig, "mysql");
        if (ConfigUtil.getBooleanValue(mysqlConfig, "enabled", false)) {
            stream.addSink(new MysqlSink<>(mysqlConfig))
                  .name("MySQL Sink")
                  .uid("mysql-sink");
            LOG.info("MySQL Sink已启用");
        }
    }
    
    /**
     * 设置实时分析
     */
    private static void setupRealTimeAnalytics(DataStream<ChangeEvent> stream, Map<String, Object> config) {
        
        // 表级统计 - 每分钟统计各表操作次数
        DataStream<String> tableStats = stream
            .keyBy(event -> event.getDatabase() + "." + event.getTable())
            .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
            .process(new TableStatsWindowProcessor())
            .name("Table Stats Window")
            .uid("table-stats-window");
        
        // 操作类型统计 - 每分钟统计各操作类型次数
        DataStream<String> operationStats = stream
            .keyBy(ChangeEvent::getOperation)
            .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
            .process(new OperationStatsWindowProcessor())
            .name("Operation Stats Window")
            .uid("operation-stats-window");
        
        // 数据库级统计 - 每5分钟统计各数据库活跃度
        DataStream<String> databaseStats = stream
            .keyBy(ChangeEvent::getDatabase)
            .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .process(new DatabaseStatsWindowProcessor())
            .name("Database Stats Window")
            .uid("database-stats-window");
        
        // 输出统计结果 (可以发送到监控系统)
        tableStats.print("TableStats").name("Table Stats Print");
        operationStats.print("OperationStats").name("Operation Stats Print");
        databaseStats.print("DatabaseStats").name("Database Stats Print");
        
        LOG.info("实时分析组件已启用");
    }
    
    /**
     * 表级统计窗口处理器
     */
    public static class TableStatsWindowProcessor 
            extends ProcessWindowFunction<ChangeEvent, String, String, TimeWindow> {
        
        @Override
        public void process(String key, Context context, 
                          Iterable<ChangeEvent> elements, Collector<String> out) {
            
            Map<String, Integer> operationCounts = new HashMap<>();
            int totalCount = 0;
            
            for (ChangeEvent event : elements) {
                String operation = event.getOperation();
                operationCounts.put(operation, operationCounts.getOrDefault(operation, 0) + 1);
                totalCount++;
            }
            
            Map<String, Object> stats = new HashMap<>();
            stats.put("table", key);
            stats.put("window_start", context.window().getStart());
            stats.put("window_end", context.window().getEnd());
            stats.put("total_count", totalCount);
            stats.put("operation_counts", operationCounts);
            stats.put("timestamp", System.currentTimeMillis());
            
            out.collect(JsonUtil.toJson(stats));
        }
    }
    
    /**
     * 操作类型统计窗口处理器
     */
    public static class OperationStatsWindowProcessor 
            extends ProcessWindowFunction<ChangeEvent, String, String, TimeWindow> {
        
        @Override
        public void process(String operation, Context context, 
                          Iterable<ChangeEvent> elements, Collector<String> out) {
            
            Map<String, Integer> tableCounts = new HashMap<>();
            int totalCount = 0;
            
            for (ChangeEvent event : elements) {
                String table = event.getDatabase() + "." + event.getTable();
                tableCounts.put(table, tableCounts.getOrDefault(table, 0) + 1);
                totalCount++;
            }
            
            Map<String, Object> stats = new HashMap<>();
            stats.put("operation", operation);
            stats.put("window_start", context.window().getStart());
            stats.put("window_end", context.window().getEnd());
            stats.put("total_count", totalCount);
            stats.put("table_counts", tableCounts);
            stats.put("timestamp", System.currentTimeMillis());
            
            out.collect(JsonUtil.toJson(stats));
        }
    }
    
    /**
     * 数据库级统计窗口处理器
     */
    public static class DatabaseStatsWindowProcessor 
            extends ProcessWindowFunction<ChangeEvent, String, String, TimeWindow> {
        
        @Override
        public void process(String database, Context context, 
                          Iterable<ChangeEvent> elements, Collector<String> out) {
            
            Map<String, Integer> tableCounts = new HashMap<>();
            Map<String, Integer> operationCounts = new HashMap<>();
            int totalCount = 0;
            
            for (ChangeEvent event : elements) {
                String table = event.getTable();
                String operation = event.getOperation();
                
                tableCounts.put(table, tableCounts.getOrDefault(table, 0) + 1);
                operationCounts.put(operation, operationCounts.getOrDefault(operation, 0) + 1);
                totalCount++;
            }
            
            Map<String, Object> stats = new HashMap<>();
            stats.put("database", database);
            stats.put("window_start", context.window().getStart());
            stats.put("window_end", context.window().getEnd());
            stats.put("total_count", totalCount);
            stats.put("table_counts", tableCounts);
            stats.put("operation_counts", operationCounts);
            stats.put("timestamp", System.currentTimeMillis());
            
            out.collect(JsonUtil.toJson(stats));
        }
    }
}