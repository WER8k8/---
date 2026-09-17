/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface Props {
  items: any[];
  itemHeight?: number;
  containerHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  itemHeight: 50,
  containerHeight: '400px',
});

const containerRef = ref<HTMLElement>();
const scrollTop = ref(0);
const visibleStart = ref(0);

const visibleCount = computed(() => {
  if (!containerRef.value) return 10;
  const containerHeight = containerRef.value.getBoundingClientRect().height;
  return Math.ceil(containerHeight / props.itemHeight) + 2;
});

const visibleEnd = computed(() => {
  return Math.min(visibleStart.value + visibleCount.value, props.items.length);
});

const visibleItems = computed(() => {
  return props.items.slice(visibleStart.value, visibleEnd.value);
});

const offsetTop = computed(() => {
  return visibleStart.value * props.itemHeight;
});

function handleScroll() {
  if (!containerRef.value) return;
  scrollTop.value = containerRef.value.scrollTop;
  visibleStart.value = Math.floor(scrollTop.value / props.itemHeight);
}

onMounted(() => {
  handleScroll();
});
</script>

<template>
  <div
    ref="containerRef"
    :style="{ height: containerHeight, overflow: 'auto' }"
    class="virtual-scroll-container"
    @scroll="handleScroll"
  >
    <div
      class="relative"
      :style="{ height: items.length * itemHeight + 'px' }"
    >
      <div
        class="absolute top-0 left-0 right-0"
        :style="{ transform: `translateY(${offsetTop}px)` }"
      >
        <slot
          v-for="(item, index) in visibleItems"
          :key="visibleStart + index"
          :item="item"
          :index="visibleStart + index"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.virtual-scroll-container {
  position: relative;
  overflow-y: auto;
}
</style>
