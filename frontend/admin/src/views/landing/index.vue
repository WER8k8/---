/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="landing-page" surface="brand-hero">
    <header class="landing-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-mark">优</span>
          <span class="logo-text">优丁 YOU DING</span>
        </div>
        <nav class="nav-links">
          <a href="#features">能力</a>
          <a href="#scenarios">场景</a>
          <a href="#hierarchy">渠道</a>
          <a href="#pricing">套餐</a>
          <a href="#contact">联系</a>
        </nav>
        <div class="header-actions">
          <a-button size="large" @click="goTenantLogin()">卖家登录</a-button>
          <a-button size="large" @click="goAgentLogin()">成为代理</a-button>
          <a-button type="primary" size="large" @click="router.push('/tenants/register')">
            免费试用
          </a-button>
        </div>
      </div>
    </header>

    <section class="hero-section">
      <div class="hero-content">
        <p class="hero-eyebrow">{{ copy.hero.eyebrow }}</p>
        <h1 class="hero-title">{{ copy.hero.h1 }}</h1>
        <p class="hero-subtitle">{{ copy.hero.sub }}</p>
        <div class="hero-actions">
          <a-button type="primary" size="large" @click="router.push('/tenants/register')">
            {{ copy.hero.ctaPrimary }}
            <template #icon><ArrowRightOutlined /></template>
          </a-button>
          <a-button size="large" @click="goTenantLogin()">
            {{ copy.hero.ctaSecondary }}
            <template #icon><LoginOutlined /></template>
          </a-button>
          <a-button size="large" ghost class="hero-actions__ghost" @click="goPartnerLogin()">
            {{ copy.hero.ctaPartner }}
          </a-button>
        </div>
        <p class="hero-trial-note">{{ copy.hero.trialNote }}</p>
        <p class="hero-demo-note">下方工作台预览为产品示意图，非真实客户数据</p>
        <div class="hero-stats">
          <div v-for="item in mock.items" :key="item.label" class="stat-item">
            <span class="stat-number">{{ item.value }}</span>
            <span class="stat-label">{{ item.label }}</span>
          </div>
        </div>
      </div>
      <div class="hero-image">
        <div class="workbench-preview">
          <div class="workbench-preview__head">
            <span>{{ mock.greeting }}</span>
            <span>{{ mock.plan }}</span>
          </div>
          <ul class="workbench-preview__list">
            <li><span class="dot dot--urgent" />美国 · 轻集料 LC15 — 样品与报价</li>
            <li><span class="dot dot--urgent" />阿联酋 · 保温砂浆 — data sheet</li>
            <li><span class="dot" />发布中：Alibaba 批次 2/5 SKU</li>
          </ul>
        </div>
      </div>
    </section>

    <section id="features" class="features-section">
      <div class="section-header">
        <h2>{{ copy.sections.capabilitiesTitle }}</h2>
        <p>{{ copy.sections.capabilitiesSub }}</p>
      </div>
      <div class="features-grid features-grid--four">
        <div
          v-for="cap in copy.capabilities"
          :key="cap.id"
          class="feature-card"
          :class="{ 'feature-card--featured': cap.featured }"
        >
          <span class="feature-metric">{{ cap.metric }}</span>
          <h3>{{ cap.title }}</h3>
          <p>{{ cap.desc }}</p>
        </div>
      </div>
    </section>

    <section id="scenarios" class="scenarios-section">
      <div class="section-header">
        <h2>建材厂常见出海场景</h2>
        <p>轻集料、岩棉、橡塑、砂浆 — 同一套工作台</p>
      </div>
      <div class="scenarios-grid">
        <article v-for="scene in copy.scenarios" :key="scene.title" class="scenario-card">
          <h3>{{ scene.title }}</h3>
          <p>{{ scene.desc }}</p>
        </article>
      </div>
    </section>

    <section id="hierarchy" class="hierarchy-section">
      <div class="section-header">
        <h2>四级渠道，各看各的盘</h2>
        <p>超管 → 省代 → 市代 → 建材卖家，数据一体、权限分层</p>
      </div>
      <div class="hierarchy-visual">
        <div class="hierarchy-card" v-for="level in hierarchyLevels" :key="level.code">
          <div class="hierarchy-icon" :style="{ backgroundColor: level.color }">
            <component :is="level.icon" />
          </div>
          <h3>{{ level.name }}</h3>
          <p>{{ level.description }}</p>
          <ul class="hierarchy-features">
            <li v-for="feat in level.features" :key="feat">{{ feat }}</li>
          </ul>
        </div>
      </div>
    </section>

    <section id="pricing" class="pricing-section">
      <div class="section-header">
        <h2>四档套餐，按需升级</h2>
        <p>体验版 · 启航版 · 专业版 · 企业版 — 命名与定价页完全一致</p>
      </div>
      <div class="pricing-grid pricing-grid--four">
        <div
          v-for="plan in pricingPlans"
          :key="plan.id"
          class="pricing-card"
          :class="{ 'pricing-card--recommended': plan.recommended }"
        >
          <div class="pricing-header">
            <span v-if="plan.recommended" class="pricing-badge">推荐</span>
            <h3>{{ plan.name }}</h3>
            <p class="pricing-tagline">{{ plan.tagline }}</p>
          </div>
          <ul class="pricing-features">
            <li v-for="feature in plan.features" :key="feature">
              <CheckCircleOutlined />
              {{ feature }}
            </li>
          </ul>
          <a-button
            :type="plan.recommended ? 'primary' : 'default'"
            block
            size="large"
            @click="router.push('/tenants/register')"
          >
            {{ plan.recommended ? '立即开通' : '免费试用' }}
          </a-button>
        </div>
      </div>
      <p class="pricing-more">
        <a @click.prevent="router.push('/tenants/pricing')">查看完整定价矩阵 →</a>
      </p>
    </section>

    <section id="contact" class="contact-section">
      <div class="contact-content">
        <div class="contact-info">
          <h2>联系我们</h2>
          <p>有任何问题或需求，欢迎随时联系我们的团队</p>
          <div class="contact-details">
            <div class="contact-item">
              <EnvironmentOutlined />
              <span>北京市朝阳区科技园区</span>
            </div>
            <div class="contact-item">
              <PhoneOutlined />
              <span>400-888-8888</span>
            </div>
            <div class="contact-item">
              <MailOutlined />
              <span>contact@exportplatform.com</span>
            </div>
          </div>
        </div>
        <div class="contact-form">
          <a-form layout="vertical" @finish="submitContact">
            <a-form-item label="姓名" name="name" :rules="[{ required: true, message: '请填写姓名' }]">
              <a-input v-model:value="contactForm.name" placeholder="请输入您的姓名" />
            </a-form-item>
            <a-form-item label="手机号" name="phone" :rules="phoneRules">
              <a-input v-model:value="contactForm.phone" placeholder="11 位中国大陆手机号" :maxlength="11" />
            </a-form-item>
            <a-form-item label="邮箱">
              <a-input v-model:value="contactForm.email" placeholder="请输入您的邮箱" />
            </a-form-item>
            <a-form-item label="公司名称">
              <a-input v-model:value="contactForm.company" placeholder="请输入公司名称" />
            </a-form-item>
            <a-form-item label="需求描述" name="message" :rules="[{ required: true, message: '请描述您的需求' }]">
              <a-textarea v-model:value="contactForm.message" placeholder="请描述您的需求" :rows="4" />
            </a-form-item>
            <a-button type="primary" block size="large" html-type="submit" :loading="contactSubmitting">
              提交咨询
            </a-button>
          </a-form>
        </div>
      </div>
    </section>

    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-logo">
          <span class="logo-mark logo-mark--sm">优</span>
          <span>优丁 YOU DING</span>
        </div>
        <div class="footer-links">
          <div class="footer-column">
            <h4>产品</h4>
            <a href="#features">能力</a>
            <a href="#pricing">套餐</a>
            <a href="/tenants/register">免费试用</a>
            <a :href="publicPlatformUrl" target="_blank" rel="noopener">公网营销页</a>
          </div>
          <div class="footer-column">
            <h4>登录</h4>
            <a href="#" @click.prevent="goTenantLogin()">卖家登录</a>
            <a href="#" @click.prevent="goAgentLogin()">代理登录</a>
            <a href="#" @click.prevent="goPartnerLogin()">省代登录</a>
          </div>
          <div class="footer-column">
            <h4>支持</h4>
            <a href="#">帮助中心</a>
            <a href="#contact">联系我们</a>
          </div>
          <div class="footer-column">
            <h4>公司</h4>
            <a href="#">关于优丁</a>
            <a href="#">加入我们</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 优丁 · 建材外贸 AI 卖货操作系统</p>
      </div>
    </footer>
  </YdPage>
