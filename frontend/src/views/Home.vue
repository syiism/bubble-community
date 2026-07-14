<template>
  <div class="pb-32" style="padding-top: calc(5rem + env(safe-area-inset-top, 0px))">
    <div class="max-w-4xl mx-auto px-6">
      <div class="mb-12 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-4">段评气泡社区</h1>
        <p class="text-sm text-muted leading-relaxed">
          选择喜欢的气泡外观，保存后回到阅读界面翻页即可生效。你也可以自己添加/编辑气泡，生成分享码给别人用。
        </p>
      </div>

      <!-- 吸附式搜索栏 -->
      <div class="sticky z-40 -mx-6 px-6 mb-6 bg-surface/40 backdrop-blur-md"
           style="top: calc(4rem + env(safe-area-inset-top, 0px)); backdrop-filter: blur(12px);">
        <div class="max-w-4xl mx-auto">
          <div class="relative flex items-center py-2.5">
            <svg class="absolute left-0 w-4 h-4 text-muted pointer-events-none ml-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input v-model="searchQuery" type="text" placeholder="搜索气泡名称 / 署名..."
                   class="w-full pl-8 pr-20 py-2.5 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted
                          transition-all duration-200
                          focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 focus:bg-surface"
                   @keyup.enter="onSearchSubmit" />
            <button v-if="searchQuery"
                    class="absolute right-0 px-3 py-1.5 text-xs font-medium text-muted hover:text-ink bg-surface/80 border border-border rounded-lg transition-colors"
                    @click="clearSearch">
              清空
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading && !styles.length" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
        <!-- 分区 category（二级筛选） -->
        <div class="mb-4 -mx-6 px-6 sm:mx-0 sm:px-0 overflow-x-auto scrollbar-none scroll-animate">
          <div class="flex gap-1 min-w-max">
            <button v-for="tab in categoryTabs" :key="tab.key"
                    :class="[
                      'px-3 sm:px-4 py-1.5 text-xs sm:text-sm font-medium rounded-full transition-colors whitespace-nowrap',
                      currentCategory === tab.key
                        ? 'bg-ink text-white'
                        : 'text-muted bg-surface border border-border hover:text-ink hover:bg-canvas'
                    ]"
                    @click="switchCategory(tab.key)">
              {{ tab.label }}
            </button>
          </div>
        </div>

        <!-- section Tab：公开 / 我的 / 收藏 / 导入 -->
        <div class="mb-6 -mx-6 px-6 sm:mx-0 sm:px-0 overflow-x-auto scrollbar-none scroll-animate">
          <div class="flex gap-1 border-b border-border min-w-max sm:min-w-0">
            <button v-for="tab in sectionTabs" :key="tab.key"
                    :class="[
                      'px-3 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-medium transition-colors rounded-t-lg -mb-px whitespace-nowrap flex-shrink-0',
                      currentSection === tab.key
                        ? 'text-accent border-b-2 border-accent bg-accent/5'
                        : 'text-muted hover:text-ink hover:bg-canvas'
                    ]"
                    @click="switchSection(tab.key)">
              <span class="sm:hidden">{{ tab.shortLabel }}</span>
              <span class="hidden sm:inline">{{ tab.label }}</span>
              <span v-if="sectionCount(tab.key) != null" class="ml-1 text-[10px] sm:text-xs opacity-70">{{ sectionCount(tab.key) }}</span>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="md:col-span-2 space-y-4">
            <div class="bg-surface border border-border rounded-xl p-5 scroll-animate scroll-animate-delay-1">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-base font-medium text-ink">我的气泡</h2>
                <button
                  v-if="canUpload"
                  class="text-sm font-medium text-accent hover:text-accent/80 transition-colors flex items-center gap-1"
                  @click="openEditor()"
                >
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  添加
                </button>
              </div>

              <div v-if="authorNamePanel" class="bg-pale-yellow/50 border border-accent/20 rounded-xl p-4 mb-4">
                <div class="flex items-center justify-between mb-2">
                  <h3 class="text-sm font-medium text-ink">我的署名</h3>
                </div>
                <p class="text-xs text-muted mb-3">
                  这个名字只在你公开或用分享码分享出去的气泡上，给别人看到（显示为"by 署名"）。不影响你的登录账号，可随时修改，不可与他人重复。
                </p>
                <div class="flex gap-3">
                  <input
                    v-model="authorName"
                    type="text"
                    maxlength="16"
                    placeholder="如 隔壁老王（留空=匿名书友）"
                    class="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                  />
                  <button
                    :disabled="savingAuthor"
                    class="px-4 py-2 text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="saveAuthorName"
                  >
                    {{ savingAuthor ? '保存中...' : '保存' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="bg-surface border border-border rounded-xl p-5 scroll-animate scroll-animate-delay-2">
              <h2 class="text-base font-medium text-ink mb-4">输入分享码使用</h2>
              <div class="flex gap-3">
                <input
                  v-model="redeemCode"
                  type="text"
                  placeholder="粘贴别人给你的分享码"
                  class="flex-1 px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors uppercase"
                />
                <button
                  :disabled="redeeming"
                  class="px-5 py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="redeem"
                >
                  {{ redeeming ? '使用中...' : '使用' }}
                </button>
              </div>
            </div>
          </div>

          <div class="md:col-span-1">
            <div class="bg-surface border border-border rounded-xl p-5 scroll-animate scroll-animate-delay-3" style="position: sticky; top: calc(6rem + env(safe-area-inset-top, 0px));">
              <div class="flex items-center gap-3 mb-4">
                <div class="relative w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center overflow-hidden cursor-pointer"
                     @click="$refs.avatarInput.click()">
                  <img v-if="userAvatar" :src="userAvatar" :alt="userName" class="w-full h-full object-cover" />
                  <svg v-else class="w-6 h-6 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <!-- 右下角笔图标 -->
                  <div class="absolute bottom-0 right-0 w-4 h-4 bg-surface rounded-full shadow-sm flex items-center justify-center">
                    <svg class="w-2.5 h-2.5 text-ink" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                      <path d="M16.84 2.73c-.39 0-.77.15-1.07.44l-2.12 2.12 5.3 5.3 2.12-2.12c.6-.6.6-1.56 0-2.16l-3.18-3.18c-.28-.28-.66-.44-1.05-.44M2 18.08V22h3.92l11.3-11.3-5.3-5.3L2 18.08Z"/>
                    </svg>
                  </div>
                  <input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="onAvatarChange" />
                </div>
                <div>
                  <div class="text-sm font-medium text-ink">{{ userName }}</div>
                  <div class="text-xs text-muted">{{ authorName || '匿名书友' }}</div>
                </div>
              </div>

              <div class="grid grid-cols-3 gap-2">
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ myStylesCount }}</div>
                  <div class="text-xs text-muted">我的气泡</div>
                </div>
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ publicStylesCount }}</div>
                  <div class="text-xs text-muted">公开</div>
                </div>
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ privateStylesCount }}</div>
                  <div class="text-xs text-muted">私有</div>
                </div>
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ importedStylesCount }}</div>
                  <div class="text-xs text-muted">已导入</div>
                </div>
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ favoritesCount }}</div>
                  <div class="text-xs text-muted">收藏</div>
                </div>
                <div class="bg-canvas rounded-lg p-2.5 text-center">
                  <div class="text-base font-medium text-ink">{{ totalUses }}</div>
                  <div class="text-xs text-muted">被使用</div>
                </div>
              </div>

              <div class="mt-4 pt-4 border-t border-border">
                <div class="text-xs text-muted mb-2">全站统计</div>
                <div class="grid grid-cols-2 gap-2">
                  <div class="bg-canvas rounded-lg p-2.5 text-center">
                    <div class="text-base font-medium text-ink">{{ communityStats.totalPublic }}</div>
                    <div class="text-xs text-muted">公开</div>
                  </div>
                  <div class="bg-canvas rounded-lg p-2.5 text-center">
                    <div class="text-base font-medium text-ink">{{ communityStats.totalPrivate }}</div>
                    <div class="text-xs text-muted">私有</div>
                  </div>
                </div>
              </div>
              <div class="mt-3">
                <button class="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-muted bg-canvas rounded-xl hover:text-ink hover:bg-border/50 transition-colors"
                        @click="showAllAnnouncements = true">
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                  </svg>
                  查看公告
                </button>
              </div>
            </div>
          </div>
        </div>

        <BubbleList
          :styles="styles"
          :current-id="currentId"
          :title="currentSectionTitle"
          :total="listTotal"
          :sortable="currentSection === 'public'"
          :sort-by="sortBy"
          :loading="loading"
          :loading-more="loadingMore"
          :has-more="hasMore"
          @select="handleSelect"
          @edit="handleEdit"
          @delete="handleDelete"
          @share="handleShare"
          @copy-share="handleCopyShare"
          @toggle-public="handleTogglePublic"
          @toggle-favorite="handleToggleFavorite"
          @remove-import="handleRemoveImport"
          @load-more="loadMore"
          @toggle-sort="toggleSort"
        />
      </template>
    </div>
  </div>

  <div
    v-if="currentId"
    class="fixed bottom-0 left-0 right-0 z-30 bg-surface/95 backdrop-blur border-t border-border p-safe-bottom"
  >
    <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
      <div class="flex-1 min-w-0">
        <div class="text-xs text-muted">当前选中</div>
        <div class="text-sm font-medium text-ink truncate">{{ currentBubbleName }}</div>
      </div>
      <button
        :disabled="!currentId || saving"
        class="px-8 py-3 text-sm font-medium text-white bg-accent rounded-xl hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        @click="saveCurrentStyle"
      >
        {{ saving ? '保存中...' : '保存并应用' }}
      </button>
    </div>
  </div>

  <Editor
    v-model="showEditor"
    :style="editingStyle"
    @close="closeEditor"
    @submit="handleEditorSubmit"
    @toast="showToast"
  />

  <!-- 公告弹窗（霸屏） -->
  <el-dialog v-model="showAnnouncementModal" width="600px" top="5vh"
             :close-on-click-modal="false" :show-close="false" class="announcement-dialog"
             @closed="showAnnouncementModal = false">
    <div class="py-2">
      <div class="flex items-center gap-3 mb-6">
        <span class="text-2xl">📢</span>
        <h2 class="text-xl font-medium text-ink">公告</h2>
      </div>
      <div v-if="activeAnnouncements.length" class="space-y-5">
        <div v-for="ann in activeAnnouncements" :key="ann.id"
             class="bg-canvas rounded-xl p-5 border border-border/50"
             :class="ann.priority === 'high' ? 'border-l-4 border-l-red-400' : ''">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-base font-medium text-ink">{{ ann.title }}</span>
            <span v-if="ann.priority === 'high'"
                  class="px-2 py-0.5 text-xs font-medium text-white bg-red-500 rounded">重要</span>
          </div>
          <p class="text-sm text-muted leading-relaxed whitespace-pre-wrap">{{ ann.content }}</p>
          <div class="text-xs text-muted mt-3">{{ fmtDate(ann.createdAt) }}</div>
        </div>
      </div>
      <div v-else class="text-center py-8 text-sm text-muted">暂无公告</div>
      <button class="w-full mt-6 py-3 rounded-xl text-sm font-medium bg-ink text-white hover:bg-charcoal transition-colors"
              @click="closeAnnouncementModal">
        我知道了
      </button>
    </div>
  </el-dialog>

  <!-- 全部公告面板 -->
  <el-dialog v-model="showAllAnnouncements" title="全部公告" width="560px" top="8vh"
             class="editor-dialog" @closed="showAllAnnouncements = false">
    <div v-if="allAnnouncements.length" class="space-y-4">
      <div v-for="ann in allAnnouncements" :key="ann.id"
           class="bg-canvas rounded-xl p-4 border border-border/50"
           :class="{ 'opacity-50': !ann.isActive }">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-medium text-ink">{{ ann.title }}</span>
          <span v-if="ann.priority === 'high'" class="px-1.5 py-0.5 text-xs font-medium text-red-600 bg-red-50 rounded">重要</span>
          <span v-if="!ann.isActive" class="px-1.5 py-0.5 text-xs text-muted bg-border/50 rounded">已关闭</span>
        </div>
        <p class="text-xs text-muted">{{ ann.content }}</p>
        <div class="text-xs text-muted mt-2">{{ fmtDate(ann.createdAt) }}</div>
      </div>
    </div>
    <div v-else class="text-center py-10 text-sm text-muted">暂无公告</div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox, ElNotification } from 'element-plus'
