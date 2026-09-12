<template>
  <a-config-provider :locale="zhCN" :theme="antTheme">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <router-view />
    <CookieConsent />
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { theme as antThemeAlgorithm } from 'ant-design-vue';
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import { storeToRefs } from 'pinia';

import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { useRumBeacon } from '@/composables/useRumBeacon';
import CookieConsent from '@/components/common/CookieConsent.vue';

dayjs.locale('zh-cn');

const ui = useUiPreferencesStore();
useRumBeacon();
const { theme, primaryColor, antBorderRadius, accentRole } = storeToRefs(ui);

const antTheme = computed(() => {
  const accentColors: Record<string, string> = {
    platform: primaryColor.value,
    client: '#4a9b8c',
    agent: '#0d9488',
  };
  const isDark = theme.value === 'dark';
  const accent = accentColors[accentRole.value] ?? primaryColor.value;
  const darkPrimary =
    accentRole.value === 'client' ? '#6ba3e8' : accentRole.value === 'agent' ? '#5cc4b0' : '#58c4ae';

  const darkTokens = isDark
    ? {
        colorBgBase: '#2a3038',
        colorBgLayout: '#2a3038',
        colorBgContainer: '#3d4550',
        colorBgElevated: '#454d58',
        colorBorder: 'rgba(255, 255, 255, 0.16)',
        colorBorderSecondary: 'rgba(255, 255, 255, 0.12)',
        colorText: '#eef2f6',
        colorTextSecondary: '#a8b0bb',
        colorTextTertiary: '#8a939f',
        colorFillSecondary: 'rgba(255, 255, 255, 0.09)',
        colorFillTertiary: 'rgba(255, 255, 255, 0.05)',
        controlItemBgHover: 'rgba(255, 255, 255, 0.09)',
        colorPrimary: darkPrimary,
        colorLink: darkPrimary,
        colorPrimaryHover: accentRole.value === 'client' ? '#93c5fd' : '#7ecfb8',
      }
    : {};

  return {
    algorithm: isDark ? antThemeAlgorithm.darkAlgorithm : antThemeAlgorithm.defaultAlgorithm,
    token: {
      colorPrimary: isDark ? darkPrimary : accent,
      borderRadius: antBorderRadius.value,
      fontFamily: 'var(--uj-font-sans)',
      fontSize: 15,
      fontSizeSM: 13,
      fontSizeLG: 17,
      fontSizeXL: 20,
      fontSizeHeading1: 34,
      fontSizeHeading2: 28,
      fontSizeHeading3: 22,
      fontSizeHeading4: 18,
      fontSizeHeading5: 15,
      ...darkTokens,
    },
  };
});

onMounted(() => ui.applyDom());
</script>
