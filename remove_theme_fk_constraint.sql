-- 移除 themes 表外键约束的 SQL 脚本
-- 执行前建议备份数据库

-- 1. 查看当前外键约束信息
SELECT 
    TABLE_NAME, 
    COLUMN_NAME, 
    CONSTRAINT_NAME, 
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'themes' AND CONSTRAINT_NAME LIKE '%ibfk%';

-- 2. 根据你的数据库的实际约束名来移除外键约束
-- 注意：约束名可能不是 themes_ibfk_1 和 themes_ibfk_2，请根据上一步查询结果修改

-- 如果约束名是 themes_ibfk_1 和 themes_ibfk_2
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_1;
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_2;

-- 3. 可选：移除索引（如果需要）
-- ALTER TABLE themes DROP INDEX default_node_style_id;
-- ALTER TABLE themes DROP INDEX default_edge_style_id;

-- 4. 查看修改后的表结构
DESCRIBE themes;

-- 5. 查看索引情况
SHOW INDEX FROM themes;

-- 6. 数据迁移验证示例（确保现有数据不受影响）
-- 6.1 检查现有行数
SELECT COUNT(*) as total_themes FROM themes;

-- 6.2 检查非空值的样式
SELECT 
    COUNT(*) as themes_with_node_style, 
    COUNT(CASE WHEN default_node_style_id IS NOT NULL AND default_node_style_id != '' THEN 1 END) as themes_with_valid_node_style,
    COUNT(CASE WHEN default_edge_style_id IS NOT NULL AND default_edge_style_id != '' THEN 1 END) as themes_with_valid_edge_style
FROM themes;

-- 6.3 检查可以存储分隔符字符串的示例
SELECT  
    id,
    name,
    default_node_style_id,
    CHAR_LENGTH(default_node_style_id) as node_style_length,
    default_edge_style_id,
    CHAR_LENGTH(default_edge_style_id) as edge_style_length
FROM themes
WHERE default_node_style_id LIKE '%,%' OR default_edge_style_id LIKE '%,%';

-- 如果希望扩展字段长度来容纳更多样式ID，可以执行以下DDL：
-- ALTER TABLE themes MODIFY COLUMN default_node_style_id VARCHAR(500);
-- ALTER TABLE themes MODIFY COLUMN default_edge_style_id VARCHAR(500);

-- 7. 注意：应用程序层需要处理分隔符字符串的解析
--    - 分隔符：逗号 (,)
--    - 单个ID示例: "style_1"
--    - 多个ID示例: "style_1,style_2,style_3"
--    - 空值或空字符串表示没有样式

-- 8. 回滚脚本（如果需要）
-- -- 重新添加外键约束
-- ALTER TABLE themes 
-- ADD CONSTRAINT themes_ibfk_1 
-- FOREIGN KEY (default_node_style_id) REFERENCES node_styles(id) ON DELETE SET NULL;
-- 
-- ALTER TABLE themes 
-- ADD CONSTRAINT themes_ibfk_2 
-- FOREIGN KEY (default_edge_style_id) REFERENCES edge_styles(id) ON DELETE SET NULL;

-- 重要安全提示：
-- 1. 执行前请备份数据库
-- 2. 在开发环境测试后再上生产环境
-- 3. 确保应用层代码已经修改为支持分隔符字符串格式