/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <nav class="bg-white shadow-sm sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo -->
        <div class="flex-shrink-0">
          <NuxtLink
            to="/"
            class="flex items-center gap-2"
          >
            <img
              src="/images/logo.svg"
              :alt="$t('common.companyName')"
              class="h-8 w-auto"
            >
            <span class="text-xl font-bold text-gray-900 hidden sm:inline">
              {{ $t('common.companyName') }}
            </span>
          </NuxtLink>
        </div>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex md:items-center md:space-x-1">
          <NuxtLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="isActive(item.path) ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'"
          >
            {{ item.label }}
          </NuxtLink>
        </div>

        <!-- Desktop Actions -->
        <div class="hidden md:flex md:items-center md:gap-3">
          <button
            class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
            @click="toggleSearch"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>
          <NuxtLink
            to="/contact"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {{ $t('nav.contact') }}
          </NuxtLink>
        </div>

        <!-- Mobile menu button -->
        <div class="md:hidden">
          <button
            class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
            :class="{ 'bg-gray-100': isMobileMenuOpen }"
            @click="toggleMobileMenu"
          >
            <svg
              v-if="!isMobileMenuOpen"
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            <svg
              v-else
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-show="isMobileMenuOpen"
        class="md:hidden border-t border-gray-100 bg-white"
      >
        <div class="px-4 py-3 space-y-1">
          <NuxtLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="block px-3 py-3 rounded-lg text-base font-medium transition-colors min-h-[44px] flex items-center"
            :class="isActive(item.path) ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-100'"
            @click="closeMobileMenu"
          >
            {{ item.label }}
          </NuxtLink>
        </div>
        <div class="px-4 py-3 border-t border-gray-100 space-y-2">
          <button
            class="w-full px-3 py-3 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-100 transition-colors min-h-[44px] flex items-center gap-2"
            @click="toggleSearch"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            {{ $t('nav.search') }}
          </button>
          <NuxtLink
            to="/contact"
            class="block w-full px-3 py-3 bg-blue-600 text-white text-base font-medium rounded-lg hover:bg-blue-700 transition-colors text-center min-h-[44px] flex items-center justify-center"
            @click="closeMobileMenu"
          >
            {{ $t('nav.contact') }}
          </NuxtLink>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const navItems = computed(() => [
  { path: '/', label: t('nav.home') },
  { path: '/products', label: t('nav.products') },
  { path: '/cases', label: t('nav.cases') },
  { path: '/about', label: t('nav.about') },
  { path: '/news', label: t('nav.news') }
])

const route = useRoute()
const isMobileMenuOpen = ref(false)

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const emit = defineEmits<{ (e: 'toggle-search'): void }>()

const toggleSearch = () => {
  emit('toggle-search')
}

// Close mobile menu when route changes
watch(() => route.path, () => {
  closeMobileMenu()
})
</script>
