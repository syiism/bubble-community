<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-border">
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
      <div class="hidden md:flex items-center gap-6">
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
      </div>

      <!-- 移动端汉堡菜单 -->
      <button class="md:hidden p-2 -mr-2 text-muted hover:text-ink transition-colors" @click="menuOpen = !menuOpen">
        <svg v-if="!menuOpen" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
        <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 移动端下拉菜单 -->
    <div v-if="menuOpen"
         class="md:hidden border-t border-border bg-white/95 backdrop-blur-md px-6 py-4 space-y-3 shadow-lg">
      <template v-if="isAuthenticated">
        <a href="https://vossc.com" target="_blank" rel="noopener noreferrer"
           class="block text-sm font-medium text-muted hover:text-accent transition-colors"
           @click="menuOpen = false">论坛</a>
        <router-link to="/" @click="menuOpen = false"
           class="block text-sm font-medium transition-colors hover:text-accent"
           :class="$route.name === 'home' ? 'text-accent' : 'text-muted'">社区</router-link>
        <router-link to="/profile" @click="menuOpen = false"
           class="block text-sm font-medium transition-colors hover:text-accent"
           :class="$route.name === 'profile' ? 'text-accent' : 'text-muted'">{{ user?.username || '我的' }}</router-link>
        <router-link v-if="user?.role === 'admin'" to="/admin" @click="menuOpen = false"
           class="block text-sm font-medium transition-colors hover:text-accent"
           :class="$route.name === 'admin' ? 'text-accent' : 'text-muted'">管理</router-link>
        <button class="block text-sm font-medium text-muted hover:text-accent transition-colors w-full text-left"
                @click="onLogout">退出</button>
      </template>
      <template v-else>
        <router-link to="/register" @click="menuOpen = false"
           class="block text-sm font-medium text-accent hover:text-accent/80 transition-colors">注册</router-link>
        <router-link to="/login" @click="menuOpen = false"
           class="block text-sm font-medium text-accent hover:text-accent/80 transition-colors">登录</router-link>
      </template>
    </div>
  </nav>
  <!-- 移动端菜单遮罩 -->
  <div v-if="menuOpen" class="fixed inset-0 z-40 md:hidden" @click="menuOpen = false"></div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isAuthenticated, logout, getUser } from '@/stores/auth'

const user = computed(() => getUser())
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)

const navLinkClass = (name) => {
  return [
    'text-sm font-medium transition-colors hover:text-accent',
    route.name === name ? 'text-accent' : 'text-muted'
  ]
}

const onLogout = async () => {
  menuOpen.value = false
  await logout()
  router.push('/login')
}
</script>
