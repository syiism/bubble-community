<template>
  <div class="min-h-screen bg-canvas">
    <Navbar />
    <main class="pb-20">
      <router-view />
    </main>
    <Toast />
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
import Toast from './components/Toast.vue'
import { provideToast } from '@/composables/useToast'

provideToast()
</script>
