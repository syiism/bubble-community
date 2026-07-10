<template>
  <div class="min-h-screen bg-canvas flex items-center justify-center px-4 py-8">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-lg p-8">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-accent flex items-center justify-center">
            <svg class="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="8"/>
              <circle cx="12" cy="12" r="4"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-ink mb-2">段评气泡社区</h1>
          <p class="text-sm text-muted">登录您的账号</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-ink mb-2">用户名</label>
            <input
              v-model="form.username"
              type="text"
              placeholder="请输入用户名"
              class="w-full px-4 py-3 rounded-xl border border-border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
              :disabled="loading"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-ink mb-2">密码</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              class="w-full px-4 py-3 rounded-xl border border-border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
              :disabled="loading"
            />
          </div>

          <button
            type="submit"
            :disabled="loading || !canSubmit"
            :class="[
              'w-full py-3.5 rounded-xl font-medium text-white transition-all flex items-center justify-center gap-2',
              loading || !canSubmit
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-accent hover:bg-accent/90 active:scale-[0.98]'
            ]"
          >
            <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-muted">
            还没有账号？
            <router-link to="/register" class="text-accent hover:underline">立即注册</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '@/stores/auth'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const form = ref({
  username: '',
  password: '',
})

const canSubmit = computed(() => {
  return form.value.username.trim() && form.value.password.trim()
})

const handleSubmit = async () => {
  if (!canSubmit.value || loading.value) return

  loading.value = true
  try {
    await login({
      username: form.value.username.trim(),
      password: form.value.password,
    })
    const redirect = route.query.redirect || '/'
    await router.push(redirect)
  } catch (err) {
    console.error('登录失败:', err)
  } finally {
    loading.value = false
  }
}
</script>