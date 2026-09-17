/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="代理能力划拨" subtitle="各级别后台 API 边界与前台工作台入口勾选（localStorage）" surface="elevated">
    <template #actions>
      <a-select v-model:value="sessionLevel" style="min-width: 200px" :options="levelOptions" />
      <a-button type="link" @click="router.push('/admin')">工作台预览</a-button>
    </template>
  <div class="agent-cap-page">
    <a-tabs
      v-model:active-key="mainTab"
      class="main-tabs"
      type="card"
    >
      <a-tab-pane
        key="blueprint"
        tab="级别蓝图与设计"
      >
        <p class="tab-intro">
          与 <code>@/constants/agentLevelBlueprint.ts</code> 同源；后端实现时可按「模块 key +
          scope」映射到路由中间件或策略表。
        </p>
        <div class="blueprint-grid">
          <a-card
            v-for="bp in AGENT_LEVEL_BLUEPRINTS"
            :key="bp.id"
            class="bp-card"
            :title="levelLabel(bp.id)"
            size="small"
          >
            <template #extra>
              <a-button
                type="link"
                size="small"
                @click="openGrantsFor(bp.id)"
              >
                去勾选能力
              </a-button>
            </template>
            <p class="bp-tagline">
              {{ bp.tagline }}
            </p>
            <p class="bp-meta">
              <strong>组织形态</strong> {{ bp.orgShape }}
            </p>
            <p class="bp-meta">
              <strong>数据范围</strong> {{ bp.dataScope }}
            </p>
            <a-divider
              orientation="left"
              plain
            >
              后台模块与权限
            </a-divider>
            <a-table
              :columns="backendColumns"
              :data-source="bp.backendModules"
              :pagination="false"
              size="small"
              row-key="key"
              class="bp-table"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'scope'">
                  {{ scopeLabel(record.scope) }}
                </template>
              </template>
            </a-table>
            <a-divider
              orientation="left"
              plain
            >
              工作台主题
            </a-divider>
            <div class="chip-row">
              <a-tag
                v-for="t in bp.workbenchThemes"
                :key="`${bp.id}-${t}`"
                color="processing"
              >
                {{ t }}
              </a-tag>
            </div>
            <a-divider
              orientation="left"
              plain
            >
              功能要点
            </a-divider>
            <ul class="bp-list">
              <li
                v-for="(f, i) in bp.features"
                :key="`f-${bp.id}-${i}`"
              >
                {{ f }}
              </li>
            </ul>
            <a-divider
              orientation="left"
              plain
            >
              限制
            </a-divider>
            <ul class="bp-list restrict">
              <li
                v-for="(r, i) in bp.restrictions"
                :key="`r-${bp.id}-${i}`"
              >
                {{ r }}
              </li>
            </ul>
          </a-card>
        </div>
      </a-tab-pane>
      <a-tab-pane
        key="grants"
        tab="工作台能力勾选"
      >
        <div class="layout-split">
          <aside class="level-aside glass">
            <div class="aside-title">
              编辑对象
            </div>
            <button
              v-for="opt in levelOptions"
              :key="opt.value"
              type="button"
              class="level-btn"
              :class="{ active: editingLevel === opt.value }"
              @click="editingLevel = opt.value as AgentLevelId"
            >
              {{ opt.label }}
            </button>
            <div class="aside-actions">
              <a-button
                size="small"
                @click="selectAllEditing"
              >
                全选
              </a-button>
              <a-button
                size="small"
                @click="clearEditing"
              >
                全不选
              </a-button>
            </div>
            <a-button
              danger
              block
              size="small"
              @click="onResetDefaults"
            >
              全部级别恢复默认
            </a-button>
          </aside>

          <div class="main-panels">
            <article
              v-for="sec in WORKBENCH_CAPABILITY_REGISTRY"
              :key="sec.key"
              class="sec-card glass"
              :class="{ 'sec-card--dense': sec.items.length > 12 }"
            >
              <header class="sec-head">
                <div
                  class="sec-icon"
                  :class="'tone-' + sec.tone"
                >
                  <component :is="iconFor(sec.sectionIcon)" />
                </div>
                <div>
                  <h2>{{ sec.title }}</h2>
                  <p>{{ sec.subtitle }}</p>
                </div>
              </header>
              <div class="tile-grid">
                <label
                  v-for="item in sec.items"
                  :key="item.id"
                  class="cap-tile"
                  :class="'tone-' + item.tone"
                  @click="onCapTileClick(item.id, $event)"
                >
                  <a-checkbox
                    :checked="checkedSet.has(item.id)"
                    @click.stop
                    @change="(e) => onCapCheckboxChange(item.id, e)"
                  />
                  <span class="cap-icon"><component :is="iconFor(item.itemIcon)" /></span>
                  <span class="cap-text">
                    <span class="cap-name">{{ item.name }}</span>
                    <span class="cap-desc">{{ item.description }}</span>
                  </span>
                </label>
              </div>
            </article>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Modal } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { PartitionOutlined } from '@ant-design/icons-vue';
