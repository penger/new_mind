<template>
  <div class="graph-container" ref="containerRef" style="width: 100%; height: 100%; position: relative;">
    <svg ref="svgRef" class="graph-2d-svg">
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
  visibleThemes: Set, physicsEnabled: Boolean, mode: String,
  searchMatches: { type: Map, default: () => new Map() }
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

// 获取搜索高亮样式
const getSearchHighlightStyle = (nodeId) => {
  const matchType = props.searchMatches?.get(nodeId)
  
  if (!matchType || matchType === 0) {
    return null // 无匹配
  }
  
  const styles = {
    3: { // 两者都匹配 - 最显眼
      stroke: '#e74c3c',
      strokeWidth: 4,
      strokeOpacity: 1,
      filter: 'drop-shadow(0 0 8px rgba(231, 76, 60, 0.8))'
    },
    1: { // 仅label匹配 - 中等显眼
      stroke: '#f39c12',
      strokeWidth: 3,
      strokeOpacity: 1,
      filter: 'drop-shadow(0 0 5px rgba(243, 156, 18, 0.6))'
    },
    2: { // 仅content匹配 - 较弱显眼
      stroke: '#3498db',
      strokeWidth: 2,
      strokeOpacity: 0.8,
      filter: 'drop-shadow(0 0 3px rgba(52, 152, 219, 0.5))'
    }
  }
  
  return styles[matchType] || null
}

const syncD3Data = () => {
  const oldMap = new Map(d3Nodes.map(n => [n.id, n]))
  const w = svgRef.value?.clientWidth || 800, h = svgRef.value?.clientHeight || 600
  const padding = 100; // 边界内边距
  
  // 边界检查辅助函数
  const enforceBoundary = (x, y) => {
    const minX = padding;
    const maxX = w - padding;
    const minY = padding;
    const maxY = h - padding;
    
    return {
      x: Math.max(minX, Math.min(maxX, x)),
      y: Math.max(minY, Math.min(maxY, y))
    };
  };

  d3Nodes = (props.nodes || []).map(n => {
    const old = oldMap.get(n.id)
    if (old) return { 
      ...n, x: old.x, y: old.y, vx: old.vx ?? 0, vy: old.vy ?? 0, 
      fx: (props.mode === 'edit' && !isStabilizing.value) ? old.x : (n.fx ?? old.fx), 
      fy: (props.mode === 'edit' && !isStabilizing.value) ? old.y : (n.fy ?? old.fy) 
    }
    
    // 新节点：在更大范围内随机分布，但确保不在边界外
    const randomX = w/2 + (Math.random()-0.5) * (w - padding*2) * 0.7;
    const randomY = h/2 + (Math.random()-0.5) * (h - padding*2) * 0.7;
    const boundedPos = enforceBoundary(randomX, randomY);
    
    return { ...n, x: boundedPos.x, y: boundedPos.y, vx: 0, vy: 0 }
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
    .join('line').attr('class', 'link')
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
    // 应用搜索高亮样式
    .attr('stroke', function(d) {
      const highlight = getSearchHighlightStyle(d.id)
      if (highlight) {
        return highlight.stroke
      }
      return '#fff' // 默认白色边框
    })
    .attr('stroke-width', function(d) {
      const highlight = getSearchHighlightStyle(d.id)
      if (highlight) {
        return highlight.strokeWidth
      }
      return 2 // 默认边框宽度
    })
    .attr('stroke-opacity', function(d) {
      const highlight = getSearchHighlightStyle(d.id)
      if (highlight) {
        return highlight.strokeOpacity
      }
      return 1
    })
    .style('filter', function(d) {
      const highlight = getSearchHighlightStyle(d.id)
      if (highlight) {
        return highlight.filter
      }
      return 'none'
    })

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
    
    // 专业级物理参数优化 - 增强分散和稳定性
    simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).distance(70).strength(0.8))  // 增加距离，增强连接力
      .force('charge', d3.forceManyBody().strength(-300).distanceMax(100))      // 增强排斥力，扩大最大作用距离
      .force('center', d3.forceCenter(w/2, h/2).strength(0.1))                  // 减弱中心引力
      .force('collision', d3.forceCollide().radius(60))                         // 增加碰撞半径
      .velocityDecay(0.2) // 增加摩擦力，让节点更快停稳
      .alphaDecay(0.02)   // 减慢冷却速度，给予更多时间找到平衡位置
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
    // 动态计算预热次数：基础600次 + 每2个节点增加1次
    const preTickCount = 600 + Math.floor((props.nodes?.length || 0) / 2);
    console.log(`🔧 静默预热开始：${props.nodes?.length || 0}个节点，预计算${preTickCount}次`);
    
    for (let i = 0; i < preTickCount; ++i) simulation.tick();
    
    // 关键优化：预热后重置所有节点的速度，防止晃动
    d3Nodes.forEach(n => { n.vx = 0; n.vy = 0; });
    
    renderGraph(); // 此时再进行首屏渲染，节点已经是稳定的了

    // 动态计算等待时间：根据预热次数调整
    const stabilizationDelay = Math.max(100, Math.min(500, 50 + preTickCount / 10));
    console.log(`⏱️ 等待${stabilizationDelay}ms后完成稳定`);
    
    setTimeout(() => {
      isStabilizing.value = false;
      console.log(`✅ 布局稳定完成，准备显示`);
      if (props.mode === 'edit') {
        simulation.stop();
        d3Nodes.forEach(d => { d.fx = d.x; d.fy = d.y });
      }
      // 平滑居中
      d3.select(svgRef.value).transition().duration(800).call(zoom.transform, d3.zoomIdentity)
      ticked();
    }, stabilizationDelay);
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

// 监听搜索匹配变化，重新渲染节点高亮
watch(() => props.searchMatches, () => {
  if (props.searchMatches && props.searchMatches.size > 0) {
    // 触发节点样式更新
    nextTick(() => {
      if (svgRef.value) {
        const mainG = d3.select(mainGroup.value)
        mainG.select('#nodes-group').selectAll('.node-wrapper')
          .select('.node-shape')
          .attr('stroke', function(d) {
            const highlight = getSearchHighlightStyle(d.id)
            if (highlight) return highlight.stroke
            return '#fff'
          })
          .attr('stroke-width', function(d) {
            const highlight = getSearchHighlightStyle(d.id)
            if (highlight) return highlight.strokeWidth
            return 2
          })
          .attr('stroke-opacity', function(d) {
            const highlight = getSearchHighlightStyle(d.id)
            if (highlight) return highlight.strokeOpacity
            return 1
          })
          .style('filter', function(d) {
            const highlight = getSearchHighlightStyle(d.id)
            if (highlight) return highlight.filter
            return 'none'
          })
      }
    })
  }
}, { deep: true })
</script>