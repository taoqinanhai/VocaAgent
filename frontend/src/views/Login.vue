<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="login-container fade-in-up">
      <div class="login-wrapper glass-panel">
        
        <!-- 左侧欢迎区域 (彻底移除生硬边界，提升通透度) -->
        <div class="login-welcome-section glass-inner-panel-light">
          <div class="welcome-content">
            <h2 class="welcome-title gradient-text-light">WELCOME</h2>
            <p class="welcome-subtitle">大学生就业规划平台</p>
            <div class="welcome-avatar">
              <img src="../../76d8b86c6e02b85dbb8b15b40047d3fa.png" alt="Welcome" />
            </div>
          </div>
        </div>
        
        <!-- 右侧表单区域 (通过柔和渐变与左侧自然过渡) -->
        <div class="login-form-section">
          <div class="login-card">
            <div class="login-header">
              <div class="icon-wrapper glass-item">
                <el-icon size="36" color="#5a67d8"><Connection /></el-icon>
              </div>
              <h1 class="login-title gradient-text">星途职引</h1>
              <p class="login-subtitle">{{ isSignUp ? '创建您的专属账号' : '欢迎回来，请登录' }}</p>
            </div>

            <div class="login-tabs">
              <el-tabs v-model="isSignUp" class="glass-tabs">
                <el-tab-pane label="登录" :name="false">
                  <el-form
                    ref="loginFormRef"
                    :model="loginForm"
                    :rules="loginRules"
                    label-width="0"
                    class="login-form"
                  >
                    <el-form-item prop="email">
                      <el-input
                        v-model="loginForm.email"
                        placeholder="请输入邮箱"
                        size="large"
                        :prefix-icon="Message"
                        class="glass-input"
                      />
                    </el-form-item>

                    <el-form-item prop="password">
                      <el-input
                        v-model="loginForm.password"
                        type="password"
                        placeholder="请输入密码"
                        size="large"
                        :prefix-icon="Lock"
                        show-password
                        class="glass-input"
                      />
                    </el-form-item>

                    <!-- 验证码 -->
                    <el-form-item prop="captcha" class="captcha-form-item">
                      <el-input
                        v-model="loginForm.captcha"
                        placeholder="请输入验证码"
                        size="large"
                        class="glass-input"
                        @keyup.enter="handleLogin"
                      >
                        <template #suffix>
                          <div class="captcha-code glass-btn-small hover-lift" @click="generateCaptcha">{{ captchaCode }}</div>
                        </template>
                      </el-input>
                    </el-form-item>

                    <el-form-item>
                      <el-button
                        type="primary"
                        size="large"
                        :loading="loading"
                        @click="handleLogin"
                        class="glass-submit-btn hover-lift"
                      >
                        {{ loading ? '登录中...' : '立即登录' }}
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-tab-pane>
                <el-tab-pane label="注册" :name="true">
                  <el-form
                    ref="registerFormRef"
                    :model="registerForm"
                    :rules="registerRules"
                    label-width="0"
                    class="login-form"
                  >
                    <el-form-item prop="username">
                      <el-input
                        v-model="registerForm.username"
                        placeholder="请输入用户名"
                        size="large"
                        :prefix-icon="User"
                        class="glass-input"
                      />
                    </el-form-item>

                    <el-form-item prop="email">
                      <el-input
                        v-model="registerForm.email"
                        placeholder="请输入邮箱"
                        size="large"
                        :prefix-icon="Message"
                        class="glass-input"
                      />
                    </el-form-item>

                    <el-form-item prop="password">
                      <el-input
                        v-model="registerForm.password"
                        type="password"
                        placeholder="请输入密码"
                        size="large"
                        :prefix-icon="Lock"
                        show-password
                        class="glass-input"
                      />
                    </el-form-item>

                    <el-form-item prop="confirmPassword">
                      <el-input
                        v-model="registerForm.confirmPassword"
                        type="password"
                        placeholder="请确认密码"
                        size="large"
                        :prefix-icon="Lock"
                        show-password
                        class="glass-input"
                        @keyup.enter="handleRegister"
                      />
                    </el-form-item>

                    <el-form-item>
                      <el-button
                        type="primary"
                        size="large"
                        :loading="loading"
                        @click="handleRegister"
                        class="glass-submit-btn hover-lift"
                      >
                        {{ loading ? '注册中...' : '注册新账号' }}
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Connection } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '../stores'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const isSignUp = ref(false)
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  email: '',
  password: '',
  captcha: ''
})

