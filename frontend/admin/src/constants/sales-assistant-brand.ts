/** 功能模块名（与租户公司名无关）；助手话术以租户 company_name 为准 */

export const FEATURE = {
  flywheel: '卖货飞轮',
  assistantRole: '卖货智能助手',
  researchBrief: '市场研究简报',
  executionLayer: '卖货执行',
  deepResearchJob: '深度研究任务',
  roadmap: '能力路线图',
  salesMenu: '智能销售',
  siteBuilder: 'AI 智能建站',
  siteBuilderEngine: '智能建站引擎',
} as const

/** @deprecated 使用 FEATURE；保留别名避免大范围替换 */
export const BRAND = {
  productName: FEATURE.flywheel,
  assistantName: FEATURE.assistantRole,
  researchBrief: FEATURE.researchBrief,
  executionLayer: FEATURE.executionLayer,
  deepResearchJob: FEATURE.deepResearchJob,
  roadmap: FEATURE.roadmap,
  salesMenu: FEATURE.salesMenu,
} as const

const DEFAULT_COMPANY = '您的公司'

export function normalizeCompanyName(name?: string | null): string {
  const t = String(name || '').trim()
  return t || DEFAULT_COMPANY
}

export function assistantIntroLine(companyName?: string | null): string {
  const co = normalizeCompanyName(companyName)
  return `我是${co}的卖货智能助手。可以说找采购商、写开发信、谈单话术、出口可行性，或问「本周线索复盘」——我会直接给可执行建议。`
}

export function assistantGreeting(companyName?: string | null): string {
  const co = normalizeCompanyName(companyName)
  return `您好，我是财旺，${co}的卖货助手。可问「你会干什么」了解我能帮什么，或直接说出口可行性、找买家、询盘回复等。`
}

export function assistantHeaderSubtitle(companyName?: string | null): string {
  const co = normalizeCompanyName(companyName)
  return `${co} · 卖货智能助手 — 找客、开发信、谈单与出口研判；发送/发布前需您确认。`
}

export function flywheelTitle(companyName?: string | null): string {
  const co = normalizeCompanyName(companyName)
  return `${co} · ${FEATURE.flywheel}`
}

const SKILL_LABELS: Record<string, string> = {
  find_buyers: '自动找客',
  outreach_letter_pack: '开发信',
  negotiation_draft: '谈单话术',
  lead_content_pack: '获客内容包',
  geo_content_matrix: 'GEO 内容矩阵',
  china_platform_content: '国内平台内容编排',
  geo_submit_pack: 'GEO 提交',
  matrix_publish: '矩阵发布',
  inquiry_score: '询盘评分',
  inquiry_draft: '询盘回复',
  export_feasibility: '出口可行性',
  blue_ocean: '蓝海市场',
  hs_lookup: 'HS 编码',
  weekly_lead_report: '线索周报',
  market_research: '市场研究',
  sync_feedback: '同步反馈',
  osint_check: '客户背调',
  website_icp: '官网 ICP',
  proforma_invoice: '形式发票 PI',
  prospect_clean: '潜客清洗',
}

export function skillLabel(skillId?: string): string {
  if (!skillId) return '任务'
  return SKILL_LABELS[skillId] || skillId.replace(/_/g, ' ')
}

export function gapSkillLabel(g: { id?: string; group_name?: string; accio_analog?: string }): string {
  return g.group_name || skillLabel(g.id) || g.accio_analog || g.id || '待上线能力'
}

/** 将后端偶发的内部代号替换为客户向表述 */
export function polishCustomerText(text: string, companyName?: string | null): string {
  if (!text) return text
  const co = normalizeCompanyName(companyName)
  return text
    .replace(/AccioWork/gi, FEATURE.executionLayer)
    .replace(/Accio/gi, FEATURE.executionLayer)
    .replace(/DeerFlow/gi, '深度研究')
    .replace(/Research Brief/gi, FEATURE.researchBrief)
    .replace(/UBrain(-X)?/gi, FEATURE.assistantRole)
    .replace(/优丁助手/g, `${co}的卖货智能助手`)
    .replace(/优丁建材/g, co)
    .replace(/优丁/g, co)
    .replace(/编排\+Accio/g, '智能编排')
    .replace(/编排\+卖货执行/g, '智能编排')
}
