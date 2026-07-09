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
  login: (data) => request('POST', '/bubble-community/api/auth/login', data),
  me: () => request('GET', '/bubble-community/api/auth/me'),
  logout: () => request('POST', '/bubble-community/api/auth/logout'),
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
}