</template>

<script setup lang="ts">
/**
 * SaaS 营销官网 · Admin 完整版（site id: saas-marketing）
 * MKT-PLATFORM-02 · 文案与 /platform 同源 @marketing
 */
import { ref, reactive, computed } from 'vue';
import { YdPage } from '@/components/youding';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { loginPortalPath } from '@/constants/loginPortalCopy';
import {
  PLATFORM_COPY,
  LANDING_HERO_PREVIEW,
  PLAN_FEATURE_BULLETS,
} from '@marketing';
import {
  ArrowRightOutlined,
  LoginOutlined,
  CrownOutlined,
  CheckCircleOutlined,
  EnvironmentOutlined,
  PhoneOutlined,
  MailOutlined,
  GlobalOutlined,
  SettingOutlined,
  RocketOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue';

const copy = PLATFORM_COPY;
const mock = LANDING_HERO_PREVIEW;
const router = useRouter();

const publicPlatformUrl = computed(
  () => import.meta.env.VITE_PUBLIC_PLATFORM_URL || 'http://127.0.0.1:3000/platform',
);

function goLoginWithRedirect(redirect: string) {
  router.push({ path: loginPortalPath(), query: { redirect } });
}

function goTenantLogin() {
  goLoginWithRedirect('/client/today');
}

function goAgentLogin() {
  goLoginWithRedirect('/agent/performance');
}

function goPartnerLogin() {
  goLoginWithRedirect('/partner/performance');
}

const contactForm = reactive({
  name: '',
  phone: '',
  email: '',
  company: '',
  message: '',
});
const contactSubmitting = ref(false);

const phoneRules = [
  { required: true, message: '请填写手机号' },
  {
    pattern: /^1[3-9]\d{9}$/,
    message: '请填写有效的 11 位中国大陆手机号',
  },
];

async function submitContact() {
  contactSubmitting.value = true;
  try {
    const res = await fetch('/api/v1/inquiries/public', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: contactForm.name.trim(),
        phone: contactForm.phone.trim(),
        email: contactForm.email.trim() || undefined,
        product: contactForm.company.trim() || undefined,
        message: contactForm.message.trim(),
        source_channel: 'platform_landing',
        landing_path: window.location.pathname,
      }),
    });
    const body = await res.json();
    if (!res.ok || body.code !== 0) {
      throw new Error(body.message || '提交失败，请稍后重试');
    }
    message.success('咨询已提交，我们会尽快联系您');
    contactForm.name = '';
    contactForm.phone = '';
    contactForm.email = '';
    contactForm.company = '';
    contactForm.message = '';
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '提交失败，请稍后重试';
    message.error(msg);
  } finally {
    contactSubmitting.value = false;
  }
}

