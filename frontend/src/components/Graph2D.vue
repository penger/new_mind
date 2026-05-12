<template>
  <div class="graph-container" ref="containerRef" style="width: 100%; height: 100%; position: relative;">
    <svg ref="svgRef" class="graph-2d-svg">
      <defs>
        <marker id="arrowhead" viewBox="0 -5 10 10" refX="25" refY="0" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,-5L10,0L0,5" fill="#999" />
        </marker>
      </defs>
      <g ref="mainGroup">
        <line ref="ghostLineRef" style="stroke: #409eff; stroke-dasharray: 5; stroke-width: 2; display: none; pointer-events: none;" />
        <g id="links-group"></g>
        <g id="nodes-group"></g>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  nodes: Array, links: Array, nodeStyles: Array, edgeStyles: Array,
  visibleThemes: Set, physicsEnabled: Boolean, mode: String
})

const emit = defineEmits(['node-click', 'node-hover', 'node-leave', 'node-add', 'edge-add', 'edge-click'])

const containerRef = ref(null), svgRef = ref(null), mainGroup = ref(null), ghostLineRef = ref(null)
let simulation = null, d3Nodes = [], d3Links = [], zoom = null, currentTransform = d3.zoomIdentity
let isLinking = false, linkSourceNode = null, hoveredNodeId = null
let isStabilizing = ref(true), resizeObserver = null

const getNodeStyle = (id) => props.nodeStyles?.find(s => s.id === id) || { color: '#3498db', shape: 'circle' }
const getEdgeStyle = (id) => props.edgeStyles?.find(s => s.id === id) || { color: '#ccc', style: 'solid' }

const getSymbolPath = (shapeStr, size) => {
  let symbolType;
  switch (shapeStr) {
    case 'diamond': symbolType = d3.symbolDiamond; break;
    case 'square':  symbolType = d3.symbolSquare; break;
    case 'star':    symbolType = d3.symbolStar; break;
    case 'triangle': symbolType = d3.symbolTriangle; break;
    default:        symbolType = d3.symbolCircle; break;
  }
  return d3.symbol().type(symbolType).size(Math.pow(size || 18, 2) * 2)()
}

const syncD3Data = () => {
  const oldMap = new Map(d3Nodes.map(n => [n.id, n]))
  const w = svgRef.value?.clientWidth || 800, h = svgRef.value?.clientHeight || 600

  d3Nodes = (props.nodes || []).map(n => {
    const old = oldMap.get(n.id)
    if (old) return { 
      ...n, x: old.x, y: old.y, vx: old.vx, vy: old.vy, 
      fx: (props.mode === 'edit' && !isStabilizing.value) ? old.x : (n.fx ?? old.fx), 
      fy: (props.mode === 'edit' && !isStabilizing.value) ? old.y : (n.fy ?? old.fy) 
    }
    return { ...n, x: n.x ?? (w/2 + (Math.random()-0.5)*100), y: n.y ?? (h/2 + (Math.random()-0.5)*100) }
  })
  
  const nMap = new Map(d3Nodes.map(n => [n.id, n]))
  d3Links = (props.links || []).map(l => ({ 
    ...l, 
    source: nMap.get(typeof l.source === 'object' ? l.source.id : l.source), 
    target: nMap.get(typeof l.target === 'object' ? l.target.id : l.target) 
  })).filter(l => l.source && l.target)
}

const ticked = () => {
  const g = d3.select(mainGroup.value)
  g.selectAll('.link').attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y)
  g.selectAll('.link-label').attr('x', d => (d.source?.x + d.target?.x) / 2).attr('y', d => (d.source?.y + d.target?.y) / 2 - 8)
  g.selectAll('.node-wrapper').attr('transform', d => `translate(${d.x},${d.y})`)
}

const renderGraph = () => {
  if (!svgRef.value) return
  syncD3Data()
  const mainG = d3.select(mainGroup.value)
  
  mainG.select('#links-group').selectAll('.link').data(d3Links, d => d.id)
    .join('line').attr('class', 'link').attr('marker-end', 'url(#arrowhead)')
    .attr('stroke', d => d.style?.color || getEdgeStyle(d.edgeStyleId).color)
    .attr('stroke-width', d => d.width || 2)
    .attr('stroke-dasharray', d => d.style?.style === 'dashed' ? '6,6' : 'none')
    .on('click', (e, d) => { e.stopPropagation(); if (props.mode === 'edit') emit('edge-click', d) })

  mainG.select('#links-group').selectAll('.link-label').data(d3Links.filter(d => d.label), d => d.id)
    .join('text').attr('class', 'link-label')
    .attr('text-anchor', 'middle')
    .attr('fill', '#666')
    .attr('font-size', '11px')
    .attr('pointer-events', 'none')
    .attr('x', d => (d.source?.x + d.target?.x) / 2)
    .attr('y', d => (d.source?.y + d.target?.y) / 2 - 8)
    .text(d => d.label)

  const nodeSel = mainG.select('#nodes-group').selectAll('.node-wrapper').data(d3Nodes, d => d.id)
    .join(enter => {
      const g = enter.append('g').attr('class', 'node-wrapper').call(d3.drag().on('start', dragStarted).on('drag', dragged).on('end', dragEnded))
      g.append('path').attr('class', 'node-shape').attr('stroke', '#fff').attr('stroke-width', 2)
      g.append('text').attr('dy', 30).attr('text-anchor', 'middle').style('font-size', '12px').style('font-weight', 'bold').style('pointer-events', 'none')
      return g
    })
    .on('mouseover', (e, d) => { hoveredNodeId = d.id; if (props.mode === 'view') emit('node-hover', { event: e, node: d }) })
    .on('mouseout', () => { hoveredNodeId = null; if (props.mode === 'view') emit('node-leave') })
    .on('click', (e, d) => { e.stopPropagation(); emit('node-click', d) })

  nodeSel.select('.node-shape')
    .attr('fill', d => d.style?.color || getNodeStyle(d.nodeStyleId).color)
    .attr('fill-opacity', d => d.style?.opacity ?? 1)
    .attr('d', d => getSymbolPath(d.style?.shape || getNodeStyle(d.nodeStyleId).shape, d.size))

  nodeSel.select('text').text(d => d.label)

  simulation.nodes(d3Nodes); simulation.force('link').links(d3Links)
  
  // 模式决策
  if (isStabilizing.value) {
    simulation.alpha(1).restart()
  } else {
    if (props.mode === 'edit') simulation.stop(); else if (props.physicsEnabled) simulation.alpha(0.2).restart()
    ticked()
  }
}

