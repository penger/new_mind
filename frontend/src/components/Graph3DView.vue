<template>
  <div ref="containerRef" class="graph-3d-view"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as THREE from 'three'
import ForceGraph3D from '3d-force-graph'
import SpriteText from 'three-spritetext'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
  nodeStyles: { type: Array, default: () => [] },
  edgeStyles: { type: Array, default: () => [] },
  visibleThemes: { type: Set, default: () => new Set() }
})

const emit = defineEmits(['node-click', 'node-dblclick'])

const containerRef = ref(null)
let graph = null

const getNodeStyle = (id) => props.nodeStyles.find(s => s.id === id) || props.nodeStyles[0]

const initGraph = () => {
  if (!containerRef.value) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  if (width === 0 || height === 0) {
    setTimeout(initGraph, 300)
    return
  }

  if (graph) {
    graph._destructor()
    graph = null
  }

  const filteredNodes = props.nodes.filter(n => props.visibleThemes.has(n.themeId))
  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))

  const graphData = {
    nodes: filteredNodes.map(n => ({
      id: n.id,
      label: n.label,
      color: getNodeStyle(n.nodeStyleId)?.color || '#3498db',
      size: n.size || 2,
      themeId: n.themeId
    })),
    links: props.links
      .filter(l => {
        const sId = typeof l.source === 'object' ? l.source.id : l.source
        const tId = typeof l.target === 'object' ? l.target.id : l.target
        return filteredNodeIds.has(sId) && filteredNodeIds.has(tId)
      })
      .map(l => ({
        source: typeof l.source === 'object' ? l.source.id : l.source,
        target: typeof l.target === 'object' ? l.target.id : l.target
      }))
  }

  graph = ForceGraph3D()(container)
    .width(width)
    .height(height)
    .backgroundColor('#1a1a2e')
    .graphData(graphData)
    .nodeRelSize(2)
    .nodeThreeObject((node) => {
      const group = new THREE.Group()

      const sphereSize = 1.5
      const sphereGeo = new THREE.SphereGeometry(sphereSize, 16, 16)
      const sphereMat = new THREE.MeshLambertMaterial({
        color: node.color || '#3498db',
        transparent: true,
        opacity: 0.85
      })
      const sphere = new THREE.Mesh(sphereGeo, sphereMat)
      group.add(sphere)

      if (SpriteText) {
        const sprite = new SpriteText(node.label || '')
        sprite.color = '#ffffff'
        sprite.textHeight = 5
        sprite.position.y = sphereSize + 4
        group.add(sprite)
      }

      return group
    })
    .onNodeClick((node) => {
      const originalNode = props.nodes.find(n => n.id === node.id)
      if (originalNode) {
        emit('node-click', originalNode)
      }
    })
}

let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    initGraph()

    if (containerRef.value?.parentElement) {
      resizeObserver = new ResizeObserver(() => {
        if (graph && containerRef.value) {
          const width = containerRef.value.clientWidth
          const height = containerRef.value.clientHeight
          graph.width(width).height(height)
        }
      })
      resizeObserver.observe(containerRef.value.parentElement)
    }
  })
})

onUnmounted(() => {
  if (graph) {
    graph._destructor()
    graph = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

watch(() => [props.nodes, props.links, props.visibleThemes], () => {
  nextTick(() => initGraph())
}, { deep: true })
</script>

<style scoped>
.graph-3d-view {
  width: 100%;
  height: 100%;
  background: #1a1a2e;
}
</style>