const FALLBACK_HIERARCHY_FEATURES: Record<string, string[]> = {
  platform: ['租户治理', '系统配置', '数据看板'],
  partner: ['省区经营', '客户开户', '渠道报表'],
  agent: ['辖区客户', '业绩统计', '渠道赋能'],
  tenant: ['询盘 inbox', '多平台发品', '独立站运营'],
};

const hierarchyLevels = copy.hierarchy.map((level) => {
  const iconMap = {
    platform: CrownOutlined,
    partner: GlobalOutlined,
    agent: TeamOutlined,
    tenant: RocketOutlined,
  } as const;
  const colorMap = {
    platform: '#1e3a5f',
    partner: '#4a9b8c',
    agent: '#0284c7',
    tenant: '#059669',
  } as const;
  const code = level.code as keyof typeof iconMap;
  return {
    code: level.code,
    name: level.name,
    description: level.desc,
    icon: iconMap[code] ?? SettingOutlined,
    color: colorMap[code] ?? '#4a9b8c',
    features: FALLBACK_HIERARCHY_FEATURES[level.code] ?? [],
  };
});

const pricingPlans = copy.plans.map((plan) => ({
  id: plan.id,
  name: plan.name,
  tagline: plan.tagline,
  recommended: plan.featured,
  features: PLAN_FEATURE_BULLETS[plan.id] ?? [],
}));
</script>

<style scoped lang="scss">
.landing-page {
  max-width: none;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: #fff;
}

.landing-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e5e7eb;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8bb8f5, #6a9ee8);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-mark--sm {
  width: 28px;
  height: 28px;
  font-size: 12px;
}

.logo-icon {
  font-size: 24px;
  color: #7c3aed;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.nav-links {
  display: flex;
  gap: 32px;
}

