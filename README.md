# 关系图谱编辑器 - 专业版

一个功能强大的在线关系图谱编辑和管理系统，支持多种可视化视图、丰富的交互功能和灵活的数据管理。

## 📋 项目概述

本项目是一个现代化的关系图谱编辑器，采用前后端分离架构，支持多种视图模式、丰富的编辑功能和主题管理。系统基于 **Vue 3** 前端框架和 **FastAPI** 后端框架构建，提供流畅的用户体验和强大的数据管理能力。

**注意**：本系统采用**原子操作**模式，每次修改都会立即保存到数据库，无需手动保存。

## ✨ 核心功能

### 🎨 多视图模式

系统提供四种不同的视图模式，满足不同的使用场景：

1. **普通浏览模式** - 简洁的 2D SVG 图形展示
   - 节点自动布局
   - 鼠标悬停显示详情
   - 支持节点拖拽调整位置
   - 物理模拟引擎驱动

2. **星云浏览模式** - 震撼的 3D 星云效果
   - Three.js 驱动的 3D 可视化
   - 动态粒子效果
   - 沉浸式交互体验
   - 视角缩放和旋转

3. **星图浏览模式** - 优雅的星图展示
   - 基于 D3.js 的力导向图
   - 节点发光效果
   - 连线动画
   - 星空背景

4. **编辑模式** - 完整的图谱编辑功能
   - 双击添加新节点
   - Shift + 拖拽创建连线
   - 右侧属性面板编辑
   - 实时预览样式效果
   - 节点和边的增删改查

### 🎯 交互功能

#### 浏览模式交互
- **鼠标悬停** - 快速查看节点/连线信息
- **节点拖拽** - 调整节点位置，自动固定释放
- **节点点击** - 选中节点并高亮相关连线
- **视图缩放** - 支持图形缩放和平移

#### 编辑模式交互
- **双击空白区域** - 创建新节点
- **Shift + 拖拽** - 从节点拖出创建连线
- **双击节点/连线** - 打开属性编辑面板
- **Delete 键** - 删除选中元素
- **Ctrl + 鼠标框选** - 多选节点

### 🎭 样式系统

#### 预设样式管理
系统提供预设样式模板，包括：

**节点样式预设**：
- 蓝色方形 - 适合普通节点
- 红色圆形 - 适合重点节点
- 绿色三角 - 适合特殊节点
- 支持自定义添加/修改/删除

**连线样式预设**：
- 灰色实线 - 默认连线
- 灰色虚线 - 辅助关系
- 深色粗线 - 重要关系
- 支持自定义样式参数

#### 个性化样式定制
每个节点和连线都支持独立样式设置：

**节点样式参数**：
```json
{
  "color": "#e74c3c",    // 节点颜色
  "shape": "square",     // 形状 (circle/square/triangle/diamond/star)
  "opacity": 0.8         // 透明度 (0.0-1.0)
}
```

**连线样式参数**：
```json
{
  "color": "#2ecc71",    // 连线颜色
  "style": "dashed",     // 线型 (solid/dashed)
  "width": 3             // 线宽
}
```

**样式优先级**：自定义样式 > 预设样式 > 默认值

### 🗂️ 主题管理

系统支持多主题管理，每个主题可以设置：
- 默认节点样式
- 默认连线样式
- 主题描述和说明

节点和连线可以关联到特定主题，实现：
- 图层过滤和显示
- 批量样式应用
- 主题化的视觉分组

### 📊 数据管理

#### 完整的数据模型
- **节点** - 标签、大小、内容、图片、位置坐标
- **连线** - 源节点、目标节点、标签、宽度、描述
- **主题** - 名称、默认样式配置
- **样式预设** - 节点/连线的可复用样式模板

#### 原子操作
所有数据操作都是原子化的：
- 每次修改立即保存到数据库
- 无需手动保存操作
- 支持单个元素的增删改查
- 自动处理级联删除

## 🏗️ 技术架构

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.5.32 | 核心框架 (Composition API) |
| Element Plus | 2.13.7 | UI 组件库 |
| D3.js | v7 | 2D 图形渲染和力导向图 |
| Three.js | - | 3D 星云视图 |
| Vite | 5.4.8 | 构建工具 |
| ECharts | - | 图表可视化 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.109.0 | Web 框架 |
| SQLAlchemy | 2.0.25 | ORM 工具 |
| Pydantic | 2.5.3 | 数据验证 |
| Uvicorn | 0.27.0 | ASGI 服务器 |
| PyMySQL | 1.1.0 | MySQL 驱动 |

### 数据库

- **MySQL 8.0** - 关系型数据库存储
- **连接配置**：
  - Host: `localhost` (本地)
  - Port: `3306`
  - Database: `graph_db`
  - User: `root`
  - Password: `9ijn)OKM`

### 部署架构

