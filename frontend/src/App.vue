<template>
  <div class="app-container">
    <el-header>
      <div class="header-left">
        <h1>关系图谱专业版</h1>
        <el-switch 
          v-model="isEditing" 
          active-text="编辑模式" 
          inactive-text="浏览模式" 
          @change="handleEditChange" 
          style="margin-left: 20px;" 
        />
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="header-right">
        <el-radio-group v-model="viewType" size="default">
          <el-radio-button value="2d">平面图</el-radio-button>
          <el-radio-button value="3d">星云图</el-radio-button>
        </el-radio-group>
        <el-divider direction="vertical" />
        <el-button @click="openResourceManager">⚙️ 资源管理</el-button>
      </div>
    </el-header>

    <div class="main-wrapper">
      <el-aside width="280px">
        <el-card class="sidebar-card">
          <template #header><span class="card-title">图层控制</span></template>
          <el-form label-position="top" size="small">
            <el-form-item label="主题过滤">
              <el-select v-model="activeThemeFilter" @change="onThemeFilterChangeHandler" style="width: 100%">
                <el-option v-for="theme in themes" :key="theme.id" :label="theme.name" :value="theme.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="sidebar-card" style="margin-top: 12px;">
          <template #header><span class="card-title">选中详情</span></template>
          <div v-if="!selectedNodes || selectedNodes.length === 0" class="empty-text">{{ isEditing ? '点击节点进行编辑' : '点击节点查看详情' }}</div>
          <div v-else v-for="node in selectedNodes" :key="node.id" class="selection-item">
            <el-tag size="small" :style="{ backgroundColor: node.style?.color || getNodeStyle(node.nodeStyleId)?.color }">●</el-tag>
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div v-if="node.content && node.content.trim()" class="node-content">{{ node.content }}</div>
              <div v-else-if="!isEditing" class="empty-content">暂无内容描述</div>
            </div>
          </div>
        </el-card>
      </el-aside>

      <main class="graph-area" ref="graphArea">
        <Graph2D
          v-if="viewType === '2d'"
          :key="'graph-2d-' + activeThemeFilter + '-' + viewType"
          :nodes="nodes"
          :links="links"
          :nodeStyles="nodeStyles"
          :edgeStyles="edgeStyles"
          :visibleThemes="visibleThemes"
          :physicsEnabled="physicsEnabled"
          :mode="isEditing ? 'edit' : 'view'"
          @node-click="onNodeClick"
          @node-hover="onNodeHover"
          @node-leave="onNodeLeave"
          @node-add="onEditorNodeAdd"
          @edge-add="onEditorEdgeAdd"
          @edge-click="onEdgeClick"
        />

        <Graph3DView v-if="viewType === '3d'" :nodes="nodes" :links="links" :nodeStyles="nodeStyles" :edgeStyles="edgeStyles" :visibleThemes="visibleThemes" @node-click="onNodeClick" />

        <div class="info-card" v-show="isInfoCardOpen" :style="{ left: infoCardPos.x + 'px', top: infoCardPos.y + 'px' }">
          <div class="info-card-header"><b>{{ hoverItem.label }}</b></div>
          <div class="info-card-body">{{ hoverItem.content }}</div>
        </div>
      </main>

      <el-drawer v-model="isPanelOpen" :title="isEditing ? '配置节点样式与信息' : '属性详情'" direction="rtl" size="380px">
        <el-form label-position="top" :disabled="!isEditing" style="padding: 0 20px;">
          <el-divider content-position="left">基础属性</el-divider>
          <el-form-item label="标签"><el-input v-model="editingItem.label" /></el-form-item>
          <el-form-item label="描述"><el-input v-model="editingItem.content" type="textarea" :rows="3" /></el-form-item>

          <template v-if="editingItem.type === 'node'">
            <el-divider content-position="left">视觉定制</el-divider>
            <el-form-item label="关联预设模板 (仅显示当前主题默认样式)">
              <el-select 
                v-model="editingItem.nodeStyleId" 
                @change="onNodePresetChange" 
                style="width: 100%"
                :disabled="currentThemeNodeStyles.length === 0"
              >
                <template v-if="currentThemeNodeStyles.length > 0">
                  <el-option 
                    v-for="s in currentThemeNodeStyles" 
                    :key="s.id" 
                    :label="s.name" 
                    :value="s.id"
                  >
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span :style="{ color: s.color, fontSize: '16px' }">●</span>
                      <span>{{ s.name }}</span>
                      <el-tag v-if="s.id === editingItem.nodeStyleId" size="small" type="success">已选</el-tag>
                    </div>
                  </el-option>
                </template>
                <template v-else>
                  <el-option :disabled="true" value="">
                    当前主题未设置默认节点样式
                  </el-option>
                </template>
              </el-select>
              <div v-if="currentThemeId && currentThemeNodeStyles.length === 0" class="theme-info-hint">
                提示：当前主题 <strong>{{ themes.value?.find(t => t.id === currentThemeId)?.name }}</strong> 未配置默认节点样式
              </div>
            </el-form-item>
            <el-row :gutter="15">
              <el-col :span="10">
                <el-form-item label="颜色"><el-color-picker v-model="editingItem.style.color" /></el-form-item>
              </el-col>
              <el-col :span="14">
                <el-form-item label="形状">
                  <el-select v-model="editingItem.style.shape">
                    <el-option label="圆形" value="circle" /><el-option label="矩形" value="square" /><el-option label="菱形" value="diamond" /><el-option label="星形" value="star" /><el-option label="三角形" value="triangle" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="尺寸"><el-slider v-model="editingItem.size" :min="5" :max="50" /></el-form-item>
          </template>

          <template v-if="editingItem.type === 'edge'">
            <el-divider content-position="left">连线样式</el-divider>
            <el-form-item label="关联预设样式 (仅显示当前主题默认样式)">
              <el-select 
                v-model="editingItem.edgeStyleId" 
                @change="onEdgePresetChange" 
                style="width: 100%"
                :disabled="currentThemeEdgeStyles.length === 0"
              >
                <template v-if="currentThemeEdgeStyles.length > 0">
                  <el-option 
                    v-for="s in currentThemeEdgeStyles" 
                    :key="s.id" 
                    :label="s.name" 
                    :value="s.id"
                  >
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span :style="{ backgroundColor: s.color || '#999', display: 'inline-block', width: '16px', height: '4px', borderRadius: '2px' }"></span>
                      <span>{{ s.name }}</span>
                      <span style="color: #909399; font-size: 12px;">({{ getLineStyleName(s.line_style) }})</span>
                      <el-tag v-if="s.id === editingItem.edgeStyleId" size="small" type="success">已选</el-tag>
                    </div>
                  </el-option>
                </template>
                <template v-else>
                  <el-option :disabled="true" value="">
                    当前主题未设置默认边样式
                  </el-option>
                </template>
              </el-select>
              <div v-if="currentThemeId && currentThemeEdgeStyles.length === 0" class="theme-info-hint">
                提示：当前主题 <strong>{{ themes.value?.find(t => t.id === currentThemeId)?.name }}</strong> 未配置默认边样式
              </div>
            </el-form-item>
            <el-row :gutter="15">
              <el-col :span="12">
                <el-form-item label="颜色"><el-color-picker v-model="editingItem.style.color" /></el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="线宽"><el-input-number v-model="editingItem.style.width" :min="1" :max="10" /></el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="线型">
              <el-select v-model="editingItem.style.style">
                <el-option label="实线" value="solid" /><el-option label="虚线" value="dashed" />
              </el-select>
            </el-form-item>
          </template>

          <div v-if="isEditing" style="margin-top: 30px; display: flex; gap: 12px;">
            <el-button type="primary" @click="saveProperties" style="flex: 1;">保存修改</el-button>
            <el-button type="danger" @click="deleteSelected" style="flex: 1;">删除</el-button>
          </div>
        </el-form>
      </el-drawer>

      <ResourceManager
        v-model="isResourceManagerOpen"
        :themes="themes"
        :nodeStyles="nodeStyles"
        :edgeStyles="edgeStyles"
        @refresh="handleResourceRefresh"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useGraphCore } from './composables/useGraphCore'
