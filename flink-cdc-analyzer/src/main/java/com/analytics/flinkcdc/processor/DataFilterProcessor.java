package com.analytics.flinkcdc.processor;

import com.analytics.flinkcdc.model.ChangeEvent;
import com.analytics.flinkcdc.model.ColumnChange;
import com.analytics.flinkcdc.model.TableConfig;
import com.analytics.flinkcdc.util.JsonUtil;

import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.util.Collector;
import org.apache.flink.util.OutputTag;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

/**
 * CDC 数据过滤和解析处理器
 * 
 * 功能特性:
 * 1. 解析 Debezium CDC 消息
 * 2. 过滤目标表的变更事件
 * 3. 提取和转换数据内容
 * 4. 生成标准化的 ChangeEvent 对象
 * 5. 支持列级过滤和敏感数据处理
 */
public class DataFilterProcessor extends ProcessFunction<String, ChangeEvent> {
    
    private static final Logger LOG = LoggerFactory.getLogger(DataFilterProcessor.class);
    
    // 侧输出标签，用于处理不同类型的事件
    public static final OutputTag<String> FILTERED_EVENTS_TAG = new OutputTag<String>("filtered-events") {};
    public static final OutputTag<String> ERROR_EVENTS_TAG = new OutputTag<String>("error-events") {};
    public static final OutputTag<ChangeEvent> SCHEMA_CHANGE_TAG = new OutputTag<ChangeEvent>("schema-changes") {};
    
    private final TableConfig tableConfig;
    private final String processorId;
    
    // 统计计数器
    private transient long processedCount = 0;
    private transient long filteredCount = 0;
    private transient long errorCount = 0;
    
    public DataFilterProcessor(TableConfig tableConfig) {
        this.tableConfig = tableConfig;
        this.processorId = UUID.randomUUID().toString();
        LOG.info("初始化 DataFilterProcessor, processorId: {}", processorId);
    }
    
    @Override
    public void processElement(String value, Context ctx, Collector<ChangeEvent> out) throws Exception {
        processedCount++;
        
        try {
            // 解析 Debezium JSON 消息
            JsonNode jsonNode = JsonUtil.parseJson(value);
            
            if (jsonNode == null || !jsonNode.isObject()) {
                handleError("无效的JSON消息", value, ctx);
                return;
            }
            
            // 检查消息类型
            if (isSchemaChangeEvent(jsonNode)) {
                handleSchemaChange(jsonNode, ctx);
                return;
            }
            
            if (!isDataChangeEvent(jsonNode)) {
                handleFilteredEvent("非数据变更事件", value, ctx);
                return;
            }
            
            // 提取表信息
            String database = extractDatabase(jsonNode);
            String table = extractTable(jsonNode);
            String operation = extractOperation(jsonNode);
            
            if (database == null || table == null || operation == null) {
                handleError("缺少必要字段: database, table, operation", value, ctx);
                return;
            }
            
            // 检查是否为目标表
            if (!isTargetTable(database, table)) {
                handleFilteredEvent("非目标表: " + database + "." + table, value, ctx);
                return;
            }
            
            // 检查操作类型是否需要监控
            if (!isTargetOperation(database, table, operation)) {
                handleFilteredEvent("非监控操作: " + operation, value, ctx);
                return;
            }
            
            // 解析并生成 ChangeEvent
            ChangeEvent changeEvent = parseChangeEvent(jsonNode, database, table, operation);
            
            if (changeEvent != null) {
                // 应用列级过滤
                applyColumnFiltering(changeEvent, database, table);
                
                // 设置处理信息
                changeEvent.setProcessorId(processorId);
                changeEvent.setProcessedTimestamp(Instant.now());
                
                // 添加标签
                addEventTags(changeEvent);
                
                // 输出事件
                out.collect(changeEvent);
                
                // 定期输出统计信息
                if (processedCount % 10000 == 0) {
                    LOG.info("处理统计 - 总数: {}, 过滤: {}, 错误: {}", 
                            processedCount, filteredCount, errorCount);
                }
            }
            
        } catch (Exception e) {
            errorCount++;
            LOG.error("处理事件失败: {}", e.getMessage(), e);
            handleError("处理异常: " + e.getMessage(), value, ctx);
        }
    }
    
