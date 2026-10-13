import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  { path: '/', name: 'home', component: () => import('@/views/Home.vue') },
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/Register.vue') },
  { path: '/read/:id', name: 'reader', component: () => import('@/views/Reader.vue') },
  { path: '/profile', name: 'profile', component: () => import('@/views/Profile.vue'), meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: () => import('@/views/Admin.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.requiresAuth && !store.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !store.isAdmin) {
    return { path: '/' }
  }
  return true
})

export default router
