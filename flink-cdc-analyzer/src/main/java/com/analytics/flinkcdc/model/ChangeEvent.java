package com.analytics.flinkcdc.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.Serializable;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;

/**
 * CDC 变更事件数据模型
 * 
 * 表示数据库表中的一次变更操作，包含：
 * - 基础信息：数据库、表、操作类型
 * - 数据内容：变更前后的数据
 * - 元数据：时间戳、binlog位置等
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ChangeEvent implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    // 基础信息
    @JsonProperty("id")
    private String id;
    
    @JsonProperty("timestamp")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSXXX")
    private Instant timestamp;
    
    @JsonProperty("database")
    private String database;
    
    @JsonProperty("table")
    private String table;
    
    @JsonProperty("operation")
    private String operation;  // INSERT, UPDATE, DELETE
    
    // 数据内容
    @JsonProperty("before")
    private Map<String, Object> before;  // 变更前数据 (UPDATE/DELETE)
    
    @JsonProperty("after")
    private Map<String, Object> after;   // 变更后数据 (INSERT/UPDATE)
    
    @JsonProperty("primary_key")
    private Map<String, Object> primaryKey;  // 主键值
    
    // 元数据
    @JsonProperty("source")
    private String source;  // 数据源类型: mysql, postgresql, mongodb
    
    @JsonProperty("binlog_file")
    private String binlogFile;
    
    @JsonProperty("binlog_position")
    private Long binlogPosition;
    
    @JsonProperty("gtid")
    private String gtid;
    
    @JsonProperty("server_id")
    private Long serverId;
    
    @JsonProperty("thread_id")
    private Long threadId;
    
    // 处理信息
    @JsonProperty("processed_timestamp")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSXXX")
    private Instant processedTimestamp;
    
    @JsonProperty("processor_id")
    private String processorId;
    
    @JsonProperty("schema_version")
    private String schemaVersion;
    
    // 分析信息
    @JsonProperty("changes")
    private Map<String, ColumnChange> changes;  // 列级变更详情
    
    @JsonProperty("event_size")
    private Integer eventSize;  // 事件大小（字节）
    
    @JsonProperty("tags")
    private Map<String, String> tags;  // 自定义标签
    
    // 构造函数
    public ChangeEvent() {
        this.processedTimestamp = Instant.now();
    }
    
    public ChangeEvent(String database, String table, String operation) {
        this();
        this.database = database;
        this.table = table;
        this.operation = operation;
    }
    
    // Getter 和 Setter 方法
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public Instant getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }
    
    public String getDatabase() {
        return database;
    }
    
    public void setDatabase(String database) {
        this.database = database;
    }
    
    public String getTable() {
        return table;
    }
    
    public void setTable(String table) {
        this.table = table;
    }
    
    public String getOperation() {
        return operation;
    }
    
    public void setOperation(String operation) {
        this.operation = operation;
    }
    
    public Map<String, Object> getBefore() {
        return before;
    }
    
    public void setBefore(Map<String, Object> before) {
        this.before = before;
    }
    
    public Map<String, Object> getAfter() {
        return after;
    }
    
    public void setAfter(Map<String, Object> after) {
        this.after = after;
    }
    
    public Map<String, Object> getPrimaryKey() {
        return primaryKey;
    }
    
    public void setPrimaryKey(Map<String, Object> primaryKey) {
        this.primaryKey = primaryKey;
    }
    
    public String getSource() {
        return source;
    }
    
    public void setSource(String source) {
        this.source = source;
    }
    
    public String getBinlogFile() {
        return binlogFile;
    }
    
    public void setBinlogFile(String binlogFile) {
        this.binlogFile = binlogFile;
    }
    
    public Long getBinlogPosition() {
        return binlogPosition;
    }
    
    public void setBinlogPosition(Long binlogPosition) {
        this.binlogPosition = binlogPosition;
    }
    
    public String getGtid() {
        return gtid;
    }
    
    public void setGtid(String gtid) {
        this.gtid = gtid;
    }
    
    public Long getServerId() {
        return serverId;
    }
    
    public void setServerId(Long serverId) {
        this.serverId = serverId;
    }
    
    public Long getThreadId() {
        return threadId;
    }
    
    public void setThreadId(Long threadId) {
        this.threadId = threadId;
    }
    
    public Instant getProcessedTimestamp() {
        return processedTimestamp;
    }
    
    public void setProcessedTimestamp(Instant processedTimestamp) {
        this.processedTimestamp = processedTimestamp;
    }
    
    public String getProcessorId() {
        return processorId;
    }
    
    public void setProcessorId(String processorId) {
        this.processorId = processorId;
    }
    
    public String getSchemaVersion() {
        return schemaVersion;
    }
    
    public void setSchemaVersion(String schemaVersion) {
        this.schemaVersion = schemaVersion;
    }
    
    public Map<String, ColumnChange> getChanges() {
        return changes;
    }
    
    public void setChanges(Map<String, ColumnChange> changes) {
        this.changes = changes;
    }
    
    public Integer getEventSize() {
        return eventSize;
    }
    
    public void setEventSize(Integer eventSize) {
        this.eventSize = eventSize;
    }
    
    public Map<String, String> getTags() {
        return tags;
    }
    
    public void setTags(Map<String, String> tags) {
        this.tags = tags;
    }
    
    // 工具方法
    
    /**
     * 获取表的完整标识符
     */
    public String getTableKey() {
        return database + "." + table;
    }
    
    /**
     * 获取事件的唯一标识符
     */
    public String getEventKey() {
        return getTableKey() + ":" + operation + ":" + timestamp.toEpochMilli();
    }
    
    /**
     * 判断是否为INSERT操作
     */
    public boolean isInsert() {
        return "INSERT".equalsIgnoreCase(operation) || "c".equals(operation);
    }
    
    /**
     * 判断是否为UPDATE操作
     */
    public boolean isUpdate() {
        return "UPDATE".equalsIgnoreCase(operation) || "u".equals(operation);
    }
    
    /**
     * 判断是否为DELETE操作
     */
    public boolean isDelete() {
        return "DELETE".equalsIgnoreCase(operation) || "d".equals(operation);
    }
    
    /**
     * 获取有效的数据 (INSERT/UPDATE用after，DELETE用before)
     */
    public Map<String, Object> getEffectiveData() {
        if (isDelete()) {
            return before;
        } else {
            return after;
        }
    }
    
    /**
     * 获取主键值的字符串表示
     */
    public String getPrimaryKeyAsString() {
        if (primaryKey == null || primaryKey.isEmpty()) {
            return "";
        }
        
        if (primaryKey.size() == 1) {
            return String.valueOf(primaryKey.values().iterator().next());
        }
        
        return primaryKey.toString();
    }
    
    /**
     * 检查是否包含指定列的变更
     */
    public boolean hasColumnChange(String columnName) {
        return changes != null && changes.containsKey(columnName);
    }
    
    /**
     * 获取指定列的变更信息
     */
    public ColumnChange getColumnChange(String columnName) {
        return changes != null ? changes.get(columnName) : null;
    }
    
    /**
     * 添加标签
     */
    public void addTag(String key, String value) {
        if (tags == null) {
            tags = new java.util.HashMap<>();
        }
        tags.put(key, value);
    }
    
    /**
     * 获取标签值
     */
    public String getTag(String key) {
        return tags != null ? tags.get(key) : null;
    }
    
    // equals, hashCode, toString
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ChangeEvent that = (ChangeEvent) o;
        return Objects.equals(id, that.id) &&
               Objects.equals(timestamp, that.timestamp) &&
               Objects.equals(database, that.database) &&
               Objects.equals(table, that.table) &&
               Objects.equals(operation, that.operation) &&
               Objects.equals(binlogPosition, that.binlogPosition);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id, timestamp, database, table, operation, binlogPosition);
    }
    
    @Override
    public String toString() {
        return "ChangeEvent{" +
               "id='" + id + '\'' +
               ", timestamp=" + timestamp +
               ", database='" + database + '\'' +
               ", table='" + table + '\'' +
               ", operation='" + operation + '\'' +
               ", source='" + source + '\'' +
               ", binlogFile='" + binlogFile + '\'' +
               ", binlogPosition=" + binlogPosition +
               ", primaryKey=" + primaryKey +
               '}';
    }
    
    /**
     * 构建器模式
     */
    public static class Builder {
        private ChangeEvent event;
        
        public Builder() {
            this.event = new ChangeEvent();
        }
        
        public Builder id(String id) {
            event.setId(id);
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            event.setTimestamp(timestamp);
            return this;
        }
        
        public Builder database(String database) {
            event.setDatabase(database);
            return this;
        }
        
        public Builder table(String table) {
            event.setTable(table);
            return this;
        }
        
        public Builder operation(String operation) {
            event.setOperation(operation);
            return this;
        }
        
        public Builder before(Map<String, Object> before) {
            event.setBefore(before);
            return this;
        }
        
        public Builder after(Map<String, Object> after) {
            event.setAfter(after);
            return this;
        }
        
        public Builder primaryKey(Map<String, Object> primaryKey) {
            event.setPrimaryKey(primaryKey);
            return this;
        }
        
        public Builder source(String source) {
            event.setSource(source);
            return this;
        }
        
        public Builder binlogFile(String binlogFile) {
            event.setBinlogFile(binlogFile);
            return this;
        }
        
        public Builder binlogPosition(Long binlogPosition) {
            event.setBinlogPosition(binlogPosition);
            return this;
        }
        
        public Builder gtid(String gtid) {
            event.setGtid(gtid);
            return this;
        }
        
        public Builder serverId(Long serverId) {
            event.setServerId(serverId);
            return this;
        }
        
        public Builder threadId(Long threadId) {
            event.setThreadId(threadId);
            return this;
        }
        
        public Builder processorId(String processorId) {
            event.setProcessorId(processorId);
            return this;
        }
        
        public Builder schemaVersion(String schemaVersion) {
            event.setSchemaVersion(schemaVersion);
            return this;
        }
        
        public Builder changes(Map<String, ColumnChange> changes) {
            event.setChanges(changes);
            return this;
        }
        
        public Builder eventSize(Integer eventSize) {
            event.setEventSize(eventSize);
            return this;
        }
        
        public Builder tags(Map<String, String> tags) {
            event.setTags(tags);
            return this;
        }
        
        public Builder addTag(String key, String value) {
            event.addTag(key, value);
            return this;
        }
        
        public ChangeEvent build() {
            // 基础验证
            if (event.database == null || event.table == null || event.operation == null) {
                throw new IllegalArgumentException("Database, table, and operation are required");
            }
            
            // 设置默认值
            if (event.id == null) {
                event.id = java.util.UUID.randomUUID().toString();
            }
            
            if (event.timestamp == null) {
                event.timestamp = Instant.now();
            }
            
            return event;
        }
    }
    
    /**
     * 创建构建器
     */
    public static Builder builder() {
        return new Builder();
    }
    
    /**
     * 从现有事件创建构建器
     */
    public static Builder builder(ChangeEvent existingEvent) {
        Builder builder = new Builder();
        builder.event = new ChangeEvent();
        
        // 复制所有字段
        builder.event.id = existingEvent.id;
        builder.event.timestamp = existingEvent.timestamp;
        builder.event.database = existingEvent.database;
        builder.event.table = existingEvent.table;
        builder.event.operation = existingEvent.operation;
        builder.event.before = existingEvent.before;
        builder.event.after = existingEvent.after;
        builder.event.primaryKey = existingEvent.primaryKey;
        builder.event.source = existingEvent.source;
        builder.event.binlogFile = existingEvent.binlogFile;
        builder.event.binlogPosition = existingEvent.binlogPosition;
        builder.event.gtid = existingEvent.gtid;
        builder.event.serverId = existingEvent.serverId;
        builder.event.threadId = existingEvent.threadId;
        builder.event.processedTimestamp = existingEvent.processedTimestamp;
        builder.event.processorId = existingEvent.processorId;
        builder.event.schemaVersion = existingEvent.schemaVersion;
        builder.event.changes = existingEvent.changes;
        builder.event.eventSize = existingEvent.eventSize;
        builder.event.tags = existingEvent.tags;
        
        return builder;
    }
}

