<template>
  <div class="pt-20 pb-20">
    <div class="max-w-4xl mx-auto px-6">
      <div class="scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-4">个人中心</h1>
        <p class="text-sm text-muted">管理你的气泡和个人设置</p>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-12">
        <div class="lg:col-span-1 space-y-6">
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-1">
            <div class="flex flex-col items-center text-center">
              <div class="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mb-4 overflow-hidden">
                <img v-if="user.avatarUrl" :src="user.avatarUrl" :alt="user.username" class="w-full h-full object-cover" />
                <svg v-else class="w-10 h-10 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <h2 class="text-xl font-medium text-ink mb-1">{{ user.username }}</h2>
              <p class="text-sm text-muted mb-4">
                {{ user.authorName ? `署名：${user.authorName}` : '匿名书友' }}
              </p>
              <div class="w-full h-px bg-border mb-4"></div>
              <div class="grid grid-cols-2 gap-4 w-full">
                <div class="bg-canvas rounded-xl p-4">
                  <div class="text-2xl font-medium text-ink">{{ stats.created }}</div>
                  <div class="text-xs text-muted">创建气泡</div>
                </div>
                <div class="bg-canvas rounded-xl p-4">
                  <div class="text-2xl font-medium text-ink">{{ stats.imported }}</div>
                  <div class="text-xs text-muted">导入气泡</div>
                </div>
                <div class="bg-canvas rounded-xl p-4">
                  <div class="text-2xl font-medium text-ink">{{ stats.favorites }}</div>
                  <div class="text-xs text-muted">收藏</div>
                </div>
                <div class="bg-canvas rounded-xl p-4">
                  <div class="text-2xl font-medium text-ink">{{ stats.usedBy }}</div>
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
                @click="$router.push('/')"
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
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                我的收藏
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
        
        <div class="lg:col-span-2 space-y-6">
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
          
          <div v-if="showStats" class="bg-surface border border-border rounded-2xl p-6 scroll-animate">
            <h2 class="text-lg font-medium text-ink mb-6">数据统计</h2>
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">创建气泡总数</div>
                <div class="text-3xl font-medium text-ink">{{ stats.created }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">导入气泡总数</div>
                <div class="text-3xl font-medium text-ink">{{ stats.imported }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">收藏气泡数</div>
                <div class="text-3xl font-medium text-ink">{{ stats.favorites }}</div>
              </div>
              <div class="bg-canvas rounded-xl p-4">
                <div class="text-xs text-muted mb-2">被使用次数</div>
                <div class="text-3xl font-medium text-ink">{{ stats.usedBy }}</div>
              </div>
            </div>
          </div>
          
          <div class="bg-surface border border-border rounded-2xl p-6 scroll-animate scroll-animate-delay-4">
            <h2 class="text-lg font-medium text-ink mb-6">账户设置</h2>
            
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-ink mb-2">登录昵称</label>
                <input
                  type="text"
                  :value="user.username"
                  disabled
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink disabled:opacity-50"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-ink mb-2">分享署名</label>
                <input 
                  v-model="authorName"
                  type="text" 
                  maxlength="16"
                  placeholder="如 隔壁老王（留空=匿名书友）"
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
                />
                <p class="text-xs text-muted mt-2">
                  这个名字只在你公开或用分享码分享出去的气泡上，给别人看到（显示为"by 署名"）。不影响你的登录账号，可随时修改，不可与他人重复。
                </p>
              </div>
              
              <button 
                :disabled="!authorName.trim() || saving"
                class="w-full py-3 text-sm font-medium text-white bg-ink rounded-xl hover:bg-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                @click="saveAuthorName"
              >
                {{ saving ? '保存中...' : '保存设置' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'
import { getUser, refreshUser } from '@/stores/auth'
import { svgToImg } from '@/utils/svgHelper'

const user = ref(getUser() || { username: '', authorName: '' })
const authorName = ref('')
const saving = ref(false)
const showSaved = ref(false)
const showStats = ref(false)
const styles = ref([])
const loading = ref(false)

const stats = computed(() => ({
  created: styles.value.filter(s => s.mine).length,
  imported: styles.value.filter(s => s.imported).length,
  favorites: styles.value.filter(s => s.favorited).length,
  usedBy: styles.value.filter(s => s.mine).reduce((sum, s) => sum + (s.uses || 0), 0)
}))

const myStyles = computed(() => styles.value.filter(s => s.mine))
const favoriteStyles = computed(() => styles.value.filter(s => s.favorited))

const getPreview = (style) => {
  return svgToImg(style.svg, 'h-8 w-auto', style.color, style.textColor)
}

const saveAuthorName = async () => {
  saving.value = true
  try {
    const res = await api.setAuthorName(authorName.value.trim())
    authorName.value = res.authorName || ''
    user.value = { ...user.value, authorName: res.authorName || '' }
    alert('设置已保存')
  } catch (e) {
    alert(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await refreshUser()
    user.value = getUser() || user.value
    authorName.value = user.value.authorName || ''
    const data = await api.listBubbles()
    styles.value = data.styles || []
  } catch (e) {
    alert(e.message || '加载失败')
  } finally {
    loading.value = false
  }
})
</script>
