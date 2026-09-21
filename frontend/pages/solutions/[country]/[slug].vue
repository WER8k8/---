/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="country-solution-page min-h-screen bg-[#fafaf9] text-text-primary">
    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex flex-col items-center justify-center min-h-[60vh]"
    >
      <div class="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
      <p class="text-text-secondary text-sm">
        正在加载全球出海本地化解决方案...
      </p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error || !bundle"
      class="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center"
    >
      <div class="w-16 h-16 rounded-full bg-red-50 text-red-500 flex items-center justify-center text-2xl font-bold mb-4">
        !
      </div>
      <h2 class="text-xl font-bold text-text-primary mb-2">
        方案暂未就绪
      </h2>
      <p class="text-text-secondary text-sm max-w-md mb-6">
        {{ error || '未找到该国家或产品的工程适配方案' }}
      </p>
      <NuxtLink
        to="/products"
        class="px-6 py-2.5 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-primary-hover transition-colors shadow-sm"
      >
        返回全线产品目录
      </NuxtLink>
    </div>

    <!-- Active State -->
    <div
      v-else
      class="pb-24"
    >
      <!-- Top Country Banner -->
      <div class="bg-white border-b border-border/40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between text-xs sm:text-sm">
          <div class="flex items-center gap-2">
            <span class="text-2xl">{{ bundle.country_profile.flag_emoji }}</span>
            <span class="font-bold text-text-primary">{{ bundle.country_profile.country_name_en }}</span>
            <span class="text-text-secondary">({{ bundle.country_profile.country_name_zh }})</span>
            <span class="hidden md:inline-block px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
              {{ bundle.country_profile.region_name }}
            </span>
          </div>

          <div class="flex items-center gap-3 text-text-secondary">
            <span>直航海运: <strong class="text-primary">{{ bundle.country_profile.transit_days }}</strong></span>
            <span class="hidden sm:inline">|</span>
            <span class="hidden sm:inline">结算币种: <strong class="text-text-primary">{{ bundle.country_profile.currency }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Breadcrumbs -->
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-text-secondary">
        <ol class="flex items-center gap-2 flex-wrap">
          <li>
            <NuxtLink
              to="/"
              class="hover:text-primary transition-colors"
            >
              首页
            </NuxtLink>
          </li>
          <li>/</li>
          <li>
            <NuxtLink
              to="/products"
              class="hover:text-primary transition-colors"
            >
              产品中心
            </NuxtLink>
          </li>
          <li>/</li>
          <li><span>全球工程出海</span></li>
          <li>/</li>
          <li class="text-text-primary font-medium">
            {{ bundle.country_profile.country_name_en }}
          </li>
          <li>/</li>
          <li class="text-primary font-semibold truncate max-w-xs">
            {{ bundle.product.name_en || bundle.product.name }}
          </li>
        </ol>
      </nav>

      <!-- Hero Section -->
      <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-10">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div class="lg:col-span-7">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold tracking-wide uppercase mb-4">
              <span>{{ bundle.country_profile.flag_emoji }} 本地化采购专供方案</span>
            </div>
            <h1 class="text-2xl sm:text-4xl font-extrabold text-text-primary leading-tight mb-4">
              {{ bundle.country_profile.country_name_en }} Certified <br class="hidden sm:inline">
              <span class="text-primary">{{ bundle.product.name_en || bundle.product.name }}</span>
            </h1>
            <p class="text-sm sm:text-base text-text-secondary leading-relaxed mb-6">
              针对 <strong class="text-text-primary">{{ bundle.country_profile.target_climate }}</strong> 专向研发，直供 <strong class="text-text-primary">{{ bundle.country_profile.destination_ports.join(' / ') }}</strong>。执行国际与当地标准准入认证，提供全套海关清关与原产地凭证。
            </p>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <template v-if="bundle.product.key_specs && bundle.product.key_specs.length">
                <div
                  v-for="(spec, sIdx) in bundle.product.key_specs"
                  :key="sIdx"
                  class="bg-white p-3.5 rounded-xl border border-border/50 shadow-sm"
                >
                  <span class="block text-xs text-text-secondary mb-1">{{ spec.label }}</span>
                  <span class="text-sm sm:text-base font-bold text-text-primary truncate block">{{ spec.value }}</span>
                </div>
              </template>
              <template v-else>
                <div class="bg-white p-3.5 rounded-xl border border-border/50 shadow-sm">
                  <span class="block text-xs text-text-secondary mb-1">主要规格 / Spec</span>
                  <span class="text-sm sm:text-base font-bold text-text-primary">{{ bundle.product.density || '工业标准' }}</span>
                </div>
                <div class="bg-white p-3.5 rounded-xl border border-border/50 shadow-sm">
                  <span class="block text-xs text-text-secondary mb-1">性能强度 / Rating</span>
                  <span class="text-sm sm:text-base font-bold text-text-primary">{{ bundle.product.strength || '高精受控' }}</span>
                </div>
                <div class="bg-white p-3.5 rounded-xl border border-border/50 shadow-sm">
                  <span class="block text-xs text-text-secondary mb-1">综合指标 / Efficiency</span>
                  <span class="text-sm sm:text-base font-bold text-text-primary">{{ bundle.product.thermal_conductivity || '优化能效' }}</span>
                </div>
                <div class="bg-white p-3.5 rounded-xl border border-border/50 shadow-sm">
                  <span class="block text-xs text-text-secondary mb-1">合规等级 / Grade</span>
                  <span class="text-sm sm:text-base font-bold text-primary">{{ bundle.product.fire_rating || '国际认证' }}</span>
                </div>
              </template>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <button
                @click="scrollToInquiry"
                class="px-6 py-3 bg-primary hover:bg-primary-hover text-white text-sm font-bold rounded-xl shadow-md hover:shadow-lg transition-all"
              >
                获取 {{ bundle.country_profile.country_name_en }} 专项到港报价 (CIF)
              </button>
              <a
                :href="whatsappUrl"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-2 px-5 py-3 bg-[#25D366] hover:bg-[#20ba59] text-white text-sm font-bold rounded-xl shadow-sm transition-all"
              >
                <span>WhatsApp 在线详谈</span>
              </a>
            </div>
          </div>

          <div class="lg:col-span-5">
            <div class="relative bg-white p-4 rounded-2xl border border-border/60 shadow-lg overflow-hidden">
              <img
                :src="bundle.product.image_url || '/images/product-default.jpg'"
                :alt="bundle.product.name"
                class="w-full h-72 sm:h-80 object-cover rounded-xl"
              >
              <div class="absolute bottom-6 left-6 right-6 bg-black/75 backdrop-blur-md px-4 py-3 rounded-xl text-white text-xs">
                <div class="flex items-center justify-between font-semibold mb-1">
                  <span>{{ bundle.country_profile.destination_ports[0] }} 直航专线</span>
                  <span class="text-[#25D366]">{{ bundle.country_profile.transit_days }}</span>
                </div>
                <p class="text-white/80 line-clamp-1">
                  {{ bundle.shipping_logistics.container_load_advice }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Pain Points & Compliance Grid -->
      <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white p-6 rounded-2xl border border-border/60 shadow-sm">
            <h2 class="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-primary" />
              {{ bundle.country_profile.country_name_en }} 施工环境与痛点对标
            </h2>
            <ul class="space-y-3">
              <li
                v-for="(point, idx) in bundle.country_profile.primary_pain_points"
                :key="idx"
                class="flex items-start gap-3 text-sm text-text-secondary leading-relaxed bg-[#f8faf9] p-3 rounded-xl border border-border/40"
              >
                <span class="text-primary font-bold text-xs mt-0.5">0{{ idx + 1 }}</span>
                <span>{{ point }}</span>
              </li>
            </ul>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-border/60 shadow-sm">
            <h2 class="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-primary" />
              国际认证与当地清关合规 (Compliance)
            </h2>
            <div class="space-y-4">
              <div>
                <span class="block text-xs font-semibold text-text-secondary uppercase mb-2">执行与互认标准：</span>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="(std, sIdx) in bundle.country_profile.local_standards"
                    :key="sIdx"
                    class="px-3 py-1.5 rounded-lg bg-primary/5 text-primary text-xs font-semibold border border-primary/20"
                  >
                    ✓ {{ std }}
                  </span>
                </div>
              </div>

              <div class="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/60 text-xs text-amber-900 leading-relaxed">
                <strong>关税与清关优势：</strong>
                {{ bundle.country_profile.preferential_tariffs }}
              </div>

              <div>
                <span class="block text-xs font-semibold text-text-secondary uppercase mb-2">随货出具法定单证 (7步履约)：</span>
                <div class="grid grid-cols-2 gap-2 text-xs text-text-primary">
                  <span
                    v-for="(doc, dIdx) in bundle.shipping_logistics.documents_provided"
                    :key="dIdx"
                    class="flex items-center gap-1.5"
                  >
                    <span class="text-primary">●</span> {{ doc }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ Section -->
      <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="bg-white p-6 sm:p-8 rounded-2xl border border-border/60 shadow-sm">
          <div class="max-w-3xl mb-6">
            <h2 class="text-xl font-bold text-text-primary mb-2">
              {{ bundle.country_profile.country_name_en }} 采购疑虑深度解答 (FAQ)
            </h2>
            <p class="text-xs sm:text-sm text-text-secondary">
              针对该国客户关心的包装受潮、海关清关、海运航程与抗候耐受性的官方回答。
            </p>
          </div>

          <div class="space-y-4">
            <div
              v-for="(faq, fIdx) in bundle.faqs"
              :key="fIdx"
              class="border border-border/50 rounded-xl p-4 sm:p-5 hover:border-primary/40 transition-colors"
            >
              <h3 class="text-sm sm:text-base font-bold text-text-primary mb-2 flex items-start gap-2">
                <span class="text-primary font-mono text-sm">Q:</span>
                <span>{{ faq.question_en }} ({{ faq.question_zh }})</span>
              </h3>
              <p class="text-xs sm:text-sm text-text-secondary leading-relaxed pl-6">
                {{ faq.answer_en }}
              </p>
              <p class="text-xs text-text-secondary/80 leading-relaxed pl-6 mt-1 font-sans">
                译文: {{ faq.answer_zh }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Inquiry Section -->
      <section
        id="inquiry-section"
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        <div class="bg-gradient-to-br from-primary/5 via-white to-primary/5 p-6 sm:p-10 rounded-3xl border border-primary/20 shadow-md">
          <div class="max-w-2xl mx-auto text-center mb-8">
            <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-2">
              索取 {{ bundle.country_profile.country_name_en }} 港口到岸价 (CIF) 与技术样品
            </h2>
            <p class="text-xs sm:text-sm text-text-secondary">
              由 YouDing 外贸获客团队直通对接，10 分钟内完成配载核价与提单预排
            </p>
          </div>

          <form
            @submit.prevent="submitCountryInquiry"
            class="max-w-xl mx-auto space-y-4"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-text-secondary mb-1">您的姓名 / Name *</label>
                <input
                  v-model="inquiryForm.name"
                  type="text"
                  required
                  class="w-full px-4 py-2.5 text-sm bg-white border border-border rounded-xl focus:outline-none focus:border-primary"
                  placeholder="e.g. Abdullah Al-Otaibi"
                >
              </div>
              <div>
                <label class="block text-xs font-semibold text-text-secondary mb-1">邮箱 / Email *</label>
                <input
                  v-model="inquiryForm.email"
                  type="email"
                  required
                  class="w-full px-4 py-2.5 text-sm bg-white border border-border rounded-xl focus:outline-none focus:border-primary"
                  placeholder="name@company.com"
                >
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-text-secondary mb-1">国际电话 / WhatsApp *</label>
                <input
                  v-model="inquiryForm.phone"
                  type="tel"
                  required
                  class="w-full px-4 py-2.5 text-sm bg-white border border-border rounded-xl focus:outline-none focus:border-primary"
                  placeholder="+966 50 123 4567"
                >
              </div>
              <div>
                <label class="block text-xs font-semibold text-text-secondary mb-1">目的港口 / Destination Port</label>
                <select
                  v-model="inquiryForm.destinationPort"
                  class="w-full px-4 py-2.5 text-sm bg-white border border-border rounded-xl focus:outline-none focus:border-primary"
                >
                  <option
                    v-for="(port, pIdx) in bundle.country_profile.destination_ports"
                    :key="pIdx"
                    :value="port"
                  >
                    {{ port }}
                  </option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-text-secondary mb-1">项目需求 / Requirements</label>
              <textarea
                v-model="inquiryForm.message"
                rows="3"
                class="w-full px-4 py-2.5 text-sm bg-white border border-border rounded-xl focus:outline-none focus:border-primary"
                placeholder="Please specify required quantity, application type, and project location..."
              />
            </div>

            <button
              type="submit"
              :disabled="submitting"
              class="w-full py-3.5 bg-primary hover:bg-primary-hover text-white text-sm font-bold rounded-xl shadow-lg transition-all disabled:opacity-50"
            >
              {{ submitting ? '正在加密提交询盘...' : '立即获取专属技术方案与报价单 (PI)' }}
            </button>

            <p
              v-if="submitSuccess"
              class="text-center text-xs text-primary font-semibold mt-2"
            >
              ✓ 询盘已成功送达！我们的外贸专员将通过 WhatsApp 与邮件在 2 小时内与您联络。
            </p>
          </form>
        </div>
      </section>

      <!-- Global WhatsApp Floating Bubble -->
      <WhatsAppFloatBubble
        :product-name="(bundle.product.name_en || bundle.product.name) + ' (' + bundle.country_profile.country_name_en + ')'"
        :product-slug="productSlug"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useHead } from '#imports';
import { useApi } from '~/composables/useApi';
import { useMarketingBeacon } from '~/composables/useMarketingBeacon';
import WhatsAppFloatBubble from '~/components/marketing/WhatsAppFloatBubble.vue';

const route = useRoute();
const { request } = useApi();
const { trackLeadSubmitted, trackViewItem } = useMarketingBeacon();

const countryCode = computed(() => (route.params.country as string || 'sa').toLowerCase());
const productSlug = computed(() => route.params.slug as string || '');

const bundle = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const submitting = ref(false);
const submitSuccess = ref(false);

const inquiryForm = reactive({
  name: '',
  email: '',
  phone: '',
  destinationPort: '',
  message: '',
});

const whatsappUrl = computed(() => {
  if (!bundle.value) return 'https://wa.me/';
  const prodName = bundle.value.product?.name_en || bundle.value.product?.name || '';
  const cName = bundle.value.country_profile?.country_name_en || '';
  const text = 'Hello, I am inquiring about ' + prodName + ' for ' + cName;
  return 'https://wa.me/?text=' + encodeURIComponent(text);
});

async function fetchBundle() {
  loading.value = true;
  error.value = null;
  try {
    const res: any = await request('/geo/solutions/' + countryCode.value + '/' + productSlug.value, {
      method: 'GET',
    });
    if (res && res.data) {
      bundle.value = res.data;
      if (bundle.value.country_profile?.destination_ports?.length) {
        inquiryForm.destinationPort = bundle.value.country_profile.destination_ports[0];
      }
      trackViewItem(bundle.value.product.id, bundle.value.product.name_en || bundle.value.product.name);
      injectSEO(bundle.value);
    } else {
      error.value = '未获取到有效数据包';
    }
  } catch (err: any) {
    error.value = err?.message || '获取方案失败';
  } finally {
    loading.value = false;
  }
}

function injectSEO(data: any) {
  if (!data || !data.seo) return;

  const scriptTags: any[] = [];
  if (data.schemas?.product) {
    scriptTags.push({
      type: 'application/ld+json',
      children: JSON.stringify(data.schemas.product),
    });
  }
  if (data.schemas?.breadcrumbs) {
    scriptTags.push({
      type: 'application/ld+json',
      children: JSON.stringify(data.schemas.breadcrumbs),
    });
  }

  useHead({
    title: data.seo.meta_title,
    meta: [
      { name: 'description', content: data.seo.meta_description },
      { name: 'keywords', content: data.seo.keywords },
      { property: 'og:title', content: data.seo.meta_title },
      { property: 'og:description', content: data.seo.meta_description },
      { property: 'og:image', content: data.product.image_url || '' },
      { property: 'og:url', content: data.seo.canonical_url },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
    link: [
      { rel: 'canonical', href: data.seo.canonical_url },
    ],
    script: scriptTags,
  });
}

function scrollToInquiry() {
  const el = document.getElementById('inquiry-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
}

async function submitCountryInquiry() {
  submitting.value = true;
  submitSuccess.value = false;
  try {
    await request('/marketing/events', {
      method: 'POST',
      body: {
        event_name: 'generate_lead',
        event_data: {
          name: inquiryForm.name,
          email: inquiryForm.email,
          phone: inquiryForm.phone,
          country: countryCode.value,
          destination_port: inquiryForm.destinationPort,
          message: inquiryForm.message,
          product_slug: productSlug.value,
          product_id: bundle.value?.product?.id,
          source: 'geo_matrix_solution_landing',
        },
      },
    });

    trackLeadSubmitted({
      name: inquiryForm.name,
      email: inquiryForm.email,
      phone: inquiryForm.phone,
      product: bundle.value?.product?.name,
      country: countryCode.value,
    });

    submitSuccess.value = true;
    inquiryForm.message = '';
  } catch (err) {
    console.error('Submit inquiry failed:', err);
  } finally {
    submitting.value = false;
  }
}

await fetchBundle();
</script>
