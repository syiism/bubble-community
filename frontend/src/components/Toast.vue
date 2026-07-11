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
import { useToast } from '@/composables/useToast'

const { message, visible } = useToast()
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