```
┌─────────────────────────────────────────┐
│           后端服务 (FastAPI)              │
│             Port: 8000                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
          ┌──────────────┐
          │  MySQL 8.0   │
          │   数据库     │
          └──────────────┘
                 ▲
                 │
┌────────────────┴────────────────────────┐
│         前端开发服务器 (Vite)            │
│           Port: 8080                   │
└─────────────────────────────────────────┘
```

### 🔧 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 (Vite) | **8080** | Vue.js 开发服务器 |
| 后端 (FastAPI) | **8000** | Python API 服务 |
| MySQL | 3306 | 数据库服务 |

**注意**：如果 8080 端口被占用，可以修改 `frontend/vite.config.js` 中的 `server.port` 配置。

## 📐 数据模型

### ER 关系图

```
┌────────────────┐         ┌────────────────┐
│  node_styles   │         │  edge_styles  │
│  节点样式预设   │         │  连线样式预设  │
└───────┬────────┘         └───────┬────────┘
        │                         │
        └──────┬────────┬─────────┘
               │        │
               ▼        ▼
        ┌────────────────┐
        │    themes      │
        │     主题       │
        └───────┬────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
   ┌─────────┐      ┌─────────┐
   │  nodes  │◄────►│  edges  │
   │  节点   │ 1:N  │  连线   │
   └─────────┘      └─────────┘
```

### 数据库表结构

#### 1. node_styles - 节点样式预设表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 主键，样式唯一标识 |
| name | VARCHAR(50) | 样式名称 |
| color | VARCHAR(20) | 节点颜色 |
| shape | VARCHAR(20) | 节点形状 |
| opacity | FLOAT | 透明度 (0.0-1.0) |

#### 2. edge_styles - 连线样式预设表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 主键，样式唯一标识 |
| name | VARCHAR(50) | 样式名称 |
| color | VARCHAR(20) | 边颜色 |
| line_style | VARCHAR(20) | 线型 (solid/dashed/dotted) |

#### 3. themes - 主题表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 主键，主题唯一标识 |
| name | VARCHAR(50) | 主题名称 |
| default_node_style_id | VARCHAR(50) | 默认节点样式 (FK) |
| default_edge_style_id | VARCHAR(50) | 默认连线样式 (FK) |

#### 4. nodes - 节点表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 主键，节点唯一标识 |
| label | VARCHAR(255) | 节点标签/名称 |
| size | FLOAT | 节点大小 |
| theme_id | VARCHAR(50) | 所属主题 (FK) |
| node_style_id | VARCHAR(50) | 节点样式 (FK) |
| content | TEXT | 详情描述 |
| style | JSON | 个性化样式配置 |
| imageUrl | VARCHAR(500) | 节点图片URL (可选) |

#### 5. edges - 连线表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50) | 主键，连线唯一标识 |
| source_id | VARCHAR(50) | 源节点ID (FK) |
| target_id | VARCHAR(50) | 目标节点ID (FK) |
| label | VARCHAR(255) | 连线标签 |
| width | FLOAT | 线宽 |
| theme_id | VARCHAR(50) | 所属主题 (FK) |
| edge_style_id | VARCHAR(50) | 连线样式 (FK) |
| content | TEXT | 详情描述 |
| style | JSON | 个性化样式配置 |

## 🔌 API 接口

### 基础信息

- **Base URL**: `http://localhost:8000/api`
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **数据格式**: JSON
- **操作模式**: 原子操作，每次修改立即生效

### 接口列表

#### 1. 获取图谱数据

```
GET /api/data
```

**响应示例**：
```json
{
  "themes": [...],
  "nodeStyles": [...],
  "edgeStyles": [...],
  "nodes": [...],
  "links": [...]
}
```

#### 2. 节点操作

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/nodes` | 创建节点 |
| PUT | `/api/nodes/{node_id}` | 更新节点 |
| DELETE | `/api/nodes/{node_id}` | 删除节点 |

#### 3. 连线操作

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/edges` | 创建连线 |
| PUT | `/api/edges/{edge_id}` | 更新连线 |
| DELETE | `/api/edges/{edge_id}` | 删除连线 |

#### 4. 主题操作

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/themes` | 创建主题 |
| PUT | `/api/themes/{theme_id}` | 更新主题 |
| DELETE | `/api/themes/{theme_id}` | 删除主题 |

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+
- MySQL 8.0+
- uv (Python 包管理工具)

### 安装 uv

如果你还没有安装 uv，请先安装：

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**使用 pipx:**
```bash
pipx install uv
```

### 启动后端服务

```bash
# 进入后端目录
cd backend

# 使用 uv 安装依赖并运行（自动创建虚拟环境）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

uv 会自动：
- 检测 `pyproject.toml` 或 `requirements.txt`
- 创建隔离的虚拟环境
- 安装所有依赖
- 启动开发服务器

### 启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器会自动热重载，**修改代码后无需手动重启**。

### 停止服务

#### 停止后端服务

在运行后端服务的终端窗口按 `Ctrl + C` 即可停止服务。