import Graph2D from './components/Graph2D.vue'
import Graph3DView from './components/Graph3DView.vue'
import ResourceManager from './components/ResourceManager.vue'

const {
  nodes, links, nodeStyles, edgeStyles, themes, activeThemeFilter, visibleThemes,
  physicsEnabled, getNodeStyle, fetchDataFromServer, addNode, addEdge,
  updateNodeToServer, updateEdgeToServer, onThemeFilterChange, deleteNodesAndRelatedEdges, deleteEdge, refreshKey
} = useGraphCore()

const viewType = ref('2d'), isEditing = ref(false), isPanelOpen = ref(false), isInfoCardOpen = ref(false)
const isResourceManagerOpen = ref(false)
const infoCardPos = reactive({ x: 0, y: 0 }), hoverItem = reactive({ label: '', content: '' })
const editingItem = reactive({ id: '', label: '', content: '', style: {}, type: 'node', size: 18 })
const selectedNodeIds = ref([]), graphArea = ref(null)

// 安全计算选中节点
const selectedNodes = computed(() => {
  const currentNodes = nodes.value || [];
  const ids = selectedNodeIds.value || [];
  return currentNodes.filter(n => ids.includes(n.id));
})

const statusText = computed(() => isEditing.value ? '✏️ 编辑模式: 位置已锁定，可手动调整' : '👁️ 浏览模式: 布局已自动优化')

