<template>
  <div class="tenant-blank-root min-h-screen">
    <div v-if="booting" class="tenant-blank-boot" aria-live="polite">
      <p class="tenant-blank-boot__title">正在打开您的网站…</p>
      <p class="tenant-blank-boot__hint">若长时间空白，请确认 Nuxt :3000 与 API :8001 已启动</p>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

useHead({
  titleTemplate: '%s',
});

const booting = ref(false);

onMounted(() => {
  booting.value = false;
});
</script>

<style scoped>
.tenant-blank-boot {
  position: fixed;
  inset: 0;
  z-index: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #f4f6f9;
  color: #1a2332;
  pointer-events: none;
}

.tenant-blank-boot__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.tenant-blank-boot__hint {
  margin: 0;
  font-size: 0.875rem;
  color: #5c6b7f;
}

.tenant-blank-root :deep(.lpro-root) {
  position: relative;
  z-index: 1;
}
</style>
