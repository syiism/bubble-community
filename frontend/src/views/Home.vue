<template>
  <div class="pt-20 pb-32">
    <div class="max-w-4xl mx-auto px-6">
      <div class="mb-12 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-4">段评气泡社区</h1>
        <p class="text-sm text-muted leading-relaxed">
          选择喜欢的气泡外观，保存后回到阅读界面翻页即可生效。你也可以自己添加/编辑气泡，生成分享码给别人用。
        </p>
      </div>

      <!-- 吸附式搜索栏 -->
      <div class="sticky top-16 z-40 -mx-6 px-6 mb-6"
           style="background: rgba(255,255,255,0.4); backdrop-filter: blur(12px);">
        <div class="max-w-4xl mx-auto">
          <div class="relative flex items-center py-2.5">
            <svg class="absolute left-0 w-4 h-4 text-muted pointer-events-none ml-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input v-model="searchQuery" type="text" placeholder="搜索气泡名称 / 作者..."
                   class="w-full pl-8 pr-20 py-2 bg-transparent border-0 text-sm text-ink placeholder:text-muted
                          focus:outline-none focus:ring-0" />
            <button v-if="searchQuery"
                    class="absolute right-0 px-3 py-1.5 text-xs font-medium text-muted hover:text-ink bg-white/80 border border-border rounded-lg transition-colors"
                    @click="searchQuery = ''">
              清空
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading && !styles.length" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div class="lg:col-span-2 space-y-4">
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

          <div class="lg:col-span-1">
            <div class="bg-surface border border-border rounded-xl p-5 sticky top-24 scroll-animate scroll-animate-delay-3">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center overflow-hidden">
                  <img v-if="userAvatar" :src="userAvatar" :alt="userName" class="w-full h-full object-cover" />
                  <svg v-else class="w-6 h-6 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
                <div>
                  <div class="text-sm font-medium text-ink">{{ userName }}</div>
                  <div class="text-xs text-muted">{{ authorName || '匿名书友' }}</div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="bg-canvas rounded-lg p-3 text-center">
                  <div class="text-lg font-medium text-ink">{{ myStylesCount }}</div>
                  <div class="text-xs text-muted">我的气泡</div>
                </div>
                <div class="bg-canvas rounded-lg p-3 text-center">
                  <div class="text-lg font-medium text-ink">{{ publicStylesCount }}</div>
                  <div class="text-xs text-muted">公开分享</div>
                </div>
                <div class="bg-canvas rounded-lg p-3 text-center">
                  <div class="text-lg font-medium text-ink">{{ importedStylesCount }}</div>
                  <div class="text-xs text-muted">已导入</div>
                </div>
                <div class="bg-canvas rounded-lg p-3 text-center">
                  <div class="text-lg font-medium text-ink">{{ favoritesCount }}</div>
                  <div class="text-xs text-muted">收藏</div>
                </div>
                <div class="bg-canvas rounded-lg p-3 text-center">
                  <div class="text-lg font-medium text-ink">{{ totalUses }}</div>
                  <div class="text-xs text-muted">被使用</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <BubbleList
          :styles="filteredStyles"
          :current-id="currentId"
          @select="handleSelect"
          @edit="handleEdit"
          @delete="handleDelete"
          @share="handleShare"
          @copy-share="handleCopyShare"
          @toggle-public="handleTogglePublic"
          @toggle-favorite="handleToggleFavorite"
        />
      </template>
    </div>
  </div>

  <div
    v-if="filteredStyles.length"
    class="fixed bottom-0 left-0 right-0 z-30 bg-surface/95 backdrop-blur border-t border-border"
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
    v-if="showEditor"
    :style="editingStyle"
    @close="closeEditor"
    @submit="handleEditorSubmit"
    @toast="showToast"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BubbleList from '@/components/BubbleList.vue'
import Editor from '@/components/Editor.vue'
import { api } from '@/api'
import { getUser } from '@/stores/auth'

