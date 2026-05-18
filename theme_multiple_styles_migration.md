# Theme 多样式支持数据库迁移方案

## 概述

本文档描述了将 themes 表的默认样式从单一选择改造为多选择的数据库迁移方案。当前结构是一个 theme 只能选择一个默认节点样式和一个默认边样式，改造后将支持一个 theme 可以选择多个节点样式和多个边样式。

## 当前数据结构

### 1. themes 表 (当前结构)
```sql
CREATE TABLE `themes` (
  `id` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `default_node_style_id` varchar(50) DEFAULT NULL,
  `default_edge_style_id` varchar(50) DEFAULT NULL,
  `sort_num` int DEFAULT NULL COMMENT '排序最大的排在最前边',
  PRIMARY KEY (`id`),
  KEY `default_node_style_id` (`default_node_style_id`),
  KEY `default_edge_style_id` (`default_edge_style_id`),
  CONSTRAINT `themes_ibfk_1` FOREIGN KEY (`default_node_style_id`) REFERENCES `node_styles` (`id`) ON DELETE SET NULL,
  CONSTRAINT `themes_ibfk_2` FOREIGN KEY (`default_edge_style_id`) REFERENCES `edge_styles` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 2. node_styles 表
```sql
CREATE TABLE `node_styles` (
  `id` VARCHAR(50) PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL,
  `color` VARCHAR(20) NOT NULL,
  `shape` VARCHAR(20) NOT NULL,
  `opacity` FLOAT DEFAULT NULL
);
```

### 3. edge_styles 表
```sql
CREATE TABLE `edge_styles` (
  `id` VARCHAR(50) PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL,
  `color` VARCHAR(20) NOT NULL,
  `line_style` VARCHAR(20) NOT NULL
);
```

## 目标数据结构

### 1. themes 表 (改造后结构)
```sql
CREATE TABLE `themes` (
  `id` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `sort_num` int DEFAULT NULL COMMENT '排序最大的排在最前边',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 2. theme_node_styles 表 (新建 - 多对多关联表)
```sql
CREATE TABLE `theme_node_styles` (
  `theme_id` varchar(50) NOT NULL,
  `node_style_id` varchar(50) NOT NULL,
  `sort_order` int DEFAULT 0 COMMENT '样式在theme中的排序，数字越大越靠前',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`theme_id`, `node_style_id`),
  FOREIGN KEY (`theme_id`) REFERENCES `themes` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_style_id`) REFERENCES `node_styles` (`id`) ON DELETE CASCADE,
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 3. theme_edge_styles 表 (新建 - 多对多关联表)
```sql
CREATE TABLE `theme_edge_styles` (
  `theme_id` varchar(50) NOT NULL,
  `edge_style_id` varchar(50) NOT NULL,
  `sort_order` int DEFAULT 0 COMMENT '样式在theme中的排序，数字越大越靠前',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`theme_id`, `edge_style_id`),
  FOREIGN KEY (`theme_id`) REFERENCES `themes` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`edge_style_id`) REFERENCES `edge_styles` (`id`) ON DELETE CASCADE,
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

## 数据迁移步骤

### 步骤 1: 准备工作 (重要!)
```sql
-- 1.1 备份当前 themes 表数据
CREATE TABLE themes_backup AS SELECT * FROM themes;

-- 1.2 备份当前 themes 表结构
SHOW CREATE TABLE themes;
```

### 步骤 2: 创建多对多关联表
```sql
-- 2.1 创建节点样式关联表
CREATE TABLE `theme_node_styles` (
  `theme_id` varchar(50) NOT NULL,
  `node_style_id` varchar(50) NOT NULL,
  `sort_order` int DEFAULT 0 COMMENT '样式在theme中的排序，数字越大越靠前',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`theme_id`, `node_style_id`),
  FOREIGN KEY (`theme_id`) REFERENCES `themes` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_style_id`) REFERENCES `node_styles` (`id`) ON DELETE CASCADE,
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2.2 创建边样式关联表
CREATE TABLE `theme_edge_styles` (
  `theme_id` varchar(50) NOT NULL,
  `edge_style_id` varchar(50) NOT NULL,
  `sort_order` int DEFAULT 0 COMMENT '样式在theme中的排序，数字越大越靠前',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`theme_id`, `edge_style_id`),
  FOREIGN KEY (`theme_id`) REFERENCES `themes` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`edge_style_id`) REFERENCES `edge_styles` (`id`) ON DELETE CASCADE,
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 步骤 3: 数据迁移
```sql
-- 3.1 迁移现有默认节点样式到关联表
INSERT INTO theme_node_styles (theme_id, node_style_id, sort_order)
SELECT id, default_node_style_id, 999 -- 使用高排序值表示原来的默认样式
FROM themes 
WHERE default_node_style_id IS NOT NULL;

-- 3.2 迁移现有默认边样式到关联表
INSERT INTO theme_edge_styles (theme_id, edge_style_id, sort_order)
SELECT id, default_edge_style_id, 999 -- 使用高排序值表示原来的默认样式
FROM themes 
WHERE default_edge_style_id IS NOT NULL;
```

### 步骤 4: 清理无效数据
```sql
-- 4.1 删除关联表中无效的节点样式记录
DELETE FROM theme_node_styles tns
WHERE NOT EXISTS (
  SELECT 1 FROM node_styles ns WHERE ns.id = tns.node_style_id
);

