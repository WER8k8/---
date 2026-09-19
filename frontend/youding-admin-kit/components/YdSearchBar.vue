<template>
  <div class="yd-search-bar">
    <div class="yd-search-bar__fields">
      <slot />
    </div>
    <div class="yd-search-bar__actions">
      <a-button
        type="primary"
        @click="$emit('search')"
      >
        查询
      </a-button>
      <a-button @click="$emit('reset')">
        重置
      </a-button>
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ search: []; reset: [] }>()
</script>

<style scoped>
.yd-search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--uj-bg-card, #fff);
  border: 1px solid var(--uj-border, #e5e7eb);
  border-radius: var(--uj-radius-md, 12px);
}
.yd-search-bar__fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  flex: 1;
}
.yd-search-bar__actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
