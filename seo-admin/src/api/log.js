// 日志管理 API
import request from './index';

export const logApi = {
  // 获取操作日志列表
  getOperationList: params => request.get('/logs/operations', { params }),

  // 获取登录日志列表
  getLoginList: params => request.get('/logs/login', { params }),

  // 获取日志详情
  getDetail: id => request.get(`/logs/${id}`),

  // 导出操作日志
  exportOperation: params =>
    request.get('/logs/operations/export', { params, responseType: 'blob' }),

  // 导出登录日志
  exportLogin: params => request.get('/logs/login/export', { params, responseType: 'blob' }),

  // 清理日志
  clean: data => request.post('/logs/clean', data),
};
