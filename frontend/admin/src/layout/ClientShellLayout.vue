/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="client-shell">
    <header class="client-header">
      <div class="client-header__left">
        <button type="button" class="client-header__menu" aria-label="菜单" @click="mobileOpen = !mobileOpen">
          <MenuOutlined />
        </button>
        <div class="client-header__logo">{{ brandMark }}</div>
        <div>
          <div class="client-header__name">{{ brand.company_name }}</div>
          <div class="client-header__tag">出海工作台</div>
        </div>
      </div>
      <div class="client-header__right">
        <a
          v-if="siteUrl !== '#'"
          :href="siteUrl"
          target="_blank"
          rel="noopener"
          class="client-header__link"
        >我的网站</a>
        <a-button type="text" size="small" danger @click="logout">退出</a-button>
      </div>
    </header>

    <YdClientPlanUsageBar v-if="showPlanBar" />

    <div class="client-body">
      <aside class="client-sidebar" :class="{ 'client-sidebar--open': mobileOpen }">
        <nav class="client-nav" aria-label="主要功能">
          <div v-for="group in visibleNavGroups" :key="group.key" class="client-nav__group">
            <div class="client-nav__group-title">{{ group.title }}</div>
            <button
              v-for="item in group.items"
              :key="item.path"
              type="button"
              class="client-nav__item"
              :class="{
                'client-nav__item--active': isActiveMenu(item.path),
                'client-nav__item--highlight': item.highlight,
              }"
              @click="navigate(item.path)"
            >
              <YdNavIcon :name="item.icon" size="sm" :active="isActiveMenu(item.path)" />
              <span class="client-nav__item-label">{{ item.label }}</span>
              <span v-if="item.badge" class="client-nav__badge">{{ item.badge }}</span>
            </button>
          </div>
          <div class="client-nav__more">
            <button
              type="button"
              class="client-nav__more-toggle"
              :aria-expanded="moreOpen"
              @click="moreOpen = !moreOpen"
            >
              <AppstoreOutlined />
              <span class="client-nav__item-label">更多功能</span>
              <span class="client-nav__more-caret">{{ moreOpen ? '−' : '+' }}</span>
            </button>
            <div v-if="moreOpen" class="client-nav__more-panel">
              <div v-for="group in moreNavGroups" :key="group.key" class="client-nav__group">
                <div class="client-nav__group-title">{{ group.title }}</div>
                <button
                  v-for="item in group.items"
                  :key="item.path"
                  type="button"
                  class="client-nav__item"
                  :class="{ 'client-nav__item--active': isActiveMenu(item.path) }"
                  @click="navigate(item.path)"
                >
                  <YdNavIcon :name="item.icon" size="sm" :active="isActiveMenu(item.path)" />
                  <span class="client-nav__item-label">{{ item.label }}</span>
                </button>
              </div>
            </div>
          </div>
        </nav>
      </aside>
      <div v-if="mobileOpen" class="client-overlay" @click="mobileOpen = false" />

      <main id="main-content" class="client-content" tabindex="-1">
        <!-- 无 out-in 过渡，避免切页白屏闪 -->
        <router-view />
      </main>
    </div>
    <UBrainAssistant />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { MenuOutlined, AppstoreOutlined } from '@ant-design/icons-vue';
import { useAuthStore } from '@/stores/auth';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { getAuthToken, apiGet } from '@/utils/api';
import { provideTenantBrand } from '@/composables/useTenantBrand';
import { getClientShellMenu, CLIENT_PRIMARY_SHELL_PATHS } from '@/constants/proShellMenus';
import UBrainAssistant from '@/components/UBrainAssistant.vue';
import { YdNavIcon, YdClientPlanUsageBar } from '@/components/youding';
import '@/styles/client-experience-2026.scss';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const uiPrefs = useUiPreferencesStore();
const mobileOpen = ref(false);
const moreOpen = ref(false);

const tenantBrand = provideTenantBrand();
const brand = computed(() => ({
  company_name: tenantBrand.loaded.value
    ? tenantBrand.companyName.value
    : tenantBrand.companyName.value || '工作台',
}));
const brandMark = computed(() => (brand.value.company_name || '工').charAt(0));
const siteUrl = computed(() => tenantBrand.siteUrl.value || '#');
const showPlanBar = computed(() => Boolean(getAuthToken()) && route.path.startsWith('/client'));

