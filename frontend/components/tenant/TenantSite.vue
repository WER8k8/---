<template>
  <div class="tenant-site-root" :dir="documentDir" :class="{ 'tenant-site-root--rtl': isRtl }">
  <div
    class="tenant-site min-h-screen flex flex-col"
    :style="siteThemeVars"
  >
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto" :style="{ borderColor: themePrimary }"></div>
        <p class="mt-4 text-gray-500">{{ tSite('loading') }}</p>
      </div>
    </div>

    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center max-w-md mx-auto p-8">
        <h1 class="text-2xl font-bold text-gray-800 mb-2">{{ tSite('site_unavailable') }}</h1>
        <p class="text-gray-500">{{ error }}</p>
      </div>
    </div>

    <template v-else-if="tenant">

      <!-- 可视化建站导出页（GrapesJS 保存的 HTML/CSS） -->
      <div v-if="hasVisualSite" class="tenant-visual-site">
        <component :is="'style'" v-if="visualSiteCss">{{ visualSiteCss }}</component>
        <div ref="visualHtmlRef" class="tenant-visual-site__html" v-html="visualSiteHtml" />
      </div>

      <template v-else>
      <div class="tenant-topbar" :style="{ backgroundColor: themePrimary }">
        <div class="tenant-container tenant-topbar-inner">
          <a
            v-for="ch in topbarChannels"
            :key="`${ch.channel_type}-${ch.value}`"
            :href="topbarContactHref(ch)"
            :target="isExternalContactChannel(ch) ? '_blank' : undefined"
            :rel="isExternalContactChannel(ch) ? 'noopener noreferrer' : undefined"
          >
            {{ ch.label }}: {{ ch.value }}
          </a>
        </div>
      </div>

      <!-- 导航 -->
      <header class="tenant-header sticky top-0 z-50 bg-white shadow-sm border-b border-gray-100">
        <nav class="tenant-container">
          <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-3 min-w-0">
              <img v-if="tenant.brand.logo_url" :src="tenant.brand.logo_url" :alt="companyName" class="h-10 w-auto object-contain" />
              <div class="min-w-0">
                <div class="font-bold text-gray-900 truncate">{{ companyName }}</div>
                <div v-if="brandTagline" class="text-xs text-gray-500 truncate">{{ brandTagline }}</div>
              </div>
            </div>
            <div class="hidden md:flex items-center gap-6">
              <a v-for="item in navItems" :key="item.key" :href="item.href" class="tenant-nav-link" :class="{ active: activeNav === item.key }">
                {{ item.label }}
              </a>
            </div>
            <button
              type="button"
              class="tenant-mobile-menu-btn md:hidden"
              :aria-expanded="mobileMenuOpen"
              aria-controls="tenant-mobile-nav"
              @click="toggleMobileMenu"
            >
              <span class="tenant-sr-only">{{ mobileMenuOpen ? tSite('menu_close') : tSite('menu_open') }}</span>
              <span class="tenant-mobile-menu-icon" :class="{ 'is-open': mobileMenuOpen }">
                <span /><span /><span />
              </span>
            </button>
          </div>
          <Transition name="tenant-mobile-nav">
            <div
              v-if="mobileMenuOpen"
              id="tenant-mobile-nav"
              class="tenant-mobile-nav md:hidden"
              role="dialog"
              aria-modal="true"
              :aria-label="tSite('menu_open')"
            >
              <div class="tenant-mobile-nav-inner">
                <a
                  v-for="item in navItems"
                  :key="item.key"
                  :href="item.href"
                  class="tenant-mobile-nav-link"
                  :class="{ active: activeNav === item.key }"
                  @click="closeMobileMenu(); activeNav = item.key"
                >
                  {{ item.label }}
                </a>
                <a href="#contact" class="tenant-mobile-nav-cta" @click="closeMobileMenu">{{ ctaPrimary }}</a>
              </div>
            </div>
          </Transition>
          <div
            v-if="mobileMenuOpen"
            class="tenant-mobile-backdrop md:hidden"
            aria-hidden="true"
            @click="closeMobileMenu"
          />
        </nav>
      </header>

      <!-- Hero 左右分栏（luyang / cattuong 企业叙事） -->
      <section id="home" class="tenant-hero" :style="{ backgroundColor: themeHeroBg }">
        <div class="tenant-container tenant-hero-grid">
          <div class="tenant-hero-copy">
            <p v-if="primaryPromise" class="tenant-hero-eyebrow tenant-hero-eyebrow--promise">{{ primaryPromise }}</p>
            <p v-else-if="establishedYear" class="tenant-hero-eyebrow">{{ tSite('hero_since', { year: establishedYear }) }}</p>
            <h1 class="tenant-hero-title">{{ heroTitle }}</h1>
            <p class="tenant-hero-desc">{{ heroDescription }}</p>
            <div v-if="trustBadges.length" class="tenant-trust-badges">
              <span v-for="(badge, i) in trustBadges" :key="i" class="tenant-trust-badge">{{ badge }}</span>
            </div>
            <div class="tenant-hero-actions">
              <a href="#contact" class="tenant-btn tenant-btn-primary">{{ ctaPrimary }}</a>
              <a href="#contact" class="tenant-btn tenant-btn-outline">{{ ctaSecondary }}</a>
            </div>
            <p v-if="inquiryHook" class="tenant-inquiry-hook">{{ inquiryHook }}</p>
          </div>
          <div class="tenant-hero-media">
            <img v-if="heroImage" :src="resolveMediaUrl(heroImage)" :alt="heroTitle" class="tenant-hero-img" />
            <div v-else class="tenant-hero-placeholder" :style="heroPlaceholderStyle">
              <div class="tenant-hero-placeholder-pattern" aria-hidden="true">
                <svg viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="8" y="52" width="48" height="56" rx="4" stroke="currentColor" stroke-width="2" opacity="0.35" />
                  <rect x="72" y="28" width="56" height="80" rx="4" stroke="currentColor" stroke-width="2" opacity="0.5" />
                  <rect x="144" y="44" width="48" height="64" rx="4" stroke="currentColor" stroke-width="2" opacity="0.35" />
                  <path d="M20 52 L32 36 L44 52" stroke="currentColor" stroke-width="2" opacity="0.4" />
                  <path d="M84 28 L100 12 L116 28" stroke="currentColor" stroke-width="2" opacity="0.55" />
                  <path d="M156 44 L168 30 L180 44" stroke="currentColor" stroke-width="2" opacity="0.4" />
                </svg>
              </div>
              <div class="tenant-hero-placeholder-content">
                <img
                  v-if="tenant.brand.logo_url"
                  :src="tenant.brand.logo_url"
                  :alt="companyName"
                  class="tenant-hero-placeholder-logo"
                />
                <span class="tenant-hero-placeholder-name">{{ companyName }}</span>
                <span v-if="brandTagline" class="tenant-hero-placeholder-tagline">{{ brandTagline }}</span>
                <span v-else class="tenant-hero-placeholder-hint">{{ heroPlaceholderHint }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 大数字条（rsref / luyang WHY CHOOSE） -->
      <section v-if="stats.length" class="tenant-stats" :style="{ backgroundColor: themePrimary }">
        <div class="tenant-container">
          <p class="tenant-stats-eyebrow">{{ tSite('stats_eyebrow') }}</p>
          <h2 class="tenant-stats-title">{{ tSite('stats_title') }}</h2>
          <div class="tenant-stats-grid">
            <div v-for="(stat, i) in stats" :key="i" class="tenant-stat-item">
              <div class="tenant-stat-value">{{ stat.value }}</div>
              <div class="tenant-stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="serviceStages.length" class="tenant-section bg-white">
        <div class="tenant-container">
          <p class="tenant-stats-eyebrow">{{ tSite('section_stages_eyebrow') }}</p>
          <h2 class="tenant-section-title">{{ tSite('section_stages_title') }}</h2>
          <p class="tenant-section-desc">{{ tSite('section_stages_desc') }}</p>
          <div class="tenant-stage-grid">
            <article v-for="(stage, i) in serviceStages" :key="i" class="tenant-stage-card">
              <div class="tenant-stage-num">{{ stage.stage || String(i + 1).padStart(2, '0') }}</div>
              <h3>{{ stage.title }}</h3>
              <p v-if="stage.description">{{ stage.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <!-- 全领域解决方案（cnabm / shenzhou / rockwool） -->
      <section v-if="solutions.length" id="solutions" class="tenant-section bg-gray-50">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('section_solutions') }}</h2>
          <p class="tenant-section-desc">{{ tSite('section_solutions_desc') }}</p>
          <div class="tenant-solution-grid">
            <article v-for="(sol, i) in solutions" :key="i" class="tenant-solution-card">
              <div class="tenant-solution-segment">{{ sol.segment }}</div>
              <h3>{{ sol.title }}</h3>
              <p>{{ sol.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <!-- 四大优势（证据链） -->
      <section v-if="advantages.length" id="advantages" class="tenant-section bg-gray-50">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ sectionTitle }}</h2>
          <div class="tenant-adv-grid">
            <article v-for="(adv, i) in advantages" :key="i" class="tenant-adv-card">
              <div class="tenant-adv-icon">{{ i + 1 }}</div>
              <h3>{{ adv.title }}</h3>
              <p>{{ adv.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <!-- 产品分类 -->
      <section v-if="categories.length" id="categories" class="tenant-section bg-white">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('section_categories') }}</h2>
          <p class="tenant-section-desc">{{ tSite('section_categories_desc') }}</p>
          <div class="tenant-card-grid">
            <article v-for="(cat, i) in categories" :key="i" class="tenant-card">
              <h3>{{ cat.name }}</h3>
              <p>{{ cat.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <!-- 产品列表（tingertech 风格） -->
      <section id="products" class="tenant-section bg-gray-50">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ productsTitle }}</h2>
          <p v-if="productsDescription" class="tenant-section-desc">{{ productsDescription }}</p>
          <p v-else class="tenant-section-desc">{{ tSite('section_products_desc') }}</p>
          <div class="tenant-card-grid">
            <article v-for="(item, i) in productItems" :key="i" class="tenant-card tenant-product-card">
              <div class="tenant-product-thumb">
                <img v-if="item.image" :src="resolveMediaUrl(item.image)" :alt="item.name" class="tenant-product-img" />
              </div>
              <h3>{{ item.name }}</h3>
              <p>{{ item.summary }}</p>
              <a href="#contact" class="tenant-link">{{ tSite('inquiry_link') }}</a>
            </article>
          </div>
        </div>
      </section>

      <!-- 应用场景 -->
      <section v-if="applications.length" id="applications" class="tenant-section bg-white">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ applicationsTitle }}</h2>
          <div class="tenant-card-grid tenant-card-grid--3">
            <article v-for="(app, i) in applications" :key="i" class="tenant-card">
              <h3>{{ app.title }}</h3>
              <p>{{ app.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section v-if="knowledgeTopics.length" class="tenant-section bg-gray-50">
        <div class="tenant-container">
          <p class="tenant-stats-eyebrow">{{ tSite('section_knowledge_eyebrow') }}</p>
          <h2 class="tenant-section-title">{{ tSite('section_knowledge_title') }}</h2>
          <p class="tenant-section-desc">{{ tSite('section_knowledge_desc') }}</p>
          <div class="tenant-card-grid">
            <article v-for="(topic, i) in knowledgeTopics" :key="i" class="tenant-card">
              <h3>{{ topic.title }}</h3>
              <p v-if="topic.hook">{{ topic.hook }}</p>
              <a href="#contact" class="tenant-link">{{ tSite('inquiry_link') }}</a>
            </article>
          </div>
        </div>
      </section>

      <!-- 关于（cattuong Mission / Vision / Timeline） -->
      <section v-if="aboutText || mission || vision" id="about" class="tenant-section bg-white">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('section_about', { name: companyName }) }}</h2>
          <p v-if="aboutText" class="tenant-about-text">{{ aboutText }}</p>
          <div v-if="mission || vision" class="tenant-mv-grid">
            <article v-if="mission" class="tenant-mv-card">
              <h3 class="tenant-mv-heading">{{ tSite('mission') }}</h3>
              <p class="tenant-mv-text">{{ mission }}</p>
            </article>
            <article v-if="vision" class="tenant-mv-card">
              <h3 class="tenant-mv-heading">{{ tSite('vision') }}</h3>
              <p class="tenant-mv-text">{{ vision }}</p>
            </article>
          </div>
          <p v-if="capacitySummary" class="tenant-capacity">{{ capacitySummary }}</p>
          <div v-if="milestones.length" class="tenant-timeline">
            <h3 class="tenant-timeline-heading">{{ tSite('company_history') }}</h3>
            <div class="tenant-timeline-track">
              <article v-for="(m, i) in milestones" :key="i" class="tenant-timeline-item">
                <div class="tenant-timeline-year">{{ m.year }}</div>
                <div class="tenant-timeline-body">
                  <h4>{{ m.title }}</h4>
                  <p>{{ m.description }}</p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <!-- 视频 -->
      <section v-if="videos.length" id="videos" class="tenant-section bg-gray-50">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('video_center') }}</h2>
          <div class="tenant-card-grid">
            <article v-for="v in videos" :key="v.id" class="tenant-card p-0 overflow-hidden">
              <div class="aspect-video bg-black">
                <video v-if="v.playback_url" :src="v.playback_url" controls preload="metadata" class="w-full h-full object-contain" />
              </div>
              <div class="p-4">
                <h3 class="font-semibold">{{ v.title }}</h3>
                <a href="#contact" class="tenant-link mt-2 inline-block">{{ tSite('inquiry_link') }}</a>
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- 买家问答（Answer Sidecar iframe） -->
      <section v-if="forumEmbed?.enabled && forumEmbed.iframe_src" id="forum" class="tenant-section bg-white">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('nav_qa') }}</h2>
          <p v-if="forumEmbed.honest_note" class="text-sm text-gray-500 mb-4">{{ forumEmbed.honest_note }}</p>
          <iframe
            :src="forumEmbed.iframe_src"
            class="tenant-forum-iframe"
            :title="tSite('nav_qa')"
            loading="lazy"
          />
        </div>
      </section>

      <!-- 联系 -->
      <section id="contact" class="tenant-section bg-white">
        <div class="tenant-container">
          <h2 class="tenant-section-title">{{ tSite('section_contact') }}</h2>
          <p v-if="inquiryPrompt" class="tenant-inquiry-banner">{{ inquiryPrompt }}</p>
          <div class="tenant-contact-grid">
            <a
              v-for="ch in contactDisplayChannels"
              :key="`${ch.channel_type}-${ch.value}`"
              :href="topbarContactHref(ch)"
              class="tenant-contact-item tenant-contact-item--link"
              :target="isExternalContactChannel(ch) ? '_blank' : undefined"
              :rel="isExternalContactChannel(ch) ? 'noopener noreferrer' : undefined"
            >
              <strong>{{ ch.label }}</strong><span>{{ ch.value }}</span>
            </a>
            <div v-if="factoryAddress" class="tenant-contact-item">
              <strong>{{ tSite('factory_label') }}</strong><span>{{ factoryAddress }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 页脚 -->
      <footer class="tenant-footer" :style="{ backgroundColor: themePrimary }">
        <div class="tenant-container tenant-footer-grid">
          <div>
            <div class="font-bold text-lg mb-2">{{ companyName }}</div>
            <p class="text-white/70 text-sm">{{ brandTagline }}</p>
          </div>
          <div>
            <div class="font-semibold mb-2">{{ tSite('footer_quick_links') }}</div>
            <a v-for="item in navItems" :key="item.key" :href="item.href" class="block text-white/70 text-sm py-0.5 hover:text-white">{{ item.label }}</a>
          </div>
          <div>
            <div class="font-semibold mb-2">{{ tSite('footer_contact') }}</div>
            <a
              v-for="ch in contactDisplayChannels"
              :key="`footer-${ch.channel_type}-${ch.value}`"
              :href="topbarContactHref(ch)"
              class="block text-white/70 text-sm py-0.5 hover:text-white"
            >
              {{ ch.label }}: {{ ch.value }}
            </a>
          </div>
        </div>
        <div class="tenant-container text-center text-white/50 text-xs pt-6 border-t border-white/10 mt-6">
          {{ footerText }}
        </div>
      </footer>
      </template>
    </template>
  </div>

  <!-- 移动端底部快捷操作栏 -->
  <nav
    v-if="tenant && !loading && !error && showMobileActionBar"
    class="tenant-mobile-action-bar md:hidden"
    :style="{ gridTemplateColumns: `repeat(${Math.max(mobileQuickActions.length, 1)}, minmax(0, 1fr))` }"
    :aria-label="tSite('mobile_quick_actions')"
  >
    <a
      v-for="action in mobileQuickActions"
      :key="action.key"
      :href="action.href"
      class="tenant-mobile-action-btn"
      :class="{ 'is-primary': action.primary }"
      :target="action.external ? '_blank' : undefined"
      :rel="action.external ? 'noopener noreferrer' : undefined"
      @click="onMobileActionClick(action)"
    >
      <span v-if="action.icon" class="tenant-mobile-action-icon" aria-hidden="true">{{ action.icon }}</span>
      <span class="tenant-mobile-action-label">{{ action.label }}</span>
    </a>
  </nav>

  <!-- 旺财外置引导挂件：固定视口跟随滚动，不暴露 Agent 信息 -->
  <TenantSiteCompanion
    v-if="tenant && !loading && !error"
    :company-name="companyName"
    :phone="contactPhone"
    :email="contactEmail"
    :whatsapp="contactWhatsapp"
    :wechat="contactWechat"
    :qq="contactQq"
    :accent="themePrimary"
    :product-hint="productHint"
    :tenant-domain="tenant.domain"
    :api-base="apiBase"
    :visitor-language="visitorLanguage"
    :visitor-country="visitorCountry"
    :cn-compliant-only="cnCompliantOnly"
    :wangcai-ui="wangcaiUi"
    :contact-channels="effectiveChannels"
    :trade-qa-enabled="tradeQaEnabled"
    :is-rtl="isRtl"
  />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { bindVisualSiteInquiryForms } from '../../composables/useVisualSiteInquiryBinder';
import { bindVisualSiteNavLinks } from '../../composables/useVisualSiteNavBinder';
import { resolveTenantDomainFromRoute, useVisitorLocale } from '../../composables/useVisitorLocale';
import {
  isExternalContactChannel,
  topbarContactHref,
  useTenantVisitorContacts,
} from '../../composables/useTenantVisitorContacts';
import { useTenantMediaUrl } from '../../composables/useTenantMediaUrl';

const { resolveMediaUrl } = useTenantMediaUrl();

interface BrandColors {
  primary: string;
  secondary: string;
  accent: string;
}

interface SiteCategory {
  name: string;
  description?: string;
}

interface SiteApplication {
  title: string;
  description?: string;
}

interface SiteAdvantage {
  title: string;
  description?: string;
}

interface SiteStat {
  value: string;
  label: string;
}

interface SiteMilestone {
  year: string;
  title: string;
  description?: string;
}

interface SiteSolution {
  segment: string;
  title: string;
  description?: string;
}

interface ProductItem {
  name: string;
  summary?: string;
  image?: string;
}

interface SiteContent {
  brand?: { name?: string; tagline?: string };
  footer?: { text?: string };
  theme?: { headerBg?: string; heroBg?: string; footerBg?: string };
  pages?: Record<string, Record<string, unknown>>;
  visualEditor?: { html?: string; css?: string; templateId?: string };
}

interface TenantBrand {
  site_title: string;
  logo_url: string;
  brand_colors: BrandColors;
  product_categories: string[];
  company_name: string;
  slogan: string;
  about_summary: string;
  contact_phone: string;
  contact_email: string;
  footer_text: string;
  custom_css: string;
  site_content?: SiteContent | null;
}

interface TenantInfo {
  id: string;
  name: string;
  domain: string;
  status: string;
  plan_code: string | null;
  brand: TenantBrand;
  is_online: boolean;
}

interface NavItem {
  key: string;
  label: string;
  href: string;
}

interface TenantVideo {
  id: string;
  title: string;
  playback_url?: string;
}

const props = withDefaults(
  defineProps<{
    subdomain?: string;
    apiBase?: string;
    visualPage?: 'home' | 'products' | 'about' | 'contact';
  }>(),
  { subdomain: '', apiBase: '/api/v1', visualPage: 'home' },
);

const loading = ref(true);
const error = ref<string | null>(null);
const tenant = ref<TenantInfo | null>(null);
const visualHtmlRef = ref<HTMLElement | null>(null);
const activeNav = ref('home');
const mobileMenuOpen = ref(false);
const contactSectionVisible = ref(false);
const videos = ref<TenantVideo[]>([]);
const forumEmbed = ref<{ enabled?: boolean; iframe_src?: string; honest_note?: string } | null>(null);
let navObserver: IntersectionObserver | null = null;

const {
  fetchVisitorContext,
  tSite,
  wangcaiUi,
  language: visitorLanguage,
  countryCode: visitorCountry,
  contactChannels,
  cnCompliantOnly,
  tradeQaEnabled,
  context: visitorContext,
} = useVisitorLocale(
  () => tenant.value?.domain || '',
  () => props.apiBase,
);

const siteContent = computed(() => tenant.value?.brand?.site_content || null);
const siteOverlay = computed(() => visitorContext.value?.site_content_localized || null);
const visualEditor = computed(() => siteContent.value?.visualEditor);
const hasVisualSite = computed(() => {
  const ve = visualEditor.value;
  if (!ve) return false;
  if (props.visualPage === 'home') return Boolean(String(ve.html || '').trim());
  return Boolean(String(ve.subPages?.[props.visualPage] || ve.html || '').trim());
});
const visualSiteHtml = computed(() => {
  const ve = visualEditor.value;
  if (!ve) return '';
  if (props.visualPage !== 'home' && ve.subPages?.[props.visualPage]) {
    return String(ve.subPages[props.visualPage]);
  }
  return String(ve.html || '');
});
const visualSiteCss = computed(() => String(visualEditor.value?.css || ''));
const tenantIdRef = computed(() => tenant.value?.id);
const apiBaseRef = computed(() => props.apiBase);

let unbindVisualInquiry = () => {};
let unbindVisualNav = () => {};

function rebindVisualInquiryForms() {
  unbindVisualInquiry();
  unbindVisualNav();
  if (!hasVisualSite.value || !import.meta.client) return;
  nextTick(() => {
    unbindVisualInquiry = bindVisualSiteInquiryForms(visualHtmlRef.value, {
      tenantId: tenantIdRef,
      apiBase: apiBaseRef,
      getAttribution: () => ({
        landing_path: typeof window !== 'undefined' ? window.location.pathname : '/tenant',
        last_click_label: 'visual_inquiry_form',
      }),
      messages: {
        requiredName: tSite('form_required_name'),
        requiredContact: tSite('form_required_contact'),
        requiredMessage: tSite('form_required_message'),
        success: tSite('form_success'),
        error: tSite('form_error'),
      },
    });
    unbindVisualNav = bindVisualSiteNavLinks(visualHtmlRef.value);
  });
}

watch([hasVisualSite, visualSiteHtml, () => tenant.value?.id, () => props.visualPage], () => {
  rebindVisualInquiryForms();
});

onUnmounted(() => {
  unbindVisualInquiry();
  unbindVisualNav();
});

const homePage = computed(() => (siteContent.value?.pages?.home || {}) as Record<string, unknown>);
const productsPage = computed(() => (siteContent.value?.pages?.products || {}) as Record<string, unknown>);
const aboutPage = computed(() => (siteContent.value?.pages?.about || {}) as Record<string, unknown>);
const contactPage = computed(() => (siteContent.value?.pages?.contact || {}) as Record<string, unknown>);

const themePrimary = computed(() =>
  siteContent.value?.theme?.headerBg || tenant.value?.brand.brand_colors.primary || '#1e293b',
);
const themeHeroBg = computed(() =>
  siteContent.value?.theme?.heroBg || '#f8fafc',
);
const siteThemeVars = computed(() => ({
  '--tenant-primary': themePrimary.value,
  '--tenant-hero-bg': themeHeroBg.value,
  '--tenant-on-primary': '#ffffff',
}));
const isRtl = computed(() => visitorLanguage.value === 'ar');
const documentDir = computed(() => (isRtl.value ? 'rtl' : 'ltr'));

function overlayList<T>(section: 'home' | 'about', key: string, fallback: T[]): T[] {
  const overlay = siteOverlay.value?.[section]?.[key];
  if (Array.isArray(overlay) && overlay.length) return overlay as T[];
  const page = section === 'home' ? homePage.value : aboutPage.value;
  const raw = page[key];
  if (Array.isArray(raw) && raw.length) return raw as T[];
  return fallback;
}

const companyName = computed(() =>
  siteOverlay.value?.brand?.name
  || siteContent.value?.brand?.name
  || tenant.value?.brand.company_name
  || tenant.value?.name
  || 'Company',
);
const brandTagline = computed(() =>
  siteOverlay.value?.brand?.tagline
  || siteContent.value?.brand?.tagline
  || tenant.value?.brand.slogan
  || '',
);
const heroTitle = computed(() =>
  String(
    siteOverlay.value?.home?.title
    || homePage.value.title
    || tenant.value?.brand.site_title
    || companyName.value,
  ),
);
const heroDescription = computed(() =>
  String(
    siteOverlay.value?.home?.description
    || homePage.value.description
    || tenant.value?.brand.about_summary
    || '',
  ),
);

const seoPageTitle = computed(() => {
  const base = String(homePage.value.title || companyName.value);
  if (props.visualPage === 'products') return `${productsTitle.value} | ${base}`;
  if (props.visualPage === 'about') return `${tSite('section_about', { name: companyName.value })} | ${base}`;
  if (props.visualPage === 'contact') return `${tSite('section_contact')} | ${base}`;
  return base;
});
const seoPageDescription = computed(() =>
  String(homePage.value.seoDescription || heroDescription.value || '').slice(0, 160),
);
const seoPageKeywords = computed(() => String(homePage.value.seoKeywords || ''));
const seoRobotsContent = computed(() =>
  homePage.value.robotsNoIndex === true ? 'noindex,nofollow' : 'index,follow',
);

useHead(() => ({
  title: seoPageTitle.value,
  meta: [
    { name: 'description', content: seoPageDescription.value },
    ...(seoPageKeywords.value ? [{ name: 'keywords', content: seoPageKeywords.value }] : []),
    { name: 'robots', content: seoRobotsContent.value },
  ],
}));

const heroImage = computed(() => String(homePage.value.heroImage || ''));
const establishedYear = computed(() => String(homePage.value.establishedYear || ''));
const sectionTitle = computed(() =>
  String(siteOverlay.value?.home?.sectionTitle || homePage.value.sectionTitle || tSite('why_choose_us')),
);
const applicationsTitle = computed(() =>
  String(
    siteOverlay.value?.home?.applicationsTitle
    || homePage.value.applicationsTitle
    || tSite('applications_title_default'),
  ),
);
const ctaPrimary = computed(() =>
  String(siteOverlay.value?.home?.ctaPrimary || homePage.value.ctaPrimary || tSite('cta_primary')),
);
const ctaSecondary = computed(() =>
  String(siteOverlay.value?.home?.ctaSecondary || homePage.value.ctaSecondary || tSite('cta_secondary')),
);
const inquiryHook = computed(() =>
  String(siteOverlay.value?.home?.inquiryHook || homePage.value.inquiryHook || ''),
);
const primaryPromise = computed(() =>
  String(siteOverlay.value?.home?.primary_promise || homePage.value.primary_promise || '').trim(),
);
const inquiryPrompt = computed(() => String(contactPage.value.inquiryPrompt || ''));
const aboutText = computed(() =>
  String(
    siteOverlay.value?.about?.aboutText
    || aboutPage.value.aboutText
    || tenant.value?.brand.about_summary
    || '',
  ),
);
const mission = computed(() => String(siteOverlay.value?.about?.mission || aboutPage.value.mission || ''));
const vision = computed(() => String(siteOverlay.value?.about?.vision || aboutPage.value.vision || ''));
const capacitySummary = computed(() =>
  String(siteOverlay.value?.about?.capacitySummary || aboutPage.value.capacitySummary || ''),
);
const productsTitle = computed(() =>
  String(siteOverlay.value?.products?.title || productsPage.value.title || tSite('section_products_default')),
);
const productsDescription = computed(() =>
  String(siteOverlay.value?.products?.description || productsPage.value.description || ''),
);
const productHint = computed(() => {
  const items = productsPage.value.productItems;
  if (Array.isArray(items) && items[0] && typeof items[0] === 'object' && items[0].name) {
    return String(items[0].name);
  }
  const cats = homePage.value.categories;
  if (Array.isArray(cats) && cats[0] && typeof cats[0] === 'object' && cats[0].name) {
    return String(cats[0].name);
  }
  return '';
});

const categories = computed<SiteCategory[]>(() => {
  const fromOverlay = overlayList<SiteCategory>('home', 'categories', []);
  if (fromOverlay.length) {
    return fromOverlay.filter((c): c is SiteCategory => typeof c === 'object' && c !== null && 'name' in c);
  }
  const legacy = tenant.value?.brand.product_categories || [];
  return legacy.map((name) => ({ name, description: `${companyName.value} ${name}` }));
});

const applications = computed<SiteApplication[]>(() =>
  overlayList<SiteApplication>('home', 'applications', []),
);

const solutions = computed<SiteSolution[]>(() => {
  const raw = overlayList<SiteSolution>('home', 'solutions', []);
  return raw.filter((s): s is SiteSolution => typeof s === 'object' && s !== null && 'title' in s);
});

const advantages = computed<SiteAdvantage[]>(() => {
  const fromOverlay = overlayList<SiteAdvantage>('home', 'advantages', []);
  if (fromOverlay.length) return fromOverlay;
  const feats = homePage.value.features;
  if (Array.isArray(feats)) {
    return feats.map((f) => ({ title: String(f), description: '' }));
  }
  return [];
});

const stats = computed<SiteStat[]>(() => {
  const raw = overlayList<SiteStat>('home', 'stats', []);
  return raw.filter((s): s is SiteStat => typeof s === 'object' && s !== null && 'value' in s);
});

const serviceStages = computed(() => {
  const raw = overlayList<{ stage?: string; title: string; description?: string }>('home', 'serviceStages', []);
  return raw.filter((s) => s && typeof s === 'object' && 'title' in s);
});

const knowledgeTopics = computed(() => {
  const raw = overlayList<{ title: string; hook?: string }>('home', 'knowledgeTopics', []);
  return raw.filter((k) => k && typeof k === 'object' && 'title' in k);
});

const trustBadges = computed<string[]>(() =>
  overlayList<string>('home', 'trustBadges', []).map(String).filter(Boolean),
);

const milestones = computed<SiteMilestone[]>(() => {
  const raw = overlayList<SiteMilestone>('about', 'milestones', []);
  return raw.filter((m): m is SiteMilestone => typeof m === 'object' && m !== null && 'year' in m);
});

const productItems = computed<ProductItem[]>(() => {
  const raw = productsPage.value.productItems;
  if (Array.isArray(raw) && raw.length) return raw as ProductItem[];
  const names = productsPage.value.products;
  if (Array.isArray(names)) {
    return names.map((n) => ({ name: String(n), summary: `${companyName.value} ${n}` }));
  }
  return (tenant.value?.brand.product_categories || []).map((n) => ({
    name: n,
    summary: `${companyName.value} ${n}`,
  }));
});

const contactPhone = computed(() =>
  String(contactPage.value.phone || tenant.value?.brand.contact_phone || ''),
);
const contactEmail = computed(() =>
  String(contactPage.value.email || tenant.value?.brand.contact_email || ''),
);
const contactWhatsapp = computed(() => String(contactPage.value.whatsapp || ''));
const contactWechat = computed(() => String(contactPage.value.wechat || ''));
const contactQq = computed(() => String(contactPage.value.qq || ''));
const factoryAddress = computed(() =>
  String(contactPage.value.factoryAddress || contactPage.value.address || ''),
);

const {
  effectiveChannels,
  topbarChannels,
  contactDisplayChannels,
  mobileQuickActions,
} = useTenantVisitorContacts({
  contactChannels: () => contactChannels.value,
  cnCompliantOnly: () => cnCompliantOnly.value,
  language: () => visitorLanguage.value,
  rawContacts: () => ({
    phone: contactPhone.value,
    email: contactEmail.value,
    whatsapp: contactWhatsapp.value,
    wechat: contactWechat.value,
    qq: contactQq.value,
  }),
  quoteLabel: () => ctaPrimary.value,
});

const footerText = computed(() => {
  const custom = siteContent.value?.footer?.text || tenant.value?.brand.footer_text;
  if (custom) return custom;
  return `Copyright © ${new Date().getFullYear()} ${companyName.value}. All Rights Reserved.`;
});

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [{ key: 'home', label: tSite('nav_home'), href: '#home' }];
  if (categories.value.length || productItems.value.length) {
    items.push({ key: 'products', label: tSite('nav_products'), href: '#products' });
  }
  if (solutions.value.length) items.push({ key: 'solutions', label: tSite('nav_solutions'), href: '#solutions' });
  if (applications.value.length) items.push({ key: 'applications', label: tSite('nav_applications'), href: '#applications' });
  if (aboutText.value || mission.value || vision.value) items.push({ key: 'about', label: tSite('nav_about'), href: '#about' });
  if (videos.value.length) items.push({ key: 'videos', label: tSite('nav_video'), href: '#videos' });
  if (forumEmbed.value?.enabled && forumEmbed.value?.iframe_src) {
    items.push({ key: 'forum', label: tSite('nav_qa'), href: '#forum' });
  }
  items.push({ key: 'contact', label: tSite('nav_contact'), href: '#contact' });
  return items;
});

