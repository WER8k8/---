/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100"
  >
    <div class="text-center px-4">
      <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
        <svg
          class="w-12 h-12 text-red-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        {{ t('error.pageError') }}
      </h1>
      <p class="text-gray-600 mb-6">
        {{
          typeof error === 'string' ? error : (error as any)?.message || t('error.defaultMessage')
        }}
      </p>
      <div class="space-x-4">
        <button
          @click="goHome"
          class="px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
        >
          {{ t('error.backHome') }}
        </button>
        <button
          @click="reloadPage"
          class="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors"
        >
          {{ t('error.reload') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NuxtError } from '#app'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  error: NuxtError
}>()

function goHome() {
  clearError({ redirect: '/' })
}

function reloadPage() {
  window.location.reload()
}
</script>
