import { ref, provide, inject } from 'vue'

const TOAST_KEY = '$$bubble_toast'

export function provideToast() {
  const message = ref('')
  const visible = ref(false)
  let timer = null

  function show(msg) {
    message.value = msg
    visible.value = true
    clearTimeout(timer)
    timer = setTimeout(() => {
      visible.value = false
    }, 2200)
  }

  provide(TOAST_KEY, { message, visible, show })
}

export function useToast() {
  return inject(TOAST_KEY) || { message: ref(''), visible: ref(false), show: () => {} }
}
