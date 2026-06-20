import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/jobs',
      name: 'Jobs',
      component: () => import('../views/Jobs.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/jobs/:id',
      name: 'JobDetail',
      component: () => import('../views/JobDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/job-explore/:id',
      name: 'JobExplore',
      component: () => import('../views/JobExplore.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/matching',
      name: 'Matching',
      component: () => import('../views/Matching.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/report',
      name: 'Report',
      component: () => import('../views/Report.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/report/:id',
      name: 'ReportDetail',
      component: () => import('../views/ReportDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/interview/:student_id/:job_id',
      name: 'Interview',
      component: () => import('../views/Interview.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('../views/Admin.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (userStore.isLoggedIn) {
      // 检查是否需要管理员权限
      if (to.meta.requiresAdmin && !userStore.isAdmin) {
        next('/')
      } else {
        next()
      }
    } else {
      next('/login')
    }
  } else {
    next()
  }
})

export default router
