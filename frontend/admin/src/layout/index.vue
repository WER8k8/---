/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <CertWatermark>
  <div class="shell" :class="`shell--${shellMode}`">
    <YdProSidebar
      v-model:collapsed="collapsed"
      :menu-items="menuItems"
      :is-mobile="isMobile"
      :flyout-menu="flyoutMenu"
      :expanded-sub-menus="expandedSubMenus"
      :brand-home="brandHome"
      :brand-mark="brandMark"
      :brand-title="brandTitle"
      :brand-subtitle="brandSubtitle"
      :username="auth.username || ''"
      :role-label="shellRoleLabel"
      :is-nav-item-active="isNavItemActive"
      :is-nav-descendant-active="isNavDescendantActive"
      @navigate="handleNavClick"
      @logout="handleLogout"
      @toggle-submenu="toggleSubMenu"
      @parent-main-click="onParentMainClick"
      @brand-click="onSidebarBrandClick"
    />

    <!-- Main Area -->
    <div class="main-area" :class="{ collapsed }">
      <YdProTopbar
        v-model:collapsed="collapsed"
        v-model:copilot-open="copilotOpen"
        v-model:theme-drawer-open="showThemeDrawer"
        :page-title="currentPageTitle"
        :page-subtitle="currentPageSubtitle"
        :show-breadcrumb-subtitle="showBreadcrumbSubtitle"
        :username="auth.username || ''"
        :brand-home="brandHome"
        :show-platform-home="showPlatformReturnHome"
        platform-home-path="/admin"
        @navigate="handleNavClick"
      />

      <a-alert
        v-if="devBackendDown"
        class="dev-backend-hint"
        type="error"
        show-icon
        banner
        closable
        message="本地 API 未响应（:8001）。请在本机运行：powershell -File scripts/start-dev-admin.ps1 -ForceRestart，然后 Ctrl+F5 刷新。"
      />

      <a-alert
        v-if="needsDevRelogin && shellMode === 'platform'"
        class="dev-relogin-hint"
        type="warning"
        show-icon
        banner
        message="会话角色仍是旧的「运营管理员」，请退出后重新登录一次，与本地平台超管账号对齐。"
      />

      <YdClientPlanUsageBar v-if="shellMode === 'client'" />

      <YdProWorktabs
        :role-label="shellRoleLabel"
        :username="auth.username || '优丁平台'"
        :shell-mode="shellMode"
      />

      <!-- Content：去掉 out-in，避免切页白屏闪；懒加载期间保留上一页，不插 empty 占位 -->
      <div class="content-area" :class="{ 'content-area--wide': isWideContentRoute }">
        <router-view v-slot="{ Component }">
          <keep-alive v-if="Component" :max="MAX_WORK_TABS">
            <component :is="Component" :key="normalizeLocationPath(route.path)" />
          </keep-alive>
        </router-view>
      </div>
    </div>

    <YdCopilotSlot v-model:open="copilotOpen" />
    <UBrainAssistant v-if="shellMode === 'client'" />
    <GlobalSearch />
    <ThemeSettingsDrawer v-model:open="showThemeDrawer" />
  </div>
  </CertWatermark>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAgentCapabilitiesStore } from '@/stores/agentCapabilities'
import { resolveCapabilityIdForPath, normalizeLocationPath } from '@/constants/workbenchPathCapabilities'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import GlobalSearch from '@/components/GlobalSearch.vue'
import { flattenMenuNav, pageTitlesToSearchRows } from '@/utils/flattenMenuNav'
import { resolveWorkTabNavigatePath } from '@/utils/workTabPath'
import YdProWorktabs from '@/components/layout/YdProWorktabs.vue'
import YdProSidebar from '@/components/layout/YdProSidebar.vue'
import { readStoredAccessToken, isPlatformAdminFromToken } from '@/utils/sessionAuth'
import YdProTopbar from '@/components/layout/YdProTopbar.vue'
import ThemeSettingsDrawer from '@/components/layout/ThemeSettingsDrawer.vue'
import YdCopilotSlot from '@/components/layout/YdCopilotSlot.vue'
import CertWatermark from '@/components/layout/CertWatermark.vue'
import UBrainAssistant from '@/components/UBrainAssistant.vue'
import { YdClientPlanUsageBar } from '@/components/youding'
import { provideTenantBrand } from '@/composables/useTenantBrand'
import {
  getAgentShellMenu,
  getClientShellMenu,
  getPartnerShellMenu,
  resolveShellMode,
  type ShellMode,
} from '@/constants/proShellMenus'
import { MAX_WORK_TABS, useWorkTabsStore } from '@/stores/workTabs'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { useShellNavigation } from '@/composables/useShellNavigation'
import { useDevBackendProbe } from '@/composables/useDevBackendProbe'
import { useEffectivePlatformRole } from '@/composables/useEffectivePlatformRole'
import type { ShellNavItem } from '@/types/shellNav'
import {
  CERT_INSPECTION_MENU,
  filterShellMenuByCertMode,
  isCertInspectionMode,
  shellCertMode,
  shellLabMode,
  isPlatformKilledPath,
  stripPlatformLabMenuItems,
} from '@/constants/stubVisibility'
import {
  homePathForRole,
  isPathAllowedForRoleTier,
  resolveRoleShellTier,
} from '@/constants/roleShellLock'
import { getPlatformOpsMenuItems } from '@/constants/platformShellMenu'

