<template>
  <div class="app-wrapper">
    <!-- 动态光晕背景 -->
    <div class="ambient-background">
      <div class="color-blob blob-1"></div>
      <div class="color-blob blob-2"></div>
      <div class="color-blob blob-3"></div>
      <div class="color-blob blob-4"></div>
    </div>

    <el-container class="main-container">
      <!-- 悬浮头部导航 -->
      <el-header class="header">
        <div class="header-glass-panel">
          <div class="logo">
            <img src="/tubiao.jpg" alt="Logo" class="logo-image" />
            <span class="logo-text">星途职引</span>
          </div>
          
          <div class="nav-container">
            <el-menu
              v-if="userStore.isLoggedIn"
              :default-active="activeMenu"
              mode="horizontal"
              router
              class="glass-menu"
              :ellipsis="false"
            >
              <el-menu-item index="/">首页</el-menu-item>
              <el-menu-item index="/jobs">岗位探索</el-menu-item>
              <el-menu-item index="/profile">我的画像</el-menu-item>
              <el-menu-item index="/matching">人岗匹配</el-menu-item>
              <el-menu-item index="/report">职业报告</el-menu-item>
              <el-menu-item index="/admin" v-if="userStore.isAdmin">用户管理</el-menu-item>
            </el-menu>
          </div>

          <div class="user-menu">
            <template v-if="userStore.isLoggedIn">
              <el-dropdown popper-class="glass-dropdown">
                <span class="user-dropdown">
                  <div class="avatar-placeholder">{{ userStore.userName?.charAt(0) || 'U' }}</div>
                  <span class="username">{{ userStore.userName }}</span>
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="showEditProfileDialog">修改信息</el-dropdown-item>
                    <el-dropdown-item @click="handleLogout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <el-button class="glass-btn" @click="navigateToLogin">快速登录</el-button>
            </template>
          </div>
        </div>
      </el-header>

      <!-- 修改信息对话框 -->
      <el-dialog
        v-model="editProfileDialogVisible"
        title="修改个人信息"
        width="420px"
        class="glass-dialog"
        :show-close="false"
      >
        <div class="dialog-inner">
          <h3 class="dialog-title">更新您的资料</h3>
          <el-form
            ref="editProfileFormRef"
            :model="editProfileForm"
            :rules="editProfileRules"
            label-width="80px"
            label-position="top"
          >
            <el-form-item label="姓名" prop="name">
              <el-input v-model="editProfileForm.name" placeholder="请输入姓名" class="glass-input" />
            </el-form-item>
            <el-form-item label="原密码" prop="oldPassword">
              <el-input
                v-model="editProfileForm.oldPassword"
                type="password"
                placeholder="请输入原密码"
                show-password
                class="glass-input"
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="editProfileForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                show-password
                class="glass-input"
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="editProfileForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                class="glass-input"
              />
            </el-form-item>
          </el-form>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button class="glass-btn-ghost" @click="editProfileDialogVisible = false">取消</el-button>
            <el-button class="glass-btn-primary" @click="handleEditProfile">确定修改</el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <transition name="fade-slide" mode="out-in">
          <keep-alive>
            <router-view />
          </keep-alive>
        </transition>
      </el-main>

      <!-- 底部毛玻璃面板 -->
      <el-footer class="footer">
        <div class="footer-glass-panel">
          <div class="footer-content">
            <p class="footer-title">星途职引</p>
            <p class="footer-desc">高校学生职业AI规划平台</p>


          </div>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { ArrowDown, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

// 修改信息对话框
const editProfileDialogVisible = ref(false)
const editProfileFormRef = ref<FormInstance>()
const editProfileForm = reactive({
  name: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const editProfileRules: FormRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== editProfileForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const showEditProfileDialog = () => {
  editProfileForm.name = userStore.user?.name || ''
  editProfileForm.oldPassword = ''
  editProfileForm.newPassword = ''
  editProfileForm.confirmPassword = ''
  editProfileDialogVisible.value = true
}

const handleEditProfile = async () => {
  if (!editProfileFormRef.value) return
  
  await editProfileFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await axios.put('/api/auth/profile', {
          name: editProfileForm.name,
          oldPassword: editProfileForm.oldPassword,
          newPassword: editProfileForm.newPassword
        }, {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        })
        
        if (response.data.success) {
          ElMessage.success('修改成功')
          // 更新本地用户信息
          if (userStore.user) {
            userStore.user.name = editProfileForm.name
          }
          editProfileDialogVisible.value = false
        } else {
          ElMessage.error(response.data.error || '修改失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.error || '修改失败')
      }
    }
  })
}

const navigateToLogin = () => {
  router.push('/login')
}

const handleLogout = async () => {
  try {
    await axios.post('/api/auth/logout')
    userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  }
}
</script>

<style scoped>
/* 根级容器与动态光晕背景 */
.app-wrapper {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background-color: #f0f4f8; /* 基础底色 */
  font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.ambient-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.color-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite alternate ease-in-out;
}

.blob-1 {
  width: 600px;
  height: 600px;
  background: rgba(102, 126, 234, 0.4);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 500px;
  height: 500px;
  background: rgba(118, 75, 162, 0.3);
  bottom: -50px;
  right: -50px;
  animation-delay: -5s;
}

.blob-3 {
  width: 400px;
  height: 400px;
  background: rgba(43, 203, 186, 0.3);
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

.blob-4 {
  width: 450px;
  height: 450px;
  background: rgba(253, 160, 133, 0.2);
  bottom: 20%;
  left: 10%;
  animation-delay: -15s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(40px, 40px) scale(1.05); }
}

.main-container {
  position: relative;
  z-index: 1;
}

/* 头部悬浮导航栏 (毛玻璃) */
.header {
  height: auto;
  padding: 20px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-glass-panel {
  max-width: 1400px;
  margin: 0 auto;
  height: 64px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
  border-radius: 32px;
  display: grid;
  grid-template-columns: 240px 1fr 240px;
  align-items: center;
  padding: 0 24px;
  transition: all 0.3s ease;
}

/* Logo 样式 */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-image {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  object-fit: cover;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #2d3748;
  letter-spacing: 0.5px;
}

/* 导航菜单样式 */
.nav-container {
  display: flex;
  justify-content: center;
}

.glass-menu {
  background: transparent !important;
  border-bottom: none !important;
}

:deep(.el-menu--horizontal > .el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 0 8px;
  padding: 0 20px;
  border-radius: 24px;
  color: #4a5568 !important;
  font-weight: 500;
  border-bottom: none !important;
  transition: all 0.3s ease;
}

:deep(.el-menu--horizontal > .el-menu-item:hover),
:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.7) !important;
  color: #667eea !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 用户菜单 */
.user-menu {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px 6px 6px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.3s;
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.username {
  font-weight: 500;
  color: #4a5568;
}

.glass-btn {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  color: #667eea;
  border-radius: 20px;
  padding: 8px 24px;
  font-weight: 600;
  transition: all 0.3s;
}
.glass-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

/* 路由动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 主内容区 */
.main-content {
  min-height: calc(100vh - 200px);
  padding: 0 20px 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

/* 底部区域 */
.footer {
  padding: 0 20px 20px;
  height: auto;
}

.footer-glass-panel {
  max-width: 1400px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 24px;
  padding: 30px 20px;
  text-align: center;
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.footer-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.footer-desc {
  color: #718096;
  font-size: 14px;
  margin: 0;
}

.footer-divider {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
  margin: 10px 0;
}

.footer-copyright {
  color: #a0aec0;
  font-size: 13px;
  margin: 0;
}

/* --- 全局毛玻璃弹窗覆写 --- */
:deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.75) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  border-radius: 24px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  display: none; /* 隐藏默认头部，使用自定义标题 */
}

:deep(.el-dialog__body) {
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

:deep(.el-form-item__label) {
  color: #4a5568;
  font-weight: 500;
  padding-bottom: 4px;
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6) !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
}

.dialog-footer {
  padding: 0 32px 32px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.glass-btn-ghost {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  color: #4a5568;
  transition: all 0.3s;
}

.glass-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  color: #2d3748;
}

.glass-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  transition: all 0.3s;
  padding: 0 24px;
}

.glass-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

/* --- 全局下拉菜单毛玻璃 --- */
:global(.glass-dropdown) {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 16px !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1) !important;
}

:global(.glass-dropdown .el-dropdown-menu__item) {
  color: #4a5568;
  border-radius: 8px;
  margin: 4px 8px;
  transition: all 0.2s;
}

:global(.glass-dropdown .el-dropdown-menu__item:hover) {
  background: rgba(102, 126, 234, 0.1) !important;
  color: #667eea !important;
}
</style>