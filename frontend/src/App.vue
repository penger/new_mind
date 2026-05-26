<template>
  <div class="app-container">
    <!-- 登录页面 -->
    <LoginPage v-if="!isLoggedIn" @login="handleLogin" />
    
    <!-- 主应用 -->
    <template v-else>
    <el-header>
      <div class="header-left">
        <h1>关系图谱专业版</h1>
        <el-switch
          v-if="isAdmin || canEditCurrentTheme"
          v-model="isEditing"
          active-text="编辑模式"
          inactive-text="浏览模式"
          @change="handleEditChange"
          style="margin-left: 20px;"
        />
        <el-tag v-if="!isAdmin" type="info" size="small" style="margin-left: 20px;">
          👁️ 游客模式
        </el-tag>
        <el-tag v-else-if="isAdmin && !canEditCurrentTheme" type="warning" size="small" style="margin-left: 20px;">
          ⚠️ 只读主题
        </el-tag>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索节点..."
          size="default"
          clearable
          style="width: 200px; margin-right: 10px;"
          @input="handleSearch"
          @clear="handleSearchClear"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-radio-group v-model="viewType" size="default">
          <el-radio-button value="2d">平面图</el-radio-button>
          <el-radio-button value="3d">星云图</el-radio-button>
        </el-radio-group>
        <el-divider direction="vertical" v-if="isAdmin" />
        <el-button v-if="isAdmin" @click="handleBackup" :loading="isBackingUp">💾 备份数据</el-button>
        <el-button v-if="isAdmin" @click="openResourceManager">⚙️ 资源管理</el-button>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleUserCommand">
          <span class="user-dropdown">
            {{ isAdmin ? '🔐' : '👁️' }} {{ currentUser?.username || '用户' }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="manageUsers" v-if="isAdmin">👥 管理用户</el-dropdown-item>
              <el-dropdown-item command="logout">🚪 退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <div class="main-wrapper">
      <el-aside width="280px">
        <el-card class="sidebar-card">
          <template #header><span class="card-title">图层控制</span></template>
          <el-form label-position="top" size="small">
            <el-form-item label="主题过滤">
              <el-select 
                v-if="isDataLoaded && hasAccessibleThemes"
                v-model="activeThemeFilter" 
                @change="onThemeFilterChangeHandler" 
                style="width: 100%"
                placeholder="请选择主题"
                clearable
              >
                <el-option 
                  v-for="theme in accessibleThemes" 
                  :key="theme.id" 
                  :label="theme.name" 
                  :value="theme.id" 
                />
              </el-select>
              <div v-else-if="!isDataLoaded" class="loading-text">
                加载中...
              </div>
              <div v-else class="warning-text">
                暂无可访问的主题，请联系管理员分配
              </div>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="sidebar-card" style="margin-top: 12px;">
          <template #header><span class="card-title">选中详情</span></template>
          <div v-if="!selectedNodes || selectedNodes.length === 0" class="empty-text">{{ isEditing ? '点击节点进行编辑' : '点击节点查看详情' }}</div>
          <div v-else v-for="node in selectedNodes" :key="node.id" class="selection-item">
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div v-if="node.content && node.content.trim()" class="node-content" @click="copyToClipboard(node.content)" style="cursor: pointer;" title="点击复制内容">
                {{ node.content }}
              </div>
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
          :searchMatches="searchMatches"
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

      <UserManager
        v-model="isUserManagerOpen"
        :allThemes="themes"
        @refresh="handleUserManagerRefresh"
      />

      <!-- 内容查看模态框 -->
      <el-dialog
        v-model="isContentModalOpen"
        title="查看内容"
        width="80%"
        :close-on-click-modal="true"
        destroy-on-close
      >
        <div style="max-height: 70vh; overflow-y: auto; white-space: pre-wrap; font-family: monospace; font-size: 13px; line-height: 1.6;">
          {{ modalContent }}
        </div>
        <template #footer>
          <el-button type="primary" @click="isContentModalOpen = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import { debounce } from 'lodash'
import { useGraphCore } from './composables/useGraphCore'
import Graph2D from './components/Graph2D.vue'
import Graph3DView from './components/Graph3DView.vue'
import ResourceManager from './components/ResourceManager.vue'
import LoginPage from './components/LoginPage.vue'
import UserManager from './components/UserManager.vue'

const {
  nodes, links, nodeStyles, edgeStyles, themes, activeThemeFilter, visibleThemes,
  physicsEnabled, getNodeStyle, fetchDataFromServer, addNode, addEdge,
  updateNodeToServer, updateEdgeToServer, onThemeFilterChange, deleteNodesAndRelatedEdges, deleteEdge, refreshKey, isDataLoaded
} = useGraphCore()

// 用户认证状态
const isLoggedIn = ref(false)
const currentUser = ref(null)
const isAdmin = computed(() => currentUser.value?.role === 'admin')

// 根据用户权限过滤可访问的主题
const accessibleThemes = computed(() => {
  // 确保themes是一个数组（themes是ref，需要使用.value访问）
  const themesArray = Array.isArray(themes.value) ? themes.value : []
  
  if (isAdmin.value) {
    // 管理员可以访问所有主题
    return themesArray
  }
  
  // 普通用户只能访问分配给他的主题
  const userThemeIds = (currentUser.value?.themes || []).map(t => t.theme_id)
  return themesArray.filter(theme => userThemeIds.includes(theme.id))
})

// 检查是否有可访问的主题
const hasAccessibleThemes = computed(() => {
  return accessibleThemes.value.length > 0
})

// 检查activeThemeFilter对应的主题是否在accessibleThemes中
const isCurrentThemeAccessible = computed(() => {
  if (!activeThemeFilter.value) return false
  return accessibleThemes.value.some(t => t.id === activeThemeFilter.value)
})

// 获取当前选中的主题名称
const currentThemeName = computed(() => {
  if (!activeThemeFilter.value) return ''
  const theme = accessibleThemes.value.find(t => t.id === activeThemeFilter.value)
  return theme?.name || activeThemeFilter.value || '未知主题'
})

// 检查当前用户对当前主题是否有编辑权限
const canEditCurrentTheme = computed(() => {
  if (isAdmin.value) {
    return true
  }
  
  const userTheme = currentUser.value?.themes?.find(t => t.theme_id === activeThemeFilter.value)
  return userTheme?.can_edit === true
})

// 登录处理
const handleLogin = async (user) => {
  currentUser.value = user
  isLoggedIn.value = true
  isEditing.value = false // 登录后默认浏览模式
  await fetchDataFromServer(undefined, true)
}

// 监听isDataLoaded变化，确保主题过滤正确设置
watch(isDataLoaded, (loaded) => {
  if (loaded) {
    // 数据加载完成后，确保activeThemeFilter指向有效的主题
    const currentTheme = accessibleThemes.value.find(t => t.id === activeThemeFilter.value)
    
    if (!currentTheme && accessibleThemes.value.length > 0) {
      // 当前选择的主题无效，切换到第一个主题
      activeThemeFilter.value = accessibleThemes.value[0].id
      onThemeFilterChange(activeThemeFilter.value)
    } else if (currentTheme) {
      // 当前选择的主题有效，更新visibleThemes
      visibleThemes.value = new Set([activeThemeFilter.value])
    }
  }
})

// 监听用户主题权限变化
watch(() => currentUser.value?.themes, () => {
  // 当用户主题权限变化时，重新检查当前选择的主题是否有效
  if (isDataLoaded.value && activeThemeFilter.value) {
    const hasAccess = accessibleThemes.value.some(t => t.id === activeThemeFilter.value)
    if (!hasAccess && accessibleThemes.value.length > 0) {
      activeThemeFilter.value = accessibleThemes.value[0].id
    }
  }
}, { deep: true })

// 监听accessibleThemes变化，确保下拉框选择的主题和实际主题同步
watch([accessibleThemes, activeThemeFilter], ([themes, currentFilter]) => {
  if (themes.length > 0 && currentFilter) {
    const themeExists = themes.some(t => t.id === currentFilter)
    if (!themeExists) {
      // 如果当前选择的主题不在列表中，切换到第一个主题
      activeThemeFilter.value = themes[0].id
    }
  }
}, { immediate: true })

// 用户菜单操作
const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout()
  } else if (command === 'manageUsers') {
    isUserManagerOpen.value = true
  }
}

