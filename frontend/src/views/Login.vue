<template>
  <div class="pt-24 pb-20">
    <div class="max-w-md mx-auto px-6">
      <div class="bg-surface border border-border rounded-2xl p-8 scroll-animate">
        <h1 class="text-2xl font-serif font-medium text-ink mb-2">登录</h1>
        <p class="text-sm text-muted mb-8">登录后即可使用段评气泡社区</p>

        <form class="space-y-5" @submit.prevent="submit">
          <div>
            <label class="block text-sm font-medium text-ink mb-2">用户名</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="输入用户名"
              class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-ink mb-2">密码</label>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="输入密码"
              class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <p v-if="error" class="text-sm text-paleText-red">{{ error }}</p>

          <button
            :disabled="loading || !username.trim() || !password"
            class="w-full py-3 text-sm font-medium text-white bg-accent rounded-xl hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <p class="text-sm text-muted mt-6 text-center">
          还没有账号？
          <router-link to="/register" class="text-accent hover:text-accent/80 font-medium">去注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  loading.value = true
  try {
    await login(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
