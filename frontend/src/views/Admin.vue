<template>
  <div class="pt-20 pb-32">
    <div class="max-w-6xl mx-auto px-6">

      <!-- 标题 -->
      <div class="mb-8 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-2">管理后台</h1>
        <p class="text-sm text-muted">用户 / 气泡数据总览与管理</p>
      </div>

      <!-- 吸附式搜索卡片 -->
      <div class="sticky top-16 z-40 -mx-6 px-6 bg-white/95 backdrop-blur-md border-b border-border shadow-[0_1px_6px_rgba(0,0,0,0.04)]">
        <div class="max-w-6xl mx-auto">
          <!-- 标签切换 -->
          <div class="flex gap-1 pt-3">
            <button v-for="tab in tabs" :key="tab.key"
                    :class="[
                      'px-5 py-2.5 text-sm font-medium transition-colors rounded-t-lg',
                      activeTab === tab.key
                        ? 'text-accent border-b-2 border-accent bg-accent/5'
                        : 'text-muted hover:text-ink hover:bg-canvas'
                    ]"
                    @click="activeTab = tab.key">
              {{ tab.label }}
            </button>
          </div>
          <!-- 筛选栏 -->
          <div class="flex flex-wrap items-center gap-3 pb-3 pt-2">
            <template v-if="activeTab === 'users'">
              <select v-model="userRoleFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部角色</option>
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
              </select>
              <input v-model="userQuery" type="text" placeholder="搜索用户名/署名"
                     class="flex-1 min-w-[160px] max-w-xs px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink placeholder:text-muted
                            focus:outline-none focus:border-accent transition-colors"
                     @keyup.enter="searchUsers" />
              <button class="px-3 py-1.5 text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                      @click="searchUsers">搜索</button>
            </template>
            <template v-else-if="activeTab === 'bubbles'">
              <select v-model="bubbleOfficialFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部类型</option>
                <option value="1">官方</option>
                <option value="0">用户</option>
              </select>
              <select v-model="bubblePublicFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部状态</option>
                <option value="1">公开</option>
                <option value="0">私有</option>
              </select>
              <input v-model="bubbleQuery" type="text" placeholder="搜索气泡名/作者"
                     class="flex-1 min-w-[160px] max-w-xs px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink placeholder:text-muted
                            focus:outline-none focus:border-accent transition-colors"
                     @keyup.enter="searchBubbles" />
              <button class="px-3 py-1.5 text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                      @click="searchBubbles">搜索</button>
            </template>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading && !stats" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
        <!-- 统计卡片 -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 my-8 scroll-animate scroll-animate-delay-1">
          <div v-for="card in statCards" :key="card.label"
               class="bg-surface border border-border rounded-xl p-4 text-center">
            <div class="text-2xl font-medium text-ink">{{ card.value }}</div>
            <div class="text-xs text-muted mt-1">{{ card.label }}</div>
          </div>
        </div>

        <!-- 用户管理 -->
        <div v-show="activeTab === 'users'"
             class="bg-surface border border-border rounded-xl p-5">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th class="pb-3 pr-4 font-medium">ID</th>
                  <th class="pb-3 pr-4 font-medium">用户名</th>
                  <th class="pb-3 pr-4 font-medium">署名</th>
                  <th class="pb-3 pr-4 font-medium">角色</th>
                  <th class="pb-3 pr-4 font-medium">注册时间</th>
                  <th class="pb-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id"
                    class="border-b border-border/50 hover:bg-canvas/50 transition-colors">
                  <td class="py-3 pr-4 text-muted">{{ u.id }}</td>
                  <td class="py-3 pr-4 font-medium text-ink flex items-center gap-2">
                    <img v-if="u.avatarUrl" :src="u.avatarUrl" class="w-6 h-6 rounded-full object-cover" />
                    <div class="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center text-xs text-accent" v-else>
                      {{ u.username.charAt(0).toUpperCase() }}
                    </div>
                    {{ u.username }}
                  </td>
                  <td class="py-3 pr-4 text-muted">{{ u.authorName || '—' }}</td>
                  <td class="py-3 pr-4">
                    <span :class="[
                      'inline-block px-2 py-0.5 rounded-full text-xs font-medium',
                      u.role === 'admin' ? 'bg-accent/10 text-accent' : 'bg-canvas text-muted'
                    ]">{{ u.role === 'admin' ? '管理员' : '用户' }}</span>
                  </td>
                  <td class="py-3 pr-4 text-muted text-xs">{{ fmtDate(u.createdAt) }}</td>
                  <td class="py-3">
                    <div class="flex items-center gap-3">
                      <button v-if="u.role !== 'admin'"
                              class="text-xs font-medium text-accent hover:text-accent/80 transition-colors"
                              @click="setRole(u.id, u.username, 'admin')">
                        设为管理员
                      </button>
                      <span v-else class="text-xs text-muted">—</span>
                      <button class="text-xs font-medium text-ink hover:text-accent transition-colors"
                              @click="resetPassword(u.id, u.username)">
                        重置密码
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!users.length">
                  <td colspan="6" class="py-8 text-center text-sm text-muted">暂无用户</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="usersTotalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ usersTotal }} 人，第 {{ usersPage }}/{{ usersTotalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="usersPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goUsersPage(usersPage - 1)">上一页</button>
              <button :disabled="usersPage >= usersTotalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goUsersPage(usersPage + 1)">下一页</button>
            </div>
          </div>
        </div>

        <!-- 气泡管理 -->
        <div v-show="activeTab === 'bubbles'"
             class="bg-surface border border-border rounded-xl p-5">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th class="pb-3 pr-4 font-medium">ID</th>
                  <th class="pb-3 pr-4 font-medium">名称</th>
                  <th class="pb-3 pr-4 font-medium">描述</th>
                  <th class="pb-3 pr-4 font-medium">作者</th>
                  <th class="pb-3 pr-4 font-medium">创建者</th>
                  <th class="pb-3 pr-4 font-medium">类型</th>
                  <th class="pb-3 pr-4 font-medium">状态</th>
                  <th class="pb-3 pr-4 font-medium">创建时间</th>
                  <th class="pb-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in bubbles" :key="b.id"
                    class="border-b border-border/50 hover:bg-canvas/50 transition-colors">
                  <td class="py-3 pr-4 text-muted">{{ b.id }}</td>
                  <td class="py-3 pr-4 font-medium text-ink max-w-32 truncate" :title="b.name">{{ b.name }}</td>
                  <td class="py-3 pr-4 text-muted max-w-32 truncate text-xs" :title="b.desc">{{ b.desc || '—' }}</td>
                  <td class="py-3 pr-4 text-muted">{{ b.authorName || '—' }}</td>
                  <td class="py-3 pr-4 text-muted">{{ b.username || '—' }}</td>
                  <td class="py-3 pr-4">
                    <span v-if="b.official"
                          class="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent">官方</span>
                    <span v-else class="text-xs text-muted">用户</span>
                  </td>
                  <td class="py-3 pr-4">
                    <button class="text-xs font-medium transition-colors"
                            :class="b.public ? 'text-green-600/70 hover:text-green-600' : 'text-muted hover:text-ink'"
                            @click="toggleVisibility(b)">
                      {{ b.public ? '公开' : '私有' }}
                    </button>
                  </td>
                  <td class="py-3 pr-4 text-muted text-xs">{{ fmtDate(b.createdAt) }}</td>
                  <td class="py-3">
                    <div class="flex items-center gap-2">
                      <button class="text-xs font-medium text-ink hover:text-accent transition-colors"
                              @click="openEditModal(b)">编辑</button>
                      <button class="text-xs font-medium text-red-500/70 hover:text-red-500 transition-colors"
                              @click="deleteBubble(b)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!bubbles.length">
                  <td colspan="9" class="py-8 text-center text-sm text-muted">暂无气泡</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="bubblesTotalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ bubblesTotal }} 个，第 {{ bubblesPage }}/{{ bubblesTotalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="bubblesPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goBubblesPage(bubblesPage - 1)">上一页</button>
              <button :disabled="bubblesPage >= bubblesTotalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goBubblesPage(bubblesPage + 1)">下一页</button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 编辑气泡模态框 -->
    <Teleport to="body">
      <div v-if="editingBubble"
           class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
           @click.self="editingBubble = null">
        <div class="bg-surface border border-border rounded-2xl p-6 w-full max-w-lg mx-4 shadow-2xl">
          <h3 class="text-base font-medium text-ink mb-5">编辑气泡 #{{ editingBubble.id }}</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-xs text-muted mb-1">名称</label>
              <input v-model="editForm.name" type="text" maxlength="64"
                     class="w-full px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink
                            focus:outline-none focus:border-accent transition-colors" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">描述</label>
              <input v-model="editForm.desc" type="text" maxlength="120"
                     class="w-full px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink
                            focus:outline-none focus:border-accent transition-colors" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-muted mb-1">气泡颜色</label>
                <div class="flex gap-2">
                  <input v-model="editForm.color" type="text" placeholder="#..."
                         class="flex-1 px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink
                                focus:outline-none focus:border-accent transition-colors" />
                  <input v-model="editForm.color" type="color"
                         class="w-9 h-9 rounded-lg border border-border cursor-pointer bg-canvas" />
                </div>
              </div>
              <div>
                <label class="block text-xs text-muted mb-1">文字颜色</label>
                <div class="flex gap-2">
                  <input v-model="editForm.textColor" type="text" placeholder="#..."
                         class="flex-1 px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink
                                focus:outline-none focus:border-accent transition-colors" />
                  <input v-model="editForm.textColor" type="color"
                         class="w-9 h-9 rounded-lg border border-border cursor-pointer bg-canvas" />
                </div>
              </div>
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">作者署名</label>
              <input v-model="editForm.authorName" type="text" maxlength="32"
                     class="w-full px-3 py-2 bg-canvas border border-border rounded-lg text-sm text-ink
                            focus:outline-none focus:border-accent transition-colors" />
            </div>
            <div class="flex items-center gap-3">
              <label class="text-xs text-muted">公开可见</label>
              <button @click="editForm.public = !editForm.public"
                      :class="[
                        'relative w-10 h-5 rounded-full transition-colors',
                        editForm.public ? 'bg-accent' : 'bg-border'
                      ]">
                <span :class="[
                  'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm',
                  editForm.public ? 'translate-x-5' : ''
                ]" />
              </button>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-border">
            <button class="px-4 py-2 text-sm font-medium text-muted hover:text-ink transition-colors"
                    @click="editingBubble = null">取消</button>
            <button :disabled="savingEdit"
                    class="px-5 py-2 text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors disabled:opacity-50"
                    @click="saveEdit">
              {{ savingEdit ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '@/api'

const tabs = [
  { key: 'users', label: '用户管理' },
  { key: 'bubbles', label: '气泡管理' },
]

const activeTab = ref('users')

// ===== 统计 =====
const stats = ref(null)
const statCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '用户总数', value: s.totalUsers },
    { label: '气泡总数', value: s.totalBubbles },
    { label: '官方气泡', value: s.officialBubbles },
    { label: '管理员', value: s.adminCount },
    { label: '总收藏数', value: s.totalFavorites },
    { label: '使用中气泡', value: s.activeBubbles },
  ]
})