const showMobileActionBar = computed(() => !mobileMenuOpen.value && !contactSectionVisible.value);

function onMobileActionClick(action: { href: string; key: string }) {
  if (action.key === 'quote' || action.href.startsWith('#')) {
    closeMobileMenu();
  }
}

function setupNavObserver() {
  if (!import.meta.client) return;
  navObserver?.disconnect();
  navObserver = null;

  const sectionIds = navItems.value
    .map((item) => item.href.replace(/^#/, ''))
    .filter(Boolean);

  if (!sectionIds.length) return;

  navObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (visible[0]?.target?.id) {
        activeNav.value = visible[0].target.id;
      }
      for (const entry of entries) {
        if (entry.target.id === 'contact') {
          contactSectionVisible.value = entry.isIntersecting;
        }
      }
    },
    { rootMargin: '-20% 0px -55% 0px', threshold: [0, 0.15, 0.35] },
  );

  for (const id of sectionIds) {
    const el = document.getElementById(id);
    if (el) navObserver.observe(el);
  }
  const contactEl = document.getElementById('contact');
  if (contactEl && !sectionIds.includes('contact')) {
    navObserver.observe(contactEl);
  }
}

function detectSubdomain(): string | null {
  if (props.subdomain) return props.subdomain;
  const fromRoute = resolveTenantDomainFromRoute();
  if (fromRoute) return fromRoute;
  return null;
}