// 拖拽控制：优化点击后的晃动
function dragStarted(e, d) {
  if (props.mode === 'edit' && e.sourceEvent.shiftKey) { 
    isLinking = true; linkSourceNode = d; d3.select(ghostLineRef.value).style('display', 'block').attr('x1', d.x).attr('y1', d.y) 
  } else {
    d.fx = d.x; d.fy = d.y; 
    // 浏览模式下点击节点，给一个极小的能量增量，防止大范围晃动
    if (props.mode !== 'edit' && props.physicsEnabled) simulation.alphaTarget(0.1).restart()
  }
}

function dragged(e, d) {
  if (isLinking) { 
    const [mx, my] = d3.pointer(e, mainGroup.value); d3.select(ghostLineRef.value).attr('x2', mx).attr('y2', my) 
  } else {
    d.x = e.x; d.y = e.y; d.fx = e.x; d.fy = e.y;
    if (props.mode === 'edit' || !props.physicsEnabled) ticked() 
  }
}

function dragEnded(e, d) {
  if (isLinking) {
    isLinking = false; d3.select(ghostLineRef.value).style('display', 'none')
    if (hoveredNodeId && hoveredNodeId !== linkSourceNode.id) emit('edge-add', { source: linkSourceNode, target: d3Nodes.find(x => x.id === hoveredNodeId) })
    linkSourceNode = null
  } else {
    if (props.mode !== 'edit') { 
      simulation.alphaTarget(0); 
      d.fx = null; d.fy = null 
    }
  }
}

onMounted(() => {
  nextTick(() => {
    const w = svgRef.value.clientWidth, h = svgRef.value.clientHeight
    
    // 专业级物理参数优化
    simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).distance(120).strength(0.6))
      .force('charge', d3.forceManyBody().strength(-400).distanceMax(500))
      .force('center', d3.forceCenter(w/2, h/2))
      .force('collision', d3.forceCollide().radius(40))
      .velocityDecay(0.6) // 核心：增加摩擦力（阻尼感），让节点更快停止
      .alphaDecay(0.05)   // 核心：加快冷却速度
      .on('tick', ticked)

    zoom = d3.zoom().scaleExtent([0.1, 5]).on('zoom', (e) => { 
      currentTransform = e.transform
      d3.select(mainGroup.value).attr('transform', e.transform) 
    })
    
    d3.select(svgRef.value).call(zoom).on('dblclick.zoom', null)
      .on('dblclick', (e) => { 
        if (props.mode === 'edit') { 
          const [mx, my] = d3.pointer(e, svgRef.value);
          const [ix, iy] = currentTransform.invert([mx, my]);
          emit('node-add', { x: ix, y: iy });
        } 
      })
    
    // 监听窗口大小
    resizeObserver = new ResizeObserver(() => {
      if (svgRef.value) {
        const nw = svgRef.value.clientWidth, nh = svgRef.value.clientHeight;
        simulation.force('center', d3.forceCenter(nw/2, nh/2));
        if (props.mode === 'view' && props.physicsEnabled) simulation.alpha(0.05).restart();
      }
    })
    resizeObserver.observe(containerRef.value)

    isStabilizing.value = true;
    syncD3Data(); // 先同步数据
    
    // --- 核心优化：静默预热 (Silent Pre-tick) ---
    // 在页面显示之前，先运行 300 次物理计算，让节点找好位置
    for (let i = 0; i < 300; ++i) simulation.tick();
    
    renderGraph(); // 此时再进行首屏渲染，节点已经是稳定的了

    setTimeout(() => {
      isStabilizing.value = false;
      if (props.mode === 'edit') {
        simulation.stop();
        d3Nodes.forEach(d => { d.fx = d.x; d.fy = d.y });
      }
      // 平滑居中
      d3.select(svgRef.value).transition().duration(800).call(zoom.transform, d3.zoomIdentity)
      ticked();
    }, 100); // 预热后只需极短时间即可完全稳定
  })
})

onUnmounted(() => { if (resizeObserver) resizeObserver.disconnect() })

watch(() => props.mode, (m) => { 
  if (isStabilizing.value) return;
  if (m === 'edit') { 
    simulation.stop(); d3Nodes.forEach(d => { d.fx = d.x; d.fy = d.y }) 
  } else { 
    d3Nodes.forEach(d => { d.fx = null; d.fy = null }); 
    if (props.physicsEnabled) simulation.alpha(0.2).restart() 
  }
  ticked() 
})
watch(() => [props.nodes, props.links], renderGraph, { deep: true })
</script>