const styles = ref([])
const searchQuery = ref('')
const filteredStyles = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return styles.value
  return styles.value.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.author.toLowerCase().includes(q)
  )
})
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

const props = defineProps({
  toastRef: { type: Object, default: null }
})

const myStylesCount = computed(() => styles.value.filter(s => s.mine).length)
const publicStylesCount = computed(() => styles.value.filter(s => s.mine && s.public).length)
const importedStylesCount = computed(() => styles.value.filter(s => s.imported).length)
const favoritesCount = computed(() => styles.value.filter(s => s.favorited).length)
const totalUses = computed(() => styles.value.filter(s => s.mine).reduce((sum, s) => sum + (s.uses || 0), 0))
const currentBubbleName = computed(() => {
  const s = styles.value.find(s => s.id === currentId.value)
  return s ? s.name : '未选择'
})

const showToast = (msg) => {
  if (props.toastRef) props.toastRef.show(msg)
  else alert(msg)
}

const loadStyles = async () => {
  loading.value = true
  try {
    const data = await api.listBubbles()
    styles.value = data.styles || []
    canUpload.value = !!data.canUpload
    authorName.value = data.authorName || ''
    userName.value = (getUser() && getUser().username) || ''
    userAvatar.value = (getUser() && getUser().avatarUrl) || ''
    currentId.value = data.style || (styles.value[0] ? styles.value[0].id : 0)
    const exists = styles.value.some(s => s.id === currentId.value)
    if (!exists && styles.value.length) currentId.value = styles.value[0].id
  } catch (e) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
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
  }
  try {
    if (data.id) {
      const res = await api.updateBubble(data.id, payload)
      const idx = styles.value.findIndex(s => s.id === data.id)
      if (idx >= 0 && res.style) styles.value[idx] = res.style
      showToast(data.public ? '已保存，所有使用者将同步更新' : '已保存，凭分享码使用者将更新')
    } else {
      const res = await api.createBubble(payload)
      if (res.style) styles.value.unshift(res.style)
      showToast('已创建')
    }
    closeEditor()
  } catch (e) {
    showToast(e.message || '保存失败')
  }
}

const handleDelete = async (style) => {
  const extra = style.uses > 0 ? `\n当前有 ${style.uses} 人正在使用它，删除后他们的气泡会回退为默认样式。` : ''
  if (!confirm(`确定删除这个气泡样式？${extra}`)) return
  try {
    await api.deleteBubble(style.id)
    styles.value = styles.value.filter(s => s.id !== style.id)
    if (currentId.value === style.id) {
      currentId.value = styles.value.length ? styles.value[0].id : 0
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
    showToast('分享码已生成')
  } catch (e) {
    showToast(e.message || '生成失败')
  }
}

const handleCopyShare = (code) => {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(code).then(() => showToast('已复制分享码'), () => showToast('复制失败，请手动复制'))
  } else {
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
  // 乐观更新：先改界面，再发请求
  const s = styles.value.find(s => s.id === id)
  const prevFav = s ? s.favorited : false
  if (s) s.favorited = favorite
  try {
    await api.setFavorite(id, favorite)
    // 成功：界面已是最新，无需再改
    showToast(favorite ? '已收藏' : '已取消收藏')
  } catch (e) {
    // 失败：回滚到之前的值
    if (s) s.favorited = prevFav
    showToast(e.message || '操作失败')
    await loadStyles()
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
      // 替换已有的或追加新气泡
      const idx = styles.value.findIndex(s => s.id === res.style.id)
      if (idx >= 0) {
        styles.value[idx] = res.style
      } else {
        styles.value.unshift(res.style)
      }
    }
    showToast(`已添加：${res.name || ''}`)
    redeemCode.value = ''
  } catch (e) {
    showToast(e.message || '分享码无效')
  } finally {
    redeeming.value = false
  }
}

onMounted(() => {
  loadStyles()
})
</script>
