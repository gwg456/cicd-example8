import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 页面组件导入
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Profile = () => import('@/views/Profile.vue')
const Users = () => import('@/views/admin/Users.vue')
const Roles = () => import('@/views/admin/Roles.vue')
const Layout = () => import('@/components/Layout.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { 
      requiresAuth: false,
      hideForAuth: true // 已登录用户隐藏
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { 
      requiresAuth: false,
      hideForAuth: true // 已登录用户隐藏
    }
  },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { 
          requiresAuth: true,
          title: '仪表板'
        }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: Profile,
        meta: { 
          requiresAuth: true,
          title: '个人资料'
        }
      },
      {
        path: '/admin',
        meta: { 
          requiresAuth: true,
          requiresAdmin: true,
          title: '系统管理'
        },
        children: [
          {
            path: 'users',
            name: 'AdminUsers',
            component: Users,
            meta: { 
              requiresAuth: true,
              requiresAdmin: true,
              title: '用户管理'
            }
          },
          {
            path: 'roles',
            name: 'AdminRoles',
            component: Roles,
            meta: { 
              requiresAuth: true,
              requiresAdmin: true,
              title: '角色管理'
            }
          }
        ]
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (authStore.token && !authStore.user) {
    await authStore.initialize()
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 已登录用户访问登录/注册页面重定向到首页
  if (to.meta.hideForAuth && authStore.isAuthenticated) {
    next('/')
    return
  }
  
  // 检查管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }
  
  next()
})

export default router