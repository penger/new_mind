<template>
  <el-drawer
    v-model="visible"
    title="资源配置中心"
    direction="rtl"
    size="1000px"
    custom-class="resource-manager-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <span class="title">资源配置中心</span>
        <div class="stats">
          <el-tag type="info" effect="plain">{{ themes.length }} 主题</el-tag>
          <el-tag type="info" effect="plain" class="ml-2">{{ nodeStyles.length }} 节点样式</el-tag>
        </div>
      </div>
    </template>

    <el-tabs v-model="activeTab" class="resource-tabs" type="border-card">
      <el-tab-pane name="themes">
        <template #label>
          <div class="tab-label"><el-icon><Collection /></el-icon> 主题管理</div>
        </template>
        <div class="tab-content">
          <div class="toolbar">
            <el-input
              v-model="searchQuery.themes"
              placeholder="搜索主题名称或ID..."
              prefix-icon="Search"
              clearable
              class="search-input"
            />
            <el-button type="primary" icon="Plus" @click="openThemeDialog()">新建主题</el-button>
          </div>
          
          <el-table :data="filteredThemes" border stripe size="small" highlight-current-row>
            <el-table-column prop="name" label="主题名称" min-width="120">
              <template #default="{ row }">
                <div class="name-cell">
                  <span class="main-name">{{ row.name }}</span>
                  <span class="sub-id">{{ row.id }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="sortNum" label="排序值" width="100" align="center" sortable>
              <template #default="{ row }">
                <el-input
                  v-model="row.sortNum"
                  type="number"
                  size="small"
                  style="width: 70px;"
                  :min="0"
                  :max="9999"
                  @change="handleSortNumChange(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="默认配置" width="300">
              <template #default="{ row }">
                <div class="config-tags">
                  <el-tooltip 
                    :content="row.defaultNodeStyleIds?.length > 0 ? row.defaultNodeStyleIds.join(', ') : '无默认节点样式'" 
                    placement="top"
                  >
                    <el-tag size="small" effect="light" type="success" v-if="row.defaultNodeStyleIds?.length > 0">
                      <el-icon><Avatar /></el-icon> {{ row.defaultNodeStyleIds?.length }} 个节点样式
                    </el-tag>
                    <el-tag size="small" effect="light" type="info" v-else>
                      <el-icon><Avatar /></el-icon> 无节点样式
                    </el-tag>
                  </el-tooltip>
                  <el-tooltip 
                    :content="row.defaultEdgeStyleIds?.length > 0 ? row.defaultEdgeStyleIds.join(', ') : '无默认边样式'" 
                    placement="top"
                  >
                    <el-tag size="small" effect="light" type="warning" v-if="row.defaultEdgeStyleIds?.length > 0">
                      <el-icon><Share /></el-icon> {{ row.defaultEdgeStyleIds?.length }} 个边样式
                    </el-tag>
                    <el-tag size="small" effect="light" type="info" v-else>
                      <el-icon><Share /></el-icon> 无边样式
                    </el-tag>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="openThemeDialog(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="deleteTheme(row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane name="nodeStyles">
        <template #label>
          <div class="tab-label"><el-icon><Coordinate /></el-icon> 节点样式</div>
        </template>
        <div class="tab-content">
          <div class="toolbar">
            <el-input
              v-model="searchQuery.nodeStyles"
              placeholder="搜索样式名称..."
              prefix-icon="Search"
              clearable
              class="search-input"
            />
            <el-button type="primary" icon="Plus" @click="openNodeStyleDialog()">新建节点样式</el-button>
          </div>
          <el-table :data="filteredNodeStyles" border stripe size="small">
            <el-table-column prop="name" label="样式名称" min-width="120" />
            <el-table-column label="外观预览" width="160" align="center">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span :style="{ backgroundColor: row.color, display: 'inline-block', width: '16px', height: '16px', borderRadius: row.shape === 'circle' ? '50%' : '2px' }"></span>
                  <el-tag size="small" type="info">{{ row.shape }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="opacity" label="透明度" width="100" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.opacity * 100" :show-text="false" :stroke-width="12" />
                <span class="opacity-val">{{ row.opacity }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="openNodeStyleDialog(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="deleteNodeStyle(row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane name="edgeStyles">
        <template #label>
          <div class="tab-label"><el-icon><Connection /></el-icon> 连线样式</div>
        </template>
        <div class="tab-content">
          <div class="toolbar">
            <el-input
              v-model="searchQuery.edgeStyles"
              placeholder="搜索连线样式..."
              prefix-icon="Search"
              clearable
              class="search-input"
            />
            <el-button type="primary" icon="Plus" @click="openEdgeStyleDialog()">新建连线样式</el-button>
          </div>
          <el-table :data="filteredEdgeStyles" border stripe size="small">
            <el-table-column prop="name" label="样式名称" min-width="120" />
            <el-table-column label="线型预览" width="200">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span :style="{ backgroundColor: row.color, display: 'inline-block', width: '16px', height: '4px', borderRadius: '2px' }"></span>
                  <el-tag size="small" type="info">{{ getLineStyleLabel(row.line_style) }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="openEdgeStyleDialog(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="deleteEdgeStyle(row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="themeDialogVisible" :title="editingTheme?.id ? '编辑主题' : '新建主题'" width="600px" append-to-body>
      <el-form :model="themeForm" label-position="top">
        <el-form-item label="主题显示名称" required>
          <el-input v-model="themeForm.name" placeholder="请输入主题名称" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-tooltip content="数值越高，排序越靠前。首页默认显示排序最高的主题。留空则默认为0。" placement="top">
            <el-input
              v-model="themeForm.sortNum"
              type="number"
              placeholder="输入排序值（数字）"
              style="width: 200px;"
            />
          </el-tooltip>
        </el-form-item>
        <el-form-item label="默认节点样式">
          <div class="style-multi-select">
            <el-select 
              v-model="selectedNodeStyle" 
              placeholder="选择节点样式添加到列表" 
              class="w-full mb-2"
              @change="addNodeStyle"
            >
              <el-option 
                v-for="s in nodeStyles" 
                :key="s.id" 
                :label="s.name" 
                :value="s.id"
              />
            </el-select>
            
            <div class="selected-styles" v-if="themeForm.defaultNodeStyleIds.length > 0">
              <div v-for="styleId in themeForm.defaultNodeStyleIds" :key="styleId" class="style-item">
                <el-tag 
                  type="success" 
                  size="small" 
                  closable 
                  @close="removeNodeStyle(styleId)"
                >
                  {{ getNodeStyleName(styleId) }}
                </el-tag>
              </div>
            </div>
            <div v-else class="empty-styles">
              <el-text type="info">暂无选择的节点样式</el-text>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="默认连线样式">
          <div class="style-multi-select">
            <el-select 
              v-model="selectedEdgeStyle" 
              placeholder="选择连线样式添加到列表" 
              class="w-full mb-2"
              @change="addEdgeStyle"
            >
              <el-option 
                v-for="s in edgeStyles" 
                :key="s.id" 
                :label="s.name" 
                :value="s.id"
              />
            </el-select>
            
            <div class="selected-styles" v-if="themeForm.defaultEdgeStyleIds.length > 0">
              <div v-for="styleId in themeForm.defaultEdgeStyleIds" :key="styleId" class="style-item">
                <el-tag 
                  type="warning" 
                  size="small" 
                  closable 
                  @close="removeEdgeStyle(styleId)"
                >
                  {{ getEdgeStyleName(styleId) }}
                </el-tag>
              </div>
            </div>
            <div v-else class="empty-styles">
              <el-text type="info">暂无选择的连线样式</el-text>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="themeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTheme" :loading="loading">确认保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="nodeStyleDialogVisible" :title="editingNodeStyle?.id ? '编辑节点样式' : '新建节点样式'" width="480px" append-to-body>
      <el-form :model="nodeStyleForm" label-position="top">
        <el-form-item label="样式名称" required>
          <el-input v-model="nodeStyleForm.name" placeholder="如: 核心人物样式" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="节点颜色">
              <el-color-picker v-model="nodeStyleForm.color" show-alpha class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="节点形状">
              <el-select v-model="nodeStyleForm.shape" class="w-full">
                <el-option label="圆形" value="circle" />
                <el-option label="方形" value="square" />
                <el-option label="三角形" value="triangle" />
                <el-option label="菱形" value="diamond" />
                <el-option label="星形" value="star" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="透明度">
          <el-slider v-model="nodeStyleForm.opacity" :min="0" :max="1" :step="0.1" :format-tooltip="v => (v * 100).toFixed(0) + '%'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="nodeStyleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNodeStyle" :loading="loading">确认保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="edgeStyleDialogVisible" :title="editingEdgeStyle?.id ? '编辑连线样式' : '新建连线样式'" width="480px" append-to-body>
      <el-form :model="edgeStyleForm" label-position="top">
        <el-form-item label="样式名称" required>
          <el-input v-model="edgeStyleForm.name" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="连线颜色">
              <el-color-picker v-model="edgeStyleForm.color" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="线型选择">
              <el-select v-model="edgeStyleForm.line_style" class="w-full">
                <el-option label="实线" value="solid" />
                <el-option label="虚线" value="dashed" />
                <el-option label="点线" value="dotted" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="edgeStyleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdgeStyle" :loading="loading">确认保存</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox, ElText } from 'element-plus'
import { Collection, Coordinate, Connection, Plus, Search, Edit, Delete, Share, Avatar } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  themes: { type: Array, default: () => [] },
  nodeStyles: { type: Array, default: () => [] },
  edgeStyles: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const activeTab = ref('themes')
const loading = ref(false)
const searchQuery = reactive({
  themes: '',
  nodeStyles: '',
  edgeStyles: ''
})

// 搜索过滤逻辑
const filteredThemes = computed(() => {
  const q = searchQuery.themes.toLowerCase()
  return props.themes.filter(t => t.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q))
})

const filteredNodeStyles = computed(() => {
  const q = searchQuery.nodeStyles.toLowerCase()
  return props.nodeStyles.filter(s => s.name.toLowerCase().includes(q))
})

const filteredEdgeStyles = computed(() => {
  const q = searchQuery.edgeStyles.toLowerCase()
  return props.edgeStyles.filter(s => s.name.toLowerCase().includes(q))
})

// 视觉预览辅助函数
const getLineStyleLabel = (style) => {
  const labels = { solid: '实线', dashed: '虚线', dotted: '点线' }
  return labels[style] || style
}

// 表单与 Dialog 逻辑
const themeDialogVisible = ref(false)
const nodeStyleDialogVisible = ref(false)
const edgeStyleDialogVisible = ref(false)

const editingTheme = ref(null)
const editingNodeStyle = ref(null)
const editingEdgeStyle = ref(null)

// 多选相关变量
const selectedNodeStyle = ref('')
const selectedEdgeStyle = ref('')

const themeForm = reactive({ 
  id: '', 
  name: '', 
  defaultNodeStyleId: '', 
  defaultEdgeStyleId: '',
  defaultNodeStyleIds: [],  // 解析后的数组格式
  defaultEdgeStyleIds: [],  // 解析后的数组格式
  sortNum: 0                // 添加排序字段
})
const nodeStyleForm = reactive({ id: '', name: '', color: '#3498db', shape: 'circle', opacity: 1 })
const edgeStyleForm = reactive({ id: '', name: '', color: '#95a5a6', line_style: 'solid' })

const getNodeStyleName = (id) => props.nodeStyles.find(s => s.id === id)?.name || '-'
const getEdgeStyleName = (id) => props.edgeStyles.find(s => s.id === id)?.name || '-'

// 分隔符字符串处理函数
const STYLE_ID_DELIMITER = ','

const parseStyleIds = (styleIdsString) => {
  if (!styleIdsString || styleIdsString === '') return []
  return styleIdsString.split(STYLE_ID_DELIMITER)
    .map(id => id.trim())
    .filter(id => id.length > 0)
}

const serializeStyleIds = (styleIdsArray) => {
  if (!styleIdsArray || styleIdsArray.length === 0) return ''
  return styleIdsArray.join(STYLE_ID_DELIMITER)
}

// 多选样式处理函数
const addNodeStyle = () => {
  if (selectedNodeStyle.value && !themeForm.defaultNodeStyleIds.includes(selectedNodeStyle.value)) {
    themeForm.defaultNodeStyleIds.push(selectedNodeStyle.value)
    // 清空选择
    selectedNodeStyle.value = ''
  }
}

const removeNodeStyle = (styleId) => {
  themeForm.defaultNodeStyleIds = themeForm.defaultNodeStyleIds.filter(id => id !== styleId)
}

const addEdgeStyle = () => {
  if (selectedEdgeStyle.value && !themeForm.defaultEdgeStyleIds.includes(selectedEdgeStyle.value)) {
    themeForm.defaultEdgeStyleIds.push(selectedEdgeStyle.value)
    // 清空选择
    selectedEdgeStyle.value = ''
  }
}

const removeEdgeStyle = (styleId) => {
  themeForm.defaultEdgeStyleIds = themeForm.defaultEdgeStyleIds.filter(id => id !== styleId)
}

// 通用保存封装
const request = async (url, method, body, callback) => {
  loading.value = true
  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!res.ok) throw new Error('操作失败')
    ElMessage.success('保存成功')
    callback()
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

// 主题排序值快速更新
const handleSortNumChange = async (theme) => {
  try {
    const response = await fetch(`/api/themes/${theme.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: theme.name,
        defaultNodeStyleIds: theme.defaultNodeStyleIds,
        defaultEdgeStyleIds: theme.defaultEdgeStyleIds,
        sortNum: theme.sortNum || 0
      })
    })
    if (response.ok) {
      ElMessage.success('排序值已更新')
      emit('refresh')
    } else {
      throw new Error('更新失败')
    }
  } catch (e) {
    ElMessage.error('更新排序值失败: ' + e.message)
  }
}

// 主题操作
const openThemeDialog = (theme = null) => {
  editingTheme.value = theme
  if (theme) {
    // 解析theme数据
    const themeData = {
      id: theme.id,
      name: theme.name,
      defaultNodeStyleId: theme.defaultNodeStyleId || '',
      defaultEdgeStyleId: theme.defaultEdgeStyleId || '',
      defaultNodeStyleIds: parseStyleIds(theme.defaultNodeStyleId),
      defaultEdgeStyleIds: parseStyleIds(theme.defaultEdgeStyleId),
      sortNum: Number(theme.sortNum) || 0
    }
    Object.assign(themeForm, themeData)
  } else {
    Object.assign(themeForm, {
      name: '',
      defaultNodeStyleId: '',
      defaultEdgeStyleId: '',
      defaultNodeStyleIds: [],
      defaultEdgeStyleIds: [],
      sortNum: 0
    })
  }
  themeDialogVisible.value = true
}

const saveTheme = () => {
  const isEdit = !!editingTheme.value?.id
  const method = isEdit ? 'PUT' : 'POST'
  const url = isEdit ? `/api/themes/${editingTheme.value.id}` : '/api/themes'

  // 准备发送的数据
  const requestData = {
    // 编辑模式下发送ID，创建模式下不发送ID（由后端生成UUID）
    ...(isEdit && { id: editingTheme.value.id }),
    name: themeForm.name,
    defaultNodeStyleIds: themeForm.defaultNodeStyleIds,
    defaultEdgeStyleIds: themeForm.defaultEdgeStyleIds,
    sortNum: themeForm.sortNum || 0
  }

  request(url, method, requestData, () => themeDialogVisible.value = false)
}

const deleteTheme = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除吗？', '确认', { type: 'warning' })
    const res = await fetch(`/api/themes/${id}`, { method: 'DELETE' })
    if (res.ok) { ElMessage.success('已删除'); emit('refresh') }
  } catch (e) { /* cancel */ }
}

// 节点样式操作
const openNodeStyleDialog = (style = null) => {
  editingNodeStyle.value = style
  Object.assign(nodeStyleForm, style || { id: `NS_${Date.now()}`, name: '', color: '#3498db', shape: 'circle', opacity: 1 })
  nodeStyleDialogVisible.value = true
}

const saveNodeStyle = () => {
  const method = editingNodeStyle.value?.id ? 'PUT' : 'POST'
  const url = editingNodeStyle.value?.id ? `/api/node-styles/${editingNodeStyle.value.id}` : '/api/node-styles'
  request(url, method, nodeStyleForm, () => nodeStyleDialogVisible.value = false)
}

const deleteNodeStyle = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该样式吗？', '确认', { type: 'warning' })
    const res = await fetch(`/api/node-styles/${id}`, { method: 'DELETE' })
    if (res.ok) { ElMessage.success('已删除'); emit('refresh') }
  } catch (e) { /* cancel */ }
}

// 连线样式操作
const openEdgeStyleDialog = (style = null) => {
  editingEdgeStyle.value = style
  Object.assign(edgeStyleForm, style || { id: `ES_${Date.now()}`, name: '', color: '#95a5a6', line_style: 'solid' })
  edgeStyleDialogVisible.value = true
}

const saveEdgeStyle = () => {
  const method = editingEdgeStyle.value?.id ? 'PUT' : 'POST'
  const url = editingEdgeStyle.value?.id ? `/api/edge-styles/${editingEdgeStyle.value.id}` : '/api/edge-styles'
  request(url, method, edgeStyleForm, () => edgeStyleDialogVisible.value = false)
}

const deleteEdgeStyle = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除？', '确认', { type: 'warning' })
    const res = await fetch(`/api/edge-styles/${id}`, { method: 'DELETE' })
    if (res.ok) { ElMessage.success('已删除'); emit('refresh') }
  } catch (e) { /* cancel */ }
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 20px;
}
.drawer-header .title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-content {
  padding: 15px 5px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 10px;
}

.search-input {
  max-width: 300px;
}

.name-cell {
  display: flex;
  flex-direction: column;
}
.main-name {
  font-weight: bold;
  color: #409EFF;
}
.sub-id {
  font-size: 11px;
  color: #909399;
}

.config-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.w-full {
  width: 100%;
}

.ml-2 {
  margin-left: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

:deep(.el-drawer__body) {
  padding: 0;
}
:deep(.el-tabs--border-card) {
  border: none;
}
:deep(.el-tabs__content) {
  height: calc(100vh - 110px);
  overflow-y: auto;
}

/* 多选组件的样式 */
.style-multi-select {
  width: 100%;
}

.selected-styles {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  max-height: 120px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fafbfc;
}

.style-item {
  display: flex;
  align-items: center;
}

.style-item .el-tag {
  transition: all 0.2s ease;
}

.style-item .el-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.empty-styles {
  padding: 20px;
  text-align: center;
  color: #909399;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  margin-top: 10px;
  background-color: #fafbfc;
}

/* 自定义边距 */
.mb-2 {
  margin-bottom: 8px !important;
}
</style>