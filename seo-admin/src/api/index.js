import axios from 'axios';
import { ElMessage } from 'element-plus';
import {
  getSharedBearerToken,
  clearSharedSession,
  redirectToMainAdminLogin,
} from '@/utils/authBridge';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  config => {
    const token = getSharedBearerToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请从主管理后台重新登录');
          clearSharedSession();
          redirectToMainAdminLogin(window.location.href);
          break;
        case 403:
          ElMessage.error(data?.message || '权限不足');
          break;
        case 404:
          ElMessage.error('请求的资源不存在');
          break;
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试');
          break;
        default:
          ElMessage.error(data?.message || '服务器错误');
      }
    } else {
      ElMessage.error('网络连接失败');
    }

    return Promise.reject(error);
  }
);

export default api;
