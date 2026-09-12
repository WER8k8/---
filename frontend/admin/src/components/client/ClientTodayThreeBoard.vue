<template>
  <div class="today-board client-dashboard tenant-theme coachpro-tertiary coachpro-tertiary--client">
    <header class="today-board__top">
      <div class="today-board__top-copy">
        <p class="today-board__kicker">{{ greeting }} · 外贸出海工作台</p>
        <h1 id="today-heading">今日三步</h1>
        <p class="today-board__sub">{{ payload.headline || '有货 → 有曝光 → 能接电话' }}</p>
      </div>
      <div class="today-board__progress" aria-label="完成进度">
        <div class="today-board__progress-meta">
          <span>已完成 {{ payload.done_count ?? 0 }} / {{ payload.total_steps ?? 3 }}</span>
          <span v-if="payload.region_label" class="today-board__region">{{ payload.region_label }}</span>
        </div>
        <div class="today-board__progress-track">
          <div class="today-board__progress-fill" :style="{ width: `${progressPct}%` }" />
        </div>
      </div>
    </header>

    <div class="today-board__grid">
      <section class="today-board__primary" aria-labelledby="today-checklist-heading">
        <article
          v-if="nextStep && !allDone"
          class="today-board__focus-card panel"
          aria-label="当前建议"
        >
          <p class="today-board__focus-kicker">现在做这一步</p>
          <h2>{{ nextStep.title }}</h2>
          <p>{{ nextStep.hint }}</p>
          <div class="today-board__focus-actions">
            <a-button type="primary" size="large" @click="router.push(nextStep.route)">
              {{ nextStep.cta }}
            </a-button>
            <a-button
              v-if="nextStep.alt_route"
              type="link"
              @click="router.push(nextStep.alt_route)"
            >
              {{ altLinkLabel(nextStep) }}
            </a-button>
          </div>
        </article>

        <article v-else-if="allDone" class="today-board__done-card panel">
          <CheckCircleFilled class="today-board__done-icon" />
          <h2>今日三步已完成</h2>
          <p>继续保持发布节奏，留意询盘列表里的新消息。</p>
          <a-button type="primary" @click="router.push('/client/inquiries')">查看询盘</a-button>
        </article>

        <div class="today-board__list-card panel">
          <h2 id="today-checklist-heading" class="today-board__list-title">清单</h2>
          <ol class="today-board__list" aria-label="今日三步清单">
            <li
              v-for="(step, index) in steps"
              :key="step.id"
              class="today-board__item"
              :class="{
                'today-board__item--done': step.done,
                'today-board__item--current': step.id === payload.next_step_id && !step.done,
                'today-board__item--later': step.id !== payload.next_step_id && !step.done,
              }"
            >
              <span class="today-board__item-marker" aria-hidden="true">
                <CheckOutlined v-if="step.done" />
                <span v-else>{{ step.order }}</span>
              </span>
              <div class="today-board__item-body">
                <div class="today-board__item-head">
                  <div>
                    <strong>{{ step.title }}</strong>
                    <span>{{ step.subtitle }}</span>
                  </div>
                  <a-button
                    v-if="!step.done"
                    size="small"
                    :type="step.id === payload.next_step_id ? 'primary' : 'default'"
                    @click="router.push(step.route)"
                  >
                    {{ step.cta }}
                  </a-button>
                </div>
              </div>
              <div
                v-if="index < steps.length - 1"
                class="today-board__item-line"
                aria-hidden="true"
              />
            </li>
          </ol>
        </div>

        <p class="today-board__foot">
          <a-button type="link" size="small" @click="router.push('/client/dashboard')">
            需要更多功能？打开完整工作台 →
          </a-button>
        </p>
      </section>

      <aside v-if="weekly" class="today-board__aside panel" aria-label="本周询盘实况">
        <header class="today-board__aside-head">
          <h3>本周询盘</h3>
          <p>{{ weekly.honest_note || '真实入库数据，0 即显示 0' }}</p>
        </header>
        <div class="today-board__stats">
          <div class="today-board__stat">
            <strong>{{ weekly.received ?? 0 }}</strong>
            <span>本周来了</span>
          </div>
          <div class="today-board__stat">
            <strong>{{ weekly.followed ?? 0 }}</strong>
            <span>已跟进</span>
          </div>
          <div class="today-board__stat">
            <strong>{{ weekly.pending ?? 0 }}</strong>
            <span>待处理</span>
          </div>
          <div class="today-board__stat">
            <strong>{{ weekly.with_phone ?? 0 }}</strong>
            <span>有手机号</span>
          </div>
        </div>
        <a-button block @click="router.push('/client/inquiries')">打开询盘列表</a-button>
        <p v-if="payload.product_count" class="today-board__aside-meta">
          产品库 {{ payload.product_count }} 个 · 发内容时会自动引用
        </p>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { CheckCircleFilled, CheckOutlined } from '@ant-design/icons-vue';
import { useClientTodayThree } from '@/composables/useClientTodayThree';
import type { TodayThreeStep } from '@/composables/useClientTodayThree';

const router = useRouter();
const { payload, steps, nextStep, allDone, progressPct, weekly, load, refresh } = useClientTodayThree();

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '早上好';
  if (h < 18) return '下午好';
  return '晚上好';
});

