<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <div class="flex items-center justify-between h-14">
        <h1 class="text-lg font-semibold text-gray-900">{{ $t('mobile.user.center') }}</h1>
        <button
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="logout"
        >
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </MobileNavbar>

    <!-- User Profile Card -->
    <div class="px-4 pt-6 pb-4">
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold text-gray-900 truncate">{{ user?.name || $t('mobile.user.guest') }}</h2>
            <p class="text-sm text-gray-500 truncate">{{ user?.email || '' }}</p>
          </div>
        </div>
        <!-- Quick Stats -->
        <div class="grid grid-cols-3 gap-3 pt-4 border-t border-gray-100">
          <div class="text-center">
            <div class="text-xl font-bold text-blue-600">{{ stats.orders || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ $t('mobile.user.orders') }}</div>
          </div>
          <div class="text-center">
            <div class="text-xl font-bold text-green-600">{{ stats.inquiries || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ $t('mobile.user.inquiries') }}</div>
          </div>
          <div class="text-center">
            <div class="text-xl font-bold text-purple-600">{{ stats.quotes || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ $t('mobile.user.quotes') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Menu Items -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl overflow-hidden">
        <NuxtLink
          v-for="(item, idx) in menuItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-5 py-4 transition-colors"
          :class="idx !== menuItems.length - 1 ? 'border-b border-gray-100' : ''"
        >
          <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon" />
            </svg>
          </div>
          <span class="flex-1 text-sm font-medium text-gray-900">{{ item.label }}</span>
          <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </NuxtLink>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const { $t } = useI18n();
const router = useRouter();

// User data
const { data: user } = await useFetch('/api/user/profile', { lazy: true });

// Stats
const { data: stats } = await useFetch('/api/user/stats', { lazy: true });

// Menu items
const menuItems = [
  {
    to: '/mobile/user/orders',
    label: $t('mobile.user.myOrders'),
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  },
  {
    to: '/mobile/inquiries',
    label: $t('mobile.user.myInquiries'),
    icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
  },
  {
    to: '/mobile/user/settings',
    label: $t('mobile.user.settings'),
    icon: 'M10.325 4.517c.128-2.108.328-2.05.328-3.7a1.724 1.724 0 00-2.573-1.066c-1.543.94-2.16 2.035-2.16 3.7 0 2.728-1.694 4.927-3.773 5.78a1.724 1.724 0 00-1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543 2.035 2.16 3.7 2.16 2.728 0 4.927 1.694 5.78 3.773a1.724 1.724 0 002.573 0c1.543-.94 2.16-2.035 2.16-3.7 0-2.728 1.694-4.927 3.773-5.78a1.724 1.724 0 002.573-2.573c-.94-1.543-2.035-2.16-3.7-2.16-2.728 0-4.927-1.694-5.78-3.773a1.724 1.724 0 00-2.573 0z M12 14.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z',
  },
];

// Logout
const logout = async () => {
  await $fetch('/api/auth/logout', { method: 'POST' });
  router.push('/mobile');
};

// Page meta
useHead({
  title: $t('mobile.user.center'),
});
</script>
