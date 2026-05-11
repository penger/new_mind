# 回滚文档 - Vanilla JS 版本

## 概述
本文档记录了 2026-04-22 的前端架构状态，可用于回滚 Vue 3 重构。

## 技术栈
- **前端框架**: 原生 JavaScript (ES6+)
- **图形库**: D3.js v7
- **状态管理**: GraphEditor 类内部状态
- **构建工具**: 无 (直接使用浏览器)
- **样式**: 原生 CSS

## 文件结构
```
frontend/
├── index.html          # 主 HTML 文件 (213 行)
├── css/
│   └── style.css       # 样式表 (178 行)
├── js/
│   └── app.js          # 主应用逻辑 (652 行)
└── nginx.conf          # Nginx 代理配置
```

## 核心代码架构

### GraphEditor 类 (app.js)
```javascript
class GraphEditor {
    constructor() {
        this.nodes = [];           // 节点数据
        this.links = [];            // 连线数据
        this.nodeStyles = [];      // 节点样式
        this.edgeStyles = [];      // 连线样式
        this.themes = [];          // 主题配置
        this.mode = 'view';        // view/edit 模式
        this.visibleThemes = new Set();
        this.activeThemeFilter = null;
        // ...
    }
}
```

### API 接口
- `GET /api/data` - 获取完整图谱数据
- `PUT /api/data` - 全量更新图谱数据

## 主要功能
1. **画布交互**: D3.js 力导向图布局
2. **节点/连线管理**: CRUD 操作
3. **主题过滤**: 单选下拉框，按 ID 排序
4. **属性面板**: 侧边栏编辑节点/连线属性
5. **资源管理**: 主题、节点样式、连线样式管理
6. **自动保存**: 所有操作自动同步到数据库

## 回滚步骤

### 方式一: 直接恢复文件
```bash
# 停止当前服务
docker-compose down

# 恢复前端文件
rm -rf /root/workspace/new_mind/frontend/*
cp -r /root/workspace/new_mind/.rollback/vanilla_js_backup/frontend/* /root/workspace/new_mind/frontend/

# 重启服务
docker-compose up -d
```

### 方式二: Git 回滚 (如果使用 Git)
```bash
cd /root/workspace/new_mind
git checkout <commit-hash>
```

## 备份时间
2026-04-22T09:51:00+08:00

## 相关文档
- 主项目 README: `/root/workspace/new_mind/README.md`
- 后端 API 文档: `/root/workspace/new_mind/backend/app/routers/graphs.py`