async function loadTenant() {
  loading.value = true;
  error.value = null;
  const sub = detectSubdomain();
  if (!sub) {
    loading.value = false;
    error.value = tSite('tenant_not_found');
    return;
  }
  try {
    const localeTask = fetchVisitorContext(undefined, sub);
    const res = await fetch(`${props.apiBase}/tenants/domain/${encodeURIComponent(sub)}`);
    const body = await res.json();
    if (!res.ok || (body.code !== undefined && body.code !== 0)) {
      throw new Error(body.message || tSite('load_failed'));
    }
    tenant.value = (body.data || body) as TenantInfo;
    await Promise.all([loadVideos(sub), loadForum(sub), localeTask]);
    if (import.meta.client) {
      document.title = heroTitle.value || companyName.value;
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : tSite('load_failed');
  } finally {
    loading.value = false;
  }
}

async function loadForum(domain: string) {
  forumEmbed.value = null;
  try {
    const res = await fetch(`${props.apiBase}/public/tenants/${encodeURIComponent(domain)}/forum-embed`);
    if (!res.ok) return;
    const body = await res.json();
    const data = body.data || body;
    if (data.enabled && data.iframe_src) {
      forumEmbed.value = data;
    }
  } catch {
    /* optional */
  }
}

async function loadVideos(domain: string) {
  videos.value = [];
  try {
    const res = await fetch(`${props.apiBase}/public/tenants/${encodeURIComponent(domain)}/videos`);
    if (!res.ok) return;
    const body = await res.json();
    const data = body.data || body;
    videos.value = Array.isArray(data.videos) ? data.videos : [];
  } catch {
    /* optional */
  }
}

const heroPlaceholderHint = computed(() => {
  if (productHint.value) return productHint.value;
  const firstCat = categories.value[0]?.name;
  if (firstCat) return firstCat;
  return tSite('hero_placeholder_hint');
});
const heroPlaceholderStyle = computed(() => ({
  '--placeholder-accent': themePrimary.value,
  background: `linear-gradient(145deg, color-mix(in srgb, ${themePrimary.value} 16%, #f8fafc) 0%, color-mix(in srgb, ${themePrimary.value} 6%, #e2e8f0) 100%)`,
  borderColor: `color-mix(in srgb, ${themePrimary.value} 22%, #cbd5e1)`,
}));

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value;
}

