// 模板管理 API
import request from './index';

export const templateApi = {
  // 获取模板列表
  getList: params => request.get('/templates', { params }),

  // 获取模板详情
  getDetail: id => request.get(`/templates/${id}`),

  // 创建模板
  create: data => request.post('/templates', data),

  // 更新模板
  update: (id, data) => request.put(`/templates/${id}`, data),

  // 删除模板
  delete: id => request.delete(`/templates/${id}`),

  // 复制模板
  copy: id => request.post(`/templates/${id}/copy`),

  // 模板预览
  preview: (id, data) => request.post(`/templates/${id}/preview`, data),

  // 导出
  export: params => request.get('/templates/export', { params, responseType: 'blob' }),
};