// 获取当前编辑节点的主题ID
const currentThemeId = computed(() => {
  if (!editingItem.id) return null
  if (editingItem.type === 'node') {
    // 如果是节点，返回节点的themeId
    const node = nodes.value?.find(n => n.id === editingItem.id)
    return node?.themeId || null
  } else {
    // 如果是边，返回边的themeId
    const edge = links.value?.find(e => e.id === editingItem.id)
    return edge?.themeId || null
  }
})

// 获取当前主题的默认节点样式列表
const currentThemeNodeStyles = computed(() => {
  if (!currentThemeId.value) return []
  
  const theme = themes.value?.find(t => t.id === currentThemeId.value)
  if (!theme || !theme.defaultNodeStyleIds || theme.defaultNodeStyleIds.length === 0) return []
  
  // 根据主题的defaultNodeStyleIds过滤nodeStyles
  return nodeStyles.value?.filter(style => 
    theme.defaultNodeStyleIds.includes(style.id)
  ) || []
})

// 获取当前主题的默认边样式列表
const currentThemeEdgeStyles = computed(() => {
  if (!currentThemeId.value) return []
  
  const theme = themes.value?.find(t => t.id === currentThemeId.value)
  if (!theme || !theme.defaultEdgeStyleIds || theme.defaultEdgeStyleIds.length === 0) return []
  
  // 根据主题的defaultEdgeStyleIds过滤edgeStyles
  return edgeStyles.value?.filter(style => 
    theme.defaultEdgeStyleIds.includes(style.id)
  ) || []
})

const onNodeClick = (item) => {
  const isN = item.id?.startsWith('N');
  selectedNodeIds.value = isN ? [item.id] : [];
  Object.assign(editingItem, { ...item, type: isN ? 'node' : 'edge', style: item.style ? { ...item.style } : {} });
  if (isEditing.value) isPanelOpen.value = true
}

const onNodeHover = ({ event, node }) => {
  if (isEditing.value) return;
  hoverItem.label = node.label;
  hoverItem.content = node.content || '暂无详细描述';
  const rect = graphArea.value.getBoundingClientRect();
  infoCardPos.x = event.clientX - rect.left + 15;
  infoCardPos.y = event.clientY - rect.top + 10;
  isInfoCardOpen.value = true
}

const onNodeLeave = () => { isInfoCardOpen.value = false }
const handleEditChange = (v) => { if (v && viewType.value === '3d') viewType.value = '2d' }
const onEditorNodeAdd = async ({ x, y }) => { const n = await addNode(x, y); if (n) onNodeClick(n) }
const onEditorEdgeAdd = async ({ source, target }) => { await addEdge(source, target); ElMessage.success('成功建立逻辑关系') }
const onEdgeClick = (edge) => { selectedNodeIds.value = []; Object.assign(editingItem, { ...edge, type: 'edge', style: edge.style ? { ...edge.style } : {} }); isPanelOpen.value = true }

