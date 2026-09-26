/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 今日三步 · 专业减法版
 * 契约：一屏一决策 · 一卡一步 · 人话状态 · 高级但不花
 */
<template>
  <div class="today-pro">
    <header class="today-pro__hero">
      <div class="today-pro__eyebrow">今天</div>
      <h1 class="today-pro__title">{{ heroTitle }}</h1>
      <p class="today-pro__lead">{{ heroLead }}</p>
      <div class="today-pro__cta">
        <a-button type="primary" size="large" class="today-pro__btn" @click="goPrimary()">
          {{ primaryCta }}
        </a-button>
        <a-button size="large" class="today-pro__btn-ghost" @click="reload">
          {{ loading ? '加载中…' : '刷新' }}
        </a-button>
      </div>
    </header>

    <section class="today-pro__steps" aria-label="今日三件事">
      <article
        v-for="(step, i) in steps"
        :key="step.id"
        class="step-card"
        :class="{ 'step-card--done': step.done }"
      >
        <div class="step-card__index">{{ i + 1 }}</div>
        <div class="step-card__body">
          <h2>{{ step.title }}</h2>
          <p>{{ step.subtitle }}</p>
          <p class="step-card__hint">{{ step.hint }}</p>
        </div>
        <div class="step-card__act">
          <span class="step-badge" :class="step.done ? 'ok' : 'warn'">
            {{ step.done ? '已完成' : '待处理' }}
          </span>
          <a-button
            v-if="!step.done"
            type="primary"
            class="today-pro__btn"
            @click="go(step.route)"
          >
            {{ step.cta || '去处理' }}
          </a-button>
          <a-button v-else class="today-pro__btn-ghost" @click="go(step.route)">再看看</a-button>
        </div>
      </article>
    </section>

    <section class="today-pro__good" aria-label="好消息">
      <h2>好消息</h2>
      <ul class="good-list">
        <li v-for="(g, i) in goods" :key="i">
          <span class="good-dot"></span>
          <span>{{ g }}</span>
        </li>
      </ul>
    </section>

    <section class="today-pro__bar" aria-label="本月一眼">
      <div class="mini-stat">
        <b>{{ stats.inquiries }}</b>
        <span>进行中询盘</span>
      </div>
      <div class="mini-stat">
        <b>{{ stats.pending }}</b>
        <span>待回复</span>
      </div>
      <div class="mini-stat">
        <b>{{ stats.orders }}</b>
        <span>在途履约</span>
      </div>
      <div class="mini-stat">
        <b class="ok">{{ stats.wonAmountLabel }}</b>
        <span>累计成单</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useClientTodayThree } from '@/composables/useClientTodayThree';

const router = useRouter();
const { payload, nextStep, allDone, load, recentWins, winLoss } = useClientTodayThree();

const loading = computed(() => false);

const steps = computed(() => {
  const list = payload.value.steps?.length
    ? payload.value.steps
    : [
        {
          id: 'product',
          order: 1,
          title: '把产品放上去',
          subtitle: '客户才能看到你在卖什么',
          done: false,
          route: '/client/products',
          cta: '去发品',
          hint: '产品少也可以先发 1 个，不求全。',
        },
        {
          id: 'content',
          order: 2,
          title: '让别人找到你',
          subtitle: '发内容 / 分发到多端',
          done: false,
          route: '/client/distribute',
          cta: '去分发',
          hint: '有内容才有人进站、来询盘。',
        },
        {
          id: 'inquiry',
          order: 3,
          title: '回复客户询盘',
          subtitle: '有人问了就回，回了才可能成单',
          done: false,
          route: '/client/inquiries',
          cta: '去回复',
          hint: '不会写？点进去让系统帮你起一版。',
        },
      ];
  return [...list].sort((a, b) => Number(a.done) - Number(b.done) || a.order - b.order);
});

const heroTitle = computed(() => {
  if (allDone.value) return '今天该做的都做完了';
  const t = nextStep.value?.title;
  return t ? `先做「${t}」就行` : '今天先做这 3 件事';
});

const heroLead = computed(() => {
  if (allDone.value) return '保持节奏：看询盘、回客户、盯履约。';
  return '不用一次做完。点下面最上面那件，做完再点下一件。';
});

const primaryCta = computed(() => {
  if (allDone.value) return '去看看询盘';
  return nextStep.value?.cta || '开始第一步';
});

const goods = computed(() => {
  const items: string[] = [];
  const wins = recentWins.value || [];
  for (const w of wins.slice(0, 2)) {
    const amt = Number(w.amount || 0);
    const label = amt > 0 ? `成单 $${amt.toLocaleString()}` : '已成单';
    items.push(`最近成单：${w.buyer || '客户'} · ${label}`);
  }
  const wl = winLoss.value;
  if (wl?.won_count) {
    items.push(`累计成交 ${wl.won_count} 单${wl.plain_summary ? ' — ' + wl.plain_summary : ''}`);
  }
  const w = payload.value.weekly_inquiries || {};
  if (w.received) items.push(`本周收到 ${w.received} 条询盘`);
  if (w.pending) items.push(`还有 ${w.pending} 条待回复——建议今天点掉`);
  if (!items.length) items.push('还没有新消息。先发 1 个产品，或去「找客户」。');
  return items.slice(0, 4);
});

