<template>
  <div class="app-container">
    <el-header>
      <div class="header-left">
        <h1>关系图谱专业版</h1>
        <el-tag :type="mode === 'edit' ? 'warning' : 'primary'" size="small">
          {{ mode === 'edit' ? '✏️ 编辑模式' : '👁️ 浏览模式' }}
        </el-tag>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="header-right">
        <el-radio-group v-model="currentMode" size="default">
          <el-radio-button value="view-2d">👁️ 普通浏览</el-radio-button>
          <el-radio-button value="view-3d" class="white-bg-button">✨ 星图浏览</el-radio-button>
          <el-radio-button value="edit">✏️ 编辑</el-radio-button>
        </el-radio-group>
        <el-button @click="openResourceManager">⚙️ 资源管理</el-button>
      </div>
    </el-header>

    <div class="main-wrapper">
      <el-aside width="260px">
        <el-card class="sidebar-card">
          <template #header>
            <span class="card-title">图层设置</span>
          </template>

          <el-form label-position="top" size="small">
            <el-form-item label="图层过滤 (按主题)">
              <el-select v-model="activeThemeFilter" @change="onThemeFilterChange" style="width: 100%">
                <el-option v-for="theme in themes" :key="theme.id" :label="theme.name" :value="theme.id" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="showLinkLabels" @change="render">显示连线标签</el-checkbox>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="physicsEnabled" @change="onPhysicsToggle">启用物理模拟</el-checkbox>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="sidebar-card" style="margin-top: 12px;">
          <template #header>
            <span class="card-title">当前选中元素</span>
          </template>

          <div v-if="selectedNodes.length === 0 && selectedLinks.length === 0" class="empty-text">
            当前无选中项
          </div>
          <div v-for="node in selectedNodes" :key="node.id" class="selection-item">
            <el-tag size="small" :style="{ backgroundColor: getNodeStyle(node.nodeStyleId)?.color, borderColor: getNodeStyle(node.nodeStyleId)?.color }">
              ●
            </el-tag>
            {{ node.label }}
          </div>
          <div v-for="link in selectedLinks" :key="link.id" class="selection-item">
            <el-tag size="small" type="info">➖</el-tag>
            {{ getLinkSourceLabel(link) }} ➝ {{ getLinkTargetLabel(link) }}
          </div>
        </el-card>
      </el-aside>

      <main class="graph-area" ref="graphArea">
        <!-- 2D 视图 -->
        <svg id="graph-svg" ref="svgRef" v-show="viewMode === '2d'">
          <defs>
            <marker id="arrowhead" viewBox="0 -5 10 10" refX="20" refY="0" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,-5L10,0L0,5" fill="context-stroke" />
            </marker>
            <marker id="arrowhead-selected" viewBox="0 -5 10 10" refX="20" refY="0" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,-5L10,0L0,5" fill="#e74c3c" />
            </marker>
          </defs>
          <g id="main-group" ref="mainGroup">
            <line id="ghost-line" x1="0" y1="0" x2="0" y2="0" />
            <g id="links-group"></g>
            <g id="nodes-group"></g>
            <g id="labels-group"></g>
          </g>
          <rect id="selection-box" x="0" y="0" width="0" height="0" style="pointer-events: none;"></rect>
        </svg>
        <!-- 3D 星云视图 -->
        <div id="nebula-container" v-show="viewMode === '3d'" style="width: 100%; height: 100%;"></div>
        <div id="info-card" class="info-card" v-show="isInfoCardOpen" :style="{ left: infoCardPos.x + 'px', top: infoCardPos.y + 'px' }">
          <div class="info-card-header">
            <span class="info-card-title">{{ editingType === 'node' ? '节点信息' : '连线信息' }}</span>
            <span class="info-card-close" @click="closeInfoCard">×</span>
          </div>
          <div class="info-card-body">
            <div class="info-item"><span class="info-label">标签：</span>{{ editingItem.label }}</div>
            <div class="info-item"><span class="info-label">主题：</span>{{ getThemeName(editingItem.themeId) }}</div>
            <div v-if="editingItem.content" class="info-item info-content"><span class="info-label">详情：</span>{{ editingItem.content }}</div>
          </div>
        </div>
      </main>

      <el-drawer v-model="isPanelOpen" :title="mode === 'view' ? '查看属性' : '属性与样式分配'" direction="rtl" size="320px" :before-close="closeProperties" :modal="mode === 'edit'">
        <el-form label-position="top">
          <el-form-item label="标签名称">
            <el-input v-model="editingItem.label" placeholder="请输入标签名称" />
          </el-form-item>

          <el-form-item label="详情描述">
            <el-input v-model="editingItem.content" type="textarea" :rows="3" placeholder="请输入详情描述" />
          </el-form-item>

          <template v-if="editingType === 'node'">
            <el-divider content-position="left">样式预设</el-divider>
            <el-form-item label="快捷样式">
              <el-select v-model="editingItem.nodeStyleId" style="width: 100%" @change="onNodeStylePresetChange">
                <el-option v-for="ns in nodeStyles" :key="ns.id" :label="ns.name" :value="ns.id" />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">样式预览</el-divider>
            <div class="style-preview">
              <svg width="80" height="80" viewBox="-50 -50 100 100">
                <path :d="getSymbolGenerator(editingItem.style.shape || 'circle', 25)" :fill="editingItem.style.color || '#3498db'" :fill-opacity="editingItem.style.opacity || 1" stroke="white" stroke-width="2" />
              </svg>
            </div>

            <el-divider content-position="left">自定义样式</el-divider>
            <el-form-item label="颜色">
              <div style="display: flex; gap: 8px; align-items: center;">
                <input type="color" v-model="editingItem.style.color" style="width: 40px; height: 32px; border: 1px solid #dcdfe6; border-radius: 4px; cursor: pointer;" />
                <el-input v-model="editingItem.style.color" style="width: 100px;" />
              </div>
            </el-form-item>
            <el-form-item label="形状">
              <el-select v-model="editingItem.style.shape" style="width: 100%">
                <el-option value="circle" label="圆形" />
                <el-option value="square" label="矩形" />
                <el-option value="triangle" label="三角形" />
                <el-option value="diamond" label="菱形" />
                <el-option value="star" label="星形" />
              </el-select>
            </el-form-item>
            <el-form-item label="透明度">
              <el-slider v-model="editingItem.style.opacity" :min="0.1" :max="1" :step="0.1" />
            </el-form-item>
          </template>

          <template v-else>
            <el-divider content-position="left">样式预设</el-divider>
            <el-form-item label="快捷样式">
              <el-select v-model="editingItem.edgeStyleId" style="width: 100%" @change="onEdgeStylePresetChange">
                <el-option v-for="es in edgeStyles" :key="es.id" :label="es.name" :value="es.id" />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">样式预览</el-divider>
            <div class="style-preview">
              <svg width="80" height="40" viewBox="0 0 80 40">
                <line x1="5" y1="20" x2="75" y2="20" :stroke="editingItem.style.color || '#95a5a6'" :stroke-width="editingItem.style.width || 2" :stroke-dasharray="editingItem.style.style === 'dashed' ? '6,6' : 'none'" />
              </svg>
            </div>

            <el-divider content-position="left">自定义样式</el-divider>
            <el-form-item label="颜色">
              <div style="display: flex; gap: 8px; align-items: center;">
                <input type="color" v-model="editingItem.style.color" style="width: 40px; height: 32px; border: 1px solid #dcdfe6; border-radius: 4px; cursor: pointer;" />
                <el-input v-model="editingItem.style.color" style="width: 100px;" />
              </div>
            </el-form-item>
            <el-form-item label="线宽">
              <el-input-number v-model="editingItem.style.width" :min="1" :max="10" />
            </el-form-item>
            <el-form-item label="线型">
              <el-select v-model="editingItem.style.style" style="width: 100%">
                <el-option value="solid" label="实线" />
                <el-option value="dashed" label="虚线" />
              </el-select>
            </el-form-item>
          </template>

          <el-form-item style="margin-top: 30px; display: flex; gap: 12px;">
            <el-button type="primary" style="flex: 1;" @click="saveProperties">确认修改</el-button>
            <el-button type="danger" style="flex: 1;" @click="deleteSelected">删除</el-button>
          </el-form-item>
        </el-form>
      </el-drawer>
    </div>

    <!-- 资源管理中心 -->
    <el-dialog v-model="isResourceManagerOpen" title="资源管理中心" width="850px" :close-on-click-modal="false">
      <el-tabs v-model="rmActiveTab" @tab-change="rmSwitchTab">
        <el-tab-pane label="🎨 主题管理" name="themes">
          <div class="resource-manager">
            <div class="rm-list">
              <div class="rm-list-header">
                <span>列表</span>
                <el-button size="small" @click="rmCreateNew">+ 新建</el-button>
              </div>
              <div class="rm-list-content">
                <div v-for="item in themes" :key="item.id"
                     class="rm-item" :class="{ active: item.id === rmEditingId }"
                     @click="rmSelectItem(item.id)">
                  <div class="rm-color-dot" :style="{ background: getNodeStyle(item.defaultNodeStyleId)?.color || '#ccc' }"></div>
                  <span>{{ item.name }}</span>
                </div>
              </div>
            </div>
            <div class="rm-edit" v-if="rmEditingId">
              <el-form label-position="top">
                <el-form-item label="名称">
                  <el-input v-model="rmEditingItem.name" />
                </el-form-item>

                <template v-if="rmActiveTab === 'themes'">
                  <el-divider content-position="left">默认应用样式</el-divider>
                  <el-form-item label="默认节点样式">
                    <el-select v-model="rmEditingItem.defaultNodeStyleId" style="width: 100%">
                      <el-option v-for="ns in nodeStyles" :key="ns.id" :label="ns.name" :value="ns.id" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="默认连线样式">
                    <el-select v-model="rmEditingItem.defaultEdgeStyleId" style="width: 100%">
                      <el-option v-for="es in edgeStyles" :key="es.id" :label="es.name" :value="es.id" />
                    </el-select>
                  </el-form-item>
                </template>

                <el-form-item style="margin-top: 30px;">
                  <el-button type="primary" @click="rmSave">保存更改</el-button>
                  <el-button type="danger" @click="rmDeleteCurrent">删除此项</el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="🟣 节点样式" name="nodeStyles">
          <div class="resource-manager">
            <div class="rm-list">
              <div class="rm-list-header">
                <span>列表</span>
                <el-button size="small" @click="rmCreateNew">+ 新建</el-button>
              </div>
              <div class="rm-list-content">
                <div v-for="item in nodeStyles" :key="item.id"
                     class="rm-item" :class="{ active: item.id === rmEditingId }"
                     @click="rmSelectItem(item.id)">
                  <div class="rm-color-dot" :style="{ background: item.color }"></div>
                  <span>{{ item.name }}</span>
                </div>
              </div>
            </div>
            <div class="rm-edit" v-if="rmEditingId">
              <el-form label-position="top">
                <el-form-item label="名称">
                  <el-input v-model="rmEditingItem.name" />
                </el-form-item>
                <el-divider content-position="left">视觉表现</el-divider>
                <el-form-item label="填充颜色">
                  <el-color-picker v-model="rmEditingItem.color" />
                </el-form-item>
                <el-form-item label="节点形状">
                  <el-select v-model="rmEditingItem.shape" style="width: 100%">
                    <el-option value="circle" label="圆形" />
                    <el-option value="square" label="矩形" />
                    <el-option value="triangle" label="三角形" />
                    <el-option value="diamond" label="菱形" />
                    <el-option value="star" label="星形" />
                  </el-select>
                </el-form-item>
                <el-form-item label="透明度">
                  <el-slider v-model="rmEditingItem.opacity" :min="0.1" :max="1" :step="0.1" />
                </el-form-item>
                <el-form-item style="margin-top: 30px;">
                  <el-button type="primary" @click="rmSave">保存更改</el-button>
                  <el-button type="danger" @click="rmDeleteCurrent">删除此项</el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="➖ 连线样式" name="edgeStyles">
          <div class="resource-manager">
            <div class="rm-list">
              <div class="rm-list-header">
                <span>列表</span>
                <el-button size="small" @click="rmCreateNew">+ 新建</el-button>
              </div>
              <div class="rm-list-content">
                <div v-for="item in edgeStyles" :key="item.id"
                     class="rm-item" :class="{ active: item.id === rmEditingId }"
                     @click="rmSelectItem(item.id)">
                  <div class="rm-color-dot" :style="{ background: item.color }"></div>
                  <span>{{ item.name }}</span>
                </div>
              </div>
            </div>
            <div class="rm-edit" v-if="rmEditingId">
              <el-form label-position="top">
                <el-form-item label="名称">
                  <el-input v-model="rmEditingItem.name" />
                </el-form-item>
                <el-divider content-position="left">视觉表现</el-divider>
                <el-form-item label="线条颜色">
                  <el-color-picker v-model="rmEditingItem.color" />
                </el-form-item>
                <el-form-item label="线条样式">
                  <el-select v-model="rmEditingItem.style" style="width: 100%">
                    <el-option value="solid" label="实线" />
                    <el-option value="dashed" label="虚线" />
                  </el-select>
                </el-form-item>
                <el-form-item style="margin-top: 30px;">
                  <el-button type="primary" @click="rmSave">保存更改</el-button>
                  <el-button type="danger" @click="rmDeleteCurrent">删除此项</el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as THREE from 'three'
