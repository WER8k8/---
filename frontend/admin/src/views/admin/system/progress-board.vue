/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="开发进度看板" subtitle="Sprint 任务进度 · 未完成项数" surface="elevated">
  <div class="progress-board p-4">
    <a-card v-if="swarmMeta" size="small" class="mb-4" :title="`蜂群小队 · ${swarmMeta.label}`">
      <p v-if="swarmMeta.updated_at" class="text-gray-500 text-xs mb-3">
        Sprint {{ swarmMeta.sprint_id }} · 更新 {{ swarmMeta.updated_at }}
      </p>

      <div class="bar-row mb-2">
        <div class="bar-track bar-track--lg">
          <div class="bar-fill" :style="{ width: swarmTotalPct + '%' }" />
        </div>
        <span class="bar-label">
          合计 {{ swarmTotalDone }}/{{ swarmTotalTasks }}（{{ swarmTotalPct }}%）
        </span>
      </div>
      <p class="text-gray-600 text-sm mb-4 font-medium">
        未完成 {{ swarmTotalRemain }} 项 · 共 {{ squads.length }} 个小队
      </p>

      <div v-for="s in squadRows" :key="s.id" class="module-row squad-row">
        <div class="module-head">
          <span class="module-name">
            <span v-if="s.owner" class="squad-owner">{{ s.owner }}</span>
            {{ s.name }}
          </span>
          <span class="module-pct">{{ s.pct }}%</span>
        </div>
        <div class="bar-track bar-track--sm">
          <div class="bar-fill" :style="{ width: s.pct + '%' }" />
        </div>
        <div class="module-meta">
          已完成 {{ s.done }}/{{ s.total }} ·
          <strong class="remain-strong">未完成 {{ s.remainCount }} 项</strong>
        </div>
        <ul v-if="s.remaining.length" class="remain-list">
          <li v-for="(t, i) in s.remaining" :key="i">{{ t }}</li>
        </ul>
        <p v-else class="remain-done">本小队已全部完成</p>
      </div>
    </a-card>

    <a-card size="small" class="mb-4" title="排期内研发 Sprint">
      <div class="bar-row">
        <div class="bar-track">
          <div class="bar-fill" :style="{ width: sprintPct + '%' }" />
        </div>
        <span class="bar-label">{{ sprint.done }}/{{ sprint.total }}（{{ sprintPct }}%）</span>
      </div>
      <p class="module-meta mt-2">
        未完成 {{ sprintRemain }} 项
        <span v-if="sprintRemain === 0"> · 排期任务已全部完成</span>
      </p>
    </a-card>

    <a-card size="small" class="mb-4" title="产品功能模块（全景）">
      <div class="bar-row mb-2">
        <div class="bar-track bar-track--lg">
          <div class="bar-fill" :style="{ width: modulePct + '%' }" />
        </div>
        <span class="bar-label">{{ moduleDone }}/{{ moduleTotal }}（{{ modulePct }}%）</span>
      </div>
      <p class="text-gray-500 text-xs mb-4">
        未完成 {{ moduleTotal - moduleDone }} 权重点 · {{ modules.length }} 个模块
      </p>

      <div v-for="m in modules" :key="m.id" class="module-row">
        <div class="module-head">
          <span class="module-name">{{ m.name }}</span>
          <span class="module-pct">{{ pct(m) }}%</span>
        </div>
        <div class="bar-track bar-track--sm">
          <div class="bar-fill" :style="{ width: pct(m) + '%' }" />
        </div>
        <div class="module-meta">
          已完成 {{ m.done }}/{{ m.total }} · 未完成 {{ m.total - m.done }}
          <span v-if="m.gap" class="gap-hint"> — {{ m.gap }}</span>
        </div>
      </div>
    </a-card>

    <a-card v-if="blockers.length" size="small" title="PM 阻塞项">
      <ul class="list-disc pl-5 text-sm text-gray-600">
        <li v-for="(b, i) in blockers" :key="i">{{ b }}</li>
      </ul>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import data from '@/data/module-progress.json';

