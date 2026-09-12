<template>
  <div>
    <section
      class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700"
    >
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
        <div class="text-center">
          <div
            class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-6"
          >
            <span class="w-2 h-2 bg-secondary-400 rounded-full mr-2" />
            <span class="text-sm font-medium text-white">{{ $t('about.heroBadge') }}</span>
          </div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
            {{ $t('about.heroTitle') }}
          </h1>
          <p class="text-xl text-white/80 max-w-3xl mx-auto">
            {{ $t('about.heroDesc') }}
          </p>
        </div>
      </div>
    </section>

    <section class="py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
              <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
              <span class="text-sm font-medium text-secondary-600">{{ $t('about.companyIntro') }}</span>
            </div>
            <h2 class="text-3xl md:text-4xl font-bold text-primary-900 mb-6">
              {{ $t('about.companyTitle1') }}<br><span class="text-secondary-600">{{ $t('about.companyTitle2') }}</span>
            </h2>
            <div class="space-y-4 text-text-secondary leading-relaxed">
              <p>
                {{ $t('about.aboutText1') }}
              </p>
              <p>
                {{ $t('about.aboutText2') }}
              </p>
              <p>
                {{ $t('about.aboutText3') }}
              </p>
            </div>
          </div>
          <div
            class="bg-gradient-to-br from-secondary-50 to-accent-50 rounded-2xl p-8 border border-secondary-100"
          >
            <div class="grid grid-cols-2 gap-8 text-center">
              <div
                v-for="stat in stats"
                :key="stat.label"
                class="group"
              >
                <div
                  class="w-16 h-16 mx-auto mb-3 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-lg shadow-secondary-200 group-hover:scale-110 transition-transform duration-300"
                >
                  <span class="text-2xl font-bold text-white">{{ stat.value.charAt(0) }}</span>
                </div>
                <div class="text-3xl font-bold text-primary-900">
                  {{ stat.value }}
                </div>
                <div class="text-sm text-text-muted mt-1">
                  {{ stat.label }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          {{ $t('about.history') }}
        </h2>
        <p class="section-subtitle">
          {{ $t('about.historyDesc') }}
        </p>
        <div class="max-w-4xl mx-auto relative">
          <div
            class="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-secondary-400 via-accent-400 to-warm-400 hidden md:block"
          />
          <div
            v-for="(milestone, idx) in milestones"
            :key="idx"
            class="relative flex items-start space-x-4 md:space-x-8 mb-8 last:mb-0"
          >
            <div
              class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-secondary-500 to-accent-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg shadow-secondary-200"
            >
              {{ idx + 1 }}
            </div>
            <div
              class="flex-1 bg-white rounded-2xl p-6 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300"
            >
              <div class="flex items-center justify-between mb-2">
                <span
                  class="text-sm font-semibold text-secondary-600 bg-secondary-50 px-3 py-1 rounded-full"
                >{{ milestone.year }}</span>
              </div>
              <p class="text-text-secondary">
                {{ milestone.text }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          {{ $t('about.certifications') }}
        </h2>
        <p class="section-subtitle">
          {{ $t('about.certificationsDesc') }}
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div
            v-for="cert in certifications"
            :key="cert"
            class="group bg-white rounded-2xl p-6 text-center border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1"
          >
            <div
              class="w-14 h-14 bg-gradient-to-br from-secondary-50 to-accent-50 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300"
            >
              <svg
                class="w-7 h-7 text-secondary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p class="text-sm font-medium text-primary-900 leading-tight">
              {{ cert }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Company Location Map -->
    <section class="py-16 bg-surface-elevated">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="inline-flex items-center px-2.5 py-1.5 bg-secondary-50 rounded-full mb-3 sm:mb-4">
          <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
          <span class="text-xs sm:text-sm font-medium text-secondary-600">{{ $t('about.location') }}</span>
        </div>
        <h2 class="text-2xl sm:text-3xl lg:text-4xl font-bold text-primary-900 mb-4 sm:mb-6">
          {{ $t('about.findUs') }}
        </h2>
        <p class="text-text-secondary mb-6 sm:mb-8 max-w-2xl">
          {{ $t('about.locationDesc') }}
        </p>
        <div class="rounded-xl sm:rounded-2xl overflow-hidden shadow-card border border-border">
          <iframe
            src="https://uri.amap.com/marker?position=112.454,34.619&name=%E4%B8%AD%E5%9B%BD%E5%BB%BA%E6%9D%90%E4%BA%A7%E4%B8%9A%E5%9B%AD%E5%8C%BA&coordinate=gaode"
            width="100%"
            height="400"
            style="border:0;"
            allowfullscreen
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            :title="$t('about.location')"
          />
        </div>
        <p class="text-text-muted text-xs sm:text-sm mt-3 text-center">
          {{ $t('about.locationAddress') }}
        </p>
        <div class="text-center mt-4">
          <a
            href="https://uri.amap.com/marker?position=112.454,34.619&name=%E4%B8%AD%E5%9B%BD%E5%BB%BA%E6%9D%90%E4%BA%A7%E4%B8%9A%E5%9B%AD%E5%8C%BA"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center px-5 py-2.5 bg-secondary-500 hover:bg-secondary-600 text-white text-sm font-medium rounded-lg transition-all duration-300 shadow-md"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {{ $t('about.viewOnMap') }}
          </a>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          {{ $t('about.ctaTitle') }}
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          {{ $t('about.ctaDesc') }}
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink
            to="/contact"
            class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
          >
            <svg
              class="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            {{ $t('about.contactUs') }}
          </NuxtLink>
          <NuxtLink
            to="/products"
            class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
          >
            <svg
              class="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            {{ $t('about.viewProducts') }}
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useHead } from '@vueuse/head';

const { t, tm } = useI18n();

useHead({
  title: computed(() => t('about.seo.title')),
  meta: [
    { name: 'description', content: computed(() => t('about.seo.description')) },
    { name: 'keywords', content: computed(() => t('about.seo.keywords')) },
  ],
});

const stats = computed(() => [
  { label: t('about.stats.experience'), value: '20+' },
  { label: t('about.stats.customers'), value: '500+' },
  { label: t('about.stats.models'), value: '100+' },
  { label: t('about.stats.patents'), value: '30+' },
]);

const milestones = computed(() =>
  Array.from({ length: 6 }, (_, i) => {
    const msg = tm(`about.milestone${i}`);
    return {
      year: typeof msg === 'object' ? (t(`about.milestone${i}.year`)) : '',
      text: typeof msg === 'object' ? (t(`about.milestone${i}.text`)) : '',
    };
  }),
);

const certifications = computed(() =>
  Array.from({ length: 8 }, (_, i) => t(`about.cert${i}`)),
);
</script>
