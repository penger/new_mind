import { ref, reactive, computed } from 'vue'

const API_BASE_URL = '/api'

export function useGraphCore() {
  const nodes = ref([])
  const links = ref([])
  const nodeStyles = ref([])
  const edgeStyles = ref([])
  const themes = ref([])

  const activeThemeFilter = ref(null)
  const visibleThemes = ref(new Set())
  const showLinkLabels = ref(true)
  const physicsEnabled = ref(true)

  const nodeIdCounter = ref(1)
  const linkIdCounter = ref(1)
  const resourceIdCounter = ref(1)
  const refreshKey = ref(0)

  const getNodeStyle = (id) => nodeStyles.value.find(s => s.id === id) || nodeStyles.value[0]
  const getEdgeStyle = (id) => edgeStyles.value.find(s => s.id === id) || edgeStyles.value[0]
  const getThemeName = (themeId) => themes.value.find(t => t.id === themeId)?.name || '未知'

  const syncCounters = () => {
    if (nodes.value.length) {
      nodeIdCounter.value = Math.max(...nodes.value.map(n => parseInt(n.id.replace('N',''))||0)) + 1
    }
    if (links.value.length) {
      linkIdCounter.value = Math.max(...links.value.map(l => parseInt(l.id.replace('E',''))||0)) + 1
    }
    resourceIdCounter.value = Math.max(
      ...themes.value.map(t => parseInt(t.id.replace('T',''))||0),
      ...nodeStyles.value.map(ns => parseInt(ns.id.replace('NS',''))||0),
      ...edgeStyles.value.map(es => parseInt(es.id.replace('ES',''))||0),
      0
    ) + 1
  }

  const fetchDataFromServer = async (themeId = undefined) => {
    try {
      const url = themeId !== undefined && themeId !== null && themeId !== ''
        ? `${API_BASE_URL}/data?theme_id=${encodeURIComponent(themeId)}`
        : `${API_BASE_URL}/data`
      const response = await fetch(url)
      if (!response.ok) throw new Error('网络错误')
      const data = await response.json()
      nodeStyles.value = data.nodeStyles || []
      edgeStyles.value = data.edgeStyles || []
      themes.value = data.themes || []
      nodes.value = data.nodes || []
      links.value = data.links || []
      if (themes.value.length === 0) {
        await initDefaultData()
      }
      syncCounters()
      themes.value.sort((a, b) => (b.sortNum || 0) - (a.sortNum || 0))
      if (themeId !== undefined && themeId !== null && themeId !== '') {
        visibleThemes.value = new Set([themeId])
      } else {
        visibleThemes.value = new Set([themes.value[0]?.id])
        activeThemeFilter.value = themes.value[0]?.id || null
      }
    } catch (error) {
      await initDefaultData()
    }
  }

  const initDefaultData = async () => {
    nodeStyles.value = [{ id: 'NS1', name: '默认节点', color: '#3498db', shape: 'circle', opacity: 1 }]
    edgeStyles.value = [{ id: 'ES1', name: '默认连线', color: '#95a5a6', style: 'solid' }]
    themes.value = [{ id: 'T1', name: '默认主题', defaultNodeStyleId: 'NS1', defaultEdgeStyleId: 'ES1', sortNum: 1 }]
    nodes.value = []
    links.value = []
    resourceIdCounter.value = 2
    activeThemeFilter.value = 'T1'
    visibleThemes.value = new Set(['T1'])
  }

  const addNodeToServer = async (node) => {
    try {
      const response = await fetch(`${API_BASE_URL}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: node.id, label: node.label, size: node.size, themeId: node.themeId,
          nodeStyleId: node.nodeStyleId, content: node.content, style: node.style
        })
      })
      if (!response.ok) throw new Error('保存节点失败')
      const result = await response.json()
      if (result.id && result.id !== node.id) {
        const localNode = nodes.value.find(n => n.id === node.id)
        if (localNode) {
          localNode.id = result.id
        }
      }
      return true
    } catch (error) {
      console.error('保存节点失败:', error)
      return false
    }
  }

  const updateNodeToServer = async (node) => {
    try {
      const response = await fetch(`${API_BASE_URL}/nodes/${node.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: node.id, label: node.label, size: node.size, themeId: node.themeId,
          nodeStyleId: node.nodeStyleId, content: node.content, style: node.style
        })
      })
      if (!response.ok) throw new Error('保存节点失败')
      return true
    } catch (error) {
      console.error('保存节点失败:', error)
      return false
    }
  }

  const deleteNodeToServer = async (nodeId) => {
    try { await fetch(`${API_BASE_URL}/nodes/${nodeId}`, { method: 'DELETE' }); return true } 
    catch (error) { console.error('删除节点失败:', error); return false }
  }

  const addEdgeToServer = async (edge) => {
    try {
      const response = await fetch(`${API_BASE_URL}/edges`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: edge.id, source: typeof edge.source === 'object' ? edge.source.id : edge.source,
          target: typeof edge.target === 'object' ? edge.target.id : edge.target,
          label: edge.label, width: edge.width, themeId: edge.themeId,
          edgeStyleId: edge.edgeStyleId, content: edge.content, style: edge.style
        })
      })
      if (!response.ok) throw new Error('保存连线失败')
      return true
    } catch (error) {
      console.error('保存连线失败:', error)
      return false
    }
  }

  const updateEdgeToServer = async (edge) => {
    try {
      const response = await fetch(`${API_BASE_URL}/edges/${edge.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: edge.id, source: typeof edge.source === 'object' ? edge.source.id : edge.source,
          target: typeof edge.target === 'object' ? edge.target.id : edge.target,
          label: edge.label, width: edge.style?.width || edge.width, themeId: edge.themeId,
          edgeStyleId: edge.edgeStyleId, content: edge.content, style: edge.style
        })
      })
      if (!response.ok) throw new Error('保存连线失败')
      return true
    } catch (error) {
      console.error('保存连线失败:', error)
      return false
    }
  }

  const deleteEdgeToServer = async (edgeId) => {
    try { await fetch(`${API_BASE_URL}/edges/${edgeId}`, { method: 'DELETE' }); return true } 
    catch (error) { console.error('删除连线失败:', error); return false }
  }

  const addNode = async (x, y) => {
    const theme = themes.value.find(t => t.id === activeThemeFilter.value) || themes.value[0]
    const nodeStyle = theme.defaultNodeStyleId
      ? nodeStyles.value.find(s => s.id === theme.defaultNodeStyleId) : nodeStyles.value[0]
    const newNode = {
      id: `N${nodeIdCounter.value++}`, label: `节点${nodeIdCounter.value - 1}`,
      x, y, fx: x, fy: y, // 刚创建时默认锁定坐标，防止飘走
      themeId: theme.id, nodeStyleId: nodeStyle?.id || nodeStyles.value[0]?.id,
      size: 10, content: '', selected: true,
      style: nodeStyle ? { color: nodeStyle.color, shape: nodeStyle.shape, opacity: nodeStyle.opacity } : null
    }
    nodes.value.push(newNode)
    await addNodeToServer(newNode)
    return newNode
  }

  const addEdge = async (source, target) => {
    if (source === target) return null
    const sid = source.id || source
    const tid = target.id || target

    const exists = links.value.find(l => {
      const lsid = typeof l.source === 'object' ? l.source.id : l.source
      const ltid = typeof l.target === 'object' ? l.target.id : l.target
      return (lsid === sid && ltid === tid) || (lsid === tid && ltid === sid)
    })
    if (exists) return null

    const theme = themes.value.find(t => t.id === activeThemeFilter.value) || themes.value[0]
    const edgeStyle = theme.defaultEdgeStyleId
      ? edgeStyles.value.find(s => s.id === theme.defaultEdgeStyleId) : edgeStyles.value[0]

    const newEdge = {
      id: `E${linkIdCounter.value++}`, source: sid, target: tid, label: '', width: 2,
      themeId: theme.id, edgeStyleId: edgeStyle?.id || edgeStyles.value[0]?.id,
      content: '', selected: false,
      style: edgeStyle ? { color: edgeStyle.color, style: edgeStyle.style, width: 2 } : null
    }
    links.value.push(newEdge)
    await addEdgeToServer(newEdge)
    return newEdge
  }

  const deleteNode = async (nodeId) => {
    await deleteNodeToServer(nodeId)
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
  }

  const deleteEdge = async (edgeId) => {
    await deleteEdgeToServer(edgeId)
    links.value = links.value.filter(l => l.id !== edgeId)
  }

  const deleteNodesAndRelatedEdges = async (nodeIds) => {
    for (const nodeId of nodeIds) await deleteNodeToServer(nodeId)
    for (const nodeId of nodeIds) {
      links.value = links.value.filter(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source
        const targetId = typeof l.target === 'object' ? l.target.id : l.target
        return sourceId !== nodeId && targetId !== nodeId
      })
    }
    nodes.value = nodes.value.filter(n => !nodeIds.includes(n.id))
  }

  const onThemeFilterChange = async (themeId) => {
    activeThemeFilter.value = themeId
    visibleThemes.value = new Set([themeId])
    refreshKey.value++
    await fetchDataFromServer(themeId)
  }

  return {
    nodes, links, nodeStyles, edgeStyles, themes, activeThemeFilter, visibleThemes,
    showLinkLabels, physicsEnabled, nodeIdCounter, linkIdCounter, resourceIdCounter, refreshKey,
    getNodeStyle, getEdgeStyle, getThemeName, syncCounters, fetchDataFromServer,
    initDefaultData, addNode, addEdge, deleteNode, deleteEdge, deleteNodesAndRelatedEdges,
    updateNodeToServer, updateEdgeToServer, onThemeFilterChange
  }
}