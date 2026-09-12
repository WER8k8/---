// 收录监控 API
import request from './index';

export const monitoringApi = {
  // 获取收录记录列表
  getList: params => request.get('/monitoring/records', { params }),

  // 获取收录统计
  getStats: () => request.get('/monitoring/stats'),

  // 获取趋势数据
  getTrend: params => request.get('/monitoring/trend', { params }),

  // 批量检测收录
  batchCheck: articleIds => request.post('/monitoring/batch-check', { articleIds }),

  // 获取异常预警列表
  getAlerts: params => request.get('/monitoring/alerts', { params }),

  // 处理预警
  handleAlert: (id, data) => request.put(`/monitoring/alerts/${id}`, data),

  // 设置检测计划
  setSchedule: data => request.post('/monitoring/schedule', data),

  // 获取检测计划
  getSchedule: () => request.get('/monitoring/schedule'),

  // 导出
  export: params => request.get('/monitoring/export', { params, responseType: 'blob' }),
};