import BubbleList from '@/components/BubbleList.vue'
import Editor from '@/components/Editor.vue'
import { api } from '@/api'
import { getUser, refreshUser } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const styles = ref([])
const searchQuery = ref('')
const debouncedQ = ref('')
const currentCategory = ref('')
const currentSection = ref('public')
const sortBy = ref('new')
const page = ref(1)
const pageSize = 18
const hasMore = ref(false)
const listTotal = ref(0)
const loadingMore = ref(false)
const counts = ref({ mine: 0, favorites: 0, imported: 0, public: 0, myPublic: 0, myPrivate: 0, totalUses: 0 })
const currentBubbleMeta = ref(null)
let searchTimer = null
let loadSeq = 0
/** Prefetched next page for smoother infinite scroll */
let prefetchCache = null // { page, section, sort, q, category, data } | null
let prefetchInFlight = null // Promise | null

const categoryTabs = [
  { key: '', label: '全部' },
  { key: 'original', label: '原创' },
  { key: 'anime', label: '动漫' },
  { key: 'classical', label: '古风' },
  { key: 'other', label: '其他' },
]
const sectionTabs = [
  { key: 'public', label: '大家公开的', shortLabel: '公开' },
  { key: 'mine', label: '我的气泡', shortLabel: '我的' },
  { key: 'favorites', label: '我的收藏', shortLabel: '收藏' },
  { key: 'imported', label: '我导入的', shortLabel: '导入' },
]

