<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Header -->
    <MobileNavbar>
      <div class="flex justify-between items-center h-14">
        <NuxtLink to="/mobile" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-sm">{{ $t('mobile.brandChar') }}</span>
          </div>
          <span class="text-lg font-bold text-gray-900">{{ $t('mobile.brandName') }}</span>
        </NuxtLink>
      </div>
    </MobileNavbar>

    <div class="pt-16">
      <!-- Hero CTA -->
      <div class="bg-gradient-to-br from-blue-600 to-blue-700 px-4 py-8 text-white">
        <div class="text-center mb-6">
          <h1 class="text-2xl font-bold mb-2">{{ $t('mobile.contact.pageTitle') }}</h1>
          <p class="text-sm text-blue-100">{{ $t('mobile.contact.heroSubtitle') }}</p>
        </div>

        <!-- One-Tap Call -->
        <a
          :href="'tel:' + SITE_CONFIG.phone"
          class="flex items-center justify-center gap-3 w-full py-4 bg-white text-blue-600 rounded-2xl font-bold text-lg shadow-lg active:scale-[0.98] transition-transform mb-3"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
          {{ $t('mobile.contact.oneTapCall') }}
        </a>

        <!-- WeChat -->
        <div
          class="flex items-center justify-between w-full py-3.5 px-4 bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20 active:bg-white/20 transition-colors cursor-pointer"
          @click="copyWechat"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8.5 11a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm4 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm-2 7C6.478 18 3 15.09 3 11.5S6.478 5 10.5 5 18 7.91 18 11.5c0 1.105-.316 2.14-.863 3.03l.863 2.97-2.97-.863A7.437 7.437 0 0110.5 18z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-semibold">{{ $t('mobile.contact.wechatService') }}</p>
              <p class="text-xs text-blue-100">{{ $t('mobile.contact.wechatId') }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs bg-white/20 px-2.5 py-1 rounded-full">{{ copied ? $t('mobile.contact.copied') : $t('mobile.contact.copy') }}</span>
          </div>
        </div>
      </div>

      <!-- Contact Info -->
      <div class="px-4 py-5 space-y-3">
        <div v-for="item in contactInfo" :key="item.label" class="flex items-center gap-3 bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <span class="text-lg">{{ item.icon }}</span>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-gray-900">{{ item.label }}</h3>
            <p class="text-sm text-gray-500">{{ item.value }}</p>
            <p v-if="item.sub" class="text-xs text-gray-400">{{ item.sub }}</p>
          </div>
        </div>
      </div>

      <!-- Message Form -->
      <div class="px-4 pb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ $t('mobile.contact.formTitle') }}</h2>
        <form class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100" @submit.prevent="handleSubmit">
          <div class="space-y-4">
            <!-- Name -->
            <div>
              <label class="block text-sm font-semibold text-gray-900 mb-1.5">{{ $t('mobile.contact.nameLabel') }} <span class="text-red-500">{{ $t('mobile.contact.nameRequired') }}</span></label>
              <input
                v-model="form.name"
                required
                class="w-full px-3 py-2.5 bg-gray-50 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                :class="formErrors.name ? 'border-red-300' : 'border-gray-200'"
                :placeholder="$t('mobile.contact.namePlaceholder')"
              >
              <p v-if="formErrors.name" class="text-red-500 text-xs mt-1">{{ formErrors.name }}</p>
            </div>

            <!-- Phone -->
            <div>
              <label class="block text-sm font-semibold text-gray-900 mb-1.5">{{ $t('mobile.contact.phoneLabel') }} <span class="text-red-500">{{ $t('mobile.contact.nameRequired') }}</span></label>
              <input
                v-model="form.phone"
                required
                type="tel"
                class="w-full px-3 py-2.5 bg-gray-50 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                :class="formErrors.phone ? 'border-red-300' : 'border-gray-200'"
                :placeholder="$t('mobile.contact.phonePlaceholder')"
              >
              <p v-if="formErrors.phone" class="text-red-500 text-xs mt-1">{{ formErrors.phone }}</p>
            </div>

            <!-- WeChat ID -->
            <div>
              <label class="block text-sm font-semibold text-gray-900 mb-1.5">{{ $t('mobile.contact.wechatLabel') }} <span class="text-blue-500">({{ $t('mobile.contact.wechatRecommended') }})</span></label>
              <input
                v-model="form.wechat"
                class="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                :placeholder="$t('mobile.contact.wechatPlaceholder')"
              >
            </div>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full mt-5 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold text-sm shadow-lg disabled:opacity-50 active:scale-[0.98] transition-all"
          >
            {{ submitting ? $t('mobile.contact.submitting') : $t('mobile.contact.submitMessage') }}
          </button>

          <p v-if="submitSuccess" class="text-green-600 text-center font-medium mt-4 text-sm flex items-center justify-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ $t('mobile.contact.submitSuccess') }}
          </p>
          <p v-if="submitError" class="text-red-500 text-center font-medium mt-4 text-sm">{{ submitError }}</p>
        </form>
      </div>
    </div>

    <!-- Mobile Bottom Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useApi } from '~/composables/useApi';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();
const { request } = useApi();

const contactInfo = computed(() => [
  { icon: '📞', label: t('mobile.contact.hotline'), value: SITE_CONFIG.phone, sub: t('mobile.contact.hotline24h') },
  { icon: '📧', label: t('mobile.contact.emailLabel'), value: SITE_CONFIG.email, sub: t('mobile.contact.emailReply') },
  { icon: '📍', label: t('mobile.contact.addressLabel'), value: t('mobile.contact.addressValue'), sub: t('mobile.contact.addressVisit') },
]);

const form = reactive({
  name: '',
  phone: '',
  wechat: '',
});

const formErrors = reactive({
  name: '',
  phone: '',
});

const submitting = ref(false);
const submitSuccess = ref(false);
const submitError = ref('');
const copied = ref(false);

function validateForm(): boolean {
  let isValid = true;
  formErrors.name = '';
  formErrors.phone = '';

  if (!form.name.trim()) {
    formErrors.name = t('mobile.contact.errorNameRequired');
    isValid = false;
  } else if (form.name.trim().length < 2) {
    formErrors.name = t('mobile.contact.errorNameTooShort');
    isValid = false;
  }

  if (!form.phone.trim()) {
    formErrors.phone = t('mobile.contact.errorPhoneRequired');
    isValid = false;
  } else if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    formErrors.phone = t('mobile.contact.errorPhoneInvalid');
    isValid = false;
  }

  return isValid;
}

async function handleSubmit() {
  submitSuccess.value = false;
  submitError.value = '';

  if (!validateForm()) return;

  submitting.value = true;
  try {
    await request('/inquiries', { method: 'POST', body: { ...form, source: 'mobile' } });
    submitSuccess.value = true;
    form.name = '';
    form.phone = '';
    form.wechat = '';
    setTimeout(() => {
      submitSuccess.value = false;
    }, 3000);
  } catch (e: any) {
    submitError.value = e.message || t('mobile.contact.submitFailed');
  } finally {
    submitting.value = false;
  }
}

function copyWechat() {
  navigator.clipboard.writeText('youding-builder').then(() => {
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  }).catch(() => {
    // Fallback: select text approach
    const textArea = document.createElement('textarea');
    textArea.value = 'youding-builder';
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  });
}

useHead({
  title: t('mobile.contact.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.contact.seoDesc') },
  ],
});
</script>
