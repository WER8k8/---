/** 数据分析 / 流量看板 API */
import { apiGet } from '@/utils/api'

export const dataAnalyticsAPI = {
  list: () => apiGet<Record<string, unknown>>('/analytics/'),
  dashboard: () => apiGet<Record<string, unknown>>('/analytics/dashboard'),
  traffic: (params?: { period?: string }) => {
    const q = params?.period ? `?period=${encodeURIComponent(params.period)}` : ''
    return apiGet<Record<string, unknown>>(`/analytics/traffic${q}`)
  },
  trafficBoard: (params?: { period?: string; tenant_id?: string }) => {
    const search = new URLSearchParams()
    if (params?.period) search.set('period', params.period)
    if (params?.tenant_id) search.set('tenant_id', params.tenant_id)
    const q = search.toString() ? `?${search}` : ''
    return apiGet<Record<string, unknown>>(`/analytics/traffic-board${q}`)
  },
  operationsTrafficBoard: (params?: { period?: string }) => {
    const q = params?.period ? `?period=${encodeURIComponent(params.period)}` : ''
    return apiGet<Record<string, unknown>>(`/analytics/operations/traffic-board${q}`)
  },
}