import ForceGraph3D from '3d-force-graph'
import SpriteText from 'three-spritetext'

const API_BASE_URL = '/api'

// State
const nodes = ref([])
const links = ref([])
const nodeStyles = ref([])
const edgeStyles = ref([])
const themes = ref([])

const mode = ref('view')
const activeThemeFilter = ref(null)

const isPanelOpen = ref(false)
const editingItem = reactive({
  id: '', label: '', content: '', themeId: null, nodeStyleId: null, edgeStyleId: null, width: 2, size: 22, style: {}
})
const editingType = ref(null)

const isInfoCardOpen = ref(false)
const infoCardPos = reactive({ x: 0, y: 0 })

const isResourceManagerOpen = ref(false)
const rmActiveTab = ref('themes')
const rmEditingId = ref(null)
const rmEditingItem = reactive({})

const nodeIdCounter = ref(1)
const linkIdCounter = ref(1)
const resourceIdCounter = ref(1)

const isLinking = ref(false)
const linkSourceNode = ref(null)
const hoveredNode = ref(null)

// 框选状态
const isBoxSelecting = ref(false)
const boxStart = ref({ x: 0, y: 0 })

// 悬停高亮状态
const highlightedNodes = ref(new Set())
const highlightedLinks = ref(new Set())

// 计算相邻节点和连线
const computeHighlight = (nodeId) => {
  const adjacentNodeIds = new Set()
  const adjacentLinkIds = new Set()
  
  links.value.forEach(l => {
    const sourceId = typeof l.source === 'object' ? l.source.id : l.source
    const targetId = typeof l.target === 'object' ? l.target.id : l.target
    if (sourceId === nodeId || targetId === nodeId) {
      adjacentNodeIds.add(sourceId)
      adjacentNodeIds.add(targetId)
      adjacentLinkIds.add(l.id)
    }
  })
  
  highlightedNodes.value = adjacentNodeIds
  highlightedLinks.value = adjacentLinkIds
}

