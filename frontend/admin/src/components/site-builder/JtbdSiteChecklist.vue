/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <section v-if="items.length" class="jtbd-checklist uj-glass-panel">
    <header class="jtbd-checklist__head">
      <h3>{{ title }}</h3>
      <p>{{ subtitle }}</p>
      <span class="jtbd-checklist__progress">{{ doneCount }}/{{ items.length }} 已完成</span>
    </header>
    <ul class="jtbd-checklist__list">
      <li
        v-for="item in items"
        :key="item.key"
        class="jtbd-checklist__item"
        :class="`is-${item.status || 'pending'}`"
      >
        <span class="jtbd-checklist__dot" aria-hidden="true" />
        <div class="jtbd-checklist__body">
          <strong>{{ item.title }}</strong>
          <p>{{ item.detail }}</p>
          <span v-if="item.paradigm" class="jtbd-checklist__tag">{{ item.paradigm }}</span>
        </div>
        <a-button
          v-if="item.route"
          size="small"
          type="link"
          @click="router.push(item.route)"
        >
          去完善
        </a-button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';

export type JtbdChecklistItem = {
  key: string;
  title: string;
  detail?: string;
  route?: string;
  phase?: string;
  paradigm?: string;
  status?: 'done' | 'partial' | 'pending';
};

const props = withDefaults(
  defineProps<{
    items: JtbdChecklistItem[];
    title?: string;
    subtitle?: string;
  }>(),
  {
    title: '建站四要素（卖结果 · 按阶段 · 内容获客 · 单一转化）',
    subtitle: '对齐 SITE-JTBD-01：让访客带着任务来，而不是来逛厂',
  },
);

const router = useRouter();
const doneCount = computed(
  () => props.items.filter((i) => i.status === 'done').length,
);
</script>

<style scoped>
.jtbd-checklist {
  padding: 1rem 1.15rem;
  margin-bottom: 1rem;
}
.jtbd-checklist__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem 0.75rem;
  margin-bottom: 0.75rem;
}
.jtbd-checklist__head h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}
.jtbd-checklist__head p {
  margin: 0;
  flex: 1 1 100%;
  font-size: 0.78rem;
  color: #64748b;
}
.jtbd-checklist__progress {
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 600;
  color: #0369a1;
}
.jtbd-checklist__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.jtbd-checklist__item {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.55rem 0.65rem;
  border-radius: 0.65rem;
  border: 1px solid rgb(226 232 240);
  background: rgb(248 250 252);
}
.jtbd-checklist__item.is-done {
  border-color: rgb(167 243 208);
  background: rgb(236 253 245);
}
.jtbd-checklist__item.is-partial {
  border-color: rgb(253 230 138);
  background: rgb(255 251 235);
}
.jtbd-checklist__dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 9999px;
  margin-top: 0.35rem;
  background: #94a3b8;
  flex-shrink: 0;
}
.jtbd-checklist__item.is-done .jtbd-checklist__dot {
  background: #059669;
}
.jtbd-checklist__item.is-partial .jtbd-checklist__dot {
  background: #d97706;
}
.jtbd-checklist__body {
  flex: 1;
  min-width: 0;
}
.jtbd-checklist__body strong {
  display: block;
  font-size: 0.82rem;
  color: #0f172a;
}
.jtbd-checklist__body p {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.45;
}
.jtbd-checklist__tag {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #0369a1;
}
</style>