function isActiveMenu(path: string) {
  const p = route.path;
  // 精确优先，避免 /client/product 误亮 /client/product-images
  const exact = (base: string) => p === base || p.startsWith(`${base}/`);
  switch (path) {
    case '/client/today':
      return p === '/client/today';
    case '/client/onboarding':
      return exact('/client/onboarding');
    case '/client/dashboard':
      return exact('/client/dashboard');
    case '/client/inquiries':
      return p === '/client/inquiries' || p.startsWith('/client/im');
    case '/client/queues/inquiries':
      return exact('/client/queues/inquiries');
    case '/client/acquisition-ops':
      return exact('/client/acquisition-ops');
    case '/client/email-campaigns':
      return exact('/client/email-campaigns');
    case '/client/keyword-research':
      return exact('/client/keyword-research');
    case '/client/site-editor':
      return exact('/client/site-editor');
    case '/client/product-images':
      return exact('/client/product-images');
    case '/client/video-space':
      return exact('/client/video-space');
    case '/client/explore':
      return exact('/client/explore') || exact('/client/skills') || exact('/client/plugin-market');
    case '/client/products':
      return p === '/client/products' || p.startsWith('/client/products/');
    case '/client/content':
      return p === '/client/content' || p.startsWith('/client/content/') || p.startsWith('/client/seo');
    case '/client/distribute':
      return (
        exact('/client/distribute')
        || exact('/client/queues/publish')
        || exact('/client/video-overseas')
        || exact('/client/video-studio')
        || exact('/client/article-to-video')
      );
    case '/client/cross-platform':
      return exact('/client/cross-platform') || exact('/client/engage');
    case '/client/document-maker':
    case '/client/queues/fulfillment':
      return exact('/client/document-maker') || exact('/client/export-quote') || exact('/client/queues/fulfillment');
    case '/client/tasks':
      return exact('/client/tasks');
    case '/client/billing':
      return exact('/client/billing') || exact('/client/invoices');
    case '/client/tokens':
      return exact('/client/tokens');
    case '/client/settings':
      return exact('/client/settings') || exact('/client/egress') || exact('/client/plan-gate');
    case '/client/traffic':
      return exact('/client/traffic');
    case '/client/trade-tools':
      return exact('/client/trade-tools');
    case '/client/foreign-trade-team':
      return exact('/client/foreign-trade-team');
    case '/client/referral':
      return exact('/client/referral');
    case '/client/seo':
      return exact('/client/seo');
    case '/client/seo-publish':
      return exact('/client/seo-publish');
    case '/client/queues/publish':
      return exact('/client/queues/publish');
    case '/client/engage':
      return exact('/client/engage');
    case '/client/media-factory':
      return exact('/client/media-factory');
    case '/client/article-to-video':
      return exact('/client/article-to-video');
    case '/client/ai-scenarios':
      return exact('/client/ai-scenarios');
    case '/client/video-studio':
      return exact('/client/video-studio');
    case '/client/video-overseas':
      return exact('/client/video-overseas');
    case '/client/skills':
      return exact('/client/skills');
    case '/client/plugin-market':
      return exact('/client/plugin-market');
    case '/client/product-candidates':
      return exact('/client/product-candidates');
    case '/client/assistant':
      return exact('/client/assistant');
    case '/client/copilot':
      return exact('/client/copilot');
    case '/client/geo-visibility':
      return exact('/client/geo-visibility');
    case '/client/app':
      return exact('/client/app');
    case '/client/invoices':
      return exact('/client/invoices');
    case '/client/egress':
      return exact('/client/egress');
    case '/client/plan-gate':
      return exact('/client/plan-gate');
    default:
      return p === path || p.startsWith(`${path}/`);
  }
}

interface CategorizedNavItem {
  label: string;
  path: string;
  icon: string;
  badge?: string;
  highlight?: boolean;
}

interface CategorizedNavGroup {
  key: string;
  title: string;
  items: CategorizedNavItem[];
}

