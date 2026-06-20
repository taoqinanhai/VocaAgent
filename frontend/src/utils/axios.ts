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
      // 可以在这里添加重定向到登录页面的逻辑
    }
    return Promise.reject(error)
  }
)

export default api