// ===== 用户管理 =====
const users = ref([])
const usersTotal = ref(0)
const usersPage = ref(1)
const usersPageSize = 20
const userQuery = ref('')
const userRoleFilter = ref('')
const usersTotalPages = computed(() => Math.max(1, Math.ceil(usersTotal.value / usersPageSize)))

const loadUsers = async () => {
  try {
    const data = await api.adminUsers(usersPage.value, usersPageSize, userQuery.value, userRoleFilter.value)
    users.value = data.users || []
    usersTotal.value = data.total || 0
  } catch (e) { console.error(e) }
}

const searchUsers = () => { usersPage.value = 1; loadUsers() }
const goUsersPage = (p) => { usersPage.value = p; loadUsers() }

// ===== 气泡管理 =====
const bubbles = ref([])
const bubblesTotal = ref(0)
const bubblesPage = ref(1)
const bubblesPageSize = 20
const bubbleQuery = ref('')
const bubbleOfficialFilter = ref('')
const bubblePublicFilter = ref('')
const bubblesTotalPages = computed(() => Math.max(1, Math.ceil(bubblesTotal.value / bubblesPageSize)))

const loadBubbles = async () => {
  try {
    const data = await api.adminBubbles(bubblesPage.value, bubblesPageSize, bubbleQuery.value,
                                        bubbleOfficialFilter.value, bubblePublicFilter.value)
    bubbles.value = data.bubbles || []
    bubblesTotal.value = data.total || 0
  } catch (e) { console.error(e) }
}