function closeMobileMenu() {
  mobileMenuOpen.value = false;
}

function onMobileMenuKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && mobileMenuOpen.value) {
    closeMobileMenu();
  }
}

watch(
  () => tenant.value?.brand.custom_css,
  (css) => {
    if (!import.meta.client) return;
    const id = 'tenant-custom-css';
    let el = document.getElementById(id) as HTMLStyleElement | null;
    if (!css?.trim()) {
      el?.remove();
      return;
    }
    if (!el) {
      el = document.createElement('style');
      el.id = id;
      document.head.appendChild(el);
    }
    el.textContent = css;
  },
  { immediate: true },
);

watch(mobileMenuOpen, (open) => {
  if (!import.meta.client) return;
  document.body.style.overflow = open ? 'hidden' : '';
});

watch(
  () => [loading.value, navItems.value.length] as const,
  async ([isLoading]) => {
    if (isLoading || !import.meta.client) return;
    await nextTick();
    setupNavObserver();
  },
  { flush: 'post' },
);

onUnmounted(() => {
  if (import.meta.client) {
    document.body.style.overflow = '';
    window.removeEventListener('keydown', onMobileMenuKeydown);
    document.getElementById('tenant-custom-css')?.remove();
  }
  navObserver?.disconnect();
});

onMounted(() => {
  if (import.meta.client) {
    window.addEventListener('keydown', onMobileMenuKeydown);
  }
  loadTenant();
});
</script>