const clearHighlight = () => {
  highlightedNodes.value = new Set()
  highlightedLinks.value = new Set()
}

const updateHighlightStyles = () => {
  const mainGSel = d3.select(mainGroup.value)
  
  mainGSel.selectAll('.node')
    .attr('fill-opacity', d => {
      if (d.selected && highlightedNodes.value.has(d.id)) return 1
      if (highlightedNodes.value.has(d.id)) return 0.9
      if (d.selected) return 0.85
      return d.style?.opacity ?? getNodeStyle(d.nodeStyleId)?.opacity ?? 1
    })
    .attr('stroke', d => {
      if (d.selected && highlightedNodes.value.has(d.id)) return '#ffd700'
      if (highlightedNodes.value.has(d.id)) return '#ff8c00'
      return 'white'
    })
    .attr('stroke-width', d => {
      if (d.selected && highlightedNodes.value.has(d.id)) return 6
      if (highlightedNodes.value.has(d.id)) return 5
      return 4
    })
  
  mainGSel.selectAll('.link').attr('stroke', d => {
    if (d.selected) return '#ff6b6b'
    if (highlightedLinks.value.has(d.id)) return '#ff8c00'
    return d.style?.color ?? getEdgeStyle(d.edgeStyleId)?.color ?? '#95a5a6'
  }).attr('stroke-width', d => {
    if (d.selected) return (d.style?.width ?? d.width) + 2
    if (highlightedLinks.value.has(d.id)) return (d.style?.width ?? d.width) + 2
    return d.style?.width ?? d.width
  }).attr('opacity', d => {
    if (d.selected || highlightedLinks.value.has(d.id)) return 1
    return 0.6
  })
}

const svgRef = ref(null)
const mainGroup = ref(null)

// 3D 星云视图
const viewMode = ref('2d')
const currentMode = ref('view-2d')
let nebulaGraph = null

let simulation = null
let zoom = null
let currentTransform = d3.zoomIdentity

const statusText = computed(() => mode.value === 'edit' ? '✏️ 编辑模式: 双击添加节点，Shift+拖拽连线，Shift+框选节点' : '👁️ 浏览模式: 布局自动调整中，可自由缩放和平移')
const visibleThemes = ref(new Set())
const showLinkLabels = ref(true)
const physicsEnabled = ref(true)

const selectedNodes = computed(() => nodes.value.filter(n => n.selected && visibleThemes.value.has(n.themeId)))
const selectedLinks = computed(() => links.value.filter(l => {
  const sTheme = typeof l.source === 'object' ? l.source.themeId : nodes.value.find(n => n.id === l.source)?.themeId
  const tTheme = typeof l.target === 'object' ? l.target.themeId : nodes.value.find(n => n.id === l.target)?.themeId
  return l.selected && visibleThemes.value.has(sTheme) && visibleThemes.value.has(tTheme)
}))

const rmListData = computed(() => rmActiveTab.value === 'themes' ? themes.value : (rmActiveTab.value === 'nodeStyles' ? nodeStyles.value : edgeStyles.value))

const getNodeStyle = (id) => nodeStyles.value.find(s => s.id === id) || nodeStyles.value[0]
const getEdgeStyle = (id) => edgeStyles.value.find(s => s.id === id) || edgeStyles.value[0]

const getSymbolGenerator = (shape, size) => {
  let type
  switch (shape) {
    case 'square': type = d3.symbolSquare; break
    case 'triangle': type = d3.symbolTriangle; break
    case 'star': type = d3.symbolStar; break
    case 'diamond': type = d3.symbolDiamond; break
    case 'circle': default: type = d3.symbolCircle
  }
  return d3.symbol().type(type).size(size * size * 3.14)()
}

const getLinkSourceLabel = (link) => (typeof link.source === 'object' ? link.source : nodes.value.find(n => n.id === link.source))?.label || '节点'
const getLinkTargetLabel = (link) => (typeof link.target === 'object' ? link.target : nodes.value.find(n => n.id === link.target))?.label || '节点'
const getThemeName = (themeId) => themes.value.find(t => t.id === themeId)?.name || '未知'

// ===============================================
// 统一的依赖加载，使用本地安装的 Three.js 模块
// ===============================================
const load3DLibraries = async () => {
  if (window._threeInstance && window._forceGraphInstance) {
    return { 
      THREE: window._threeInstance, 
      ForceGraph3D: window._forceGraphInstance,
      SpriteText: window._spriteTextInstance 
    }
  }

  // 使用本地安装的模块
  window._threeInstance = THREE
  window._forceGraphInstance = ForceGraph3D
  window._spriteTextInstance = SpriteText

  return { THREE, ForceGraph3D, SpriteText }
}

let nebulaRetryCount = 0
const initNebulaGraph = async () => {
  nebulaRetryCount++
  
  try {
    // 调用统一入口获取所有 3D 组件
    const { THREE, ForceGraph3D, SpriteText } = await load3DLibraries()

    const container = document.getElementById('nebula-container')
    if (!container) return

    if (nebulaGraph) {
      nebulaGraph._destructor()
      nebulaGraph = null
    }

    const filteredNodes = nodes.value.filter(n => visibleThemes.value.has(n.themeId))
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
    const graphData = {
      nodes: filteredNodes.map(n => ({
        id: n.id,
        label: n.label,
        color: getNodeStyle(n.nodeStyleId)?.color || '#3498db',
        size: n.size || 2,
        themeId: n.themeId
      })),
      links: links.value.filter(l => {
        const sId = typeof l.source === 'object' ? l.source.id : l.source
        const tId = typeof l.target === 'object' ? l.target.id : l.target
        return filteredNodeIds.has(sId) && filteredNodeIds.has(tId)
      }).map(l => ({
        source: typeof l.source === 'object' ? l.source.id : l.source,
        target: typeof l.target === 'object' ? l.target.id : l.target
      }))
    }

    const width = container.clientWidth
    const height = container.clientHeight
    if (width === 0 || height === 0) {
      setTimeout(initNebulaGraph, 300)
      return
    }

    let FG = window._forceGraphInstance
    
    // 初始化图谱 (修复了渲染参数，并引入高清文本精灵 SpriteText)
    try {
      nebulaGraph = FG()(container)
        .width(width)
        .height(height)
        .backgroundColor('#1a1a2e')
        .graphData(graphData)
        .nodeRelSize(2)
        .nodeThreeObject((node) => {
          // 组装节点：中心发光小球 + 高清文字
          const group = new THREE.Group()

          // 1. 小球本体
          const sphereSize = 1.5
          const sphereGeo = new THREE.SphereGeometry(sphereSize, 16, 16)
          // 推荐用 MeshLambertMaterial，自带的光源体系会让球体立体感更强
          const sphereMat = new THREE.MeshLambertMaterial({
            color: node.color || '#3498db',
            transparent: true,
            opacity: 0.85
          })
          const sphere = new THREE.Mesh(sphereGeo, sphereMat)
          group.add(sphere)

          // 2. 文字精灵 (规避了自己手写 CanvasTexture 的内存碎片和分辨率问题)
          if (SpriteText) {
            const sprite = new SpriteText(node.label || '')
            sprite.color = '#ffffff'
            sprite.textHeight = 5 // 字体大小 - 更大
            sprite.position.y = sphereSize + 4 // 放到小球顶部上方一点
            group.add(sprite)
          }

          return group
        })
    } catch(err) {
      console.error('实例化 ForceGraph3D 失败:', err)
    }

    if (nebulaGraph) {
      nebulaGraph.onNodeClick((node) => {
        editingType.value = 'node'
        const originalNode = nodes.value.find(n => n.id === node.id)
        if (originalNode) {
          Object.assign(editingItem, {
            id: originalNode.id, label: originalNode.label, content: originalNode.content,
            themeId: originalNode.themeId, nodeStyleId: originalNode.nodeStyleId, style: originalNode.style || {}
          })
          isInfoCardOpen.value = true
        }
      })
    }
  } catch (e) {
    if (nebulaRetryCount < 5) setTimeout(initNebulaGraph, 1000)
  }
}