const sectionCount = (key) => {
  const c = counts.value
  if (!c) return null
  if (key === 'public') return c.public
  if (key === 'mine') return c.mine
  if (key === 'favorites') return c.favorites
  if (key === 'imported') return c.imported
  return null
}

const currentSectionTitle = computed(() => {
  const t = sectionTabs.find(x => x.key === currentSection.value)
  return t ? t.label : ''
})

const switchCategory = (key) => {
  if (currentCategory.value === key) return
  currentCategory.value = key
  reloadList()
}
const switchSection = (key) => {
  if (currentSection.value === key) return
  currentSection.value = key
  reloadList()
}
const toggleSort = () => {
  sortBy.value = sortBy.value === 'new' ? 'hot' : 'new'
  reloadList()
}
const onSearchSubmit = () => {
  clearTimeout(searchTimer)
  debouncedQ.value = searchQuery.value.trim()
  reloadList()
}
const clearSearch = () => {
  searchQuery.value = ''
  clearTimeout(searchTimer)
  debouncedQ.value = ''
  reloadList()
}

const currentId = ref(0)
const canUpload = ref(false)
const authorName = ref('')
const userName = ref('')
const userAvatar = ref('')
const showEditor = ref(false)
const editingStyle = ref(null)
const authorNamePanel = ref(true)
const redeemCode = ref('')
const redeeming = ref(false)
const saving = ref(false)
const savingAuthor = ref(false)
const loading = ref(false)
const communityStats = ref({ totalPublic: 0, totalPrivate: 0 })
const activeAnnouncements = ref([])
const allAnnouncements = ref([])
const showAllAnnouncements = ref(false)
const showAnnouncementModal = ref(false)

