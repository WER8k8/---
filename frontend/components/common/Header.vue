/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-out"
    :class="[
      isScrolled ? 'bg-white/95 backdrop-blur-md shadow-sm' : 'bg-transparent',
      isHidden ? '-translate-y-full opacity-0' : 'translate-y-0 opacity-100',
      isMobileMenuOpen
        ? 'fixed inset-0 h-auto min-h-screen bg-white/95 backdrop-blur-lg'
        : 'h-auto',
    ]"
  >
    <nav class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6">
      <div class="flex justify-between h-14 sm:h-16 lg:h-20 items-center">
        <NuxtLink
          to="/"
          class="flex items-center space-x-2 sm:space-x-3 group"
          @click="isMobileMenuOpen = false"
        >
          <div
            class="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-105"
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
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <span class="text-lg sm:text-xl lg:text-2xl font-bold text-text-primary">{{ $t('common.companyNameShort') }}</span>
        </NuxtLink>

        <div class="hidden lg:flex items-center space-x-1">
          <div
            v-for="item in mainNav"
            :key="navKey(item)"
            class="relative"
            :class="item.children?.length ? 'group' : ''"
          >
            <template v-if="item.children?.length">
              <NuxtLink
                :to="item.to"
                class="relative px-3 sm:px-4 py-2 text-text-secondary font-medium rounded-lg transition-all duration-200 cursor-pointer inline-flex items-center gap-1"
                :class="
                  isNavGroupActive(item)
                    ? 'text-primary bg-primary/5'
                    : 'hover:text-primary hover:bg-surface-hover'
                "
              >
                {{ item.label }}
                <svg
                  class="w-4 h-4 text-text-muted group-hover:text-primary transition-transform group-hover:rotate-180"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
                <span
                  v-if="isNavGroupActive(item)"
                  class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-primary rounded-full"
                />
              </NuxtLink>
              <div
                class="absolute left-0 top-full pt-2 w-56 opacity-0 invisible pointer-events-none group-hover:opacity-100 group-hover:visible group-hover:pointer-events-auto transition-all duration-200 z-50"
              >
                <div
                  class="rounded-xl border border-border bg-white/95 backdrop-blur-md shadow-lg py-2"
                >
                  <NuxtLink
                    v-for="child in item.children"
                    :key="child.to"
                    :to="child.to"
                    class="block px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-hover hover:text-primary transition-colors"
                    :class="isActive(child.to) ? 'text-primary font-medium bg-primary/5' : ''"
                  >
                    <span class="block">{{ child.label }}</span>
                    <span
                      v-if="child.description"
                      class="block text-xs text-text-muted font-normal mt-0.5"
                    >{{ child.description }}</span>
                  </NuxtLink>
                </div>
              </div>
            </template>
            <NuxtLink
              v-else
              :to="item.to"
              class="relative px-3 sm:px-4 py-2 text-text-secondary font-medium rounded-lg transition-all duration-200 cursor-pointer"
              :class="
                isActive(item.to)
                  ? 'text-primary bg-primary/5'
                  : 'hover:text-primary hover:bg-surface-hover'
              "
            >
              {{ item.label }}
              <span
                v-if="isActive(item.to)"
                class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-primary rounded-full"
              />
            </NuxtLink>
          </div>
        </div>

        <div class="flex items-center space-x-1 sm:space-x-2">
          <LanguageSwitcher />

          <a
            :href="'tel:' + phone"
            class="hidden lg:flex items-center gap-1.5 text-primary font-semibold text-sm ml-2"
          >
            <svg
              class="w-4 h-4"
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
            {{ phone }}
          </a>

          <button
            class="lg:hidden p-2 sm:p-3 text-text-secondary hover:text-primary hover:bg-surface-hover rounded-lg transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center"
            @click="toggleMobileMenu"
            @touchstart="handleTouchStart"
            @touchend="handleTouchEnd"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                v-if="!isMobileMenuOpen"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M4 6h16M4 12h16M4 18h16"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <div
        v-if="isMobileMenuOpen"
        class="lg:hidden pb-8 animate-slide-up"
      >
        <div class="flex flex-col space-y-2 px-2 pt-4 border-t border-border">
          <div
            v-for="item in mainNav"
            :key="navKey(item)"
            class="relative"
          >
            <template v-if="item.children?.length">
              <button
                type="button"
                class="flex w-full items-center px-4 py-3 text-text-secondary font-medium rounded-xl transition-all duration-200 min-h-[52px] text-left"
                :class="
                  isNavGroupActive(item)
                    ? 'text-primary bg-primary/5'
                    : 'hover:text-primary hover:bg-surface-hover'
                "
                @click="toggleMobileGroup(item.label)"
                @touchstart="handleTouchStart"
                @touchend="handleTouchEnd"
              >
                <span class="flex-1">{{ item.label }}</span>
                <svg
                  class="w-5 h-5 text-text-muted transition-transform"
                  :class="{ 'rotate-90': mobileOpenGroup === item.label || childActive(item) }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
              <div
                v-show="mobileOpenGroup === item.label || childActive(item)"
                class="ml-3 pl-3 border-l border-border space-y-1 mb-1"
              >
                <NuxtLink
                  v-for="child in item.children"
                  :key="child.to"
                  :to="child.to"
                  class="flex items-center px-4 py-2.5 text-sm text-text-secondary rounded-lg min-h-[44px]"
                  :class="
                    isActive(child.to)
                      ? 'text-primary bg-primary/5 font-medium'
                      : 'hover:bg-surface-hover'
                  "
                  @click="isMobileMenuOpen = false"
                >
                  {{ child.label }}
                </NuxtLink>
              </div>
            </template>
            <NuxtLink
              v-else
              :to="item.to"
              class="flex items-center px-4 py-3 text-text-secondary font-medium rounded-xl transition-all duration-200 cursor-pointer min-h-[52px]"
              :class="
                isActive(item.to)
                  ? 'text-primary bg-primary/5'
                  : 'hover:text-primary hover:bg-surface-hover'
              "
              @click="isMobileMenuOpen = false"
              @touchstart="handleTouchStart"
              @touchend="handleTouchEnd"
            >
              <span class="flex-1 text-left">{{ item.label }}</span>
              <svg
                class="w-5 h-5 text-text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </NuxtLink>
            <span
              v-if="isNavGroupActive(item) && !item.children?.length"
              class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-lg"
            />
            <span
              v-else-if="isNavGroupActive(item) && item.children?.length"
              class="absolute left-0 top-6 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-lg"
            />
          </div>
          <div class="mt-4 pt-4 border-t border-border">
            <a
              :href="'tel:' + phone"
              class="flex items-center justify-center px-4 py-4 bg-gradient-to-r from-primary to-primary-dark text-white font-semibold rounded-xl active:opacity-90 min-h-[52px]"
              @click="isMobileMenuOpen = false"
              @touchstart="handleTouchStart"
              @touchend="handleTouchEnd"
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
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                />
              </svg>
              {{ phone }}
            </a>
          </div>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { siteMainNavigation, navKey, type SiteNavItem } from '~/config/site-navigation';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();
