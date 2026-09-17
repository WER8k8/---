/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * /platform SaaS 营销页文案 — 与 plan-copy-deck.md 同源
 * Admin /landing 后续对齐时复用本模块（MKT-PLATFORM-02）
 */
import {
  PLATFORM_PLANS,
  buildPricingMatrix,
  matrixCellLabel,
  planFeatureBullets,
  type MatrixCell,
} from './plan-catalog';

export { matrixCellLabel, matrixCellClass, type MatrixCell } from './plan-catalog';

export const PLATFORM_COPY = {
  hero: {
    eyebrow: '建材外贸 · 专注轻集料 / 保温 / 橡塑出海',
    h1: '优丁 — 外贸卖家的出海工作台',
    sub: '不是功能堆叠的后台。帮建材厂把询盘、发品、独立站收进一处，登录 30 秒就知道今天该干什么。',
    ctaPrimary: '免费试用 7 天',
    ctaSecondary: '进入工作台',
    ctaPartner: '省代合作',
    trialNote: '无需信用卡 · 完成绑域 → 发首条 → 收首询盘',
  },
  trust: ['7 天完成出海三步', '建材外贸行业场景', '四档套餐按需升级', '超管→省代→市代→卖家'],
  capabilities: [
    {
      id: 'leads',
      title: '获客 inbox',
      metric: '询盘 + IM 一条线',
      desc: 'Alibaba、独立站、SEO 矩阵来的线索进同一个 inbox，未读一键处理。',
      cta: '了解获客',
      featured: false,
    },
    {
      id: 'publish',
      title: '多平台发品',
      metric: '母版 → 5+5 平台',
      desc: '轻集料、岩棉、橡塑多 SKU：选母版批量发布，进度条看得见。',
      cta: '了解发品',
      featured: false,
    },
    {
      id: 'site',
      title: '独立站 + 账户',
      metric: '绑域 · 套餐 · 用量',
      desc: '域名、套餐档位、本月发布与询盘额度一屏掌握，续费不找客服。',
      cta: '了解账户',
      featured: false,
    },
    {
      id: 'pro',
      title: 'GEO · AI 可见',
      metric: '专业版核心',
      desc: '追踪 ChatGPT / DeepSeek / Gemini 等品牌收录，GEO 内容矩阵 + 执行清单，让 AI 搜到你而不是竞品。',
      cta: '看 GEO 套餐',
      featured: true,
    },
  ],
  valueTabs: [
    {
      id: 'time',
      label: '省时间',
      title: '登录 30 秒就知道该干什么',
      desc: '今日待回询盘、待发品批次、绑域与套餐状态排在首屏。不用在菜单里找「该点哪里」。',
      bullets: ['Dashboard 今日引导', '询盘未读优先', '发布进度条'],
    },
    {
      id: 'scale',
      label: '可扩展',
      title: '四级渠道与租户一体',
      desc: '超管、省代、市代、卖家各看各的盘。省代辖区开户、代理业绩，与租户工作台同一套数据。',
      bullets: ['省代 / 市代 / 卖家门户', '辖区客户与报表', '渠道与租户不割裂'],
    },
    {
      id: 'safe',
      label: '更放心',
      title: '企业版审计与白标',
      desc: '多账号送检场景：白标登录、操作审计、专属支持。用量 80%/100% 自动提醒升级。',
      bullets: ['白标登录（企业版）', '操作审计', 'Plan Gate 清晰升级'],
    },
  ],
  scenarios: [
    { title: 'Alibaba / MIC 发品', desc: '保温建材多规格 SKU，母版一次配置、多平台同步。' },
    { title: '独立站询盘 inbox', desc: '海外工程商留言、样品请求统一收件，24h 跟进不遗漏。' },
    { title: 'SEO 矩阵获客', desc: '行业长尾词布局，线索汇入 inbox 而非散落表格。' },
    { title: '样品与 data sheet', desc: '询盘详情挂产品规格，外贸经理一键回复模板。' },
    { title: '省代辖区开户', desc: '省代帮辖区建材厂开通体验版，三步 onboarding 可见。' },
    { title: '多品类 SKU 管理', desc: '轻集料、陶粒、砂浆分行展示，发品不串品。' },
  ],
  pillars: [
    { title: '获客', desc: '询盘、IM、国际线索进一个 inbox' },
    { title: '发品', desc: '选母版 → 多平台发布，进度看得见' },
    { title: '账户', desc: '套餐、域名、用量一目了然，续费不找客服' },
  ],
  sections: {
    capabilitiesTitle: '建材外贸，四个能力块就够用',
    capabilitiesSub: '只做外贸厂日常需要的四件事：获客、发品、账户、矩阵 — 不堆菜单、不绕弯子',
    scenariosTitle: '建材厂常见出海场景',
    scenariosSub: '轻集料、岩棉、橡塑、砂浆 — 同一套工作台',
    plansTitle: '四档套餐，按需升级',
    plansSub: '体验版 · 启航版 · 专业版 · 企业版 — 命名与后台完全一致',
  },
  plans: PLATFORM_PLANS,
  hierarchy: [
    { code: 'platform', name: '平台超管', desc: '租户治理、系统配置、数据看板' },
    { code: 'partner', name: '省区总代', desc: '省区经营、客户开户、渠道报表' },
    { code: 'agent', name: '市代 / 代理', desc: '辖区客户、业绩与赋能' },
    { code: 'tenant', name: '建材卖家', desc: '询盘、发品、独立站日常运营' },
  ],
  portals: [
    { id: 'tenant' as const, name: '卖家工作台', desc: '建材外贸日常运营' },
    { id: 'agent' as const, name: '代理中心', desc: '渠道伙伴' },
    { id: 'partner' as const, name: '省区总代', desc: '区域合伙人' },
    { id: 'platform' as const, name: '平台控制台', desc: '内部运营' },
  ],
  finalCta: {
    title: '建材厂出海，从体验版三步开始',
    sub: '绑独立域 · 发第一条产品 · 收到第一条海外询盘 — 7 天内跑通闭环。',
    primary: '免费试用',
    secondary: '预约演示',
  },
  footerTagline: '建材外贸 · AI 卖货操作系统',
} as const;

