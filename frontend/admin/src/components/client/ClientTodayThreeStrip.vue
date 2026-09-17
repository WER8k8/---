/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <section class="today-strip" :class="{ 'today-strip--done': allDone }" aria-label="今日三步摘要">
    <div class="today-strip__main">
      <div class="today-strip__head">
        <span class="today-strip__badge">外贸开店关键进展</span>
        <h2>{{ payload.headline || '建站上线 ➔ 首发推广 ➔ 捕获海外询盘' }}</h2>
      </div>
      <div
        class="today-strip__progress"
        role="progressbar"
        :aria-valuenow="progressPct"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div class="today-strip__track">
          <div class="today-strip__fill" :style="{ width: `${progressPct}%` }" />
        </div>
        <span>{{ payload.done_count ?? 0 }}/{{ payload.total_steps ?? 3 }} 完成</span>
      </div>
      <p v-if="nextStep && !allDone" class="today-strip__next">
        建议优先处理：<strong>{{ nextStep.title }}</strong> — {{ nextStep.hint }}
      </p>
      <p v-else-if="allDone" class="today-strip__next today-strip__next--ok">
        核心闭环已就绪，保持日常询盘跟进与多平台发品节奏。
      </p>

    </div>
    <div class="today-strip__actions">
      <a-button v-if="nextStep && !allDone" type="primary" @click="go(nextStep.route)">
        {{ nextStep.cta }}
      </a-button>
      <a-button type="link" @click="go('/client/today')">完整视图 →</a-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useClientTodayThree } from '@/composables/useClientTodayThree';

const router = useRouter();
const { payload, nextStep, allDone, progressPct, load } = useClientTodayThree();

function go(path: string) {
  void router.push(path);
}

onMounted(() => {
  void load();
});
</script>

<style scoped lang="scss">
.today-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 16px 18px;
  border-radius: var(--uj-radius-lg, 16px);
  border: 1px solid #e2e8f0;
  background: rgb(255 255 255 / 0.98);
  color: #374151;
  box-shadow: 0 2px 8px rgb(106 126 140 / 0.08);
}

.today-strip--done {
  border-left: 3px solid #2563eb;
}

.today-strip__badge {
  display: inline-block;
  margin-bottom: 6px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #1e40af;
  background: #eff6ff;
}

.today-strip h2 {
  margin: 0;
  font-family: var(--uj-font-display);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.today-strip__progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  font-size: 12px;
  opacity: 0.92;
}

.today-strip__track {
  flex: 1;
  max-width: 200px;
  height: 5px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.today-strip__fill {
  height: 100%;
  border-radius: 999px;
  background: #2563eb;
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.today-strip__next {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.45;
  color: #64748b;
}

.today-strip__next strong {
  color: #1f2937;
}

.today-strip__next--ok {
  color: #15803d;
}

.today-strip__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.today-strip__actions :deep(.ant-btn-primary) {
  font-weight: 600;
  border-radius: 8px !important;
  background: #2563eb !important;
  border-color: #2563eb !important;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2);
}

.today-strip__actions :deep(.ant-btn-primary:hover) {
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

.today-strip__actions :deep(.ant-btn-link) {
  color: #2563eb !important;
  padding-right: 0;
}

@media (max-width: 640px) {
  .today-strip__actions {
    width: 100%;
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
  }
}
</style>