// 验证码
const captchaCode = ref('')

// 生成随机5位验证码
const generateCaptcha = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 5; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  captchaCode.value = result
}

// 初始化验证码
generateCaptcha()

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 监听标签切换，清空表单
watch(isSignUp, (newVal) => {
  // 清空登录表单
  loginForm.email = ''
  loginForm.password = ''
  loginForm.captcha = ''
  // 清空注册表单
  registerForm.username = ''
  registerForm.email = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
  // 清除表单验证状态
  loginFormRef.value?.clearValidate()
  registerFormRef.value?.clearValidate()
  // 重新生成验证码
  generateCaptcha()
})

const loginRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'submit' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'submit' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'submit' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'submit' }
  ]
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'submit' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'submit' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'submit' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'submit' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'submit' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'submit' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'submit' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      // 验证验证码
      if (loginForm.captcha.toLowerCase() !== captchaCode.value.toLowerCase()) {
        ElMessage.error('验证码错误')
        generateCaptcha()
        loginForm.captcha = ''
        return
      }
      
      loading.value = true
      try {
        const response = await axios.post('/api/auth/login', {
          email: loginForm.email,
          password: loginForm.password
        })
        
        if (response.data.success) {
          userStore.setUser(response.data.user)
          // 保存后端返回的Token
          userStore.setToken(response.data.token)
          
          ElMessage.success('登录成功')
          
          if (response.data.user.role === 'admin') {
            router.push('/admin')
          } else {
            router.push('/')
          }
        } else {
          ElMessage.error(response.data.error || '登录失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.error || '登录失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await axios.post('/api/auth/register', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        
        if (response.data.success) {
          ElMessage.success('注册成功，请登录')
          isSignUp.value = false
          registerForm.username = ''
          registerForm.email = ''
          registerForm.password = ''
          registerForm.confirmPassword = ''
          registerFormRef.value.resetFields()
        } else {
          ElMessage.error(response.data.error || '注册失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.error || '注册失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
/* =========== 整体页面背景与流体光晕 =========== */
.page-wrapper {
  min-height: 100vh;
  position: relative;
  /* 移除固定的底色，实现背景透明，与您的主应用浑然一体 */
  background: transparent; 
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px); /* 增加模糊度，使光效非常柔和自然 */
  z-index: 0;
  opacity: 0.5;
  animation: float 18s ease-in-out infinite;
}

.shape-1 {
  top: -15%;
  left: -5%;
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}

.shape-2 {
  bottom: -15%;
  right: -10%;
  width: 700px;
  height: 700px;
  background: linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%);
  animation-delay: -5s;
}

.shape-3 {
  top: 35%;
  left: 50%;
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #fbc2eb 0%, #e6dee9 100%);
  animation-delay: -10s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(40px, -60px) scale(1.1); }
  66% { transform: translate(-30px, 30px) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

/* =========== 登录主体区域 =========== */
.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 960px;
  padding: 20px;
}

/* =========== 玻璃拟态基础样式 =========== */
.glass-panel {
  display: flex;
  /* 大幅降低不透明度，提升整块面板的通透感，不再像塑料板 */
  background: rgba(255, 255, 255, 0.25) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  border-radius: 32px !important;
  box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.08), inset 0 0 0 1px rgba(255,255,255,0.3) !important;
  overflow: hidden;
  min-height: 580px;
}

.glass-inner-panel-light {
  /* 彻底移除之前的 border-right 竖线，让背景透明自然过渡 */
  background: transparent;
}

.glass-item {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* =========== 左右两侧布局 =========== */
.login-welcome-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 45px;
  position: relative;
  overflow: hidden;
}

.login-form-section {
  flex: 1.2;
  /* 右侧表单区使用柔和的渐变底色作为分割，替代生硬的边框线条 */
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.35) 100%);
  box-shadow: -1px 0 20px rgba(0,0,0,0.02);
  padding: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 360px;
}

/* =========== 渐变文字与图标 =========== */
.gradient-text {
  background: linear-gradient(120deg, #1f2937, #3730a3);
  -webkit-background-clip: text;
  color: transparent;
}

.gradient-text-light {
  background: linear-gradient(120deg, #3730a3, #667eea);
  -webkit-background-clip: text;
  color: transparent;
}

.icon-wrapper {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0.4) 100%);
}

.welcome-content {
  text-align: center;
  position: relative;
  z-index: 1;
}

.welcome-title {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 12px;
  letter-spacing: 3px;
}

.welcome-subtitle {
  font-size: 16px;
  margin-bottom: 40px;
  color: #4b5563;
  font-weight: 500;
}

.welcome-avatar {
  width: 130px;
  height: 130px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto;
  border: 4px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  background: rgba(255,255,255,0.3);
}

.welcome-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-title {
  font-size: 26px;
  font-weight: 800;
  margin: 0 0 8px 0;
  letter-spacing: 0.5px;
}

.login-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

/* =========== 拟态 Tabs =========== */
.login-tabs {
  width: 100%;
}

.glass-tabs :deep(.el-tabs__header) {
  margin-bottom: 32px;
  border-bottom: none;
}

.glass-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: rgba(0,0,0,0.06);
}

