/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="saas-landing">
    <header class="saas-header">
      <div class="saas-container saas-header-inner">
        <NuxtLink
          to="/platform"
          class="saas-logo"
        >
          <span class="saas-logo-mark">优</span>
          <span class="saas-logo-text">优丁 YOU DING</span>
        </NuxtLink>
        <nav
          class="saas-nav hidden lg:flex"
          aria-label="营销页导航"
        >
          <a
            v-for="link in navLinks"
            :key="link.href"
            :href="link.href"
          >{{ link.label }}</a>
        </nav>
        <div class="saas-header-actions">
          <button
            type="button"
            class="saas-menu-btn lg:hidden"
            :aria-expanded="mobileNavOpen"
            aria-label="打开菜单"
            @click="mobileNavOpen = !mobileNavOpen"
          >
            ☰
          </button>
          <a
            :href="admin.login('tenant')"
            class="saas-btn saas-btn-outline saas-btn-sm hidden sm:inline-flex"
          >卖家登录</a>
          <a
            :href="admin.register"
            class="saas-btn saas-btn-primary saas-btn-sm"
          >{{ copy.hero.ctaPrimary }}</a>
        </div>
      </div>
      <nav
        v-show="mobileNavOpen"
        class="saas-mobile-nav lg:hidden"
        aria-label="移动端导航"
      >
        <a
          v-for="link in navLinks"
          :key="link.href"
          :href="link.href"
          @click="mobileNavOpen = false"
        >{{ link.label }}</a>
        <a
          :href="admin.login('tenant')"
          @click="mobileNavOpen = false"
        >卖家登录</a>
      </nav>
    </header>

    <section class="saas-hero">
      <div class="saas-container saas-hero-grid">
        <div>
          <p class="saas-eyebrow">
            {{ copy.hero.eyebrow }}
          </p>
          <h1 class="saas-hero-title">
            {{ copy.hero.h1 }}
          </h1>
          <p class="saas-hero-sub">
            {{ copy.hero.sub }}
          </p>
          <ul class="saas-bullets">
            <li
              v-for="item in copy.pillars"
              :key="item.title"
            >
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </li>
          </ul>
          <div class="saas-hero-actions">
            <a
              :href="admin.register"
              class="saas-btn saas-btn-primary"
            >{{ copy.hero.ctaPrimary }}</a>
            <a
              :href="admin.login('tenant')"
              class="saas-btn saas-btn-outline"
            >{{ copy.hero.ctaSecondary }}</a>
            <a
              :href="admin.login('partner')"
              class="saas-btn saas-btn-ghost"
            >{{ copy.hero.ctaPartner }}</a>
          </div>
          <p class="saas-trial-note">
            {{ copy.hero.trialNote }}
          </p>
          <div class="saas-trust-strip">
            <span
              v-for="badge in copy.trust"
              :key="badge"
              class="saas-trust-badge"
            >{{ badge }}</span>
          </div>
        </div>

        <div
          class="saas-workbench-mock"
          aria-label="工作台预览示意"
        >
          <div class="saas-mock-header">
            <span>{{ mock.greeting }}</span>
            <span class="saas-mock-plan">{{ mock.plan }}</span>
          </div>
          <div class="saas-mock-stats">
            <div
              v-for="item in mock.items"
              :key="item.label"
              class="saas-mock-stat"
              :class="`saas-mock-stat--${item.tone}`"
            >
              <span class="saas-mock-stat-value">{{ item.value }}</span>
              <span class="saas-mock-stat-label">{{ item.label }}</span>
            </div>
          </div>
          <div class="saas-mock-list">
            <div class="saas-mock-row">
              <span class="saas-mock-dot saas-mock-dot--urgent" />
              <span>美国 · 轻集料 LC15 — 样品与报价</span>
            </div>
            <div class="saas-mock-row">
              <span class="saas-mock-dot saas-mock-dot--urgent" />
              <span>阿联酋 · 保温砂浆 — data sheet 请求</span>
            </div>
            <div class="saas-mock-row">
              <span class="saas-mock-dot" />
              <span>发布中：Alibaba 批次 2/5 SKU</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section
      class="saas-trust-proof"
      aria-label="客户信任"
    >
      <div class="saas-container">
        <div class="saas-trust-stats">
          <div
            v-for="stat in trustProof.stats"
            :key="stat.label"
            class="saas-trust-stat"
          >
            <span class="saas-trust-stat-value">{{ stat.value }}</span>
            <span class="saas-trust-stat-label">{{ stat.label }}</span>
          </div>
        </div>
        <div
          class="saas-trust-logos"
          aria-label="建材行业客户"
        >
          <span
            v-for="logo in trustProof.logos"
            :key="logo"
            class="saas-trust-logo"
          >{{ logo }}</span>
        </div>
        <blockquote class="saas-trust-quote">
          「{{ trustProof.quote.text }}」
          <cite>— {{ trustProof.quote.author }}</cite>
        </blockquote>
      </div>
    </section>

    <section
      id="capabilities"
      class="saas-section saas-section-muted"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          {{ copy.sections.capabilitiesTitle }}
        </h2>
        <p class="saas-section-sub">
          {{ copy.sections.capabilitiesSub }}
        </p>
        <div class="saas-cap-grid">
          <article
            v-for="cap in copy.capabilities"
            :key="cap.id"
            class="saas-cap-card"
            :class="{ 'is-featured': cap.featured }"
          >
            <span class="saas-cap-metric">{{ cap.metric }}</span>
            <h3>{{ cap.title }}</h3>
            <p>{{ cap.desc }}</p>
            <a
              :href="capLink(cap)"
              class="saas-cap-cta"
            >{{ cap.cta }}</a>
          </article>
        </div>
      </div>
    </section>

    <section
      id="value"
      class="saas-section"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          为什么建材厂选优丁
        </h2>
        <p class="saas-section-sub">
          结构参考现代 SaaS，语境只为建材外贸
        </p>
        <div
          class="saas-tabs"
          role="tablist"
        >
          <button
            v-for="tab in copy.valueTabs"
            :key="tab.id"
            type="button"
            role="tab"
            class="saas-tab"
            :class="{ 'is-active': activeValueTab === tab.id }"
            :aria-selected="activeValueTab === tab.id"
            @click="activeValueTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>
        <div
          v-for="tab in copy.valueTabs"
          v-show="activeValueTab === tab.id"
          :key="tab.id"
          class="saas-value-panel"
        >
          <div class="saas-value-panel-grid">
            <div>
              <h3>{{ tab.title }}</h3>
              <p>{{ tab.desc }}</p>
              <ul class="saas-value-bullets">
                <li
                  v-for="b in tab.bullets"
                  :key="b"
                >
                  {{ b }}
                </li>
              </ul>
            </div>
            <div
              class="saas-value-visual"
              aria-hidden="true"
            >
              <div class="saas-value-visual-metric">
                <span>{{ tab.label }} · 工作台预览</span>
                <span>{{ valueVisualPct(tab.id) }}%</span>
              </div>
              <div class="saas-value-visual-bar">
                <span :style="{ width: `${valueVisualPct(tab.id)}%` }" />
              </div>
              <p class="text-sm text-slate-500 m-0">
                {{ valueVisualHint(tab.id) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section
      id="integrations"
      class="saas-section saas-section-muted"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          {{ integrations.title }}
        </h2>
        <p class="saas-section-sub">
          {{ integrations.sub }}
        </p>
        <div class="saas-integration-grid">
          <article
            v-for="item in integrations.items"
            :key="item.name"
            class="saas-integration-card"
          >
            <span class="saas-integration-name">{{ item.name }}</span>
            <span class="saas-integration-tag">{{ item.tag }}</span>
          </article>
        </div>
      </div>
    </section>

    <section
      id="scenarios"
      class="saas-section"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          {{ copy.sections.scenariosTitle }}
        </h2>
        <p class="saas-section-sub">
          {{ copy.sections.scenariosSub }}
        </p>
        <div class="saas-scenario-grid">
          <article
            v-for="scene in copy.scenarios"
            :key="scene.title"
            class="saas-scenario-card"
          >
            <h3>{{ scene.title }}</h3>
            <p>{{ scene.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <section
      id="plans"
      class="saas-section"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          {{ copy.sections.plansTitle }}
        </h2>
        <p class="saas-section-sub">
          {{ copy.sections.plansSub }}
        </p>
        <div
          class="saas-billing-toggle"
          role="group"
          aria-label="计费周期"
        >
          <button
            type="button"
            :class="{ 'is-active': billingCycle === 'monthly' }"
            @click="billingCycle = 'monthly'"
          >
            月付
          </button>
          <button
            type="button"
            :class="{ 'is-active': billingCycle === 'yearly' }"
            @click="billingCycle = 'yearly'"
          >
            年付更省
          </button>
        </div>
        <div class="saas-plan-grid">
          <article
            v-for="plan in copy.plans"
            :key="plan.id"
            class="saas-plan-card"
            :class="{ 'is-featured': plan.featured, 'is-selected': selectedPlan === plan.id }"
            role="button"
            tabindex="0"
            @click="selectPlan(plan.id)"
            @keydown.enter.prevent="selectPlan(plan.id)"
          >
            <span
              v-if="plan.featured"
              class="saas-plan-badge"
            >推荐</span>
            <h3>{{ plan.name }}</h3>
            <p class="saas-plan-price">
              <span class="saas-plan-price-value">{{ planPrice(plan.id) }}</span>
              <span class="saas-plan-price-unit">{{ planPriceUnit(plan.id) }}</span>
            </p>
            <p class="saas-plan-tagline">
              {{ plan.tagline }}
            </p>
            <ul class="saas-plan-bullets">
              <li
                v-for="item in planBullets(plan.id)"
                :key="item"
              >
                {{ item }}
              </li>
            </ul>
            <a
              :href="planRegisterUrl(plan.id)"
              class="saas-btn"
              :class="plan.featured ? 'saas-btn-primary' : 'saas-btn-outline'"
              target="_blank"
              rel="noopener noreferrer"
              @click.stop
            >
              {{ plan.featured ? '立即开通' : '免费试用' }}
            </a>
          </article>
        </div>
        <p class="saas-plan-note">
          完整功能矩阵见下方对比表 ·
          <a
            :href="admin.pricing"
            target="_blank"
            rel="noopener noreferrer"
          >Admin 定价页</a>
          · 年付可享额外折扣（以定价页为准）
        </p>
        <div
          id="plan-matrix"
          class="saas-matrix-wrap"
        >
          <table class="saas-matrix">
            <thead>
              <tr>
                <th scope="col">
                  能力
                </th>
                <th
                  v-for="col in pricingMatrix.columns"
                  :key="col.id"
                  scope="col"
                  :class="{ 'is-selected-col': selectedPlan === col.id }"
                >
                  <button
                    type="button"
                    class="saas-matrix-plan-head"
                    @click="selectPlan(col.id)"
                  >
                    {{ col.label }}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <template
                v-for="row in pricingMatrix.rows"
                :key="row.featureKey || row.feature"
              >
                <tr
                  v-if="row.group"
                  class="saas-matrix-group"
                >
                  <td :colspan="pricingMatrix.columns.length + 1">
                    {{ row.group }}
                  </td>
                </tr>
                <tr>
                  <td>{{ row.feature }}</td>
                  <td
                    v-for="col in pricingMatrix.columns"
                    :key="col.id"
                    :class="[
                      matrixCellClass(row[col.id as PlanColumnKey]),
                      { 'is-selected-col': selectedPlan === col.id },
                    ]"
                  >
                    {{ matrixCellLabel(row[col.id as PlanColumnKey]) }}
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section
      id="hierarchy"
      class="saas-section saas-section-dark"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          四级渠道，各看各的盘
        </h2>
        <p class="saas-section-sub">
          超管 → 省代 → 市代 → 建材卖家，数据一体、权限分层
        </p>
        <div class="saas-hierarchy-grid">
          <article
            v-for="level in copy.hierarchy"
            :key="level.code"
            class="saas-hierarchy-card"
          >
            <h3>{{ level.name }}</h3>
            <p>{{ level.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <section
      id="portals"
      class="saas-section saas-section-muted"
    >
      <div class="saas-container">
        <h2 class="saas-section-title">
          登录入口
        </h2>
        <p class="saas-section-sub">
          卖家、代理、省代、平台 — 四套门户，同一产品
        </p>
        <div class="saas-portal-grid">
          <a
            v-for="portal in copy.portals"
            :key="portal.id"
            :href="admin.login(portal.id)"
            class="saas-portal-card"
          >
            <span class="saas-portal-name">{{ portal.name }}</span>
            <span class="saas-portal-desc">{{ portal.desc }}</span>
          </a>
        </div>
      </div>
    </section>

    <section class="saas-final-cta">
      <div class="saas-container">
        <h2>{{ copy.finalCta.title }}</h2>
        <p>{{ copy.finalCta.sub }}</p>
        <div class="saas-final-actions">
          <a
            :href="admin.register"
            class="saas-btn saas-btn-primary"
          >{{ copy.finalCta.primary }}</a>
          <a
            :href="demoContactUrl"
            class="saas-btn saas-btn-outline"
          >{{ copy.finalCta.secondary }}</a>
        </div>
      </div>
    </section>

    <footer class="saas-footer">
      <div class="saas-container saas-footer-inner">
        <span>© {{ year }} 优丁 · {{ copy.footerTagline }}</span>
        <div class="saas-footer-links">
          <NuxtLink to="/">
            建材企业官网
          </NuxtLink>
          <a :href="admin.login('agent')">代理登录</a>
          <a :href="admin.login('tenant')">卖家登录</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
/**
 * SaaS 营销官网 — site id: saas-marketing
 * 架构门禁：.project/architect-platform-gate-20260604.json
 * 文案源：frontend/config/platform-marketing-content.ts ← plan-copy-deck.md
 */
import { ref, computed } from 'vue';
import {
  PLATFORM_COPY,
  LANDING_HERO_PREVIEW,
  NAV_LINKS,
  TRUST_PROOF,
  INTEGRATIONS,
  PRICING_MATRIX,
  PLAN_FEATURE_BULLETS,
  matrixCellLabel,
  matrixCellClass,
} from '~/config/platform-marketing-content';
import {
  PLAN_REGISTER_CODE,
  formatPlanPrice,
  planPriceSuffix,
  type PlanId,
} from '~/config/plan-catalog';

definePageMeta({ layout: 'marketing' });

type PlanColumnKey = PlanId;

const copy = PLATFORM_COPY;
const mock = LANDING_HERO_PREVIEW;
const navLinks = NAV_LINKS;
const trustProof = TRUST_PROOF;
const integrations = INTEGRATIONS;
const pricingMatrix = PRICING_MATRIX;
const admin = useAdminAppUrl();
const year = new Date().getFullYear();
const activeValueTab = ref(copy.valueTabs[0].id);
const mobileNavOpen = ref(false);
const billingCycle = ref<'monthly' | 'yearly'>('monthly');
const selectedPlan = ref<PlanId>('pro');

const demoContactUrl = computed(() => `${admin.landingMirror.value}#contact`);

function planRegisterUrl(planId: PlanId) {
  const code = PLAN_REGISTER_CODE[planId];
  return `${admin.base.value}/tenants/register?plan=${encodeURIComponent(code)}`;
}

function planPrice(planId: PlanId) {
  return formatPlanPrice(planId, billingCycle.value);
}

function planPriceUnit(planId: PlanId) {
  return planPriceSuffix(planId, billingCycle.value);
}

function planBullets(planId: PlanId) {
  return PLAN_FEATURE_BULLETS[planId] || [];
}

function selectPlan(planId: PlanId) {
  selectedPlan.value = planId;
  if (import.meta.client) {
    document.getElementById('plan-matrix')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function capLink(cap: (typeof copy.capabilities)[number]) {
  if (cap.id === 'pro') return `${admin.pricing.value}#pro`;
  if (cap.id === 'site') return `${admin.register.value}`;
  return '#plans';
}

function valueVisualPct(tabId: string) {
  if (tabId === 'time') return 72;
  if (tabId === 'scale') return 88;
  return 65;
}

function valueVisualHint(tabId: string) {
  if (tabId === 'time') return '今日待办 + 询盘未读 + 发布进度';
  if (tabId === 'scale') return '省代 / 市代 / 卖家各看各的盘';
  return '企业版：白标 + 审计 + 用量告警';
}

useHead({
  title: '外贸卖家出海工作台',
  meta: [
    {
      name: 'description',
      content:
        '优丁 — 建材外贸出海工作台。询盘、发品、独立站一体，7 天完成绑域、发首条、收首询盘。',
    },
    { name: 'robots', content: 'index,follow' },
  ],
});
</script>

<style scoped>
.saas-landing {
  width: 100%;
  max-width: none;
}

.saas-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--saas-border);
}

.saas-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 0;
}

.saas-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--saas-text);
  font-weight: 700;
  flex-shrink: 0;
}

.saas-logo-mark {
  width: 2rem;
  height: 2rem;
  border-radius: 8px;
  background: var(--saas-primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 0.875rem;
}

.saas-nav {
  gap: 1.25rem;
}

.saas-nav a {
  color: var(--saas-text-secondary);
  text-decoration: none;
  font-size: 0.9375rem;
}

.saas-nav a:hover {
  color: var(--saas-primary);
}

.saas-header-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.saas-hero {
  position: relative;
  padding: clamp(2.5rem, 5vw, 4rem) 0;
  background: linear-gradient(180deg, #eff6ff 0%, rgb(239 246 255 / 0.35) 45%, transparent 100%);
  overflow: hidden;
}

.saas-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 42% 70% at 0% 45%, rgb(37 99 235 / 0.07), transparent 68%),
    radial-gradient(ellipse 38% 65% at 100% 35%, rgb(37 99 235 / 0.09), transparent 65%);
  pointer-events: none;
}

.saas-hero-grid {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 2.5rem;
  align-items: center;
}

@media (min-width: 960px) {
  .saas-hero-grid {
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.95fr);
    gap: clamp(2rem, 4vw, 3.5rem);
  }
}

@media (min-width: 1280px) {
  .saas-hero-grid {
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  }
}

.saas-eyebrow {
  font-size: 0.8125rem;
  color: var(--saas-primary);
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.saas-hero-title {
  font-size: clamp(1.75rem, 4vw, 2.375rem);
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1rem;
}

.saas-hero-sub {
  font-size: 1.0625rem;
  color: var(--saas-text-secondary);
  margin-bottom: 1.25rem;
  line-height: 1.65;
}

.saas-bullets {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.saas-bullets li {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding-left: 1rem;
  border-left: 3px solid var(--saas-primary);
}

.saas-bullets strong {
  font-size: 0.9375rem;
}

.saas-bullets span {
  color: var(--saas-text-secondary);
  font-size: 0.875rem;
}

.saas-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.saas-trial-note {
  font-size: 0.8125rem;
  color: var(--saas-text-secondary);
  margin-bottom: 0.5rem;
}

.saas-workbench-mock {
  border: 1px solid var(--saas-border);
  border-radius: var(--saas-radius);
  background: #fff;
  box-shadow: 0 24px 48px rgba(30, 58, 95, 0.1);
  overflow: hidden;
}

.saas-mock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: var(--saas-navy);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
}

.saas-mock-plan {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.85;
}

.saas-mock-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--saas-border);
  border-bottom: 1px solid var(--saas-border);
}

