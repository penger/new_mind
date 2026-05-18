# Theme 多样式支持 - 简化方案

## 概述

这是一个更简单的方案来实现 theme 支持多个默认节点样式和边样式。通过移除外键约束，将 `default_node_style_id` 和 `default_edge_style_id` 字段改为存储多个 ID 的格式（分隔符字符串或 JSON 数组）。

## 当前数据结构

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

## 方案选择

### 方案一：分隔符字符串方案 (推荐)

使用逗号分隔的字符串存储多个 ID，例如：`"style_1,style_2,style_3"`

**优点**：
- 改动最小，只需移除外键约束
- 应用层处理简单
- 兼容现有的单个ID场景

**缺点**：
- 无法在数据库层验证ID有效性
- 查询和更新相对复杂
- 难以维护排序

### 方案二：JSON数组方案

使用MySQL的JSON类型存储ID数组，例如：`["style_1", "style_2", "style_3"]`

**优点**：
- 可以使用JSON函数进行查询
- 数据结构更清晰
- 支持更复杂的结构（如包含排序信息）

**缺点**：
- 需要修改字段类型
- 应用层需要处理JSON解析
- 某些MySQL版本JSON支持有限

### 方案三：多对多关联表方案 (之前方案)

创建 `theme_node_styles` 和 `theme_edge_styles` 关联表

**优点**：
- 符合数据库规范化
- 支持复杂的查询和排序
- 引用完整性保证

**缺点**：
- 改动较大，需要创建新表
- 数据迁移相对复杂

## 实施步骤 (分隔符字符串方案)

### 步骤1: 数据备份

```sql
-- 备份当前数据
CREATE TABLE themes_backup AS SELECT * FROM themes;

-- 查看当前数据
SELECT * FROM themes;
```

### 步骤2: 移除外键约束

```sql
-- 2.1 移除节点样式外键约束
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_1;

-- 2.2 移除边样式外键约束
ALTER TABLE themes DROP FOREIGN KEY themes_ibfk_2;

-- 2.3 可选：移除索引
-- ALTER TABLE themes DROP INDEX default_node_style_id;
-- ALTER TABLE themes DROP INDEX default_edge_style_id;
```

### 步骤3: 修改字段类型 (可选)

```sql
-- 方案A: 保持原类型，使用现有字段存储分隔符字符串 (推荐)
-- 单个ID直接存储，多个ID用逗号分隔，如 "style_1,style_2"

-- 方案B: 扩大字段长度以容纳更多ID
ALTER TABLE themes 
MODIFY COLUMN default_node_style_id VARCHAR(1000),
MODIFY COLUMN default_edge_style_id VARCHAR(1000);

-- 方案C: 改为TEXT类型
-- ALTER TABLE themes 
-- MODIFY COLUMN default_node_style_id TEXT,
-- MODIFY COLUMN default_edge_style_id TEXT;
```

### 步骤4: 数据迁移 (如果需要格式转换)

```sql
-- 如果现有数据需要格式转换（如从单ID转为数组）
-- 通常不需要，因为单ID已经是有效格式
```

## 应用层数据处理逻辑

### 1. 分隔符字符串处理函数

```javascript
// 分隔符定义
const DELIMITER = ',';

// 字符串转数组
function parseStyleIds(styleIdsString) {
  if (!styleIdsString) return [];
  return styleIdsString.split(DELIMITER)
    .map(id => id.trim())
    .filter(id => id.length > 0);
}

// 数组转字符串
function serializeStyleIds(styleIdsArray) {
  if (!styleIdsArray || styleIdsArray.length === 0) return null;
  return styleIdsArray.join(DELIMITER);
}

// 添加样式ID
function addStyleId(existingString, newStyleId) {
  const ids = parseStyleIds(existingString);
  if (!ids.includes(newStyleId)) {
    ids.push(newStyleId);
  }
  return serializeStyleIds(ids);
}

// 移除样式ID
function removeStyleId(existingString, styleIdToRemove) {
  const ids = parseStyleIds(existingString);
  const filteredIds = ids.filter(id => id !== styleIdToRemove);
  return serializeStyleIds(filteredIds);
}

// 检查是否包含样式ID
function hasStyleId(existingString, styleId) {
  const ids = parseStyleIds(existingString);
  return ids.includes(styleId);
}

// 获取样式ID数量
function countStyleIds(existingString) {
  const ids = parseStyleIds(existingString);
  return ids.length;
}
```