.glass-tabs :deep(.el-tabs__nav) {
  width: 100%;
  display: flex;
  justify-content: center;
}

/* 核心修复：移除 Tabs 在点击/聚焦时难看的默认外发光蓝框 */
.glass-tabs :deep(.el-tabs__item:focus),
.glass-tabs :deep(.el-tabs__item:focus-visible),
.glass-tabs :deep(.el-tabs__item:active) {
  outline: none !important;
  box-shadow: none !important;
}

.glass-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
  padding: 0 24px;
  transition: all 0.3s ease;
}

.glass-tabs :deep(.el-tabs__item.is-active) {
  color: #3730a3;
  font-size: 17px;
}

.glass-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #667eea, #764ba2);
  height: 3px;
  border-radius: 3px;
}

/* =========== 玻璃拟态输入框 =========== */
.login-form {
  width: 100%;
}

.login-form .el-form-item {
  margin-bottom: 20px;
}

.glass-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.4) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  padding: 12px 18px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.glass-input :deep(.el-input__wrapper:hover),
.glass-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.7) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
  border-color: rgba(255, 255, 255, 1);
}

.glass-input :deep(.el-input__prefix) {
  color: #6b7280;
  font-size: 18px;
  margin-right: 8px;
}

.glass-input :deep(input::placeholder) {
  color: #9ca3af;
  font-weight: 500;
}

/* =========== 按钮与验证码 =========== */
.glass-submit-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 14px;
  margin-top: 16px;
  color: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.glass-submit-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.captcha-form-item :deep(.el-input__wrapper) {
  padding-right: 8px;
}

.captcha-form-item :deep(.el-input__suffix) {
  right: 0;
}

.glass-btn-small {
  width: 90px;
  height: 38px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  color: #5a67d8;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  cursor: pointer;
  user-select: none;
  font-family: 'Courier New', monospace;
  transition: all 0.3s ease;
}

.glass-btn-small:hover {
  background: rgba(255, 255, 255, 0.9);
  color: #4f46e5;
  border-color: rgba(102, 126, 234, 0.5);
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(40px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========== 响应式适配 =========== */
@media (max-width: 850px) {
  .glass-panel {
    flex-direction: column;
    min-height: auto;
  }
  
  .glass-inner-panel-light {
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .login-welcome-section {
    padding: 30px;
  }
  
  .login-form-section {
    padding: 30px 20px;
  }
  
  .welcome-avatar {
    width: 90px;
    height: 90px;
  }
  
  .welcome-title {
    font-size: 28px;
  }
  
  .welcome-subtitle {
    margin-bottom: 20px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 10px;
  }
  
  .glass-panel {
    border-radius: 20px !important;
  }
  
  .login-form-section {
    padding: 24px 16px;
  }
  
  .login-title {
    font-size: 24px;
  }
}
</style>