<style scoped>
.tenant-site-root {
  position: relative;
  -webkit-tap-highlight-color: transparent;
}

.tenant-visual-site {
  min-height: 100vh;
  background: #fff;
}

.tenant-visual-site__html :deep(a) {
  color: inherit;
}

.tenant-visual-site__html :deep(.sb-inquiry-msg) {
  margin: 8px 0 0;
  font-size: 13px;
}

.tenant-visual-site__html :deep(.sb-inquiry-msg--error) {
  color: #b91c1c;
}

.tenant-visual-site__html :deep(.sb-inquiry-msg--success) {
  color: #047857;
}
.tenant-site {
  scroll-behavior: smooth;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  color: #1e293b;
}
.tenant-container {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0 1rem;
  padding-left: max(1rem, env(safe-area-inset-left));
  padding-right: max(1rem, env(safe-area-inset-right));
}
.tenant-topbar {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.75rem;
}
.tenant-topbar-inner {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.4rem 1rem;
}
.tenant-topbar a:hover {
  color: #fff;
}
.tenant-nav-link {
  font-size: 0.875rem;
  color: #475569;
  font-weight: 500;
}
.tenant-nav-link.active,
.tenant-nav-link:hover {
  color: var(--tenant-primary);
}
.tenant-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.tenant-mobile-menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  color: var(--tenant-primary);
  cursor: pointer;
}
.tenant-mobile-menu-icon {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 18px;
}
.tenant-mobile-menu-icon span {
  display: block;
  height: 2px;
  width: 100%;
  background: currentColor;
  border-radius: 1px;
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.tenant-mobile-menu-icon.is-open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}
.tenant-mobile-menu-icon.is-open span:nth-child(2) {
  opacity: 0;
}
.tenant-mobile-menu-icon.is-open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}
.tenant-mobile-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgb(15 23 42 / 0.35);
  backdrop-filter: blur(2px);
}
.tenant-mobile-nav {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  z-index: 50;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 12px 32px rgb(15 23 42 / 0.12);
}
.tenant-mobile-nav-inner {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 1rem 1rem;
  gap: 0.15rem;
  max-height: min(70vh, 420px);
  overflow-y: auto;
}
.tenant-mobile-nav-link {
  display: block;
  padding: 0.75rem 0.85rem;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  color: #334155;
  text-decoration: none;
}
.tenant-mobile-nav-link.active,
.tenant-mobile-nav-link:hover {
  color: var(--tenant-primary);
  background: color-mix(in srgb, var(--tenant-primary) 8%, #f8fafc);
}
.tenant-mobile-nav-cta {
  display: block;
  margin-top: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.9375rem;
  color: #fff;
  background: var(--tenant-primary);
  text-decoration: none;
}
.tenant-mobile-nav-enter-active,
.tenant-mobile-nav-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.tenant-mobile-nav-enter-from,
.tenant-mobile-nav-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.tenant-header {
  position: relative;
}
.tenant-hero {
  padding: 3rem 0;
}
.tenant-hero-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  align-items: center;
}
@media (min-width: 768px) {
  .tenant-hero-grid {
    grid-template-columns: 1fr 1fr;
  }
}
.tenant-hero-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 800;
  line-height: 1.2;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.tenant-hero-eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--tenant-primary);
  margin-bottom: 0.5rem;
}
.tenant-trust-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}
.tenant-trust-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  border-radius: 9999px;
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #475569;
}
.tenant-stats {
  color: #fff;
  padding: 2.5rem 0;
}
.tenant-stats-eyebrow {
  text-align: center;
  font-size: 0.7rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.75;
  margin-bottom: 0.35rem;
}
.tenant-stats-title {
  text-align: center;
  font-size: 1.35rem;
  font-weight: 700;
  margin-bottom: 1.75rem;
}
.tenant-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1.5rem;
  text-align: center;
}
.tenant-stat-value {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 800;
  line-height: 1.1;
}
.tenant-stat-label {
  margin-top: 0.35rem;
  font-size: 0.8rem;
  opacity: 0.85;
  line-height: 1.4;
}
.tenant-hero-desc {
  margin-top: 1rem;
  color: #64748b;
  line-height: 1.7;
  font-size: 1rem;
  max-width: 36rem;
}
.tenant-inquiry-hook {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #475569;
  line-height: 1.6;
  padding: 0.75rem 1rem;
  background: #fff;
  border-left: 3px solid var(--tenant-primary);
  border-radius: 0 0.5rem 0.5rem 0;
  max-width: 32rem;
}
.tenant-inquiry-banner {
  text-align: center;
  max-width: 40rem;
  margin: 0 auto 1.5rem;
  padding: 0.85rem 1.25rem;
  background: #eff6ff;
  color: #1e40af;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}
.tenant-hero-img,
.tenant-hero-placeholder {
  width: 100%;
  aspect-ratio: 4/3;
  border-radius: 0.75rem;
  object-fit: cover;
}
.tenant-hero-placeholder {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid;
  min-height: 12rem;
}
.tenant-hero-placeholder-pattern {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  color: var(--placeholder-accent, var(--tenant-primary));
  opacity: 0.55;
  pointer-events: none;
}
.tenant-hero-placeholder-pattern svg {
  width: min(92%, 280px);
  height: auto;
  margin-bottom: -0.5rem;
}
.tenant-hero-placeholder-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 1.5rem;
  text-align: center;
  max-width: 90%;
}
.tenant-hero-placeholder-logo {
  max-height: 3rem;
  width: auto;
  object-fit: contain;
  margin-bottom: 0.25rem;
}
.tenant-hero-placeholder-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
}
.tenant-hero-placeholder-tagline,
.tenant-hero-placeholder-hint {
  font-size: 0.8125rem;
  color: #64748b;
  line-height: 1.45;
  max-width: 20rem;
}
.tenant-btn {
  display: inline-flex;
  padding: 0.65rem 1.25rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
}
.tenant-btn-primary {
  background: var(--tenant-primary);
  color: #fff;
}
.tenant-btn-outline {
  border: 1px solid var(--tenant-primary);
  color: var(--tenant-primary);
}
.tenant-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
.tenant-mobile-action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9990;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.35rem;
  padding: 0.45rem 0.65rem calc(0.45rem + env(safe-area-inset-bottom));
  padding-left: max(0.65rem, env(safe-area-inset-left));
  padding-right: max(0.65rem, env(safe-area-inset-right));
  background: rgb(255 255 255 / 0.94);
  backdrop-filter: blur(10px);
  border-top: 1px solid #e2e8f0;
  box-shadow: 0 -6px 28px rgb(15 23 42 / 0.1);
}
.tenant-mobile-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
  min-height: 3.25rem;
  padding: 0.35rem 0.25rem;
  border-radius: 0.625rem;
  font-size: 0.6875rem;
  font-weight: 600;
  line-height: 1.2;
  color: #334155;
  text-decoration: none;
  text-align: center;
}
.tenant-mobile-action-btn.is-primary {
  background: var(--tenant-primary);
  color: #fff;
}
.tenant-mobile-action-icon {
  font-size: 1rem;
  line-height: 1;
}
.tenant-mobile-action-label {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tenant-section {
  padding: 3.5rem 0;
}
.tenant-section-title {
  text-align: center;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--tenant-primary);
  margin-bottom: 0.5rem;
}
.tenant-section-desc {
  text-align: center;
  color: #64748b;
  max-width: 40rem;
  margin: 0 auto 2rem;
  font-size: 0.95rem;
}
.tenant-forum-iframe {
  width: 100%;
  min-height: 520px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
}
.tenant-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;
}
.tenant-card-grid--3 {
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}
.tenant-solution-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;
}
.tenant-solution-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.35rem 1.25rem;
  border-top: 3px solid var(--tenant-primary);
}
.tenant-solution-segment {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--tenant-primary);
  margin-bottom: 0.35rem;
}
.tenant-solution-card h3 {
  font-weight: 700;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: #0f172a;
}
.tenant-solution-card p {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
}
.tenant-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.25rem;
  transition: box-shadow 0.2s;
}
.tenant-card:hover {
  box-shadow: 0 8px 24px rgb(15 23 42 / 0.08);
}
.tenant-card h3 {
  font-weight: 700;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: #0f172a;
}
.tenant-card p {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
}
.tenant-product-thumb {
  height: 120px;
  background: #f8fafc;
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.tenant-product-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 0.5rem;
}
.tenant-link {
  color: var(--tenant-primary);
  font-size: 0.875rem;
  font-weight: 600;
}
.tenant-adv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}
.tenant-hero-eyebrow--promise {
  color: var(--tenant-primary);
  font-weight: 700;
  max-width: 42rem;
}
.tenant-stage-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}
.tenant-stage-card {
  text-align: center;
  padding: 1rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.875rem;
  background: #fff;
}
.tenant-stage-num {
  width: 2.25rem;
  height: 2.25rem;
  margin: 0 auto 0.65rem;
  border-radius: 9999px;
  background: var(--tenant-primary);
  color: #fff;
  font-weight: 800;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tenant-stage-card h3 {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 700;
}
.tenant-stage-card p {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.45;
}
.tenant-adv-card {
  text-align: center;
  padding: 1.5rem 1rem;
  background: #fff;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
}
.tenant-adv-icon {
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto 0.75rem;
  border-radius: 9999px;
  background: var(--tenant-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.tenant-about {
  max-width: 52rem;
  margin: 0 auto;
  text-align: center;
}
.tenant-about-text {
  color: #475569;
  line-height: 1.8;
  font-size: 1.05rem;
  margin-bottom: 2rem;
}
.tenant-mv-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
  margin: 2rem 0;
  text-align: left;
}
@media (min-width: 768px) {
  .tenant-mv-grid {
    grid-template-columns: 1fr 1fr;
  }
}
.tenant-mv-card {
  padding: 1.5rem;
  background: #f8fafc;
  border-left: 4px solid var(--tenant-primary);
  border-radius: 0 0.5rem 0.5rem 0;
}
.tenant-mv-heading {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--tenant-primary);
  margin-bottom: 0.75rem;
}
.tenant-mv-text {
  color: #475569;
  line-height: 1.75;
  font-size: 0.95rem;
}
.tenant-capacity {
  max-width: 48rem;
  margin: 0 auto 2rem;
  padding: 1.25rem 1.5rem;
  background: #f1f5f9;
  border-radius: 0.5rem;
  color: #475569;
  line-height: 1.7;
  font-size: 0.95rem;
  text-align: center;
}
.tenant-timeline {
  max-width: 48rem;
  margin: 0 auto;
  text-align: left;
}
.tenant-timeline-heading {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 1.25rem;
  text-align: center;
}
.tenant-timeline-track {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-left: 2px solid #e2e8f0;
  margin-left: 1rem;
  padding-left: 1.5rem;
}
.tenant-timeline-item {
  position: relative;
  padding-bottom: 1.5rem;
}
.tenant-timeline-item::before {
  content: '';
  position: absolute;
  left: -1.65rem;
  top: 0.35rem;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 9999px;
  background: var(--tenant-primary);
}
.tenant-timeline-year {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--tenant-primary);
  margin-bottom: 0.25rem;
}
.tenant-timeline-body h4 {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.25rem;
}
.tenant-timeline-body p {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
}
.tenant-contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  max-width: 56rem;
  margin: 0 auto;
}
.tenant-contact-item {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.5rem;
  font-size: 0.9rem;
}
.tenant-contact-item strong {
  display: block;
  color: #64748b;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}
.tenant-contact-item--link {
  display: block;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.tenant-contact-item--link:active {
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--tenant-primary) 25%, #e2e8f0);
}
.tenant-footer {
  color: #fff;
  padding: 2.5rem 0 1.5rem;
  margin-top: auto;
}
.tenant-footer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 2rem;
}
.tenant-site-root--rtl .tenant-topbar-inner,
.tenant-site-root--rtl .tenant-header nav .flex {
  flex-direction: row-reverse;
}
.tenant-site-root--rtl .tenant-hero-grid {
  direction: rtl;
}
.tenant-site-root--rtl .tenant-stats-grid,
.tenant-site-root--rtl .tenant-trust-badges {
  direction: rtl;
}
.tenant-site-root--rtl .tenant-inquiry-hook {
  border-left: none;
  border-right: 3px solid var(--tenant-primary);
  border-radius: 0.5rem 0 0 0.5rem;
}
.tenant-site-root--rtl .tenant-mobile-nav-link.active,
.tenant-site-root--rtl .tenant-mobile-nav-link:hover {
  text-align: right;
}

