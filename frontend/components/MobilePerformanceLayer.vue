<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
  enablePullRefresh?: boolean;
  enableInfiniteScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  enablePullRefresh: true,
  enableInfiniteScroll: true,
});

const emit = defineEmits<{
  refresh: [];
  loadMore: [];
}>();

const containerRef = ref<HTMLElement>();
const isRefreshing = ref(false);
const startY = ref(0);

function handleTouchStart(e: TouchEvent) {
  startY.value = e.touches[0].clientY;
}

function handleTouchEnd(e: TouchEvent) {
  if (!props.enablePullRefresh || isRefreshing.value) return;

  const endY = e.changedTouches[0].clientY;
  const diff = endY - startY.value;

  if (diff > 60) {
    isRefreshing.value = true;
    emit('refresh');

    setTimeout(() => {
      isRefreshing.value = false;
    }, 1500);
  }
}

function handleScroll() {
  if (!props.enableInfiniteScroll || !containerRef.value) return;

  const { scrollTop, clientHeight, scrollHeight } = containerRef.value;
  if (scrollTop + clientHeight >= scrollHeight - 100) {
    emit('loadMore');
  }
}

onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll, { passive: true });
  }
});

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll);
  }
});
</script>

<template>
  <div class="relative w-full h-full overflow-hidden">
    <div
      v-if="isRefreshing && enablePullRefresh"
      class="absolute top-0 left-0 right-0 z-10 flex justify-center items-center h-12 bg-blue-50 text-blue-600 text-sm"
    >
      <svg
        class="animate-spin w-5 h-5 mr-2"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="2"
          class="opacity-25"
        />
        <path
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {{ t('common.refreshing') }}
    </div>

    <div
      ref="containerRef"
      class="w-full h-full overflow-y-auto"
      :class="enablePullRefresh ? 'touch-pan-y' : ''"
      @touchstart="enablePullRefresh ? handleTouchStart : undefined"
      @touchend="enablePullRefresh ? handleTouchEnd : undefined"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.touch-pan-y {
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
}
</style>
