<template>
  <div class="yd-table-toolbar">
    <slot />
    <a-segmented
      v-if="showDensity"
      v-model:value="densityModel"
      size="small"
      :options="densityOptions"
      @change="onDensityChange"
    />
    <a-button v-if="showRefresh" size="small" :loading="loading" @click="$emit('refresh')">刷新</a-button>
    <a-button v-if="showFullscreen" size="small" @click="toggleFullscreen">{{ fullscreen ? '退出全屏' : '全屏' }}</a-button>
    <a-button v-if="showExport" size="small" @click="$emit('export')">导出</a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

import { useUiPreferencesStore, type UiTableDensity } from '@/stores/uiPreferences';

const props = withDefaults(
  defineProps<{
    loading?: boolean;
    showDensity?: boolean;
    showRefresh?: boolean;
    showFullscreen?: boolean;
    showExport?: boolean;
    targetRef?: HTMLElement | null;
  }>(),
  {
    loading: false,
    showDensity: true,
    showRefresh: true,
    showFullscreen: true,
    showExport: false,
  },
);

defineEmits<{ refresh: []; export: [] }>();

const ui = useUiPreferencesStore();
const fullscreen = ref(false);

const densityOptions = [
  { label: '紧凑', value: 'compact' },
  { label: '默认', value: 'default' },
  { label: '宽松', value: 'comfortable' },
];

const densityModel = computed({
  get: () => ui.tableDensity,
  set: (v: UiTableDensity) => ui.setTableDensity(v),
});

function onDensityChange(v: string | number) {
  ui.setTableDensity(v as UiTableDensity);
}

function toggleFullscreen() {
  const el = props.targetRef ?? document.querySelector('.yd-table-panel');
  if (!el || !(el instanceof HTMLElement)) return;
  if (!document.fullscreenElement) {
    void el.requestFullscreen?.().then(() => {
      fullscreen.value = true;
    });
  } else {
    void document.exitFullscreen?.().then(() => {
      fullscreen.value = false;
    });
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('fullscreenchange', () => {
    fullscreen.value = !!document.fullscreenElement;
  });
}
</script>

<style scoped>
.yd-table-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
</style>
