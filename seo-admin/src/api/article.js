// 文章管理 API
import request from './index';

export const articleApi = {
  // 获取文章列表
  getList: params => request.get('/articles', { params }),

  // 获取文章详情
  getDetail: id => request.get(`/articles/${id}`),

  // 创建文章
  create: data => request.post('/articles', data),

  // 更新文章
  update: (id, data) => request.put(`/articles/${id}`, data),

  // 删除文章
  delete: id => request.delete(`/articles/${id}`),

  // 批量生成文章
  batchGenerate: data => request.post('/articles/batch-generate', data),

  // 批量删除
  batchDelete: ids => request.post('/articles/batch-delete', { ids }),

  // 导出
  export: params => request.get('/articles/export', { params, responseType: 'blob' }),
};
