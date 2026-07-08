<template>
  <Transition name="toast">
    <div 
      v-if="visible" 
      class="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-ink/94 text-white px-5 py-3 rounded-full text-sm font-medium"
    >
      {{ message }}
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'

const message = ref('')
const visible = ref(false)
let timer = null

const show = (msg) => {
  message.value = msg
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => {
    visible.value = false
  }, 2200)
}

defineExpose({ show })
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
}
</style>
