<template>
  <div class="min-h-screen bg-canvas">
    <Navbar />
    <main class="pb-20">
      <router-view v-slot="{ Component }">
        <component :is="Component" :toast-ref="toastRef" />
      </router-view>
    </main>
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navbar from './components/Navbar.vue'
import Toast from './components/Toast.vue'

const toastRef = ref(null)
</script>