const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 768 : false)
const collapsed = ref(isMobile.value)
const showThemeDrawer = ref(false)
const copilotOpen = ref(false)

// Mobile/desktop responsive
function onResize() {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  if (isMobile.value && !wasMobile) collapsed.value = true
  if (!isMobile.value && wasMobile) collapsed.value = false
}
onMounted(() => { isMobile.value = window.innerWidth < 768; collapsed.value = isMobile.value; window.addEventListener('resize', onResize) })
onUnmounted(() => window.removeEventListener('resize', onResize))

// Router & auth
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { role: platformMenuRole, roleLabel, needsDevRelogin } = useEffectivePlatformRole()
const workTabs = useWorkTabsStore()
const uiPrefs = useUiPreferencesStore()
const currentPath = computed(() => normalizeLocationPath(route.path))
const isWideContentRoute = computed(() =>
  /\/site-editor(?:-lab)?$/.test(currentPath.value),
)
const expandedSubMenus = ref<string[]>([])
const flyoutMenu = ref<string | null>(null)

function onParentMainClick(item: MenuNavItem) {
  if (collapsed.value) {
    flyoutMenu.value = flyoutMenu.value === item.name ? null : item.name
    return
  }
  void handleNavClick(item.path)
  if (!expandedSubMenus.value.includes(item.name)) {
    expandedSubMenus.value.push(item.name)
  }
}

function closeFlyout() {
  flyoutMenu.value = null
}

function onSidebarBrandClick() {
  if (isMobile.value) collapsed.value = true
}

const roleLabelMap: Record<string, string> = {
  tenant_admin: '租户管理员',
  editor: '编辑人员',
  sales: '销售人员',
  viewer: '查看者',
  l2: '大区总代(省代)',
  l3: '区域运营',
  agent: '代理',
}
const shellRoleLabel = computed(() => {
  if (shellMode.value === 'platform') return roleLabel.value
  return roleLabelMap[auth.currentRole || ''] || auth.currentRole || '用户'
})

const shellMode = computed<ShellMode>(() => resolveShellMode(route.path))
/** 仅平台 JWT（super_admin/admin）预览代理/省代壳时可回 /admin；真实代理账号不显示 */
const showPlatformReturnHome = computed(() => {
  const role = auth.currentRole
  if (resolveRoleShellTier(role) !== 'platform') return false
  if (!isPlatformAdminFromToken(readStoredAccessToken())) return false
  return shellMode.value === 'agent' || shellMode.value === 'partner'
})
const brandHome = computed(() => {
  if (shellMode.value === 'client') return '/client/dashboard'
  if (shellMode.value === 'partner') return '/partner/performance'
  if (shellMode.value === 'agent') return '/agent/performance'
  return '/admin'
})
const tenantBrand = provideTenantBrand()
const brandTitle = computed(() => {
  if (shellMode.value === 'client') return tenantBrand.companyName.value || '出海工作台'
  if (shellMode.value === 'partner') return '省代中心'
  if (shellMode.value === 'agent') return '代理中心'
  return '优丁建材'
})
const brandSubtitle = computed(() => {
  if (shellMode.value === 'client') return 'Client Workspace'
  if (shellMode.value === 'partner') return 'Provincial Partner'
  if (shellMode.value === 'agent') return 'L2 / L3 Agent'
  return 'AI SaaS'
})
const brandMark = computed(() => {
  if (shellMode.value === 'client') return (brandTitle.value || '工').charAt(0)
  if (shellMode.value === 'partner') return '省'
  if (shellMode.value === 'agent') return '代'
  return '优'
})

