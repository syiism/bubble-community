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
    throw err
  }
  return data
}

export const api = {
  // auth
  register: (username, password) => request('POST', '/api/auth/register', { username, password }),
  login: (username, password) => request('POST', '/api/auth/login', { username, password }),
  logout: () => request('POST', '/api/auth/logout'),
  me: () => request('GET', '/api/auth/me'),
  // bubbles
  listBubbles: () => request('GET', '/api/bubbles'),
  createBubble: (data) => request('POST', '/api/bubbles', data),
  updateBubble: (id, data) => request('PUT', `/api/bubbles/${id}`, data),
  deleteBubble: (id) => request('DELETE', `/api/bubbles/${id}`),
  setVisibility: (id, pub) => request('POST', '/api/bubbles/visibility', { id, public: pub }),
  genShare: (id) => request('POST', '/api/bubbles/share', { id }),
  redeem: (code) => request('POST', '/api/bubbles/redeem', { code }),
  setCurrent: (style) => request('POST', '/api/bubbles/current', { style }),
  setFavorite: (id, favorite) => request('POST', '/api/bubbles/favorite', { id, favorite }),
  // user
  setAuthorName: (name) => request('POST', '/api/user/author-name', { name }),
}
