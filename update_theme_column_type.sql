-- 将 themes 表中的 default_node_style_id 和 default_edge_style_id 列从 VARCHAR(50) 改为 TEXT
-- 以支持存储多个样式ID连接成的字符串

-- 备份现有数据（可选步骤）
-- DROP TABLE IF EXISTS themes_backup;
-- CREATE TABLE themes_backup AS SELECT * FROM themes;

-- 修改表的列类型
ALTER TABLE themes 
MODIFY COLUMN default_node_style_id TEXT,
MODIFY COLUMN default_edge_style_id TEXT;

-- 验证修改
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    CHARACTER_MAXIMUM_LENGTH 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'themes' 
AND TABLE_SCHEMA = DATABASE()
AND COLUMN_NAME IN ('default_node_style_id', 'default_edge_style_id');

-- 输出当前 themes 表结构
SHOW CREATE TABLE themes;