const stats = computed(() => {
  const t = payload.value.trade_stats || ({} as Record<string, number>);
  const won = Number(t.won_amount ?? winLoss.value?.won_amount ?? 0);
  return {
    inquiries: Number(t.active_inquiries ?? 0),
    pending: Number(t.pending_response ?? payload.value.weekly_inquiries?.pending ?? 0),
    orders: Number(t.active_fulfillment_orders ?? 0),
    wonAmountLabel: won > 0 ? `$${won.toLocaleString()}` : '¥',
  };
});

function go(path: string) {
  void router.push(path);
}

function goPrimary() {
  if (allDone.value) return go('/client/inquiries');
  go(nextStep.value?.route || '/client/products');
}

function reload() {
  void load(true);
}

onMounted(() => {
  void load();
});
</script>

<style scoped>
.today-pro {
  max-width: 860px;
  margin: 0 auto;
  padding: 28px 20px 48px;
  color: #122622;
}

.today-pro__hero {
  margin-bottom: 22px;
  padding: 22px 22px 18px;
  border-radius: 18px;
  background: linear-gradient(145deg, #e8f5f0, #f7fbfa 50%, #eef7f3);
  border: 1px solid #e3efea;
}

.today-pro__eyebrow {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #2f6a5f;
  margin-bottom: 8px;
}

.today-pro__title {
  font-size: clamp(1.45rem, 2.5vw, 1.85rem);
  font-weight: 500;
  margin: 0 0 8px;
  line-height: 1.25;
}

.today-pro__lead {
  margin: 0 0 16px;
  color: #55706b;
  font-size: 0.98rem;
  max-width: 40em;
}

.today-pro__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.today-pro__btn {
  min-height: 48px;
  padding: 0 22px;
  border-radius: 12px !important;
  font-weight: 500;
  background: #367469 !important;
  border-color: #367469 !important;
  transition: transform 160ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 160ms ease;
}
.today-pro__btn:active {
  transform: scale(0.96);
  box-shadow: inset 0 2px 6px rgba(31, 74, 66, 0.15);
}
.today-pro__btn-ghost {
  min-height: 48px;
  border-radius: 12px !important;
  font-weight: 500;
  background: #fff !important;
  border: 1px solid #e3efea !important;
  color: #2f6a5f !important;
}

.today-pro__steps {
  display: grid;
  gap: 10px;
  margin-bottom: 18px;
}

.step-card {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e3efea;
  box-shadow: 0 1px 2px rgba(31, 74, 66, 0.05);
}

.step-card--done {
  opacity: 0.72;
  background: #fbfefc;
}

.step-card__index {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #dcf0eb;
  color: #2f6a5f;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-weight: 500;
}

.step-card h2 {
  margin: 0 0 2px;
  font-size: 1.05rem;
  font-weight: 500;
}

.step-card p {
  margin: 0;
  color: #1c322d;
  font-size: 0.92rem;
}

.step-card__hint {
  margin-top: 4px !important;
  color: #55706b !important;
  font-size: 0.82rem !important;
}

.step-card__act {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  min-width: 120px;
}

.step-badge {
  text-align: center;
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 999px;
  font-weight: 500;
}
.step-badge.ok { background: #eaf7f2; color: #24705a; }
.step-badge.warn { background: #fef7e6; color: #8a6212; }

.today-pro__good {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e3efea;
}
.today-pro__good h2 {
  font-size: 0.9rem;
  font-weight: 500;
  color: #55706b;
  margin-bottom: 8px;
}
.good-list {
  list-style: none;
  display: grid;
  gap: 8px;
}
.good-list li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 0.95rem;
  color: #1c322d;
}
.good-dot {
  width: 8px;
  height: 8px;
  margin-top: 7px;
  border-radius: 50%;
  background: #4a9b8c;
  flex: 0 0 auto;
}

.today-pro__bar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.mini-stat {
  padding: 14px 12px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e3efea;
  text-align: center;
}
.mini-stat b {
  display: block;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 1.3rem;
  font-weight: 500;
}
.mini-stat b.ok { color: #2f6a5f; }
.mini-stat span {
  font-size: 0.75rem;
  color: #55706b;
}

@media (max-width: 640px) {
  .step-card {
    grid-template-columns: 36px 1fr;
  }
  .step-card__act {
    grid-column: 1 / -1;
    flex-direction: row;
  }
  .today-pro__bar {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (prefers-reduced-motion: reduce) {
  .today-pro__btn { transition: none; }
  .today-pro__btn:active { transform: none; }
}
</style>