export const NAV_LINKS = [
  { href: '#capabilities', label: '能力' },
  { href: '#value', label: '价值' },
  { href: '#integrations', label: '集成' },
  { href: '#scenarios', label: '场景' },
  { href: '#plans', label: '套餐' },
  { href: '#hierarchy', label: '渠道' },
] as const;

/** 社会证明 — 待替换真实 Logo / 证词素材 */
export const TRUST_PROOF = {
  stats: [
    { value: '7 天', label: '跑通出海三步' },
    { value: '5+5', label: '多平台发布能力' },
    { value: '4 档', label: '套餐按需升级' },
    { value: '24h', label: '询盘跟进目标' },
  ],
  logos: ['华东保温工厂', '华北轻集料', '华南橡塑出口', '西南砂浆集团'],
  quote: {
    text: '以前询盘在表格、发品在另一个后台。现在登录第一眼就知道该回哪条询盘、哪批发品还没发完。',
    author: '岩棉厂外贸经理 · 华东',
  },
} as const;

/** 集成与渠道 — 对应 IPRoyal 集成墙（建材语境） */
export const INTEGRATIONS = {
  title: '已对接的发品与获客渠道',
  sub: 'OpenAPI 可扩展 — 新平台按签约节奏接入，对外只宣传已上线能力',
  items: [
    { name: 'Alibaba.com', tag: 'B2B 发品' },
    { name: 'Made-in-China', tag: 'B2B 发品' },
    { name: '独立站询盘', tag: 'inbox' },
    { name: 'WhatsApp', tag: 'IM' },
    { name: '企业微信', tag: 'IM' },
    { name: 'SEO 矩阵', tag: '获客' },
    { name: 'GEO 引擎', tag: 'AI 收录' },
    { name: 'ChatGPT / DeepSeek', tag: 'GEO' },
    { name: 'OpenAPI', tag: '开发者' },
    { name: '抖音 / 视频号', tag: '内容分发' },
  ],
} as const;

/** plan-copy-deck §四 + plan_catalog.py 完整功能矩阵 */
export const PRICING_MATRIX = buildPricingMatrix();

/** Admin Landing 定价卡能力要点 */
export const PLAN_FEATURE_BULLETS: Record<string, string[]> = {
  trial: planFeatureBullets('trial'),
  starter: planFeatureBullets('starter'),
  pro: planFeatureBullets('pro'),
  enterprise: planFeatureBullets('enterprise'),
};

/** 营销落地页工作台示意图（非实盘；须与页面「示意图」文案配套） */
export const LANDING_HERO_PREVIEW = {
  mode: 'marketing_preview' as const,
  greeting: '上午好，今日工作台',
  items: [
    { label: '待回询盘', value: '3 条', tone: 'urgent' as const },
    { label: '待发品批次', value: '2 批', tone: 'normal' as const },
    { label: '独立域', value: '已绑定', tone: 'ok' as const },
  ],
  plan: '体验版 · 剩 5 天',
};
