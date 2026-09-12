// 系统配置 API
import request from './index';

export const configApi = {
  // 获取配置分组列表
  getGroups: () => request.get('/configs/groups'),

  // 获取配置
  get: group => request.get(`/configs/${group}`),

  // 更新配置
  update: (group, data) => request.put(`/configs/${group}`, data),

  // 重置配置
  reset: group => request.post(`/configs/${group}/reset`),

  // 导出配置
  export: () => request.get('/configs/export', { responseType: 'blob' }),

  // 导入配置
  import: file => {
    const formData = new FormData();
    formData.append('file', file);
    return request.post('/configs/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
