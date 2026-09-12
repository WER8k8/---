/** 访客 IP 段 → 国家/语言；外贸站与旺财 UI 自动跟随 */

import { ref, computed, type Ref } from 'vue';
import { useRoute, useRuntimeConfig, useRequestHeaders, useState } from 'nuxt/app';
import { resolveTenantPreviewDomain } from '../utils/tenant-preview-domain';
import { readCachedVisitorContext, writeCachedVisitorContext } from '../utils/visitorContextCache';
import { fetchVisitorContextPayload } from '../utils/visitorContextFetch';
import { readStoredTenantLanguage, writeStoredTenantLanguage } from './useTenantLanguagePicker';

export type VisitorContactChannel = {
  channel_type: string
  value: string
  label: string
  im_link: string
}

export type VisitorContext = {
  tenant_domain?: string
  country_code: string
  language: string
  language_name?: string
  site_ui: Record<string, string>
  wangcai_ui: Record<string, string>
  contact_channels?: VisitorContactChannel[]
  contacts?: Record<string, string>
  cn_compliant_only?: boolean
  wangcai_trade_qa_enabled?: boolean
  supported_languages?: Array<{ code: string; name: string }>
  site_content_localized?: {
    brand?: Record<string, string>
    home?: Record<string, string | unknown[]>
    about?: Record<string, string | unknown[]>
    products?: Record<string, string | unknown[]>
  }
}

const FALLBACK_SITE_UI: Record<string, string> = {
  loading: 'Loading…',
  site_unavailable: 'Site unavailable',
  nav_home: 'Home',
  nav_products: 'Products',
  nav_solutions: 'Solutions',
  nav_applications: 'Applications',
  nav_about: 'About',
  nav_video: 'Video',
  nav_qa: 'Buyer Q&A',
  nav_contact: 'Contact',
  cta_primary: 'Get a Quote',
  cta_secondary: 'Contact Us',
  stats_eyebrow: 'What We Do',
  stats_title: 'Trusted Manufacturing at Scale',
  section_stages_eyebrow: 'Project path',
  section_stages_title: 'Can you take my order at this stage?',
  section_stages_desc: 'RFQ → sample → pilot → volume — structured for how buyers decide.',
  section_solutions: 'Industry Solutions',
  section_solutions_desc: 'Solutions mapped to buyer jobs — not warehouse aisles.',
  section_knowledge_eyebrow: 'Technical content',
  section_knowledge_title: 'Answer search intent before the RFQ',
  section_knowledge_desc: 'Guides that prove spec fluency — then route to inquiry.',
  section_cta_title: 'Ready to start?',
  section_cta_desc: 'Send specs or drawings — we reply with scope and next steps.',
  section_products: 'Products',
  section_contact: 'Contact Us',
  tel_label: 'Tel',
  email_label: 'E-mail',
  whatsapp_label: 'WhatsApp',
  hero_since: 'Since {year}',
  section_categories: 'Product Classification',
  section_categories_desc: 'Professional export product lines',
  section_products_default: 'Our Products',
  section_products_desc: 'Hot products for export inquiry',
  inquiry_link: 'Inquiry →',
  section_about: 'About {name}',
  mission: 'Mission',
  vision: 'Vision',
  company_history: 'Company History',
  video_center: 'Video Center',
  factory_label: 'Factory',
  footer_quick_links: 'Quick Links',
  footer_contact: 'Contact',
  why_choose_us: 'Why Choose Us',
  applications_title_default: 'What Are You Insulating?',
  tenant_not_found: 'Tenant not found',
  load_failed: 'Load failed',
  contact_wechat_label: 'WeChat',
  contact_qq_label: 'QQ',
  menu_open: 'Open menu',
  menu_close: 'Close menu',
  hero_placeholder_hint: 'Professional manufacturing · Export ready',
  mobile_quick_actions: 'Quick contact',
  form_name: 'Your Name',
  form_email: 'Email',
  form_phone: 'Phone / WhatsApp',
  form_phone_cn: 'Mobile',
  form_product: 'Product / Specs',
  form_message: 'Inquiry details',
  form_submit: 'Submit Inquiry',
  form_submitting: 'Submitting…',
  form_hint: 'We reply within 24 hours on business days.',
  form_required_name: 'Please enter your name',
  form_required_contact: 'Please enter email or phone',
  form_required_message: 'Please enter inquiry details',
  form_success: 'Submitted! We will contact you soon.',
  form_error: 'Submission failed. Please try again.',
  nav_downloads: 'Downloads',
  section_downloads: 'Download Center',
  section_downloads_desc: 'Brochures, datasheets and certificates',
  downloads_empty: 'No downloadable files yet. Contact us for datasheets.',
  view_product: 'View details',
  products_empty: 'No products listed yet.',
  products_search_label: 'Search products',
  products_search_placeholder: 'Search by name, category or specs…',
  products_clear_search: 'Clear',
  products_clear_filters: 'Clear filters',
  products_no_match: 'No products match your search.',
  products_sort_label: 'Sort products',
  products_sort_default: 'Default order',
  products_sort_name_asc: 'Name A → Z',
  products_sort_name_desc: 'Name Z → A',
  products_spec_filter: 'Quick spec',
  products_spec_all: 'All specs',
  product_not_found: 'Product not found',
  download_datasheet: 'Download datasheet',
  lang_picker_label: 'Language',
  lang_more: 'More languages',
  lang_tier2_disclaimer:
    'Auto-translated view is for marketing text only. Technical specs remain in English or source language.',
  footer_copyright: 'Copyright © {year} {name}. All Rights Reserved.',
}

