<template>
  <el-drawer
    v-model="visible"
    title="用户管理"
    size="900px"
    :before-close="handleClose"
  >
    <div class="user-manager">
      <div class="toolbar">
        <el-button type="primary" @click="showAddUserDialog">
          添加用户
        </el-button>
      </div>

      <el-table :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '游客' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联主题" min-width="200">
          <template #default="{ row }">
            <div class="theme-tags">
              <el-tag
                v-for="theme in row.themes"
                :key="theme.theme_id"
                size="small"
                :type="theme.can_edit === true ? 'success' : 'info'"
                closable
                @close="removeThemeFromUser(row, theme.theme_id)"
                style="margin-right: 4px; margin-bottom: 4px;"
              >
                {{ theme.theme_name }}
                <span v-if="theme.can_edit" style="margin-left: 4px;">✏️</span>
              </el-tag>
              <el-button size="small" text @click="showThemeSelector(row)">
                + 添加主题
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditPasswordDialog(row)">
              修改密码
            </el-button>
            <el-popconfirm
              title="确定要删除这个用户吗？"
              @confirm="deleteUser(row)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="addUserDialogVisible" title="添加用户" width="400px">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="newUser.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="newUser.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="newUser.role">
            <el-radio value="viewer">游客</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addUser" :loading="loading">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editPasswordDialogVisible" title="修改密码" width="400px">
      <el-form :model="editPasswordForm" label-width="80px">
        <el-form-item label="用户名">
          <span>{{ editPasswordForm.username }}</span>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="editPasswordForm.password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="updatePassword" :loading="loading">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="themeSelectorVisible" title="选择主题" width="500px">
      <div class="theme-selector">
        <div v-if="availableThemes.length === 0" class="empty-state">
          所有主题已分配完毕
        </div>
        <div v-else class="theme-list">
          <el-table :data="availableThemes" style="width: 100%">
            <el-table-column label="选择" width="70">
              <template #default="{ row }">
                <el-checkbox 
                  :model-value="selectedThemeIds.includes(row.id)"
                  @change="(checked) => toggleThemeSelection(row.id, checked)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="name" label="主题名称" />
            <el-table-column label="可编辑" width="100">
              <template #default="{ row }">
                <el-checkbox 
                  :model-value="selectedThemesWithEdit.includes(row.id)"
                  :disabled="!selectedThemeIds.includes(row.id)"
                  @change="(checked) => toggleThemeEdit(row.id, checked)"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="themeSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="assignThemesToUser" :loading="loading">确定</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  allThemes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const users = ref([])
const loading = ref(false)

const addUserDialogVisible = ref(false)
const newUser = ref({
  username: '',
  password: '',
  role: 'viewer'
})

const editPasswordDialogVisible = ref(false)
const editPasswordForm = ref({
  userId: '',
  username: '',
  password: ''
})

const themeSelectorVisible = ref(false)
const selectedUser = ref(null)
const selectedThemeIds = ref([])
const selectedThemesWithEdit = ref([])

const availableThemes = computed(() => {
  if (!selectedUser.value) return []
  const assignedIds = selectedUser.value.themes.map(t => t.theme_id)
  return props.allThemes.filter(t => t.id && t.name && !assignedIds.includes(t.id))
})

watch(() => props.modelValue, async (val) => {
  if (val) {
    await fetchUsers()
  }
})

async function fetchUsers() {
  loading.value = true
  try {
    const response = await fetch('/auth/users')
    if (response.ok) {
      users.value = await response.json()
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function showAddUserDialog() {
  newUser.value = {
    username: '',
    password: '',
    role: 'viewer'
  }
  addUserDialogVisible.value = true
}

async function addUser() {
  if (!newUser.value.username || !newUser.value.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }

  loading.value = true
  try {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: newUser.value.username,
        password: newUser.value.password
      })
    })

    if (response.ok) {
      ElMessage.success('用户添加成功')
      addUserDialogVisible.value = false
      await fetchUsers()
    } else {
      const data = await response.json()
      ElMessage.error(data.detail || '添加用户失败')
    }
  } catch (error) {
    ElMessage.error('添加用户失败')
  } finally {
    loading.value = false
  }
}