### 2. Theme数据模型改造

```javascript
// 旧模型
class Theme {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.defaultNodeStyleId = data.default_node_style_id; // 单个ID
    this.defaultEdgeStyleId = data.default_edge_style_id; // 单个ID
    this.sortNum = data.sort_num;
  }
}

// 新模型
class Theme {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.sortNum = data.sort_num;
    
    // 解析分隔符字符串为数组
    this.defaultNodeStyleIds = parseStyleIds(data.default_node_style_id);
    this.defaultEdgeStyleIds = parseStyleIds(data.default_edge_style_id);
  }
  
  // 序列化回数据库格式
  toDatabaseFormat() {
    return {
      id: this.id,
      name: this.name,
      sort_num: this.sortNum,
      default_node_style_id: serializeStyleIds(this.defaultNodeStyleIds),
      default_edge_style_id: serializeStyleIds(this.defaultEdgeStyleIds)
    };
  }
}
```

### 3. API接口适配

```javascript
// 旧API响应
{
  "id": "theme_1",
  "name": "默认主题",
  "defaultNodeStyleId": "style_1",
  "defaultEdgeStyleId": "edge_1"
}

// 新API响应
{
  "id": "theme_1",
  "name": "默认主题",
  "defaultNodeStyleIds": ["style_1", "style_2", "style_3"],
  "defaultEdgeStyleIds": ["edge_1", "edge_2"]
}

// 或者保持兼容性
{
  "id": "theme_1",
  "name": "默认主题",
  "defaultNodeStyleId": "style_1,style_2,style_3", // 分隔符字符串
  "defaultEdgeStyleId": "edge_1,edge_2",
  "defaultNodeStyleIds": ["style_1", "style_2", "style_3"], // 解析后的数组
  "defaultEdgeStyleIds": ["edge_1", "edge_2"]
}
```

### 4. 数据库访问层

```javascript
// 获取theme及其样式
async function getThemeWithStyles(themeId) {
  const theme = await getThemeById(themeId);
  
  // 解析样式ID
  const nodeStyleIds = parseStyleIds(theme.default_node_style_id);
  const edgeStyleIds = parseStyleIds(theme.default_edge_style_id);
  
  // 获取样式详情
  const nodeStyles = nodeStyleIds.length > 0 
    ? await getNodeStylesByIds(nodeStyleIds)
    : [];
    
  const edgeStyles = edgeStyleIds.length > 0
    ? await getEdgeStylesByIds(edgeStyleIds)
    : [];
    
  return {
    ...theme,
    nodeStyles,
    edgeStyles
  };
}

// 更新theme样式
async function updateThemeStyles(themeId, nodeStyleIds, edgeStyleIds) {
  const nodeStyleString = serializeStyleIds(nodeStyleIds);
  const edgeStyleString = serializeStyleIds(edgeStyleIds);
  
  await updateTheme(themeId, {
    default_node_style_id: nodeStyleString,
    default_edge_style_id: edgeStyleString
  });
}
```

## 实施步骤 (JSON数组方案)

### 修改字段类型为JSON

```sql
-- 修改字段类型
ALTER TABLE themes 
MODIFY COLUMN default_node_style_id JSON,
MODIFY COLUMN default_edge_style_id JSON;
```

### JSON数据处理函数

```javascript
// JSON数组处理
function parseJsonStyleIds(jsonString) {
  try {
    if (!jsonString) return [];
    const parsed = JSON.parse(jsonString);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error('JSON解析错误:', error);
    return [];
  }
}

function serializeJsonStyleIds(styleIdsArray) {
  if (!styleIdsArray || styleIdsArray.length === 0) return null;
  return JSON.stringify(styleIdsArray);
}

// 使用JSON_CONTAINS查询
const query = `
  SELECT * FROM themes 
  WHERE JSON_CONTAINS(default_node_style_id, ?)
`;
// 使用: JSON_CONTAINS(default_node_style_id, '"style_1"')
```

## 兼容性考虑