.saas-mock-stat {
  background: #fff;
  padding: 0.875rem 0.5rem;
  text-align: center;
}

.saas-mock-stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 800;
  color: var(--saas-navy);
}

.saas-mock-stat--urgent .saas-mock-stat-value {
  color: #dc2626;
}

.saas-mock-stat--ok .saas-mock-stat-value {
  color: #059669;
}

.saas-mock-stat-label {
  font-size: 0.6875rem;
  color: var(--saas-text-secondary);
}

.saas-mock-list {
  padding: 0.75rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.saas-mock-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: var(--saas-text-secondary);
}

.saas-mock-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}

.saas-mock-dot--urgent {
  background: #dc2626;
}

.saas-plan-grid {
  display: grid;
  gap: 1rem;
}

@media (min-width: 768px) {
  .saas-plan-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.saas-plan-card {
  position: relative;
  border: 1px solid var(--saas-border);
  border-radius: var(--saas-radius);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.saas-plan-card:hover,
.saas-plan-card.is-selected {
  border-color: rgb(37 99 235 / 0.45);
  box-shadow: 0 4px 20px rgb(37 99 235 / 0.08);
}

.saas-plan-card.is-selected {
  box-shadow: 0 0 0 2px rgb(37 99 235 / 0.2);
}

.saas-plan-card.is-featured {
  border-color: var(--saas-primary);
  box-shadow: 0 0 0 1px var(--saas-primary);
}

.saas-plan-badge {
  position: absolute;
  top: -0.625rem;
  right: 1rem;
  background: var(--saas-primary);
  color: #fff;
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.saas-plan-tagline {
  flex: 1;
  font-size: 0.875rem;
  color: var(--saas-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.saas-plan-price {
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.saas-plan-price-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--saas-navy);
}

.saas-plan-price-unit {
  font-size: 0.8125rem;
  color: var(--saas-text-secondary);
}

.saas-plan-bullets {
  margin: 0;
  padding-left: 1.125rem;
  font-size: 0.8125rem;
  color: var(--saas-text-secondary);
  line-height: 1.55;
}

.saas-plan-bullets li {
  margin-bottom: 0.25rem;
}

.saas-plan-note {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: var(--saas-text-secondary);
}

.saas-plan-note a {
  color: var(--saas-primary);
  font-weight: 600;
}

.saas-portal-grid {
  display: grid;
  gap: 1rem;
}

@media (min-width: 640px) {
  .saas-portal-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .saas-portal-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.saas-portal-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 1.25rem;
  border: 1px solid var(--saas-border);
  border-radius: var(--saas-radius);
  background: #fff;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.saas-portal-card:hover {
  border-color: var(--saas-primary);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
}

.saas-portal-name {
  font-weight: 700;
  color: var(--saas-primary);
}

.saas-portal-desc {
  font-size: 0.875rem;
  color: var(--saas-text-secondary);
}

.saas-footer {
  border-top: 1px solid var(--saas-border);
  padding: 1.5rem 0;
  font-size: 0.875rem;
  color: var(--saas-text-secondary);
}

.saas-footer-inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.saas-footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.saas-footer-links a {
  color: var(--saas-text-secondary);
  text-decoration: none;
}

.saas-footer-links a:hover {
  color: var(--saas-primary);
}
</style>