// 退出登录
const logout = () => {
  currentUser.value = null
  isLoggedIn.value = false
  isEditing.value = false
  localStorage.removeItem('user')
  ElMessage.info('已退出登录')
}

const handleUserManagerRefresh = () => {
  // 用户管理刷新后的回调，可以添加额外的逻辑
}

// 检查本地存储中的用户状态
const checkAuthStatus = () => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      currentUser.value = JSON.parse(storedUser)
      isLoggedIn.value = true
    } catch (e) {
      localStorage.removeItem('user')
    }
  }
}

const viewType = ref('2d'), isEditing = ref(false), isPanelOpen = ref(false), isInfoCardOpen = ref(false)
const isResourceManagerOpen = ref(false)
const isUserManagerOpen = ref(false)
const isContentModalOpen = ref(false)
const modalContent = ref('')
const searchQuery = ref('')
const searchMatches = ref(new Map()) // 存储匹配结果: nodeId -> matchType (0=不匹配, 1=仅label, 2=仅content, 3=两者都匹配)
const isBackingUp = ref(false)
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

// 格式化显示内容（处理JSON转义问题）
const formatDisplayContent = (content) => {
  if (!content) return ''
  
  // 尝试检测并解析双重编码的JSON
  try {
    // 检查是否包含转义的引号（双重编码的标志）
    if (content.includes('\\"') || content.includes('\\r') || content.includes('\\n')) {
      // 尝试解析为JSON
      const parsed = JSON.parse(content)
      // 重新格式化为易读的格式，然后清理转义字符
      let formatted = JSON.stringify(parsed, null, 2)
      // 替换 \r\n 为换行符，\n 也替换为换行符，其他 \ 为空格
      formatted = formatted
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, ' ')
        .replace(/\\t/g, '  ')
        .replace(/\\"/g, '"')
        .replace(/\\/g, '')
        // 清理连续多个空格（但保留换行）
        .split('\n')
        .map(line => line.replace(/\s+/g, ' ').trim())
        .join('\n')
        .trim()
      return formatted
    }
  } catch (e) {
    // 解析失败，可能不是JSON，返回原内容
  }
  
  // 如果内容看起来像JSON字符串（以引号开头和结尾），尝试解析
  const trimmed = content.trim()
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || 
      (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      const parsed = JSON.parse(trimmed)
      let formatted = JSON.stringify(parsed, null, 2)
      // 替换 \r\n 为换行符，\n 也替换为换行符，其他 \ 为空格
      formatted = formatted
        .replace(/\\r\\n/g, '\n')
        .replace(/\\n/g, '\n')
        .replace(/\\t/g, '  ')
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, '\\')
        // 清理连续多个空格（但保留换行）
        .split('\n')
        .map(line => line.replace(/\s+/g, ' ').trim())
        .join('\n')
        .trim()
      return formatted
    } catch (e) {
      // 解析失败，返回原内容
    }
  }
  
  // 对非JSON内容也进行清理
  return content
    .replace(/\\r\\n/g, '\n')
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '  ')
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, '\\')
    // 清理连续多个空格（但保留换行）
    .split('\n')
    .map(line => line.replace(/\s+/g, ' ').trim())
    .join('\n')
    .trim()
}

