/** 401 回调 — 由 auth store 在 bootstrap 时注册 */
let _onUnauthorized = null

export function setOnUnauthorized(cb) {
  _onUnauthorized = cb
}

async function request(method, url, body) {
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
  return data
}

export const api = {
  login: (data) => request('POST', '/bubble-community/api/auth/login', data),
  me: () => request('GET', '/bubble-community/api/auth/me'),
  logout: () => request('POST', '/bubble-community/api/auth/logout'),
  checkUsername: (username) => request('GET', `/bubble-community/api/auth/check-username?username=${encodeURIComponent(username)}`),
  register: (data) => request('POST', '/bubble-community/api/auth/register', data),
  listBubbles: () => request('GET', '/bubble-community/api/bubbles'),
  createBubble: (data) => request('POST', '/bubble-community/api/bubbles', data),
  updateBubble: (id, data) => request('PUT', `/bubble-community/api/bubbles/${id}`, data),
  deleteBubble: (id) => request('DELETE', `/bubble-community/api/bubbles/${id}`),
  setVisibility: (id, pub) => request('POST', '/bubble-community/api/bubbles/visibility', { id, public: pub }),
  genShare: (id) => request('POST', '/bubble-community/api/bubbles/share', { id }),
  redeem: (code) => request('POST', '/bubble-community/api/bubbles/redeem', { code }),
  setCurrent: (style) => request('POST', '/bubble-community/api/bubbles/current', { style }),
  setFavorite: (id, favorite) => request('POST', '/bubble-community/api/bubbles/favorite', { id, favorite }),
  setAuthorName: (name) => request('POST', '/bubble-community/api/user/author-name', { name }),
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
  adminBubbles: (page, size, query, official, pub) => request('GET', `/bubble-community/api/admin/bubbles?page=${page}&size=${size}&query=${encodeURIComponent(query)}&official=${official}&public=${pub}`),
  adminDeleteBubble: (id) => request('DELETE', `/bubble-community/api/admin/bubbles/${id}`),
  adminSetBubbleVisibility: (id, pub) => request('PUT', `/bubble-community/api/admin/bubbles/${id}/visibility`, { public: pub }),
  adminUpdateBubble: (id, data) => request('PUT', `/bubble-community/api/admin/bubbles/${id}`, data),
}
