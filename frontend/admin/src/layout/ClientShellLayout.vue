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
          <button
            v-for="item in primaryMenuItems"
            :key="item.path"
            type="button"
            class="client-nav__item"
            :class="{
              'client-nav__item--active': isActiveMenu(item.path),
              'client-nav__item--primary': item.path === '/client/today',
            }"
            @click="navigate(item.path)"
          >
            <YdNavIcon :name="item.icon" size="sm" :active="isActiveMenu(item.path)" />
            <span>{{ item.label }}</span>
          </button>
          <button
            type="button"
            class="client-nav__item client-nav__more"
            :class="{ 'client-nav__item--active': moreDrawerActive }"
            aria-haspopup="dialog"
            :aria-expanded="moreOpen"
            @click="moreOpen = true"
          >
            <YdNavIcon name="AppstoreOutlined" size="sm" :active="moreDrawerActive" />
            <span>更多功能</span>
          </button>
        </nav>
      </aside>
      <div v-if="mobileOpen" class="client-overlay" @click="mobileOpen = false" />

      <main id="main-content" class="client-content" tabindex="-1">
        <!-- 无 out-in 过渡，避免切页白屏闪 -->
        <router-view />
      </main>
    </div>
    <a-drawer
      v-model:open="moreOpen"
      title="更多功能"
      placement="left"
      :width="300"
      class="client-more-drawer"
      :body-style="{ padding: '8px 0' }"
    >
      <p class="client-more-drawer__hint">进阶工具收在这里；SEO/裂变等实验项需开实验室模式才显示。</p>
      <section v-for="group in moreMenuGroups" :key="group.title" class="client-more-drawer__group">
        <h3>{{ group.title }}</h3>
        <button
          v-for="item in group.children"
          :key="item.path"
          type="button"
          class="client-more-drawer__item"
          :class="{ 'client-more-drawer__item--active': isActiveMenu(item.path) }"
          @click="navigate(item.path)"
        >
          <YdNavIcon :name="item.icon" size="sm" :active="isActiveMenu(item.path)" />
          <span>{{ item.title }}</span>
        </button>
      </section>
    </a-drawer>
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

const primaryMenuItems = [
  { label: '今日三步', path: '/client/today', icon: 'ThunderboltOutlined' },
  { label: '获客', path: '/client/inquiries', icon: 'CustomerServiceOutlined' },
  { label: '发品', path: '/client/products', icon: 'SendOutlined' },
  { label: '视频分发', path: '/client/distribute', icon: 'VideoCameraOutlined' },
  { label: '账户', path: '/client/billing', icon: 'AccountBookOutlined' },
] as const;

const moreMenuGroups = computed(() => getClientMoreShellMenu());

const moreDrawerActive = computed(() =>
  moreMenuGroups.value.some((g) => g.children.some((item) => isActiveMenu(item.path))),
);

function navigate(path: string) {
  if (isActiveMenu(path)) {
    mobileOpen.value = false;
    moreOpen.value = false;
    return;
  }
  void router.push(path);
  mobileOpen.value = false;
  moreOpen.value = false;
}

async function logout() {
  await auth.logout();
  router.push('/login');
}

onMounted(async () => {
  uiPrefs.setAccentRole('client');
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
  box-shadow: 0 4px 12px rgb(37 99 235 / 0.3);
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
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: calc(100vh - var(--uj-header-h, 52px) - 24px);
}
.client-nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 11px 14px;
  border: none;
  border-radius: var(--uj-radius-md);
  background: transparent;
  color: var(--uj-text-secondary, #475569);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s ease, color 0.12s ease;
  font-family: inherit;
}
.client-nav__item:hover {
  background: #f8fafc;
}
.client-nav__item--active {
  background: var(--uj-brand-muted);
  color: var(--uj-brand-deep);
  font-weight: 600;
}
.client-nav__icon {
  font-size: 17px;
}
.client-content {
  flex: 1;
  min-width: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: var(--uj-space-page) 16px;
  box-sizing: border-box;
}
.client-overlay {
  display: none;
}
.client-more-drawer__hint {
  margin: 0 16px 12px;
  font-size: 12px;
  color: var(--uj-text-muted);
  line-height: 1.5;
}
.client-more-drawer__group {
  margin-bottom: 8px;
}
.client-more-drawer__group h3 {
  margin: 0;
  padding: 8px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--uj-text-muted);
}
.client-more-drawer__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--uj-text-secondary, #475569);
  font-size: 14px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.client-more-drawer__item:hover {
  background: #f8fafc;
}
.client-more-drawer__item--active {
  background: var(--uj-brand-muted);
  color: var(--uj-brand-deep);
  font-weight: 600;
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
