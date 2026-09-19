/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * S0 · Stub 可见性矩阵（PM-01 / SAAS-01）
 * 策略：Hide | PlanGate | Lab | Kill
 */

import { ref } from 'vue'

export type StubStrategy = 'show' | 'hide' | 'planGate' | 'lab' | 'kill'

/** 与 localStorage 同步，供侧栏 computed 响应送检/实验室开关 */
export const shellCertMode = ref(false)
export const shellLabMode = ref(false)

function refreshShellFlagsFromStorage(): void {
  if (typeof localStorage === 'undefined') return
  migrateCertModeStorage()
  shellCertMode.value = localStorage.getItem(CERT_STORAGE_KEY) === '1'
  shellLabMode.value = localStorage.getItem(LAB_STORAGE_KEY) === '1'
}

export interface StubRouteRule {
  path: string
  strategy: StubStrategy
  note: string
}

/** 租户侧：菜单隐藏 + 路由重定向（T-PM-02 · COMM-PM-03 已实施） */
export const CLIENT_STUB_RULES: StubRouteRule[] = [
  { path: '/client/media-factory', strategy: 'planGate', note: '视频工厂 · W3 PlanGate' },
  { path: '/client/article-to-video', strategy: 'planGate', note: '文章转视频 · PlanGate' },
  { path: '/client/egress', strategy: 'planGate', note: '出口 IP · Enterprise' },
  { path: '/client/ai-scenarios', strategy: 'planGate', note: 'AI 场景 · PlanGate' },
  { path: '/client/app', strategy: 'hide', note: '出海计 App 壳 · 非送检菜单' },
  { path: '/client/copilot', strategy: 'show', note: '卖货飞轮 · ECC 认证开放' },
]

const CLIENT_HIDDEN = new Set(
  CLIENT_STUB_RULES.filter((r) => r.strategy === 'hide').map((r) => r.path),
)

/** Lab 路径：菜单隐藏，直达时走 Plan Gate（W3） */
const CLIENT_LAB_GATED = CLIENT_STUB_RULES.filter((r) => r.strategy === 'lab')

const CLIENT_PLAN_GATED = CLIENT_STUB_RULES.filter((r) => r.strategy === 'planGate')

export function isClientPathHidden(path: string): boolean {
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  return CLIENT_HIDDEN.has(p) || [...CLIENT_HIDDEN].some((h) => p.startsWith(`${h}/`))
}

/** Lab 路径默认不进「更多功能」抽屉，实验室开关打开后可见 */
export function isClientLabPathMenuHidden(path: string): boolean {
  if (isPlatformLabEnabled()) return false
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  return CLIENT_LAB_GATED.some((r) => p === r.path || p.startsWith(`${r.path}/`))
}

/** 更多功能抽屉瘦身：进阶项日常隐藏，送检/实验室模式可展开 */
const CLIENT_MORE_DEMOTED_PATHS = new Set([
  '/client/content',
  '/client/seo',
  '/client/referral',
  '/client/cross-platform',
])

export function isClientMoreMenuPathVisible(path: string): boolean {
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  if (isClientPathHidden(p)) return false
  if (isClientLabPathMenuHidden(p)) return false
  if (CLIENT_MORE_DEMOTED_PATHS.has(p)) {
    return isCertInspectionMode() || isPlatformLabEnabled()
  }
  return true
}

/** Plan Gate 路径 → 升级页（BE-04 服务端同源 feature 键） */
export function resolveClientPlanGate(path: string): string | null {
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  const rule = CLIENT_PLAN_GATED.find((r) => p === r.path || p.startsWith(`${r.path}/`))
  if (!rule) return null
  const featureMap: Record<string, string> = {
    '/client/egress': 'egress_ip',
    '/client/media-factory': 'media_factory',
    '/client/article-to-video': 'media_factory',
    '/client/ai-scenarios': 'seo_matrix',
  }
  return featureMap[rule.path] ?? rule.path.replace('/client/', '')
}

/** Lab 路径 → Plan Gate feature（与 BE-04 ROUTE_FEATURE_MAP 同源） */
export function resolveClientLabPlanGate(path: string): string | null {
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  const rule = CLIENT_LAB_GATED.find((r) => p === r.path || p.startsWith(`${r.path}/`))
  if (!rule) return null
  const featureMap: Record<string, string> = {
    '/client/media-factory': 'media_factory',
    '/client/article-to-video': 'media_factory',
    '/client/ai-scenarios': 'seo_matrix',
  }
  return featureMap[rule.path] ?? rule.path.replace('/client/', '')
}

