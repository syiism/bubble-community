<template>
  <div class="pt-20 pb-32">
    <div class="max-w-6xl mx-auto px-6">
      <div class="mb-10 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-2">管理后台</h1>
        <p class="text-sm text-muted">用户 / 气泡数据总览与管理</p>
      </div>

      <div v-if="loading" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
        <!-- 统计卡片 -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-10 scroll-animate scroll-animate-delay-1">
          <div v-for="card in statCards" :key="card.label"
               class="bg-surface border border-border rounded-xl p-4 text-center">
            <div class="text-2xl font-medium text-ink">{{ card.value }}</div>
            <div class="text-xs text-muted mt-1">{{ card.label }}</div>
          </div>
        </div>

        <!-- 用户列表 -->
        <div class="bg-surface border border-border rounded-xl p-5 scroll-animate scroll-animate-delay-2">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-base font-medium text-ink">用户列表</h2>
            <div class="flex gap-2">
              <input v-model="searchQuery" type="text" placeholder="搜索用户名/署名"
                     class="w-48 px-3 py-1.5 bg-canvas border border-border rounded-lg text-sm text-ink placeholder:text-muted
                            focus:outline-none focus:border-accent transition-colors"
                     @keyup.enter="searchUsers" />
              <button class="px-3 py-1.5 text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                      @click="searchUsers">搜索</button>
            </div>
          </div>

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
                      u.role === 'admin'
                        ? 'bg-accent/10 text-accent'
                        : 'bg-canvas text-muted'
                    ]">{{ u.role === 'admin' ? '管理员' : '用户' }}</span>
                  </td>
                  <td class="py-3 pr-4 text-muted text-xs">{{ formatDate(u.createdAt) }}</td>
                  <td class="py-3">
                    <button v-if="u.role !== 'admin'"
                            class="text-xs font-medium text-accent hover:text-accent/80 transition-colors"
                            @click="setRole(u.id, u.username, 'admin')">
                      设为管理员
                    </button>
                    <span v-else class="text-xs text-muted">—</span>
                  </td>
                </tr>
                <tr v-if="!users.length">
                  <td colspan="6" class="py-8 text-center text-sm text-muted">暂无用户</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ total }} 人，第 {{ currentPage }}/{{ totalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="currentPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40
                             hover:bg-canvas transition-colors"
                      @click="goPage(currentPage - 1)">上一页</button>
              <button :disabled="currentPage >= totalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40
                             hover:bg-canvas transition-colors"
                      @click="goPage(currentPage + 1)">下一页</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'

const loading = ref(false)
const stats = ref(null)
const users = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')

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

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const formatDate = (iso) => {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

const loadStats = async () => {
  try {
    const data = await api.adminStats()
    stats.value = data.stats
  } catch (e) {
    console.error(e)
  }
}

const loadUsers = async () => {
  loading.value = true
  try {
    const data = await api.adminUsers(currentPage.value, pageSize.value, searchQuery.value)
    users.value = data.users || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const searchUsers = () => {
  currentPage.value = 1
  loadUsers()
}

const goPage = (p) => {
  currentPage.value = p
  loadUsers()
}

const setRole = async (userId, username, role) => {
  if (!confirm(`确定将 ${username} 设为管理员？`)) return
  try {
    await api.adminSetRole(userId, role)
    await loadUsers()
  } catch (e) {
    alert(e.message || '操作失败')
  }
}

onMounted(() => {
  loadStats()
  loadUsers()
})
</script>