// Submenu
function toggleSubMenu(name: string) { const i = expandedSubMenus.value.indexOf(name); i > -1 ? expandedSubMenus.value.splice(i, 1) : expandedSubMenus.value.push(name) }
function autoExpand() {
  menuItems.value.forEach(g => g.children.forEach((item: any) => {
    if (item.children?.length && item.children.some((sub: any) => route.path === sub.path || route.path.startsWith(sub.path + '/'))) {
      if (!expandedSubMenus.value.includes(item.name)) expandedSubMenus.value.push(item.name)
    }
  }))
}
onMounted(autoExpand)
watch(() => route.path, () => {
  autoExpand()
  closeFlyout()
})
onMounted(() => document.addEventListener('click', closeFlyout))
onUnmounted(() => document.removeEventListener('click', closeFlyout))

const { backendDown: devBackendDown } = useDevBackendProbe()

// Menu
import { PLATFORM_SHELL_MENU as menuTreeSource } from '@/constants/platformShellMenu';

// Feature map for tenant filtering
const pathFeatureMap: Record<string, string> = {
  '/dashboard': 'dashboard',
  '/products': 'products',
  '/products/categories': 'products',
  '/content': 'content',
  '/cases': 'content',
  '/news': 'content',
  '/inquiries': 'inquiries',
  '/seo': 'seo',
  '/seo/content-optimizer': 'ai_content',
  '/seo-matrix/keywords': 'seo',
  '/seo-matrix/publish': 'seo',
  '/ai-config': 'ai_content',
  '/globalization': 'globalization',
  '/international': 'international',
  '/users': 'users',
  '/settings': 'settings',
}

interface MenuNavItem extends ShellNavItem {}
const tenantFeatures = ref<string[] | null>(null)
async function loadTenantFeatures() {
  const tk = readStoredAccessToken()
  if (!tk) return
  if (isPlatformAdminFromToken(tk)) return
  try {
    const res = await fetch('/api/v1/tenants/current', { headers: { Authorization: `Bearer ${tk}` } })
    const d = await res.json()
    const data = d.data || d
    if (data?.features) tenantFeatures.value = data.features
  } catch { /* non-tenant user gets full access */ }
}
onMounted(loadTenantFeatures)

function menuPathAllowed(path:string):boolean {
  if (isPlatformKilledPath(path)) return false

  // 超级管理员拥有所有权限
  if (auth.currentRole === 'super_admin') {
    return true
  }
  
  // 如果没有角色（未登录或token无效），允许访问所有菜单（降级处理）
  if (!auth.currentRole) {
    return true
  }
  
  const capStore = useAgentCapabilitiesStore()
  const capId = resolveCapabilityIdForPath(path)
  
  // 如果路径没有注册能力ID，允许访问
  if (capId == null) {
    return true
  }
  
  // 检查能力权限
  if (!capStore.canAccess(capId)) {
    return false
  }
  
  // 检查租户功能限制
  if (tenantFeatures.value) {
    const feature = pathFeatureMap[path]
    if (feature && !tenantFeatures.value.includes(feature)) {
      return false
    }
  }
  
  return true
}

function filterMenuNavChildren(children:MenuNavItem[]):MenuNavItem[] {
  const next:MenuNavItem[] = []
  for (const item of children) {
    if (item.children?.length) { const sub = filterMenuNavChildren(item.children); if (sub.length===0) continue; next.push({...item,children:sub}); continue }
    if (menuPathAllowed(item.path)) next.push(item)
  }
  return next
}

const roleFilters: Record<string, Set<string>> = {
  super_admin: new Set(),
  editor: new Set(['数据看板', '文章内容', '案例展示', '新闻动态', 'SEO总览', 'AI内容优化']),
  sales: new Set(['询盘留言', '销售工作台']),
  viewer: new Set(['数据看板']),
  l2: new Set(['数据看板', '流量看板', '产品管理', '文章内容', '案例展示', '新闻动态', '询盘留言', 'SEO总览', 'AI内容优化', '关键词排名', '站点体检', '矩阵词管理', '多平台发布', '账户管理', '系统设置', '业绩看板', '佣金管理', '客户开户', '经营日报', '流失预警']),
  l3: new Set(['数据看板', '流量看板', '产品管理', '询盘留言', 'SEO总览', 'AI内容优化', '站点体检', '业绩看板', '佣金管理', '经营日报', '流失预警']),
}

const roleGroupFilters: Record<string, Set<string>> = {
  super_admin: new Set(),
  editor: new Set(['总览', '业务管理', '网站优化']),
  sales: new Set(['总览', '客户线索', '网站优化']),
  viewer: new Set(['总览']),
  l2: new Set(['总览', '业务管理', '客户线索', '网站优化', '代理中心', '系统']),
  l3: new Set(['总览', '业务管理', '客户线索', '网站优化', '代理中心']),
}

