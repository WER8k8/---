<template>
  <div class="yd-skeleton" :class="[variant, { animated }]">
    <!-- Card skeleton -->
    <template v-if="variant === 'card'">
      <div class="yd-skeleton-card">
        <div class="yd-skeleton-line w-1/3 h-4"></div>
        <div class="yd-skeleton-line w-full h-8 mt-3"></div>
        <div class="yd-skeleton-line w-2/3 h-3 mt-2"></div>
      </div>
    </template>

    <!-- KPI skeleton -->
    <template v-else-if="variant === 'kpi'">
      <div class="yd-skeleton-kpi">
        <div class="flex items-center justify-between">
          <div class="yd-skeleton-line w-20 h-3"></div>
          <div class="yd-skeleton-line w-8 h-8 rounded-lg"></div>
        </div>
        <div class="yd-skeleton-line w-24 h-8 mt-3"></div>
        <div class="yd-skeleton-line w-16 h-3 mt-2"></div>
        <div class="yd-skeleton-line w-full h-6 mt-3"></div>
      </div>
    </template>

    <!-- Table skeleton -->
    <template v-else-if="variant === 'table'">
      <div class="yd-skeleton-table">
        <div class="yd-skeleton-row" v-for="i in rows" :key="i">
          <div class="yd-skeleton-cell w-8"></div>
          <div class="yd-skeleton-cell flex-1"></div>
          <div class="yd-skeleton-cell w-20"></div>
          <div class="yd-skeleton-cell w-16"></div>
          <div class="yd-skeleton-cell w-12"></div>
        </div>
      </div>
    </template>

    <!-- Chart skeleton -->
    <template v-else-if="variant === 'chart'">
      <div class="yd-skeleton-chart">
        <div class="yd-skeleton-line w-32 h-4 mb-4"></div>
        <div class="yd-skeleton-bars">
          <div class="yd-skeleton-bar" v-for="i in 7" :key="i"
               :style="{ height: `${20 + Math.random() * 60}%` }"></div>
        </div>
      </div>
    </template>

    <!-- Text skeleton -->
    <template v-else>
      <div class="yd-skeleton-text">
        <div class="yd-skeleton-line w-full h-4"></div>
        <div class="yd-skeleton-line w-5/6 h-4 mt-2"></div>
        <div class="yd-skeleton-line w-4/6 h-4 mt-2"></div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'card' | 'kpi' | 'table' | 'chart' | 'text';
  rows?: number;
  animated?: boolean;
}>(), {
  variant: 'card',
  rows: 5,
  animated: true,
});
</script>

<style scoped>
.yd-skeleton {
  width: 100%;
}

.yd-skeleton-line {
  border-radius: 6px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
}

.yd-skeleton.animated .yd-skeleton-line,
.yd-skeleton.animated .yd-skeleton-cell,
.yd-skeleton.animated .yd-skeleton-bar {
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Card variant */
.yd-skeleton-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

/* KPI variant */
.yd-skeleton-kpi {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

/* Table variant */
.yd-skeleton-table {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.yd-skeleton-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.yd-skeleton-row:last-child {
  border-bottom: none;
}

.yd-skeleton-cell {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
}

/* Chart variant */
.yd-skeleton-chart {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

.yd-skeleton-bars {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 160px;
  padding-top: 16px;
}

.yd-skeleton-bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  min-height: 20px;
}

/* Text variant */
.yd-skeleton-text {
  padding: 8px 0;
}

/* Size utilities */
.w-1\/3 { width: 33.333%; }
.w-2\/3 { width: 66.666%; }
.w-4\/6 { width: 66.666%; }
.w-5\/6 { width: 83.333%; }
.w-full { width: 100%; }
.w-20 { width: 80px; }
.w-24 { width: 96px; }
.w-16 { width: 64px; }
.w-32 { width: 128px; }
.w-12 { width: 48px; }
.w-8 { width: 32px; }
.h-3 { height: 12px; }
.h-4 { height: 16px; }
.h-6 { height: 24px; }
.h-8 { height: 32px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mb-4 { margin-bottom: 16px; }
.rounded-lg { border-radius: 8px; }
</style>
