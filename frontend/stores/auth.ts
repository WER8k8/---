import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'
import { useCookie } from '#app'

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
      const { request, setAuthToken } = useApi()
      const res = await request<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: { username, password },
        skipAuth: true,
      })
      this.token = res.access_token
      this.username = username
      setAuthToken(res.access_token)
      // 使用cookie存储用户名
      if (import.meta.client) {
        const usernameCookie = useCookie('admin_username', {
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: 60 * 60 * 24 * 7,
          path: '/'
        })
        usernameCookie.value = username
        // 清理旧的localStorage
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_username')
      }
    },
    logout() {
      const { setAuthToken } = useApi()
      this.token = null
      this.username = null
      setAuthToken(null)
      if (import.meta.client) {
        const usernameCookie = useCookie('admin_username')
        usernameCookie.value = null
      }
    },
    initFromStorage() {
      const { getAuthToken } = useApi()
      const savedToken = getAuthToken()
      if (savedToken) {
        this.token = savedToken
      }
      if (import.meta.client) {
        const usernameCookie = useCookie('admin_username')
        if (usernameCookie.value) {
          this.username = usernameCookie.value
        }
      }
    },
  },
})