/** Platform 实验室路径（菜单隐藏，lab 开关可开） */
export const PLATFORM_OPS_ALWAYS_VISIBLE: string[] = [
  '/admin/system/command-center',
  '/admin/system/deerflow-monitor',
  '/admin/system/publish-history',
  '/admin/system/rank-scheduler',
  '/admin/system/greedy-hub',
  '/admin/system/greedy-cumulative',
  '/admin/system/greedy-contest-leaderboard',
  '/admin/system/greedy-publish-queue',
  '/admin/system/survival-dashboard',
  '/admin/system/greedy-expert-memory',
  '/admin/system/ecc-hangar',
  '/admin/system/integrations-stack',
  '/admin/system/storage-provision',
  '/admin/system/ops-wrap',
  '/admin/system/progress-board',
  '/admin/platform-zones',
  '/admin/platform-registry',
  '/admin/platform-credentials',
  '/admin/file-manager',
]

/** COMM-PM-03 Kill：评审后永久下架（菜单与直达均拦截） */
export const PLATFORM_KILLED_PREFIXES = [
  '/admin/v2ray-legacy',
  '/cognitive',
] as const

export function isPlatformKilledPath(path: string): boolean {
  const p = path.split('?')[0]
  return PLATFORM_KILLED_PREFIXES.some((pre) => p === pre || p.startsWith(`${pre}/`))
}

export const PLATFORM_LAB_PREFIXES = [
  '/admin/v2ray',
  '/agent-hub',
  '/media-factory',
  '/admin/code-tools',
  '/edge-cdn',
  '/developer',
  '/templates',
  '/globalization',
  '/referral',
  '/admin/automation',
  '/admin/projects',
  '/admin/runtime',
  '/admin/scheduler-hub',
  '/admin/ai-center/article-to-video',
  '/admin/ai-center/article-generator',
  '/admin/ai-center/knowledge',
  '/tenants/product-showcase',
  '/tenants/white-label',
]

/**
 * 功能域菜单（/admin/annex/*）不列为 Lab：
 * 社媒拓客 / 外贸履约 = 优丁业务功能域（无特权），与其它模块同级可达；
 * 藏在实验室开关后会让「子系统没入口」被误判成「子系统没设计」。
 * 未部署时页面自身已有降级提示，不需要靠菜单隐藏来表达状态。
 */

export function isPlatformLabPath(path: string): boolean {
  const p = path.split('?')[0]
  if (isPlatformKilledPath(p)) return false
  if (PLATFORM_OPS_ALWAYS_VISIBLE.some((pre) => p === pre || p.startsWith(`${pre}/`))) {
    return false
  }
  return PLATFORM_LAB_PREFIXES.some((pre) => p === pre || p.startsWith(`${pre}/`))
}

export interface PlatformMenuNavItem {
  name: string
  path: string
  title: string
  icon: string
  children?: PlatformMenuNavItem[]
}

/** COMM-PM-03：递归剥离已 Kill 的菜单项 */
export function stripPlatformKilledMenuItems(items: PlatformMenuNavItem[]): PlatformMenuNavItem[] {
  return items
    .filter((i) => !isPlatformKilledPath(i.path))
    .map((i) =>
      i.children?.length
        ? { ...i, children: stripPlatformKilledMenuItems(i.children) }
        : i,
    )
    .filter((i) => !i.children?.length || (i.children?.length ?? 0) > 0)
}

/** H-08：递归剥离实验室菜单（保留司令部运维页） */
export function stripPlatformLabMenuItems(items: PlatformMenuNavItem[]): PlatformMenuNavItem[] {
  const retired = stripPlatformKilledMenuItems(items)
  if (isPlatformLabEnabled()) return retired
  return retired
    .filter((i) => !isPlatformLabPath(i.path))
    .map((i) =>
      i.children?.length
        ? { ...i, children: stripPlatformLabMenuItems(i.children) }
        : i,
    )
    .filter((i) => !i.children?.length || (i.children?.length ?? 0) > 0)
}