-- 4.2 删除关联表中无效的边样式记录
DELETE FROM theme_edge_styles tes
WHERE NOT EXISTS (
  SELECT 1 FROM edge_styles es WHERE es.id = tes.edge_style_id
);
```

### 步骤 5: 修改 themes 表结构 (可选)
```sql
-- 5.1 方案A: 保留原有字段作为兼容 (推荐)
-- 保持原有字段不变，应用层逐步迁移到新的关联表

-- 5.2 方案B: 移除旧字段 (激进方案，需要确保应用层已适配)
ALTER TABLE themes 
DROP FOREIGN KEY themes_ibfk_1,
DROP FOREIGN KEY themes_ibfk_2,
DROP INDEX default_node_style_id,
DROP INDEX default_edge_style_id,
DROP COLUMN default_node_style_id,
DROP COLUMN default_edge_style_id;
```

## 应用层适配建议

### 1. 数据访问层改造
```javascript
// 旧方式: 获取单个默认样式
const theme = await getThemeById(themeId);
const defaultNodeStyleId = theme.default_node_style_id;
const defaultEdgeStyleId = theme.default_edge_style_id;

// 新方式: 获取多个默认样式
const theme = await getThemeById(themeId);
const nodeStyles = await getThemeNodeStyles(themeId); // 返回数组，已按sort_order排序
const edgeStyles = await getThemeEdgeStyles(themeId); // 返回数组，已按sort_order排序
```

### 2. API 接口改造
```javascript
// 旧接口
GET /api/themes/:id
响应: {
  "id": "theme_1",
  "name": "默认主题",
  "defaultNodeStyleId": "node_style_1",
  "defaultEdgeStyleId": "edge_style_1"
}

// 新接口
GET /api/themes/:id
响应: {
  "id": "theme_1",
  "name": "默认主题",
  "nodeStyles": [
    {
      "id": "node_style_1",
      "name": "蓝色圆形",
      "color": "#3498db",
      "shape": "circle",
      "sortOrder": 999
    },
    {
      "id": "node_style_2", 
      "name": "红色方形",
      "color": "#e74c3c",
      "shape": "square",
      "sortOrder": 888
    }
  ],
  "edgeStyles": [
    {
      "id": "edge_style_1",
      "name": "实线",
      "color": "#95a5a6",
      "lineStyle": "solid",
      "sortOrder": 999
    }
  ]
}
```

### 3. 数据管理界面改造
- 样式选择器从单选改为多选
- 添加样式排序功能
- 在theme编辑页面显示当前关联的样式列表

## 回滚方案

### 回滚步骤 (如果出现问题)
```sql
-- 1. 删除新创建的表
DROP TABLE IF EXISTS theme_node_styles;
DROP TABLE IF EXISTS theme_edge_styles;

-- 2. 如果修改了themes表结构，还原它
-- 首先检查themes表是否有备份
SHOW TABLES LIKE 'themes_backup';

-- 如果有备份表，可以恢复数据
TRUNCATE TABLE themes;
INSERT INTO themes SELECT * FROM themes_backup;

-- 3. 删除备份表
DROP TABLE IF EXISTS themes_backup;
```

## 扩展考虑

### 1. 未来可能的扩展
1. **样式分组**: 在关联表中添加 `group_id` 字段，支持样式分组
2. **样式权重**: 添加 `weight` 字段，用于智能样式推荐
3. **样式标签**: 添加标签系统，支持按标签筛选样式
4. **样式继承**: 支持theme之间的样式继承关系

### 2. 性能优化考虑
1. 在关联表上创建适当的索引
2. 考虑使用缓存减少数据库查询
3. 对于热门theme，预加载关联样式

## 验证步骤

迁移完成后，请执行以下验证：

1. **数据完整性验证**
   ```sql
   -- 验证迁移的数据是否正确
   SELECT COUNT(*) as theme_count FROM themes;
   SELECT COUNT(*) as node_style_count FROM theme_node_styles;
   SELECT COUNT(*) as edge_style_count FROM theme_edge_styles;
   
   -- 验证数据一致性
   SELECT t.id, t.name, tns.node_style_id
   FROM themes t
   LEFT JOIN theme_node_styles tns ON t.id = tns.theme_id
   WHERE t.default_node_style_id IS NOT NULL;
   ```

2. **应用层验证**
   - 确保所有用到默认样式的查询都正常
   - 验证新的多选逻辑工作正常
   - 测试样式排序功能

## 注意事项

1. **数据安全**: 迁移前务必备份数据
2. **兼容性**: 建议分阶段迁移，先创建关联表，应用层逐步适配，最后移除旧字段
3. **性能影响**: 多对多关联会增加查询复杂度，需要优化查询语句
4. **事务处理**: 数据迁移建议在事务中执行，确保原子性

---
*文档最后更新: 2026-05-15*