const searchBubbles = () => { bubblesPage.value = 1; loadBubbles() }
const goBubblesPage = (p) => { bubblesPage.value = p; loadBubbles() }

// 筛选变化时自动重新搜索
watch([userRoleFilter], () => { usersPage.value = 1; loadUsers() })
watch([bubbleOfficialFilter, bubblePublicFilter], () => { bubblesPage.value = 1; loadBubbles() })

// ===== 工具 =====
const loading = ref(false)
const fmtDate = (iso) => {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

// ===== 用户操作 =====
const setRole = async (userId, username, role) => {
  if (!confirm(`确定将 ${username} 设为管理员？`)) return
  try { await api.adminSetRole(userId, role); await loadUsers() }
  catch (e) { alert(e.message || '操作失败') }
}

const resetPassword = async (userId, username) => {
  const pwd = prompt(`输入 ${username} 的新密码（至少 6 位）：`)
  if (!pwd) return
  if (pwd.length < 6) { alert('密码长度不能少于 6 个字符'); return }
  try { await api.adminSetPassword(userId, pwd); alert(`用户 ${username} 的密码已重置`) }
  catch (e) { alert(e.message || '操作失败') }
}

// ===== 气泡操作 =====
const toggleVisibility = async (b) => {
  try { const d = await api.adminSetBubbleVisibility(b.id, !b.public); b.public = d.public }
  catch (e) { alert(e.message || '操作失败') }
}

const deleteBubble = async (b) => {
  const label = b.name || `#${b.id}`
  if (!confirm(`确定删除气泡「${label}」？\n此操作不可撤销。`)) return
  try { await api.adminDeleteBubble(b.id); bubbles.value = bubbles.value.filter(x => x.id !== b.id) }
  catch (e) { alert(e.message || '操作失败') }
}

// ===== 编辑气泡 =====
const editingBubble = ref(null)
const savingEdit = ref(false)
const editForm = ref({ name: '', desc: '', color: '', textColor: '', public: false, authorName: '' })

const openEditModal = (b) => {
  editForm.value = {
    name: b.name,
    desc: b.desc || '',
    color: b.color || '',
    textColor: b.textColor || '',
    public: b.public,
    authorName: b.authorName || '',
  }
  editingBubble.value = b
}

const saveEdit = async () => {
  savingEdit.value = true
  try {
    await api.adminUpdateBubble(editingBubble.value.id, editForm.value)
    // 更新本地行
    const idx = bubbles.value.findIndex(x => x.id === editingBubble.value.id)
    if (idx >= 0) {
      Object.assign(bubbles.value[idx], {
        name: editForm.value.name,
        desc: editForm.value.desc,
        public: editForm.value.public,
        authorName: editForm.value.authorName,
      })
    }
    editingBubble.value = null
  } catch (e) { alert(e.message || '保存失败') }
  finally { savingEdit.value = false }
}

// ===== 初始化 =====
const loadAll = async () => {
  loading.value = true
  try { const d = await api.adminStats(); stats.value = d.stats } catch (e) { console.error(e) }
  loading.value = false
  await Promise.all([loadUsers(), loadBubbles()])
}

onMounted(loadAll)
</script>