/** 送检鉴定面 · 超管侧栏唯一源（FE-10） */
export const CERT_INSPECTION_MENU: Array<{
  title: string
  children: Array<{ name: string; path: string; title: string; icon: string }>
}> = [
  {
    title: '送检 · 平台治理',
    children: [
      { name: 'AdminHub', path: '/admin', title: '超管工作台', icon: 'CrownOutlined' },
      { name: 'AdminTenantsPage', path: '/admin/tenants', title: '租户列表', icon: 'TeamOutlined' },
      { name: 'AdminHierarchy', path: '/admin/hierarchy', title: '层级管理', icon: 'AppstoreOutlined' },
      { name: 'AdminAggregation', path: '/admin/aggregation', title: '数据中心', icon: 'BarChartOutlined' },
      { name: 'SystemHealth', path: '/system-health/dashboard', title: '系统健康', icon: 'HeartOutlined' },
    ],
  },
  {
    title: '送检 · 财务板块',
    children: [
      { name: 'AdminFinance', path: '/admin/finance', title: '财务概览', icon: 'AccountBookOutlined' },
      { name: 'AdminFinancePaymentOps', path: '/admin/finance/payment-ops', title: '支付码与接口', icon: 'PayCircleOutlined' },
      { name: 'AdminFinancePaymentOrders', path: '/admin/finance/payment-orders', title: '租户支付订单', icon: 'OrderedListOutlined' },
      { name: 'AdminFinanceIpPool', path: '/admin/finance/ip-pool', title: '静态 IP 池', icon: 'GlobalOutlined' },
      { name: 'AdminFinanceInvoices', path: '/admin/finance/invoices', title: '开票审核', icon: 'FileTextOutlined' },
    ],
  },
  {
    title: '送检 · 业务链',
    children: [
      { name: 'Products', path: '/products', title: '产品管理', icon: 'ShoppingOutlined' },
      { name: 'ProductCategories', path: '/products/categories', title: '分类管理', icon: 'FolderOpenOutlined' },
      { name: 'IntlInquiries', path: '/international/inquiries', title: '海外询盘', icon: 'MessageOutlined' },
      { name: 'SEOMatrixPublish', path: '/seo-matrix/publish', title: '多平台发布', icon: 'SendOutlined' },
      { name: 'AICenterContent', path: '/admin/ai-center/content', title: 'AI 内容助手', icon: 'EditOutlined' },
      { name: 'AdminMediaLibrary', path: '/admin/file-manager', title: '产品图片空间', icon: 'PictureOutlined' },
      { name: 'AIEngineTradeIntel', path: '/admin/ai-engine/trade-intel', title: '贸易情报', icon: 'GlobalOutlined' },
    ],
  },
  {
    title: '送检 · 多角色演示',
    children: [
      { name: 'ClientSiteEditor', path: '/client/site-editor', title: '可视化建站', icon: 'EditOutlined' },
      { name: 'ClientProductImages', path: '/client/product-images', title: '产品图片空间', icon: 'PictureOutlined' },
      { name: 'ClientVideoSpace', path: '/client/video-space', title: '视频空间', icon: 'VideoCameraOutlined' },
      { name: 'ClientInquiries', path: '/client/inquiries', title: '租户询盘', icon: 'MessageOutlined' },
      { name: 'AgentPerformance', path: '/agent/performance', title: '代理业绩', icon: 'LineChartOutlined' },
      { name: 'AgentAccountOpening', path: '/agent/account-opening', title: '代理开户', icon: 'UserAddOutlined' },
    ],
  },
  {
    title: '设置',
    children: [
      { name: 'SystemAgentCapabilities', path: '/admin/system/agent-capabilities', title: '能力划拨', icon: 'PartitionOutlined' },
      { name: 'AdminPlatformZones', path: '/admin/platform-zones', title: '三区与送检开关', icon: 'AppstoreOutlined' },
      { name: 'AdminDemoRehearsal', path: '/admin/demo-rehearsal', title: '90 秒彩排', icon: 'PlayCircleOutlined' },
    ],
  },
]

const CERT_ALLOWED_PATHS = new Set<string>([
  '/admin',
  '/access-denied',
  '/login',
  ...CERT_INSPECTION_MENU.flatMap((g) => g.children.map((c) => c.path)),
])