    /**
     * 判断是否为模式变更事件
     */
    private boolean isSchemaChangeEvent(JsonNode jsonNode) {
        JsonNode source = jsonNode.path("source");
        return source.has("snapshot") && "schema".equals(source.path("snapshot").asText());
    }
    
    /**
     * 判断是否为数据变更事件
     */
    private boolean isDataChangeEvent(JsonNode jsonNode) {
        return jsonNode.has("op") && jsonNode.has("source");
    }
    
    /**
     * 提取数据库名
     */
    private String extractDatabase(JsonNode jsonNode) {
        JsonNode source = jsonNode.path("source");
        return source.path("db").asText(null);
    }
    
    /**
     * 提取表名
     */
    private String extractTable(JsonNode jsonNode) {
        JsonNode source = jsonNode.path("source");
        return source.path("table").asText(null);
    }
    
    /**
     * 提取操作类型
     */
    private String extractOperation(JsonNode jsonNode) {
        String op = jsonNode.path("op").asText(null);
        if (op == null) return null;
        
        switch (op.toLowerCase()) {
            case "c": return "INSERT";
            case "u": return "UPDATE";
            case "d": return "DELETE";
            case "r": return "READ";  // 初始快照读取
            default: return op.toUpperCase();
        }
    }
    
    /**
     * 检查是否为目标表
     */
    private boolean isTargetTable(String database, String table) {
        return tableConfig.getTables().stream()
                .anyMatch(t -> t.getDatabase().equals(database) && t.getTable().equals(table));
    }
    
    /**
     * 检查是否为目标操作
     */
    private boolean isTargetOperation(String database, String table, String operation) {
        return tableConfig.getTables().stream()
                .filter(t -> t.getDatabase().equals(database) && t.getTable().equals(table))
                .findFirst()
                .map(t -> t.getOperations().contains(operation))
                .orElse(false);
    }
    
