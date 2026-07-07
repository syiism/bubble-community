import { reactive, computed } from 'vue'
import { api } from '@/api'

const state = reactive({
  user: null,
  ready: false,
})

export const isAuthenticated = computed(() => !!state.user)

export async function bootstrapAuth() {
  try {
    const res = await api.me()
    state.user = res.user
  } catch {
    state.user = null
  }
  state.ready = true
}

export async function login(username, password) {
  const res = await api.login(username, password)
  state.user = res.user
  return res.user
}

export async function register(username, password) {
  const res = await api.register(username, password)
  state.user = res.user
  return res.user
}

export async function logout() {
  try { await api.logout() } catch {}
  state.user = null
}

export async function refreshUser() {
  try {
    const res = await api.me()
    state.user = res.user
  } catch {
    state.user = null
  }
}

export function getUser() {
  return state.user
}