const route = useRoute()

const { show: showToast } = useToast()

const myStylesCount = computed(() => counts.value.mine || 0)
const publicStylesCount = computed(() => counts.value.myPublic || 0)
const privateStylesCount = computed(() => counts.value.myPrivate || 0)
const importedStylesCount = computed(() => counts.value.imported || 0)
const favoritesCount = computed(() => counts.value.favorites || 0)
const totalUses = computed(() => counts.value.totalUses || 0)
const currentBubbleName = computed(() => {
  const s = styles.value.find(s => s.id === currentId.value)
  if (s) return s.name
  if (currentBubbleMeta.value && currentBubbleMeta.value.id === currentId.value) {
    return currentBubbleMeta.value.name
  }
  return currentId.value ? '已选气泡' : '未选择'
})

const listContextKey = () =>
  `${currentSection.value}|${sortBy.value}|${debouncedQ.value || ''}|${currentCategory.value || ''}`

const clearPrefetch = () => {
  prefetchCache = null
  prefetchInFlight = null
}

const fetchPage = async (pageNum) => {
  const seq = ++loadSeq
  const data = await api.listBubbles({
    section: currentSection.value,
    page: pageNum,
    size: pageSize,
    sort: sortBy.value,
    q: debouncedQ.value || undefined,
    category: currentCategory.value || undefined,
  })
  if (seq !== loadSeq) return null
  return data
}

