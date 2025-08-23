import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/views/AuthCallback.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/diet-plans',
    name: 'DietPlans',
    component: () => import('@/views/DietPlans.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/meals',
    name: 'Meals',
    component: () => import('@/views/Meals.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exercises',
    name: 'Exercises',
    component: () => import('@/views/Exercises.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/weight-tracking',
    name: 'WeightTracking',
    component: () => import('@/views/WeightTracking.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    const isAuthenticated = await authStore.checkAuth()
    if (!isAuthenticated) {
      next('/login')
      return
    }
  }
  
  // 检查是否需要游客状态（如登录页）
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router