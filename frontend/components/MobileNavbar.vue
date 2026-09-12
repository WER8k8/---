<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface Props {
  safeAreaTop?: boolean;
  safeAreaBottom?: boolean;
  blur?: boolean;
  transparent?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  safeAreaTop: true,
  safeAreaBottom: true,
  blur: true,
  transparent: false,
});

const scrollY = ref(0);
const isVisible = ref(true);
const lastScrollY = ref(0);

function handleScroll() {
  const currentScrollY = window.scrollY;
  isVisible.value = currentScrollY < lastScrollY.value || currentScrollY < 100;
  lastScrollY.value = currentScrollY;
  scrollY.value = currentScrollY;
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true });
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 transition-transform duration-300"
    :class="[
      isVisible ? 'translate-y-0' : '-translate-y-full',
      transparent ? 'bg-transparent' : 'bg-white/95 backdrop-blur-md',
      safeAreaTop ? 'pt-safe-top' : '',
      safeAreaBottom ? 'pb-safe-bottom' : '',
      'border-b border-gray-100 shadow-sm',
    ]"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <slot />
    </div>
  </header>
</template>
