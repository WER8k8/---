<template>
  <YdPage title="GEO 可见性" subtitle="AEO · 统一 GEO 分 · llms.txt · AI 探针" surface="elevated">
    <template v-if="loading">
      <SkeletonCard variant="kpi" />
    </template>
    <template v-else>
      <div v-if="unified?.ok" class="grid gap-4 md:grid-cols-4 mb-4">
        <div class="yd-panel p-4 md:col-span-1 border-2 border-indigo-200">
          <p class="text-xs text-gray-500">统一 GEO 分</p>
          <p class="text-3xl font-semibold text-indigo-700">{{ unified.overall ?? '—' }}</p>
          <p class="text-[10px] text-gray-400 mt-1">{{ unified.schema_version }}</p>
        </div>
        <div
          v-for="(comp, key) in componentRows"
          :key="key"
          class="yd-panel p-4"
        >
          <p class="text-xs text-gray-500">{{ comp.label }}</p>
          <p class="text-xl font-semibold" :class="comp.color">{{ comp.score ?? '—' }}</p>
          <p class="text-[10px] text-gray-400 mt-1">权重 {{ comp.weight }}%</p>
        </div>
      </div>

      <div v-if="dash?.ok" class="grid gap-4 md:grid-cols-3">
        <div class="yd-panel p-4">
          <p class="text-xs text-gray-500">AEO 事实得分</p>
          <p class="text-2xl font-semibold text-indigo-700">{{ dash.scores?.aeo_fact_score ?? '—' }}</p>
        </div>
        <div class="yd-panel p-4">
          <p class="text-xs text-gray-500">内容就绪度</p>
          <p class="text-2xl font-semibold text-emerald-700">{{ dash.scores?.content_readiness ?? '—' }}</p>
        </div>
        <div class="yd-panel p-4">
          <p class="text-xs text-gray-500">GEO 产品化</p>
          <p class="text-2xl font-semibold text-amber-700">{{ dash.scores?.geo_productization ?? '—' }}</p>
        </div>
      </div>

      <div v-if="dash?.llms_urls" class="yd-panel p-4 mt-4">
        <p class="font-medium mb-2">llms.txt 入口</p>
        <ul class="text-sm text-gray-700 list-disc pl-5 space-y-1">
          <li v-if="dash.llms_urls.llms_txt">
            预览站：<a :href="previewUrl(dash.llms_urls.llms_txt)" target="_blank" rel="noopener">llms.txt</a>
          </li>
          <li v-if="dash.llms_urls.llms_full">
            完整版：<a :href="previewUrl(dash.llms_urls.llms_full)" target="_blank" rel="noopener">llms-full.txt</a>
          </li>
          <li v-if="dash.llms_urls.public_api_llms">API：{{ dash.llms_urls.public_api_llms }}</li>
        </ul>
      </div>

      <div v-if="probeModels.length" class="yd-panel p-4 mt-4">
        <p class="font-medium mb-2">AI Search 探针</p>
        <div class="flex flex-wrap gap-2">
          <a-tag
            v-for="m in probeModels"
            :key="m.id"
            :color="probeColor(m.status)"
          >
            {{ m.name || m.id }} · {{ probeLabel(m.status) }}
          </a-tag>
        </div>
        <p class="text-xs text-gray-500 mt-2">未配置 Key 的探针显示「未接通」，不计为收录。</p>
      </div>

      <a-alert
        v-if="dash?.citations?.mode === 'honest_stub'"
        type="info"
        show-icon
        class="mt-4"
        :message="dash.citations.note"
      />

      <div v-if="gscStatus" class="yd-panel p-4 mt-4">
        <p class="font-medium mb-2">GSC/Ads 归因（GW-P-GSC-02）</p>
        <p class="text-sm text-gray-700">
          Webhook {{ gscStatus?.configured ? '已配置' : '未配置' }}
          <span v-if="gscStatus?.endpoint"> · {{ gscStatus.endpoint }}</span>
        </p>
        <p v-if="gscStatus?.honesty_note" class="text-xs text-gray-500 mt-1">{{ gscStatus.honesty_note }}</p>
      </div>

      <div v-if="dash?.content_stats" class="yd-panel p-4 mt-4">
        <p class="font-medium mb-2">内容统计</p>
        <p class="text-sm text-gray-700">
          母版 {{ dash.content_stats.masters_total }} · 已发布 {{ dash.content_stats.masters_published }} ·
          FAQ {{ dash.content_stats.faq_entries }} · 带图 SKU {{ dash.content_stats.products_with_images }}
        </p>
      </div>

      <div v-if="dash?.next_actions?.length" class="yd-panel p-4 mt-4">
        <p class="font-medium mb-2">建议下一步</p>
        <ul class="text-sm text-gray-700 list-disc pl-5">
          <li v-for="(a, i) in dash.next_actions" :key="i">{{ a }}</li>
        </ul>
      </div>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import {
  fetchGeoVisibilityDashboard,
  fetchUnifiedGeoScore,
  type GeoVisibilityDashboard,
  type UnifiedGeoScore,
} from '@/api/cross-border';
import { apiGet } from '@/utils/api';