const destroyNebulaGraph = () => {
  if (nebulaGraph) {
    nebulaGraph._destructor()
    nebulaGraph = null
  }
}

watch(viewMode, (newMode) => {
  if (newMode === '3d') {
    nextTick(() => requestAnimationFrame(() => initNebulaGraph()))
  } else {
    destroyNebulaGraph()
    nextTick(() => nextTick(() => render()))
  }
})

watch(currentMode, (newMode) => {
  if (newMode === 'edit') { mode.value = 'edit'; viewMode.value = '2d' }
  else if (newMode === 'view-3d') { mode.value = 'view'; viewMode.value = '3d' }
  else { mode.value = 'view'; viewMode.value = '2d' }
})

const closeInfoCard = () => { isInfoCardOpen.value = false; clearSelectionOnly() }

const onPhysicsToggle = () => {
  if (physicsEnabled.value) {
    // 启用物理模拟：释放所有节点的固定状态，并重启模拟
    nodes.value.forEach(n => { 
      if (n.x !== undefined && n.y !== undefined) {
        n.fx = null
        n.fy = null
      }
    })
    simulation?.alpha(1).restart()
  } else {
    // 禁用物理模拟：停止模拟并固定所有节点位置
    simulation?.stop()
    nodes.value.forEach(n => { 
      if (n.x !== undefined && n.y !== undefined) {
        n.fx = n.x
        n.fy = n.y
      }
    })
  }
}

const updateInfoCardPosition = (e) => {
  const cardWidth = 250, cardHeight = 150, offsetX = 15, offsetY = 10
  const graphArea = document.querySelector('.graph-area')
  const rect = graphArea.getBoundingClientRect()
  let x = e.clientX - rect.left + offsetX, y = e.clientY - rect.top + offsetY
  if (x + cardWidth > rect.width) x = e.clientX - rect.left - cardWidth - offsetX
  if (y + cardHeight > rect.height) y = e.clientY - rect.top - cardHeight - offsetY
  infoCardPos.x = Math.max(0, x); infoCardPos.y = Math.max(0, y)
}

const showToast = (msg, type = 'success') => ElMessage({ message: msg, type })
const asyncConfirm = (msg) => ElMessageBox.confirm(msg, '确认操作', { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }).then(() => true).catch(() => false)

const syncCounters = () => {
  if (nodes.value.length) nodeIdCounter.value = Math.max(...nodes.value.map(n => parseInt(n.id.replace('N',''))||0)) + 1
  if (links.value.length) linkIdCounter.value = Math.max(...links.value.map(l => parseInt(l.id.replace('E',''))||0)) + 1
  resourceIdCounter.value = Math.max(...themes.value.map(t => parseInt(t.id.replace('T',''))||0), ...nodeStyles.value.map(ns => parseInt(ns.id.replace('NS',''))||0), ...edgeStyles.value.map(es => parseInt(es.id.replace('ES',''))||0), 0) + 1
}