或者查找并终止进程：

```bash
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 终止进程（将 <PID> 替换为实际的进程 ID）
taskkill /F /PID <PID>
```

#### 停止前端服务

在运行前端服务的终端窗口按 `Ctrl + C` 即可停止服务。

或者查找并终止进程：

```bash
# 查找占用 8080 端口的进程
netstat -ano | findstr :8080

# 终止进程（将 <PID> 替换为实际的进程 ID）
taskkill /F /PID <PID>
```

### 数据库初始化

确保 MySQL 中存在 `graph_db` 数据库：

```sql
CREATE DATABASE IF NOT EXISTS graph_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 访问应用

- 前端界面：http://localhost:8080
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 🛠️ 使用指南

### 创建第一个节点

1. 切换到 **编辑模式**
2. 在图形区域**双击**空白处
3. 输入节点名称和基本信息
4. 选择节点样式或设置个性化样式
5. 点击确认保存（数据自动保存到数据库）

### 创建节点连线

1. 确保处于**编辑模式**
2. 选中源节点
3. 按住 **Shift** 键
4. 从源节点**拖拽**到目标节点
5. 在弹出的面板中设置连线属性
6. 点击确认保存（数据自动保存到数据库）

### 原子操作说明

- 每次对节点或连线的修改都会**立即保存**
- 无需手动触发保存操作
- 删除操作也会立即生效
- 所有操作都是原子性的，失败会自动回滚

### 主题管理

1. 在侧边栏选择**图层设置**
2. 使用主题过滤功能
3. 关联节点和连线到特定主题
4. 支持主题化的样式批量应用

## 📁 项目结构

```
new_mind/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 入口和配置
│   │   ├── database.py        # 数据库连接和会话
│   │   ├── models.py         # SQLAlchemy 模型定义
│   │   ├── schemas.py        # Pydantic 数据模型
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── graphs.py     # 图谱 API 路由
│   ├── requirements.txt
│   └── pyproject.toml        # Python 项目配置 (uv)
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── main.js           # Vue 应用入口
│   │   ├── App.vue          # 主组件 (核心业务逻辑)
│   │   ├── style.css        # 全局样式
│   │   └── components/
│   │       └── StarGraph.vue # 星图组件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── database.md               # 数据库设计文档
└── README.md                 # 项目说明文档
```

## 🎓 关键文件说明

| 文件路径 | 说明 |
|---------|------|
| `frontend/src/App.vue` | 前端主组件，包含所有业务逻辑和视图切换 |
| `frontend/src/style.css` | 样式文件，包含 info-card、preview 等组件样式 |
| `frontend/src/components/StarGraph.vue` | 星图可视化组件 |
| `backend/app/models.py` | SQLAlchemy 模型，定义数据库表结构 |
| `backend/app/schemas.py` | Pydantic 模型，定义 API 数据验证 |
| `backend/app/routers/graphs.py` | API 路由，实现所有图谱操作接口 |
| `backend/app/database.py` | 数据库连接配置和会话管理 |

## 🔒 安全说明

当前配置仅供开发和测试使用。生产环境请注意：

1. **数据库密码** - 修改默认的 `9ijn)OKM` 密码
2. **CORS 配置** - 限制前端域名访问
3. **API 认证** - 添加用户认证和授权机制
4. **数据加密** - 敏感数据加密存储
5. **HTTPS** - 使用 HTTPS 加密通信

## 🐛 常见问题

### Q: 节点样式不生效？

A: 检查样式优先级：自定义 `style` > 预设样式 `nodeStyleId` > 默认值。确保 JSON 格式正确。

### Q: 连线创建失败？

A: 确保源节点和目标节点都存在，且 ID 正确。检查是否触发了外键约束。

### Q: 3D 星云视图加载慢？

A: 大量节点会导致性能问题，建议在 500+ 节点时使用 2D 视图。

### Q: 数据保存失败？

A: 检查后端日志，查看数据库连接是否正常，确认 MySQL 服务运行中。

### Q: 如何使用 uv 管理后端依赖？

A: 在 backend 目录运行 `uv add <package>` 来添加新依赖，或 `uv sync` 来同步所有依赖。

## 📈 性能优化建议

1. **大量节点** - 使用主题过滤，减少渲染数量
2. **3D 视图** - 限制节点数量在 200 以内
3. **样式缓存** - 复用预设样式而非每个节点独立样式
4. **原子操作** - 利用自动保存特性，减少不必要的数据传输

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 👥 作者

New Mind Team

## 🙏 致谢

- Vue.js 团队 - 优秀的渐进式框架
- Element Plus 团队 - 精美的 UI 组件库
- D3.js 社区 - 强大的数据可视化库
- FastAPI 团队 - 现代高效的 Python Web 框架
- Astral 团队 - 极速的 Python 包管理工具 uv

---

**项目版本**: 1.0.0  
**最后更新**: 2026-05-09  
**文档语言**: 简体中文
