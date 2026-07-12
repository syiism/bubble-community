<template>
  <div class="pb-20" style="padding-top: calc(5rem + env(safe-area-inset-top, 0px))">
    <div class="max-w-4xl mx-auto px-6">
      <div class="scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-4">个人中心</h1>
        <p class="text-sm text-muted">管理你的气泡和个人设置</p>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div class="md:col-span-1 space-y-6">
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-1">
            <div class="flex flex-col items-center text-center">
              <div class="relative w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mb-4 overflow-hidden cursor-pointer"
                   @click="$refs.avatarInput.click()">
                <img v-if="user.avatarUrl" :src="user.avatarUrl" :alt="user.username" class="w-full h-full object-cover" />
                <svg v-else class="w-10 h-10 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <!-- 右下角笔图标 -->
                <div class="absolute bottom-[0.3rem] right-[0.3rem] w-5 h-5 bg-surface rounded-full shadow-sm flex items-center justify-center">
                  <svg class="w-3.5 h-3.5 text-ink" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                    <path d="M16.84 2.73c-.39 0-.77.15-1.07.44l-2.12 2.12 5.3 5.3 2.12-2.12c.6-.6.6-1.56 0-2.16l-3.18-3.18c-.28-.28-.66-.44-1.05-.44M2 18.08V22h3.92l11.3-11.3-5.3-5.3L2 18.08Z"/>
                  </svg>
                </div>
                <input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="onAvatarChange" />
              </div>
              <h2 class="text-xl font-medium text-ink mb-1">{{ user.username }}</h2>
              <p class="text-sm text-muted mb-4">
                {{ user.authorName ? `署名：${user.authorName}` : '匿名书友' }}
              </p>
              <div class="w-full h-px bg-border mb-4"></div>
              <div class="grid grid-cols-3 gap-3 w-full">
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.created }}</div>
                  <div class="text-xs text-muted">创建</div>
                </div>
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.public }}</div>
                  <div class="text-xs text-muted">公开</div>
                </div>
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.private }}</div>
                  <div class="text-xs text-muted">私有</div>
                </div>
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.imported }}</div>
                  <div class="text-xs text-muted">导入</div>
                </div>
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.favorites }}</div>
                  <div class="text-xs text-muted">收藏</div>
                </div>
                <div class="bg-canvas rounded-xl p-3 text-center">
                  <div class="text-xl font-medium text-ink">{{ stats.usedBy }}</div>
                  <div class="text-xs text-muted">被使用</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-2">
            <h3 class="text-sm font-medium text-ink mb-4">快捷操作</h3>
            <div class="space-y-3">
              <button 
                class="w-full flex items-center gap-3 px-4 py-3 bg-canvas rounded-xl text-sm text-ink hover:bg-border/50 transition-colors"
                @click="openProfileEditor()"
              >
                <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                添加新气泡
              </button>
              <button
                class="w-full flex items-center gap-3 px-4 py-3 bg-canvas rounded-xl text-sm text-ink hover:bg-border/50 transition-colors"
                @click="showSaved = !showSaved"
              >
                <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                我的收藏
              </button>
              <button
                class="w-full flex items-center gap-3 px-4 py-3 bg-canvas rounded-xl text-sm text-ink hover:bg-border/50 transition-colors"
                @click="showImported = !showImported"
              >
                <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                我的导入
              </button>
              <button
                class="w-full flex items-center gap-3 px-4 py-3 bg-canvas rounded-xl text-sm text-ink hover:bg-border/50 transition-colors"
                @click="showStats = !showStats"
              >
                <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="7" height="7"></rect>
                  <rect x="14" y="3" width="7" height="7"></rect>
                  <rect x="14" y="14" width="7" height="7"></rect>
                  <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
                数据统计
              </button>
            </div>
          </div>
        </div>
        
        <div class="md:col-span-2 space-y-6">
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-3">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-medium text-ink">我创建的气泡</h2>
              <button 
                class="text-sm font-medium text-accent hover:text-accent/80 transition-colors"
                @click="$router.push('/')"
              >
                查看全部
              </button>
            </div>
            
            <div v-if="myStyles.length" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div 
                v-for="style in myStyles" 
                :key="style.id"
                class="bg-canvas rounded-xl p-4 cursor-pointer hover:shadow-subtle transition-all"
                @click="$router.push('/')"
              >
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-surface rounded-lg flex items-center justify-center border border-border">
                    <span v-html="getPreview(style)"></span>
                  </div>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-ink">{{ style.name }}</div>
                    <div class="text-xs text-muted">{{ style.desc }}</div>
                  </div>
                  <div class="text-xs text-muted">
                    {{ style.uses > 0 ? `${style.uses} 人在用` : '暂无使用' }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-sm text-muted">
              还没有创建气泡，快去创建一个吧
            </div>
          </div>
          
          <div v-if="showSaved" class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">我的收藏</h2>
            <div v-if="favoriteStyles.length" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                v-for="style in favoriteStyles"
                :key="style.id"
                class="bg-canvas rounded-xl p-4 cursor-pointer hover:shadow-subtle transition-all"
                @click="$router.push('/')"
              >
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-surface rounded-lg flex items-center justify-center border border-border">
                    <span v-html="getPreview(style)"></span>
                  </div>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-ink">{{ style.name }}</div>
                    <div class="text-xs text-muted">{{ style.desc || (style.official ? '官方样式' : '社区样式') }}</div>
                  </div>
                  <div v-if="style.uses > 0" class="text-xs text-muted">
                    {{ style.uses }} 人在用
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-sm text-muted">
              暂无收藏，去首页收藏喜欢的气泡吧
            </div>
          </div>

          <div v-if="showImported" class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">我的导入</h2>
            <div v-if="importedStyles.length" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                v-for="style in importedStyles"
                :key="style.id"
                class="bg-canvas rounded-xl p-4 cursor-pointer hover:shadow-subtle transition-all"
                @click="$router.push('/')"
              >
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-surface rounded-lg flex items-center justify-center border border-border">
                    <span v-html="getPreview(style)"></span>
                  </div>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-ink">{{ style.name }}</div>
                    <div class="text-xs text-muted">{{ style.desc || (style.official ? '官方样式' : '社区样式') }}</div>
                  </div>
                  <div v-if="style.uses > 0" class="text-xs text-muted">
                    {{ style.uses }} 人在用
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-sm text-muted">
              暂无导入，去首页通过分享码导入气泡吧
            </div>
          </div>

          <div v-if="showStats" class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">数据统计</h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">创建气泡</div>
                <div class="text-3xl font-medium text-ink">{{ stats.created }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">公开</div>
                <div class="text-3xl font-medium text-ink">{{ stats.public }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">私有</div>
                <div class="text-3xl font-medium text-ink">{{ stats.private }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">导入气泡</div>
                <div class="text-3xl font-medium text-ink">{{ stats.imported }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">收藏</div>
                <div class="text-3xl font-medium text-ink">{{ stats.favorites }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">被使用</div>
                <div class="text-3xl font-medium text-ink">{{ stats.usedBy }}</div>
              </div>
            </div>
          </div>
          
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-4">
            <h2 class="text-lg font-medium text-ink mb-6">账户设置</h2>

            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-ink mb-2">登录昵称</label>
                <div class="flex gap-3">
                  <input
                    v-model="usernameForm"
                    type="text"
                    maxlength="32"
                    placeholder="输入新用户名"
                    class="flex-1 px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                  />
                  <button
                    :disabled="!usernameForm.trim() || usernameForm.trim() === user.username || usernameSaving"
                    class="px-5 py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="saveUsername"
                  >
                    {{ usernameSaving ? '保存中...' : '保存' }}
                  </button>
                </div>
                <p class="text-xs text-muted mt-2">
                  修改登录用户名，不可与他人重复。
                </p>
              </div>

              <div>
                <label class="block text-sm font-medium text-ink mb-2">分享署名</label>
                <div class="flex gap-3">
                  <input
                    v-model="authorName"
                    type="text"
                    maxlength="16"
                    placeholder="如 隔壁老王（留空=匿名书友）"
                    class="flex-1 px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                  />
                  <button
                    :disabled="saving"
                    class="px-5 py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    @click="saveAuthorName"
                  >
                    {{ saving ? '保存中...' : '保存' }}
                  </button>
                </div>
                <p class="text-xs text-muted mt-2">
                  这个名字只在你公开或用分享码分享出去的气泡上，给别人看到（显示为"by 署名"）。不影响你的登录账号，可随时修改，不可与他人重复。
                </p>
              </div>
            </div>
          </div>

          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">密码设置</h2>
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-ink mb-2">新密码</label>
                <input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="至少 6 个字符"
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-ink mb-2">确认新密码</label>
                <input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="再次输入新密码"
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <button
                :disabled="!canSavePassword || passwordSaving"
                class="w-full py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                @click="savePassword"
              >
                {{ passwordSaving ? '保存中...' : '设置密码' }}
              </button>
            </div>
          </div>

          <!-- 设备管理 -->
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">登录设备管理</h2>

            <div v-if="loadingSessions" class="text-sm text-muted text-center py-4">加载中...</div>

            <div v-else-if="sessions.length === 0" class="text-sm text-muted text-center py-4">
              暂无活跃设备
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="session in sessions"
                :key="session.id"
                class="flex items-center justify-between bg-canvas rounded-xl p-4"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <svg class="w-5 h-5 flex-shrink-0" :class="session.is_current ? 'text-accent' : 'text-muted'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <template v-if="session.device_info && session.device_info.includes('Mobile')">
                      <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>
                    </template>
                    <template v-else-if="session.device_info && (session.device_info.includes('iPad') || session.device_info.includes('Tablet'))">
                      <rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>
                    </template>
                    <template v-else>
                      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
                    </template>
                  </svg>
                  <div class="min-w-0">
                    <div class="text-sm font-medium text-ink flex items-center gap-2 truncate">
                      {{ parseDevice(session.device_info) }}
                      <span v-if="session.is_current" class="px-2 py-0.5 text-xs font-medium text-accent bg-pale-yellow/60 rounded-full flex-shrink-0">当前设备</span>
                    </div>
                    <div class="text-xs text-muted mt-0.5">
                      {{ session.ip_address || '未知 IP' }} · {{ fmtRelative(session.last_seen_at) }}
                    </div>
                  </div>
                </div>
                <button
                  v-if="!session.is_current"
                  class="px-3 py-1.5 text-xs font-medium text-paleText-red bg-pale-red border border-transparent rounded-lg hover:bg-red-50 transition-colors flex-shrink-0 ml-3"
                  @click="revokeSession(session.id)"
                >
                  退出
                </button>
              </div>
            </div>

            <button
              v-if="sessions.length > 1"
              class="mt-6 w-full py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors"
              @click="logoutAllDevices"
            >
              退出所有其他设备
            </button>
          </div>
        </div>
      </div>
    </div>

    <Editor v-model="showProfileEditor"
            :style="editingProfileStyle"
            @close="closeProfileEditor"
            @submit="handleProfileEditorSubmit"
            @toast="toast.show"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api } from '@/api'
import Editor from '@/components/Editor.vue'
import { getUser, refreshUser } from '@/stores/auth'
import { svgToImg } from '@/utils/svgHelper'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const router = useRouter()

const user = ref(getUser() || { username: '', authorName: '' })
const authorName = ref('')
const usernameForm = ref('')
const usernameSaving = ref(false)
const saving = ref(false)
const showSaved = ref(false)
const showImported = ref(false)
const showStats = ref(false)
const styles = ref([])
const loading = ref(false)

// ===== 快捷创建气泡 =====
const showProfileEditor = ref(false)
const editingProfileStyle = ref(null)

const openProfileEditor = () => {
  editingProfileStyle.value = null
  showProfileEditor.value = true
}
const closeProfileEditor = () => {
  showProfileEditor.value = false
  editingProfileStyle.value = null
}
const handleProfileEditorSubmit = async (data) => {
  const payload = {
    name: data.name, desc: data.desc, svg: data.svg,
    color: data.color, textColor: data.textColor, public: !!data.public,
  }
  try {
    await api.createBubble(payload)
    closeProfileEditor()
    router.push('/')
  } catch (e) {
    toast.show(e.message || '创建失败')
  }
}

// 密码设置
const passwordForm = ref({ newPassword: '', confirmPassword: '' })
const passwordSaving = ref(false)
const canSavePassword = computed(() => {
  const np = passwordForm.value.newPassword
  const cp = passwordForm.value.confirmPassword
  return np.length >= 6 && np === cp
})

const savePassword = async () => {
  passwordSaving.value = true
  try {
    await api.forgetPassword({
      new_password: passwordForm.value.newPassword,
      confirm_password: passwordForm.value.confirmPassword,
    })
    passwordForm.value = { newPassword: '', confirmPassword: '' }
    toast.show('密码设置成功')
  } catch (e) {
    toast.show(e.message || '设置失败')
  } finally {
    passwordSaving.value = false
  }
}

const stats = computed(() => ({
  created: styles.value.filter(s => s.mine).length,
  public: styles.value.filter(s => s.mine && s.public).length,
  private: styles.value.filter(s => s.mine && !s.public).length,
  imported: styles.value.filter(s => s.imported).length,
  favorites: styles.value.filter(s => s.favorited).length,
  usedBy: styles.value.filter(s => s.mine).reduce((sum, s) => sum + (s.uses || 0), 0)
}))

const myStyles = computed(() => styles.value.filter(s => s.mine))
const favoriteStyles = computed(() => styles.value.filter(s => s.favorited))
const importedStyles = computed(() => styles.value.filter(s => s.imported))

const getPreview = (style) => {
  return svgToImg(style.svg, 'h-8 w-auto', style.color, style.textColor)
}

const onAvatarChange = async (e) => {
  const file = e.target?.files?.[0]
  if (!file) return
  e.target.value = ''
  try {
    const data = await api.uploadAvatar(file)
    if (data.avatarUrl) {
      user.value = { ...user.value, avatarUrl: data.avatarUrl }
      await refreshUser()
    }
  } catch (err) {
    toast.show(err.message || '上传失败')
  }
}

const saveAuthorName = async () => {
  saving.value = true
  try {
    const res = await api.setAuthorName(authorName.value.trim())
    authorName.value = res.authorName || ''
    user.value = { ...user.value, authorName: res.authorName || '' }
    toast.show('设置已保存')
  } catch (e) {
    toast.show(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const saveUsername = async () => {
  const name = usernameForm.value.trim()
  if (!name || name === user.value.username) return
  usernameSaving.value = true
  try {
    const res = await api.setUsername(name)
    user.value = { ...user.value, username: res.username }
    usernameForm.value = res.username
    toast.show('用户名修改成功')
  } catch (e) {
    toast.show(e.message || '修改失败')
  } finally {
    usernameSaving.value = false
  }
}

// 设备管理
const sessions = ref([])
const loadingSessions = ref(false)

const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const data = await api.listSessions()
    sessions.value = data.sessions || []
  } catch (e) {
    // 设备管理是辅助功能，静默失败
    sessions.value = []
  } finally {
    loadingSessions.value = false
  }
}

const revokeSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm('确定要退出该设备？', '退出设备', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try {
    await api.revokeSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
  } catch (e) {
    toast.show(e.message || '操作失败')
  }
}

const logoutAllDevices = async () => {
  try {
    await ElMessageBox.confirm('确定要退出所有其他设备？当前设备不受影响。', '退出所有设备', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  try {
    await api.logoutAll()
    await loadSessions()
  } catch (e) {
    toast.show(e.message || '操作失败')
  }
}

const parseDevice = (ua) => {
  if (!ua) return '未知设备'
  if (ua.includes('iPhone')) return 'iPhone'
  if (ua.includes('iPad')) return 'iPad'
  if (ua.includes('Android')) return 'Android 设备'
  if (ua.includes('Windows')) return 'Windows 电脑'
  if (ua.includes('Mac OS') || ua.includes('Macintosh')) return 'Mac 电脑'
  if (ua.includes('Linux')) return 'Linux 设备'
  return '其他设备'
}

const fmtRelative = (iso) => {
  if (!iso) return '未知'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  return `${Math.floor(hours / 24)} 天前`
}

onMounted(async () => {
  loading.value = true
  try {
    await refreshUser()
    user.value = getUser() || user.value
    authorName.value = user.value.authorName || ''
    usernameForm.value = user.value.username || ''
    const data = await api.listBubbles()
    styles.value = data.styles || []
    loadSessions()
  } catch (e) {
    toast.show(e.message || '加载失败')
  } finally {
    loading.value = false
  }
})
</script>
