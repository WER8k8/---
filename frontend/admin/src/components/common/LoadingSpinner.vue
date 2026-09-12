<template>
  <!-- Skeleton mode: show SkeletonCard instead of spinner -->
  <div v-if="skeleton" class="loading-skeleton" :class="{ fullscreen }">
    <SkeletonCard :variant="skeletonVariant" :rows="skeletonRows" :animated="true" />
  </div>

  <!-- Spinner mode (default / fallback) -->
  <div v-else class="loading-spinner" :class="[size, { fullscreen }]">
    <a-spin :size="size" :tip="tip" :spinning="true">
      <template #indicator>
        <div class="custom-indicator">
          <LoadingOutlined :style="{ fontSize: iconSize }" />
        </div>
      </template>
    </a-spin>

    <div v-if="tip" class="loading-tip">{{ tip }}</div>

    <div v-if="showCancel" class="loading-cancel">
      <a-button type="link" size="small" @click="handleCancel">
        取消加载
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { LoadingOutlined } from '@ant-design/icons-vue';
import SkeletonCard from './SkeletonCard.vue';

const props = withDefaults(defineProps<{
  size?: 'small' | 'default' | 'large';
  tip?: string;
  fullscreen?: boolean;
  showCancel?: boolean;
  /** When true, show a skeleton placeholder instead of the spinner */
  skeleton?: boolean;
  /** Which skeleton variant to render (card, kpi, table, chart, text) */
  skeletonVariant?: 'card' | 'kpi' | 'table' | 'chart' | 'text';
  /** Number of skeleton rows (only used for table variant) */
  skeletonRows?: number;
}>(), {
  size: 'default',
  tip: '',
  fullscreen: false,
  showCancel: false,
  skeleton: false,
  skeletonVariant: 'card',
  skeletonRows: 5,
});

const emit = defineEmits<{
  (e: 'cancel'): void;
}>();

const iconSize = computed(() => {
  const sizeMap: Record<string, string> = {
    small: '16px',
    default: '24px',
    large: '32px',
  };
  return sizeMap[props.size] || '24px';
});

function handleCancel() {
  emit('cancel');
}
</script>

<style scoped>
.loading-skeleton {
  width: 100%;
}

.loading-skeleton.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.loading-spinner.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;
}

.loading-spinner.small {
  padding: 12px;
}

.loading-spinner.large {
  padding: 48px;
}

.custom-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

.custom-indicator :deep(.anticon) {
  animation: spin 1s linear infinite;
  color: var(--uj-brand, #4a9b8c);
}

.loading-tip {
  margin-top: 12px;
  font-size: 14px;
  color: #8c8c8c;
}

.loading-cancel {
  margin-top: 16px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>