/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
  src: string;
  alt?: string;
  placeholder?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  alt: '',
  placeholder: '',
});

const isLoaded = ref(false);
const hasError = ref(false);
const imgRef = ref<HTMLImageElement>();
const observer = ref<IntersectionObserver>();

onMounted(() => {
  if (import.meta.client) {
    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            loadImage();
            observer.value?.disconnect();
          }
        });
      },
      { rootMargin: '50px' }
    );

    if (imgRef.value) {
      observer.value.observe(imgRef.value);
    }
  }
});

onUnmounted(() => {
  observer.value?.disconnect();
});

function loadImage() {
  if (!props.src || isLoaded.value) return;

  const img = new Image();
  img.onload = () => {
    isLoaded.value = true;
  };
  img.onerror = () => {
    hasError.value = true;
  };
  img.src = props.src;
}
</script>

<template>
  <div
    ref="imgRef"
    :class="[props.class, 'relative overflow-hidden bg-gray-100 rounded-lg']"
    :style="{ minHeight: '100px' }"
  >
    <div
      v-if="!isLoaded && !hasError"
      class="absolute inset-0 flex items-center justify-center"
    >
      <svg
        class="w-8 h-8 text-gray-400 animate-pulse"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>

    <img
      v-show="isLoaded"
      :src="src"
      :alt="alt"
      class="w-full h-auto transition-opacity duration-300"
      :class="hasError ? 'hidden' : ''"
    >

    <div
      v-if="hasError"
      class="absolute inset-0 flex flex-col items-center justify-center text-gray-400"
    >
      <svg
        class="w-12 h-12 mb-2"
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
      <span class="text-sm">{{ placeholder || t('common.imageLoadError') }}</span>
    </div>
  </div>
</template>
