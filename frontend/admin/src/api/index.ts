import axios from 'axios'

const baseURL = (import.meta as any).env.VITE_API_BASE || '/api/v1'

const api = axios.create({
  baseURL,
  timeout: 30000,
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    console.debug('[API] 请求URL:', config.url)
    console.debug('[API] Token存在:', !!token)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.debug('[API] Authorization头已设置')
    } else {
      console.warn('[API] Token不存在，请求将不携带认证信息')
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('[API] 401认证失败:', error.response.config.url)
      console.error('[API] 响应详情:', error.response.data)
      const currentPath = window.location.pathname
      // 如果已经在登录页面，不需要重复跳转
      if (currentPath !== '/login') {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_username')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const productsAPI = {
  list: (params?: Record<string, any>) => api.get('/products', { params }),
  get: (id: string) => api.get(`/products/${id}`),
  create: (data: any) => api.post('/products', data),
  update: (id: string, data: any) => api.put(`/products/${id}`, data),
  delete: (id: string) => api.delete(`/products/${id}`),
  categories: () => api.get('/products/categories'),
  createCategory: (data: any) => api.post('/products/categories', data),
  updateCategory: (id: string, data: any) => api.put(`/products/categories/${id}`, data),
  deleteCategory: (id: string) => api.delete(`/products/categories/${id}`),
}

export const seoAPI = {
  dashboard: () => api.get('/seo/dashboard'),
  generateLLMSTxt: (data: any) => api.post('/seo/generate-llms-txt', data),
  optimizeContent: (data: any) => api.post('/seo/optimize-content', data),
  audit: (data: any) => api.post('/seo/audit', data),
  getAudit: (id: string) => api.get(`/seo/audit/${id}`),
  pages: (params?: Record<string, any>) => api.get('/seo/pages', { params }),
  updatePage: (id: string, data: any) => api.put(`/seo/pages/${id}`, data),
  optimizePage: (id: string, data: any) => api.post(`/seo/pages/${id}/optimize`, data),
  schemaGenerate: (data: any) => api.post('/seo/schema/generate', data),
  schemaValidate: (data: any) => api.post('/seo/schema/validate', data),
  schemaList: () => api.get('/seo/schema'),
  schemaExport: (id: string) => api.get(`/seo/schema/export/${id}`),
  schemaGet: (id: string) => api.get(`/seo/schema/${id}`),
  schemaTypes: () => api.get('/seo/schema/types'),
  schemaDelete: (id: string) => api.delete(`/seo/schema/${id}`),
  authors: () => api.get('/seo/authors'),
  authorCreate: (data: any) => api.post('/seo/authors', data),
  authorUpdate: (id: string, data: any) => api.put(`/seo/authors/${id}`, data),
  authorDelete: (id: string) => api.delete(`/seo/authors/${id}`),
  trustSignals: () => api.get('/seo/trust-signals'),
  score: (data: any) => api.post('/seo/score', data),
}

export const contentAPI = {
  list: (params?: Record<string, any>) => api.get('/content/pages', { params }),
  get: (id: string) => api.get(`/content/pages/${id}`),
  create: (data: any) => api.post('/content/pages', data),
  update: (id: string, data: any) => api.put(`/content/pages/${id}`, data),
  delete: (id: string) => api.delete(`/content/pages/${id}`),
  aiGenerate: (data: any) => api.post('/content/ai/generate', data),
  aiPolish: (data: any) => api.post('/content/ai/polish', data),
}

export const casesAPI = {
  list: (params?: Record<string, any>) => api.get('/cases', { params }),
  get: (id: string) => api.get(`/cases/${id}`),
  create: (data: any) => api.post('/cases', data),
  update: (id: string, data: any) => api.put(`/cases/${id}`, data),
  delete: (id: string) => api.delete(`/cases/${id}`),
}

export const inquiriesAPI = {
  list: (params?: Record<string, any>) => api.get('/inquiries', { params }),
  get: (id: string) => api.get(`/inquiries/${id}`),
  update: (id: string, data: any) => api.put(`/inquiries/${id}`, data),
  delete: (id: string) => api.delete(`/inquiries/${id}`),
}

export const systemAPI = {
  login: (data: any) => api.post('/system/login', data),
  contact: (data: any) => api.post('/system/contact', data),
  auditLogs: (params?: Record<string, any>) => api.get('/system/audit/logs', { params }),
  deleteAuditLog: (id: string) => api.delete(`/system/audit/logs/${id}`),
  clearAuditLogs: (params?: Record<string, any>) => api.delete('/system/audit/logs', { params }),
}

export const usersAPI = {
  list: (params?: Record<string, any>) => api.get('/users', { params }),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
}

export default api