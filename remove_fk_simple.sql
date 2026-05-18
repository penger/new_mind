-- 简单直接的 thees 表外键约束移除脚本
-- 运行此脚本前请确保已备份数据库！

-- 备份 themes 表数据
CREATE TABLE IF NOT EXISTS themes_backup_before_fk_removal AS SELECT * FROM themes;

-- 1. 查看当前表结构
DESCRIBE themes;

-- 2. 查看外键约束名称
SELECT CONSTRAINT_NAME 
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE TABLE_NAME = 'themes' AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- 3. 根据上一步查出的约束名进行移除
-- 通常约束名类似 themes_ibfk_1, themes_ibfk_2

-- 3.1 首先尝试移除 themes_ibfk_1（节点样式外键）
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_1;

-- 3.2 然后尝试移除 themes_ibfk_2（边样式外键）
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_2;

-- 如果上面的名称不对，可以用下面的语句查找确切名称后手动替换
/*
-- 查找所有外键约束名
SELECT 
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'themes' AND CONSTRAINT_NAME LIKE '%ibfk%';
*/

-- 4. 验证外键已移除
SELECT CONSTRAINT_NAME 
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE TABLE_NAME = 'themes' AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- 应返回空结果集

-- 5. 可选：如果希望保留索引性能，可以保留索引
-- 查看索引
SHOW INDEX FROM themes;

-- 如果不需要，可以移除索引以彻底清除外键痕迹
-- ALTER TABLE themes DROP INDEX default_node_style_id;
-- ALTER TABLE themes DROP INDEX default_edge_style_id;

-- 6. 查看修改后的表结构
DESCRIBE themes;

-- 7. 测试数据完整性
SELECT COUNT(*) as total_rows FROM themes;
SELECT COUNT(*) as valid_rows FROM themes_backup_before_fk_removal;

-- 两个计数应该相等

-- 8. 清理备份表（如果需要）
-- DROP TABLE IF EXISTS themes_backup_before_fk_removal;