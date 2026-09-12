import { ApiError } from '@/utils/api'

export interface AiProviderRow {
  id: string
  name: string
  provider_type?: string
  base_url?: string
  default_model?: string
  has_api_key?: boolean
  api_key?: string | null
  api_key_masked?: string | null
  enabled?: boolean
  is_active?: boolean
  models?: Array<{ model_name: string; model_type?: string; is_active?: boolean }>
}

/** 后端返回 masked key 或 has_api_key 时判定为已配置 */
export function isProviderConfigured(p: Pick<AiProviderRow, 'has_api_key' | 'api_key'>): boolean {
  return Boolean(p.has_api_key || p.api_key)
}

export function providerConfiguredTagColor(p: Pick<AiProviderRow, 'has_api_key' | 'api_key'>): string {
  return isProviderConfigured(p) ? 'green' : 'red'
}

export function providerConfiguredLabel(p: Pick<AiProviderRow, 'has_api_key' | 'api_key'>): string {
  return isProviderConfigured(p) ? '已配置' : '未配置'
}

export function buildProviderStatusMap(providers: AiProviderRow[]): Record<string, boolean> {
  const map: Record<string, boolean> = {}
  providers.forEach((p) => {
    if (isProviderConfigured(p)) map[p.name] = true
  })
  return map
}

export function apiErrorMessage(e: unknown, fallback: string): string {
  if (e instanceof ApiError && e.message && !e.message.startsWith('API ')) return e.message
  if (e instanceof Error && e.message) return e.message
  return fallback
}

export function maskApiKey(key: string | undefined | null): string {
  if (!key) return '---'
  if (key.length <= 8) return '****'
  return `${key.slice(0, 4)}****${key.slice(-4)}`
}