async function deleteUser(user) {
  if (user.username === 'admin') {
    ElMessage.warning('不能删除管理员账户')
    return
  }

  loading.value = true
  try {
    const response = await fetch(`/auth/users/${user.id}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      ElMessage.success('用户删除成功')
      await fetchUsers()
    } else {
      const data = await response.json()
      ElMessage.error(data.detail || '删除用户失败')
    }
  } catch (error) {
    ElMessage.error('删除用户失败')
  } finally {
    loading.value = false
  }
}

function showEditPasswordDialog(user) {
  editPasswordForm.value = {
    userId: user.id,
    username: user.username,
    password: ''
  }
  editPasswordDialogVisible.value = true
}

async function updatePassword() {
  if (!editPasswordForm.value.password) {
    ElMessage.warning('请输入新密码')
    return
  }

  loading.value = true
  try {
    const response = await fetch(`/auth/users/${editPasswordForm.value.userId}/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        password: editPasswordForm.value.password
      })
    })

    if (response.ok) {
      ElMessage.success('密码修改成功')
      editPasswordDialogVisible.value = false
    } else {
      const data = await response.json()
      ElMessage.error(data.detail || '修改密码失败')
    }
  } catch (error) {
    ElMessage.error('修改密码失败')
  } finally {
    loading.value = false
  }
}

function showThemeSelector(user) {
  selectedUser.value = user
  selectedThemeIds.value = user.themes.map(t => t.theme_id)
  selectedThemesWithEdit.value = user.themes.filter(t => t.can_edit).map(t => t.theme_id)
  themeSelectorVisible.value = true
}

function toggleThemeSelection(themeId, checked) {
  if (checked) {
    if (!selectedThemeIds.value.includes(themeId)) {
      selectedThemeIds.value.push(themeId)
    }
  } else {
    const index = selectedThemeIds.value.indexOf(themeId)
    if (index > -1) {
      selectedThemeIds.value.splice(index, 1)
    }
    // 同时移除可编辑权限
    const editIndex = selectedThemesWithEdit.value.indexOf(themeId)
    if (editIndex > -1) {
      selectedThemesWithEdit.value.splice(editIndex, 1)
    }
  }
}

function toggleThemeEdit(themeId, checked) {
  if (checked) {
    if (!selectedThemesWithEdit.value.includes(themeId)) {
      selectedThemesWithEdit.value.push(themeId)
    }
  } else {
    const index = selectedThemesWithEdit.value.indexOf(themeId)
    if (index > -1) {
      selectedThemesWithEdit.value.splice(index, 1)
    }
  }
}

async function assignThemesToUser() {
  if (!selectedUser.value) return

  loading.value = true
  try {
    for (const themeId of selectedThemeIds.value) {
      if (!selectedUser.value.themes.find(t => t.theme_id === themeId)) {
        const canEdit = selectedThemesWithEdit.value.includes(themeId)
        await fetch(`/auth/users/${selectedUser.value.id}/themes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            theme_id: themeId,
            can_edit: canEdit
          })
        })
      }
    }

    ElMessage.success('主题分配成功')
    themeSelectorVisible.value = false
    await fetchUsers()
  } catch (error) {
    ElMessage.error('主题分配失败')
  } finally {
    loading.value = false
  }
}

async function removeThemeFromUser(user, themeId) {
  try {
    const response = await fetch(`/auth/users/${user.id}/themes/${themeId}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      ElMessage.success('已移除主题')
      await fetchUsers()
    } else {
      const data = await response.json()
      ElMessage.error(data.detail || '移除主题失败')
    }
  } catch (error) {
    ElMessage.error('移除主题失败')
  }
}

function handleClose() {
  emit('update:modelValue', false)
  emit('refresh')
}
</script>

<style scoped>
.user-manager {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.theme-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.theme-selector {
  max-height: 400px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>
