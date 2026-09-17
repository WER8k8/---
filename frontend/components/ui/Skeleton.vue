/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';

interface Props {
  isLoading?: boolean;
  error?: Error | null;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: null,
});

const skeletonLines = ref(5);

const lines = computed(() => Array.from({ length: skeletonLines.value }));
</script>

<template>
  <div
    v-if="error"
    class="flex flex-col items-center justify-center py-12 px-4"
  >
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
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </div>
    <p class="text-sm text-gray-500">
      {{ error.message }}
    </p>
  </div>
  <div
    v-else-if="isLoading"
    class="space-y-3 py-4"
  >
    <div
      v-for="(_, i) in lines"
      :key="i"
      class="animate-pulse bg-gray-200 rounded"
      :class="{
        'h-4 w-full': i === 0,
        'h-3 w-4/5': i === lines.length - 1,
        'h-3 w-full': i !== 0 && i !== lines.length - 1,
      }"
    />
  </div>
  <template v-else>
    <slot />
  </template>
</template>