const fetchDataFromServer = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/data`)
    if (!response.ok) throw new Error('网络错误')
    const data = await response.json()
    nodeStyles.value = data.nodeStyles || []; edgeStyles.value = data.edgeStyles || []; themes.value = data.themes || []
    nodes.value = data.nodes || []; links.value = data.links || []
    console.log('从API获取的themes数据:', JSON.parse(JSON.stringify(themes.value)))
    if (themes.value.length === 0) await initDefaultData()
    syncCounters()
    // 按 sortNum 降序排列，sortNum 最大的在最前面
    themes.value.sort((a, b) => (b.sortNum || 0) - (a.sortNum || 0))
    console.log('排序后的themes数据:', JSON.parse(JSON.stringify(themes.value)))
    visibleThemes.value = new Set([themes.value[0]?.id])
    activeThemeFilter.value = themes.value[0]?.id || null
    console.log('设置的默认主题:', themes.value[0]?.name, 'sortNum:', themes.value[0]?.sortNum)
    showToast('从数据库加载成功！')
  } catch (error) {
    await initDefaultData()
  }
  render()
}

const initDefaultData = async () => {
  nodeStyles.value = [{ id: 'NS1', name: '默认节点', color: '#3498db', shape: 'circle', opacity: 1 }]
  edgeStyles.value = [{ id: 'ES1', name: '默认连线', color: '#95a5a6', style: 'solid' }]
  themes.value = [{ id: 'T1', name: '默认主题', defaultNodeStyleId: 'NS1', defaultEdgeStyleId: 'ES1', sortNum: 1 }]
  nodes.value = []; links.value = []; resourceIdCounter.value = 2; activeThemeFilter.value = 'T1'; visibleThemes.value = new Set(['T1'])
}

const openProperties = (item, type) => {
  editingType.value = type
  const preset = type === 'node' ? getNodeStyle(item.nodeStyleId) : getEdgeStyle(item.edgeStyleId)
  let styleObj = {}
  if (item.style && typeof item.style === 'object') Object.keys(item.style).forEach(k => { styleObj[k] = item.style[k] })
  if (type === 'node') {
    if (!styleObj.color) styleObj.color = preset?.color || '#3498db'
    if (!styleObj.shape) styleObj.shape = preset?.shape || 'circle'
    if (styleObj.opacity === undefined) styleObj.opacity = preset?.opacity ?? 1
  } else {
    if (!styleObj.color) styleObj.color = preset?.color || '#95a5a6'
    if (!styleObj.style) styleObj.style = preset?.style || 'solid'
    if (!styleObj.width) styleObj.width = item.width || 2
  }
  Object.assign(editingItem, { id: item.id, label: item.label, content: item.content || '', themeId: item.themeId, nodeStyleId: item.nodeStyleId, edgeStyleId: item.edgeStyleId, width: item.width, size: item.size, style: styleObj })
  if (!item.selected) { clearSelection(); item.selected = true; render() }
  isPanelOpen.value = true
}

const closeProperties = () => {
  isPanelOpen.value = false; Object.assign(editingItem, { id: '', label: '', content: '', themeId: null, nodeStyleId: null, edgeStyleId: null, width: 2, size: 22, style: {} }); editingType.value = null
}

const onNodeStylePresetChange = (presetId) => {
  const preset = getNodeStyle(presetId)
  if (preset) editingItem.style = { color: preset.color, shape: preset.shape, opacity: preset.opacity }
}

const onEdgeStylePresetChange = (presetId) => {
  const preset = getEdgeStyle(presetId)
  if (preset) editingItem.style = { color: preset.color, style: preset.style, width: 2 }
}

const saveProperties = async () => {
  if (!editingItem.label) return
  const node = nodes.value.find(n => n.id === editingItem.id)
  if (node) {
    node.label = editingItem.label; node.themeId = editingItem.themeId; node.nodeStyleId = editingItem.nodeStyleId; node.content = editingItem.content || ''; node.style = editingItem.style || null
    
    // 保存节点到数据库
    try {
      const response = await fetch(`${API_BASE_URL}/nodes/${node.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: node.id,
          label: node.label,
          size: node.size,
          themeId: node.themeId,
          nodeStyleId: node.nodeStyleId,
          content: node.content,
          style: node.style
        })
      })
      if (!response.ok) throw new Error('保存节点失败')
      showToast('保存成功')
    } catch (error) {
      console.error('保存节点失败:', error)
      showToast('保存节点失败', 'error')
    }
  }
  
  const link = links.value.find(l => l.id === editingItem.id)
  if (link) {
    link.label = editingItem.label; link.themeId = editingItem.themeId; link.edgeStyleId = editingItem.edgeStyleId; link.content = editingItem.content || ''; link.style = editingItem.style || null
    
    // 保存连线到数据库
    try {
      const response = await fetch(`${API_BASE_URL}/edges/${link.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: link.id,
          source: typeof link.source === 'object' ? link.source.id : link.source,
          target: typeof link.target === 'object' ? link.target.id : link.target,
          label: link.label,
          width: link.style?.width || link.width,
          themeId: link.themeId,
          edgeStyleId: link.edgeStyleId,
          content: link.content,
          style: link.style
        })
      })
      if (!response.ok) throw new Error('保存连线失败')
      showToast('保存成功')
    } catch (error) {
      console.error('保存连线失败:', error)
      showToast('保存连线失败', 'error')
    }
  }
  
  closeProperties()
  render()
}

const clearSelection = () => { nodes.value.forEach(n => n.selected = false); links.value.forEach(l => l.selected = false); isInfoCardOpen.value = false }
const clearSelectionOnly = () => {
  nodes.value.forEach(n => n.selected = false); links.value.forEach(l => l.selected = false); isInfoCardOpen.value = false
  requestAnimationFrame(() => {
    const svgEl = svgRef.value
    if (svgEl) {
      svgEl.querySelectorAll('.node.selected').forEach(el => el.classList.remove('selected'))
      svgEl.querySelectorAll('.link.selected').forEach(el => { el.classList.remove('selected'); el.setAttribute('marker-end', null) })
    }
  })
}

const deleteSelected = async () => {
  if (mode.value !== 'edit') return
  
  // 检查是否有选中的节点或连线
  const selectedNodeCount = nodes.value.filter(n => n.selected).length
  const selectedLinkCount = links.value.filter(l => l.selected).length
  const totalCount = selectedNodeCount + selectedLinkCount
  
  if (totalCount === 0) return
  
  // 弹出确认对话框
  const message = selectedNodeCount > 0 && selectedLinkCount > 0
    ? `确定要删除选中的 ${selectedNodeCount} 个节点和 ${selectedLinkCount} 条连线吗？`
    : selectedNodeCount > 0
      ? `确定要删除选中的 ${selectedNodeCount} 个节点吗？相关连线也会被删除。`
      : `确定要删除选中的 ${selectedLinkCount} 条连线吗？`
  
  const confirmed = await asyncConfirm(message)
  if (!confirmed) return
  
  const selectedNodeIds = nodes.value.filter(n => n.selected).map(n => n.id)
  const selectedLinkIds = links.value.filter(l => l.selected).map(l => l.id)
  
  // 从数据库删除节点
  try {
    for (const nodeId of selectedNodeIds) {
      await fetch(`${API_BASE_URL}/nodes/${nodeId}`, { method: 'DELETE' })
    }
  } catch (error) {
    console.error('删除节点失败:', error)
    showToast('删除节点失败', 'error')
  }
  
  // 从数据库删除连线
  try {
    for (const linkId of selectedLinkIds) {
      await fetch(`${API_BASE_URL}/edges/${linkId}`, { method: 'DELETE' })
    }
  } catch (error) {
    console.error('删除连线失败:', error)
    showToast('删除连线失败', 'error')
  }
  
  // 更新前端数据
  nodes.value = nodes.value.filter(n => !n.selected)
  links.value = links.value.filter(l => !l.selected && !selectedNodeIds.includes(typeof l.source === 'object' ? l.source.id : l.source) && !selectedNodeIds.includes(typeof l.target === 'object' ? l.target.id : l.target))
  closeProperties(); render()
}

const openResourceManager = () => { isResourceManagerOpen.value = true; rmSwitchTab('themes') }
const closeResourceManager = () => { isResourceManagerOpen.value = false }

const rmSwitchTab = (tabName) => {
  rmActiveTab.value = tabName; const list = rmListData.value
  if (list.length > 0) rmSelectItem(list[0].id); else rmEditingId.value = null
}

const rmSelectItem = (id) => { rmEditingId.value = id; const item = rmListData.value.find(x => x.id === id); if (item) Object.assign(rmEditingItem, item) }

const rmCreateNew = async () => {
  let newItem
  if (rmActiveTab.value === 'themes') {
    // sortNum 会在保存时由后端自动设置，前端暂时设为 0
    newItem = { id: `T${resourceIdCounter.value++}`, name: '新主题', defaultNodeStyleId: nodeStyles.value[0]?.id, defaultEdgeStyleId: edgeStyles.value[0]?.id, sortNum: 0 }
    themes.value.push(newItem); themes.value.sort((a, b) => (b.sortNum || 0) - (a.sortNum || 0)); visibleThemes.value.add(newItem.id)
    
    // 保存到数据库
    try {
      const response = await fetch(`${API_BASE_URL}/themes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: newItem.id,
          name: newItem.name,
          defaultNodeStyleId: newItem.defaultNodeStyleId,
          defaultEdgeStyleId: newItem.defaultEdgeStyleId,
          sortNum: newItem.sortNum
        })
      })
      if (!response.ok) throw new Error('创建主题失败')
      const result = await response.json()
      // 如果后端返回了自动设置的 sortNum，更新前端数据
      if (result.sortNum) {
        newItem.sortNum = result.sortNum
        themes.value.sort((a, b) => (b.sortNum || 0) - (a.sortNum || 0))
      }
      showToast('创建成功')
    } catch (error) {
      console.error('创建主题失败:', error)
      showToast('创建主题失败', 'error')
    }
  } else if (rmActiveTab.value === 'nodeStyles') {
    newItem = { id: `NS${resourceIdCounter.value++}`, name: '新节点样式', color: '#9b59b6', shape: 'circle', opacity: 1 }
    nodeStyles.value.push(newItem)
    
    // 保存到数据库
    try {
      const response = await fetch(`${API_BASE_URL}/node-styles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: newItem.id,
          name: newItem.name,
          color: newItem.color,
          shape: newItem.shape,
          opacity: newItem.opacity
        })
      })
      if (!response.ok) throw new Error('创建节点样式失败')
      showToast('创建成功')
    } catch (error) {
      console.error('创建节点样式失败:', error)
      showToast('创建节点样式失败', 'error')
    }
  } else {
    newItem = { id: `ES${resourceIdCounter.value++}`, name: '新连线样式', color: '#95a5a6', style: 'solid' }
    edgeStyles.value.push(newItem)
    
    // 保存到数据库
    try {
      const response = await fetch(`${API_BASE_URL}/edge-styles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: newItem.id,
          name: newItem.name,
          color: newItem.color,
          style: newItem.style
        })
      })
      if (!response.ok) throw new Error('创建连线样式失败')
      showToast('创建成功')
    } catch (error) {
      console.error('创建连线样式失败:', error)
      showToast('创建连线样式失败', 'error')
    }
  }
  rmSelectItem(newItem.id)
}