import {
  WORKBENCH_CAPABILITY_REGISTRY,
  allCapabilityIds,
} from '@/constants/workbenchCapabilityRegistry';
import { AGENT_LEVEL_BLUEPRINTS } from '@/constants/agentLevelBlueprint';
import { WORKBENCH_ICONS } from '@/constants/workbenchIcons';
import {
  useAgentCapabilitiesStore,
  AGENT_LEVEL_IDS,
  AGENT_LEVEL_LABELS,
  type AgentLevelId,
} from '@/stores/agentCapabilities';

const router = useRouter();
const capStore = useAgentCapabilitiesStore();

const mainTab = ref('blueprint');

const backendColumns = [
  { title: '模块', dataIndex: 'key', key: 'key', ellipsis: true },
  { title: '范围', dataIndex: 'scope', key: 'scope', width: 112 },
  { title: '说明', dataIndex: 'note', key: 'note', ellipsis: true },
];

function scopeLabel(s: string) {
  const map: Record<string, string> = {
    full: '全量',
    read: '只读',
    scoped_write: '限定写',
    none: '关闭',
  };
  return map[s] ?? s;
}

function levelLabel(id: AgentLevelId) {
  return AGENT_LEVEL_LABELS[id];
}

function openGrantsFor(id: AgentLevelId) {
  editingLevel.value = id;
  mainTab.value = 'grants';
}

const editingLevel = ref<AgentLevelId>('L1');

const sessionLevel = computed({
  get: () => capStore.currentLevelId,
  set: (v: AgentLevelId | string) => {
    if (AGENT_LEVEL_IDS.includes(v as AgentLevelId)) capStore.setCurrentLevel(v as AgentLevelId);
  },
});

const levelOptions = AGENT_LEVEL_IDS.map((id) => ({
  value: id,
  label: AGENT_LEVEL_LABELS[id],
}));

const checkedSet = computed(() => new Set(capStore.grantsForLevel(editingLevel.value)));

function iconFor(name: string) {
  return WORKBENCH_ICONS[name] ?? WORKBENCH_ICONS.DashboardOutlined;
}

function toggle(id: string, checked: boolean) {
  const set = new Set(capStore.grantsForLevel(editingLevel.value));
  if (checked) set.add(id);
  else set.delete(id);
  capStore.setGrantsForLevel(editingLevel.value, [...set]);
}

function onCapCheckboxChange(id: string, e: { target: { checked: boolean } }) {
  toggle(id, e.target.checked);
}

/** 点击卡片空白处切换（避免 label 与 checkbox 双触发） */
function onCapTileClick(id: string, e: MouseEvent) {
  const el = e.target as HTMLElement | null;
  if (el?.closest('.ant-checkbox-wrapper, .ant-checkbox')) return;
  toggle(id, !checkedSet.value.has(id));
}

function selectAllEditing() {
  capStore.setGrantsForLevel(editingLevel.value, allCapabilityIds());
}

function clearEditing() {
  capStore.setGrantsForLevel(editingLevel.value, []);
}

function onResetDefaults() {
  Modal.confirm({
    title: '恢复默认划拨？',
    content: '所有级别的勾选将恢复为内置建议方案。',
    okText: '恢复',
    cancelText: '取消',
    onOk: () => capStore.resetAllGrantsToDefaults(),
  });
}

