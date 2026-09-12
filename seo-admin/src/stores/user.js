import { defineStore } from 'pinia';
import axios from 'axios';
import { getSharedBearerToken, persistSharedToken, clearSharedSession } from '@/utils/authBridge';

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    refreshToken: localStorage.getItem('refreshToken') || '',
    user: null,
    permissions: [],
  }),

  getters: {
    isLoggedIn: state => !!state.token,
    username: state => state.user?.username || '',
    nickname: state => state.user?.nickname || '',
  },

  actions: {
    /** 从主后台写入的 admin_token / 旧 token 恢复会话 */
    hydrateFromMainAdminToken() {
      const t = getSharedBearerToken();
      if (t && t !== this.token) {
        this.token = t;
        axios.defaults.headers.common.Authorization = `Bearer ${t}`;
      }
      if (!this.token) {
        delete axios.defaults.headers.common.Authorization;
      }
    },

    /**
     * 已废弃独立登录：请使用主管理后台（超级管理员工作台）登录。
     * 若仍需程序化写 token，可调用 setToken。
     */
    async login() {
      return { success: false, error: '请使用主管理后台统一登录' };
    },

    async logout() {
      try {
        await axios.post('/api/v1/auth/logout');
      } catch (e) {
        // 忽略
      }

      this.token = '';
      this.refreshToken = '';
      this.user = null;
      this.permissions = [];

      clearSharedSession();
      delete axios.defaults.headers.common.Authorization;
    },

    async fetchProfile() {
      try {
        const response = await axios.get('/api/v1/auth/profile');
        const body = response.data?.data ?? response.data;
        this.user = body;
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    },

    async setToken(token) {
      this.token = token;
      persistSharedToken(token);
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    },

    async setUserInfo(user) {
      this.user = user;
    },
  },
});
