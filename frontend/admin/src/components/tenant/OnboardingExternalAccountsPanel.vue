/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div id="external-accounts" class="external-accounts">
    <a-alert
      v-if="preview"
      type="info"
      show-icon
      class="mb-4"
      :message="preview.headline"
    >
      <template #description>
        <p class="mb-2">{{ preview.platform_managed_summary }}</p>
        <p class="mb-0">{{ preview.tenant_managed_summary }}</p>
      </template>
    </a-alert>

    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <a-collapse v-if="phases.length" v-model:active-key="activePhases" bordered>
        <a-collapse-panel
          v-for="phase in phases"
          :key="phase.id"
          :header="`${phase.title}（${phase.done}/${phase.total}）`"
        >
          <p class="text-sm text-slate-500 mb-3">{{ phase.summary }}</p>
          <div class="space-y-4">
            <div
              v-for="item in phase.items"
              :key="item.id"
              class="ext-card"
            >
              <div class="ext-card__head">
                <strong>{{ item.title }}</strong>
                <a-tag :color="item.owner === 'platform' ? 'blue' : 'orange'">
                  {{ item.owner_label }}
                </a-tag>
                <a-tag :color="statusColor(item.status)">{{ statusLabel(item.status) }}</a-tag>
              </div>
              <p class="ext-card__summary">{{ item.summary }}</p>
              <ol v-if="item.steps?.length" class="ext-card__steps">
                <li v-for="(step, idx) in item.steps" :key="idx">{{ step }}</li>
              </ol>
              <div class="ext-card__actions">
                <a-button
                  v-if="item.register_url"
                  type="link"
                  size="small"
                  :href="item.register_url"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  去官网注册 / 实名
                </a-button>
                <a-button
                  v-if="item.settings_route"
                  type="link"
                  size="small"
                  @click="goRoute(item.settings_route)"
                >
                  在优丁里绑定
                </a-button>
              </div>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>
      <a-empty v-else description="暂无第三方账号清单" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useRouter } from 'vue-router';
import { apiGet } from '@/utils/api';

interface ExternalAccountItem {
  id: string;
  title: string;
  owner: string;
  owner_label: string;
  summary: string;
  steps?: string[];
  register_url?: string;
  settings_route?: string;
  status: string;
}

interface ExternalPhase {
  id: string;
  title: string;
  summary: string;
  done: number;
  total: number;
  items: ExternalAccountItem[];
}

interface Preview {
  headline: string;
  platform_managed_summary: string;
  tenant_managed_summary: string;
}

const router = useRouter();
const loading = ref(false);
const phases = ref<ExternalPhase[]>([]);
const preview = ref<Preview | null>(null);
const activePhases = ref<string[]>(['open', 'visible']);

function statusColor(status: string) {
  if (status === 'done') return 'success';
  if (status === 'partial') return 'processing';
  return 'default';
}

function statusLabel(status: string) {
  if (status === 'done') return '已完成';
  if (status === 'partial') return '进行中';
  return '待处理';
}

function goRoute(path: string) {
  if (path.startsWith('/')) router.push(path);
}

async function load() {
  loading.value = true;
  try {
    const data = await apiGet<{
      preview?: Preview;
      phases?: ExternalPhase[];
    }>('/tenants/self/external-accounts');
    preview.value = data?.preview || null;
    phases.value = data?.phases || [];
  } catch {
    phases.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(load);
defineExpose({ reload: load });
</script>

<style scoped>
.ext-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fafafa;
}
.ext-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.ext-card__summary {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 8px;
}
.ext-card__steps {
  margin: 0 0 8px 18px;
  font-size: 13px;
  color: #475569;
}
.ext-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
