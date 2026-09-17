/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, onErrorCaptured, type ComponentPublicInstance, type VNode } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
  fallback?: VNode | (() => VNode);
}

const props = withDefaults(defineProps<Props>(), {
  fallback: () => null,
});

const error = ref<Error | null>(null);
const errorInfo = ref<{ componentStack: string } | null>(null);

onErrorCaptured((err: Error, instance: ComponentPublicInstance | null, info: string) => {
  error.value = err;
  errorInfo.value = { componentStack: info };
  console.error('Error Boundary:', err, info);
  return false;
});

function resetError() {
  error.value = null;
  errorInfo.value = null;
}
</script>

<template>
  <template v-if="error">
    <div
      v-if="fallback"
      class="error-fallback"
    >
      <slot
        name="fallback"
        :error="error"
        :error-info="errorInfo"
        @reset="resetError"
      >
        <div class="flex flex-col items-center justify-center py-12 px-4">
          <div class="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <svg
              class="w-8 h-8 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">
            {{ t('common.componentError') }}
          </h3>
          <p class="text-sm text-gray-500 mb-4">
            {{ error.message }}
          </p>
          <button
            @click="resetError"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            {{ t('common.retry') }}
          </button>
        </div>
      </slot>
    </div>
  </template>
  <template v-else>
    <slot />
  </template>
</template>
