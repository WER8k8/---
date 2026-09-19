/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    class="relative"
    ref="dropdownRef"
  >
    <button
      type="button"
      class="flex items-center space-x-1 px-2 sm:px-3 py-2 text-text-secondary hover:text-primary hover:bg-surface-hover rounded-lg transition-all duration-200 text-sm font-medium min-w-[44px] min-h-[44px] justify-center"
      @click="toggleOpen"
      @keydown.escape="isOpen = false"
      :aria-label="$t('common.language')"
    >
      <span class="text-base leading-none">{{ currentLocaleFlag }}</span>
      <span class="hidden md:inline text-xs">{{ currentLocaleName }}</span>
      <svg
        class="w-3 h-3 text-text-muted transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
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
    </button>

    <transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-1 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-1 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 top-full mt-1 w-48 sm:w-56 rounded-xl border border-border bg-white shadow-lg py-1 z-50 max-h-80 overflow-y-auto"
      >
        <button
          v-for="locale in locales"
          :key="locale.code"
          type="button"
          class="flex items-center w-full px-4 py-2.5 text-sm text-left transition-colors duration-150"
          :class="locale.code === currentLocale
            ? 'text-primary font-medium bg-primary/5'
            : 'text-text-secondary hover:bg-surface-hover hover:text-primary'"
          @click="switchLanguage(locale.code)"
        >
          <span class="text-base mr-2">{{ localeFlag(locale.code) }}</span>
          <span>{{ locale.name }}</span>
          <span
            v-if="locale.code === currentLocale"
            class="ml-auto"
          >
            <svg
              class="w-4 h-4 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </span>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

const { locale, locales, setLocale } = useI18n();
const switchLocalePath = useSwitchLocalePath();

const isOpen = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

const currentLocale = computed(() => typeof locale.value === 'string' ? locale.value : 'zh');

const currentLocaleName = computed(() => {
  const found = (locales.value as Array<{ code: string; name: string }>).find(
    (l) => l.code === currentLocale.value
  );
  return found?.name ?? currentLocale.value;
});

const currentLocaleFlag = computed(() => localeFlag(currentLocale.value));

function localeFlag(code: string): string {
  const flags: Record<string, string> = {
    zh: '🇨🇳',
    en: '🇺🇸',
    de: '🇩🇪',
    fr: '🇫🇷',
    es: '🇪🇸',
    ar: '🇸🇦',
    ja: '🇯🇵',
    ko: '🇰🇷',
    ru: '🇷🇺',
    pt: '🇵🇹',
    th: '🇹🇭',
    vi: '🇻🇳',
  };
  return flags[code] || '🌐';
}

function toggleOpen() {
  isOpen.value = !isOpen.value;
}

async function switchLanguage(code: string) {
  if (code === currentLocale.value) {
    isOpen.value = false;
    return;
  }
  isOpen.value = false;
  try {
    await setLocale(code);
    const target = switchLocalePath(code);
    if (target) {
      await navigateTo(target, { replace: true });
    }
  } catch {
    try {
      await setLocale(code);
    } catch {
      /* locale cookie may still update on partial success */
    }
  }
}

function handleClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>
