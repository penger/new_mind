<template>
  <div class="star-graph-wrapper">
    <div id="star-graph-canvas" class="star-graph-container"></div>
    <div v-if="loading" class="loading-overlay">
      <div class="loading-text">加载中...</div>
      <div v-if="debugInfo" class="debug-text">{{ debugInfo }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  graphData: {
    type: Object,
    required: true,
    default: () => ({ nodes: [], links: [] })
  }
})

const emit = defineEmits(['nodeClick', 'nodeRightClick', 'initSuccess', 'initError'])

const loading = ref(true)
const debugInfo = ref(null)

let nebulaGraph = null

// 使用 3d-force-graph 内置的 nodeLabel（CSS2D 渲染器）显示文字
const initGraph = async () => {
  const containerEl = document.getElementById('star-graph-canvas')
  if (!containerEl) {
    debugInfo.value = 'Container not found'
    loading.value = false
    return
  }

  loading.value = true
  debugInfo.value = 'Loading ForceGraph3D...'

  try {
    // 动态导入 ForceGraph3D
    debugInfo.value = 'Loading ForceGraph3D...'
    const module = await import('https://esm.sh/3d-force-graph@1.73.0')
    console.log('[StarGraph] module keys:', Object.keys(module))

    let ForceGraph3D = module.default || module
    console.log('[StarGraph] ForceGraph3D type:', typeof ForceGraph3D)

    if (typeof ForceGraph3D !== 'function') {
      throw new Error(`ForceGraph3D is not a function: ${typeof ForceGraph3D}`)
    }

    debugInfo.value = 'Creating graph...'

    console.log('[StarGraph] container:', containerEl, 'tagName:', containerEl?.tagName)

    // 尝试链式调用: FG()(container)
    debugInfo.value = 'Trying FG()(container)...'

    try {
      const FG = ForceGraph3D
      nebulaGraph = FG()
      console.log('[StarGraph] After FG(), nebulaGraph:', nebulaGraph)
      nebulaGraph(containerEl)
      console.log('[StarGraph] After containerEl call')

      nebulaGraph
        .width(containerEl.clientWidth || 800)
        .height(containerEl.clientHeight || 600)
        .backgroundColor('#1a1a2e')
        .graphData(props.graphData)
        .nodeAutoColorBy('themeId')
        .nodeRelSize(6)
        .nodeLabel((node) => `<span class="star-graph-label">${node.label || '?'}</span>`)
        .nodeColor((node) => node.color || '#3498db')
        .linkColor(() => '#555555')
        .linkWidth(1)
        .linkOpacity(0.6)

      console.log('[StarGraph] Chain config done')
    } catch (e1) {
      console.error('[StarGraph] Chain method failed:', e1)

      // 如果链式失败，尝试直接调用
      debugInfo.value = 'Trying direct call...'
      try {
        nebulaGraph = ForceGraph3D(containerEl)({
          width: containerEl.clientWidth || 800,
          height: containerEl.clientHeight || 600,
          backgroundColor: '#1a1a2e',
          graphData: props.graphData,
          nodeAutoColorBy: 'themeId',
          nodeRelSize: 6,
          nodeLabel: (node) => `<span class="star-graph-label">${node.label || '?'}</span>`,
          nodeColor: (node) => node.color || '#3498db',
          linkColor: () => '#555555',
          linkWidth: 1,
          linkOpacity: 0.6
        })
      } catch (e2) {
        console.error('[StarGraph] Direct call also failed:', e2)
        throw e2
      }
    }

    // 事件绑定
    nebulaGraph.onNodeClick((node) => {
      emit('nodeClick', node)
    })

    nebulaGraph.onNodeRightClick((node) => {
      emit('nodeRightClick', node)
    })

    loading.value = false
    debugInfo.value = null
    emit('initSuccess')

  } catch (e) {
    loading.value = false
    debugInfo.value = `Error: ${e.message}`
    console.error('[StarGraph] Init error:', e)
    console.error('[StarGraph] Error stack:', e.stack)
    emit('initError', e)
  }
}

// 更新数据
const updateData = (newData) => {
  if (nebulaGraph) {
    nebulaGraph.graphData(newData)
  }
}

// 销毁
const destroyGraph = () => {
  if (nebulaGraph) {
    try {
      nebulaGraph._destructor()
    } catch (e) {
      console.warn('[StarGraph] Destructor error:', e)
    }
    nebulaGraph = null
  }
}

defineExpose({
  updateData,
  destroyGraph,
  initGraph
})

onMounted(() => {
  // 延迟初始化确保 DOM 完全就绪
  setTimeout(() => {
    nextTick(() => {
      initGraph()
    })
  }, 100)
})

onUnmounted(() => {
  destroyGraph()
})

watch(() => props.graphData, (newData) => {
  if (newData && nebulaGraph) {
    updateData(newData)
  }
}, { deep: true })
</script>

<style scoped>
.star-graph-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.star-graph-container {
  width: 100%;
  height: 100%;
  background: #1a1a2e;
  border-radius: 8px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 46, 0.95);
  z-index: 100;
}

.loading-text {
  color: #ffffff;
  font-size: 16px;
  margin-bottom: 8px;
}

.debug-text {
  color: #00ff00;
  font-size: 12px;
  font-family: monospace;
  max-width: 80%;
  word-break: break-all;
}
</style>

<style>
/* 全局样式 - 让 CSS2DRenderer 的标签默认可见 */
.star-graph-container .label-zone {
  opacity: 1 !important;
  visibility: visible !important;
  transition: opacity 0.2s;
}

.star-graph-container .label-zone span {
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: bold;
  white-space: nowrap;
  pointer-events: none;
}
</style>
