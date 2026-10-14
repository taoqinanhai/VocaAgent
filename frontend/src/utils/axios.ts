import axios from 'axios'
import { useUserStore } from '@/stores/user'

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 60000, // 增加超时时间到60秒
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      // 跳回登录页。这里用 window.location 而不是 router.push：router 会引入各页面
      // 组件、页面又反过来引入本文件，形成循环依赖。
      // 场景：改密码后服务端会删掉该用户所有 Token，当前会话立即失效——
      // 若不跳转，用户会停在原页面反复请求失败，看起来像"网站坏了"。
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
