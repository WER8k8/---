/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar
      safe-area-top
      :blur="true"
    >
      <div class="flex items-center h-14">
        <button
          class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="router.back()"
        >
          <svg
            class="w-5 h-5 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <h1 class="ml-2 text-base font-semibold text-gray-900">
          {{ $t('mobile.user.settings') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Settings Form -->
    <div class="px-4 py-6 space-y-6">
      <!-- Profile Section -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">
          {{ $t('mobile.settings.profile') }}
        </h2>
        <form
          @submit.prevent="updateProfile"
          class="space-y-4"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.name') }}</label>
            <input
              v-model="profileForm.name"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.email') }}</label>
            <input
              v-model="profileForm.email"
              type="email"
              disabled
              class="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-500 text-sm"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.phone') }}</label>
            <input
              v-model="profileForm.phone"
              type="tel"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.company') }}</label>
            <input
              v-model="profileForm.company"
              type="text"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <button
            type="submit"
            class="w-full mobile-btn-primary py-3 rounded-xl font-semibold text-sm"
            :disabled="profileUpdating"
          >
            {{ profileUpdating ? $t('mobile.settings.saving') : $t('mobile.settings.saveProfile') }}
          </button>
        </form>
      </div>

      <!-- Password Section -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">
          {{ $t('mobile.settings.password') }}
        </h2>
        <form
          @submit.prevent="updatePassword"
          class="space-y-4"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.currentPassword') }}</label>
            <input
              v-model="passwordForm.current"
              type="password"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.newPassword') }}</label>
            <input
              v-model="passwordForm.new"
              type="password"
              required
              minlength="8"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.settings.confirmPassword') }}</label>
            <input
              v-model="passwordForm.confirm"
              type="password"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
          </div>
          <button
            type="submit"
            class="w-full mobile-btn-primary py-3 rounded-xl font-semibold text-sm"
            :disabled="passwordUpdating"
          >
            {{ passwordUpdating ? $t('mobile.settings.updating') : $t('mobile.settings.updatePassword') }}
          </button>
        </form>
      </div>

      <!-- Language Section -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">
          {{ $t('mobile.settings.language') }}
        </h2>
        <div class="space-y-2">
          <button
            v-for="lang in languages"
            :key="lang.code"
            class="w-full flex items-center justify-between px-4 py-3 rounded-xl transition-colors"
            :class="currentLocale === lang.code ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'"
            @click="switchLanguage(lang.code)"
          >
            <span class="text-sm font-medium">{{ lang.name }}</span>
            <svg
              v-if="currentLocale === lang.code"
              class="w-5 h-5"
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
          </button>
        </div>
      </div>

      <!-- Logout Button -->
      <div class="pt-4">
        <button
          class="w-full py-3.5 rounded-xl font-semibold text-sm text-red-600 bg-white shadow-sm border border-red-200"
          @click="logout"
        >
          {{ $t('mobile.user.logout') }}
        </button>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';

const router = useRouter();
const { $t, locale } = useI18n();

// Current locale
const currentLocale = ref(locale.value);

// Profile form
const profileForm = reactive({
  name: '',
  email: '',
  phone: '',
  company: '',
});
const profileUpdating = ref(false);

// Password form
const passwordForm = reactive({
  current: '',
  new: '',
  confirm: '',
});
const passwordUpdating = ref(false);

// Languages
const languages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
];

// Load user profile
onMounted(async () => {
  try {
    const user = await $fetch('/api/user/profile');
    profileForm.name = user.name || '';
    profileForm.email = user.email || '';
    profileForm.phone = user.phone || '';
    profileForm.company = user.company || '';
  } catch (err) {
    console.error('Failed to load profile', err);
  }
});

// Update profile
const updateProfile = async () => {
  profileUpdating.value = true;
  try {
    await $fetch('/api/user/profile', {
      method: 'PUT',
      body: profileForm,
    });
    alert($t('mobile.settings.profileUpdated'));
  } catch (err) {
    alert($t('mobile.settings.updateError'));
  } finally {
    profileUpdating.value = false;
  }
};

// Update password
const updatePassword = async () => {
  if (passwordForm.new !== passwordForm.confirm) {
    alert($t('mobile.settings.passwordMismatch'));
    return;
  }
  passwordUpdating.value = true;
  try {
    await $fetch('/api/user/password', {
      method: 'PUT',
      body: {
        current: passwordForm.current,
        new: passwordForm.new,
      },
    });
    alert($t('mobile.settings.passwordUpdated'));
    passwordForm.current = '';
    passwordForm.new = '';
    passwordForm.confirm = '';
  } catch (err) {
    alert($t('mobile.settings.passwordError'));
  } finally {
    passwordUpdating.value = false;
  }
};

// Switch language
const switchLanguage = (code: string) => {
  locale.value = code as any;
  currentLocale.value = code;
  localStorage.setItem('locale', code);
};

// Logout
const logout = async () => {
  await $fetch('/api/auth/logout', { method: 'POST' });
  router.push('/mobile');
};

// Page meta
useHead({
  title: $t('mobile.user.settings'),
});
</script>