onMounted(async () => {
  try { await apiGet('/agent-tree'); } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.agent-cap-page {
  padding: 1.25rem 1.5rem 2rem;
  width: 100%;
  max-width: none;
  margin: 0;
}

.glass {
  background: var(--uj-glass-bg-strong, rgb(255 255 255 / 0.96));
  border: 1px solid var(--uj-border, rgb(226 232 240 / 0.95));
  border-radius: 20px;
  box-shadow: var(--uj-glass-shadow, 0 8px 32px rgb(45 107 96 / 0.08));
}

.page-head {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
}

.title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.desc {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.55;
  max-width: 52rem;
}

.session-row {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.session-row .label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

.main-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 1rem;
}

.tab-intro {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.5;
}

.blueprint-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media (min-width: 1100px) {
  .blueprint-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.bp-card :deep(.ant-card-head-title) {
  font-size: 0.95rem;
  font-weight: 700;
}

.bp-tagline {
  margin: 0 0 0.65rem;
  font-size: 0.88rem;
  color: #334155;
  line-height: 1.5;
}

.bp-meta {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.45;
}

.bp-table {
  margin-bottom: 0.25rem;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.bp-list {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.55;
}
.bp-list.restrict {
  color: #b45309;
}

.layout-split {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}

.level-aside {
  flex: 0 0 200px;
  padding: 1rem;
  position: sticky;
  top: 1rem;
}

.aside-title {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin-bottom: 0.75rem;
}

.level-btn {
  width: 100%;
  text-align: left;
  padding: 0.55rem 0.65rem;
  margin-bottom: 0.35rem;
  border-radius: 12px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.4);
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s;
}
.level-btn:hover {
  background: #fff;
  border-color: #e2e8f0;
}
.level-btn.active {
  background: linear-gradient(135deg, #6f93ab, #55778f);
  color: #fff;
  border-color: transparent;
}

.aside-actions {
  display: flex;
  gap: 0.35rem;
  margin: 0.75rem 0;
}

.main-panels {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.sec-card {
  padding: 1.15rem 1.25rem 1rem;
  width: 100%;
}

.sec-head {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}

.sec-head h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
}
.sec-head p {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  color: #64748b;
}

.sec-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #fff;
  flex-shrink: 0;
}

.tile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.65rem 0.75rem;
}

/* 条目多的分组（如超级管理员套件）用更密网格，避免整页过长 */
.sec-card--dense .tile-grid {
  grid-template-columns: repeat(auto-fill, minmax(185px, 1fr));
  gap: 0.5rem 0.65rem;
}

.sec-card--dense .cap-tile {
  padding: 0.5rem 0.6rem;
}

.sec-card--dense .cap-desc {
  -webkit-line-clamp: 1;
  font-size: 0.68rem;
}

.cap-tile {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 0.65rem 0.75rem;
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  transition:
    border-color 0.12s,
    box-shadow 0.12s;
}
.cap-tile :deep(.ant-checkbox-wrapper) {
  flex-shrink: 0;
  margin-top: 2px;
}
.cap-tile:hover {
  border-color: rgba(124, 92, 252, 0.3);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
}

.cap-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  color: #fff;
  flex-shrink: 0;
  margin-top: 2px;
}

.cap-text {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}
.cap-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.35;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cap-desc {
  font-size: 0.72rem;
  line-height: 1.4;
  color: #64748b;
  word-break: keep-all;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tone-sky.sec-icon,
.tone-sky .cap-icon {
  background: linear-gradient(135deg, #38bdf8, #0284c7);
}
.tone-violet.sec-icon,
.tone-violet .cap-icon {
  background: linear-gradient(135deg, #8fa8bc, #55778f);
}
.tone-indigo.sec-icon,
.tone-indigo .cap-icon {
  background: linear-gradient(135deg, #818cf8, #4f46e5);
}
.tone-amber.sec-icon,
.tone-amber .cap-icon {
  background: linear-gradient(135deg, #fbbf24, #d97706);
}
.tone-emerald.sec-icon,
.tone-emerald .cap-icon {
  background: linear-gradient(135deg, #34d399, #059669);
}
.tone-rose.sec-icon,
.tone-rose .cap-icon {
  background: linear-gradient(135deg, #fb7185, #e11d48);
}
.tone-cyan.sec-icon,
.tone-cyan .cap-icon {
  background: linear-gradient(135deg, #22d3ee, #0891b2);
}
.tone-orange.sec-icon,
.tone-orange .cap-icon {
  background: linear-gradient(135deg, #fb923c, #ea580c);
}
.tone-blue.sec-icon,
.tone-blue .cap-icon {
  background: linear-gradient(135deg, #76e0bd, var(--uj-brand, #4a9b8c));
}
.tone-pink.sec-icon,
.tone-pink .cap-icon {
  background: linear-gradient(135deg, #f472b6, #db2777);
}
.tone-teal.sec-icon,
.tone-teal .cap-icon {
  background: linear-gradient(135deg, #2dd4bf, #0d9488);
}
.tone-slate.sec-icon,
.tone-slate .cap-icon {
  background: linear-gradient(135deg, #94a3b8, #475569);
}
.tone-red.sec-icon,
.tone-red .cap-icon {
  background: linear-gradient(135deg, #f87171, #dc2626);
}
.tone-green.sec-icon,
.tone-green .cap-icon {
  background: linear-gradient(135deg, #4ade80, #16a34a);
}
.tone-purple.sec-icon,
.tone-purple .cap-icon {
  background: linear-gradient(135deg, #c084fc, #9333ea);
}

@media (max-width: 900px) {
  .layout-split {
    flex-direction: column;
  }
  .level-aside {
    position: static;
    width: 100%;
    flex: none;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.35rem;
  }
  .aside-title {
    grid-column: 1 / -1;
  }
  .level-btn {
    margin-bottom: 0;
  }
  .aside-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 639px) {
  .tile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
