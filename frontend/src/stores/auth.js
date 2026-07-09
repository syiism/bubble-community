import { reactive, computed } from 'vue'
import { api, setOnUnauthorized } from '@/api'

const state = reactive({
  user: null,
  ready: false,
  /** 期望的用户 ID，用于检测 session 是否被其他登录覆盖 */
  expectedUserId: null,
})

export const isAuthenticated = computed(() => !!state.user)

/** 清除登录态的公共方法 — 供 api 层的 401 回调使用 */
function _clearAuth(reason) {
  console.warn(`[auth] 清除登录态: ${reason}`)
  _stopIdentityCheck()
  state.user = null
  state.expectedUserId = null
}

/** 后台定时检测身份一致性的 timer ID */
let _identityTimer = null

function _startIdentityCheck() {
  if (_identityTimer) return
  _identityTimer = setInterval(async () => {
    if (!state.expectedUserId) return
    try {
      const res = await api.me()
      if (res.user.id !== state.expectedUserId) {
        _clearAuth('session 被其他登录覆盖（定时检查发现用户不一致）')
      }
    } catch {
      // 网络错误不处理
    }
  }, 60000)
}

function _stopIdentityCheck() {
  if (_identityTimer) {
    clearInterval(_identityTimer)
    _identityTimer = null
  }
}

// 注册 401 回调 — 当任何 API 请求返回 401 时清除登录态
setOnUnauthorized(() => {
  _clearAuth('API 返回 401（session 过期或无效）')
})

export async function bootstrapAuth() {
  try {
    const res = await api.me()
    if (state.expectedUserId && res.user.id !== state.expectedUserId) {
      // session 已被其他登录覆盖，当前用户已不是期望的用户
      _clearAuth('bootstrapAuth 发现用户身份不匹配')
    } else {
      state.user = res.user
      state.expectedUserId = res.user.id
      _startIdentityCheck()
    }
  } catch {
    state.user = null
    state.expectedUserId = null
  }
  state.ready = true
}

export async function login(data) {
  const res = await api.login(data)
  state.user = res.user
  state.expectedUserId = res.user.id
  _startIdentityCheck()
}

export async function register(data) {
  const res = await api.register(data)
  state.user = res.user
  state.expectedUserId = res.user.id
  _startIdentityCheck()
}

export async function logout() {
  try {
    await api.logout()
  } catch {}
  state.user = null
  state.expectedUserId = null
  _stopIdentityCheck()
}

export async function refreshUser() {
  try {
    const res = await api.me()
    if (state.expectedUserId && res.user.id !== state.expectedUserId) {
      _clearAuth('refreshUser 发现用户身份不匹配')
      return
    }
    state.user = res.user
  } catch {
    _clearAuth('refreshUser 请求失败')
  }
}

export function getUser() {
  return state.user
}
