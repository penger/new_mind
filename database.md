# Graph DB 数据库设计文档

## 概述

数据库：`graph_db` (MySQL)
连接：`mysql+pymysql://root:root123@host.docker.internal:3307/graph_db`

## 表清单

| 表名 | 说明 |
|------|------|
| node_styles | 节点样式表 |
| edge_styles | 边样式表 |
| themes | 主题表 |
| nodes | 节点表 |
| edges | 边表 |

---

## ER 关系图

```
node_styles (1:N) ────┐
                     ├── themes (1:N) ─── nodes (1:N) ─── edges (N:1)
edge_styles (1:N) ──┘
```

---

## 表结构

---

### 1. node_styles - 节点样式表

定义节点的视觉样式。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 样式唯一标识 |
| name | VARCHAR(50) | NOT NULL | 样式名称 |
| color | VARCHAR(20) | NOT NULL | 节点颜色 (如 `#ffffff`, `red`) |
| shape | VARCHAR(20) | NOT NULL | 节点形状 (如 `circle`, `rect`) |
| opacity | FLOAT | DEFAULT NULL | 透明度 (0.0-1.0) |

**示例数据：**

| id | name | color | shape | opacity |
|----|------|-------|-------|---------|
| NS1 | 蓝色方形 | #3498db | square | 0.4 |
| NS2 | 红色圆形 | #e74c3c | circle | 0.8 |
| NS3 | 绿色三角 | #2ecc71 | triangle | 0.7 |

---

### 2. edge_styles - 边样式表

定义连线的视觉样式。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 样式唯一标识 |
| name | VARCHAR(50) | NOT NULL | 样式名称 |
| color | VARCHAR(20) | NOT NULL | 边颜色 |
| line_style | VARCHAR(20) | NOT NULL | 线型 (如 `solid`, `dashed`, `dotted`) |

**示例数据：**

| id | name | color | line_style |
|----|------|-------|------------|
| ES1 | 灰色实线 | #95a5a6 | solid |
| ES2 | 灰色虚线 | #95a5a6 | dashed |
| ES3 | 深色粗线 | #2c3e50 | bold |

---

### 3. themes - 主题表

主题用于将节点样式和边样式分组。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 主题唯一标识 |
| name | VARCHAR(50) | NOT NULL | 主题名称 |
| default_node_style_id | VARCHAR(50) | FOREIGN KEY → node_styles.id, ON DELETE SET NULL | 默认节点样式 |
| default_edge_style_id | VARCHAR(50) | FOREIGN KEY → edge_styles.id, ON DELETE SET NULL | 默认边样式 |

---

### 4. nodes - 节点表

存储图谱中的节点。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 节点唯一标识 |
| label | VARCHAR(255) | NOT NULL | 节点标签/名称 |
| imageurl | VARCHAR(500) | DEFAULT NULL | 节点图片 URL (可选) |
| size | FLOAT | DEFAULT NULL | 节点大小 |
| theme_id | VARCHAR(50) | FOREIGN KEY → themes.id, ON DELETE SET NULL | 所属主题 (可选) |
| node_style_id | VARCHAR(50) | FOREIGN KEY → node_styles.id, ON DELETE SET NULL | 节点样式 (可选) |
| content | TEXT | DEFAULT NULL | 节点内容/描述 (可选) |
| style | JSON | DEFAULT NULL | 自定义样式 JSON (可选) |

---

### 5. edges - 边表

存储节点之间的连线关系。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 边唯一标识 |
| source_id | VARCHAR(50) | FOREIGN KEY → nodes.id, ON DELETE CASCADE | 起始节点 |
| target_id | VARCHAR(50) | FOREIGN KEY → nodes.id, ON DELETE CASCADE | 目标节点 |
| label | VARCHAR(255) | DEFAULT NULL | 边标签 (可选) |
| width | FLOAT | DEFAULT NULL | 边宽度 |
| theme_id | VARCHAR(50) | FOREIGN KEY → themes.id, ON DELETE SET NULL | 所属主题 (可选) |
| edge_style_id | VARCHAR(50) | FOREIGN KEY → edge_styles.id, ON DELETE SET NULL | 边样式 (可选) |
| content | TEXT | DEFAULT NULL | 边内容/描述 (可选) |
| style | JSON | DEFAULT NULL | 自定义样式 JSON (可选) |

---

## 外键约束与级联删除

| 约束字段 | 参考表 | ON DELETE | 说明 |
|----------|--------|-----------|------|
| nodes.theme_id | themes.id | SET NULL | 节点所属主题删除时，节点 theme_id 置空 |
| nodes.node_style_id | node_styles.id | SET NULL | 节点样式删除时，节点样式置空 |
| edges.source_id | nodes.id | CASCADE | 删除节点时，联动删除以该节点为源的所有边 |
| edges.target_id | nodes.id | CASCADE | 删除节点时，联动删除以该节点为目标的所有边 |
| edges.theme_id | themes.id | SET NULL | 主题删除时，边 theme_id 置空 |
| edges.edge_style_id | edge_styles.id | SET NULL | 边样式删除时，边样式置空 |
| themes.default_node_style_id | node_styles.id | SET NULL | 节点样式删除时，主题默认节点样式置空 |
| themes.default_edge_style_id | edge_styles.id | SET NULL | 边样式删除时，主题默认边样式置空 |

---

## 数据类型说明

| 字段类型 | 说明 |
|----------|------|
| VARCHAR(n) | 变长字符串，最大 n 个字符 |
| FLOAT | 浮点数，用于尺寸、透明度等数值 |
| TEXT | 长文本，用于节点/边的描述内容 |
| JSON | JSON 对象，用于存储自定义样式配置 |

---

## 使用示例

```json
{
  "themes": [
    {
      "id": "theme_default",
      "name": "默认主题",
      "defaultNodeStyleId": "style_node_1",
      "defaultEdgeStyleId": "style_edge_1"
    }
  ],
  "nodeStyles": [
    {
      "id": "style_node_1",
      "name": "圆形蓝色节点",
      "color": "#3498db",
      "shape": "circle",
      "opacity": 1.0
    }
  ],
  "edgeStyles": [
    {
      "id": "style_edge_1",
      "name": "实线灰色边",
      "color": "#95a5a6",
      "style": "solid"
    }
  ],
  "nodes": [
    {
      "id": "node_1",
      "label": "概念A",
      "imageurl": "https://example.com/image.png",
      "size": 25,
      "themeId": "theme_default",
      "nodeStyleId": "style_node_1",
      "content": "这是节点的详细描述",
      "style": {}
    }
  ],
  "links": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "label": "关联",
      "width": 2,
      "themeId": "theme_default",
      "edgeStyleId": "style_edge_1",
      "content": "边的描述",
      "style": {}
    }
  ]
}
```
