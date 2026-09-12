// 平台管理 API
import request from './index';

export const platformApi = {
  // 获取平台列表
  getList: params => request.get('/platforms', { params }),

  // 获取平台详情
  getDetail: id => request.get(`/platforms/${id}`),

  // 创建平台
  create: data => request.post('/platforms', data),

  // 更新平台
  update: (id, data) => request.put(`/platforms/${id}`, data),

  // 删除平台
  delete: id => request.delete(`/platforms/${id}`),

  // 获取平台账号列表
  getAccounts: platformId => request.get(`/platforms/${platformId}/accounts`),

  // 添加平台账号
  addAccount: (platformId, data) => request.post(`/platforms/${platformId}/accounts`, data),

  // 更新平台账号
  updateAccount: (accountId, data) => request.put(`/platforms/accounts/${accountId}`, data),

  // 删除平台账号
  deleteAccount: accountId => request.delete(`/platforms/accounts/${accountId}`),

  // 测试账号连接
  testAccount: accountId => request.post(`/platforms/accounts/${accountId}/test`),
};
