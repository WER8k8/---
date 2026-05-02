import { useApi } from './useApi'

interface DashboardData {
  total_keywords: number
  ranked_keywords: number
  avg_rank: number | null
  ai_optimized_pages: number
  llms_txt_generated: boolean
  last_audit_score: number | null
  keyword_trend: Array<{ date: string; avg_rank: number | null }>
  page_coverage: Array<{ type: string; count: number }>
}

interface KeywordRanking {
  keyword: string
  slug: string
  search_volume: number
  difficulty: string
  current_rank: number | null
  target_rank: string | null
  rank_change: number | null
  trend: Array<{ date: string; rank: number | null; engine: string }>
  suggestions: string[]
}

interface OptimizeRequest {
  content: string
  opt_type: 'title' | 'description' | 'alt_text' | 'content'
  keywords: string[]
  model?: string
}

interface OptimizeResponse {
  optimized_content: string
  changes: string[]
  token_usage: number
  cost: number
  technical_params_preserved: boolean
}

interface ValidateContentResponse {
  is_valid: boolean
  issues: Array<{ param: string | null; original: string | null; optimized: string | null; issue: string }>
  technical_params_preserved: boolean
}

interface ExtractParamsResponse {
  technical_params: Record<string, string>
  found: boolean
}

interface LlmsGenerateRequest {
  sections?: Array<{ type: string; title?: string; content?: string; url?: string; description?: string; question?: string; answer?: string }>
  include_ai_instructions?: boolean
}

interface LlmsGenerateResponse {
  content: string
  line_count: number
  size_bytes: number
}

interface LlmsValidateResponse {
  is_valid: boolean
  issues: Array<{ severity: string; message: string }>
  section_count: number
}

interface LlmsTemplateResponse {
  template: string
  available_sections: string[]
}

interface SeoPageSummary {
  id: string
  title: string
  slug: string
  meta_title: string | null
  meta_description: string | null
  ai_optimized: boolean
  status: string
  view_count: number
  updated_at: string | null
}

interface KeywordGroup {
  group: string
  count: number
  ranked: number
}

export function useSeo() {
  const { request, useRequest } = useApi()

  function getDashboard() {
    return useRequest<DashboardData>('/seo/dashboard')
  }

  async function getKeywordRanking(keywordId: string): Promise<KeywordRanking> {
    return request<KeywordRanking>(`/seo/keyword-ranking/${keywordId}`)
  }

  function getKeywordGroups() {
    return useRequest<KeywordGroup[]>('/seo/keyword-groups')
  }

  function getSeoPagesSummary() {
    return useRequest<SeoPageSummary[]>('/seo/seo-pages-summary')
  }

  async function optimizeContent(req: OptimizeRequest): Promise<OptimizeResponse> {
    return request<OptimizeResponse>('/seo/optimize-content', { method: 'POST', body: req })
  }

  async function validateContent(original: string, optimized: string): Promise<ValidateContentResponse> {
    return request<ValidateContentResponse>('/seo/validate-content', { method: 'POST', body: { original, optimized } })
  }

  async function extractParams(content: string): Promise<ExtractParamsResponse> {
    return request<ExtractParamsResponse>('/seo/extract-params', { method: 'POST', body: { content } })
  }

  async function generateLlmsTxt(req: LlmsGenerateRequest): Promise<LlmsGenerateResponse> {
    return request<LlmsGenerateResponse>('/seo/generate-llms-txt', { method: 'POST', body: req })
  }

  async function validateLlmsTxt(content: string): Promise<LlmsValidateResponse> {
    return request<LlmsValidateResponse>('/seo/validate-llms-txt', { method: 'POST', body: { content } })
  }

  function getTemplate() {
    return useRequest<LlmsTemplateResponse>('/seo/llms-txt-template')
  }

  async function runAudit(url: string, auditType: string = 'full') {
    return request('/seo/run-audit', { method: 'POST', body: { url, audit_type: auditType } })
  }

  return {
    getDashboard,
    getKeywordRanking,
    getKeywordGroups,
    getSeoPagesSummary,
    optimizeContent,
    validateContent,
    extractParams,
    generateLlmsTxt,
    validateLlmsTxt,
    getTemplate,
    runAudit,
  }
}
