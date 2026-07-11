<template>
  <div class="min-h-screen bg-canvas">
    <Navbar />
    <main class="pb-20">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>