const applyMeta = (data, { preserveCurrent = false } = {}) => {
  if (!data) return
  canUpload.value = !!data.canUpload
  authorName.value = data.authorName || ''
  userName.value = (getUser() && getUser().username) || ''
  userAvatar.value = (getUser() && getUser().avatarUrl) || ''
  if (data.counts) counts.value = { ...counts.value, ...data.counts }
  if (!preserveCurrent) {
    if (data.style != null) currentId.value = data.style || 0
    if (data.currentBubble) currentBubbleMeta.value = data.currentBubble
  }
  listTotal.value = data.total || 0
  hasMore.value = !!data.hasMore
  page.value = data.page || 1
}

const appendItems = (items) => {
  const seen = new Set(styles.value.map(s => s.id))
  for (const it of items || []) {
    if (!seen.has(it.id)) {
      styles.value.push(it)
      seen.add(it.id)
    }
  }
}

/** Background-fetch next page; store in prefetchCache */
const schedulePrefetch = () => {
  if (!hasMore.value || loading.value || loadingMore.value) return
  const next = page.value + 1
  const ctx = listContextKey()
  if (prefetchCache && prefetchCache.page === next && prefetchCache.ctx === ctx) return
  if (prefetchInFlight) return

  const seqAtStart = loadSeq
  const p = api.listBubbles({
    section: currentSection.value,
    page: next,
    size: pageSize,
    sort: sortBy.value,
    q: debouncedQ.value || undefined,
    category: currentCategory.value || undefined,
  }).then((data) => {
    if (seqAtStart !== loadSeq) return
    if (listContextKey() !== ctx) return
    prefetchCache = { page: next, ctx, data }
  }).catch(() => {
    /* silent — touch-bottom will retry via loadMore */
  }).finally(() => {
    if (prefetchInFlight === p) prefetchInFlight = null
  })
  prefetchInFlight = p
}

const takePrefetch = (nextPage) => {
  const ctx = listContextKey()
  if (
    prefetchCache &&
    prefetchCache.page === nextPage &&
    prefetchCache.ctx === ctx &&
    prefetchCache.data
  ) {
    const data = prefetchCache.data
    prefetchCache = null
    return data
  }
  return null
}

const reloadList = async () => {
  clearPrefetch()
  loading.value = true
  page.value = 1
  hasMore.value = false
  try {
    const data = await fetchPage(1)
    if (!data) return
    styles.value = data.items || data.styles || []
    applyMeta(data)
    schedulePrefetch()
  } catch (e) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  if (loadingMore.value || loading.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const next = page.value + 1
    let data = takePrefetch(next)
    if (!data) {
      // wait in-flight prefetch if it's for the same next page
      if (prefetchInFlight) {
        try { await prefetchInFlight } catch { /* ignore */ }
        data = takePrefetch(next)
      }
    }
    if (!data) {
      data = await fetchPage(next)
    }
    if (!data) return
    appendItems(data.items || data.styles || [])
    applyMeta(data, { preserveCurrent: true })
    schedulePrefetch()
  } catch (e) {
    showToast(e.message || '加载失败')
  } finally {
    loadingMore.value = false
  }
}

const loadStyles = reloadList

// debounced search
watch(searchQuery, (val) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    const next = (val || '').trim()
    if (next === debouncedQ.value) return
    debouncedQ.value = next
    reloadList()
  }, 300)
})

const loadCommunityCounts = async () => {
  try {
    const data = await api.communityCounts()
    communityStats.value = { totalPublic: data.totalPublic || 0, totalPrivate: data.totalPrivate || 0 }
  } catch {}
}

