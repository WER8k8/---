// 地域管理 API
import request from './index';

export const regionApi = {
  // 获取地域树
  getTree: () => request.get('/regions/tree'),

  // 获取地域列表
  getList: params => request.get('/regions', { params }),

  // 创建地域
  create: data => request.post('/regions', data),

  // 更新地域
  update: (id, data) => request.put(`/regions/${id}`, data),

  // 删除地域
  delete: id => request.delete(`/regions/${id}`),

  // 批量导入
  batchImport: file => {
    const formData = new FormData();
    formData.append('file', file);
    return request.post('/regions/batch-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // 导出
  export: () => request.get('/regions/export', { responseType: 'blob' }),
};
