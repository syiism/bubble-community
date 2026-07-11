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
            <input v-model="searchQuery" type="text" placeholder="搜索气泡名称 / 作者..."
                   class="w-full pl-8 pr-20 py-2.5 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted
                          transition-all duration-200
                          focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 focus:bg-surface" />
            <button v-if="searchQuery"
                    class="absolute right-0 px-3 py-1.5 text-xs font-medium text-muted hover:text-ink bg-surface/80 border border-border rounded-lg transition-colors"
                    @click="searchQuery = ''">
              清空
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading && !styles.length" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
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
          @remove-import="handleRemoveImport"
        />
      </template>
    </div>
  </div>

  <div
    v-if="filteredStyles.length"
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox, ElNotification } from 'element-plus'
import BubbleList from '@/components/BubbleList.vue'
import Editor from '@/components/Editor.vue'
import { api } from '@/api'
import { getUser, refreshUser } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

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

const { show: showToast } = useToast()

const myStylesCount = computed(() => styles.value.filter(s => s.mine).length)
const publicStylesCount = computed(() => styles.value.filter(s => s.mine && s.public).length)
const importedStylesCount = computed(() => styles.value.filter(s => s.imported).length)
const favoritesCount = computed(() => styles.value.filter(s => s.favorited).length)
const totalUses = computed(() => styles.value.filter(s => s.mine).reduce((sum, s) => sum + (s.uses || 0), 0))
const currentBubbleName = computed(() => {
  const s = styles.value.find(s => s.id === currentId.value)
  return s ? s.name : '未选择'
})

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
  // 弹窗展示分享码并自动复制
  try {
    // 先复制到剪贴板
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
    // 弹窗展示
    await ElMessageBox.alert(
      `<div style="text-align:center">
        <p style="margin-bottom:12px;color:var(--el-text-color-regular)">分享码已复制到剪贴板</p>
        <code style="display:inline-block;padding:12px 24px;background:var(--el-fill-color-light);border-radius:8px;font-size:22px;font-weight:700;letter-spacing:6px;color:var(--el-color-primary);user-select:all">${code}</code>
        <p style="margin-top:12px;font-size:12px;color:var(--el-text-color-secondary)">发送给好友即可导入你的气泡样式</p>
      </div>`,
      '复制分享码',
      { dangerouslyUseHTMLString: true, confirmButtonText: '关闭', center: true }
    )
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

const handleRemoveImport = async (style) => {
  try {
    await ElMessageBox.confirm(`确定移除导入的气泡「${style.name}」？`, '移除导入', {
      confirmButtonText: '确定移除', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try {
    await api.removeImported(style.id)
    styles.value = styles.value.filter(s => s.id !== style.id)
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
      // 替换已有的或追加新气泡
      const idx = styles.value.findIndex(s => s.id === res.style.id)
      if (idx >= 0) {
        styles.value[idx] = res.style
      } else {
        styles.value.unshift(res.style)
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

onMounted(() => {
  loadStyles()
})
</script>