const saveProperties = async () => {
  if (editingItem.type === 'node') {
    const n = (nodes.value || []).find(x => x.id === editingItem.id);
    if (n) { Object.assign(n, editingItem); await updateNodeToServer(n) }
  } else if (editingItem.type === 'edge') {
    const e = (links.value || []).find(x => x.id === editingItem.id);
    if (e) { Object.assign(e, editingItem); await updateEdgeToServer(e) }
  }
  isPanelOpen.value = false;
  ElMessage.success('数据已同步至数据库')
}

const deleteSelected = async () => {
  // 如果是节点，使用现有的节点删除功能
  if (editingItem.type === 'node' && selectedNodeIds.value.length > 0) {
    await deleteNodesAndRelatedEdges(selectedNodeIds.value);
    selectedNodeIds.value = []; isPanelOpen.value = false;
    ElMessage.success('节点已删除');
  } 
  // 如果是边，使用边删除功能
  else if (editingItem.type === 'edge' && editingItem.id) {
    await deleteEdge(editingItem.id);
    isPanelOpen.value = false;
    ElMessage.success('连线已删除');
  }
  // 没有选中任何东西时显示提示
  else {
    ElMessage.warning('请先选中要删除的元素');
  }
}

const getEdgeDashArray = (style) => {
  if (style === 'dashed') return '8,4'
  if (style === 'dotted') return '2,4'
  return ''
}
const getLineStyleName = (style) => {
  const map = { solid: '实线', dashed: '虚线', dotted: '点线' }
  return map[style] || style
}
const onNodePresetChange = (id) => { 
  const p = currentThemeNodeStyles.value?.find(s => s.id === id) || getNodeStyle(id); 
  if (p) { 
    editingItem.style.color = p.color; 
    editingItem.style.shape = p.shape 
  } 
}
const onEdgePresetChange = (id) => { 
  const s = edgeStyles.value?.find(x => x.id === id); 
  if (s) { 
    editingItem.style.color = s.color; 
    editingItem.style.width = s.width || 2; 
    editingItem.style.style = s.line_style || 'solid'; 
  } 
}
const onThemeFilterChangeHandler = () => onThemeFilterChange(activeThemeFilter.value)
const openResourceManager = () => { isResourceManagerOpen.value = true }
const handleResourceRefresh = async () => { await fetchDataFromServer() }

onMounted(async () => { await fetchDataFromServer() })
</script>

<style>
/* 终极专业版 CSS 布局 */
html, body, #app { margin: 0; padding: 0; height: 100vh; width: 100%; overflow: hidden; font-family: 'Segoe UI', system-ui, sans-serif; }
:root { --header-h: 60px; --border-color: #dcdfe6; }

.app-container { display: flex; flex-direction: column; height: 100vh; width: 100%; }
.el-header { height: var(--header-h); flex-shrink: 0; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; background: #fff; z-index: 1000; }
.main-wrapper { display: flex; flex: 1; min-height: 0; width: 100%; overflow: hidden; }
.el-aside { background: #fff; border-right: 1px solid var(--border-color); overflow-y: auto; }
.graph-area { flex: 1; position: relative; min-width: 0; background: #f5f7fa; overflow: hidden; }

.graph-area svg { display: block; width: 100%; height: 100%; }
.info-card { position: absolute; background: rgba(255,255,255,0.95); border-radius: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 10px; z-index: 2000; pointer-events: none; border: 1px solid #ebeef5; max-width: 250px; }
.empty-text { padding: 40px; text-align: center; color: #909399; font-size: 13px; }

/* 主题信息提示样式 */
.theme-info-hint {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border: 1px solid #d1efff;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.theme-info-hint strong {
  color: #409eff;
  font-weight: 600;
}

/* 样式选择器中标签样式 */
.el-select .el-tag {
  margin-left: auto;
}

/* 选中详情样式优化 */
.selection-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.selection-item:last-child {
  border-bottom: none;
}

.node-info {
  margin-left: 8px;
  flex: 1;
  min-width: 0; /* 允许文本换行 */
}

.node-label {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  word-break: break-word;
}

.node-content {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  background-color: #f8f9fa;
  padding: 6px 8px;
  border-radius: 4px;
  border-left: 3px solid #409eff;
  margin-top: 4px;
  word-break: break-word;
  white-space: pre-line; /* 保留换行符 */
}

.empty-content {
  font-size: 11px;
  color: #909399;
  font-style: italic;
  margin-top: 2px;
}
</style>