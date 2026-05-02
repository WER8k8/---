import { defineNuxtPlugin } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  if (process.client) {
    nuxtApp.hook('app:created', () => {
      const { useAuthStore } = require('~/stores/auth')
      const auth = useAuthStore()
      auth.initFromStorage()
    })
  }
})
