import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refreshToken: localStorage.getItem('refreshToken') || '',
    user: null,
    permissions: []
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '',
    nickname: (state) => state.user?.nickname || ''
  },
  
  actions: {
    async login(credentials) {
      try {
        const response = await axios.post('/api/v1/auth/login', credentials)
        const { token, refreshToken, user } = response.data.data
        
        this.token = token
        this.refreshToken = refreshToken
        this.user = user
        
        localStorage.setItem('token', token)
        localStorage.setItem('refreshToken', refreshToken)
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data?.message || '登录失败' }
      }
    },
    
    async logout() {
      try {
        await axios.post('/api/v1/auth/logout')
      } catch (e) {
        // 忽略错误
      }
      
      this.token = ''
      this.refreshToken = ''
      this.user = null
      this.permissions = []
      
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      delete axios.defaults.headers.common['Authorization']
    },
    
    async fetchProfile() {
      try {
        const response = await axios.get('/api/v1/auth/profile')
        this.user = response.data.data
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
  }
})
