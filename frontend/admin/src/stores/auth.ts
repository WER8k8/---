import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin_token'))
  const username = ref<string | null>(localStorage.getItem('admin_username'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(usernameValue: string, password: string) {
    try {
      const res = await fetch('/api/v1/system/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usernameValue, password }),
      })
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '登录失败' }))
        // 将HTTP状态码加入错误信息，方便前端判断
        throw new Error(`HTTP ${res.status}: ${err.detail || '登录失败'}`)
      }
      
      const data = await res.json()
      token.value = data.access_token
      username.value = usernameValue
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_username', usernameValue)
      
    } catch (e: any) {
      // 网络错误处理
      if (e.message && e.message.includes('Failed to fetch')) {
        throw new Error('NetworkError: 无法连接到服务器，请检查后端服务是否正常运行')
      }
      throw e
    }
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
  }

  return { token, username, isAuthenticated, login, logout }
})