const certInspectionMenuItems = () =>
  CERT_INSPECTION_MENU.map((g) => ({
    title: g.title,
    children: g.children as MenuNavItem[],
  }))

const menuItems = computed(() => {
  void shellCertMode.value
  void shellLabMode.value
  void platformMenuRole.value
  if (shellMode.value === 'client') {
    return filterShellMenuByCertMode(getClientShellMenu())
  }
  if (shellMode.value === 'partner') {
    return filterShellMenuByCertMode(getPartnerShellMenu())
  }
  if (shellMode.value === 'agent') {
    return filterShellMenuByCertMode(getAgentShellMenu())
  }

  if (isCertInspectionMode()) {
    return certInspectionMenuItems()
  }

  const role = platformMenuRole.value ?? auth.currentRole
  let items = menuTreeSource.map(g=>({title:g.title,children:filterMenuNavChildren(g.children as MenuNavItem[])})).filter(g=>g.children.length>0)

  // 如果没有角色（未登录或token无效），返回所有菜单（降级处理）
  if (!role) {
    console.warn('[Menu] No role found, returning all menu items')
    return items
  }

  if (role === 'admin' || role === 'super_admin') {
    if (role === 'admin' && !import.meta.env.DEV) {
      items = items
        .filter(g => g.title !== '超级管理工具')
        .map(g => ({
          ...g,
          children: stripPlatformLabMenuItems(g.children as MenuNavItem[]),
        }))
        .filter(g => g.children.length > 0)
        .concat([
          { title: 'Platform 三区', children: [
            { name:'AdminPlatformZones',path:'/admin/platform-zones',title:'三区治理',icon:'AppstoreOutlined' },
            { name:'AdminPlatformRegistry',path:'/admin/platform-registry',title:'平台来源审计',icon:'GlobalOutlined' },
            { name:'AdminPlatformCredentials',path:'/admin/platform-credentials',title:'平台凭证',icon:'KeyOutlined' },
            { name:'AdminDemoRehearsal',path:'/admin/demo-rehearsal',title:'七步彩排',icon:'PlayCircleOutlined' },
          ]},
          { title: '运营管理', children: [
            { name:'AdminDashboardPage',path:'/admin/dashboard',title:'运营看板',icon:'DashboardOutlined' },
            { name:'OperationsTrafficBoard',path:'/operations/traffic',title:'流量看板',icon:'LineChartOutlined' },
            { name:'AdminMediaLibrary',path:'/admin/file-manager',title:'产品图片空间',icon:'PictureOutlined' },
          ]},
          { title: '租户管理', children: [
            { name:'AdminTenantsPage',path:'/admin/tenants',title:'租户列表',icon:'TeamOutlined' },
          ]},
          ...(getPlatformOpsMenuItems().length
            ? [{ title: '摸金校尉', children: getPlatformOpsMenuItems() as MenuNavItem[] }]
            : []),
        ])
      return items
    }
    // super_admin 非送检：隐藏实验室项，保留全量菜单
    items = items.map(g => ({
      ...g,
      children: stripPlatformLabMenuItems(filterMenuNavChildren(g.children as MenuNavItem[])),
    })).filter(g => g.children.length > 0)
    return items
  }

  // 如果角色不在过滤器中定义，返回所有菜单（向后兼容）
  if (!roleFilters[role]) {
    console.warn(`[Menu] Role "${role}" not found in filters, returning all menu items`)
    return items
  }

  const allowedTitles = roleFilters[role]
  const allowedGroups = roleGroupFilters[role] || new Set()

  // 如果过滤器都是空集合，返回所有菜单
  if (allowedTitles.size === 0 && allowedGroups.size === 0) {
    return items
  }

  items = items
    .filter(g => allowedGroups.size === 0 || allowedGroups.has(g.title))
    .map(g => ({
      ...g,
      children: allowedTitles.size === 0 ? g.children : g.children.filter(item => allowedTitles.has(item.title))
    }))
    .filter(g => g.children.length > 0)

  return items
})

const { isNavItemActive, isNavDescendantActive, resolveNavTitle } = useShellNavigation(menuItems)

