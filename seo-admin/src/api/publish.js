// 发布任务 API
import request from './index';

export const publishApi = {
  // 获取任务列表
  getList: params => request.get('/publish/tasks', { params }),

  // 获取任务详情
  getDetail: id => request.get(`/publish/tasks/${id}`),

  // 创建任务
  create: data => request.post('/publish/tasks', data),

  // 更新任务
  update: (id, data) => request.put(`/publish/tasks/${id}`, data),

  // 取消任务
  cancel: id => request.post(`/publish/tasks/${id}/cancel`),

  // 重试任务
  retry: id => request.post(`/publish/tasks/${id}/retry`),

  // 删除任务
  delete: id => request.delete(`/publish/tasks/${id}`),

  // 批量创建任务
  batchCreate: data => request.post('/publish/tasks/batch', data),

  // 获取任务日志
  getLogs: (id, params) => request.get(`/publish/tasks/${id}/logs`, { params }),

  // 导出
  export: params => request.get('/publish/tasks/export', { params, responseType: 'blob' }),
};