type Mod = { id: string; name: string; done: number; total: number; gap?: string };
type SquadTask = { title: string; status: 'done' | 'pending' | 'in_progress' };
type Squad = {
  id: string;
  name: string;
  owner?: string;
  done?: number;
  total?: number;
  tasks?: SquadTask[];
};
type SwarmMeta = {
  sprint_id?: string;
  label?: string;
  updated_at?: string;
  squads?: Squad[];
};

onMounted(async () => {
  try {
    await apiGet('/daily-report');
  } catch {
    /* 空状态 */
  }
});

const swarmMeta = computed(() => (data as { swarm_squads?: SwarmMeta }).swarm_squads ?? null);
const squads = computed(() => swarmMeta.value?.squads ?? []);

function squadStats(s: Squad) {
  if (s.tasks?.length) {
    const total = s.tasks.length;
    const done = s.tasks.filter((t) => t.status === 'done').length;
    const remaining = s.tasks.filter((t) => t.status !== 'done').map((t) => t.title);
    return { done, total, remaining, remainCount: total - done };
  }
  const total = s.total ?? 0;
  const done = s.done ?? 0;
  return { done, total, remaining: [] as string[], remainCount: Math.max(0, total - done) };
}

const squadRows = computed(() =>
  squads.value.map((s) => {
    const st = squadStats(s);
    const pctVal = st.total ? Math.round((100 * st.done) / st.total) : 0;
    return { id: s.id, name: s.name, owner: s.owner, ...st, pct: pctVal };
  }),
);

const swarmTotalTasks = computed(() => squadRows.value.reduce((a, s) => a + s.total, 0));
const swarmTotalDone = computed(() => squadRows.value.reduce((a, s) => a + s.done, 0));
const swarmTotalRemain = computed(() => swarmTotalTasks.value - swarmTotalDone.value);
const swarmTotalPct = computed(() =>
  swarmTotalTasks.value ? Math.round((100 * swarmTotalDone.value) / swarmTotalTasks.value) : 0,
);

const sprint = computed(() => {
  const s = data.sprint_scheduled as { done: number; total: number };
  return s;
});

const modules = computed(() => (data.modules || []) as Mod[]);
const blockers = computed(() => (data.pm_blockers || []) as string[]);

const sprintPct = computed(() =>
  sprint.value.total ? Math.round((100 * sprint.value.done) / sprint.value.total) : 0,
);
const sprintRemain = computed(() => Math.max(0, sprint.value.total - sprint.value.done));

const moduleDone = computed(() => modules.value.reduce((a, m) => a + m.done, 0));
const moduleTotal = computed(() => modules.value.reduce((a, m) => a + m.total, 0));
const modulePct = computed(() =>
  moduleTotal.value ? Math.round((100 * moduleDone.value) / moduleTotal.value) : 0,
);

function pct(m: Mod) {
  return m.total ? Math.round((100 * m.done) / m.total) : 0;
}
</script>

<style scoped lang="scss">
.bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.bar-track {
  flex: 1;
  height: 10px;
  background: #e8e8e8;
  border-radius: 2px;
  overflow: hidden;
}
.bar-track--lg {
  height: 14px;
}
.bar-track--sm {
  height: 8px;
}
.bar-fill {
  height: 100%;
  background: #111;
  border-radius: 2px;
  transition: width 0.3s ease;
}
.bar-label {
  font-size: 13px;
  white-space: nowrap;
  color: #333;
}
.module-row {
  margin-bottom: 16px;
}
.squad-row {
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}
.module-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 13px;
}
.module-name {
  font-weight: 500;
}
.squad-owner {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #55778f;
  background: #f3e8ff;
  padding: 0 6px;
  border-radius: 4px;
  margin-right: 6px;
}
.module-pct {
  color: #666;
}
.module-meta {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}
.remain-strong {
  color: #b45309;
  font-weight: 600;
}
.remain-list {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #64748b;
  li {
    margin-bottom: 2px;
  }
}
.remain-done {
  margin: 4px 0 0;
  font-size: 12px;
  color: #16a34a;
}
.gap-hint {
  color: #999;
}
</style>
