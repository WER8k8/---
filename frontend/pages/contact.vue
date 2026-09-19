/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div>
    <section
      class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700"
    >
      <div class="absolute inset-0 opacity-10">
        <div
          class="absolute top-1/4 right-0 w-48 h-48 sm:w-64 sm:h-64 lg:w-96 lg:h-96 bg-secondary-400 rounded-full blur-3xl"
        />
        <div
          class="absolute bottom-1/4 left-0 w-40 h-40 sm:w-64 sm:h-64 lg:w-80 lg:h-80 bg-accent-400 rounded-full blur-3xl"
        />
      </div>
      <div class="relative max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-12 sm:py-16 lg:py-20">
        <div class="text-center">
          <div
            class="inline-flex items-center px-3 py-1.5 bg-white/10 backdrop-blur-sm rounded-full mb-4 sm:mb-6"
          >
            <span class="w-1.5 h-1.5 bg-secondary-400 rounded-full mr-2" />
            <span class="text-xs sm:text-sm font-medium text-white">{{ t('contact.heroBadge') }}</span>
          </div>
          <h1
            class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-3 sm:mb-4 leading-tight"
          >
            {{ t('contact.heroTitle') }}
          </h1>
          <p class="text-xs sm:text-sm md:text-lg lg:text-xl text-white/80">
            {{ t('contact.heroSubtitle') }}
          </p>
        </div>
      </div>
    </section>

    <section class="py-8 sm:py-12 lg:py-16 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-12">
          <div>
            <div
              class="inline-flex items-center px-2.5 py-1.5 bg-secondary-50 rounded-full mb-3 sm:mb-4"
            >
              <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
              <span class="text-xs sm:text-sm font-medium text-secondary-600">{{ t('contact.contactInfoBadge') }}</span>
            </div>
            <h2
              class="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold text-primary-900 mb-4 sm:mb-6 lg:mb-8"
            >
              {{ t('contact.infoTitle') }}
            </h2>
            <div class="space-y-4 sm:space-y-6">
              <div
                v-for="item in contactInfo"
                :key="item.label"
                class="group flex items-start space-x-3 sm:space-x-4 p-3 sm:p-4 lg:p-5 bg-white rounded-lg sm:rounded-xl border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300"
              >
                <div
                  class="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-secondary-50 to-accent-50 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform"
                >
                  <span class="text-sm sm:text-base lg:text-xl">{{ item.icon }}</span>
                </div>
                <div>
                  <h3 class="text-xs sm:text-sm font-semibold text-primary-900">
                    {{ item.label }}
                  </h3>
                  <p class="text-xs sm:text-sm text-text-secondary mt-0.5 sm:mt-1">
                    {{ item.value }}
                  </p>
                  <p
                    v-if="item.sub"
                    class="text-text-muted text-xs mt-0.5"
                  >
                    {{ item.sub }}
                  </p>
                </div>
              </div>
            </div>

            <div
              class="mt-6 sm:mt-8 lg:mt-12 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-xl sm:rounded-2xl p-4 sm:p-6 lg:p-8 text-white shadow-lg shadow-secondary-200"
            >
              <div class="flex items-center space-x-2 sm:space-x-3 mb-3 sm:mb-4">
                <div
                  class="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-lg sm:rounded-xl flex items-center justify-center"
                >
                  <svg
                    class="w-5 h-5 sm:w-6 sm:h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 class="text-base sm:text-lg lg:text-xl font-bold">
                    {{ t('contact.onlineConsultTitle') }}
                  </h3>
                  <p class="text-white/70 text-xs sm:text-sm">
                    {{ t('contact.onlineConsultDesc') }}
                  </p>
                </div>
              </div>
              <p class="text-white/80 text-xs sm:text-sm mb-4 sm:mb-6">
                {{ t('contact.workHours') }}
              </p>
              <a
                :href="'tel:' + SITE_CONFIG.phone"
                class="inline-flex items-center justify-center px-4 sm:px-6 lg:px-8 py-3 sm:py-4 bg-white text-secondary-600 font-semibold rounded-lg sm:rounded-xl hover:bg-gray-100 transition-all shadow-md w-full"
              >
                <svg
                  class="w-4 h-4 sm:w-5 sm:h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
                <span class="text-xs sm:text-sm">{{ t('contact.callButton') }}</span>
              </a>
            </div>
          </div>

          <div>
            <div
              class="inline-flex items-center px-2.5 py-1.5 bg-accent-50 rounded-full mb-3 sm:mb-4"
            >
              <span class="w-1.5 h-1.5 bg-accent-500 rounded-full mr-2" />
              <span class="text-xs sm:text-sm font-medium text-accent-600">{{ t('contact.formBadge') }}</span>
            </div>
            <h2
              class="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold text-primary-900 mb-4 sm:mb-6 lg:mb-8"
            >
              {{ t('contact.formTitle') }}
            </h2>
            <form
              class="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 lg:p-8 border border-border shadow-card"
              @submit.prevent="handleSubmit"
            >
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 lg:gap-6">
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formNameLabel') }} <span class="text-danger">*</span></label>
                  <input
                    v-model="form.name"
                    required
                    :class="[
                      'w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border rounded-lg sm:rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:ring-2 transition-all text-sm',
                      formErrors.name
                        ? 'border-danger focus:border-danger focus:ring-danger/20'
                        : 'border-border focus:border-secondary-500 focus:ring-secondary-500/20',
                    ]"
                    :placeholder="t('contact.formNamePlaceholder')"
                  >
                  <p
                    v-if="formErrors.name"
                    class="text-danger text-xs mt-1"
                  >
                    {{ formErrors.name }}
                  </p>
                </div>
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formPhoneLabel') }} <span class="text-danger">*</span></label>
                  <input
                    v-model="form.phone"
                    required
                    type="tel"
                    :class="[
                      'w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border rounded-lg sm:rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:ring-2 transition-all text-sm',
                      formErrors.phone
                        ? 'border-danger focus:border-danger focus:ring-danger/20'
                        : 'border-border focus:border-secondary-500 focus:ring-secondary-500/20',
                    ]"
                    :placeholder="t('contact.formPhonePlaceholder')"
                  >
                  <p
                    v-if="formErrors.phone"
                    class="text-danger text-xs mt-1"
                  >
                    {{ formErrors.phone }}
                  </p>
                </div>
              </div>
              <div>
                <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formWechatLabel') }} <span class="text-secondary-500">{{ t('contact.formWechatRecommend') }}</span></label>
                <input
                  v-model="form.wechat"
                  :class="[
                    'w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border rounded-lg sm:rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:ring-2 transition-all text-sm',
                    formErrors.wechat
                      ? 'border-danger focus:border-danger focus:ring-danger/20'
                      : 'border-border focus:border-secondary-500 focus:ring-secondary-500/20',
                  ]"
                  :placeholder="t('contact.formWechatPlaceholder')"
                >
                <p
                  v-if="formErrors.wechat"
                  class="text-danger text-xs mt-1"
                >
                  {{ formErrors.wechat }}
                </p>
              </div>
              <div>
                <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formEmailLabel') }}</label>
                <input
                  v-model="form.email"
                  type="email"
                  :class="[
                    'w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border rounded-lg sm:rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:ring-2 transition-all text-sm',
                    formErrors.email
                      ? 'border-danger focus:border-danger focus:ring-danger/20'
                      : 'border-border focus:border-secondary-500 focus:ring-secondary-500/20',
                  ]"
                  :placeholder="t('contact.formEmailPlaceholder')"
                >
                <p
                  v-if="formErrors.email"
                  class="text-danger text-xs mt-1"
                >
                  {{ formErrors.email }}
                </p>
              </div>
              <div>
                <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formProductLabel') }}</label>
                <select
                  v-model="form.product"
                  class="w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border border-border rounded-lg sm:rounded-xl text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all text-sm"
                >
                  <option value="">
                    {{ t('contact.formProductPlaceholder') }}
                  </option>
                  <option value="light-aggregate">
                    {{ t('contact.formProductLight') }}
                  </option>
                  <option value="ceramsite">
                    {{ t('contact.formProductCeramsite') }}
                  </option>
                  <option value="mortar">
                    {{ t('contact.formProductMortar') }}
                  </option>
                  <option value="other">
                    {{ t('contact.formProductOther') }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-xs sm:text-sm font-semibold text-primary-900 mb-1.5">{{ t('contact.formMessageLabel') }} <span class="text-danger">*</span></label>
                <textarea
                  v-model="form.message"
                  required
                  rows="4"
                  :class="[
                    'w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border rounded-lg sm:rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:ring-2 transition-all resize-none text-sm',
                    formErrors.message
                      ? 'border-danger focus:border-danger focus:ring-danger/20'
                      : 'border-border focus:border-secondary-500 focus:ring-secondary-500/20',
                  ]"
                  :placeholder="t('contact.formMessagePlaceholder')"
                />
                <p
                  v-if="formErrors.message"
                  class="text-danger text-xs mt-1"
                >
                  {{ formErrors.message }}
                </p>
                <p class="text-text-muted text-xs mt-1">
                  {{ form.message.length }}/500
                </p>
              </div>
              <button
                type="submit"
                :disabled="submitting"
                class="w-full px-4 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-lg sm:rounded-xl hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 font-semibold transition-all shadow-lg shadow-secondary-200 text-sm mt-2 sm:mt-4"
              >
                {{ submitting ? t('contact.submitting') : t('contact.formSubmit') }}
              </button>
              <p
                v-if="submitSuccess"
                class="text-accent-600 text-center font-medium mt-3 sm:mt-4 flex items-center justify-center"
              >
                <svg
                  class="w-4 h-4 sm:w-5 sm:h-5 mr-2"
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
                <span class="text-xs sm:text-sm">{{ t('contact.formSuccess') }}</span>
              </p>
              <p
                v-if="submitError"
                class="text-danger text-center font-medium mt-3 sm:mt-4 text-xs sm:text-sm"
              >
                {{ submitError }}
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>

    <section class="py-8 sm:py-12 lg:py-16 bg-gradient-to-r from-primary-800 to-primary-900">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <div
          class="bg-white/10 backdrop-blur-sm rounded-xl sm:rounded-2xl p-4 sm:p-6 lg:p-8 text-center"
        >
          <div class="flex items-center justify-center mb-3 sm:mb-4">
            <div
              class="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 rounded-lg sm:rounded-xl flex items-center justify-center mr-3 sm:mr-4"
            >
              <svg
                class="w-5 h-5 sm:w-6 sm:h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
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
            </div>
            <div>
              <h3 class="text-base sm:text-lg lg:text-xl font-bold text-white">
                {{ t('contact.companyAddress') }}
              </h3>
              <p class="text-white/70 text-xs sm:text-sm">
                {{ t('contact.companyAddressDetail') }}
              </p>
            </div>
          </div>
          <div class="mt-4">
            <a
              href="https://uri.amap.com/marker?position=112.454,34.619&name=%E4%B8%AD%E5%9B%BD%E5%BB%BA%E6%9D%90%E4%BA%A7%E4%B8%9A%E5%9B%AD%E5%8C%BA"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center px-4 py-2 bg-white/15 hover:bg-white/25 text-white text-sm font-medium rounded-lg transition-all duration-300"
            >
              <svg
                class="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
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
              {{ t('contact.mapLinkText') }}
            </a>
          </div>
        </div>
      </div>
    </section>

    <section class="py-8 sm:py-12 lg:py-16 bg-surface">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <div class="inline-flex items-center px-2.5 py-1.5 bg-secondary-50 rounded-full mb-3 sm:mb-4">
          <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
          <span class="text-xs sm:text-sm font-medium text-secondary-600">{{ t('contact.mapBadge') }}</span>
        </div>
        <h2 class="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold text-primary-900 mb-4 sm:mb-6 lg:mb-8">
          {{ t('contact.mapTitle') }}
        </h2>
        <div class="rounded-xl sm:rounded-2xl overflow-hidden shadow-card border border-border">
          <iframe
            src="https://uri.amap.com/marker?position=112.454,34.619&name=%E4%B8%AD%E5%9B%BD%E5%BB%BA%E6%9D%90%E4%BA%A7%E4%B8%9A%E5%9B%AD%E5%8C%BA&coordinate=gaode"
            width="100%"
            height="400"
            style="border:0;"
            allowfullscreen
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            :title="t('contact.mapIframeTitle')"
          />
        </div>
        <p class="text-text-muted text-xs sm:text-sm mt-3 text-center">
          {{ t('contact.mapAddressText') }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useApi } from '~/composables/useApi';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();

