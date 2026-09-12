/**
 * 套餐功能矩阵 — 与 backend/app/api/v1/admin_bff/plan_catalog.py 同源
 * Plan Gate：backend/app/services/plan_gate_service.py · FEATURE_MIN_PLAN
 * 对外文案：docs/marketing/plan-copy-deck.md
 */

export const PLAN_ORDER = ['trial', 'starter', 'pro', 'enterprise'] as const;
export type PlanId = (typeof PLAN_ORDER)[number];

/** 营销 plan_id → 注册页 TenantPlan.code */
export const PLAN_REGISTER_CODE: Record<PlanId, string> = {
  trial: 'free',
  starter: 'basic',
  pro: 'pro',
  enterprise: 'enterprise',
};

/** 注册页 code → 营销 plan_id */
export const REGISTER_CODE_TO_PLAN: Record<string, PlanId> = {
  free: 'trial',
  basic: 'starter',
  pro: 'pro',
  enterprise: 'enterprise',
};

/** 与 plan_catalog.PLAN_FEATURES 一致（静态兜底；运行时可用 API 覆盖 features 列表） */
export const PLAN_CATALOG: Record<
  PlanId,
  { name: string; features: string[]; tagline: string; featured?: boolean }
> = {
  trial: {
    name: '体验版',
    tagline: '7 天试用，完成「绑域 → 发首条 → 收首询盘」',
    features: ['domain_bind', 'publish_limited', 'inquiry_limited', 'geo_submit_limited'],
  },
  starter: {
    name: '启航版',
    tagline: '独立站 + 基础多平台发布，适合刚出海的小团队',
    features: ['domain_bind', 'publish', 'inquiry', 'geo_submit_limited'],
  },
  pro: {
    name: '专业版',
    tagline: 'SEO + GEO 一体：AI 大模型收录追踪、内容矩阵与询盘 inbox',
    featured: true,
    features: [
      'domain_bind',
      'publish',
      'inquiry',
      'im',
      'seo_matrix',
      'geo_engine',
      'geo_content_matrix',
      'geo_submit_pack',
      'media_factory',
      'video_matrix',
    ],
  },
  enterprise: {
    name: '企业版',
    tagline: '含专业版 GEO + 收录巡检与白标审计，适合多账号与送检',
    features: [
      'domain_bind',
      'publish',
      'inquiry',
      'im',
      'seo_matrix',
      'geo_engine',
      'geo_content_matrix',
      'geo_submit_pack',
      'geo_monitor',
      'media_factory',
      'video_matrix',
      'egress_ip',
      'white_label',
      'audit_log',
    ],
  },
};

export const FEATURE_LABELS: Record<string, string> = {
  domain_bind: '独立域绑定',
  publish_limited: '多平台发布（5+5）',
  publish: '多平台发布（5+5）',
  inquiry_limited: '询盘 inbox',
  inquiry: '询盘 inbox',
  im: 'IM 配置（WhatsApp / 企微等）',
  seo_matrix: 'SEO 矩阵',
  geo_engine: 'GEO 引擎（AI 大模型收录追踪）',
  geo_content_matrix: 'GEO 内容矩阵（母版 + 多平台变体）',
  geo_submit_pack: 'GEO 执行清单 / AI 引用优化',
  geo_submit_limited: 'GEO 执行清单（试用）',
  geo_monitor: 'GEO 收录巡检与告警（企业版）',
  media_factory: '多媒体内容工厂',
  video_matrix: '视频矩阵分发',
  ai_quota: 'Token / AI 额度',
  egress_ip: '独立出口 IP（Plan Gate）',
  white_label: '白标登录',
  audit_log: '操作审计',
};

export type MatrixCell = true | false | 'limit' | 'low' | 'mid' | 'high' | 'custom';

export type PricingMatrixRow = {
  group?: string;
  feature: string;
  featureKey?: string;
  trial: MatrixCell;
  starter: MatrixCell;
  pro: MatrixCell;
  enterprise: MatrixCell;
};

function planHas(planId: PlanId, key: string): boolean {
  return PLAN_CATALOG[planId].features.includes(key);
}

function cellForFeature(planId: PlanId, key: string): MatrixCell {
  if (key === 'publish') {
    if (planId === 'trial') return planHas(planId, 'publish_limited') ? 'limit' : false;
    return planHas(planId, 'publish');
  }
  if (key === 'inquiry') {
    if (planId === 'trial') return planHas(planId, 'inquiry_limited') ? 'limit' : false;
    return planHas(planId, 'inquiry');
  }
  if (key === 'geo_submit_pack') {
    if (planHas(planId, 'geo_submit_pack')) return true;
    if (planHas(planId, 'geo_submit_limited')) return 'limit';
    return false;
  }
  if (key === 'ai_quota') {
    if (planId === 'trial') return 'low';
    if (planId === 'starter') return 'mid';
    if (planId === 'pro') return 'high';
    return 'custom';
  }
  return planHas(planId, key);
}