// Page meta
const pageTitles: Record<string,{title:string;subtitle:string}> = {
  '/dashboard':{title:'数据看板',subtitle:'今日访问、询盘与线索统计'},
  '/access-denied':{title:'无权访问',subtitle:'当前会话级别未包含该页面能力'},
  '/admin':{title:'平台超管工作台',subtitle:'全站模块导航与能力入口'},
  '/admin/finance':{title:'财务概览',subtitle:'营收、成本、分润与到期租户'},
  '/admin/finance/payment-ops':{title:'支付码与接口',subtitle:'微信/支付宝收款码探针、回调地址与证书'},
  '/admin/finance/payment-orders':{title:'租户支付订单',subtitle:'全平台租户付款单与状态筛选'},
  '/admin/finance/ip-pool':{title:'静态 IP 池',subtitle:'出口 IP 槽位使用率与租户分配'},
  '/admin/finance/invoices':{title:'开票审核',subtitle:'租户开票申请审核与开具'},
  '/admin/finance/commissions':{title:'分润结算',subtitle:'代理佣金结算与确认'},
  '/admin/finance/commission-rules':{title:'分润规则',subtitle:'各级代理分润比例配置'},
  '/admin/demo-rehearsal':{title:'90秒送检彩排',subtitle:'融资演示路径 · LOCKED v1'},
  '/admin/system':{title:'系统管理',subtitle:'日志与配置'},
  '/admin/system/command-center':{title:'超管司令部',subtitle:'Hermes 运维总览与快捷入口'},
  '/admin/system/greedy-hub':{title:'摸金校尉总控',subtitle:'全球累计 · 大赛 · 耐力赛 · 搞钱闭环'},
  '/admin/system/greedy-cumulative':{title:'摸金累计看板',subtitle:'全球/月度/人格累计与趋势'},
  '/admin/system/greedy-contest-leaderboard':{title:'挣钱大赛',subtitle:'211 专家记分 · protected 永不下线'},
  '/admin/system/greedy-publish-queue':{title:'L4 发布队列',subtitle:'摸金 PublishTask 审核与重试'},
  '/admin/system/survival-dashboard':{title:'Survival 台账',subtitle:'真钱入账与 runway 脉冲'},
  '/admin/system/greedy-expert-memory':{title:'专家记忆',subtitle:'运维专用：查 AI 专家经验与备注，日常运营可忽略'},
  '/products':{title:'产品管理',subtitle:'管理产品信息和分类'},
  '/products/categories':{title:'分类管理',subtitle:'管理产品分类结构'},
  '/seo':{title:'SEO总览',subtitle:'网站SEO数据总览'},
  '/seo/batch-seo':{title:'批量SEO',subtitle:'批量优化页面SEO'},
  '/seo/content-optimizer':{title:'AI内容优化',subtitle:'智能优化内容质量'},
  '/seo/llms-txt':{title:'LLMs.txt',subtitle:'搜索引擎友好内容生成'},
  '/seo/site-audit':{title:'站点体检',subtitle:'全面检测网站问题'},
  '/seo/schema-markup':{title:'Schema标记',subtitle:'结构化数据与富摘要'},
  '/seo/eeat':{title:'EEAT评分',subtitle:'经验、专业、权威、可信'},
  '/seo/compliance':{title:'广告法合规',subtitle:'内容与合规扫描'},
  '/seo/building-wiki':{title:'AI建材百科',subtitle:'AI生成建材行业知识文章'},
  '/seo/keyword-ranking':{title:'关键词排名',subtitle:'排名追踪与历史'},
  '/seo/baidu-tools':{title:'百度站长工具',subtitle:'百度搜索资源平台集成'},
  '/seo/performance':{title:'性能与安全',subtitle:'监控与健康检查'},
  '/seo-matrix/dashboard':{title:'SEO矩阵',subtitle:'地域词与生成分发'},
  '/seo-matrix/settings':{title:'矩阵设置',subtitle:'矩阵全局参数'},
  '/seo-matrix/regions':{title:'地域词库',subtitle:'省市区与词组'},
  '/seo-matrix/keywords':{title:'矩阵词管理',subtitle:'组合与生成词管理'},
  '/seo-matrix/content':{title:'文案生成',subtitle:'模板与批量文案'},
  '/seo-matrix/publish':{title:'多平台发布',subtitle:'发布任务与账号'},
  '/seo-matrix/inclusion':{title:'收录监控',subtitle:'收录状态与复检'},
  '/seo-matrix/growth-tools':{title:'增长工具',subtitle:'热词库、质检、引流监测与智能跑盘'},
  '/content':{title:'文章内容',subtitle:'管理网站图文内容'},
  '/cases':{title:'案例展示',subtitle:'管理成功案例'},
  '/inquiries':{title:'询盘管理',subtitle:'客户咨询与询价跟进'},
  '/sales/dashboard':{title:'销售工作台',subtitle:'我的销售业绩与客户跟进'},
  '/sales/customer-finder':{title:'客户开发',subtitle:'多渠道客户采集与智能筛选'},
  '/sales/auto-negotiator':{title:'自动谈单',subtitle:'RFQ监控、询盘回复与智能报价'},
  '/sales/email-automation':{title:'开发信管理',subtitle:'个性化邮件生成与效果追踪'},
  '/news':{title:'新闻动态',subtitle:'新闻资讯与发布状态'},
  '/compliance':{title:'合规治理',subtitle:'全局合规概览与问题单'},
  '/ai-config':{title:'AI配置',subtitle:'模型提供商与调用统计'},
  '/users':{title:'账户管理',subtitle:'管理系统用户'},
  '/settings':{title:'系统设置',subtitle:'基本参数配置'},
  '/international':{title:'采集概览',subtitle:'国际询盘采集数据总览'},
  '/international/inquiries':{title:'海外询盘',subtitle:'查看和管理海外客户询盘'},
  '/international/sites':{title:'目标网站',subtitle:'配置国际B2B平台采集源'},
  '/tenants/dashboard':{title:'租户管理',subtitle:'多租户隔离与资源配额'},
  '/tenants/product-showcase':{title:'产品展示',subtitle:'向客户展示 SaaS 产品功能'},
  '/tenants/pricing':{title:'定价方案',subtitle:'套餐对比与购买'},
  '/tenants/plans':{title:'套餐配置',subtitle:'管理 SaaS 套餐与配额'},
  '/tenants/billing':{title:'计费结算',subtitle:'账单与交易记录'},
  '/tenants/white-label':{title:'白标品牌',subtitle:'品牌自定义与域名配置'},
  '/tenants/domain':{title:'域名管理',subtitle:'自定义域名绑定与 DNS 配置'},
  '/tenants/site-editor':{title:'AI智能建站',subtitle:'输入产品名，Hermes 按设计规范生成官网'},
  '/agent-hub/dashboard':{title:'智能体协同',subtitle:'MCP桥接与任务调度'},
  '/media-factory/dashboard':{title:'多媒体工厂',subtitle:'视频生成与TTS配音'},
  '/globalization/dashboard':{title:'全球化多语言',subtitle:'术语库与翻译引擎'},
  '/logistics/dashboard':{title:'智能物流定价',subtitle:'LBS测距与运费精算'},
  '/system-health/dashboard':{title:'系统健康压测',subtitle:'资源监控与压测管理'},
  '/ai-learning/dashboard':{title:'AI深度学习',subtitle:'行为分析与转化漏斗'},
  '/cognitive/dashboard':{title:'认知智能',subtitle:'知识图谱与智能问答'},
  '/edge-cdn/dashboard':{title:'边缘计算CDN',subtitle:'节点管理与内容预热'},
  '/developer/dashboard':{title:'开发者生态',subtitle:'API网关与低代码平台'},
  '/referral/rules':{title:'活动规则',subtitle:'呼朋唤友计划详细介绍'},
  '/admin/aggregation':{title:'数据中心',subtitle:'全平台数据汇总看板'},
  '/admin/dashboard':{title:'运营看板',subtitle:'平台运营数据概览'},
  '/operations/traffic':{title:'流量看板',subtitle:'访客·点击·询盘归因全链路'},
  '/admin/traffic-board':{title:'全平台流量',subtitle:'各租户与代理流量汇总'},
  '/admin/tenants':{title:'租户管理',subtitle:'查看和管理平台租户'},
  '/admin/ai-center':{title:'AI中心',subtitle:'AI控制台与模型管理'},
  '/admin/ai-center/models':{title:'模型管理',subtitle:'AI提供商与模型配置'},
  '/admin/ai-center/content':{title:'AI内容助手',subtitle:'内容生成与SEO优化'},
  '/admin/ai-center/analytics':{title:'智能分析',subtitle:'SEO分析·转化漏斗·行为分析'},
  '/admin/ai-center/logs':{title:'调用日志',subtitle:'AI调用记录与费用统计'},
  '/admin/ai-center/provider-setup':{title:'模型配置',subtitle:'AI大模型平台接入引导'},
  '/admin/ai-center/scenario-models':{title:'场景模型切换',subtitle:'按功能场景独立选择与切换 NVIDIA 模型'},
  '/admin/ai-center/article-generator':{title:'文章生成器',subtitle:'按「文章」场景模型生成长文'},
  '/admin/ai-center/article-to-video':{title:'文章转视频',subtitle:'文章→脚本→Cosmos 渲染队列'},
  '/admin/ai-center/usage':{title:'用量监控',subtitle:'Token用量与告警管理'},
  '/admin/ai-center/knowledge':{title:'知识库',subtitle:'建材行业知识问答与检索'},
  '/agent/performance':{title:'业绩看板',subtitle:'客户开发与收款数据总览'},
  '/agent/commission':{title:'佣金管理',subtitle:'佣金记录与结算规则'},
  '/agent/account-opening':{title:'客户开户',subtitle:'提交新客户开户申请'},
  '/agent/daily-report':{title:'经营日报',subtitle:'每日经营数据自动汇总'},
  '/agent/churn-warning':{title:'流失预警',subtitle:'客户流失风险检测与跟进'},
  '/agent/traffic':{title:'流量看板',subtitle:'代理客户流量汇总'},
  '/partner/performance':{title:'省代看板',subtitle:'省区节点经营与回款总览'},
  '/partner/commission':{title:'佣金管理',subtitle:'省区佣金与结算管理'},
  '/partner/account-opening':{title:'客户开户',subtitle:'省区客户开通审批'},
  '/partner/daily-report':{title:'经营日报',subtitle:'省区经营日报与趋势'},
  '/partner/churn-warning':{title:'流失预警',subtitle:'省区客户流失风险管理'},
  '/partner/traffic':{title:'流量看板',subtitle:'省区客户流量总览'},
  '/client/dashboard':{title:'租户工作台',subtitle:'出海 KPI 与今日待办'},
  '/client/inquiries':{title:'租户询盘',subtitle:'客户咨询与询价跟进'},
  '/client/onboarding':{title:'开通向导',subtitle:'完成站点与产品初始化'},
  '/client/billing':{title:'套餐续费',subtitle:'套餐与账单管理'},
  '/client/products':{title:'产品管理',subtitle:'管理产品与分类'},
  '/client/settings':{title:'系统设置',subtitle:'租户侧参数配置'},
  '/client/queues/inquiries':{title:'询盘队列',subtitle:'待处理询盘优先队列'},
  '/client/queues/publish':{title:'发布队列',subtitle:'内容发布任务队列'},
  '/client/queues/fulfillment':{title:'履约队列',subtitle:'订单履约跟进'},
  '/admin/hierarchy':{title:'层级管理',subtitle:'L1-L4 组织架构与权限'},
  '/admin/platform-zones':{title:'三区治理',subtitle:'Platform / Client / Agent 与送检开关'},
  '/admin/platform-registry':{title:'平台来源审计',subtitle:'客户自填/连接平台 · 养号与指纹模板（仅超管）'},
  '/admin/platform-credentials':{title:'平台凭证与真发就绪',subtitle:'凭证字段、缺项、会话巡检（仅超管）'},
}