### 1. 向后兼容
- 保持字段名不变，现有代码可以继续工作
- 对单ID场景完全兼容
- 应用层逐步适配多ID处理逻辑

### 2. 向前兼容
- 新功能识别分隔符格式
- 支持同时返回解析后的数组和原始字符串
- API版本控制（如/v2/themes）

### 3. 数据验证
由于移除了外键约束，需要在应用层验证样式ID的有效性：

```javascript
async function validateStyleIds(nodeStyleIds, edgeStyleIds) {
  // 验证节点样式
  if (nodeStyleIds.length > 0) {
    const validNodeStyles = await checkNodeStylesExist(nodeStyleIds);
    if (validNodeStyles.length !== nodeStyleIds.length) {
      throw new Error('部分节点样式ID不存在');
    }
  }
  
  // 验证边样式
  if (edgeStyleIds.length > 0) {
    const validEdgeStyles = await checkEdgeStylesExist(edgeStyleIds);
    if (validEdgeStyles.length !== edgeStyleIds.length) {
      throw new Error('部分边样式ID不存在');
    }
  }
}
```

## 维护排序

如果需要维护样式在theme中的显示顺序，可以考虑以下方案：

### 方案A: 固定顺序
按照添加顺序排列，或按ID字母顺序排列

### 方案B: 带排序信息的分隔符
使用特殊格式，如 `"style_1:1,style_2:2,style_3:3"`

```javascript
function parseWithOrder(styleString) {
  return styleString.split(',')
    .map(item => {
      const [id, order] = item.split(':');
      return { id, order: parseInt(order) || 0 };
    })
    .sort((a, b) => b.order - a.order) // 数字越大越靠前
    .map(item => item.id);
}
```

### 方案C: 单独排序字段
添加 `style_order` 字段存储排序信息

## 优缺点对比

| 方面 | 分隔符方案 | 多对多关联表方案 |
|------|-----------|------------------|
| 实施复杂度 | **低** - 只需移除外键 | **高** - 需要创建新表 |
| 数据完整性 | 无数据库级验证 | 有外键约束保证 |
| 查询性能 | 简单查询快，复杂查询慢 | 关联查询可能更快 |
| 扩展性 | 有限 | **好** - 支持更多属性 |
| 排序支持 | 需要额外处理 | **好** - 关联表可加排序字段 |
| 数据迁移 | 简单 | 相对复杂 |
| 应用层适配 | 较简单 | 需要重构数据访问 |

## 推荐实施方案

### 短期方案 (快速上线)
1. 使用分隔符字符串方案
2. 移除外键约束，保持字段类型不变
3. 应用层添加多ID处理逻辑
4. API同时支持新旧格式

### 长期方案 (推荐)
1. 先实施分隔符方案作为过渡
2. 逐步重构为多对多关联表方案
3. 最终移除分隔符字段，完全使用关联表

### 实施时间线
1. **第1周**: 数据库修改 + 基础应用层适配
2. **第2周**: 前端界面改造（多选组件）
3. **第3周**: 测试和bug修复
4. **第4周**: 上线观察，准备关联表方案

## 回滚方案

如果出现问题，可以回滚：

```sql
-- 1. 如果有备份表，恢复数据
DROP TABLE IF EXISTS themes;
CREATE TABLE themes_backup_restore AS SELECT * FROM themes_backup;

-- 2. 重新添加外键约束
ALTER TABLE themes 
ADD CONSTRAINT themes_ibfk_1 
FOREIGN KEY (default_node_style_id) REFERENCES node_styles(id) ON DELETE SET NULL,
ADD CONSTRAINT themes_ibfk_2 
FOREIGN KEY (default_edge_style_id) REFERENCES edge_styles(id) ON DELETE SET NULL;

-- 3. 删除备份表
DROP TABLE IF EXISTS themes_backup;
```

## 测试建议

1. **单元测试**: 测试分隔符解析和序列化函数
2. **集成测试**: 测试数据库操作和API接口
3. **兼容性测试**: 确保现有功能不受影响
4. **性能测试**: 测试多ID处理的性能
5. **数据一致性测试**: 验证数据迁移的正确性

---
*文档最后更新: 2026-05-15*  
*方案选择: 分隔符字符串方案 (快速实施，兼容性好)*