/**
 * 列变更信息
 */
class ColumnChange implements Serializable {
    private static final long serialVersionUID = 1L;
    
    @JsonProperty("column")
    private String column;
    
    @JsonProperty("old_value")
    private Object oldValue;
    
    @JsonProperty("new_value")
    private Object newValue;
    
    @JsonProperty("data_type")
    private String dataType;
    
    @JsonProperty("is_primary_key")
    private Boolean isPrimaryKey;
    
    @JsonProperty("is_sensitive")
    private Boolean isSensitive;
    
    // 构造函数
    public ColumnChange() {}
    
    public ColumnChange(String column, Object oldValue, Object newValue) {
        this.column = column;
        this.oldValue = oldValue;
        this.newValue = newValue;
    }
    
    // Getter 和 Setter
    public String getColumn() {
        return column;
    }
    
    public void setColumn(String column) {
        this.column = column;
    }
    
    public Object getOldValue() {
        return oldValue;
    }
    
    public void setOldValue(Object oldValue) {
        this.oldValue = oldValue;
    }
    
    public Object getNewValue() {
        return newValue;
    }
    
    public void setNewValue(Object newValue) {
        this.newValue = newValue;
    }
    
    public String getDataType() {
        return dataType;
    }
    
    public void setDataType(String dataType) {
        this.dataType = dataType;
    }
    
    public Boolean getIsPrimaryKey() {
        return isPrimaryKey;
    }
    
    public void setIsPrimaryKey(Boolean isPrimaryKey) {
        this.isPrimaryKey = isPrimaryKey;
    }
    
    public Boolean getIsSensitive() {
        return isSensitive;
    }
    
    public void setIsSensitive(Boolean isSensitive) {
        this.isSensitive = isSensitive;
    }
    
    // 工具方法
    public boolean hasChanged() {
        return !Objects.equals(oldValue, newValue);
    }
    
    @Override
    public String toString() {
        return "ColumnChange{" +
               "column='" + column + '\'' +
               ", oldValue=" + oldValue +
               ", newValue=" + newValue +
               ", dataType='" + dataType + '\'' +
               ", isPrimaryKey=" + isPrimaryKey +
               ", isSensitive=" + isSensitive +
               '}';
    }
}