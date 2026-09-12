<template>
  <section class="yd-today-workbench panel uj-glass-panel">
    <header class="yd-today-workbench__head">
      <div class="yd-today-workbench__intro">
        <p class="yd-today-workbench__kicker">登录 30 秒就知道该干什么</p>
        <h2 class="yd-today-workbench__title">今日工作台</h2>
        <p v-if="headline" class="yd-today-workbench__headline">{{ headline }}</p>
      </div>
      <div class="yd-today-workbench__plan">
        <a-tag :color="planTagColor">{{ planName }}</a-tag>
        <span v-if="planExpiryLabel" class="yd-today-workbench__expiry">{{ planExpiryLabel }}</span>
        <a-button size="small" type="link" @click="emit('navigate', '/client/billing')">套餐与用量</a-button>
      </div>
    </header>

    <div class="yd-today-workbench__usage">
      <YdUsageMeter
        class="yd-today-workbench__meter"
        label="AI 额度（本月）"
        :used="aiUsed"
        :max="aiMax"
        :hint="usageHint"
      />
      <YdUsageMeter
        v-if="publishUsed > 0"
        class="yd-today-workbench__meter"
        label="发布任务（进行中）"
        :used="publishUsed"
        :max="Math.max(publishUsed, 1)"
        hint="点击「待发品」查看队列"
      />
    </div>

    <div class="yd-today-workbench__tiles">
      <button
        v-for="tile in tiles"
        :key="tile.id"
        type="button"
        class="yd-today-workbench__tile"
        :class="`yd-today-workbench__tile--${tile.tone}`"
        @click="emit('navigate', tile.route)"
      >
        <span class="yd-today-workbench__tile-value">{{ tile.value }}</span>
        <span class="yd-today-workbench__tile-label">{{ tile.label }}</span>
        <span v-if="tile.hint" class="yd-today-workbench__tile-hint">{{ tile.hint }}</span>
      </button>
    </div>

    <YdTodayQueue
      class="yd-today-workbench__queue"
      title="今日待办"
      :items="todayItems"
      empty-text="今日暂无待办 — 点下方开始今日三步"
      empty-action-route="/client/today"
      @navigate="emit('navigate', $event)"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import YdTodayQueue from './YdTodayQueue.vue';
import YdUsageMeter from './YdUsageMeter.vue';
import type { QueueItem } from './types';

export type WorkbenchTile = {
  id: string;
  label: string;
  value: string | number;
  hint?: string;
  route: string;
  tone?: 'default' | 'urgent' | 'ok';
};

const props = withDefaults(
  defineProps<{
    planName: string;
    planExpiry?: string;
    headline?: string;
    aiUsed: number;
    aiMax: number;
    publishUsed?: number;
    tiles: WorkbenchTile[];
    todayItems: QueueItem[];
  }>(),
  {
    planExpiry: '',
    headline: '',
    publishUsed: 0,
  },
);

const emit = defineEmits<{
  navigate: [path: string];
}>();

const planTagColor = computed(() => {
  const n = props.planName || '';
  if (n.includes('企业')) return 'purple';
  if (n.includes('专业') || n.includes('Pro')) return 'blue';
  if (n.includes('体验') || n.includes('试用')) return 'default';
  return 'processing';
});

const planExpiryLabel = computed(() => {
  if (!props.planExpiry || props.planExpiry === '—') return '';
  const d = props.planExpiry.slice(0, 10);
  return props.planName.includes('体验') ? `体验至 ${d}` : `到期 ${d}`;
});

const usageHint = computed(() => {
  const pct = props.aiMax ? Math.round((props.aiUsed / props.aiMax) * 100) : 0;
  if (pct >= 100) return '额度已满，升级专业版继续发布';
  if (pct >= 80) return '本月发布额度已用 80%';
  return '续费与升级在套餐页';
});
</script>

<style scoped lang="scss">
.yd-today-workbench {
  padding: var(--uj-space-card, 16px);
  margin-bottom: 16px;

  &__head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 12px 16px;
    margin-bottom: 16px;
  }

  &__kicker {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    color: var(--uj-brand, #4a9b8c);
  }

  &__title {
    margin: 4px 0 0;
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
  }

  &__headline {
    margin: 6px 0 0;
    font-size: 13px;
    color: #475569;
    line-height: 1.5;
    max-width: 36rem;
  }

  &__plan {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  &__expiry {
    font-size: 12px;
    color: #64748b;
  }

  &__usage {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 16px;
  }

  &__tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }

  &__tile {
    text-align: left;
    padding: 14px 16px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background: #fff;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;

    &:hover {
      border-color: var(--uj-brand, #4a9b8c);
      box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
    }

    &--urgent {
      border-color: #fecaca;
      background: #fffbfb;
    }

    &--ok {
      border-color: #bbf7d0;
      background: #f0fdf4;
    }
  }

  &__tile-value {
    display: block;
    font-size: 28px;
    font-weight: 800;
    color: #1e3a5f;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }

  &__tile--urgent &__tile-value {
    color: #dc2626;
  }

  &__tile--ok &__tile-value {
    color: #059669;
    font-size: 15px;
    font-weight: 700;
  }

  &__tile-label {
    display: block;
    margin-top: 4px;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
  }

  &__tile-hint {
    display: block;
    margin-top: 4px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.4;
  }

  &__queue {
    padding: 0;
    background: transparent;
    border: none;
    box-shadow: none;
  }
}

@media (max-width: 960px) {
  .yd-today-workbench__usage,
  .yd-today-workbench__tiles {
    grid-template-columns: 1fr;
  }
}
</style>
