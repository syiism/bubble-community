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

          <div>
            <label class="block text-sm font-medium text-ink mb-2">安全提问</label>
            <select
              v-model="form.questionid"
              class="w-full px-4 py-3 rounded-xl border border-border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
              :disabled="loading"
              @change="toggleAnswer"
            >
              <option :value="0">安全提问(未设置请忽略)</option>
              <option :value="1">母亲的名字</option>
              <option :value="2">爷爷的名字</option>
              <option :value="3">父亲出生的城市</option>
              <option :value="4">您其中一位老师的名字</option>
              <option :value="5">您个人计算机的型号</option>
              <option :value="6">您最喜欢的餐馆名称</option>
              <option :value="7">驾驶执照最后四位数字</option>
            </select>
          </div>

          <div v-if="showAnswer" class="animate-fadeIn">
            <label class="block text-sm font-medium text-ink mb-2">答案</label>
            <input
              v-model="form.answer"
              type="text"
              placeholder="请输入安全提问答案"
              class="w-full px-4 py-3 rounded-xl border border-border bg-canvas focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition-all"
              :disabled="loading"
            />
          </div>

          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="form.cookietime"
                type="checkbox"
                :value="2592000"
                class="w-4 h-4 text-accent rounded border-border focus:ring-accent"
                :disabled="loading"
              />
              <span class="text-sm text-muted">自动登录</span>
            </label>
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
            <a href="https://vossc.com/member.php?mod=register" target="_blank" class="text-accent hover:underline">立即注册</a>
          </p>
          <p class="text-sm text-muted mt-2">
            <a href="javascript:;" onclick="display('layer_login');display('layer_lostpw');" class="text-accent hover:underline">找回密码</a>
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
  questionid: 0,
  answer: '',
  cookietime: 0,
})

const showAnswer = computed(() => Number(form.value.questionid) > 0)

const canSubmit = computed(() => {
  return form.value.username.trim() && form.value.password.trim()
})

const toggleAnswer = () => {
  if (Number(form.value.questionid) === 0) {
    form.value.answer = ''
  }
}

const handleSubmit = async () => {
  if (!canSubmit.value || loading.value) return

  loading.value = true
  try {
    await login({
      username: form.value.username.trim(),
      password: form.value.password,
      questionid: Number(form.value.questionid),
      answer: form.value.answer.trim(),
      cookietime: form.value.cookietime,
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