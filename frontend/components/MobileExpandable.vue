/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
  maxHeight?: string;
  collapsedHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  maxHeight: '200px',
  collapsedHeight: '100px',
});

const isExpanded = ref(false);

function toggle() {
  isExpanded.value = !isExpanded.value;
}
</script>

<template>
  <div
    class="relative overflow-hidden"
    :class="{ expanded: isExpanded }"
  >
    <div
      class="transition-all duration-300 ease-in-out"
      :style="{
        maxHeight: isExpanded ? maxHeight : collapsedHeight,
      }"
    >
      <slot />
    </div>
    <div
      v-if="!isExpanded"
      class="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white to-transparent"
    />
    <button
      class="relative z-10 w-full py-2 text-center text-sm text-blue-600 font-medium hover:text-blue-700 transition-colors"
      @click="toggle"
    >
      {{ isExpanded ? t('common.close') : t('common.expandMore') }}
    </button>
  </div>
</template>