function altLinkLabel(step: TodayThreeStep) {
  if (step.id === 'product') return '或从产业带候选导入 →';
  if (step.id === 'content') return '或去内容分发 →';
  return '其他方式 →';
}

onMounted(() => {
  void load();
});

onActivated(() => {
  void refresh();
});
</script>

<style scoped lang="scss">
/* 单色系：slate 正文 + #5c7284 唯一强调色 */
$today-accent: #5c7284;
$today-accent-hover: #4a6174;
$today-text: #1f2937;
$today-muted: #64748b;
$today-border: #e5e7eb;
$today-surface: #ffffff;
$today-page: #f3f4f6;

.today-board {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 20px 20px 28px;
  font-family: var(--uj-font-sans);
  color: $today-text;
  background: $today-page;
  box-sizing: border-box;
}

.today-board :deep(.panel) {
  background: $today-surface !important;
  border: 1px solid $today-border !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 2px rgb(15 23 42 / 0.04) !important;
}

.today-board__top {
  margin-bottom: 16px;
  padding: 0 4px;
}

.today-board__kicker {
  margin: 0;
  font-size: 12px;
  color: $today-muted;
}

.today-board h1 {
  margin: 4px 0 0;
  font-size: clamp(1.35rem, 3vw, 1.6rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: $today-text;
  line-height: 1.25;
}

.today-board__sub {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: $today-muted;
  max-width: 40rem;
}

.today-board__progress {
  margin-top: 14px;
  max-width: 320px;
}

.today-board__progress-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  color: $today-muted;
  margin-bottom: 6px;
}

.today-board__region {
  color: $today-muted;
}

.today-board__progress-track {
  height: 6px;
  border-radius: 999px;
  background: $today-border;
  overflow: hidden;
}

.today-board__progress-fill {
  height: 100%;
  border-radius: 999px;
  background: $today-accent;
  transition: width 0.4s ease;
}

.today-board__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  align-items: start;
}

@media (min-width: 960px) {
  .today-board__grid {
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 16px;
  }
}

.today-board__focus-card {
  padding: 18px 20px;
  margin-bottom: 12px;
  border-left: 3px solid $today-accent !important;
}

.today-board__focus-kicker {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: $today-muted;
}

.today-board__focus-card h2 {
  margin: 6px 0 0;
  font-size: 17px;
  font-weight: 700;
  color: $today-text;
}

.today-board__focus-card p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: $today-muted;
}

.today-board__focus-actions {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.today-board__done-card {
  padding: 22px 20px;
  margin-bottom: 12px;
  text-align: center;
  border-left: 3px solid $today-accent !important;
}

.today-board__done-icon {
  font-size: 32px;
  color: $today-accent;
}

.today-board__done-card h2 {
  margin: 8px 0 0;
  font-size: 17px;
  font-weight: 700;
  color: $today-text;
}

.today-board__done-card p {
  margin: 6px 0 14px;
  font-size: 13px;
  color: $today-muted;
}

.today-board__list-card {
  padding: 16px 18px;
}

.today-board__list-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: $today-muted;
}

.today-board__list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.today-board__item {
  position: relative;
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 12px;
  padding: 12px 0;
}

.today-board__item-line {
  position: absolute;
  left: 17px;
  top: 48px;
  bottom: -4px;
  width: 2px;
  background: $today-border;
}

.today-board__item-marker {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: $today-muted;
  background: #f9fafb;
  border: 1px solid $today-border;
}

.today-board__item--done .today-board__item-marker {
  color: $today-accent;
  border-color: #d1d5db;
  background: #f3f4f6;
}

.today-board__item--current .today-board__item-marker {
  color: #fff;
  border-color: $today-accent;
  background: $today-accent;
}

.today-board__item--later {
  opacity: 0.72;
}

.today-board__item-body strong {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: $today-text;
}

.today-board__item-body span {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.4;
  color: $today-muted;
}

.today-board__item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.today-board__foot {
  margin: 8px 4px 0;
}

.today-board__foot :deep(.ant-btn-link) {
  color: $today-accent !important;
  padding-left: 0;
}

.today-board__aside {
  padding: 16px 18px;
}

.today-board__aside-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: $today-text;
}

.today-board__aside-head p {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: $today-muted;
}

.today-board__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 14px 0 12px;
}

.today-board__stat {
  padding: 12px 10px;
  border-radius: 10px;
  text-align: center;
  border: 1px solid $today-border;
  background: #f9fafb;
}

.today-board__stat strong {
  display: block;
  font-size: 1.3rem;
  font-weight: 700;
  color: $today-text;
  font-variant-numeric: tabular-nums;
}

.today-board__stat span {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: $today-muted;
}

.today-board__aside-meta {
  margin: 12px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: $today-muted;
}

.today-board :deep(.ant-btn-primary) {
  background: $today-accent;
  border-color: $today-accent;
  box-shadow: none;
}

.today-board :deep(.ant-btn-primary:not(:disabled):hover) {
  background: $today-accent-hover;
  border-color: $today-accent-hover;
}

.today-board :deep(.ant-btn-default) {
  border-color: #d1d5db;
  color: $today-text;
}

@media (max-width: 640px) {
  .today-board {
    padding: 16px 12px 24px;
  }

  .today-board__item-head {
    flex-direction: column;
  }
}
</style>