/** 送检模式下允许的路径前缀（含子路由） */
const CERT_ALLOWED_PREFIXES = [
  '/admin/finance',
  '/admin/ai-center/content',
  '/admin/file-manager',
  '/admin/video-space',
  '/admin/ai-engine/trade-intel',
  '/admin/hierarchy',
  '/admin/demo-rehearsal',
  '/admin/system',
  '/admin/aggregation',
  '/admin/traffic-board',
  '/admin/system/agent-capabilities',
  '/admin/system/permissions',
  '/admin/capability-hub',
  ...PLATFORM_OPS_ALWAYS_VISIBLE,
  '/client/product-images',
  '/client/video-space',
  '/products',
  '/international/inquiries',
  '/seo-matrix/publish',
  '/system-health',
]

const CERT_STORAGE_KEY = 'admin_cert_mode'
/** 一次性：日常默认关送检（2026-06） */
const CERT_MODE_LEGACY_MIGRATED = 'admin_cert_mode_default_off_202606'
const LAB_STORAGE_KEY = 'admin_lab_enabled'

/**
 * 送检模式：默认关闭（日常开发 / 全功能验收）。
 * 仅 localStorage `admin_cert_mode=1` 时开启；录屏送检在三区治理页手动打开。
 */
function migrateCertModeStorage(): void {
  if (typeof localStorage === 'undefined') return
  if (localStorage.getItem(CERT_MODE_LEGACY_MIGRATED) === '1') return
  // 旧版默认「开」：未写 localStorage 也会走送检菜单；统一落为关
  localStorage.setItem(CERT_STORAGE_KEY, '0')
  localStorage.setItem(CERT_MODE_LEGACY_MIGRATED, '1')
}

export function isCertInspectionMode(): boolean {
  if (typeof localStorage === 'undefined') return false
  refreshShellFlagsFromStorage()
  return shellCertMode.value
}

export function setCertInspectionMode(on: boolean): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(CERT_STORAGE_KEY, on ? '1' : '0')
  localStorage.setItem(CERT_MODE_LEGACY_MIGRATED, '1')
  shellCertMode.value = on
}

export function setPlatformLabEnabled(on: boolean): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(LAB_STORAGE_KEY, on ? '1' : '0')
  shellLabMode.value = on
}

export function isPlatformLabEnabled(): boolean {
  if (typeof localStorage === 'undefined') return false
  refreshShellFlagsFromStorage()
  return shellLabMode.value
}

export function certPathAllowed(path: string): boolean {
  const p = path.split('?')[0].replace(/\/$/, '') || '/'
  if (isPlatformKilledPath(p)) return false
  if (CERT_ALLOWED_PATHS.has(p)) return true
  if (CERT_ALLOWED_PREFIXES.some((pre) => p === pre || p.startsWith(`${pre}/`))) return true
  if (isPlatformLabEnabled() && isPlatformLabPath(p)) return true
  return false
}

/** 送检模式：按 certPathAllowed 过滤侧栏分组（Client/Agent 壳） */
export function filterShellMenuByCertMode<
  G extends { title: string; children: Array<{ path: string }> },
>(groups: G[]): G[] {
  if (!isCertInspectionMode()) return groups
  return groups
    .map((g) => ({
      ...g,
      children: g.children.filter((item) => certPathAllowed(item.path)),
    }))
    .filter((g) => g.children.length > 0) as G[]
}

/** 超管送检模式：非鉴定面路径拦截 */
export function isPlatformPathBlockedInCertMode(path: string): boolean {
  if (!isCertInspectionMode()) return false
  const p = path.split('?')[0]
  if (p.startsWith('/client/login') || p.startsWith('/login')) return false
  if (p.startsWith('/client') || p.startsWith('/agent')) {
    return !certPathAllowed(p)
  }
  if (p.startsWith('/admin') || p.startsWith('/products') || p.startsWith('/international') || p.startsWith('/seo-matrix') || p.startsWith('/system-health') || p.startsWith('/dashboard')) {
    return !certPathAllowed(p)
  }
  return false
}

if (typeof window !== 'undefined') {
  refreshShellFlagsFromStorage()
  window.addEventListener('storage', (ev) => {
    if (ev.key === CERT_STORAGE_KEY || ev.key === LAB_STORAGE_KEY) {
      refreshShellFlagsFromStorage()
    }
  })
}