const route = useRoute();
const phone = SITE_CONFIG.phone;
const isScrolled = ref(false);
const isHidden = ref(false);
const isMobileMenuOpen = ref(false);
const lastScrollTop = ref(0);
const scrollThreshold = 100;
const mobileOpenGroup = ref<string | null>(null);

/** Compute translated navigation */
function translateItem(item: SiteNavItem): SiteNavItem & { label: string } {
  return {
    ...item,
    label: t(item.label),
    children: item.children?.map((child) => ({
      ...child,
      label: t(child.label),
      description: child.description ? t(child.description) : undefined,
    })),
  };
}

const mainNav = computed(() => siteMainNavigation.map(translateItem));

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/';
  return route.path.startsWith(path);
}

function isNavGroupActive(item: SiteNavItem): boolean {
  if (isActive(item.to)) return true;
  return item.children?.some((c) => isActive(c.to)) ?? false;
}

function childActive(item: SiteNavItem): boolean {
  return item.children?.some((c) => isActive(c.to)) ?? false;
}

function toggleMobileGroup(label: string) {
  mobileOpenGroup.value = mobileOpenGroup.value === label ? null : label;
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
}

function handleScroll() {
  const currentScrollTop = window.scrollY;

  if (currentScrollTop > scrollThreshold) {
    isScrolled.value = true;

    if (currentScrollTop > lastScrollTop.value) {
      isHidden.value = true;
    } else {
      isHidden.value = false;
    }
  } else {
    isScrolled.value = false;
    isHidden.value = false;
  }

  lastScrollTop.value = currentScrollTop <= 0 ? 0 : currentScrollTop;
}

function handleTouchStart(e: TouchEvent) {
  const target = e.currentTarget as HTMLElement;
  if (target) target.style.transform = 'scale(0.98)';
}

function handleTouchEnd(e: TouchEvent) {
  const target = e.currentTarget as HTMLElement;
  if (target) target.style.transform = 'scale(1)';
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true });
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});

watch(
  () => route.path,
  () => {
    isMobileMenuOpen.value = false;
    mobileOpenGroup.value = null;
  }
);
</script>
