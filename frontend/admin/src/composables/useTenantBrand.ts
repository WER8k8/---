/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { computed, inject, onMounted, provide, ref, type InjectionKey, type Ref } from 'vue'
import { getAuthToken } from '@/utils/api'
import {
  assistantGreeting,
  assistantHeaderSubtitle,
  assistantIntroLine,
  FEATURE,
  flywheelTitle,
} from '@/constants/sales-assistant-brand'
import { resolveTenantSiteUrl } from '@/utils/tenantSitePreview'

export type TenantBrandContext = {
  companyName: Ref<string>
  tenantDomain: Ref<string>
  siteUrl: Ref<string>
  loaded: Ref<boolean>
  fabInitial: Ref<string>
  assistantTitle: Ref<string>
  headerSubtitle: Ref<string>
  welcomeMessage: Ref<string>
  greetingMessage: Ref<string>
  flywheelTitle: Ref<string>
  load: () => Promise<void>
}

const TENANT_BRAND_KEY: InjectionKey<TenantBrandContext> = Symbol('tenantBrand')

async function fetchBootstrap(): Promise<{
  company_name?: string
  tenant_domain?: string
  site_url?: string
} | null> {
  const tk = getAuthToken()
  if (!tk) return null
  const headers = { Authorization: `Bearer ${tk}` }
  try {
    const res = await fetch('/api/v1/bff/client/bootstrap', { headers })
    const body = await res.json()
    if (typeof body.code === 'number' && body.code !== 0) return null
    const data = (body.data ?? body) as Record<string, unknown>
    const tenant = (data.tenant ?? {}) as Record<string, unknown>
    return {
      company_name: String(tenant.name || '').trim() || undefined,
      tenant_domain: String(tenant.domain || '').trim() || undefined,
      site_url: String(data.site_url || '').trim() || undefined,
    }
  } catch {
    return null
  }
}

async function fetchBranding(): Promise<{ company_name?: string; tenant_domain?: string; site_url?: string }> {
  const boot = await fetchBootstrap()
  if (boot?.company_name || boot?.tenant_domain) return boot
  const tk = getAuthToken()
  if (!tk) return {}
  const headers = { Authorization: `Bearer ${tk}` }
  try {
    const res = await fetch('/api/v1/client/branding', { headers })
    const body = await res.json()
    const data = (body.data ?? body) as Record<string, unknown>
    if (typeof body.code === 'number' && body.code !== 0) return {}
    return {
      company_name: String(data.company_name || '').trim() || undefined,
      tenant_domain: String(data.tenant_domain || '').trim() || undefined,
    }
  } catch {
    try {
      const res = await fetch('/api/v1/client/dashboard', { headers })
      const body = await res.json()
      const data = (body.data ?? body) as Record<string, unknown>
      const brand = (data.brand ?? {}) as Record<string, unknown>
      return {
        company_name: String(brand.company_name || '').trim() || undefined,
      }
    } catch {
      return {}
    }
  }
}

function fabChar(name: string): string {
  const t = name.trim()
  if (!t) return '助'
  return t.charAt(0)
}

export function provideTenantBrand(): TenantBrandContext {
  const companyName = ref('您的公司')
  const tenantDomain = ref('')
  const siteUrl = ref('')
  const loaded = ref(false)

  const assistantTitle = computed(() => `${companyName.value} · ${FEATURE.assistantRole}`)
  const headerSubtitle = computed(() => assistantHeaderSubtitle(companyName.value))
  const welcomeMessage = computed(() => assistantIntroLine(companyName.value))
  const greetingMessage = computed(() => assistantGreeting(companyName.value))
  const flywheelTitleText = computed(() => flywheelTitle(companyName.value))
  const fabInitial = computed(() => fabChar(companyName.value))

  async function load() {
    const data = await fetchBranding()
    if (data.company_name) companyName.value = data.company_name
    if (data.tenant_domain) tenantDomain.value = data.tenant_domain
    const resolved = resolveTenantSiteUrl(data.tenant_domain || '', data.site_url)
    if (resolved) siteUrl.value = resolved
    loaded.value = true
  }

  const ctx: TenantBrandContext = {
    companyName,
    tenantDomain,
    siteUrl,
    loaded,
    fabInitial,
    assistantTitle,
    headerSubtitle,
    welcomeMessage,
    greetingMessage,
    flywheelTitle: flywheelTitleText,
    load,
  }

  provide(TENANT_BRAND_KEY, ctx)
  onMounted(() => {
    void load()
  })
  return ctx
}

export function useTenantBrand(): TenantBrandContext {
  const ctx = inject(TENANT_BRAND_KEY)
  if (ctx) return ctx

  const companyName = ref('您的公司')
  const tenantDomain = ref('')
  const siteUrl = ref('')
  const loaded = ref(false)
  const assistantTitle = computed(() => `${companyName.value} · ${FEATURE.assistantRole}`)
  const headerSubtitle = computed(() => assistantHeaderSubtitle(companyName.value))
  const welcomeMessage = computed(() => assistantIntroLine(companyName.value))
  const greetingMessage = computed(() => assistantGreeting(companyName.value))
  const flywheelTitleText = computed(() => flywheelTitle(companyName.value))
  const fabInitial = computed(() => fabChar(companyName.value))

  async function load() {
    const data = await fetchBranding()
    if (data.company_name) companyName.value = data.company_name
    if (data.tenant_domain) tenantDomain.value = data.tenant_domain
    const resolved = resolveTenantSiteUrl(data.tenant_domain || '', data.site_url)
    if (resolved) siteUrl.value = resolved
    loaded.value = true
  }

  onMounted(() => {
    void load()
  })

  return {
    companyName,
    tenantDomain,
    siteUrl,
    loaded,
    fabInitial,
    assistantTitle,
    headerSubtitle,
    welcomeMessage,
    greetingMessage,
    flywheelTitle: flywheelTitleText,
    load,
  }
}
