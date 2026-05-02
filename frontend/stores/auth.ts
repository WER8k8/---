import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    username: null as string | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(username: string, password: string) {
      const { request } = useApi()
      const res = await request<{ access_token: string }>('/system/login', {
        method: 'POST',
        body: { username, password },
        skipAuth: true,
      })
      this.token = res.access_token
      this.username = username
      localStorage.setItem('admin_token', res.access_token)
      localStorage.setItem('admin_username', username)
    },
    logout() {
      this.token = null
      this.username = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_username')
    },
    initFromStorage() {
      const savedToken = localStorage.getItem('admin_token')
      const savedUsername = localStorage.getItem('admin_username')
      if (savedToken) {
        this.token = savedToken
        this.username = savedUsername
      }
    },
  },
})
