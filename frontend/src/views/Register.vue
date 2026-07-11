<template>
  <div class="min-h-screen bg-canvas flex items-center justify-center px-4 py-12 overflow-y-auto">
    <div class="w-full max-w-md">
      <div class="bg-surface rounded-2xl shadow-lg p-8">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-accent flex items-center justify-center">
            <svg class="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="8"/>
              <circle cx="12" cy="12" r="4"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-ink mb-2">段评气泡社区</h1>
          <p class="text-sm text-muted">注册新账号</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-ink mb-2">用户名</label>
            <div class="relative">
              <input
                v-model="form.username"
                type="text"
                placeholder="1~15 个字符"
                class="w-full px-4 py-3 rounded-xl border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
                :class="[
                  usernameStatus === 'taken' ? 'border-red-400' : usernameStatus === 'available' ? 'border-green-400' : 'border-border',
                  loading ? 'opacity-50' : ''
                ]"
                :disabled="loading"
                maxlength="15"
                @input="onUsernameInput"
              />
              <span
                v-if="usernameChecking"
                class="absolute right-3 top-1/2 -translate-y-1/2"
              >
                <svg class="w-4 h-4 text-muted animate-spin" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
              </span>
            </div>
            <p
              v-if="usernameStatus === 'taken'"
              class="mt-1 text-xs text-red-500"
            >该用户名已被注册</p>
            <p
              v-else-if="usernameStatus === 'available'"
              class="mt-1 text-xs text-green-600"
            >用户名可用</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-ink mb-2">密码</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="至少 6 个字符"
              class="w-full px-4 py-3 rounded-xl border border-border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
              :class="{ 'opacity-50': loading }"
              :disabled="loading"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-ink mb-2">确认密码</label>
            <input
              v-model="form.password2"
              type="password"
              placeholder="请再次输入密码"
              class="w-full px-4 py-3 rounded-xl border bg-canvas outline-none transition-all"
              :class="{
                'opacity-50': loading,
                'border-red-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20': passwordMismatch,
                'border-border focus:border-accent focus:ring-2 focus:ring-accent/20': !passwordMismatch,
              }"
              :disabled="loading"
            />
            <p v-if="passwordMismatch" class="mt-1.5 text-xs text-red-500 flex items-center gap-1">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              两次输入的密码不一致
            </p>
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
            <span>{{ loading ? '注册中...' : '注册' }}</span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-muted">
            已有账号？
            <router-link to="/login" class="text-accent hover:underline">立即登录</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { register as registerUser } from '@/stores/auth'
import { api } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const toast = useToast()

const loading = ref(false)
const usernameChecking = ref(false)
const usernameStatus = ref(null) // null | 'checking' | 'available' | 'taken'
let usernameTimer = null

const form = ref({
  username: '',
  password: '',
  password2: '',
})

const canSubmit = computed(() => {
  return form.value.username.trim().length >= 1
})

const passwordMismatch = computed(() => {
  return form.value.password2.length > 0 && form.value.password !== form.value.password2
})

const onUsernameInput = () => {
  clearTimeout(usernameTimer)
  const val = form.value.username.trim()
  if (val.length < 1) {
    usernameStatus.value = null
    usernameChecking.value = false
    return
  }
  usernameChecking.value = true
  usernameStatus.value = 'checking'
  usernameTimer = setTimeout(async () => {
    try {
      const res = await api.checkUsername(val)
      usernameStatus.value = res.available ? 'available' : 'taken'
    } catch {
      usernameStatus.value = null
    } finally {
      usernameChecking.value = false
    }
  }, 500)
}

const handleSubmit = async () => {
  if (!canSubmit.value || loading.value) return

  if (form.value.password.length < 6) {
    toast.show('密码长度不能少于 6 个字符')
    return
  }
  if (form.value.password !== form.value.password2) {
    toast.show('两次输入的密码不一致')
    return
  }

  if (usernameStatus.value === 'taken') {
    toast.show('该用户名已被注册')
    return
  }

  loading.value = true
  try {
    await registerUser({
      username: form.value.username.trim(),
      password: form.value.password,
      password2: form.value.password2,
    })
    await ElMessageBox.alert('账号注册成功！现在可以登录了。', '注册成功', {
      confirmButtonText: '去登录', type: 'success', center: true
    })
    const redirect = route.query.redirect || '/'
    await router.push(redirect)
  } catch (err) {
    toast.show(err.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>
