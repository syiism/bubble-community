/** 401 回调 — 由 auth store 在 bootstrap 时注册 */
let _onUnauthorized = null

export function setOnUnauthorized(cb) {
  _onUnauthorized = cb
}

const _cache = new Map()
const CACHE_TTL = 5000

function _cacheKey(method, url) {
  const token = document.cookie.match(/(?:^|;\s*)bubble_community_token=([^;]+)/)
  const tag = token ? token[1].slice(-8) : 'anon'
  return `${tag}:${method}:${url}`
}

function _cacheGet(method, url) {
  const key = _cacheKey(method, url)
  const entry = _cache.get(key)
  if (entry && Date.now() - entry.ts < CACHE_TTL) {
    return entry.data
  }
  _cache.delete(key)
  return null
}

function _cacheSet(method, url, data) {
  _cache.set(_cacheKey(method, url), { data, ts: Date.now() })
}

function _cacheClear() {
  _cache.clear()
}

async function request(method, url, body) {
  if (method === 'GET') {
    const cached = _cacheGet(method, url)
    if (cached !== null) return cached
  }

  const headers = { 'Content-Type': 'application/json' }
  const opts = { method, headers, credentials: 'include' }
  if (body !== undefined) opts.body = JSON.stringify(body)

  const res = await fetch(url, opts)
  let data = null
  const text = await res.text()
  if (text) {
    try { data = JSON.parse(text) } catch { data = { detail: text } }
  }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `请求失败 (${res.status})`
    const err = new Error(msg)
    err.status = res.status
    // 401 → session 过期或被覆盖，通知 auth store 清除状态
    if (res.status === 401 && _onUnauthorized) {
      _onUnauthorized()
    }
    throw err
  }
  if (method === 'GET') _cacheSet(method, url, data)
  else _cacheClear()
  return data
}

