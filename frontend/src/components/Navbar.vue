<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md border-b border-border p-safe-top"
       role="navigation" aria-label="主导航">
    <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="8"/>
            <circle cx="12" cy="12" r="4"/>
          </svg>
        </div>
        <span class="text-lg font-medium text-ink">段评气泡</span>
      </router-link>

      <!-- 桌面端导航 -->
      <div class="hidden md:flex items-center gap-4">
        <template v-if="isAuthenticated">
          <a href="https://vossc.com" target="_blank" rel="noopener noreferrer"
             class="text-sm font-medium text-muted hover:text-accent transition-colors">论坛</a>
          <router-link to="/" :class="navLinkClass('home')">社区</router-link>
          <router-link to="/profile" :class="navLinkClass('profile')">{{ user?.username || '我的' }}</router-link>
          <router-link v-if="user?.role === 'admin'" to="/admin" :class="navLinkClass('admin')">管理</router-link>
          <button class="text-sm font-medium text-muted hover:text-accent transition-colors" @click="onLogout">退出</button>
        </template>
        <template v-else>
          <router-link to="/register"
             class="px-4 py-1.5 text-sm font-medium text-accent border border-accent rounded-lg hover:bg-accent/10 transition-colors">注册</router-link>
          <router-link to="/login"
             class="px-4 py-1.5 text-sm font-medium text-white bg-accent rounded-lg hover:bg-accent/90 transition-colors">登录</router-link>
        </template>

        <!-- 深色模式切换 -->
        <button
          class="p-2 rounded-lg text-muted hover:text-ink hover:bg-canvas transition-colors"
          @click="toggleDark"
          :title="isDark ? '切换到浅色模式' : '切换到深色模式'"
          :aria-label="isDark ? '切换到浅色模式' : '切换到深色模式'"
        >
          <!-- 太阳图标（浅色） -->
          <svg v-if="!isDark" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          <!-- 月亮图标（深色） -->
          <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
      </div>

      <!-- 移动端按钮组 -->
      <div class="md:hidden flex items-center gap-1">
        <!-- 深色模式切换（移动端） -->
        <button
          class="p-2 rounded-lg text-muted hover:text-ink transition-colors"
          @click="toggleDark"
          :aria-label="isDark ? '切换到浅色模式' : '切换到深色模式'"
        >
          <svg v-if="!isDark" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>

        <!-- 汉堡菜单 -->
        <button
          class="p-2 -mr-2 text-muted hover:text-ink transition-colors"
          @click="menuOpen = !menuOpen"
          :aria-expanded="menuOpen"
          aria-controls="mobile-menu"
          aria-label="菜单"
        >
          <svg v-if="!menuOpen" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
          <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 移动端下拉菜单（带过渡动画） -->
    <Transition name="slide-down">
      <div v-if="menuOpen"
           id="mobile-menu"
           class="md:hidden border-t border-border bg-surface/95 backdrop-blur-md px-6 py-4 space-y-3 shadow-lg"
           @touchstart="touchStartX = $event.touches[0].clientX"
           @touchmove="onMenuTouchMove"
           @touchend="onMenuTouchEnd">
        <template v-if="isAuthenticated">
          <a href="https://vossc.com" target="_blank" rel="noopener noreferrer"
             class="block text-sm font-medium text-muted hover:text-accent transition-colors"
             @click="closeMenu">论坛</a>
          <router-link to="/" @click="closeMenu"
             class="block text-sm font-medium transition-colors hover:text-accent"
             :class="$route.name === 'home' ? 'text-accent' : 'text-muted'">社区</router-link>
          <router-link to="/profile" @click="closeMenu"
             class="block text-sm font-medium transition-colors hover:text-accent"
             :class="$route.name === 'profile' ? 'text-accent' : 'text-muted'">{{ user?.username || '我的' }}</router-link>
          <router-link v-if="user?.role === 'admin'" to="/admin" @click="closeMenu"
             class="block text-sm font-medium transition-colors hover:text-accent"
             :class="$route.name === 'admin' ? 'text-accent' : 'text-muted'">管理</router-link>
          <button class="block text-sm font-medium text-muted hover:text-accent transition-colors w-full text-left"
                  @click="onLogout">退出</button>
        </template>
        <template v-else>
          <router-link to="/register" @click="closeMenu"
             class="block text-sm font-medium text-accent hover:text-accent/80 transition-colors">注册</router-link>
          <router-link to="/login" @click="closeMenu"
             class="block text-sm font-medium text-accent hover:text-accent/80 transition-colors">登录</router-link>
        </template>
      </div>
    </Transition>
  </nav>
  <!-- 移动端菜单遮罩 -->
  <div v-if="menuOpen" class="fixed inset-0 z-40 md:hidden" @click="closeMenu"></div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isAuthenticated, logout, getUser } from '@/stores/auth'
import { useDarkMode } from '@/composables/useDarkMode'

const user = computed(() => getUser())
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)
const touchStartX = ref(0)
const { isDark, toggle: toggleDark } = useDarkMode()

const navLinkClass = (name) => {
  return [
    'text-sm font-medium transition-colors hover:text-accent',
    route.name === name ? 'text-accent' : 'text-muted'
  ]
}

const closeMenu = () => {
  menuOpen.value = false
}

const onLogout = async () => {
  closeMenu()
  await logout()
  router.push('/login')
}

// 移动端菜单滑动手势
const onMenuTouchMove = (e) => {
  const dx = e.touches[0].clientX - touchStartX.value
  // 左滑超过阈值关闭菜单
  if (dx < -60) {
    closeMenu()
  }
}

const onMenuTouchEnd = () => {
  touchStartX.value = 0
}

// 路由变化时自动关闭菜单
watch(() => route.path, () => {
  closeMenu()
})

// ESC 键关闭菜单
const onKeydown = (e) => {
  if (e.key === 'Escape' && menuOpen.value) {
    closeMenu()
  }
}

// 菜单打开时锁定 body 滚动
watch(menuOpen, (open) => {
  if (open) {
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeydown)
  } else {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.slide-down-enter-active {
  transition: all 250ms cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-down-leave-active {
  transition: all 150ms ease-in;
}
.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
