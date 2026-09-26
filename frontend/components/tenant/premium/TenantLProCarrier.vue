/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <PremiumB2bShell
    active-key="about"
    :document-title="meta.title"
    :document-description="meta.description"
  >
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ meta.h1 }}</h1>
        <p>{{ meta.intro }}</p>
      </div>
    </section>

    <section class="lpro-section lpro-section--white">
      <div class="lpro-container max-w-3xl">
        <!-- 租户后台已录入的内容优先展示；否则诚实占位 -->
        <article
          v-if="pageBody"
          class="lpro-card mb-6"
          v-html="pageBody"
        />
        <div
          v-else
          class="lpro-card lpro-card--muted mb-6"
        >
          <p>{{ tSite('carrier_pending', { section: meta.h1 }) }}</p>
        </div>

        <!-- 资质与认证：列出常见认证类型作为行业上下文（以租户实际持有为准，不作伪称） -->
        <template v-if="page === 'certifications'">
          <h2 class="lpro-section-title">
            {{ tSite('carrier_cert_types') }}
          </h2>
          <ul class="lpro-grid lpro-grid--tags">
            <li
              v-for="c in certTypes"
              :key="c"
              class="lpro-tag"
            >
              {{ c }}
            </li>
          </ul>
        </template>

        <!-- 产品技术参数：给出选型常看的关键参数说明（行业通识，非租户假数据） -->
        <template v-if="page === 'parameters'">
          <h2 class="lpro-section-title">
            {{ tSite('carrier_param_help') }}
          </h2>
          <div class="lpro-grid">
            <article
              v-for="p in paramHints"
              :key="p.label"
              class="lpro-card"
            >
              <h3 class="font-semibold mb-2">
                {{ p.label }}
              </h3>
              <p>{{ p.hint }}</p>
            </article>
          </div>
        </template>

        <!-- 常见问题：诚实种子 FAQ（真实通用问题），并注入 FAQPage 结构化数据 -->
        <template v-if="page === 'faq'">
          <h2 class="lpro-section-title">
            {{ tSite('carrier_faq_title') }}
          </h2>
          <div class="lpro-faq">
            <details
              v-for="(item, i) in faqItems"
              :key="i"
              class="lpro-faq-item"
            >
              <summary>{{ item.q }}</summary>
              <p>{{ item.a }}</p>
            </details>
          </div>
        </template>

        <!-- 转化收口：导向联系 / 询盘 -->
        <div class="lpro-cta-block">
          <NuxtLink
            to="/tenant/contact"
            class="lpro-header-cta"
          >
            {{ tSite('carrier_cta') }}
          </NuxtLink>
        </div>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { localizedSiteString } from '../../../utils/tenant-site-i18n';

type CarrierPageKind =
  | 'test-reports'
  | 'parameters'
  | 'certifications'
  | 'supplier-onboarding'
  | 'brand-guide'
  | 'faq';

const props = defineProps<{ page: CarrierPageKind }>();

const {
  tenant,
  siteContent,
  pages,
  tSite,
  context: visitorContext,
  language,
} = useTenantSiteBootstrap();

const overlay = computed(() => visitorContext.value?.site_content_localized || null);

const companyName = computed(
  () =>
    localizedSiteString(
      siteContent.value,
      overlay.value?.brand,
      'brand',
      'name',
      language.value,
      [tenant.value?.brand.company_name, tenant.value?.name].filter(
        (x): x is string => typeof x === 'string',
      ),
    ) || 'Company',
);

interface MetaCopy {
  title: string;
  description: string;
  h1: string;
  intro: string;
}