const categorizedNavGroups: CategorizedNavGroup[] = [
  {
    key: 'overview',
    title: '今天先干这些',
    items: [
      { label: '今日三步', path: '/client/today', icon: 'ThunderboltOutlined', highlight: true },
      { label: '开通向导', path: '/client/onboarding', icon: 'CarryOutOutlined' },
      { label: '经营概览', path: '/client/dashboard', icon: 'DashboardOutlined' },
    ],
  },
  {
    key: 'leads',
    title: '找客户',
    items: [
      { label: '询盘管理', path: '/client/inquiries', icon: 'CustomerServiceOutlined' },
      { label: '询盘队列', path: '/client/queues/inquiries', icon: 'OrderedListOutlined' },
      { label: '获客作战台', path: '/client/acquisition-ops', icon: 'AimOutlined', highlight: true },
      { label: '关键词热度', path: '/client/keyword-research', icon: 'RiseOutlined', highlight: true },
      { label: '邮件开发', path: '/client/email-campaigns', icon: 'MailOutlined' },
    ],
  },
  {
    key: 'site',
    title: '独立站与素材',
    items: [
      { label: '可视化建站', path: '/client/site-editor', icon: 'EditOutlined', highlight: true, badge: '核心' },
      { label: '产品图片', path: '/client/product-images', icon: 'PictureOutlined' },
      { label: '视频素材', path: '/client/video-space', icon: 'VideoCameraOutlined' },
      { label: '模板与技能', path: '/client/explore', icon: 'AppstoreOutlined' },
    ],
  },
  {
    key: 'catalog',
    title: '发品与推广',
    items: [
      { label: '产品管理', path: '/client/products', icon: 'ShoppingOutlined' },
      { label: '内容管理', path: '/client/content', icon: 'FileOutlined' },
      { label: '多端分发', path: '/client/distribute', icon: 'SendOutlined' },
      { label: '跨平台数据', path: '/client/cross-platform', icon: 'BarChartOutlined' },
    ],
  },
  {
    key: 'operations',
    title: '成交与账户',
    items: [
      { label: '制单中心', path: '/client/document-maker', icon: 'FileTextOutlined', highlight: true },
      { label: '履约队列', path: '/client/queues/fulfillment', icon: 'CarryOutOutlined', highlight: true },
      { label: '我的任务', path: '/client/tasks', icon: 'NodeIndexOutlined' },
      { label: '套餐续费', path: '/client/billing', icon: 'AccountBookOutlined' },
      { label: 'AI 用量充值', path: '/client/tokens', icon: 'ThunderboltOutlined' },
      { label: '系统设置', path: '/client/settings', icon: 'SettingOutlined' },
    ],
  },
];

/** 开通向导完成后：从顶栏隐藏，收进「系统设置」（设置页内保留入口） */
const onboardingCompleted = ref(false);

const visibleNavGroups = computed<CategorizedNavGroup[]>(() =>
  categorizedNavGroups
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => !(item.path === '/client/onboarding' && onboardingCompleted.value),
      ),
    }))
    .filter((group) => group.items.length > 0),
);

const primaryPathSet = new Set<string>(CLIENT_PRIMARY_SHELL_PATHS);

const moreNavGroups = computed<CategorizedNavGroup[]>(() => {
  const groups: CategorizedNavGroup[] = [];
  for (const group of getClientShellMenu()) {
    const items: CategorizedNavItem[] = [];
    const seen = new Set<string>();
    for (const child of group.children) {
      if (primaryPathSet.has(child.path) || seen.has(child.path)) continue;
      seen.add(child.path);
      items.push({
        label: child.title,
        path: child.path,
        icon: child.icon,
        highlight: false,
      });
    }
    if (items.length > 0) {
      groups.push({ key: `more-${group.title}`, title: group.title, items });
    }
  }
  return groups;
});

async function loadOnboardingStatus() {
  if (!getAuthToken()) return;
  try {
    const status = await apiGet<{
      wizard_completed?: boolean;
      autopilot_completed?: boolean;
    }>('/tenants/self/onboarding-status');
    onboardingCompleted.value = Boolean(
      status?.wizard_completed || status?.autopilot_completed,
    );
  } catch {
    /* 接口不可用（未登录/无权限）时保持显示，避免误隐藏 */
  }
}

const primaryMenuItems = [
  { label: '今日', path: '/client/today', icon: 'ThunderboltOutlined' },
  { label: '找客户', path: '/client/inquiries', icon: 'CustomerServiceOutlined' },
  { label: '发品', path: '/client/products', icon: 'SendOutlined' },
  { label: '履约', path: '/client/queues/fulfillment', icon: 'CarryOutOutlined' },
  { label: '账户', path: '/client/billing', icon: 'AccountBookOutlined' },
] as const;

