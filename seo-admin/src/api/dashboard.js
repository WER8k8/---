// 数据看板 API
import request from './index';

export const dashboardApi = {
  // 获取统计数据
  getStats: () => request.get('/dashboard/stats'),

  // 获取今日统计
  getTodayStats: () => request.get('/dashboard/today'),

  // 获取趋势数据
  getTrend: params => request.get('/dashboard/trend', { params }),

  // 获取分布数据
  getDistribution: params => request.get('/dashboard/distribution', { params }),

  // 获取实时状态
  getRealTime: () => request.get('/dashboard/realtime'),

  // 导出报表
  export: params => request.get('/dashboard/export', { params, responseType: 'blob' }),
};