@media (max-width: 767px) {
  .tenant-site-root {
    --tenant-mobile-bar-height: 4.35rem;
  }
  .tenant-site {
    padding-bottom: calc(var(--tenant-mobile-bar-height) + 4.5rem + env(safe-area-inset-bottom));
  }
  .tenant-topbar-inner {
    flex-wrap: nowrap;
    overflow-x: auto;
    overscroll-behavior-x: contain;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    gap: 0.85rem;
    padding-top: 0.55rem;
    padding-bottom: 0.55rem;
  }
  .tenant-topbar-inner::-webkit-scrollbar {
    display: none;
  }
  .tenant-topbar a {
    flex-shrink: 0;
    white-space: nowrap;
    min-height: 2.25rem;
    display: inline-flex;
    align-items: center;
    font-size: 0.8125rem;
  }
  .tenant-header nav > .flex {
    min-height: 3.5rem;
    height: auto;
    padding: 0.35rem 0;
  }
  .tenant-header nav > .flex .font-bold {
    font-size: 0.9375rem;
  }
  .tenant-mobile-nav {
    position: fixed;
    left: 0;
    right: 0;
    top: auto;
    bottom: 0;
    max-height: min(78vh, 520px);
    border-radius: 1rem 1rem 0 0;
    border-bottom: none;
  }
  .tenant-mobile-nav-inner {
    max-height: min(72vh, 480px);
    padding-bottom: calc(1rem + env(safe-area-inset-bottom));
  }
  .tenant-mobile-backdrop {
    z-index: 45;
  }
  .tenant-mobile-nav {
    z-index: 46;
  }
  .tenant-header {
    z-index: 50;
  }
  .tenant-hero {
    padding: 1.75rem 0 2rem;
  }
  .tenant-hero-grid {
    gap: 1.25rem;
  }
  .tenant-hero-media {
    order: -1;
  }
  .tenant-hero-title {
    font-size: clamp(1.5rem, 6.5vw, 2rem);
  }
  .tenant-hero-desc {
    font-size: 0.9375rem;
    line-height: 1.65;
  }
  .tenant-hero-actions {
    flex-direction: column;
    margin-top: 1.25rem;
  }
  .tenant-hero-actions .tenant-btn {
    width: 100%;
    justify-content: center;
    min-height: 2.75rem;
    font-size: 0.9375rem;
  }
  .tenant-trust-badge {
    font-size: 0.6875rem;
  }
  .tenant-stats {
    padding: 2rem 0;
  }
  .tenant-stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
  .tenant-stat-value {
    font-size: 1.625rem;
  }
  .tenant-section {
    padding: 2.5rem 0;
  }
  .tenant-section-title {
    font-size: 1.375rem;
    padding: 0 0.25rem;
  }
  .tenant-section-desc {
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }
  .tenant-card-grid,
  .tenant-card-grid--3,
  .tenant-solution-grid,
  .tenant-adv-grid,
  .tenant-contact-grid,
  .tenant-footer-grid {
    grid-template-columns: 1fr;
    gap: 0.85rem;
  }
  .tenant-solution-card,
  .tenant-card,
  .tenant-adv-card {
    padding: 1.1rem;
  }
  .tenant-product-thumb {
    height: 140px;
  }
  .tenant-about-text {
    font-size: 0.9375rem;
    text-align: left;
  }
  .tenant-mv-grid {
    margin: 1.5rem 0;
  }
  .tenant-timeline-track {
    margin-left: 0.5rem;
    padding-left: 1.25rem;
  }
  .tenant-footer {
    padding: 2rem 0 1.25rem;
  }
  .tenant-footer-grid {
    gap: 1.5rem;
  }
  .tenant-inquiry-hook,
  .tenant-inquiry-banner {
    max-width: none;
    font-size: 0.8125rem;
  }
  .tenant-contact-item {
    min-height: 3.25rem;
  }
  .tenant-mobile-nav-link {
    min-height: 2.75rem;
    display: flex;
    align-items: center;
  }
  .tenant-mobile-nav-cta {
    min-height: 2.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

@media (min-width: 768px) {
  .tenant-site {
    padding-bottom: 0;
  }
}
</style>