const rmSave = async () => {
  if (!rmEditingId.value) return
  const item = rmListData.value.find(x => x.id === rmEditingId.value)
  Object.assign(item, rmEditingItem)
  
  // 保存到数据库
  try {
    if (rmActiveTab.value === 'themes') {
      const response = await fetch(`${API_BASE_URL}/themes/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: item.id,
          name: item.name,
          defaultNodeStyleId: item.defaultNodeStyleId,
          defaultEdgeStyleId: item.defaultEdgeStyleId,
          sortNum: item.sortNum
        })
      })
      if (!response.ok) throw new Error('保存主题失败')
      showToast('保存成功')
    } else if (rmActiveTab.value === 'nodeStyles') {
      const response = await fetch(`${API_BASE_URL}/node-styles/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: item.id,
          name: item.name,
          color: item.color,
          shape: item.shape,
          opacity: item.opacity
        })
      })
      if (!response.ok) throw new Error('保存节点样式失败')
      showToast('保存成功')
    } else if (rmActiveTab.value === 'edgeStyles') {
      const response = await fetch(`${API_BASE_URL}/edge-styles/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: item.id,
          name: item.name,
          color: item.color,
          style: item.style
        })
      })
      if (!response.ok) throw new Error('保存连线样式失败')
      showToast('保存成功')
    }
  } catch (error) {
    console.error('保存失败:', error)
    showToast('保存失败', 'error')
  }
  
  render()
}

const rmDeleteCurrent = async () => {
  if (rmListData.value.length <= 1) return showToast('该类别下必须保留至少一个选项！')
  const confirmed = await asyncConfirm('确定要删除此项吗？相关引用会被重置！')
  if (!confirmed) return
  const dId = rmEditingId.value
  
  // 从数据库删除
  try {
    if (rmActiveTab.value === 'themes') {
      await fetch(`${API_BASE_URL}/themes/${dId}`, { method: 'DELETE' })
    } else if (rmActiveTab.value === 'nodeStyles') {
      await fetch(`${API_BASE_URL}/node-styles/${dId}`, { method: 'DELETE' })
    } else {
      await fetch(`${API_BASE_URL}/edge-styles/${dId}`, { method: 'DELETE' })
    }
    showToast('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
    showToast('删除失败', 'error')
  }
  
  // 更新前端数据
  if (rmActiveTab.value === 'themes') {
    themes.value = themes.value.filter(x => x.id !== dId)
    nodes.value.forEach(n => { if (n.themeId === dId) n.themeId = themes.value[0].id })
    links.value.forEach(l => { if (l.themeId === dId) l.themeId = themes.value[0].id })
    if (activeThemeFilter.value === dId) activeThemeFilter.value = themes.value[0].id
  } else if (rmActiveTab.value === 'nodeStyles') {
    nodeStyles.value = nodeStyles.value.filter(x => x.id !== dId)
    nodes.value.forEach(n => { if (n.nodeStyleId === dId) n.nodeStyleId = nodeStyles.value[0].id })
    themes.value.forEach(t => { if (t.defaultNodeStyleId === dId) t.defaultNodeStyleId = nodeStyles.value[0].id })
  } else {
    edgeStyles.value = edgeStyles.value.filter(x => x.id !== dId)
    links.value.forEach(l => { if (l.edgeStyleId === dId) l.edgeStyleId = edgeStyles.value[0].id })
    themes.value.forEach(t => { if (t.defaultEdgeStyleId === dId) t.defaultEdgeStyleId = edgeStyles.value[0].id })
  }
  if (rmListData.value.length > 0) rmSelectItem(rmListData.value[0].id); else rmEditingId.value = null
  render()
}

const onThemeFilterChange = () => { visibleThemes.value = new Set([activeThemeFilter.value]); render() }

const addNode = async (x, y) => {
  const theme = themes.value.find(t => t.id === activeThemeFilter.value) || themes.value[0]
  const nodeStyle = theme.defaultNodeStyleId ? nodeStyles.value.find(s => s.id === theme.defaultNodeStyleId) : nodeStyles.value[0]
  const newNode = {
    id: `N${nodeIdCounter.value++}`, label: `节点${nodeIdCounter.value - 1}`, x, y, themeId: theme.id, nodeStyleId: nodeStyle?.id || nodeStyles.value[0]?.id,
    size: 10, content: '', style: nodeStyle ? { color: nodeStyle.color, shape: nodeStyle.shape, opacity: nodeStyle.opacity } : null, selected: true
  }
  if (mode.value === 'edit') { newNode.fx = x; newNode.fy = y }
  clearSelection(); nodes.value.push(newNode); render()
  
  // 保存到数据库
  try {
    const response = await fetch(`${API_BASE_URL}/nodes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: newNode.id,
        label: newNode.label,
        size: newNode.size,
        themeId: newNode.themeId,
        nodeStyleId: newNode.nodeStyleId,
        content: newNode.content,
        style: newNode.style
      })
    })
    if (!response.ok) throw new Error('保存节点失败')
  } catch (error) {
    console.error('保存节点失败:', error)
    showToast('保存节点失败', 'error')
  }
}