// 复制内容到剪贴板并显示模态框
const copyToClipboard = async (content) => {
  if (!content) return
  
  // 显示模态框（使用格式化后的内容）
  modalContent.value = formatDisplayContent(content)
  isContentModalOpen.value = true
  
  // 复制原始内容到剪贴板
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('内容已复制到剪贴板')
  } catch (err) {
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement('textarea')
    textArea.value = content
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('内容已复制到剪贴板')
    } catch (err2) {
      ElMessage.error('复制失败，请手动复制')
    }
    document.body.removeChild(textArea)
  }
}

// 复制模态框内容到剪贴板（复制格式化后的内容）
const copyModalContent = async () => {
  if (!modalContent.value) return
  try {
    await navigator.clipboard.writeText(modalContent.value)
    ElMessage.success('内容已复制到剪贴板')
  } catch (err) {
    const textArea = document.createElement('textarea')
    textArea.value = modalContent.value
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('内容已复制到剪贴板')
    } catch (err2) {
      ElMessage.error('复制失败')
    }
    document.body.removeChild(textArea)
  }
}

// 防抖搜索函数 - 延迟 300ms 执行
const debouncedSearch = debounce(() => {
  performSearch()
}, 300)

// 搜索处理函数
const handleSearch = () => {
  debouncedSearch()
}

