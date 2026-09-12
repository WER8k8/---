<template>
  <nav
    class="bg-white shadow-sm border-t border-gray-100 fixed bottom-0 left-0 right-0 z-50"
    :class="safeAreaBottom ? 'pb-safe-bottom' : ''"
  >
    <div class="flex items-center justify-around h-14 max-w-lg mx-auto">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center justify-center flex-1 h-full min-h-[56px] py-1 transition-colors"
        :class="[isActive(item.path) ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700']"
      >
        <component
          :is="item.icon"
          class="w-5 h-5 mb-0.5"
          :stroke-width="isActive(item.path) ? 2.5 : 2"
        />
        <span class="text-[10px] font-medium">{{ item.label }}</span>
      </NuxtLink>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { h, computed } from 'vue';
import { useRoute } from '#app';
import { useI18n } from 'vue-i18n';

interface Props {
  safeAreaBottom?: boolean;
}

withDefaults(defineProps<Props>(), {
  safeAreaBottom: true,
});

const route = useRoute();
const { t } = useI18n();

const HomeIcon = () =>
  h(
    'svg',
    {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24',
    },
    [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
      }),
    ]
  );

const ProductIcon = () =>
  h(
    'svg',
    {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24',
    },
    [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
      }),
    ]
  );

const CaseIcon = () =>
  h(
    'svg',
    {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24',
    },
    [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      }),
    ]
  );

const NewsIcon = () =>
  h(
    'svg',
    {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24',
    },
    [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z',
      }),
    ]
  );

const navItems = computed(() => [
  { path: '/mobile', label: t('nav.home'), icon: HomeIcon },
  { path: '/mobile/products', label: t('nav.products'), icon: ProductIcon },
  { path: '/mobile/cases', label: t('nav.cases'), icon: CaseIcon },
  { path: '/mobile/news', label: t('nav.news'), icon: NewsIcon },
]);

const isActive = (path: string) =>
  route.path === path || (path !== '/mobile' && route.path.startsWith(path));
</script>