const addEdge = async (source, target) => {
  if (source === target) return
  const sid = source.id || source; const tid = target.id || target
  if (links.value.find(l => { const lsid = typeof l.source === 'object' ? l.source.id : l.source; const ltid = typeof l.target === 'object' ? l.target.id : l.target; return (lsid === sid && ltid === tid) || (lsid === tid && ltid === sid) })) return
  const theme = themes.value.find(t => t.id === activeThemeFilter.value) || themes.value[0]
  const edgeStyle = theme.defaultEdgeStyleId ? edgeStyles.value.find(s => s.id === theme.defaultEdgeStyleId) : edgeStyles.value[0]
  const newEdge = {
    id: `E${linkIdCounter.value++}`, source: sid, target: tid, label: '', width: 2, themeId: theme.id, edgeStyleId: edgeStyle?.id || edgeStyles.value[0]?.id, content: '',
    style: edgeStyle ? { color: edgeStyle.color, style: edgeStyle.style, width: 2 } : null, selected: false
  }
  links.value.push(newEdge)
  render()
  
  // 保存到数据库
  try {
    const response = await fetch(`${API_BASE_URL}/edges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: newEdge.id,
        source: sid,
        target: tid,
        label: newEdge.label,
        width: newEdge.width,
        themeId: newEdge.themeId,
        edgeStyleId: newEdge.edgeStyleId,
        content: newEdge.content,
        style: newEdge.style
      })
    })
    if (!response.ok) throw new Error('保存连线失败')
  } catch (error) {
    console.error('保存连线失败:', error)
    showToast('保存连线失败', 'error')
  }
}

const initD3 = () => {
  const svg = d3.select(svgRef.value)
  const mainG = d3.select(mainGroup.value)
  zoom = d3.zoom().scaleExtent([0.1, 5]).filter(event => event.type !== 'dblclick' && !event.shiftKey).on('zoom', (event) => { currentTransform = event.transform; mainG.attr('transform', event.transform) })
  svg.call(zoom)
  simulation = d3.forceSimulation().alpha(1).alphaDecay(0.02).velocityDecay(0.3).force('link', d3.forceLink().id(d => d.id).distance(120).strength(0.6)).force('charge', d3.forceManyBody().strength(-300)).force('center', d3.forceCenter(svgRef.value.clientWidth / 2, svgRef.value.clientHeight / 2)).force('collision', d3.forceCollide().radius(40))
    .on('tick', () => {
      const mainGSel = d3.select(mainGroup.value)
      mainGSel.selectAll('.link').attr('x1', d => d.source?.x || 0).attr('y1', d => d.source?.y || 0).attr('x2', d => d.target?.x || 0).attr('y2', d => d.target?.y || 0)
      mainGSel.selectAll('.node').attr('transform', d => `translate(${d.x || 0}, ${d.y || 0})`)
      mainGSel.selectAll('.node-label').attr('x', d => d.x || 0).attr('y', d => (d.y || 0) - (d.size + 8))
      mainGSel.selectAll('.link-label').attr('x', d => ((d.source?.x || 0) + (d.target?.x || 0)) / 2).attr('y', d => ((d.source?.y || 0) + (d.target?.y || 0)) / 2 - 8)
    })
}

const render = (forceRestart = false) => {
  const svg = d3.select(svgRef.value)
  const mainG = d3.select(mainGroup.value)
  if (nodes.value.length > 0) {
    const centerX = svgRef.value?.clientWidth / 2 || 400; const centerY = svgRef.value?.clientHeight / 2 || 300
    nodes.value.forEach((n) => { if (n.x === undefined || n.y === undefined || n.x === null || n.y === null) { n.x = centerX + (Math.random() - 0.5) * 200; n.y = centerY + (Math.random() - 0.5) * 200; n.vx = 0; n.vy = 0 } })
  }

  const link = mainG.select('#links-group').selectAll('.link').data(links.value, d => d.id)
  link.exit().remove()
  const linkEnter = link.enter().append('line').attr('class', 'link')
    .on('mouseover', (e, d) => { if (mode.value === 'view') { editingType.value = 'edge'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true } })
    .on('mouseout', () => { if (mode.value === 'view') isInfoCardOpen.value = false })
    .on('click', (e, d) => {
      e.stopPropagation()
      if (mode.value === 'view') {
        if (!e.shiftKey) {
          clearSelectionOnly()
          clearHighlight()
          updateHighlightStyles()
        }
        d.selected = true
        computeHighlight(d.id)
        updateHighlightStyles()
        editingType.value = 'edge'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true
      }
    })
    .on('dblclick', (e, d) => { e.stopPropagation(); if (mode.value === 'edit') openProperties(d, 'edge'); else { editingType.value = 'edge'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true } })

  linkEnter.merge(link).attr('stroke', d => {
    if (d.selected) return '#ff6b6b'
    if (highlightedLinks.value.has(d.id)) return '#ff8c00'
    return d.style?.color ?? getEdgeStyle(d.edgeStyleId)?.color ?? '#95a5a6'
  }).attr('stroke-width', d => {
    if (d.selected) return (d.style?.width ?? d.width) + 2
    if (highlightedLinks.value.has(d.id)) return (d.style?.width ?? d.width) + 2
    return d.style?.width ?? d.width
  }).attr('stroke-dasharray', d => (d.style?.style ?? getEdgeStyle(d.edgeStyleId)?.style) === 'dashed' ? '6,6' : 'none').attr('opacity', d => {
    if (d.selected || highlightedLinks.value.has(d.id)) return 1
    return 0.6
  }).classed('selected', d => d.selected).attr('marker-end', null).style('display', d => {
    const sTheme = typeof d.source === 'object' ? d.source.themeId : nodes.value.find(n => n.id === d.source)?.themeId
    const tTheme = typeof d.target === 'object' ? d.target.themeId : nodes.value.find(n => n.id === d.target)?.themeId
    return visibleThemes.value.has(sTheme) && visibleThemes.value.has(tTheme) ? 'block' : 'none'
  })

  const nodeDrag = d3.drag().filter(event => true)
    .on('start', function(event, d) {
      if (mode.value === 'edit' && event.sourceEvent.shiftKey) { isLinking.value = true; linkSourceNode.value = d }
      else { 
        if (mode.value === 'edit' && !d.selected) { clearSelection(); d.selected = true; render() }
        if (mode.value === 'edit') {
          nodes.value.filter(n => n.selected).forEach(n => { n.fx = n.x; n.fy = n.y })
        }
      }
    })
    .on('drag', function(event, d) {
      if (isLinking.value) { d3.select('#ghost-line').style('display', 'block').attr('x1', linkSourceNode.value?.x).attr('y1', linkSourceNode.value?.y).attr('x2', event.x).attr('y2', event.y) }
      else { 
        let dx = event.dx; let dy = event.dy
        if (mode.value === 'view') {
          dx = dx / currentTransform.k; dy = dy / currentTransform.k
        }
        nodes.value.filter(n => n.selected).forEach(n => { n.x += dx; n.y += dy; if (mode.value === 'edit') { n.fx = n.x; n.fy = n.y } }); 
        manualTick()
        if (physicsEnabled.value && simulation && mode.value === 'view') {
          simulation.alpha(Math.max(simulation.alpha(), 0.05))
        }
      }
    })
    .on('end', function(event, d) {
      if (isLinking.value) { isLinking.value = false; d3.select('#ghost-line').style('display', 'none'); if (hoveredNode.value && hoveredNode.value !== linkSourceNode.value) addEdge(linkSourceNode.value, hoveredNode.value); linkSourceNode.value = null }
      else { 
        if (mode.value === 'view' && physicsEnabled.value && simulation) {
          simulation.alpha(0.3).restart()
        } else if (mode.value === 'view') { 
          nodes.value.filter(n => n.selected).forEach(n => { n.fx = n.x; n.fy = n.y }) 
        } 
      }
    })

  const node = mainG.select('#nodes-group').selectAll('.node').data(nodes.value, d => d.id)
  node.exit().remove()
  const nodeEnter = node.enter().append('path').attr('class', 'node').call(nodeDrag)
    .on('click', (e, d) => {
      e.stopPropagation()
      if (mode.value === 'view') {
        if (!e.shiftKey) {
          clearSelectionOnly()
          clearHighlight()
          updateHighlightStyles()
        }
        d.selected = true
        computeHighlight(d.id)
        updateHighlightStyles()
        editingType.value = 'node'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true
      }
    })
    .on('dblclick', (e, d) => { e.stopPropagation(); if (mode.value === 'edit') openProperties(d, 'node'); else { editingType.value = 'node'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true } })
    .on('mouseover', (e, d) => {
      hoveredNode.value = d; if (mode.value === 'view') { 
        if (!e.shiftKey) clearSelectionOnly(); 
        d.selected = true; 
        editingType.value = 'node'; Object.assign(editingItem, d); updateInfoCardPosition(e); isInfoCardOpen.value = true
      }
    })
    .on('mouseout', () => { hoveredNode.value = null; if (mode.value === 'view') isInfoCardOpen.value = false })

  nodeEnter.merge(node).attr('d', d => getSymbolGenerator(d.style?.shape || getNodeStyle(d.nodeStyleId)?.shape || 'circle', d.size)).attr('fill', d => d.style?.color ?? getNodeStyle(d.nodeStyleId)?.color ?? '#3498db').attr('fill-opacity', d => d.style?.opacity ?? getNodeStyle(d.nodeStyleId)?.opacity ?? 1).attr('stroke', 'white').attr('stroke-width', 4).attr('paint-order', 'stroke').classed('selected', d => d.selected).style('display', d => visibleThemes.value.has(d.themeId) ? 'block' : 'none')

  const nodeLabels = mainG.select('#labels-group').selectAll('.node-label').data(nodes.value, d => d.id)
  nodeLabels.exit().remove()
  nodeLabels.enter().append('text').attr('class', 'node-label').attr('text-anchor', 'middle').merge(nodeLabels).text(d => d.label).style('display', d => visibleThemes.value.has(d.themeId) ? 'block' : 'none')

  const linkLabels = mainG.select('#labels-group').selectAll('.link-label').data(links.value, d => d.id)
  linkLabels.exit().remove()
  linkLabels.enter().append('text').attr('class', 'link-label').attr('text-anchor', 'middle').merge(linkLabels).text(d => d.label || '').style('display', d => { if (!showLinkLabels.value) return 'none'; const sTheme = typeof d.source === 'object' ? d.source.themeId : nodes.value.find(n => n.id === d.source)?.themeId; const tTheme = typeof d.target === 'object' ? d.target.themeId : nodes.value.find(n => n.id === d.target)?.themeId; return (visibleThemes.value.has(sTheme) && visibleThemes.value.has(tTheme)) ? 'block' : 'none' }).attr('x', d => ((d.source?.x || 0) + (d.target?.x || 0)) / 2).attr('y', d => ((d.source?.y || 0) + (d.target?.y || 0)) / 2 - 8)

  if (mode.value === 'view') {
    if (nodes.value.length > 0) { const centerX = svgRef.value?.clientWidth / 2 || 400; const centerY = svgRef.value?.clientHeight / 2 || 300; nodes.value.forEach((n) => { if (n.x === undefined || n.y === undefined || (n.x === 0 && n.y === 0)) { n.x = centerX + (Math.random() - 0.5) * 300; n.y = centerY + (Math.random() - 0.5) * 300 } n.fx = null; n.fy = null }) }
    simulation.nodes(nodes.value); simulation.force('link').links(links.value)
    if (forceRestart || !simulation.alpha()) {
      simulation.alpha(1).restart()
    }
  } else {
    simulation.stop()
    simulation.nodes(nodes.value); simulation.force('link').links(links.value)
    const mainGSel = d3.select(mainGroup.value)
    mainGSel.selectAll('.link').attr('x1', d => {
      const node = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
      return node?.x || 0
    }).attr('y1', d => {
      const node = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
      return node?.y || 0
    }).attr('x2', d => {
      const node = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
      return node?.x || 0
    }).attr('y2', d => {
      const node = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
      return node?.y || 0
    })
    mainGSel.selectAll('.node').attr('transform', d => `translate(${d.x}, ${d.y})`)
    mainGSel.selectAll('.node-label').attr('x', d => d.x).attr('y', d => d.y - (d.size + 8))
  }
}

const updatePositions = (links, nodes, labels) => { 
  links.attr('x1', d => {
    const node = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
    return node?.x || 0
  }).attr('y1', d => {
    const node = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
    return node?.y || 0
  }).attr('x2', d => {
    const node = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
    return node?.x || 0
  }).attr('y2', d => {
    const node = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
    return node?.y || 0
  })
  nodes.attr('transform', d => `translate(${d.x || 0}, ${d.y || 0})`)
  labels.attr('x', d => d.x || 0).attr('y', d => (d.y || 0) - (d.size + 8))
}

const manualTick = () => {
  const mainG = d3.select(mainGroup.value)
  updatePositions(mainG.selectAll('.link'), mainG.selectAll('.node'), mainG.selectAll('.node-label'))
  mainG.selectAll('.link-label').attr('x', d => {
    const sNode = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
    const tNode = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
    return ((sNode?.x || 0) + (tNode?.x || 0)) / 2
  }).attr('y', d => {
    const sNode = typeof d.source === 'object' ? d.source : nodes.value.find(n => n.id === d.source)
    const tNode = typeof d.target === 'object' ? d.target : nodes.value.find(n => n.id === d.target)
    return ((sNode?.y || 0) + (tNode?.y || 0)) / 2 - 8
  })
}

const initEvents = () => {
  const svg = d3.select(svgRef.value)
  svg.on('dblclick', (event) => { if (mode.value === 'edit' && event.target.id === 'graph-svg') { const [x, y] = currentTransform.invert(d3.pointer(event)); addNode(x, y) } })
  
  // 框选功能 - Shift + 拖拽选择节点
  svg.on('mousedown', function(event) {
    if (mode.value === 'edit' && event.shiftKey) {
      const [x, y] = d3.pointer(event, svgRef.value)
      boxStart.value = { x, y }
      isBoxSelecting.value = true
      d3.select('#selection-box')
        .style('display', 'block')
        .attr('x', x)
        .attr('y', y)
        .attr('width', 0)
        .attr('height', 0)
      event.preventDefault()
      event.stopImmediatePropagation()
    }
  })
  
  svg.on('mousemove', function(event) {
    if (isBoxSelecting.value) {
      const [x, y] = d3.pointer(event, svgRef.value)
      const startX = boxStart.value.x
      const startY = boxStart.value.y
      const width = x - startX
      const height = y - startY
      
      d3.select('#selection-box')
        .attr('x', width < 0 ? x : startX)
        .attr('y', height < 0 ? y : startY)
        .attr('width', Math.abs(width))
        .attr('height', Math.abs(height))
    }
  })
  
  svg.on('mouseup', function(event) {
    if (isBoxSelecting.value) {
      isBoxSelecting.value = false
      d3.select('#selection-box').style('display', 'none')
      
      const box = d3.select('#selection-box')
      const boxX = parseFloat(box.attr('x'))
      const boxY = parseFloat(box.attr('y'))
      const boxWidth = parseFloat(box.attr('width'))
      const boxHeight = parseFloat(box.attr('height'))
      
      const screenX1 = boxX
      const screenY1 = boxY
      const screenX2 = boxX + boxWidth
      const screenY2 = boxY + boxHeight
      
      nodes.value.forEach(n => {
        const screenPos = currentTransform.apply([n.x, n.y])
        const nodeScreenX = screenPos[0]
        const nodeScreenY = screenPos[1]
        if (nodeScreenX >= screenX1 && nodeScreenX <= screenX2 && nodeScreenY >= screenY1 && nodeScreenY <= screenY2) {
          n.selected = true
        }
      })
      
      render()
    }
  })
  
  svgRef.value.addEventListener('mousedown', (event) => {
    const target = event.target; const classList = target.classList || []
    const isBackground = target.tagName === 'svg' || target.id === 'main-group' || target.id === 'links-group' || target.id === 'nodes-group' || target.id === 'labels-group' || (target.tagName === 'rect' && target.id === 'selection-box')
    if (isBackground || (!classList.contains('node') && !classList.contains('link'))) { 
      if (!isBoxSelecting.value) {
        clearSelectionOnly(); closeProperties() 
      }
    }
  }, true)
  window.addEventListener('keydown', (event) => { 
    if (mode.value === 'edit' && (event.key === 'Delete' || event.key === 'Backspace')) { 
      const target = event.target
      const isEditableInput = target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      const isInDrawer = target.closest('.el-drawer') !== null
      if (!isEditableInput && !isInDrawer) deleteSelected() 
    } 
  })
  window.addEventListener('mouseup', () => { if (isLinking.value) { isLinking.value = false; d3.select('#ghost-line').style('display', 'none'); linkSourceNode.value = null } })
}

watch(mode, (newMode) => {
  if (newMode === 'edit') { nodes.value.forEach(n => { if (n.x !== undefined && n.y !== undefined) { n.fx = n.x; n.fy = n.y } }); simulation?.stop() }
  else { nodes.value.forEach(n => { n.fx = null; n.fy = null }); clearSelection(); closeProperties(); if (simulation) { simulation.nodes(nodes.value); simulation.force('link').links(links.value); simulation.alpha(1).restart() } }
})

onMounted(async () => {
  await nextTick()
  initD3()
  initEvents()
  await fetchDataFromServer()
})
</script>