const FALLBACK_WANGCAI_UI: Record<string, string> = {
  panel_sub: 'Export sales · Quick reply',
  tab_contact: 'Contact',
  tab_ask: 'Trade Q&A',
  panel_tip_default: 'Tell us quantity, specs & destination port — we reply within 24 hours.',
  contact_wa_sub: 'International chat',
  contact_wechat_sub_copied: 'ID copied!',
  contact_email_sub: 'Email',
  contact_call_sub: 'Call',
  contact_form_sub: 'Full factory details',
  chat_hint: 'Not sure about HS codes or export markets? Ask here — 20 categories × 50 countries.',
  chat_loading: 'Checking trade data…',
  ask_placeholder: 'e.g. Best markets for rock wool?',
  ask_button: 'Ask',
  error_retry: 'Sorry — try again or use the contact form.',
  error_network: 'Network error. Please use WhatsApp or the contact form.',
  mascot_aria: 'sales assistant',
  bubble_1: 'Hi! {name} export team here — need a quotation?',
  bubble_2: 'Ask me export markets & HS codes — tap Trade Q&A.',
  bubble_3: 'Tap for WhatsApp, email or phone.',
  bubble_4: 'Free sample & datasheet for qualified projects.',
  bubble_product: 'Looking for {product}? Ask us!',
}

function applyContext(
  target: Ref<VisitorContext | null>,
  ctx: VisitorContext,
  domain?: string,
) {
  target.value = ctx
  if (import.meta.client && domain && ctx.country_code && ctx.language) {
    writeCachedVisitorContext(domain, ctx)
    localStorage.setItem('buyer_country', ctx.country_code)
  }
}

function buildFallbackContext(language: string, countryCode = 'US'): VisitorContext {
  return {
    country_code: countryCode,
    language: language.slice(0, 5),
    site_ui: FALLBACK_SITE_UI,
    wangcai_ui: FALLBACK_WANGCAI_UI,
    wangcai_trade_qa_enabled: countryCode !== 'CN',
  }
}

