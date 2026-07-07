import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { bootstrapAuth } from './stores/auth'
import './style.css'

bootstrapAuth().finally(() => {
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
})
