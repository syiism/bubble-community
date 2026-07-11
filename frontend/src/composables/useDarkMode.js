import { ref, watchEffect } from 'vue'

const THEME_KEY = 'bubble-theme'
const isDark = ref(false)

export function useDarkMode() {
  // 初始化：读取 localStorage 或跟随系统偏好
  const stored = localStorage.getItem(THEME_KEY)
  if (stored === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  } else if (stored === 'light') {
    isDark.value = false
    document.documentElement.classList.remove('dark')
  } else {
    // 默认跟随系统
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    isDark.value = prefersDark
    document.documentElement.classList.toggle('dark', prefersDark)
  }

  const toggle = () => {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
  }

  return { isDark, toggle }
}
