import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, getUser } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
  },
  {
    path: '/docs',
    name: 'docs',
    component: () => import('@/views/Docs.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory('/bubble-community/'),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin) {
    const u = getUser()
    if (!u || (u.role !== 'admin' && u.role !== 'reviewer')) {
      return { name: 'home' }
    }
  }
  // 允许已登录用户访问登录/注册页，方便切换账号
  // （在同一浏览器中，如果前一个用户未退出，新用户需要能登录）
})

export default router