const META: Record<CarrierPageKind, { zh: MetaCopy; en: MetaCopy }> = {
  'test-reports': {
    zh: {
      title: '产品检测报告',
      description:
        '优丁租户第三方产品检测报告与质量证明文件索引。报告由租户在后台录入后展示，涵盖耐火、导热、抗拉、环保等关键指标，支持按产品检索。',
      h1: '产品检测报告',
      intro:
        '本页汇总可公开的产品检测与质量证明文件。检测报告由租户在后台录入后展示；如暂未列出，请直接联系我们获取对应产品的第三方检测报告原件。',
    },
    en: {
      title: 'Product Test Reports',
      description:
        'Index of third-party test reports and quality certificates from this Youding tenant. Reports are published once entered by the tenant, covering fire resistance, thermal conductivity, tensile strength and more.',
      h1: 'Product Test Reports',
      intro:
        'This page aggregates publicly available product test and quality documents. Reports appear here after the tenant enters them. If not listed yet, contact us for the original third-party test report of a specific product.',
    },
  },
  parameters: {
    zh: {
      title: '产品技术参数',
      description:
        '优丁租户建材产品技术参数表，含尺寸、密度、导热系数、耐火等级、抗拉强度、使用温度等关键指标，支持按产品查询。',
      h1: '产品技术参数',
      intro:
        '本页提供产品标准技术参数。租户录入后展示完整参数表；下列为选型时常看的关键参数说明，供您对照需求。',
    },
    en: {
      title: 'Product Specifications',
      description:
        'Technical specification sheets for building-material products from this Youding tenant, including dimensions, density, thermal conductivity, fire rating, tensile strength and service temperature.',
      h1: 'Product Specifications',
      intro:
        'Standard technical parameters for the products. The full table appears after the tenant enters it. Below are the key parameters buyers usually check when specifying materials.',
    },
  },
  certifications: {
    zh: {
      title: '资质与认证',
      description:
        '优丁租户持有的企业资质与产品认证索引。认证以租户实际持有为准，常见类型包括 CE、ISO 9001、ASTM、RoHS 等。',
      h1: '资质与认证',
      intro:
        '本页展示租户实际持有的资质与产品认证。下方列出建材行业常见的认证类型作为参考；具体以租户录入内容为准。',
    },
    en: {
      title: 'Certifications',
      description:
        'Index of corporate qualifications and product certifications held by this Youding tenant. Certifications shown reflect what the tenant actually holds, such as CE, ISO 9001, ASTM, RoHS and more.',
      h1: 'Certifications',
      intro:
        'This page shows the qualifications and product certifications the tenant actually holds. Common certification types in the building-materials industry are listed below for reference; the exact list depends on what the tenant enters.',
    },
  },
  'supplier-onboarding': {
    zh: {
      title: '供应商合作与入驻',
      description:
        '成为优丁租户供应链合作伙伴的资质要求、合作模式与入驻流程说明。欢迎具备稳定产能与质量体系的工厂洽谈。',
      h1: '供应商合作与入驻',
      intro:
        '本页说明与租户建立供应链合作的资质要求与入驻流程。如未列出详细条款，请通过下方联系入口获取最新的合作政策。',
    },
    en: {
      title: 'Supplier Partnership & Onboarding',
      description:
        'Qualification requirements, cooperation models and onboarding steps to become a supply-chain partner of this Youding tenant. Factories with stable capacity and a quality system are welcome to talk.',
      h1: 'Supplier Partnership & Onboarding',
      intro:
        'This page explains the qualification requirements and onboarding flow for supply-chain cooperation. If detailed terms are not listed, use the contact link below for the latest partnership policy.',
    },
  },
  'brand-guide': {
    zh: {
      title: '品牌资料',
      description:
        '优丁租户品牌视觉规范与对外传播资料下载，含 Logo、标准色、宣传册等，供授权渠道与媒体使用。',
      h1: '品牌资料',
      intro:
        '本页提供品牌视觉与对外传播规范资料。资料由租户在后台录入后展示；如暂未提供，请通过联系入口获取授权素材。',
    },
    en: {
      title: 'Brand Assets',
      description:
        'Brand visual guidelines and PR assets from this Youding tenant, including logo, brand colors and brochures, for authorized channels and media.',
      h1: 'Brand Assets',
      intro:
        'Brand visual and communication guidelines are provided here. Assets appear after the tenant uploads them. If not available yet, contact us for authorized materials.',
    },
  },
  faq: {
    zh: {
      title: '常见问题',
      description:
        '关于产品、检测报告、认证、技术参数、物流与合作的常见问题解答，帮助采购方快速评估与合作。',
      h1: '常见问题',
      intro:
        '下列为采购与协作过程中的常见通用问题。如需针对具体产品的答案，请通过联系入口提交询盘。',
    },
    en: {
      title: 'FAQ',
      description:
        'Frequently asked questions about products, test reports, certifications, specifications, logistics and cooperation to help buyers evaluate and collaborate.',
      h1: 'FAQ',
      intro:
        'Common general questions from procurement and cooperation are listed below. For product-specific answers, submit an inquiry via the contact link.',
    },
  },
};

const meta = computed<MetaCopy>(() => {
  const entry = META[props.page];
  return (language.value === 'zh' ? entry.zh : entry.en);
});

const pageBody = computed(() => {
  const raw = pages.value?.[props.page] as Record<string, unknown> | undefined;
  const body = raw?.body;
  return typeof body === 'string' && body.trim().length > 0 ? body : '';
});

const certTypes = ['CE', 'ISO 9001', 'ASTM', 'RoHS', 'REACH', 'EN 13501', 'UL'];

const paramHints = [
  { label: '导热系数', hint: '衡量保温隔热性能，数值越低保温越好，单位 W/(m·K)。' },
  { label: '耐火等级', hint: '按标准（如 EN 13501 / GB 8624）划分 A、B 等级，决定适用场景。' },
  { label: '密度', hint: '影响强度与重量，单位 kg/m³，需与力学性能平衡。' },
  { label: '抗拉/抗弯强度', hint: '结构承载关键指标，单位 MPa，依工况选型。' },
  { label: '使用温度', hint: '材料可长期稳定工作的温度区间，单位 ℃。' },
  { label: '尺寸与公差', hint: '长度、宽度、厚度及允许偏差，影响安装与拼缝。' },
];

const faqItems = [
  {
    q: '如何获取某款产品的第三方检测报告？',
    a: '请在对应产品页提交询盘或直接联系我们，我们将提供该产品的第三方检测报告原件扫描件。',
  },
  {
    q: '产品是否持有 CE / ISO 9001 / ASTM 等认证？',
    a: '本页「资质与认证」展示租户实际持有的认证。如列表为空，请直接联系我们确认具体产品的认证状态。',
  },
  {
    q: '最小起订量（MOQ）与交货周期如何？',
    a: 'MOQ 与交期因产品规格与定制要求而异，请通过询盘获取针对您订单的报价与排产计划。',
  },
  {
    q: '是否支持 OEM 与定制规格？',
    a: '支持按图纸与参数定制；可在「产品技术参数」页查询标准参数作为基准，并在询盘中附技术要求。',
  },
  {
    q: '包装与物流方式？',
    a: '支持海运 / 陆运，采用标准出口包装；订单确认后由专人跟进物流方案。',
  },
];

// FAQ 页额外注入 FAQPage 结构化数据，提升富摘要捕获
if (props.page === 'faq') {
  useHead(() => ({
    script: [
      {
        type: 'application/ld+json',
        key: 'carrier-faq-schema',
        innerHTML: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: faqItems.map((item) => ({
            '@type': 'Question',
            name: item.q,
            acceptedAnswer: { '@type': 'Answer', text: item.a },
          })),
        }),
      },
    ],
  }));
}
</script>