function resolveFetchLanguage(
  domain: string,
  overrides?: { country?: string; language?: string },
  routeLanguage?: string | null,
): string | undefined {
  const explicit = overrides?.language?.trim().toLowerCase()
  if (explicit) return explicit.slice(0, 5)
  const fromRoute = (routeLanguage || '').trim().toLowerCase()
  if (fromRoute) {
    if (import.meta.client) writeStoredTenantLanguage(domain, fromRoute.slice(0, 5))
    return fromRoute.slice(0, 5)
  }
  if (import.meta.client) {
    const stored = readStoredTenantLanguage(domain)
    if (stored?.trim()) return stored.trim().toLowerCase().slice(0, 5)
  }
  return undefined
}

export function useVisitorLocale(tenantDomain: () => string, apiBase: () => string) {
  const context = useState<VisitorContext | null>('visitorContext', () => null)
  const route = useRoute()

  const loading = ref(false)
  const ready = ref(false)

  const siteUi = computed(() => context.value?.site_ui || FALLBACK_SITE_UI)
  const wangcaiUi = computed(() => context.value?.wangcai_ui || FALLBACK_WANGCAI_UI)
  const language = computed(() => context.value?.language || 'en')
  const countryCode = computed(() => context.value?.country_code || 'US')
  const contactChannels = computed(() => context.value?.contact_channels || [])
  const cnCompliantOnly = computed(() => {
    if (context.value?.cn_compliant_only !== undefined) {
      return context.value.cn_compliant_only
    }
    return countryCode.value === 'CN'
  })
  const tradeQaEnabled = computed(() => {
    if (context.value?.wangcai_trade_qa_enabled !== undefined) {
      return context.value.wangcai_trade_qa_enabled
    }
    return !cnCompliantOnly.value
  })
  const publicContacts = computed(() => context.value?.contacts || {})
  const supportedLanguages = computed(() => context.value?.supported_languages || [])

  function buildVisitorContextUrl(
    domain: string,
    overrides?: { country?: string; language?: string },
    effectiveLanguage?: string,
  ) {
    const params = new URLSearchParams();
    if (overrides?.country) params.set('country', overrides.country);
    if (effectiveLanguage) params.set('language', effectiveLanguage);
    const qs = params.toString() ? `?${params}` : '';

    const config = useRuntimeConfig();
    const host = import.meta.server
      ? (config.public.apiHost as string) || 'http://localhost:8001'
      : '';
    const base = host || apiBase().replace(/\/$/, '');
    const path = `/public/tenants/${encodeURIComponent(domain)}/visitor-context${qs}`;
    return host ? `${base}/api/v1${path}` : `${base}${path}`;
  }

  function buildVisitorContextHeaders(effectiveLanguage?: string) {
    const headers: Record<string, string> = {};
    if (import.meta.server) {
      const reqHeaders = useRequestHeaders(['cf-ipcountry', 'accept-language', 'x-visitor-country']);
      if (reqHeaders['cf-ipcountry']) headers['CF-IPCountry'] = reqHeaders['cf-ipcountry'];
      if (reqHeaders['accept-language']) headers['Accept-Language'] = reqHeaders['accept-language'];
      if (reqHeaders['x-visitor-country']) headers['X-Visitor-Country'] = reqHeaders['x-visitor-country'];
    } else if (typeof navigator !== 'undefined' && !effectiveLanguage) {
      headers['Accept-Language'] = navigator.language || 'en';
    }
    return headers;
  }

  async function fetchVisitorContext(
    overrides?: { country?: string; language?: string },
    domainOverride?: string,
    options?: { background?: boolean; cancelInflight?: boolean },
  ) {
    const domain = domainOverride || tenantDomain()
    if (!domain) return

    const effectiveLanguage = resolveFetchLanguage(
      domain,
      overrides,
      typeof route.query.language === 'string' ? route.query.language : null,
    )

    if (overrides?.language && context.value) {
      context.value = {
        ...context.value,
        language: (effectiveLanguage || overrides.language).slice(0, 5),
      }
    }

    if (!overrides?.country && import.meta.client) {
      const cached = readCachedVisitorContext(domain, effectiveLanguage)
        || (effectiveLanguage ? null : readCachedVisitorContext(domain, readStoredTenantLanguage(domain) || undefined))
      if (cached && (!effectiveLanguage || cached.language === effectiveLanguage)) {
        context.value = cached
      }
    }

    const background = options?.background === true
    const hasVisibleContext = Boolean(context.value)
    if (!background || !hasVisibleContext) {
      loading.value = true
    }

    const url = buildVisitorContextUrl(domain, overrides, effectiveLanguage)
    const headers = buildVisitorContextHeaders(effectiveLanguage)

    try {
      const result = await fetchVisitorContextPayload<VisitorContext>(url, headers, {
        cancelPrevious: options?.cancelInflight === true,
      })
      if (result.ok && result.data) {
        applyContext(context, result.data, domain)
      } else if (!context.value && effectiveLanguage) {
        context.value = buildFallbackContext(effectiveLanguage)
        writeCachedVisitorContext(domain, context.value)
      }
    } catch {
      if (!context.value) {
        context.value = buildFallbackContext(effectiveLanguage || 'en')
      }
    } finally {
      loading.value = false
      ready.value = true
    }
  }

  function tSite(key: string, vars?: Record<string, string>): string {
    let text = siteUi.value[key] || FALLBACK_SITE_UI[key] || key
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        text = text.replace(`{${k}}`, v)
      }
    }
    return text
  }

  function tWangcai(key: string, vars?: Record<string, string>): string {
    let text = wangcaiUi.value[key] || FALLBACK_WANGCAI_UI[key] || key
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        text = text.replace(`{${k}}`, v)
      }
    }
    return text
  }

  function prefetchLanguages(codes: string[]) {
    if (!import.meta.client) return
    const domain = tenantDomain()
    if (!domain) return
    const current = context.value?.language
    const run = async () => {
      for (const code of codes) {
        if (!code || code === current) continue
        if (readCachedVisitorContext(domain, code)) continue
        const url = buildVisitorContextUrl(domain, { language: code }, code.slice(0, 5))
        const headers = buildVisitorContextHeaders(code.slice(0, 5))
        const result = await fetchVisitorContextPayload<VisitorContext>(url, headers, {
          cancelPrevious: false,
          isolated: true,
        })
        if (result.ok && result.data) {
          writeCachedVisitorContext(domain, result.data)
        }
      }
    }
    const idle = window.requestIdleCallback ?? ((cb: () => void) => window.setTimeout(cb, 1500))
    idle(() => {
      void run()
    })
  }

  return {
    context,
    loading,
    ready,
    siteUi,
    wangcaiUi,
    language,
    countryCode,
    contactChannels,
    cnCompliantOnly,
    publicContacts,
    tradeQaEnabled,
    supportedLanguages,
    fetchVisitorContext,
    prefetchLanguages,
    tSite,
    tWangcai,
  }
}

export function resolveTenantDomainFromRoute(): string | null {
  const route = useRoute()
  const fromQuery = resolveTenantPreviewDomain(
    route.query as Record<string, unknown>,
    import.meta.client && typeof window !== 'undefined' ? window.location.search : '',
  )
  if (fromQuery) return fromQuery
  if (import.meta.server) {
    const host = (useRequestHeaders()['host'] || '').split(':')[0]?.toLowerCase() || ''
    const prod = host.match(/^([a-z0-9][a-z0-9-]+)\.(youding-saas|youding)\.com$/)
    if (prod) return prod[1]
    const local = host.match(/^([a-z0-9][a-z0-9-]+)\.localhost$/)
    if (local) return local[1]
  }
  if (import.meta.client && typeof window !== 'undefined') {
    const host = window.location.hostname.toLowerCase()
    const prod = host.match(/^([a-z0-9][a-z0-9-]+)\.(youding-saas|youding)\.com$/)
    if (prod) return prod[1]
    const local = host.match(/^([a-z0-9][a-z0-9-]+)\.localhost$/)
    if (local) return local[1]
  }
  return null
}
