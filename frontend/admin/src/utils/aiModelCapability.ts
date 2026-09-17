/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export type AiModelStatus =
  | 'available'
  | 'key_ok'
  | 'unavailable'
  | 'no_key'
  | 'disabled'
  | 'unknown'

export interface AiModelEnrichedRow {
  id: string
  provider_id?: string
  model_name: string
  model_type: string
  provider_name?: string
  capability_label?: string
  capability_desc?: string
  endpoint?: string
  input_modes?: string[]
  status?: AiModelStatus
  status_label?: string
  healthy?: boolean | null
  latency_ms?: number | null
  error?: string
  note?: string
  active?: boolean
  sort_order?: number
}

export function modelStatusColor(status?: AiModelStatus): string {
  switch (status) {
    case 'available':
      return 'success'
    case 'key_ok':
      return 'processing'
    case 'unavailable':
      return 'error'
    case 'no_key':
      return 'default'
    case 'disabled':
      return 'default'
    default:
      return 'warning'
  }
}

export function endpointLabel(endpoint?: string): string {
  return endpoint === '/v1/infer' ? '视频 infer' : '对话 chat'
}

export function endpointColor(endpoint?: string): string {
  return endpoint === '/v1/infer' ? 'purple' : 'cyan'
}

export function inputModesLabel(modes?: string[]): string {
  if (!modes?.length) return '文本'
  const map: Record<string, string> = {
    text: '文本',
    image: '图片',
    video: '视频',
  }
  return modes.map((m) => map[m] || m).join(' + ')
}

export function mergeProbeResults(
  models: AiModelEnrichedRow[],
  probeRows: AiModelEnrichedRow[],
): AiModelEnrichedRow[] {
  const byId = new Map(probeRows.map((r) => [r.id, r]))
  return models.map((m) => {
    const probe = byId.get(m.id)
    if (!probe) return m
    return { ...m, ...probe }
  })
}

export function summarizeModelStatus(models: AiModelEnrichedRow[]) {
  const active = models.filter((m) => m.active !== false)
  const available = active.filter((m) => m.status === 'available' || m.status === 'key_ok').length
  const unavailable = active.filter((m) => m.status === 'unavailable').length
  const unknown = active.filter((m) => !m.status || m.status === 'unknown').length
  return { total: active.length, available, unavailable, unknown }
}
