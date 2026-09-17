/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-stats-row" :style="{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ cols?: number }>(), { cols: 4 });
</script>

<style scoped>
.yd-stats-row {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 1024px) {
  .yd-stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}
@media (max-width: 640px) {
  .yd-stats-row {
    grid-template-columns: 1fr !important;
  }
}
</style>
