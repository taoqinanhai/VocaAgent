import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAgentPipeline } from './agentPipeline'

export interface User {
  id: number
  username: string
  email: string
  name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(loadUserFromStorage())

  function loadUserFromStorage(): User | null {
    try {
      const raw = localStorage.getItem('user')
      return raw ? JSON.parse(raw) : null
    } catch {
      // localStorage 数据损坏时降级为未登录，避免整站白屏
      return null
    }
  }

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userName = computed(() => user.value?.name || user.value?.username || '')

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(newUser: User) {
    user.value = newUser
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    // 清空 Agent Pipeline 状态，避免换账号登录后看到上一个账号的数据
    try {
      useAgentPipeline().clearAll()
    } catch {
      // store 未初始化（循环依赖保护）时忽略
    }
  }

  async function fetchCurrentUser() {
    try {
      const response = await axios.get('/api/auth/user')
      if (response.data.success) {
        setUser(response.data.user)
        return response.data.user
      }
      return null
    } catch (error) {
      logout()
      return null
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    userName,
    setToken,
    setUser,
    logout,
    fetchCurrentUser
  }
})
