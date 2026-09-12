/**
 * @deprecated FIX-4: 此模块已废弃，请统一使用 axios 实例（通常在 @/api/ 或 @/utils/api.ts 中）。
 *
 * 废弃原因：
 * 1. 与 axios 拦截器双通道并存，401 处理逻辑不一致（这里直接跳登录页，axios 走自动续期）
 * 2. 手动拼 token 不走统一鉴权层
 * 3. 无请求/响应拦截器、无重试、无取消能力
 *
 * 迁移指南：
 *   // 旧写法
 *   import { apiFetch } from '@/api/fetchWrapper';
 *   const { data } = await apiFetch('/some/path', { method: 'POST', body: JSON.stringify(payload) });
 *
 *   // 新写法
 *   import request from '@/utils/api';  // 或你项目中的 axios 实例路径
 *   const { data } = await request.post('/some/path', payload);
 *
 * 本文件将在所有调用方迁移完成后删除。
 */

import { apiV1Base } from '@/api/authPaths';

/** @deprecated 使用 axios 实例替代 */
export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<{ data: T | null; error?: string; status: number }> {
  const token = sessionStorage.getItem('admin_token') || localStorage.getItem('admin_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${apiV1Base()}${path}`, { ...options, headers });

  if (res.status === 401) {
    sessionStorage.removeItem('admin_token');
    sessionStorage.removeItem('admin_refresh_token');
    sessionStorage.removeItem('admin_username');
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_refresh_token');
    localStorage.removeItem('admin_username');
    window.location.href = '/login';
    return { data: null, error: '会话已过期', status: 401 };
  }

  const json = await res.json().catch(() => ({}));
  return { data: json, status: res.status };
}