    /**
     * 解析变更事件
     */
    private ChangeEvent parseChangeEvent(JsonNode jsonNode, String database, String table, String operation) {
        try {
            ChangeEvent.Builder builder = ChangeEvent.builder()
                    .database(database)
                    .table(table)
                    .operation(operation)
                    .source("mysql");
            
            // 提取时间戳
            JsonNode source = jsonNode.path("source");
            if (source.has("ts_ms")) {
                long timestamp = source.path("ts_ms").asLong();
                builder.timestamp(Instant.ofEpochMilli(timestamp));
            }
            
            // 提取binlog信息
            if (source.has("file")) {
                builder.binlogFile(source.path("file").asText());
            }
            if (source.has("pos")) {
                builder.binlogPosition(source.path("pos").asLong());
            }
            if (source.has("gtid")) {
                builder.gtid(source.path("gtid").asText());
            }
            if (source.has("server_id")) {
                builder.serverId(source.path("server_id").asLong());
            }
            if (source.has("thread")) {
                builder.threadId(source.path("thread").asLong());
            }
            
            // 提取数据内容
            Map<String, Object> beforeData = null;
            Map<String, Object> afterData = null;
            
            if (jsonNode.has("before") && !jsonNode.path("before").isNull()) {
                beforeData = JsonUtil.toMap(jsonNode.path("before"));
            }
            
            if (jsonNode.has("after") && !jsonNode.path("after").isNull()) {
                afterData = JsonUtil.toMap(jsonNode.path("after"));
            }
            
            builder.before(beforeData).after(afterData);
            
            // 提取主键
            Map<String, Object> primaryKey = extractPrimaryKey(beforeData, afterData, database, table);
            builder.primaryKey(primaryKey);
            
            // 计算列级变更
            Map<String, ColumnChange> changes = calculateColumnChanges(beforeData, afterData, database, table);
            builder.changes(changes);
            
            // 计算事件大小
            int eventSize = calculateEventSize(jsonNode);
            builder.eventSize(eventSize);
            
            return builder.build();
            
        } catch (Exception e) {
            LOG.error("解析变更事件失败: {}", e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * 提取主键值
     */
    private Map<String, Object> extractPrimaryKey(Map<String, Object> beforeData, 
                                                 Map<String, Object> afterData, 
                                                 String database, String table) {
        
        // 获取表配置中的主键列
        Optional<TableConfig.Table> tableOpt = tableConfig.getTables().stream()
                .filter(t -> t.getDatabase().equals(database) && t.getTable().equals(table))
                .findFirst();
        
        if (!tableOpt.isPresent()) {
            return Collections.emptyMap();
        }
        
        List<String> primaryKeyColumns = tableOpt.get().getPrimaryKey();
        if (primaryKeyColumns == null || primaryKeyColumns.isEmpty()) {
            primaryKeyColumns = Arrays.asList("id");  // 默认主键
        }
        
        // 从数据中提取主键值
        Map<String, Object> data = afterData != null ? afterData : beforeData;
        if (data == null) {
            return Collections.emptyMap();
        }
        
        Map<String, Object> primaryKey = new HashMap<>();
        for (String column : primaryKeyColumns) {
            if (data.containsKey(column)) {
                primaryKey.put(column, data.get(column));
            }
        }
        
        return primaryKey;
    }
    
    /**
     * 计算列级变更
     */
    private Map<String, ColumnChange> calculateColumnChanges(Map<String, Object> beforeData,
                                                            Map<String, Object> afterData,
                                                            String database, String table) {
        if (beforeData == null && afterData == null) {
            return Collections.emptyMap();
        }
        
        Map<String, ColumnChange> changes = new HashMap<>();
        
        // 获取所有列名
        Set<String> allColumns = new HashSet<>();
        if (beforeData != null) allColumns.addAll(beforeData.keySet());
        if (afterData != null) allColumns.addAll(afterData.keySet());
        
        // 获取敏感列配置
        Set<String> sensitiveColumns = getSensitiveColumns(database, table);
        
        for (String column : allColumns) {
            Object oldValue = beforeData != null ? beforeData.get(column) : null;
            Object newValue = afterData != null ? afterData.get(column) : null;
            
            // 如果值发生变化，记录变更
            if (!Objects.equals(oldValue, newValue)) {
                ColumnChange change = new ColumnChange(column, oldValue, newValue);
                change.setIsSensitive(sensitiveColumns.contains(column));
                changes.put(column, change);
            }
        }
        
        return changes;
    }
    
    /**
     * 获取敏感列配置
     */
    private Set<String> getSensitiveColumns(String database, String table) {
        return tableConfig.getTables().stream()
                .filter(t -> t.getDatabase().equals(database) && t.getTable().equals(table))
                .findFirst()
                .map(t -> new HashSet<>(t.getSensitiveColumns()))
                .orElse(Collections.emptySet());
    }
    
    /**
     * 应用列级过滤
     */
    private void applyColumnFiltering(ChangeEvent changeEvent, String database, String table) {
        Optional<TableConfig.Table> tableOpt = tableConfig.getTables().stream()
                .filter(t -> t.getDatabase().equals(database) && t.getTable().equals(table))
                .findFirst();
        
        if (!tableOpt.isPresent()) {
            return;
        }
        
        List<String> trackColumns = tableOpt.get().getTrackColumns();
        if (trackColumns == null || trackColumns.isEmpty()) {
            return;  // 如果没有配置跟踪列，则保留所有列
        }
        
        // 过滤 before 数据
        if (changeEvent.getBefore() != null) {
            Map<String, Object> filteredBefore = changeEvent.getBefore().entrySet().stream()
                    .filter(entry -> trackColumns.contains(entry.getKey()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
            changeEvent.setBefore(filteredBefore);
        }
        
        // 过滤 after 数据
        if (changeEvent.getAfter() != null) {
            Map<String, Object> filteredAfter = changeEvent.getAfter().entrySet().stream()
                    .filter(entry -> trackColumns.contains(entry.getKey()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
            changeEvent.setAfter(filteredAfter);
        }
        
        // 过滤变更详情
        if (changeEvent.getChanges() != null) {
            Map<String, ColumnChange> filteredChanges = changeEvent.getChanges().entrySet().stream()
                    .filter(entry -> trackColumns.contains(entry.getKey()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
            changeEvent.setChanges(filteredChanges);
        }
    }
    
    /**
     * 添加事件标签
     */
    private void addEventTags(ChangeEvent changeEvent) {
        changeEvent.addTag("processor", "data-filter");
        changeEvent.addTag("version", "1.0.0");
        
        // 根据操作类型添加标签
        if (changeEvent.isInsert()) {
            changeEvent.addTag("operation_type", "create");
        } else if (changeEvent.isUpdate()) {
            changeEvent.addTag("operation_type", "modify");
        } else if (changeEvent.isDelete()) {
            changeEvent.addTag("operation_type", "remove");
        }
        
        // 添加表相关标签
        changeEvent.addTag("table_key", changeEvent.getTableKey());
        
        // 如果有敏感数据变更，添加标签
        if (changeEvent.getChanges() != null) {
            boolean hasSensitiveChange = changeEvent.getChanges().values().stream()
                    .anyMatch(change -> Boolean.TRUE.equals(change.getIsSensitive()));
            if (hasSensitiveChange) {
                changeEvent.addTag("has_sensitive_data", "true");
            }
        }
    }
    
    /**
     * 计算事件大小
     */
    private int calculateEventSize(JsonNode jsonNode) {
        try {
            return JsonUtil.toJson(jsonNode).getBytes("UTF-8").length;
        } catch (Exception e) {
            return 0;
        }
    }
    
    /**
     * 处理模式变更事件
     */
    private void handleSchemaChange(JsonNode jsonNode, Context ctx) {
        try {
            // 创建模式变更事件
            ChangeEvent schemaEvent = ChangeEvent.builder()
                    .database(extractDatabase(jsonNode))
                    .table(extractTable(jsonNode))
                    .operation("SCHEMA_CHANGE")
                    .source("mysql")
                    .processorId(processorId)
                    .addTag("event_type", "schema_change")
                    .build();
            
            ctx.output(SCHEMA_CHANGE_TAG, schemaEvent);
            LOG.debug("处理模式变更事件: {}.{}", schemaEvent.getDatabase(), schemaEvent.getTable());
        } catch (Exception e) {
            LOG.warn("处理模式变更事件失败: {}", e.getMessage());
        }
    }
    
    /**
     * 处理被过滤的事件
     */
    private void handleFilteredEvent(String reason, String event, Context ctx) {
        filteredCount++;
        
        // 创建过滤事件信息
        Map<String, Object> filteredInfo = new HashMap<>();
        filteredInfo.put("reason", reason);
        filteredInfo.put("timestamp", System.currentTimeMillis());
        filteredInfo.put("processor_id", processorId);
        filteredInfo.put("event", event);
        
        ctx.output(FILTERED_EVENTS_TAG, JsonUtil.toJson(filteredInfo));
        
        LOG.debug("事件被过滤: {}", reason);
    }
    
    /**
     * 处理错误事件
     */
    private void handleError(String reason, String event, Context ctx) {
        errorCount++;
        
        // 创建错误事件信息
        Map<String, Object> errorInfo = new HashMap<>();
        errorInfo.put("error", reason);
        errorInfo.put("timestamp", System.currentTimeMillis());
        errorInfo.put("processor_id", processorId);
        errorInfo.put("event", event);
        
        ctx.output(ERROR_EVENTS_TAG, JsonUtil.toJson(errorInfo));
        
        LOG.warn("事件处理错误: {}", reason);
    }
    
    /**
     * 获取处理统计信息
     */
    public Map<String, Long> getProcessingStats() {
        Map<String, Long> stats = new HashMap<>();
        stats.put("processed_count", processedCount);
        stats.put("filtered_count", filteredCount);
        stats.put("error_count", errorCount);
        stats.put("success_count", processedCount - filteredCount - errorCount);
        return stats;
    }
    
    /**
     * 重置统计计数器
     */
    public void resetStats() {
        processedCount = 0;
        filteredCount = 0;
        errorCount = 0;
    }
}