.nav-links a {
  color: #475569;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: #7c3aed;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.hero-section {
  padding-top: 120px;
  padding-bottom: 80px;
  background: linear-gradient(135deg, #f5f3ff 0%, #e0f2fe 50%, #ecfdf5 100%);
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
}

.hero-eyebrow {
  font-size: 13px;
  font-weight: 600;
  color: var(--uj-brand, #4a9b8c);
  margin: 0 0 12px 0;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
  margin: 0 0 24px 0;
}

.hero-subtitle {
  font-size: 18px;
  color: #475569;
  line-height: 1.8;
  margin: 0 0 32px 0;
}

.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.hero-trial-note {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 8px 0;
}
.hero-demo-note {
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 24px 0;
}
.hero-actions__ghost {
  border-color: rgb(139 184 245 / 0.6) !important;
  color: #5b8fd4 !important;
}

.hero-stats {
  display: flex;
  gap: 48px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 28px;
  font-weight: 800;
  color: #1e3a5f;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}

.hero-image {
  display: flex;
  justify-content: center;
}

.workbench-preview {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 48px rgba(30, 58, 95, 0.12);
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.workbench-preview__head {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #1e3a5f;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.workbench-preview__list {
  list-style: none;
  margin: 0;
  padding: 16px;
}

.workbench-preview__list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #475569;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.workbench-preview__list li:last-child {
  border-bottom: none;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}

.dot--urgent {
  background: #dc2626;
}

.features-section,
.scenarios-section,
.hierarchy-section,
.pricing-section {
  padding: 80px 0;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-header h2 {
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.section-header p {
  font-size: 18px;
  color: #64748b;
  margin: 0;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.feature-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 28px 22px;
  text-align: left;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feature-card--featured {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 0 0 1px var(--uj-brand, #4a9b8c);
}

.feature-card:hover {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.1);
}

.feature-metric {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--uj-brand, #4a9b8c);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin-bottom: 8px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.feature-card p {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}

.scenarios-section {
  background: #fff;
}

.scenarios-grid {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.scenario-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}

.scenario-card h3 {
  font-size: 16px;
  font-weight: 700;
  color: #1e3a5f;
  margin: 0 0 8px 0;
}

.scenario-card p {
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
  margin: 0;
}

.hierarchy-section {
  background: #f8fafc;
}

.hierarchy-visual {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.hierarchy-card {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
}

.hierarchy-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 36px;
  color: #fff;
}

.hierarchy-card h3 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.hierarchy-card > p {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 20px 0;
}

.hierarchy-features {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}

.hierarchy-features li {
  padding: 8px 0;
  font-size: 14px;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
}

.hierarchy-features li:last-child {
  border-bottom: none;
}

.pricing-grid {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.pricing-card {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 32px;
}

.pricing-grid--four {
  grid-template-columns: repeat(4, 1fr);
}

.pricing-card--recommended {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 8px 32px rgba(37, 99, 235, 0.12);
}

.pricing-badge {
  display: inline-block;
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.pricing-tagline {
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
  margin: 0;
}

.pricing-more {
  text-align: center;
  margin-top: 24px;
  font-size: 15px;
}

.pricing-more a {
  color: var(--uj-brand, #4a9b8c);
  font-weight: 600;
  cursor: pointer;
}

.pricing-card:has(button.ant-btn-primary) {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 10px 40px rgba(37, 99, 235, 0.12);
}

.pricing-header {
  text-align: center;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 24px;
}

.pricing-header h3 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.pricing-amount {
  margin-bottom: 8px;
}

.currency {
  font-size: 20px;
  font-weight: 600;
  color: #64748b;
  vertical-align: top;
}

.price {
  font-size: 48px;
  font-weight: 800;
  color: #0f172a;
}

.period {
  font-size: 14px;
  color: #64748b;
}

.pricing-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 32px 0;
}

.pricing-features li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
  color: #475569;
}

.pricing-features li :deep(.anticon) {
  color: #22c55e;
}

.contact-section {
  padding: 80px 0;
  background: #f8fafc;
}

.contact-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
}

.contact-info h2 {
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.contact-info > p {
  font-size: 18px;
  color: #64748b;
  margin: 0 0 32px 0;
}

.contact-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 16px;
  color: #475569;
}

.contact-item :deep(.anticon) {
  font-size: 20px;
  color: #7c3aed;
}

.contact-form {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
}

.landing-footer {
  background: #0f172a;
  padding: 48px 0 24px;
  color: #fff;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  margin-bottom: 48px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-logo .logo-icon {
  font-size: 24px;
  color: #7c3aed;
}

.footer-logo span {
  font-size: 18px;
  font-weight: 700;
}

.footer-links {
  display: flex;
  gap: 80px;
}

.footer-column h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.footer-column a {
  display: block;
  font-size: 14px;
  color: #94a3b8;
  text-decoration: none;
  padding: 6px 0;
  transition: color 0.2s;
}

.footer-column a:hover {
  color: #fff;
}

.footer-bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 24px 0;
  border-top: 1px solid #1e293b;
}

.footer-bottom p {
  text-align: center;
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

@media (max-width: 1024px) {
  .hero-content {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .hero-stats {
    justify-content: center;
  }
  .hero-actions {
    justify-content: center;
  }
  .features-grid,
  .hierarchy-visual {
    grid-template-columns: repeat(2, 1fr);
  }
  .pricing-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
  }
  .contact-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  .nav-links {
    display: none;
  }
  .features-grid,
  .features-grid--four,
  .scenarios-grid,
  .hierarchy-visual,
  .pricing-grid,
  .pricing-grid--four {
    grid-template-columns: 1fr;
  }
  .footer-content {
    flex-direction: column;
    gap: 32px;
  }
  .footer-links {
    gap: 32px;
  }
}
</style>
