/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { computed, ref } from 'vue'
import { apiGet } from '@/utils/api'

export type NvidiaProbeSummary = {
  last_probe_at?: string | null
  available_count?: number
  total_count?: number
  available_scenarios?: Array<{ id?: string; label?: string; model?: string }>
  probe_schedule?: string
}

export type AiConnectStatus = {
  ready?: boolean
  mode?: string
  free_tier?: boolean
  alert_title?: string
  effective_provider_id?: string
  effective_provider_label?: string
  user_notice?: string
  usage_policy_notice?: string
  recharge_cta?: string
  nvidia_probe?: NvidiaProbeSummary | null
  fallback_from_requested?: boolean
}

export const FREE_NVIDIA_ALERT_TITLE = '英伟达免费体验（哪些模型能用以实时为准）'
export const FREE_NVIDIA_NOTICE =
  '英伟达（NVIDIA）目前有免费额度可供体验，但我们无法保证每一个模型都能用——' +
  '哪些能用、哪些暂时不能用，以平台实时情况为准，速度也偏慢。' +
  '要想获得更好的体验，请充值 AI 流量。'

export const NVIDIA_USAGE_POLICY_NOTICE =
  '【客户须知】英伟达免费通道受官方限速与用量额度约束，规则可能随时调整；' +
  '高峰时段可能排队、变慢或个别模型暂时不可用。' +
  '系统于每日 1:00、12:00、20:00 自动检测可用模型，仍以您实际调用时为准。' +
  '要想获得更稳定、更快的服务，请充值 AI 流量。'

export function useAiConnect() {
  const aiConnect = ref<AiConnectStatus | null>(null)
  const loading = ref(false)

  const notice = computed(() => aiConnect.value?.user_notice || '')
  const freeTier = computed(() => !!aiConnect.value?.free_tier)
  const ready = computed(() => !!aiConnect.value?.ready)
  const alertType = computed(() => (freeTier.value ? 'info' : 'success'))
  const alertTitle = computed(
    () =>
      aiConnect.value?.alert_title ||
      (freeTier.value ? FREE_NVIDIA_ALERT_TITLE : 'AI 通道已接通'),
  )
  const usagePolicyNotice = computed(
    () => aiConnect.value?.usage_policy_notice || (freeTier.value ? NVIDIA_USAGE_POLICY_NOTICE : ''),
  )
  const nvidiaProbe = computed(() => aiConnect.value?.nvidia_probe || null)
  const probeSummaryLine = computed(() => {
    const p = nvidiaProbe.value
    if (!p?.last_probe_at) return ''
    const labels = (p.available_scenarios || [])
      .map((s) => s.label)
      .filter(Boolean)
      .slice(0, 4)
    const tail = labels.length ? `当前可用：${labels.join('、')}${labels.length < (p.available_count || 0) ? ' 等' : ''}` : ''
    return `最近检测 ${p.last_probe_at?.slice(0, 16).replace('T', ' ')}（${p.available_count ?? 0}/${p.total_count ?? 0} 项可用）${tail ? ` · ${tail}` : ''}`
  })

  async function refresh() {
    loading.value = true
    try {
      const data = await apiGet<AiConnectStatus>('/client/ai-connect')
      aiConnect.value = data || null
    } catch {
      /* Hermes 执行时会再次 ensure */
    } finally {
      loading.value = false
    }
  }

  return {
    aiConnect,
    loading,
    notice,
    freeTier,
    ready,
    alertType,
    alertTitle,
    usagePolicyNotice,
    nvidiaProbe,
    probeSummaryLine,
    refresh,
  }
}