export const api = {
  login: (data) => request('POST', '/bubble-community/api/auth/login', data),
  me: () => request('GET', '/bubble-community/api/auth/me'),
  logout: () => request('POST', '/bubble-community/api/auth/logout'),
  checkUsername: (username) => request('GET', `/bubble-community/api/auth/check-username?username=${encodeURIComponent(username)}`),
  register: (data) => request('POST', '/bubble-community/api/auth/register', data),
  listBubbles: (params = {}) => {
    const q = new URLSearchParams()
    if (typeof params === 'string') {
      // backward compat: listBubbles(category)
      if (params) q.set('category', params)
    } else {
      const { section, page, size, sort, q: search, category } = params
      if (section) q.set('section', section)
      if (page) q.set('page', String(page))
      if (size) q.set('size', String(size))
      if (sort) q.set('sort', sort)
      if (search) q.set('q', search)
      if (category) q.set('category', category)
    }
    const qs = q.toString()
    return request('GET', `/bubble-community/api/bubbles${qs ? `?${qs}` : ''}`)
  },
  createBubble: (data) => request('POST', '/bubble-community/api/bubbles', data),
  updateBubble: (id, data) => request('PUT', `/bubble-community/api/bubbles/${id}`, data),
  deleteBubble: (id) => request('DELETE', `/bubble-community/api/bubbles/${id}`),
  setVisibility: (id, pub) => request('POST', '/bubble-community/api/bubbles/visibility', { id, public: pub }),
  genShare: (id) => request('POST', '/bubble-community/api/bubbles/share', { id }),
  communityCounts: () => request('GET', '/bubble-community/api/bubbles/community-counts'),
  redeem: (code) => request('POST', '/bubble-community/api/bubbles/redeem', { code }),
  removeImported: (bubbleId) => request('POST', '/bubble-community/api/bubbles/remove-imported', { bubble_id: bubbleId }),
  setCurrent: (style) => request('POST', '/bubble-community/api/bubbles/current', { style }),
  setFavorite: (id, favorite) => request('POST', '/bubble-community/api/bubbles/favorite', { id, favorite }),
  setAuthorName: (name) => request('POST', '/bubble-community/api/user/author-name', { name }),
  setUsername: (username) => request('POST', '/bubble-community/api/user/username', { username }),
  uploadAvatar: (file) => {
    const form = new FormData()
    form.append('file', file)
    return fetch('/bubble-community/api/user/avatar', {
      method: 'POST', body: form, credentials: 'include',
    }).then(async res => {
      const text = await res.text()
      const data = text ? JSON.parse(text) : {}
      if (!res.ok) throw new Error(data.detail || data.message || '上传失败')
      return data
    })
  },
  forgetPassword: (data) => request('POST', '/bubble-community/api/auth/forget', data),
  // 管理后台
  adminStats: () => request('GET', '/bubble-community/api/admin/stats'),
  adminUsers: (page, size, query, role) => request('GET', `/bubble-community/api/admin/users?page=${page}&size=${size}&query=${encodeURIComponent(query)}&role=${role}`),
  adminSetRole: (userId, role) => request('PUT', `/bubble-community/api/admin/users/${userId}/role`, { role }),
  adminSetPassword: (userId, password) => request('PUT', `/bubble-community/api/admin/users/${userId}/password`, { password }),
  adminDeleteUser: (userId) => request('DELETE', `/bubble-community/api/admin/users/${userId}`),
  adminBatchDeleteUsers: (ids) => request('POST', '/bubble-community/api/admin/users/batch-delete', { ids }),
  adminBatchDeleteBubbles: (ids) => request('POST', '/bubble-community/api/admin/bubbles/batch-delete', { ids }),
  adminBubbles: (page, size, query, official, pub, startDate, category) =>
    request('GET', `/bubble-community/api/admin/bubbles?page=${page}&size=${size}&query=${encodeURIComponent(query)}&official=${official}&public=${pub}&start_date=${startDate || ''}&category=${category || ''}`),
  adminDeleteBubble: (id) => request('DELETE', `/bubble-community/api/admin/bubbles/${id}`),
  adminSetBubbleVisibility: (id, pub) => request('PUT', `/bubble-community/api/admin/bubbles/${id}/visibility`, { public: pub }),
  adminUpdateBubble: (id, data) => request('PUT', `/bubble-community/api/admin/bubbles/${id}`, data),
  // 多设备会话管理
  listSessions: () => request('GET', '/bubble-community/api/auth/sessions'),
  revokeSession: (sessionId) => request('POST', '/bubble-community/api/auth/sessions/revoke', { session_id: sessionId }),
  logoutAll: () => request('POST', '/bubble-community/api/auth/sessions/logout-all'),
  // 公告
  announcements: () => request('GET', '/bubble-community/api/announcements'),
  announcementsAll: () => request('GET', '/bubble-community/api/announcements/all'),
  adminAnnouncements: (page, size) =>
    request('GET', `/bubble-community/api/admin/announcements?page=${page}&size=${size}`),
  adminCreateAnnouncement: (data) => request('POST', '/bubble-community/api/admin/announcements', data),
  adminUpdateAnnouncement: (id, data) => request('PUT', `/bubble-community/api/admin/announcements/${id}`, data),
  adminDeleteAnnouncement: (id) => request('DELETE', `/bubble-community/api/admin/announcements/${id}`),
  // 在线管理
  adminOnlineUsers: (page, size) =>
    request('GET', `/bubble-community/api/admin/online-users?page=${page}&size=${size}`),
  adminKickSession: (userId, sessionId) =>
    request('POST', '/bubble-community/api/admin/online-users/kick', { user_id: userId, session_id: sessionId }),
  adminBlockUser: (userId) => request('POST', `/bubble-community/api/admin/users/${userId}/block`),
  adminUnblockUser: (userId) => request('POST', `/bubble-community/api/admin/users/${userId}/unblock`),
}