function matchPageMeta(path: string) {
  const loc = normalizeLocationPath(path)
  if (pageTitles[loc]) return pageTitles[loc]
  const prefixes = Object.keys(pageTitles).filter(k => k !== '/' && loc.startsWith(k + '/'))
  prefixes.sort((a,b) => b.length - a.length)
  return prefixes[0] ? pageTitles[prefixes[0]] : null
}

const globalSearchMenuIndex = computed(() => {
  const role = auth.currentRole
  const fromMenu = flattenMenuNav(menuItems.value as { title?: string; children: MenuNavItem[] }[])
  const fromPages = pageTitlesToSearchRows(pageTitles)
  const seen = new Set<string>()
  return [...fromMenu, ...fromPages].filter((row) => {
    if (!isPathAllowedForRoleTier(row.path, role)) return false
    if (seen.has(row.path)) return false
    seen.add(row.path)
    return true
  })
})
provide('globalSearchMenuIndex', globalSearchMenuIndex)

const currentPageTitle = computed(() => resolveNavTitle(currentPath.value) || matchPageMeta(currentPath.value)?.title || '控制台')
const currentPageSubtitle = computed(() => {
  const meta = matchPageMeta(currentPath.value)
  const sub = meta?.subtitle?.trim()
  if (!sub) return ''
  if (sub === '日志与配置' && currentPath.value !== '/admin/system') return ''
  const title = resolveNavTitle(currentPath.value) || meta?.title || ''
  if (sub === title) return ''
  return sub
})
/** 销售等子模块已有 Tab 导航，顶栏不再重复副标题 */
const showBreadcrumbSubtitle = computed(() => {
  const p = currentPath.value
  if (p.startsWith('/sales/')) return false
  if (p.startsWith('/admin/finance')) return false
  const sub = currentPageSubtitle.value
  if (sub === '日志与配置' && p !== '/admin/system') return false
  return Boolean(sub)
})

