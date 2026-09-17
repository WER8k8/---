/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 系统管理 API */
import { apiGet } from '@/utils/api'

export const systemAPI = {
  auditLogs: (params: { page?: number; page_size?: number }) => {
    const search = new URLSearchParams()
    if (params.page != null) search.set('page', String(params.page))
    if (params.page_size != null) search.set('page_size', String(params.page_size))
    const q = search.toString() ? `?${search}` : ''
    return apiGet<{ items?: unknown[]; data?: unknown[]; total?: number }>(
      `/system/audit/logs${q}`,
    )
  },
}
