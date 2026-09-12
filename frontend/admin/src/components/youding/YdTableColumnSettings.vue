<template>
  <a-popover trigger="click" placement="bottomRight" overlay-class-name="yd-col-settings-pop">
    <template #content>
      <div class="yd-col-settings">
        <div class="yd-col-settings__head">
          <span>列显示与顺序</span>
          <a-button type="link" size="small" @click="$emit('reset')">恢复默认</a-button>
        </div>
        <ul class="yd-col-settings__list">
          <li v-for="col in columns" :key="col.key" class="yd-col-settings__row">
            <a-checkbox
              :checked="!hiddenKeys.includes(col.key)"
              @change="() => $emit('toggle', col.key)"
            >
              {{ col.title }}
            </a-checkbox>
            <span class="yd-col-settings__move">
              <a-button type="text" size="small" aria-label="上移" @click="$emit('move-up', col.key)">↑</a-button>
              <a-button type="text" size="small" aria-label="下移" @click="$emit('move-down', col.key)">↓</a-button>
            </span>
          </li>
        </ul>
      </div>
    </template>
    <a-button>列设置</a-button>
  </a-popover>
</template>

<script setup lang="ts">
import type { YoudingTableColumn } from '@/composables/useYoudingTableBridge';

defineProps<{
  columns: YoudingTableColumn[];
  hiddenKeys: string[];
}>();

defineEmits<{
  toggle: [key: string];
  'move-up': [key: string];
  'move-down': [key: string];
  reset: [];
}>();
</script>

<style scoped>
.yd-col-settings {
  min-width: 220px;
  max-width: 280px;
}
.yd-col-settings__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
.yd-col-settings__list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 280px;
  overflow-y: auto;
}
.yd-col-settings__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f1f5f9;
}
.yd-col-settings__row:last-child {
  border-bottom: none;
}
.yd-col-settings__move {
  display: flex;
  flex-shrink: 0;
}
</style>
