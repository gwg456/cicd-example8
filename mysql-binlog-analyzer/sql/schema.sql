-- =========================================
-- MySQL Binlog 数据分析系统 - 数据库表结构
-- =========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS binlog_analysis DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE binlog_analysis;

-- =========================================
-- 1. binlog变更记录表
-- =========================================
CREATE TABLE IF NOT EXISTS binlog_changes (
    id VARCHAR(36) NOT NULL PRIMARY KEY COMMENT '唯一标识符',
    timestamp DATETIME(6) NOT NULL COMMENT '变更时间',
    database_name VARCHAR(64) NOT NULL COMMENT '数据库名',
    table_name VARCHAR(64) NOT NULL COMMENT '表名',
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL COMMENT '操作类型',
    
    -- 主键信息
    primary_key JSON NOT NULL COMMENT '主键值(JSON格式)',
    
    -- 数据内容
    old_data JSON NULL COMMENT '变更前数据(JSON格式)',
    new_data JSON NULL COMMENT '变更后数据(JSON格式)',
    changes JSON NULL COMMENT '变更详情(JSON格式)',
    
    -- Binlog位置信息
    binlog_file VARCHAR(255) NULL COMMENT 'Binlog文件名',
    binlog_position BIGINT UNSIGNED NULL COMMENT 'Binlog位置',
    server_id INT UNSIGNED NULL COMMENT 'MySQL服务器ID',
    
    -- 处理信息
    processed_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '处理时间',
    parser_version VARCHAR(32) DEFAULT '1.0.0' COMMENT '解析器版本',
    
    -- 索引
    INDEX idx_timestamp (timestamp),
    INDEX idx_database_table (database_name, table_name),
    INDEX idx_operation (operation),
    INDEX idx_binlog_position (binlog_file, binlog_position),
    INDEX idx_processed_at (processed_at),
    
    -- 复合索引
    INDEX idx_table_time (database_name, table_name, timestamp),
    INDEX idx_operation_time (operation, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Binlog变更记录表'
PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 2. binlog位置信息表
-- =========================================
CREATE TABLE IF NOT EXISTS binlog_position (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT UNSIGNED NOT NULL COMMENT 'MySQL服务器ID',
    binlog_file VARCHAR(255) NOT NULL COMMENT '当前Binlog文件',
    binlog_position BIGINT UNSIGNED NOT NULL COMMENT '当前Binlog位置',
    gtid_set TEXT NULL COMMENT 'GTID集合',
    
    -- 时间信息
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    -- 状态信息
    status ENUM('active', 'paused', 'stopped') DEFAULT 'active' COMMENT '状态',
    description TEXT NULL COMMENT '描述信息',
    
    UNIQUE KEY uk_server_id (server_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Binlog位置管理表';

-- =========================================
-- 3. 统计信息表
-- =========================================
CREATE TABLE IF NOT EXISTS binlog_statistics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL COMMENT '统计日期',
    stat_hour TINYINT UNSIGNED NULL COMMENT '统计小时(0-23)',
    database_name VARCHAR(64) NOT NULL COMMENT '数据库名',
    table_name VARCHAR(64) NOT NULL COMMENT '表名',
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL COMMENT '操作类型',
    
    -- 统计数据
    count BIGINT UNSIGNED DEFAULT 0 COMMENT '操作次数',
    total_rows BIGINT UNSIGNED DEFAULT 0 COMMENT '影响行数',
    avg_size DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均数据大小(KB)',
    
    -- 时间信息
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    -- 唯一约束
    UNIQUE KEY uk_stats (stat_date, stat_hour, database_name, table_name, operation),
    
    -- 索引
    INDEX idx_stat_date (stat_date),
    INDEX idx_database_table (database_name, table_name),
    INDEX idx_operation (operation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Binlog统计信息表'
PARTITION BY RANGE (YEAR(stat_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 4. 表配置信息表
-- =========================================
CREATE TABLE IF NOT EXISTS table_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    database_name VARCHAR(64) NOT NULL COMMENT '数据库名',
    table_name VARCHAR(64) NOT NULL COMMENT '表名',
    
    -- 监控配置
    operations JSON NOT NULL COMMENT '监控的操作类型',
    track_columns JSON NULL COMMENT '跟踪的列',
    sensitive_columns JSON NULL COMMENT '敏感列',
    primary_key VARCHAR(64) DEFAULT 'id' COMMENT '主键列名',
    
    -- 状态配置
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    description TEXT NULL COMMENT '描述信息',
    
    -- 时间信息
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    UNIQUE KEY uk_database_table (database_name, table_name),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='表配置信息表';

-- =========================================
-- 5. 错误日志表
-- =========================================
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    error_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '错误时间',
    error_type ENUM('PARSE_ERROR', 'STORAGE_ERROR', 'CONNECTION_ERROR', 'UNKNOWN_ERROR') NOT NULL COMMENT '错误类型',
    
    -- 错误信息
    error_message TEXT NOT NULL COMMENT '错误消息',
    error_details JSON NULL COMMENT '错误详情',
    stack_trace TEXT NULL COMMENT '堆栈跟踪',
    
    -- 上下文信息
    binlog_file VARCHAR(255) NULL COMMENT '出错时的Binlog文件',
    binlog_position BIGINT UNSIGNED NULL COMMENT '出错时的Binlog位置',
    database_name VARCHAR(64) NULL COMMENT '相关数据库',
    table_name VARCHAR(64) NULL COMMENT '相关表名',
    
    -- 处理状态
    status ENUM('new', 'investigating', 'resolved', 'ignored') DEFAULT 'new' COMMENT '处理状态',
    resolved_at DATETIME(6) NULL COMMENT '解决时间',
    
    INDEX idx_error_time (error_time),
    INDEX idx_error_type (error_type),
    INDEX idx_status (status),
    INDEX idx_database_table (database_name, table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='错误日志表'
PARTITION BY RANGE (YEAR(error_time)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 6. 系统监控表
-- =========================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '指标时间',
    
    -- 性能指标
    events_per_second DECIMAL(10,2) DEFAULT 0.00 COMMENT '每秒事件数',
    binlog_lag_seconds INT UNSIGNED DEFAULT 0 COMMENT 'Binlog延迟秒数',
    queue_size INT UNSIGNED DEFAULT 0 COMMENT '队列大小',
    
    -- 系统指标  
    memory_usage_mb DECIMAL(10,2) DEFAULT 0.00 COMMENT '内存使用MB',
    memory_usage_percent DECIMAL(5,2) DEFAULT 0.00 COMMENT '内存使用百分比',
    cpu_usage_percent DECIMAL(5,2) DEFAULT 0.00 COMMENT 'CPU使用百分比',
    
    -- 错误指标
    error_count INT UNSIGNED DEFAULT 0 COMMENT '错误次数',
    error_rate DECIMAL(5,4) DEFAULT 0.0000 COMMENT '错误率',
    
    -- 连接指标
    active_connections INT UNSIGNED DEFAULT 0 COMMENT '活跃连接数',
    
    INDEX idx_metric_time (metric_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='系统监控指标表'
PARTITION BY RANGE (YEAR(metric_time)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 7. 用户查询历史表
-- =========================================
CREATE TABLE IF NOT EXISTS query_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    query_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '查询时间',
    
    -- 查询信息
    query_type ENUM('table_changes', 'operations', 'statistics', 'search') NOT NULL COMMENT '查询类型',
    query_params JSON NOT NULL COMMENT '查询参数',
    
    -- 结果信息
    result_count INT UNSIGNED DEFAULT 0 COMMENT '结果数量',
    execution_time_ms INT UNSIGNED DEFAULT 0 COMMENT '执行时间(毫秒)',
    
    -- 用户信息
    user_ip VARCHAR(45) NULL COMMENT '用户IP',
    user_agent TEXT NULL COMMENT '用户代理',
    
    INDEX idx_query_time (query_time),
    INDEX idx_query_type (query_type),
    INDEX idx_user_ip (user_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='用户查询历史表'
PARTITION BY RANGE (YEAR(query_time)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 8. 告警记录表
-- =========================================
CREATE TABLE IF NOT EXISTS alert_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '告警时间',
    
    -- 告警信息
    alert_type VARCHAR(64) NOT NULL COMMENT '告警类型',
    alert_level ENUM('info', 'warning', 'error', 'critical') NOT NULL COMMENT '告警级别',
    alert_message TEXT NOT NULL COMMENT '告警消息',
    
    -- 相关信息
    database_name VARCHAR(64) NULL COMMENT '相关数据库',
    table_name VARCHAR(64) NULL COMMENT '相关表名',
    metric_value DECIMAL(15,4) NULL COMMENT '指标值',
    threshold_value DECIMAL(15,4) NULL COMMENT '阈值',
    
    -- 处理状态
    status ENUM('new', 'acknowledged', 'resolved', 'suppressed') DEFAULT 'new' COMMENT '处理状态',
    acknowledged_at DATETIME(6) NULL COMMENT '确认时间',
    resolved_at DATETIME(6) NULL COMMENT '解决时间',
    
    -- 通知状态
    notification_sent BOOLEAN DEFAULT FALSE COMMENT '是否已发送通知',
    notification_channels JSON NULL COMMENT '通知渠道',
    
    INDEX idx_alert_time (alert_time),
    INDEX idx_alert_level (alert_level),
    INDEX idx_status (status),
    INDEX idx_database_table (database_name, table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='告警记录表'
PARTITION BY RANGE (YEAR(alert_time)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =========================================
-- 创建用户和权限
-- =========================================

-- 创建binlog读取用户
CREATE USER IF NOT EXISTS 'binlog_reader'@'%' IDENTIFIED BY 'BinlogReader2024!';
GRANT SELECT ON *.* TO 'binlog_reader'@'%';
GRANT REPLICATION SLAVE ON *.* TO 'binlog_reader'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'binlog_reader'@'%';

-- 创建存储用户
CREATE USER IF NOT EXISTS 'storage_user'@'%' IDENTIFIED BY 'StorageUser2024!';
GRANT ALL PRIVILEGES ON binlog_analysis.* TO 'storage_user'@'%';

-- 创建只读查询用户
CREATE USER IF NOT EXISTS 'query_user'@'%' IDENTIFIED BY 'QueryUser2024!';
GRANT SELECT ON binlog_analysis.* TO 'query_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- =========================================
-- 初始化数据
-- =========================================

-- 插入默认的binlog位置记录
INSERT IGNORE INTO binlog_position (server_id, binlog_file, binlog_position, status, description)
VALUES (1001, '', 4, 'active', '默认起始位置');

-- 插入默认表配置（示例）
INSERT IGNORE INTO table_configs (database_name, table_name, operations, track_columns, primary_key, description)
VALUES 
('ecommerce', 'users', '["INSERT", "UPDATE", "DELETE"]', '["id", "username", "email", "status"]', 'id', '用户表配置'),
('ecommerce', 'orders', '["INSERT", "UPDATE", "DELETE"]', '["id", "user_id", "amount", "status"]', 'id', '订单表配置'),
('ecommerce', 'products', '["INSERT", "UPDATE", "DELETE"]', '["id", "name", "price", "stock"]', 'id', '商品表配置');

-- =========================================
-- 创建视图（便于查询）
-- =========================================

-- 最近变更视图
CREATE OR REPLACE VIEW recent_changes AS
SELECT 
    id,
    timestamp,
    database_name,
    table_name,
    operation,
    primary_key,
    CASE 
        WHEN operation = 'INSERT' THEN new_data
        WHEN operation = 'DELETE' THEN old_data  
        ELSE JSON_OBJECT('old', old_data, 'new', new_data)
    END as data,
    binlog_file,
    binlog_position
FROM binlog_changes 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;

-- 每日统计视图
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    stat_date,
    database_name,
    table_name,
    operation,
    SUM(count) as total_count,
    AVG(avg_size) as avg_data_size
FROM binlog_statistics 
WHERE stat_hour IS NULL
GROUP BY stat_date, database_name, table_name, operation
ORDER BY stat_date DESC;

-- 表活跃度视图
CREATE OR REPLACE VIEW table_activity AS
SELECT 
    database_name,
    table_name,
    COUNT(*) as change_count,
    MAX(timestamp) as last_change,
    MIN(timestamp) as first_change,
    COUNT(DISTINCT DATE(timestamp)) as active_days
FROM binlog_changes 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY database_name, table_name
ORDER BY change_count DESC;

-- =========================================
-- 创建存储过程
-- =========================================

DELIMITER //

-- 清理过期数据的存储过程
CREATE PROCEDURE CleanupOldData(IN days_to_keep INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE table_name VARCHAR(64);
    DECLARE cleanup_cursor CURSOR FOR 
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'binlog_analysis' 
        AND TABLE_NAME IN ('binlog_changes', 'binlog_statistics', 'error_logs', 'system_metrics', 'query_history', 'alert_records');
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cleanup_cursor;
    cleanup_loop: LOOP
        FETCH cleanup_cursor INTO table_name;
        IF done THEN
            LEAVE cleanup_loop;
        END IF;
        
        CASE table_name
            WHEN 'binlog_changes' THEN
                DELETE FROM binlog_changes WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
            WHEN 'binlog_statistics' THEN  
                DELETE FROM binlog_statistics WHERE stat_date < DATE_SUB(CURDATE(), INTERVAL days_to_keep DAY);
            WHEN 'error_logs' THEN
                DELETE FROM error_logs WHERE error_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
            WHEN 'system_metrics' THEN
                DELETE FROM system_metrics WHERE metric_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
            WHEN 'query_history' THEN
                DELETE FROM query_history WHERE query_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
            WHEN 'alert_records' THEN
                DELETE FROM alert_records WHERE alert_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
        END CASE;
    END LOOP;
    CLOSE cleanup_cursor;
    
    -- 优化表
    OPTIMIZE TABLE binlog_changes, binlog_statistics, error_logs, system_metrics, query_history, alert_records;
END //

-- 获取表统计信息的存储过程
CREATE PROCEDURE GetTableStats(IN db_name VARCHAR(64), IN tbl_name VARCHAR(64), IN days INT)
BEGIN
    SELECT 
        operation,
        COUNT(*) as count,
        DATE(timestamp) as date
    FROM binlog_changes 
    WHERE database_name = db_name 
        AND table_name = tbl_name
        AND timestamp >= DATE_SUB(NOW(), INTERVAL days DAY)
    GROUP BY operation, DATE(timestamp)
    ORDER BY date DESC, operation;
END //

DELIMITER ;

-- =========================================
-- 创建事件调度器（自动清理）
-- =========================================

-- 启用事件调度器
SET GLOBAL event_scheduler = ON;

-- 创建每日清理事件
CREATE EVENT IF NOT EXISTS daily_cleanup
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE, '02:00:00')
DO
  CALL CleanupOldData(90);  -- 保留90天数据

-- 创建每小时统计事件
CREATE EVENT IF NOT EXISTS hourly_stats
ON SCHEDULE EVERY 1 HOUR
DO
  INSERT INTO binlog_statistics (stat_date, stat_hour, database_name, table_name, operation, count)
  SELECT 
    DATE(timestamp) as stat_date,
    HOUR(timestamp) as stat_hour,
    database_name,
    table_name,
    operation,
    COUNT(*) as count
  FROM binlog_changes 
  WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    AND timestamp < DATE_SUB(NOW(), INTERVAL 0 HOUR)
  GROUP BY DATE(timestamp), HOUR(timestamp), database_name, table_name, operation
  ON DUPLICATE KEY UPDATE 
    count = VALUES(count),
    updated_at = CURRENT_TIMESTAMP(6);