type GscAdsStatus = {
  configured?: boolean;
  endpoint?: string;
  honesty_note?: string;
};

type ProbeModel = { id?: string; name?: string; status?: string };

const loading = ref(false);
const dash = ref<GeoVisibilityDashboard | null>(null);
const unified = ref<UnifiedGeoScore | null>(null);
const gscStatus = ref<GscAdsStatus | null>(null);

const componentRows = computed(() => {
  const comps = unified.value?.components || {};
  const labels: Record<string, { label: string; color: string }> = {
    aeo_readiness: { label: 'AEO 就绪', color: 'text-indigo-700' },
    content_visibility: { label: '内容可见', color: 'text-emerald-700' },
    content_readiness: { label: '内容就绪', color: 'text-teal-700' },
    model_mention: { label: '模型提及', color: 'text-violet-700' },
    ai_search_probes: { label: 'AI Search', color: 'text-amber-700' },
  };
  return Object.entries(comps)
    .filter(([k]) => k in labels)
    .map(([key, val]) => ({
      key,
      label: labels[key].label,
      color: labels[key].color,
      score: val.score ?? null,
      weight: Math.round((val.weight ?? 0) * 100),
    }));
});

const probeModels = computed(() => {
  const detail = unified.value?.components?.ai_search_probes?.detail;
  const models = (detail?.models || []) as ProbeModel[];
  return Array.isArray(models) ? models : [];
});

function previewUrl(path: string) {
  const domain = dash.value?.tenant_domain || 'dev.local';
  if (path.startsWith('http')) return path;
  return `http://127.0.0.1:3000${path.startsWith('/') ? path : `/${path}`}`;
}

function probeColor(status?: string) {
  return (
    { indexed: 'green', partial: 'orange', not_indexed: 'red', not_configured: 'default', error: 'red' }[
      status || ''
    ] || 'default'
  );
}

function probeLabel(status?: string) {
  return (
    {
      indexed: '已提及',
      partial: '部分',
      not_indexed: '未提及',
      not_configured: '未接通',
      error: '错误',
    }[status || ''] || status || '—'
  );
}

onMounted(async () => {
  loading.value = true;
  try {
    const [dashRes, unifiedRes, gscRes] = await Promise.allSettled([
      fetchGeoVisibilityDashboard(),
      fetchUnifiedGeoScore(false),
      apiGet<GscAdsStatus>('/foreign-trade/attribution/gsc-ads-status'),
    ]);
    if (dashRes.status === 'fulfilled') dash.value = dashRes.value;
    if (unifiedRes.status === 'fulfilled') unified.value = unifiedRes.value;
    if (gscRes.status === 'fulfilled') gscStatus.value = gscRes.value;
  } finally {
    loading.value = false;
  }
});
</script>