// 清除搜索
const handleSearchClear = () => {
  searchQuery.value = ''
  searchMatches.value = new Map()
  debouncedSearch.cancel() // 取消待执行的搜索
  ElMessage.info('已清除搜索')
}

// 执行搜索
const performSearch = () => {
  const query = searchQuery.value.trim().toLowerCase()
  
  if (!query) {
    searchMatches.value = new Map()
    return
  }
  
  const matches = new Map()
  const currentNodes = nodes.value || []
  
  currentNodes.forEach(node => {
    const label = (node.label || '').toLowerCase()
    const content = (node.content || '').toLowerCase()
    
    const labelMatch = label.includes(query)
    const contentMatch = content.includes(query)
    
    let matchType = 0
    if (labelMatch && contentMatch) {
      matchType = 3 // 两者都匹配
    } else if (labelMatch) {
      matchType = 1 // 仅label匹配
    } else if (contentMatch) {
      matchType = 2 // 仅content匹配
    }
    
    if (matchType > 0) {
      matches.set(node.id, matchType)
    }
  })
  
  searchMatches.value = matches
  
  if (matches.size > 0) {
    ElMessage.success(`找到 ${matches.size} 个匹配结果`)
  } else {
    ElMessage.warning('未找到匹配结果')
  }
}
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
const onThemeFilterChangeHandler = () => {
  // 切换主题时自动切换到浏览模式，确保显示一致性
  if (isEditing.value) {
    console.log('🔀 切换主题，自动切换到浏览模式')
    isEditing.value = false
    selectedNodeIds.value = []
    selectedLinkIds.value = []
    isPanelOpen.value = false
    
    // 完整重置编辑项到初始状态
    editingItem.id = ''
    editingItem.type = 'node'
    editingItem.label = ''
    editingItem.content = ''
    editingItem.size = 18
    editingItem.style = {}
  }
  onThemeFilterChange(activeThemeFilter.value)
}
const openResourceManager = () => { isResourceManagerOpen.value = true }
const handleResourceRefresh = async () => { await fetchDataFromServer() }

const handleBackup = async () => {
  if (isBackingUp.value) return
  
  isBackingUp.value = true
  try {
    const response = await fetch(`/api/backup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (!response.ok) {
      throw new Error('Backup failed')
    }
    
    const result = await response.json()
    ElMessage.success(`备份成功！时间戳: ${result.timestamp}`)
  } catch (error) {
    console.error('Backup error:', error)
    ElMessage.error('备份失败: ' + error.message)
  } finally {
    isBackingUp.value = false
  }
}

onMounted(async () => {
  checkAuthStatus()
  if (isLoggedIn.value) {
    await fetchDataFromServer(undefined, true)
  }
})

// 监听主题变化，如果切换到没有编辑权限的主题，自动关闭编辑模式
watch(activeThemeFilter, () => {
  if (!canEditCurrentTheme.value && isEditing.value) {
    isEditing.value = false
    ElMessage.warning('当前主题没有编辑权限')
  }
})

// 当可访问的主题列表变化时，如果当前选择的主题不在列表中，自动切换到第一个主题
watch(accessibleThemes, (newThemes) => {
  if (newThemes.length > 0 && activeThemeFilter.value) {
    const currentExists = newThemes.some(t => t.id === activeThemeFilter.value)
    if (!currentExists) {
      activeThemeFilter.value = newThemes[0].id
    }
  }
}, { deep: true })
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

/* 侧边栏卡片样式 */
.sidebar-card { border: none; box-shadow: none; }
.sidebar-card :deep(.el-card__header) { padding: 12px 16px; border-bottom: 1px solid #ebeef5; }
.sidebar-card :deep(.el-card__body) { padding: 16px; }

/* 主题过滤下拉框样式 */
.el-select { width: 100% !important; }
.el-select :deep(.el-input__wrapper) { width: 100%; }
.el-form-item { margin-bottom: 12px; }
.el-form-item__label { padding: 0 0 8px 0 !important; font-weight: 500; color: #303133; }

/* 加载和警告文本样式 */
.loading-text { color: #909399; font-size: 12px; padding: 8px 0; }
.warning-text { color: #e6a23c; font-size: 12px; padding: 8px 0; }

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

/* 用户下拉菜单样式 */
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
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
</style>