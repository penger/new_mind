-- 安全更新 themes 表列类型脚本
-- 此脚本将 default_node_style_id 和 default_edge_style_id 列改为 TEXT 类型

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;

-- 检查当前列类型
SELECT 
    '当前列类型检查:' AS info,
    COLUMN_NAME, 
    DATA_TYPE, 
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'themes' 
AND TABLE_SCHEMA = DATABASE()
AND COLUMN_NAME IN ('default_node_style_id', 'default_edge_style_id');

-- 检查是否有过长数据
SELECT 
    '检查数据长度:' AS info,
    id,
    name,
    LENGTH(default_node_style_id) AS node_style_length,
    LENGTH(default_edge_style_id) AS edge_style_length
FROM themes
WHERE LENGTH(default_node_style_id) > 45 OR LENGTH(default_edge_style_id) > 45
LIMIT 10;

-- 修改列类型（如果存在外键约束，需要先删除）
-- 首先尝试修改列类型
ALTER TABLE themes 
CHANGE COLUMN default_node_style_id default_node_style_id TEXT NULL DEFAULT NULL,
CHANGE COLUMN default_edge_style_id default_edge_style_id TEXT NULL DEFAULT NULL;

-- 另一种方法：如果上面的 CHANGE 失败，可以尝试 MODIFY
-- ALTER TABLE themes 
-- MODIFY COLUMN default_node_style_id TEXT NULL DEFAULT NULL,
-- MODIFY COLUMN default_edge_style_id TEXT NULL DEFAULT NULL;

-- 查看更新后的表结构
SELECT 
    '更新后列类型:' AS info,
    COLUMN_NAME, 
    DATA_TYPE, 
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'themes' 
AND TABLE_SCHEMA = DATABASE()
AND COLUMN_NAME IN ('default_node_style_id', 'default_edge_style_id');

-- 验证一些数据
SELECT 
    '验证数据:' AS info,
    id,
    name,
    IF(LENGTH(default_node_style_id) < 100, CONCAT(SUBSTRING(default_node_style_id, 1, 50), '...'), default_node_style_id) AS node_style_preview,
    IF(LENGTH(default_edge_style_id) < 100, CONCAT(SUBSTRING(default_edge_style_id, 1, 50), '...'), default_edge_style_id) AS edge_style_preview
FROM themes
LIMIT 5;

SET SQL_SAFE_UPDATES = 1;
SET FOREIGN_KEY_CHECKS = 1;

-- 最终确认
SHOW CREATE TABLE themes;