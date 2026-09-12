<template>
  <YdPage
    title="增长工具"
    subtitle="热门关键词 · 内容质检 · AI 引流监测 · 智能跑盘"
    surface="elevated"
  >
    <template #actions>
      <a-button @click="refreshAll">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新
      </a-button>
    </template>

    <a-tabs v-model:activeKey="activeTool" class="growth-tools-tabs" :destroy-inactive-tab-pane="false">
      <!-- 总览 -->
      <a-tab-pane key="overview" tab="总览">
        <div class="space-y-6 growth-tools-pane">
          <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="stat-card bg-white border border-gray-100">
              <p class="text-sm text-gray-500">热词合计</p>
              <p class="text-2xl font-bold mt-1">{{ dashboard.keywords?.total ?? 0 }}</p>
            </div>
            <div class="stat-card bg-white border border-gray-100">
              <p class="text-sm text-gray-500">专属词库</p>
              <p class="text-2xl font-bold mt-1">{{ dashboard.keywords?.library_count ?? 0 }}</p>
            </div>
            <div class="stat-card bg-white border border-gray-100">
              <p class="text-sm text-gray-500">监测通道</p>
              <p class="text-2xl font-bold mt-1">{{ dashboard.traffic?.platforms ?? 0 }}</p>
            </div>
            <div class="stat-card bg-white border border-gray-100">
              <p class="text-sm text-gray-500">API 探针</p>
              <p class="text-2xl font-bold mt-1">{{ dashboard.traffic?.probe_ready ?? 0 }}</p>
            </div>
            <div class="stat-card bg-white border border-gray-100">
              <p class="text-sm text-gray-500">待接入</p>
              <p class="text-2xl font-bold mt-1 text-amber-600">{{ dashboard.traffic_idle_count ?? 0 }}</p>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div class="bg-white rounded-2xl shadow-card p-6">
              <h3 class="text-lg font-semibold mb-4">快捷入口</h3>
              <div class="flex flex-wrap gap-2">
                <a-button type="primary" @click="activeTool = 'autopilot'">智能跑盘</a-button>
                <a-button @click="activeTool = 'traffic'">引流监测</a-button>
                <a-button @click="activeTool = 'quality'">内容质检</a-button>
                <a-button @click="activeTool = 'keywords'">热词库</a-button>
              </div>
              <a-alert
                v-if="dashboard.last_agent_run"
                class="mt-4"
                type="info"
                show-icon
                :message="`最近跑盘：${dashboard.last_agent_run.focus_keyword || '—'} · ${dashboard.last_agent_run.status}`"
              />
            </div>
            <div class="bg-white rounded-2xl shadow-card p-6">
              <h3 class="text-lg font-semibold mb-4">跑盘预设</h3>
              <div class="space-y-2">
                <div
                  v-for="p in dashboard.presets || []"
                  :key="p.id"
                  class="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer"
                  @click="startPresetFromOverview(p)"
                >
                  <div>
                    <p class="font-medium text-gray-900">{{ p.label }}</p>
                    <p class="text-xs text-gray-400">{{ p.hint }}</p>
                  </div>
                  <span class="text-primary-600 text-sm">开始 →</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- 热门关键词 -->
      <a-tab-pane key="keywords" tab="热门关键词">
        <div class="space-y-6 growth-tools-pane">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div
              v-for="wc in wordClasses"
              :key="wc"
              class="stat-card bg-white border border-gray-100"
            >
              <p class="text-sm text-gray-500">
                {{ classLabels[wc] || wc }}
              </p>
              <p class="text-2xl font-bold text-gray-900 mt-1">
                {{ hotTotals[wc] ?? 0 }}
              </p>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div
              v-for="wc in wordClasses"
              :key="`bucket-${wc}`"
              class="bg-white rounded-2xl shadow-card p-5"
            >
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-base font-semibold text-gray-900">
                  {{ classLabels[wc] }}
                </h3>
                <a-tag color="blue">
                  {{ (hotBuckets[wc] || []).length }} 条
                </a-tag>
              </div>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="(item, idx) in hotBuckets[wc] || []"
                  :key="`${wc}-${idx}`"
                  class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                  @click="useKeywordInAutopilot(item.keyword)"
                >
                  <span class="text-sm text-gray-800 truncate flex-1 mr-2">{{
                    item.keyword
                  }}</span>
                  <span class="text-xs text-gray-400 shrink-0">{{
                    item.search_volume || '-'
                  }}</span>
                </div>
                <p
                  v-if="!(hotBuckets[wc] || []).length"
                  class="text-sm text-gray-400 text-center py-6"
                >
                  暂无数据，可在下方专属词库添加
                </p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-2xl shadow-card p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">
                专属词库
              </h3>
              <a-button type="primary" size="small" @click="showAddKeyword = true">
                <PlusOutlined class="w-4 h-4 mr-1" />
                添加关键词
              </a-button>
            </div>
            <a-table
              :columns="libraryColumns"
              :data-source="libraryItems"
              :loading="libraryLoading"
              row-key="id"
              size="small"
              :pagination="{ pageSize: 10 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'word_class'">
                  <a-tag>{{ record.word_class_label || record.word_class }}</a-tag>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-popconfirm
                    title="确定删除该关键词？"
                    @confirm="removeKeyword(record.id)"
                  >
                    <a-button type="link" size="small" danger>
                      删除
                    </a-button>
                  </a-popconfirm>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </a-tab-pane>

      <!-- 内容质检 -->
      <a-tab-pane key="quality" tab="内容质检">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 growth-tools-pane">
          <div class="bg-white rounded-2xl shadow-card p-6 space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">
              待检内容
            </h3>
            <a-input v-model:value="inspectForm.title" placeholder="标题（可选）" />
            <a-textarea
              v-model:value="inspectForm.body"
              placeholder="粘贴正文，至少 10 字"
              :rows="12"
            />
            <a-input
              v-model:value="inspectKeywordsText"
              placeholder="目标关键词，逗号分隔（可选）"
            />
            <a-button
              type="primary"
              block
              :loading="inspectLoading"
              @click="runInspect"
            >
              <SafetyCertificateOutlined class="w-4 h-4 mr-2" />
              开始质检
            </a-button>
          </div>

          <div class="bg-white rounded-2xl shadow-card p-6">
            <div v-if="!inspectReport" class="text-center text-gray-400 py-16">
              填写内容后点击「开始质检」查看报告
            </div>
            <div v-else class="space-y-4">
              <div class="flex items-center gap-4">
                <div
                  :class="[
                    'w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold',
                    inspectReport.passed
                      ? 'bg-success-50 text-success-600'
                      : 'bg-warning-50 text-warning-600',
                  ]"
                >
                  {{ inspectReport.grade }}
                </div>
                <div>
                  <p class="text-lg font-semibold">
                    {{ inspectReport.summary }}
                  </p>
                  <p class="text-sm text-gray-500">
                    SEO {{ inspectReport.seo?.total_score ?? '-' }}/100 · 逻辑
                    {{ Math.round((inspectReport.logic?.score ?? 0) * 100) }}%
                  </p>
                </div>
              </div>

              <a-alert
                v-if="inspectReport.blockers?.length"
                type="warning"
                show-icon
                :message="'需处理 ' + inspectReport.blockers.length + ' 项'"
              >
                <template #description>
                  <ul class="list-disc pl-4 mt-1">
                    <li v-for="(b, i) in inspectReport.blockers" :key="i">
                      {{ b }}
                    </li>
                  </ul>
                </template>
              </a-alert>

              <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">
                    合规问题
                  </p>
                  <p class="font-semibold mt-1">
                    {{ inspectReport.compliance?.total_issues ?? 0 }}
                    <span class="text-xs text-gray-400">
                      （高风险 {{ inspectReport.compliance?.high_severity_count ?? 0 }}）
                    </span>
                  </p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">
                    GEO/AI 适配
                  </p>
                  <p class="font-semibold mt-1">
                    {{ inspectReport.geo_ai?.passed ? '通过' : '未达标' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- AI 引流监测 -->
      <a-tab-pane key="traffic" tab="AI 引流监测">
        <div class="space-y-6 growth-tools-pane">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
              <p class="text-primary-100 text-sm">
                监测平台
              </p>
              <p class="text-3xl font-bold mt-2">
                {{ trafficSummary.platforms ?? 0 }}
              </p>
            </div>
            <div class="stat-card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <p class="text-purple-100 text-sm">
                AI 平台
              </p>
              <p class="text-3xl font-bold mt-2">
                {{ trafficSummary.ai_platforms ?? 0 }}
              </p>
            </div>
            <div class="stat-card bg-gradient-to-br from-success-500 to-success-600 text-white">
              <p class="text-success-100 text-sm">
                已收录 URL
              </p>
              <p class="text-3xl font-bold mt-2">
                {{ trafficSummary.indexed_urls ?? 0 }}
              </p>
            </div>
            <div class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <p class="text-blue-100 text-sm">
                整体收录率
              </p>
              <p class="text-3xl font-bold mt-2">
                {{ trafficSummary.overall_inclusion_rate ?? 0 }}%
              </p>
            </div>
          </div>

          <a-alert
            v-if="trafficNote"
            type="info"
            show-icon
            :message="trafficNote"
          />

          <div class="bg-white rounded-2xl shadow-card p-5 border border-gray-100">
            <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h3 class="text-base font-semibold text-gray-900 mb-1">
                  {{ domesticCrawl.title || '百度收录探针' }}
                </h3>
                <p class="text-sm text-gray-500">
                  {{ domesticCrawl.hint || '输入关键词即可检测；未部署采集服务时会如实提示，不会假数据。' }}
                </p>
              </div>
              <a-tag :color="domesticCrawlTagColor">
                {{ domesticCrawl.status || '未接入' }}
              </a-tag>
            </div>
            <div class="flex flex-col sm:flex-row gap-3">
              <a-input
                v-model:value="baiduKeyword"
                :placeholder="domesticCrawl.placeholder_keyword || '输入关键词'"
                class="flex-1"
                @press-enter="runBaiduProbe"
              />
              <a-button type="primary" :loading="baiduProbeLoading" @click="runBaiduProbe">
                测百度收录
              </a-button>
            </div>
            <a-alert
              v-if="baiduProbeResult"
              class="mt-4"
              :type="baiduProbeResult.ok ? 'success' : 'warning'"
              show-icon
              :message="baiduProbeResult.message_zh || (baiduProbeResult.ok ? '检测完成' : '未能完成检测')"
            >
              <template v-if="baiduProbeResult.ok && baiduProbeResult.evidence_url" #description>
                <a :href="baiduProbeResult.evidence_url" target="_blank" rel="noopener">
                  打开核对链接
                </a>
                <span v-if="baiduProbeResult.human_review_required" class="ml-2 text-amber-600">
                  · 结果须人工核实
                </span>
              </template>
            </a-alert>
          </div>

          <div class="bg-white rounded-2xl shadow-card p-5 border border-gray-100">
            <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h3 class="text-base font-semibold text-gray-900 mb-1">
                  {{ behaviorAnalytics.title || '页面转化分析' }}
                </h3>
                <p class="text-sm text-gray-500">
                  {{ behaviorAnalytics.hint || 'Spark 单跳转化率；未部署时如实提示，不伪造漏斗数据。' }}
                </p>
              </div>
              <a-tag :color="behaviorAnalyticsTagColor">
                {{ behaviorAnalytics.status || '未接入' }}
              </a-tag>
            </div>
            <div class="flex flex-col sm:flex-row gap-3">
              <a-input
                v-model:value="conversionSite"
                placeholder="站点域名，例如 example.com（可选）"
                class="flex-1"
                @press-enter="runConversionProbe"
              />
              <a-button type="primary" :loading="conversionProbeLoading" @click="runConversionProbe">
                查页面转化
              </a-button>
            </div>
            <a-alert
              v-if="conversionProbeResult"
              class="mt-4"
              :type="conversionProbeResult.ok ? 'success' : 'warning'"
              show-icon
              :message="conversionProbeResult.message_zh || (conversionProbeResult.ok ? '分析完成' : '未能完成分析')"
            >
              <template v-if="conversionProbeResult.ok && conversionProbeResult.items?.length" #description>
                <ul class="list-disc pl-4 mb-0 text-sm">
                  <li
                    v-for="(row, idx) in conversionProbeResult.items.slice(0, 5)"
                    :key="idx"
                  >
                    {{ row.from_page || '—' }} → {{ row.to_page || '—' }}
                    <span v-if="row.conversion_rate != null">
                      · {{ Math.round(Number(row.conversion_rate) * 1000) / 10 }}%
                    </span>
                  </li>
                </ul>
              </template>
            </a-alert>
          </div>

          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-0">
              AI 搜索 / 对话平台
              <span class="text-sm font-normal text-gray-400 ml-2">{{ filteredAiPlatforms.length }} 个</span>
            </h3>
            <a-radio-group v-model:value="trafficFilter" size="small">
              <a-radio-button value="all">全部</a-radio-button>
              <a-radio-button value="ready">已接探针</a-radio-button>
              <a-radio-button value="active">有数据</a-radio-button>
              <a-radio-button value="idle">待接入</a-radio-button>
            </a-radio-group>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="card in filteredAiPlatforms"
              :key="card.engine_id"
              class="bg-white rounded-xl shadow-card p-4 border border-gray-100"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="font-medium text-gray-900">{{ card.name }}</span>
                <a-tag :color="trafficTagColor(card)">
                  {{ trafficTagLabel(card) }}
                </a-tag>
              </div>
              <p class="text-sm text-gray-500 mt-2">
                收录 {{ card.inclusion_included }}/{{ card.inclusion_total }}
                · {{ card.inclusion_rate }}%
              </p>
              <div v-if="card.top_rankings?.length" class="mt-3 space-y-1">
                <p
                  v-for="(r, i) in card.top_rankings.slice(0, 3)"
                  :key="i"
                  class="text-xs text-gray-600 truncate"
                >
                  #{{ r.rank || '-' }} {{ r.keyword }}
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              国内搜索引擎
              <span class="text-sm font-normal text-gray-400 ml-2">
                {{ domesticSearchPlatforms.length }} 个通道
              </span>
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
              <div
                v-for="card in domesticSearchPlatforms"
                :key="card.engine_id"
                class="bg-white rounded-xl shadow-card p-4 border border-gray-100"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="font-medium text-gray-900">{{ card.name }}</span>
                  <a-tag :color="trafficTagColor(card)">
                    {{ trafficTagLabel(card) }}
                  </a-tag>
                </div>
                <p class="text-xs text-gray-400 mt-1">
                  {{ card.inclusion_included }}/{{ card.inclusion_total }} URL · {{ card.inclusion_rate }}%
                </p>
              </div>
            </div>

            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              出海搜索引擎
              <span class="text-sm font-normal text-gray-400 ml-2">
                {{ globalSearchPlatforms.length }} 个通道
              </span>
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div
                v-for="card in globalSearchPlatforms"
                :key="card.engine_id"
                class="bg-white rounded-xl shadow-card p-4 border border-gray-100"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="font-medium text-gray-900">{{ card.name }}</span>
                  <a-tag :color="trafficTagColor(card)">
                    {{ trafficTagLabel(card) }}
                  </a-tag>
                </div>
                <p class="text-xs text-gray-400 mt-1">
                  {{ card.inclusion_included }}/{{ card.inclusion_total }} URL · {{ card.inclusion_rate }}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- 智能跑盘 -->
      <a-tab-pane key="autopilot" tab="智能跑盘">
        <GrowthAutopilotPanel
          ref="autopilotRef"
          @apply-inspect="onApplyInspectFromAgent"
          @completed="onAgentCompleted"
        />
      </a-tab-pane>
    </a-tabs>

    <a-modal
      v-model:open="showAddKeyword"
      title="添加专属关键词"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="addKeywordLoading"
      @ok="submitKeyword"
    >
      <div class="space-y-4 py-2">
        <a-input v-model:value="keywordForm.keyword" placeholder="关键词" />
        <a-select v-model:value="keywordForm.word_class" class="w-full">
          <a-select-option value="industry">
            行业词
          </a-select-option>
          <a-select-option value="brand">
            品牌词
          </a-select-option>
          <a-select-option value="competitor">
            竞品词
          </a-select-option>
          <a-select-option value="demand">
            需求词
          </a-select-option>
        </a-select>
        <a-input-number
          v-model:value="keywordForm.search_volume"
          class="w-full"
          :min="0"
          placeholder="搜索量（可选）"
        />
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ReloadOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import GrowthAutopilotPanel from '@/components/growth/GrowthAutopilotPanel.vue';
import { growthToolsAPI, unwrapApiData } from '@/api';

const activeTool = ref('overview');
const autopilotRef = ref<InstanceType<typeof GrowthAutopilotPanel> | null>(null);
const dashboard = ref<Record<string, any>>({});
const trafficFilter = ref<'all' | 'ready' | 'active' | 'idle'>('all');

const wordClasses = ref<string[]>(['industry', 'brand', 'competitor', 'demand']);
const classLabels = ref<Record<string, string>>({});
const hotBuckets = ref<Record<string, Array<{ keyword: string; search_volume?: number }>>>({});
const hotTotals = ref<Record<string, number>>({});

const libraryItems = ref<any[]>([]);
const libraryLoading = ref(false);
const libraryColumns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
  { title: '分类', key: 'word_class', width: 100 },
  { title: '搜索量', dataIndex: 'search_volume', key: 'search_volume', width: 90 },
  { title: '来源', dataIndex: 'source', key: 'source', width: 90 },
  { title: '操作', key: 'actions', width: 80 },
];

const showAddKeyword = ref(false);
const addKeywordLoading = ref(false);
const keywordForm = reactive({
  keyword: '',
  word_class: 'industry',
  search_volume: 0,
});

const inspectForm = reactive({ title: '', body: '' });
const inspectKeywordsText = ref('');
const inspectLoading = ref(false);
const inspectReport = ref<any>(null);

const trafficSummary = ref<Record<string, number>>({});
const aiPlatforms = ref<any[]>([]);
const searchPlatforms = ref<any[]>([]);
const domesticSearchPlatforms = ref<any[]>([]);
const globalSearchPlatforms = ref<any[]>([]);
const trafficNote = ref('');
const domesticCrawl = ref<Record<string, any>>({});
const baiduKeyword = ref('');
const baiduProbeLoading = ref(false);
const baiduProbeResult = ref<Record<string, any> | null>(null);
const behaviorAnalytics = ref<Record<string, any>>({});
const conversionSite = ref('');
const conversionProbeLoading = ref(false);
const conversionProbeResult = ref<Record<string, any> | null>(null);

const domesticCrawlTagColor = computed(() => {
  const s = domesticCrawl.value?.status;
  if (s === '已就绪') return 'green';
  if (s === '不可达') return 'orange';
  return 'default';
});

const behaviorAnalyticsTagColor = computed(() => {
  const s = behaviorAnalytics.value?.status;
  if (s === '已就绪') return 'green';
  if (s === '不可达') return 'orange';
  return 'default';
});

function filterTrafficCards(cards: any[]) {
  const f = trafficFilter.value;
  if (f === 'all') return cards;
  if (f === 'ready') return cards.filter((c) => c.probe_ready);
  if (f === 'active') return cards.filter((c) => c.traffic_signal !== 'idle');
  return cards.filter((c) => c.traffic_signal === 'idle');
}

const filteredAiPlatforms = computed(() => filterTrafficCards(aiPlatforms.value));

async function fetchDashboard() {
  try {
    const res = await growthToolsAPI.getDashboard();
    dashboard.value = unwrapApiData(res) || {};
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
  }
}

function useKeywordInAutopilot(keyword: string) {
  activeTool.value = 'autopilot';
  autopilotRef.value?.fillFromKeyword(keyword);
  message.info(`已选词「${keyword}」`);
}

function startPresetFromOverview(preset: { id: string; goal: string; mode?: string }) {
  activeTool.value = 'autopilot';
  autopilotRef.value?.applyPreset(preset as any);
}

function onApplyInspectFromAgent(payload: {
  draft?: { title?: string; body?: string };
  report?: Record<string, unknown>;
  focusKeyword?: string;
}) {
  if (payload.draft?.title) inspectForm.title = payload.draft.title;
  if (payload.draft?.body) inspectForm.body = payload.draft.body;
  if (payload.report) inspectReport.value = payload.report;
  if (payload.focusKeyword) inspectKeywordsText.value = payload.focusKeyword;
  activeTool.value = 'quality';
  message.success('已同步到内容质检');
}

function onAgentCompleted() {
  // 跑盘结束后静默刷新，避免其它 Tab 被周期性 loading 打断
  if (activeTool.value === 'overview') void fetchDashboard();
  if (activeTool.value === 'keywords') {
    void Promise.all([fetchHotKeywords(), fetchLibrary(true)]);
  }
  if (activeTool.value === 'traffic') void fetchTraffic();
}

function stopAutopilotPoll() {
  autopilotRef.value?.stopPoll?.();
}

onBeforeRouteLeave(() => {
  stopAutopilotPoll();
});

onBeforeUnmount(() => {
  stopAutopilotPoll();
});

function trafficTagLabel(card: {
  traffic_signal?: string;
  probe_status_label?: string;
}): string {
  if (card.traffic_signal === 'indexed') return '已收录';
  if (card.traffic_signal === 'tracking') return '追踪中';
  return card.probe_status_label || '待接入';
}

function trafficTagColor(card: {
  traffic_signal?: string;
  probe_ready?: boolean;
}): string {
  if (card.traffic_signal === 'indexed') return 'green';
  if (card.traffic_signal === 'tracking') return 'blue';
  // 禁止 processing：Ant Tag 自带脉冲动画，20 张卡片会整页爆闪
  if (card.probe_ready) return 'cyan';
  return 'default';
}

async function fetchHotKeywords() {
  try {
    const res = await growthToolsAPI.getHotKeywords();
    const data = unwrapApiData<any>(res);
    wordClasses.value = data?.classes || wordClasses.value;
    classLabels.value = data?.class_labels || {};
    hotBuckets.value = data?.buckets || {};
    hotTotals.value = data?.totals || {};
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
    message.error('加载热门关键词失败');
  }
}

async function fetchLibrary(silent = false) {
  if (!silent) libraryLoading.value = true;
  try {
    const res = await growthToolsAPI.getKeywordLibrary();
    const data = unwrapApiData<{ items?: any[] }>(res);
    libraryItems.value = data?.items || [];
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
  } finally {
    if (!silent) libraryLoading.value = false;
  }
}

async function submitKeyword() {
  if (!keywordForm.keyword.trim()) {
    message.warning('请输入关键词');
    return;
  }
  addKeywordLoading.value = true;
  try {
    await growthToolsAPI.addKeyword({
      keyword: keywordForm.keyword.trim(),
      word_class: keywordForm.word_class,
      search_volume: keywordForm.search_volume || 0,
    });
    message.success('已加入词库');
    showAddKeyword.value = false;
    keywordForm.keyword = '';
    await Promise.all([fetchLibrary(), fetchHotKeywords()]);
  } catch (e: any) {
    message.error(e?.response?.data?.message || '添加失败');
  } finally {
    addKeywordLoading.value = false;
  }
}

async function removeKeyword(id: string) {
  try {
    await growthToolsAPI.deleteKeyword(id);
    message.success('已删除');
    await Promise.all([fetchLibrary(), fetchHotKeywords()]);
  } catch {
    message.error('删除失败');
  }
}

async function runInspect() {
  if ((inspectForm.body || '').trim().length < 10) {
    message.warning('正文至少 10 字');
    return;
  }
  inspectLoading.value = true;
  try {
    const keywords = inspectKeywordsText.value
      .split(/[,，]/)
      .map((s) => s.trim())
      .filter(Boolean);
    const res = await growthToolsAPI.inspectContent({
      title: inspectForm.title,
      body: inspectForm.body,
      keywords,
    });
    inspectReport.value = unwrapApiData(res);
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
    message.error('质检失败');
  } finally {
    inspectLoading.value = false;
  }
}

async function fetchTraffic() {
  try {
    const res = await growthToolsAPI.getAiTrafficOverview();
    const data = unwrapApiData<any>(res);
    trafficSummary.value = data?.summary || {};
    domesticCrawl.value = data?.domestic_crawl || {};
    behaviorAnalytics.value = data?.behavior_analytics || {};
    aiPlatforms.value = data?.ai_platforms || [];
    const search = data?.search_platforms || [];
    searchPlatforms.value = search;
    domesticSearchPlatforms.value =
      data?.search_platforms_domestic ||
      search.filter((c: { market?: string }) => c.market === 'domestic');
    globalSearchPlatforms.value =
      data?.search_platforms_global ||
      search.filter((c: { market?: string }) => c.market === 'global');
    trafficNote.value = data?.note || '';
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
    message.error('加载引流监测失败');
  }
}

async function runBaiduProbe() {
  const kw = baiduKeyword.value.trim();
  if (!kw) {
    message.warning('请先输入关键词');
    return;
  }
  baiduProbeLoading.value = true;
  baiduProbeResult.value = null;
  try {
    const res = await growthToolsAPI.runBaiduProbe({ keyword: kw });
    const data = unwrapApiData<any>(res);
    baiduProbeResult.value = { ok: true, ...data };
  } catch (e: any) {
    const msg =
      e?.response?.data?.message ||
      e?.message ||
      '采集服务未配置或暂不可用';
    baiduProbeResult.value = { ok: false, message_zh: msg };
  } finally {
    baiduProbeLoading.value = false;
  }
}

async function runConversionProbe() {
  conversionProbeLoading.value = true;
  conversionProbeResult.value = null;
  try {
    const site = conversionSite.value.trim();
    const res = await growthToolsAPI.runConversionProbe(site ? { site } : {});
    const data = unwrapApiData<any>(res);
    conversionProbeResult.value = { ok: true, ...data };
  } catch (e: any) {
    const msg =
      e?.response?.data?.message ||
      e?.message ||
      '行为分析服务未配置或暂不可用';
    conversionProbeResult.value = { ok: false, message_zh: msg };
  } finally {
    conversionProbeLoading.value = false;
  }
}

function refreshAll() {
  fetchDashboard();
  fetchHotKeywords();
  fetchLibrary();
  fetchTraffic();
}

onMounted(() => {
  refreshAll();
});
</script>

<style scoped>
/* ANTI-FLASH 硬约束：勿恢复 animate-fade-in、processing 标签、双进度条、1s 无脑轮询 */
.growth-tools-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}
.growth-tools-tabs :deep(.ant-tag-processing),
.growth-tools-tabs :deep(.ant-tag-processing::before),
.growth-tools-tabs :deep(.ant-progress-status-active .ant-progress-bg::before),
.growth-tools-tabs :deep(.ant-steps-item-process .ant-steps-item-icon > .ant-steps-icon) {
  animation: none !important;
}
.growth-tools-pane {
  min-height: 1px;
  contain: layout style;
}
.stat-card {
  @apply rounded-2xl p-5 relative overflow-hidden;
}
</style>
