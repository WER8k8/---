// 关键词管理 API
import request from './index';

export const keywordApi = {
  // 获取关键词列表
  getList: params => request.get('/keywords', { params }),

  // 获取行业列表
  getIndustries: () => request.get('/keywords/industries'),

  // 创建关键词
  create: data => request.post('/keywords', data),

  // 批量创建
  batchCreate: data => request.post('/keywords/batch', data),

  // 更新关键词
  update: (id, data) => request.put(`/keywords/${id}`, data),

  // 删除关键词
  delete: id => request.delete(`/keywords/${id}`),

  // AI组词
  generateWords: data => request.post('/keywords/generate', data),

  // 导出
  export: params => request.get('/keywords/export', { params, responseType: 'blob' }),
};
