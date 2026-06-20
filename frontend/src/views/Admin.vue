<template>
  <div class="admin-container">
    <div class="admin-header glass-panel">
      <h2>用户管理</h2>
      <div class="header-actions">
        <div class="glass-search-wrapper">
          <el-input
            v-model="searchKeyword"
            placeholder="输入用户名或邮箱查询..."
            clearable
            class="glass-input custom-search"
          >
            <template #prefix>
              <el-icon class="search-icon"><Search /></el-icon>
            </template>
          </el-input>
          <el-button class="glass-btn-primary search-btn" @click="handleSearch">
            查询
          </el-button>
        </div>
        <el-button class="glass-btn-primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
      </div>
    </div>

    <div class="table-container glass-panel">
      <el-table 
        :data="users" 
        style="width: 100%" 
        v-loading="loading"
        class="glass-table"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="username" label="用户名" width="150" align="center">
          <template #default="{ row }">
            <span class="user-text">{{ row.username }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="220" align="center" />
        <el-table-column prop="name" label="姓名" width="120" align="center" />
        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <span :class="['glass-tag', row.role === 'admin' ? 'tag-danger' : 'tag-primary']">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="120" align="center">
          <template #default="{ row }">
            <span :class="['glass-tag', row.is_active ? 'tag-success' : 'tag-info']">
              <span class="status-dot"></span>
              {{ row.is_active ? '已启用' : '已禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="260" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button class="glass-btn-ghost action-btn" size="small" @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button class="glass-btn-warning action-btn" size="small" @click="handleResetPassword(row)">
                重置密码
              </el-button>
              <el-button class="glass-btn-danger action-btn" size="small" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加用户弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      title="添加用户"
      width="480px"
      @close="resetCreateForm"
      class="glass-dialog"
      :show-close="false"
    >
      <div class="dialog-inner">
        <h3 class="dialog-title">新增系统用户</h3>
        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="createRules"
          label-width="80px"
          label-position="top"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="createForm.username" placeholder="请输入唯一用户名" class="glass-input" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="createForm.email" placeholder="请输入有效邮箱" class="glass-input" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="createForm.password"
              type="password"
              placeholder="请输入初始密码"
              show-password
              class="glass-input"
            />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="姓名" prop="name" class="flex-1">
              <el-input v-model="createForm.name" placeholder="请输入真实姓名" class="glass-input" />
            </el-form-item>
            <el-form-item label="系统角色" prop="role" class="flex-1">
              <el-select v-model="createForm.role" placeholder="选择角色" class="glass-select">
                <el-option label="普通用户" value="user" />
                <el-option label="系统管理员" value="admin" />
              </el-select>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="glass-btn-ghost" @click="showCreateDialog = false">取消</el-button>
          <el-button class="glass-btn-primary" @click="handleCreate" :loading="loading">
            确认创建
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑用户"
      width="480px"
      @close="resetEditForm"
      class="glass-dialog"
      :show-close="false"
    >
      <div class="dialog-inner">
        <h3 class="dialog-title">修改用户资料</h3>
        <el-form
          ref="editFormRef"
          :model="editForm"
          :rules="editRules"
          label-width="80px"
          label-position="top"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="editForm.email" placeholder="请输入邮箱" class="glass-input" />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="姓名" prop="name" class="flex-1">
              <el-input v-model="editForm.name" placeholder="请输入姓名" class="glass-input" />
            </el-form-item>
            <el-form-item label="角色" prop="role" class="flex-1">
              <el-select v-model="editForm.role" placeholder="请选择角色" class="glass-select">
                <el-option label="普通用户" value="user" />
                <el-option label="系统管理员" value="admin" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="账户状态" prop="is_active" class="switch-item">
            <div class="switch-wrapper">
              <span class="switch-label">{{ editForm.is_active ? '启用中' : '已停用' }}</span>
              <el-switch v-model="editForm.is_active" class="glass-switch" />
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="glass-btn-ghost" @click="showEditDialog = false">取消修改</el-button>
          <el-button class="glass-btn-primary" @click="handleUpdate" :loading="loading">
            保存更新
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import axios from 'axios'

interface User {
  id: number
  username: string
  email: string
  name: string | null
  role: string
  is_active: boolean
  created_at: string
}

const userStore = useUserStore()
const users = ref<User[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const currentUserId = ref<number | null>(null)
const searchKeyword = ref('')
const originalUsers = ref<User[]>([])

const createForm = reactive({
  username: '',
  email: '',
  password: '',
  name: '',
  role: 'user'
})

const editForm = reactive({
  email: '',
  name: '',
  role: '',
  is_active: true
})

const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const editRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const getToken = () => userStore.token || ''

const fetchUsers = async () => {
  if (!getToken()) return
  loading.value = true
  try {
    const response = await axios.get('/api/admin/users', {
      headers: { 'Authorization': `Bearer ${getToken()}` },
      params: { token: getToken() }
    })
    users.value = response.data.data
    originalUsers.value = response.data.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  if (!searchKeyword.value) {
    users.value = originalUsers.value
    return
  }
  const keyword = searchKeyword.value.toLowerCase()
  users.value = originalUsers.value.filter(user => 
    user.username.toLowerCase().includes(keyword) || 
    user.email.toLowerCase().includes(keyword)
  )
}

const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await axios.post('/api/admin/users', createForm, {
          headers: { 'Authorization': `Bearer ${getToken()}` },
          params: { token: getToken() }
        })
        ElMessage.success('用户创建成功')
        showCreateDialog.value = false
        resetCreateForm()
        fetchUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建用户失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleEdit = (row: User) => {
  currentUserId.value = row.id
  editForm.email = row.email
  editForm.name = row.name || ''
  editForm.role = row.role
  editForm.is_active = row.is_active
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value || !currentUserId.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await axios.put(`/api/admin/users/${currentUserId.value}`, editForm, {
          headers: { 'Authorization': `Bearer ${getToken()}` },
          params: { token: getToken() }
        })
        ElMessage.success('用户更新成功')
        showEditDialog.value = false
        resetEditForm()
        fetchUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '更新用户失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleResetPassword = async (row: User) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `请输入用户 <span style="color:#ef4444;font-weight:bold">${row.username}</span> 的新密码`,
      '重置密码',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        customClass: 'glass-message-box',
        inputType: 'password',
        inputValidator: (val: string) => {
          if (!val || val.length < 6) return '密码至少 6 位'
          return true
        }
      }
    )

    loading.value = true
    try {
      await axios.put(`/api/admin/users/${row.id}/password`, null, {
        headers: { 'Authorization': `Bearer ${getToken()}` },
        params: { token: getToken(), new_password: newPassword }
      })
      ElMessage.success('密码重置成功')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '重置密码失败')
    } finally {
      loading.value = false
    }
  } catch {
    ElMessage.info('已取消重置操作')
  }
}

const handleDelete = async (row: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 <span style="color:#ef4444;font-weight:bold">${row.username}</span> 吗？此操作不可逆！`,
      '确认删除',
      {
        confirmButtonText: '永久删除',
        cancelButtonText: '取消',
        type: 'error',
        dangerouslyUseHTMLString: true,
        customClass: 'glass-message-box'
      }
    )
    
    loading.value = true
    try {
      await axios.delete(`/api/admin/users/${row.id}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` },
        params: { token: getToken() }
      })
      ElMessage.success('用户已成功删除')
      fetchUsers()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    } finally {
      loading.value = false
    }
  } catch {
    ElMessage.info('已取消删除操作')
  }
}

const resetCreateForm = () => {
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
  createForm.name = ''
  createForm.role = 'user'
  createFormRef.value?.resetFields()
}

const resetEditForm = () => {
  editForm.email = ''
  editForm.name = ''
  editForm.role = ''
  editForm.is_active = true
  currentUserId.value = null
  editFormRef.value?.resetFields()
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
/* ==================== 基础与布局 ==================== */
.admin-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
  position: relative;
  z-index: 1;
}

/* ==================== 共享玻璃拟态类 ==================== */
.glass-panel {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
  border-radius: 20px;
}

/* ==================== 头部控制区 ==================== */
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 30px;
}

.admin-header h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #1f2937;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
}

.admin-header h2::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  margin-right: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.glass-search-wrapper {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 14px;
  padding: 4px;
  transition: all 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.glass-search-wrapper:focus-within {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.custom-search {
  width: 240px;
}
.custom-search :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent !important;
  border: none !important;
}
.custom-search :deep(.el-input__inner) {
  color: #2d3748;
}

.search-btn {
  border-radius: 10px !important;
  padding: 8px 20px !important;
  height: 34px !important;
}

/* ==================== 按钮拟态体系 ==================== */
.glass-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-weight: 600;
  padding: 10px 24px;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
.glass-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.glass-btn-ghost {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: #4a5568;
  font-weight: 600;
  transition: all 0.3s;
}
.glass-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  color: #2d3748;
  transform: translateY(-1px);
}

.glass-btn-danger {
  background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-weight: 600;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(255, 117, 140, 0.3);
}
.glass-btn-danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(255, 117, 140, 0.4);
}

.glass-btn-warning {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-weight: 600;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(246, 211, 101, 0.3);
}
.glass-btn-warning:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(246, 211, 101, 0.4);
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.action-btn {
  padding: 6px 12px;
  height: 32px;
  font-size: 13px;
}

/* ==================== 表格透视定制 ==================== */
.table-container {
  overflow: hidden;
  padding: 10px;
}

.glass-table {
  background: transparent !important;
  --el-table-border-color: rgba(255, 255, 255, 0.3);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}

.glass-table :deep(th.el-table__cell) {
  background: rgba(255, 255, 255, 0.4) !important;
  color: #1f2937;
  font-weight: 700;
  font-size: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.6) !important;
  padding: 16px 0;
}

.glass-table :deep(th.el-table__cell:first-child) {
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
}
.glass-table :deep(th.el-table__cell:last-child) {
  border-top-right-radius: 12px;
  border-bottom-right-radius: 12px;
}

.glass-table :deep(td.el-table__cell) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.3) !important;
  padding: 14px 0;
  color: #4a5568;
  transition: all 0.3s ease;
}

/* 表格行悬浮效果 */
.glass-table :deep(tbody tr:hover > td.el-table__cell) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  backdrop-filter: blur(10px);
}
.glass-table :deep(tbody tr) {
  transition: transform 0.2s ease, background-color 0.2s ease;
}
.glass-table :deep(tbody tr:hover) {
  transform: scale(1.002);
}

/* ==================== 标签与装饰 ==================== */
.glass-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.tag-primary {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.3);
}
.tag-danger {
  background: rgba(255, 117, 140, 0.15);
  color: #ff758c;
  border: 1px solid rgba(255, 117, 140, 0.3);
}
.tag-success {
  background: rgba(43, 203, 186, 0.15);
  color: #2bcbba;
  border: 1px solid rgba(43, 203, 186, 0.3);
}
.tag-info {
  background: rgba(160, 174, 192, 0.15);
  color: #718096;
  border: 1px solid rgba(160, 174, 192, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.user-text {
  font-weight: 600;
  color: #2d3748;
}

.date-text {
  font-family: 'Consolas', monospace;
  font-size: 13px;
  color: #718096;
}

/* ==================== 玻璃态弹窗与表单 (复用一致性) ==================== */
:deep(.glass-dialog) {
  background: rgba(255, 255, 255, 0.75) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  border-radius: 24px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden;
}

:deep(.glass-dialog .el-dialog__header) {
  display: none;
}

:deep(.glass-dialog .el-dialog__body) {
  padding: 0;
}

.dialog-inner {
  padding: 32px 32px 10px;
}

.dialog-title {
  margin: 0 0 24px;
  font-size: 20px;
  color: #2d3748;
  text-align: center;
  font-weight: 700;
}

.form-row {
  display: flex;
  gap: 16px;
}
.flex-1 {
  flex: 1;
}

:deep(.glass-input .el-input__wrapper),
:deep(.glass-select .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.6) !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px;
  transition: all 0.3s ease;
  height: 38px;
}

:deep(.glass-input .el-input__wrapper.is-focus),
:deep(.glass-select .el-select__wrapper.is-focused) {
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
}

.switch-item {
  margin-top: 10px;
}
.switch-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.5);
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.switch-label {
  font-weight: 600;
  color: #4a5568;
}
:deep(.glass-switch .el-switch__core) {
  border-radius: 12px;
}

.dialog-footer {
  padding: 0 32px 32px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding: 20px;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .glass-search-wrapper {
    width: 100%;
  }
  .custom-search {
    width: 100%;
  }
  .table-container {
    padding: 0;
  }
}
</style>