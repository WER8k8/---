/** 套餐展示：合并后端 TenantPlan 与营销文案，保证与配额/功能开关一致 */

export type ApiTenantPlan = {
  id: string
  name: string
  code: string
  price_monthly: number
  price_yearly: number
  max_users: number
  max_sites: number
  max_products: number
  max_ai_quota: number
  features: string
  is_active?: boolean
}

export type PlanFeatureItem = {
  name: string
  desc: string
  included: boolean
}

export type DisplayPlan = {
  id: string
  code: string
  name: string
  slogan: string
  priceMonthly: string
  priceAnnual: string
  annualSave: string
  badge: string
  featured: boolean
  suitable: string
  featureGroups: { title: string; items: PlanFeatureItem[] }[]
}

const PLAN_META: Record<
  string,
  { slogan: string; suitable: string; badge?: string; featured?: boolean }
> = {
  free: { slogan: '零成本体验核心功能', suitable: '个人用户 / 小微企业' },
  basic: { slogan: '团队入门级解决方案', suitable: '创业团队 / 小型企业' },
  pro: { slogan: '中小企业标准化方案', suitable: '成长型企业 / 专业团队', badge: '热销推荐', featured: true },
  enterprise: { slogan: '中大型企业完整方案', suitable: '中大型企业 / 跨国业务' },
  flagship: { slogan: '集团级定制解决方案', suitable: '大型集团 / 上市企业', badge: '尊享' },
}

function parseFeatures(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw || '[]')
    return Array.isArray(parsed) ? parsed.map(String) : []
  } catch {
    return []
  }
}

function fmtCount(n: number, unit: string, unlimitedAt = 999): string {
  if (n >= unlimitedAt) return '无限'
  return `${n.toLocaleString('zh-CN')}${unit}`
}

function yuanFromCents(cents: number): string {
  if (cents <= 0) return '0'
  return String(Math.round(cents / 100))
}

function annualMonthlyFromYearly(yearlyCents: number): string {
  if (yearlyCents <= 0) return '0'
  return String(Math.round(yearlyCents / 12 / 100))
}

function annualSave(monthlyCents: number, yearlyCents: number): string {
  const save = Math.max(0, monthlyCents * 12 - yearlyCents)
  return save > 0 ? String(Math.round(save / 100)) : '0'
}

function buildFeatureGroups(api: ApiTenantPlan, feats: string[]): DisplayPlan['featureGroups'] {
  const has = (k: string) => feats.includes(k)
  const sites = fmtCount(api.max_sites, ' 个站点')
  const ai = fmtCount(api.max_ai_quota, ' 次/月', 99999)
  const users = fmtCount(api.max_users, ' 人', 999)
  const products = fmtCount(api.max_products, ' 个产品', 99999)

  if (api.code === 'flagship') {
    return [
      {
        title: '站点与内容',
        items: [
          { name: '站点数量', desc: sites, included: true },
          { name: 'AI 调用配额', desc: ai, included: true },
          { name: '产品数量', desc: products, included: true },
        ],
      },
      {
        title: '部署与安全',
        items: [
          { name: '私有化部署', desc: '可选', included: true },
          { name: '白标品牌', desc: has('white_label') ? '支持' : '—', included: has('white_label') },
          { name: '开放 API', desc: has('api') ? '全开放' : '—', included: has('api') },
        ],
      },
      {
        title: '全球化与增长',
        items: [
          { name: '多语言/全球化', desc: has('globalization') ? '全功能' : '—', included: has('globalization') },
          { name: '国际询盘', desc: has('international') ? '全平台' : '—', included: has('international') },
          { name: 'SEO 矩阵', desc: has('seo') ? '全功能' : '—', included: has('seo') },
        ],
      },
    ]
  }

  return [
    {
      title: '站点与内容',
      items: [
        { name: '站点数量', desc: sites, included: api.max_sites > 0 },
        { name: 'AI 调用配额', desc: ai, included: api.max_ai_quota > 0 },
        { name: '产品数量', desc: products, included: api.max_products > 0 },
      ],
    },
    {
      title: 'SEO 与内容',
      items: [
        { name: 'SEO 优化', desc: has('seo') ? '已包含' : '—', included: has('seo') },
        { name: '数据分析', desc: has('analytics') ? '已包含' : '—', included: has('analytics') },
        { name: '内容工厂', desc: has('content') ? '已包含' : '—', included: has('content') },
      ],
    },
    {
      title: '全球化',
      items: [
        { name: '多语言/全球化', desc: has('globalization') ? '已包含' : '—', included: has('globalization') },
        { name: '国际询盘采集', desc: has('international') ? '已包含' : '—', included: has('international') },
      ],
    },
    {
      title: '平台与支持',
      items: [
        { name: '多用户', desc: users, included: api.max_users > 0 },
        { name: 'AI 能力包', desc: has('ai') ? '高级模型' : '基础', included: has('ai') || api.code === 'free' },
        { name: '白标品牌', desc: has('white_label') ? '支持' : '—', included: has('white_label') },
        { name: '开放 API', desc: has('api') ? '支持' : '—', included: has('api') },
      ],
    },
  ]
}

export function apiPlanToDisplayPlan(api: ApiTenantPlan): DisplayPlan {
  const meta = PLAN_META[api.code] || { slogan: api.name, suitable: '按需选择' }
  const feats = parseFeatures(api.features)
  const isCustom = api.code === 'flagship'

  return {
    id: api.id,
    code: api.code,
    name: api.name,
    slogan: meta.slogan,
    priceMonthly: isCustom ? '定制' : yuanFromCents(api.price_monthly),
    priceAnnual: isCustom ? '定制' : annualMonthlyFromYearly(api.price_yearly),
    annualSave: isCustom ? '—' : annualSave(api.price_monthly, api.price_yearly),
    badge: meta.badge || '',
    featured: Boolean(meta.featured),
    suitable: meta.suitable,
    featureGroups: buildFeatureGroups(api, feats),
  }
}

export function buildCompareRows(plans: DisplayPlan[], apis: ApiTenantPlan[]) {
  const byCode = Object.fromEntries(apis.map((p) => [p.code, p]))
  const codes = plans.map((p) => p.code)

  const cell = (code: string, pick: (a: ApiTenantPlan) => string | boolean) => {
    const api = byCode[code]
    if (!api) return '—'
    return pick(api)
  }

  return [
    {
      title: '站点与内容',
      rows: [
        {
          name: '站点数量',
          cells: codes.map((c) => cell(c, (a) => fmtCount(a.max_sites, ' 个', 999))),
        },
        {
          name: 'AI 调用/月',
          cells: codes.map((c) => cell(c, (a) => fmtCount(a.max_ai_quota, ' 次', 99999))),
        },
        {
          name: '产品数量',
          cells: codes.map((c) => cell(c, (a) => fmtCount(a.max_products, ' 个', 99999))),
        },
      ],
    },
    {
      title: '功能模块',
      rows: [
        {
          name: 'SEO',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('seo'))),
        },
        {
          name: '数据分析',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('analytics'))),
        },
        {
          name: '全球化',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('globalization'))),
        },
        {
          name: '国际询盘',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('international'))),
        },
        {
          name: '白标品牌',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('white_label'))),
        },
        {
          name: '开放 API',
          cells: codes.map((c) => cell(c, (a) => parseFeatures(a.features).includes('api'))),
        },
      ],
    },
    {
      title: '平台',
      rows: [
        {
          name: '多用户',
          cells: codes.map((c) => cell(c, (a) => fmtCount(a.max_users, ' 人', 999))),
        },
      ],
    },
  ]
}