async function handleNavClick(path: string) {
  closeFlyout()
  if (!path) return
  const target = resolveWorkTabNavigatePath(path, shellMode.value, auth.currentRole)
  if (normalizeLocationPath(currentPath.value) === normalizeLocationPath(target)) {
    if (isMobile.value) collapsed.value = true
    return
  }
  try {
    await router.push(target)
    if (isMobile.value) collapsed.value = true
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    if (msg.includes('Avoided redundant navigation') || msg.includes('NavigationDuplicated')) return
    message.error('页面跳转失败，请刷新后重试')
    console.warn('[nav]', path, err)
  }
}

function syncWorkTabFromRoute(path: string) {
  const meta = matchPageMeta(path)
  const title = resolveNavTitle(path) || meta?.title || '页面'
  workTabs.openTab({ path, title })
}

let lastAccentShell = ''

watch(
  () => route.path,
  (path) => {
    syncWorkTabFromRoute(path)
    const accent =
      path.startsWith('/client')
        ? 'client'
        : path.startsWith('/agent') || path.startsWith('/partner')
          ? 'agent'
          : 'platform'
    if (lastAccentShell !== accent) {
      lastAccentShell = accent
      if (accent === 'client') {
        uiPrefs.setAccentRole('client')
        workTabs.ensureAffixForShell('client')
      } else if (accent === 'agent') {
        uiPrefs.setAccentRole('agent')
        workTabs.ensureAffixForShell('agent')
      } else {
        uiPrefs.setAccentRole('platform')
        workTabs.ensureAffixForShell('platform')
      }
    }
  },
  { immediate: true },
)