function navigate(path: string) {
  if (isActiveMenu(path)) {
    mobileOpen.value = false;
    return;
  }
  void router.push(path);
  mobileOpen.value = false;
}

async function logout() {
  await auth.logout();
  router.push('/login');
}

onMounted(async () => {
  if (uiPrefs.accentRole !== 'client') {
    uiPrefs.setAccentRole('client');
  }
  await tenantBrand.load();
  void loadOnboardingStatus();
});
</script>

<style scoped lang="scss">
.client-shell {
  min-height: 100vh;
  background: var(--uj-bg-page);
}
.client-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--uj-header-h, 52px);
  padding: 0 20px;
  background: var(--uj-bg-card);
  border-bottom: 1px solid var(--uj-border);
  box-shadow: var(--uj-shadow-sm);
  position: sticky;
  top: 0;
  z-index: 40;
}
.client-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.client-header__menu {
  display: none;
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  color: var(--uj-text-muted);
}
.client-header__logo {
  width: 36px;
  height: 36px;
  border-radius: var(--uj-radius-sm);
  background: linear-gradient(135deg, var(--uj-brand), var(--uj-brand-deep));
  color: #fff;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgb(74 155 140 / 0.25);
}
.client-header__name {
  font-size: 15px;
  font-weight: 500;
}
.client-header__tag {
  font-size: 12px;
  color: var(--uj-text-muted);
}
.client-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.client-header__link {
  font-size: 15px;
  text-decoration: none;
  color: var(--uj-brand);
}
.client-body {
  display: flex;
  min-height: calc(100vh - var(--uj-header-h, 52px));
}
.client-sidebar {
  width: var(--uj-client-sidebar-w, 232px);
  flex-shrink: 0;
  background: var(--uj-bg-card);
  border-right: 1px solid var(--uj-border);
  position: sticky;
  top: var(--uj-header-h, 52px);
  height: calc(100vh - var(--uj-header-h, 52px));
  overflow-y: auto;
}
.client-nav {
  padding: 14px 10px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: calc(100vh - var(--uj-header-h, 52px) - 24px);
}
.client-nav__group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.client-nav__group-title {
  padding: 0 12px 6px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #94a3b8;
}
.client-nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: var(--uj-radius-md, 8px);
  background: transparent;
  color: var(--uj-text-secondary, #475569);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  position: relative;
}
.client-nav__item:hover {
  background: #f1f5f9;
  color: #1e293b;
}
.client-nav__item-label {
  flex: 1;
  min-width: 0;
  truncate: true;
}
.client-nav__item--active {
  background: var(--uj-brand-muted, rgba(74, 155, 140, 0.12));
  color: var(--uj-brand-deep, #2a6b60) !important;
  font-weight: 500;
}
.client-nav__item--highlight:not(.client-nav__item--active) {
  color: #1e293b;
  font-weight: 500;
}
.client-nav__badge {
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 500;
  border-radius: 9999px;
  background: #e0f2fe;
  color: #0369a1;
  margin-left: auto;
}
.client-nav__item--active .client-nav__badge {
  background: #d8f2e9;
  color: #2a6b60;
}
.client-nav__more {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--uj-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.client-nav__more-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: var(--uj-radius-md, 8px);
  background: transparent;
  color: var(--uj-text-secondary, #475569);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.client-nav__more-toggle:hover {
  background: #f1f5f9;
  color: #1e293b;
}
.client-nav__more-caret {
  margin-left: auto;
  font-size: 14px;
  color: var(--uj-text-muted);
}
.client-nav__more-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 8px;
}
.client-content {
  flex: 1;
  min-width: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: var(--uj-space-page, 16px) 20px;
  box-sizing: border-box;
}
.client-overlay {
  display: none;
}
@media (max-width: 768px) {
  .client-header__menu {
    display: flex;
  }
  .client-sidebar {
    position: fixed;
    left: 0;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: var(--uj-shadow-login);
  }
  .client-sidebar--open {
    transform: translateX(0);
  }
  .client-overlay {
    display: block;
    position: fixed;
    inset: 0;
    top: var(--uj-header-h, 52px);
    background: rgb(15 23 42 / 0.4);
    z-index: 45;
  }
  .client-content {
    padding: 16px;
  }
}
</style>