/** 完整功能对比表 — 与 plan_catalog + plan_gate 对齐 */
export function buildPricingMatrix(): {
  columns: { id: PlanId; label: string }[];
  rows: PricingMatrixRow[];
} {
  const columns = PLAN_ORDER.map((id) => ({ id, label: PLAN_CATALOG[id].name }));
  const rowKeys: { group: string; key: string }[] = [
    { group: '出海基础', key: 'domain_bind' },
    { group: '出海基础', key: 'publish' },
    { group: '出海基础', key: 'inquiry' },
    { group: '获客与增长', key: 'im' },
    { group: 'GEO · 生成式引擎优化', key: 'geo_engine' },
    { group: 'GEO · 生成式引擎优化', key: 'geo_content_matrix' },
    { group: 'GEO · 生成式引擎优化', key: 'geo_submit_pack' },
    { group: 'GEO · 生成式引擎优化', key: 'geo_monitor' },
    { group: '获客与增长', key: 'seo_matrix' },
    { group: '获客与增长', key: 'media_factory' },
    { group: '获客与增长', key: 'video_matrix' },
    { group: 'AI 与用量', key: 'ai_quota' },
    { group: '企业级', key: 'egress_ip' },
    { group: '企业级', key: 'white_label' },
    { group: '企业级', key: 'audit_log' },
  ];

  let lastGroup = '';
  const rows: PricingMatrixRow[] = rowKeys.map(({ group, key }) => {
    const row: PricingMatrixRow = {
      feature: FEATURE_LABELS[key] || key,
      featureKey: key,
      trial: cellForFeature('trial', key),
      starter: cellForFeature('starter', key),
      pro: cellForFeature('pro', key),
      enterprise: cellForFeature('enterprise', key),
    };
    if (group !== lastGroup) {
      row.group = group;
      lastGroup = group;
    }
    return row;
  });

  return { columns, rows };
}

export function matrixCellLabel(cell: MatrixCell): string {
  if (cell === true) return '✓';
  if (cell === 'limit') return '试用';
  if (cell === 'low') return '低';
  if (cell === 'mid') return '中';
  if (cell === 'high') return '高';
  if (cell === 'custom') return '定制';
  return '—';
}

export function matrixCellClass(cell: MatrixCell): string {
  if (cell === true) return 'cell-yes';
  if (cell === 'limit' || cell === 'low' || cell === 'mid' || cell === 'high') return 'cell-limit';
  if (cell === 'custom') return 'cell-yes';
  return 'cell-no';
}

/** 分档展示价（分 → 元；与 seed TenantPlan 一致，注册页同源） */
export const PLAN_PRICING_CENTS: Record<
  PlanId,
  { monthly: number; yearly: number; registerCode: string }
> = {
  trial: { monthly: 0, yearly: 0, registerCode: 'free' },
  starter: { monthly: 29900, yearly: 299000, registerCode: 'basic' },
  pro: { monthly: 69900, yearly: 699000, registerCode: 'pro' },
  enterprise: { monthly: 199900, yearly: 1999000, registerCode: 'enterprise' },
};

export function formatPlanPrice(planId: PlanId, cycle: 'monthly' | 'yearly'): string {
  const p = PLAN_PRICING_CENTS[planId];
  if (p.monthly <= 0) return '¥0';
  if (cycle === 'monthly') return `¥${Math.round(p.monthly / 100)}`;
  const perMonth = Math.round(p.yearly / 12 / 100);
  return `¥${perMonth}`;
}

export function planPriceSuffix(planId: PlanId, cycle: 'monthly' | 'yearly'): string {
  if (PLAN_PRICING_CENTS[planId].monthly <= 0) return '/ 7 天试用';
  return cycle === 'yearly' ? '/ 月 · 年付' : '/ 月';
}

export function planFeatureBullets(planId: PlanId): string[] {
  const feats = PLAN_CATALOG[planId].features;
  const labels = feats.map((k) => {
    if (k === 'publish_limited') return '多平台发布（试用配额）';
    if (k === 'inquiry_limited') return '询盘 inbox（试用配额）';
    return FEATURE_LABELS[k] || k;
  });
  if (planId === 'pro') {
    return [
      '含启航版能力',
      'GEO 引擎 · AI 大模型收录',
      'GEO 内容矩阵 + 执行清单',
      ...labels.filter((l) => !l.includes('独立域') && !l.includes('GEO')),
    ];
  }
  if (planId === 'enterprise') {
    return ['含专业版 GEO 能力', 'GEO 收录巡检与告警', '白标登录', '操作审计', '独立出口 IP', '专属支持'];
  }
  return labels;
}

export const PLATFORM_PLANS = PLAN_ORDER.map((id) => ({
  id,
  name: PLAN_CATALOG[id].name,
  tagline: PLAN_CATALOG[id].tagline,
  featured: Boolean(PLAN_CATALOG[id].featured),
}));