useHead({
  title: t('contact.seoTitle'),
  meta: [
    { name: 'description', content: t('contact.seoDescription') },
    { name: 'keywords', content: t('contact.seoKeywords') },
  ],
});

const { request } = useApi();

const contactInfo = computed(() => t('contact.contactInfoItems') as { icon: string; label: string; value: string; sub: string }[]);

const form = reactive({
  name: '',
  phone: '',
  wechat: '',
  email: '',
  product: '',
  message: '',
});

const formErrors = reactive({
  name: '',
  phone: '',
  wechat: '',
  email: '',
  message: '',
});

const submitting = ref(false);
const submitSuccess = ref(false);
const submitError = ref('');

function validateForm(): boolean {
  let isValid = true;

  formErrors.name = '';
  formErrors.phone = '';
  formErrors.email = '';
  formErrors.message = '';

  if (!form.name.trim()) {
    formErrors.name = t('contact.valNameRequired');
    isValid = false;
  } else if (form.name.trim().length < 2) {
    formErrors.name = t('contact.valNameMinLength');
    isValid = false;
  }

  if (!form.phone.trim()) {
    formErrors.phone = t('contact.valPhoneRequired');
    isValid = false;
  } else if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    formErrors.phone = t('contact.valPhoneInvalid');
    isValid = false;
  }

  if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    formErrors.email = t('contact.valEmailInvalid');
    isValid = false;
  }

  if (!form.message.trim()) {
    formErrors.message = t('contact.valMessageRequired');
    isValid = false;
  } else if (form.message.trim().length < 10) {
    formErrors.message = t('contact.valMessageMinLength');
    isValid = false;
  }

  return isValid;
}

async function handleSubmit() {
  submitSuccess.value = false;
  submitError.value = '';

  if (!validateForm()) {
    return;
  }

  submitting.value = true;
  try {
    await request('/inquiries', { method: 'POST', body: { ...form } });
    submitSuccess.value = true;
    form.name = '';
    form.phone = '';
    form.email = '';
    form.product = '';
    form.message = '';
    setTimeout(() => {
      submitSuccess.value = false;
    }, 3000);
  } catch (e: any) {
    submitError.value = e.message || t('contact.submitFallbackError');
  } finally {
    submitting.value = false;
  }
}
</script>