watch(
  () => [resolveShellMode(route.path), auth.currentRole] as const,
  ([shell, role]) => {
    workTabs.sanitizeForSession(shell, role)
  },
  { immediate: true },
)

onMounted(() => {
  const path = normalizeLocationPath(route.path)
  if (normalizeLocationPath(workTabs.activePath) !== path) {
    workTabs.setActive(path)
  }
  // 迁移：规范化已存标签 path，去掉重复项
  const normalized = workTabs.tabs.map((t) => ({
    ...t,
    path: normalizeLocationPath(t.path),
  }))
  workTabs.tabs = normalized.filter(
    (t, i, arr) => arr.findIndex((x) => normalizeLocationPath(x.path) === normalizeLocationPath(t.path)) === i,
  )
  workTabs.persist()
  if (shellMode.value === 'client') {
    void tenantBrand.load()
  }
  for (const tab of workTabs.tabs) {
    const title = resolveNavTitle(tab.path)
    if (title && title !== tab.title) {
      workTabs.openTab({ path: tab.path, title })
    }
  }
})
async function handleLogout() { await auth.logout(); router.push('/login') }
</script>

<style>
/* ========== SHELL LAYOUT ========== */
.shell { display: flex; min-height: 100vh; background: var(--uj-bg-page, #f8fafc); font-family: var(--uj-font-sans); }

.sidebar-brand-mark {
  background: var(--uj-brand, #55778f);
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* 侧栏/标签 accent 由 mint-glass-shell.scss + uiPreferences 统一，此处不再分 shell 覆写 */

/* ========== MAIN AREA ========== */
.main-area {
  flex: 1;
  margin-left: var(--uj-sidebar-width, 248px);
  width: calc(100% - var(--uj-sidebar-width, 248px));
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin 0.25s ease, width 0.25s ease;
  overflow-x: hidden;
}
.main-area.collapsed {
  margin-left: var(--uj-sidebar-collapsed-width, 64px);
  width: calc(100% - var(--uj-sidebar-collapsed-width, 64px));
}

/* ========== MOBILE ========== */
@media (max-width: 768px) {
  .main-area, .main-area.collapsed { margin-left: 0 !important; width: 100%; }
  .content-area { padding: 16px; }
}

@media (max-width: 480px) {
  .content-area { padding: 12px; }
}

/* ========== CONTENT ========== */
.content-area {
  flex: 1;
  padding: 24px;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
}
.content-area--wide {
  max-width: none;
  padding-left: 16px;
  padding-right: 16px;
}
/* page transition handled by .page-* classes below */

.empty-page {
  border: 2px dashed #fcd34d;
  background: #fffbeb;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  color: #92400e;
  font-size: 14px;
}

/* Transitions */
.page-enter-active, .page-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.page-enter-from { opacity: 0; transform: translateY(4px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }
.brand-fade-enter-active, .brand-fade-leave-active { transition: all 0.2s ease; }
.brand-fade-enter-from, .brand-fade-leave-to { opacity: 0; transform: translateX(-4px); }
/* 下拉动效见 coachpro-mint-motion.scss */
</style>
