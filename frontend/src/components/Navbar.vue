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
      <div class="flex items-center gap-6">
        <template v-if="isAuthenticated">
          <a
            href="https://vossc.com"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm font-medium text-muted hover:text-accent transition-colors"
          >
            论坛
          </a>
          <router-link
            to="/"
            :class="[
              'text-sm font-medium transition-colors hover:text-accent',
              $route.name === 'home' ? 'text-accent' : 'text-muted'
            ]"
          >
            社区
          </router-link>
          <router-link
            to="/profile"
            :class="[
              'text-sm font-medium transition-colors hover:text-accent',
              $route.name === 'profile' ? 'text-accent' : 'text-muted'
            ]"
          >
            {{ user?.username || '我的' }}
          </router-link>
          <router-link v-if="user?.role === 'admin'"
            to="/admin"
            :class="[
              'text-sm font-medium transition-colors hover:text-accent',
              $route.name === 'admin' ? 'text-accent' : 'text-muted'
            ]"
          >
            管理
          </router-link>
          <button
            class="text-sm font-medium text-muted hover:text-accent transition-colors"
            @click="onLogout"
          >
            退出
          </button>
        </template>
        <template v-else>
          <router-link
            to="/register"
            class="px-4 py-1.5 text-sm font-medium text-accent border border-accent rounded-lg hover:bg-accent/10 transition-colors"
          >
            注册
          </router-link>
          <router-link
            to="/login"
            class="px-4 py-1.5 text-sm font-medium text-white bg-accent rounded-lg hover:bg-accent/90 transition-colors"
          >
            登录
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { isAuthenticated, logout, getUser } from '@/stores/auth'

const user = computed(() => getUser())

const onLogout = async () => {
  await logout()
}
</script>