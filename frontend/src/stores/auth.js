import { reactive, computed } from 'vue'
import { api, setOnUnauthorized } from '@/api'

const state = reactive({
  user: null,
  ready: false,
})

export const isAuthenticated = computed(() => !!state.user)

/** 清除登录态 */
function _clearAuth(reason) {
  console.warn(`[auth] 清除登录态: ${reason}`)
  state.user = null
}

// 注册 401 回调 — 当任何 API 请求返回 401 时清除登录态
setOnUnauthorized(() => {
  _clearAuth('API 返回 401（session 过期或无效）')
})

export async function bootstrapAuth() {
  try {
    const res = await api.me()
    state.user = res.user
  } catch {
    state.user = null
  }
  state.ready = true
}

export async function login(data) {
  const res = await api.login(data)
  state.user = res.user
}

export async function register(data) {
  const res = await api.register(data)
  state.user = res.user
}

export async function logout() {
  try {
    await api.logout()
  } catch {}
  state.user = null
}

export async function refreshUser() {
  try {
    const res = await api.me()
    state.user = res.user
  } catch {
    _clearAuth('refreshUser 请求失败')
  }
}

export function getUser() {
  return state.user
}
