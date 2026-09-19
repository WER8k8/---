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
          <div v-for="group in categorizedNavGroups" :key="group.key" class="client-nav__group">
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
import { MenuOutlined } from '@ant-design/icons-vue';
import { useAuthStore } from '@/stores/auth';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { getAuthToken } from '@/utils/api';
import { provideTenantBrand } from '@/composables/useTenantBrand';
import { getClientMoreShellMenu } from '@/constants/proShellMenus';
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
  if (path === '/client/today') {
    return p === '/client/today';
  }
  if (path === '/client/dashboard') {
    return p === '/client/dashboard' || p === '/client/onboarding';
  }
  if (path === '/client/inquiries') {
    return p.startsWith('/client/inquir') || p.startsWith('/client/im');
  }
  if (path === '/client/products') {
    return (
      p.startsWith('/client/product')
      || p.startsWith('/client/content')
      || p.startsWith('/client/seo')
      || p.startsWith('/client/article-to-video')
    );
  }
  if (path === '/client/distribute') {
    return (
      p.startsWith('/client/distribute')
      || p.startsWith('/client/cross-platform')
      || p.startsWith('/client/publish')
      || p.startsWith('/client/queues/publish')
      || p.startsWith('/client/video-overseas')
      || p.startsWith('/client/video-studio')
    );
  }
  if (path === '/client/billing') {
    return (
      p.startsWith('/client/billing')
      || p.startsWith('/client/token')
      || p.startsWith('/client/invoice')
      || p.startsWith('/client/egress')
      || p.startsWith('/client/setting')
    );
  }
  return p === path || p.startsWith(`${path}/`);
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
    title: '经营中枢',
    items: [
      { label: '今日三步', path: '/client/today', icon: 'ThunderboltOutlined', highlight: true },
      { label: '经营概览', path: '/client/dashboard', icon: 'DashboardOutlined' },
      { label: '开通向导', path: '/client/onboarding', icon: 'CarryOutOutlined' },
    ],
  },
  {
    key: 'site',
    title: '独立站与多模态空间',
    items: [
      { label: '可视化建站', path: '/client/site-editor', icon: 'EditOutlined', highlight: true, badge: '核心' },
      { label: '模板社区', path: '/client/explore', icon: 'AppstoreOutlined', badge: 'Meoo' },
      { label: '专属技能', path: '/client/skills', icon: 'ThunderboltOutlined', badge: '新' },
      { label: '产品图片空间', path: '/client/product-images', icon: 'PictureOutlined' },
      { label: '视频空间', path: '/client/video-space', icon: 'VideoCameraOutlined' },
    ],
  },

  {
    key: 'leads',
    title: '拓客与商机',
    items: [
      { label: '询盘管理', path: '/client/inquiries', icon: 'CustomerServiceOutlined' },
      { label: '询盘队列', path: '/client/queues/inquiries', icon: 'OrderedListOutlined' },
      { label: '邮件营销', path: '/client/email-campaigns', icon: 'MailOutlined' },
      { label: '外贸工具指南', path: '/client/trade-tools', icon: 'QuestionCircleOutlined' },
    ],
  },
  {
    key: 'catalog',
    title: '发品与分发',
    items: [
      { label: '产品管理', path: '/client/products', icon: 'ShoppingOutlined' },
      { label: '内容管理', path: '/client/content', icon: 'FileOutlined' },
      { label: '多端分发', path: '/client/distribute', icon: 'SendOutlined' },
      { label: '跨平台数据', path: '/client/cross-platform', icon: 'BarChartOutlined' },
    ],
  },
  {
    key: 'operations',
    title: '履约与账户',
    items: [
      { label: '套餐与续费', path: '/client/billing', icon: 'AccountBookOutlined' },
      { label: 'AI 流量充值', path: '/client/tokens', icon: 'ThunderboltOutlined' },
      { label: '履约队列', path: '/client/queues/fulfillment', icon: 'CarryOutOutlined' },
      { label: '系统设置', path: '/client/settings', icon: 'SettingOutlined' },
    ],
  },
  {
    key: 'goodjob',
    title: '外贸履约',
    items: [
      { label: 'Hermes 任务', path: '/client/tasks', icon: 'NodeIndexOutlined' },
    ],
  },
];

const primaryMenuItems = [
  { label: '今日三步', path: '/client/today', icon: 'ThunderboltOutlined' },
  { label: '获客', path: '/client/inquiries', icon: 'CustomerServiceOutlined' },
  { label: '发品', path: '/client/products', icon: 'SendOutlined' },
  { label: '视频分发', path: '/client/distribute', icon: 'VideoCameraOutlined' },
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
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgb(74 155 140 / 0.25);
}
.client-header__name {
  font-size: 15px;
  font-weight: 600;
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
  font-weight: 700;
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
  font-weight: 600;
}
.client-nav__item--highlight:not(.client-nav__item--active) {
  color: #1e293b;
  font-weight: 600;
}
.client-nav__badge {
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9999px;
  background: #e0f2fe;
  color: #0369a1;
  margin-left: auto;
}
.client-nav__item--active .client-nav__badge {
  background: #d8f2e9;
  color: #2a6b60;
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