const loadAnnouncements = async () => {
  try {
    const [active, all] = await Promise.all([api.announcements(), api.announcementsAll()])
    const dismissed = JSON.parse(localStorage.getItem('dismissed_announcements') || '[]')
    activeAnnouncements.value = (active.announcements || []).filter(a => !dismissed.includes(a.id))
    allAnnouncements.value = all.announcements || []
    if (activeAnnouncements.value.length) {
      showAnnouncementModal.value = true
    }
  } catch {}
}

const dismissAnnouncement = (id) => {
  const dismissed = JSON.parse(localStorage.getItem('dismissed_announcements') || '[]')
  if (!dismissed.includes(id)) {
    dismissed.push(id)
    localStorage.setItem('dismissed_announcements', JSON.stringify(dismissed))
  }
  activeAnnouncements.value = activeAnnouncements.value.filter(a => a.id !== id)
}

const closeAnnouncementModal = () => {
  activeAnnouncements.value.forEach(a => dismissAnnouncement(a.id))
  showAnnouncementModal.value = false
}

const fmtDate = (iso) => {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

const handleSelect = (id) => { currentId.value = id }

const openEditor = (style = null) => {
  editingStyle.value = style
  showEditor.value = true
}
const closeEditor = () => {
  showEditor.value = false
  editingStyle.value = null
}
const handleEdit = (style) => openEditor(style)

const handleEditorSubmit = async (data) => {
  const payload = {
    name: data.name, desc: data.desc, svg: data.svg,
    color: data.color, textColor: data.textColor, public: !!data.public,
    category: data.category || 'original',
  }
  try {
    if (data.id) {
      const res = await api.updateBubble(data.id, payload)
      const idx = styles.value.findIndex(s => s.id === data.id)
      if (idx >= 0 && res.style) styles.value[idx] = res.style
      showToast(data.public ? '已保存，所有使用者将同步更新' : '已保存，凭分享码使用者将更新')
    } else {
      const res = await api.createBubble(payload)
      if (res.style) {
        if (currentSection.value === 'mine') styles.value.unshift(res.style)
        counts.value.mine = (counts.value.mine || 0) + 1
        if (res.style.public) counts.value.myPublic = (counts.value.myPublic || 0) + 1
        else counts.value.myPrivate = (counts.value.myPrivate || 0) + 1
      }
      showToast('已创建')
    }
    closeEditor()
  } catch (e) {
    showToast(e.message || '保存失败')
  }
}

const onAvatarChange = async (e) => {
  const file = e.target?.files?.[0]
  if (!file) return
  e.target.value = ''
  try {
    const data = await api.uploadAvatar(file)
    if (data.avatarUrl) {
      userAvatar.value = data.avatarUrl
      await refreshUser()
    }
    showToast('头像已更新')
  } catch (err) {
    showToast(err.message || '上传失败')
  }
}

const handleDelete = async (style) => {
  const extra = style.uses > 0 ? `<br>当前有 ${style.uses} 人正在使用它，删除后他们的气泡会回退为默认样式。` : ''
  try {
    await ElMessageBox.confirm(
      `确定删除这个气泡样式？${extra}`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning', dangerouslyUseHTMLString: true }
    )
  } catch { return }
  try {
    await api.deleteBubble(style.id)
    styles.value = styles.value.filter(s => s.id !== style.id)
    listTotal.value = Math.max(0, listTotal.value - 1)
    if (style.mine) {
      counts.value.mine = Math.max(0, (counts.value.mine || 0) - 1)
      if (style.public) counts.value.myPublic = Math.max(0, (counts.value.myPublic || 0) - 1)
      else counts.value.myPrivate = Math.max(0, (counts.value.myPrivate || 0) - 1)
    }
    if (currentId.value === style.id) {
      currentId.value = styles.value.length ? styles.value[0].id : (currentBubbleMeta.value?.id || 0)
    }
    showToast('已删除')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

const handleShare = async (style) => {
  try {
    const data = await api.genShare(style.id)
    const s = styles.value.find(s => s.id === style.id)
    if (s && data.shareCode) s.shareCode = data.shareCode
    await ElMessageBox.alert(
      `<div style="text-align:center">
        <p style="margin-bottom:12px;color:var(--el-text-color-regular)">分享码已生成，复制下方代码分享给他人</p>
        <code style="display:inline-block;padding:12px 24px;background:var(--el-fill-color-light);border-radius:8px;font-size:22px;font-weight:700;letter-spacing:6px;color:var(--el-color-primary);user-select:all">${data.shareCode}</code>
        <p style="margin-top:12px;font-size:12px;color:var(--el-text-color-secondary)">对方可在"输入分享码使用"中粘贴使用</p>
      </div>`,
      '分享码',
      { dangerouslyUseHTMLString: true, confirmButtonText: '关闭', center: true }
    )
  } catch (e) {
    showToast(e.message || '生成失败')
  }
}

const handleCopyShare = async (code) => {
  if (!code) {
    showToast('分享码为空，请先生成')
    return
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(code)
    } else {
      const ta = document.createElement('textarea')
      ta.value = code
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    ElNotification({
      title: '分享码已复制',
      message: `<div style="text-align:center;padding:8px 0;">
        <code style="display:inline-block;padding:8px 20px;background:var(--el-fill-color-light);border-radius:6px;font-size:20px;font-weight:700;letter-spacing:4px;color:var(--el-color-primary);user-select:all">${code}</code>
      </div>`,
      type: 'success',
      duration: 5000,
      dangerouslyUseHTMLString: true,
    })
  } catch {
    showToast('复制失败，请手动复制')
  }
}

const handleTogglePublic = async (id, isPublic) => {
  // 乐观更新：先改界面，再发请求
  const s = styles.value.find(s => s.id === id)
  const prevPublic = s ? s.public : false
  if (s) s.public = isPublic
  try {
    await api.setVisibility(id, isPublic)
    // 成功：界面已是最新，无需再改
    showToast(isPublic ? '已设为公开' : '已设为私有')
  } catch (e) {
    // 失败：回滚到之前的值
    if (s) s.public = prevPublic
    showToast(e.message || '操作失败')
    await loadStyles()
  }
}

const handleToggleFavorite = async (id, favorite) => {
  const s = styles.value.find(s => s.id === id)
  const prevFav = s ? s.favorited : false
  if (s) s.favorited = favorite
  if (favorite) counts.value.favorites = (counts.value.favorites || 0) + 1
  else counts.value.favorites = Math.max(0, (counts.value.favorites || 0) - 1)
  if (!favorite && currentSection.value === 'favorites') {
    styles.value = styles.value.filter(x => x.id !== id)
    listTotal.value = Math.max(0, listTotal.value - 1)
  }
  try {
    await api.setFavorite(id, favorite)
    showToast(favorite ? '已收藏' : '已取消收藏')
  } catch (e) {
    if (s) s.favorited = prevFav
    if (favorite) counts.value.favorites = Math.max(0, (counts.value.favorites || 0) - 1)
    else counts.value.favorites = (counts.value.favorites || 0) + 1
    showToast(e.message || '操作失败')
  }
}

const handleRemoveImport = async (style) => {
  try {
    await ElMessageBox.confirm(`确定移除导入的气泡「${style.name}」？`, '移除导入', {
      confirmButtonText: '确定移除', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try {
    await api.removeImported(style.id)
    styles.value = styles.value.filter(s => s.id !== style.id)
    listTotal.value = Math.max(0, listTotal.value - 1)
    counts.value.imported = Math.max(0, (counts.value.imported || 0) - 1)
    if (currentId.value === style.id) {
      currentId.value = styles.value.length ? styles.value[0].id : 0
    }
    showToast('已移除')
  } catch (e) {
    showToast(e.message || '移除失败')
  }
}

const saveAuthorName = async () => {
  savingAuthor.value = true
  const prevName = authorName.value
  try {
    const res = await api.setAuthorName(authorName.value.trim())
    const newName = res.authorName || ''
    authorName.value = newName
    // 更新所有自己的气泡的 author 字段
    styles.value.forEach(s => {
      if (s.mine) s.author = newName || '匿名书友'
    })
    showToast(newName ? `署名已保存：${newName}` : '已清空署名')
  } catch (e) {
    authorName.value = prevName
    showToast(e.message || '保存失败')
  } finally {
    savingAuthor.value = false
  }
}

const saveCurrentStyle = async () => {
  if (!currentId.value) return
  saving.value = true
  try {
    const data = await api.setCurrent(currentId.value)
    // 更新新选中气泡的 uses 计数
    const s = styles.value.find(s => s.id === currentId.value)
    if (s && data.uses !== undefined) s.uses = data.uses
    // 如果有前一个气泡，同时更新它的 uses 计数
    if (data.prevId && data.prevUses !== undefined) {
      const p = styles.value.find(s => s.id === data.prevId)
      if (p) p.uses = data.prevUses
    }
    showToast('已保存，回到阅读翻页即生效')
    // 无需 loadStyles — currentId 已是用户所选，界面立即响应
  } catch (e) {
    showToast(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const redeem = async () => {
  const code = redeemCode.value.trim()
  if (!code) { showToast('请输入分享码'); return }
  redeeming.value = true
  try {
    const res = await api.redeem(code)
    if (res.style) {
      counts.value.imported = (counts.value.imported || 0) + 1
      if (currentSection.value === 'imported') {
        const idx = styles.value.findIndex(s => s.id === res.style.id)
        if (idx >= 0) styles.value[idx] = res.style
        else styles.value.unshift(res.style)
      }
    }
    ElNotification({ title: '导入成功', message: `已添加「${res.name || ''}」到你的气泡列表`, type: 'success', duration: 4000 })
    redeemCode.value = ''
  } catch (e) {
    ElNotification({ title: '导入失败', message: e.message || '分享码无效', type: 'error', duration: 4000 })
  } finally {
    redeeming.value = false
  }
}

const VALID_SECTIONS = ['public', 'mine', 'favorites', 'imported']

const scrollToBubble = async (id) => {
  await nextTick()
  // layout may need a frame after list swap
  await new Promise(r => requestAnimationFrame(() => r()))
  const el = document.querySelector(`[data-bubble-id="${id}"]`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

/** Profile / deep-link: ?select=<id>&section=mine|favorites|imported|public */
const applySelectQuery = async () => {
  const selectId = Number(route.query.select)
  if (!selectId) return

  const sec = String(route.query.section || '')
  if (sec && VALID_SECTIONS.includes(sec) && sec !== currentSection.value) {
    currentSection.value = sec
    // clear category/search noise so target is more likely on page 1
    // keep user category if they set it; only force reload for section switch
    await reloadList()
  } else if (!styles.value.some(s => s.id === selectId)) {
    // already on section but not in first page — try loading more until found
    let guard = 0
    while (hasMore.value && !styles.value.some(s => s.id === selectId) && guard < 20) {
      guard++
      await loadMore()
    }
  }

  currentId.value = selectId
  const found = styles.value.find(s => s.id === selectId)
  if (found) currentBubbleMeta.value = found
  await scrollToBubble(selectId)
}

onMounted(async () => {
  // honor section from query before first fetch
  const sec = String(route.query.section || '')
  if (sec && VALID_SECTIONS.includes(sec)) {
    currentSection.value = sec
  }
  await loadStyles()
  loadCommunityCounts()
  loadAnnouncements()
  await applySelectQuery()
})

watch(
  () => `${route.query.select || ''}:${route.query.section || ''}`,
  async (key, prev) => {
    if (!route.query.select || key === prev) return
    await applySelectQuery()
  }
)
</script>

<style>
.announcement-dialog {
  border-radius: 20px;
  --el-dialog-bg-color: rgb(var(--color-surface));
}
.announcement-dialog .el-dialog__header {
  display: none;
}
.announcement-dialog .el-dialog__body {
  padding: 32px 32px 28px;
}
@media (max-width: 640px) {
  .announcement-dialog .el-dialog__body {
    padding: 24px 16px 24px;
  }
}
@media (max-width: 640px) {
  .announcement-dialog {
    border-radius: 16px;
    width: calc(100% - 32px) !important;
    max-width: calc(100% - 32px) !important;
    margin: 16px auto !important;
  }
}
</style>
