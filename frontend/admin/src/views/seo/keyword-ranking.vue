/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="keyword-ranking-page" title="关键词排名追踪" subtitle="追踪关键词在搜索引擎中的排名变化" surface="elevated">
    <YdHonestDataBanner
      v-if="dataTrust === 'mock'"
      level="mock"
      description="当前列表为接口失败时的降级示例，排名位次不可报给客户。请检查登录状态或稍后重试「更新排名」。"
    />
    <YdHonestDataBanner
      v-else-if="hasSimulatedRank"
      level="partial"
      title="部分排名为模拟探测"
      description="百度反爬或解析失败时，后端会标记 is_simulated。请以百度站长后台为准。"
    />
    <template #actions>
      <a-space>
        <a-button
          type="primary"
          @click="showImportModal = true"
        >
          <template #icon>
            <PlusOutlined />
          </template>
          导入关键词
        </a-button>
        <a-button
          @click="refreshRankings"
          :loading="tracking"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          更新排名
        </a-button>
      </a-space>
    </template>

    <!-- 仪表盘卡片 -->
    <a-row
      :gutter="16"
      class="dashboard-cards"
    >
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="追踪关键词"
            :value="summary.total_keywords"
            suffix="个"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="前10名"
            :value="summary.top_10"
            suffix="个"
            :value-style="{ color: ' #3f8600' }"
          >
            <template #prefix>
              <TrophyOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="排名提升"
            :value="summary.improved"
            suffix="个"
            :value-style="{ color: ' #3f8600' }"
          >
            <template #prefix>
              <ArrowUpOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="平均排名"
            :value="summary.avg_position"
            :precision="1"
            suffix="位"
          >
            <template #prefix>
              <BarChartOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选器 -->
    <a-card class="filter-card">
      <a-form layout="inline">
        <a-form-item label="搜索引擎">
          <a-select
            v-model:value="filters.search_engine"
            style="width: 150px"
            allow-clear
          >
            <a-select-option value="baidu">
              百度
            </a-select-option>
            <a-select-option value="360">
              360
            </a-select-option>
            <a-select-option value="sogou">
              搜狗
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="分类">
          <a-input
            v-model:value="filters.category"
            placeholder="输入分类"
            style="width: 150px"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            @click="loadKeywords"
          >
            查询
          </a-button>
          <a-button
            style="margin-left: 8px"
            @click="resetFilters"
          >
            重置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 关键词表格（多榜单 Tab） -->
    <a-card class="table-card">
      <a-tabs
        v-model:active-key="boardTab"
        class="leaderboard-tabs"
        @change="onBoardTabChange"
      >
        <a-tab-pane
          key="all"
          tab="全部榜单"
        />
        <a-tab-pane
          key="top10"
          tab="前十榜单"
        />
        <a-tab-pane
          key="improved"
          tab="进步榜"
        />
        <a-tab-pane
          key="pending"
          tab="待收录"
        />
      </a-tabs>
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="loadKeywords" />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="filteredKeywords"
          :loading="loading"
          :pagination="mergedPagination"
          :table-props="{ size: tableSize, rowKey: 'id' }"
          @page-change="onPageChange"
        >
          <!-- 排名列 -->
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'current_position'">
              <a-tag
                v-if="record.current_position"
                :color="getPositionColor(record.current_position)"
              >
                第{{ record.current_position }}名
              </a-tag>
              <span
                v-else
                class="text-muted"
              >未收录</span>
            </template>

            <!-- 排名变化 -->
            <template v-else-if="column.key === 'position_change'">
              <span
                v-if="record.previous_position"
                :class="getPositionChangeClass(record)"
              >
                <ArrowUpOutlined v-if="record.position_improved()" />
                <ArrowDownOutlined v-else-if="record.position_declined()" />
                <MinusOutlined v-else />
                {{ record.position_change() }}
              </span>
              <span v-else>-</span>
            </template>

            <!-- 搜索量 -->
            <template v-else-if="column.key === 'search_volume'">
              {{ record.search_volume != null ? record.search_volume : '-' }}
            </template>

            <!-- 最后更新 -->
            <template v-else-if="column.key === 'last_checked_at'">
              {{ formatDateTime(record.last_checked_at) }}
            </template>

            <!-- 难度 -->
            <template v-else-if="column.key === 'difficulty'">
              <a-badge
                :status="getDifficultyStatus(record.difficulty)"
                :text="record.difficulty"
              />
            </template>

            <!-- 操作 -->
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  @click="viewHistory(record)"
                >
                  历史
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click="editKeyword(record)"
                >
                  编辑
                </a-button>
                <a-popconfirm
                  title="确定删除?"
                  @confirm="deleteKeyword(record.id)"
                >
                  <a-button
                    type="link"
                    danger
                    size="small"
                  >
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>

    <!-- 导入关键词弹窗 -->
    <a-modal
      v-model:open="showImportModal"
      title="导入关键词"
      width="600px"
      @ok="importKeywords"
    >
      <a-alert
        message="将导入河北廊坊·大城保温建材产业带默认关键词（岩棉、玻璃棉、橡塑等）"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-textarea
        v-model:value="importText"
        placeholder="每行一个关键词，例如：&#10;轻集料混凝土&#10;LC5.0轻集料混凝土&#10;轻质混凝土"
        :rows="10"
      />
      <div class="import-tip">
        提示：留空将导入默认关键词列表（{{ defaultKeywords.length }}个）
      </div>
    </a-modal>

    <!-- 编辑关键词 -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑关键词"
      ok-text="保存"
      destroy-on-close
      :confirm-loading="editSaving"
      @ok="submitKeywordEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="关键词">
          <a-input
            v-model:value="editForm.keyword"
            placeholder="关键词文本"
          />
        </a-form-item>
        <a-form-item label="分类">
          <a-input
            v-model:value="editForm.category"
            placeholder="可选"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 排名历史弹窗 -->
    <a-modal
      v-model:open="showHistoryModal"
      title="排名历史"
      width="700px"
      :footer="null"
    >
      <v-chart
        v-if="historyData.length"
        :option="chartOption"
        style="height: 300px"
      />
      <a-empty
        v-else
        description="暂无历史数据"
      />
    </a-modal>
  </YdPage>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { message } from 'ant-design-vue';
import { YdDataTable, YdPage, YdTableToolbar, YdHonestDataBanner } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import {
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  TrophyOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  BarChartOutlined,
} from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import { applySnapCursor } from '@/composables/useChartCursor';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components';
import { unwrapFetchedJson } from '@/api';
import { getAuthToken } from '@/utils/api';

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent]);

const tablePanelRef = ref(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);

// API请求函数
const apiBase = '/api/v1/seo/keywords';

function authHeaders(extra = {}) {
  const tk = getAuthToken();
  return {
    ...(tk ? { Authorization: `Bearer ${tk}` } : {}),
    ...extra,
  };
}

function formatDateTime(value) {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function recomputeSummaryFromKeywords(list) {
  const withPos = list.filter((k) => k.current_position != null);
  const top10 = withPos.filter((k) => Number(k.current_position) <= 10);
  const improved = list.filter((k) => k.position_improved());
  const declined = list.filter((k) => k.position_declined());
  summary.value = {
    total_keywords: list.length,
    top_10: top10.length,
    top_50: withPos.filter((k) => Number(k.current_position) <= 50).length,
    improved: improved.length,
    declined: declined.length,
    avg_position: withPos.length
      ? +(withPos.reduce((s, k) => s + Number(k.current_position), 0) / withPos.length).toFixed(1)
      : 0,
  };
}

// 状态
const loading = ref(false);
const tracking = ref(false);
const keywords = ref([]);
const dataTrust = ref('live');
const hasSimulatedRank = ref(false);

/** 已移除 mock 榜单：API 不可用时仅展示空表 */
/** 榜单 Tab：all | top10 | improved | pending */
const boardTab = ref('all');
const summary = ref({
  total_keywords: 0,
  top_10: 0,
  top_50: 0,
  improved: 0,
  declined: 0,
  avg_position: 0,
});

const filters = reactive({
  search_engine: undefined,
  category: undefined,
});

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`,
});

function wrapKeyword(r) {
  const base = { ...r };
  return {
    ...base,
    position_change() {
      if (typeof base.position_change === 'function') {
        const raw = base.position_change();
        const n = typeof raw === 'number' ? raw : Number(raw);
        return Number.isFinite(n) ? Math.abs(n) : 0;
      }
      const prev = base.previous_position;
      const cur = base.current_position;
      if (prev == null || cur == null) return 0;
      return Math.abs(Number(prev) - Number(cur));
    },
    position_improved() {
      if (typeof base.position_improved === 'function') return !!base.position_improved();
      const prev = base.previous_position;
      const cur = base.current_position;
      return prev != null && cur != null && Number(cur) < Number(prev);
    },
    position_declined() {
      if (typeof base.position_declined === 'function') return !!base.position_declined();
      const prev = base.previous_position;
      const cur = base.current_position;
      return prev != null && cur != null && Number(cur) > Number(prev);
    },
  };
}

const filteredKeywords = computed(() => {
  const list = keywords.value;
  if (boardTab.value === 'top10') {
    return list.filter((k) => k.current_position && Number(k.current_position) <= 10);
  }
  if (boardTab.value === 'improved') {
    return list.filter((k) => k.position_improved());
  }
  if (boardTab.value === 'pending') {
    return list.filter((k) => !k.current_position);
  }
  return list;
});

const mergedPagination = computed(() => ({
  current: pagination.current,
  pageSize: pagination.pageSize,
  total: filteredKeywords.value.length,
  showSizeChanger: pagination.showSizeChanger,
  showTotal: pagination.showTotal,
}));

function onBoardTabChange() {
  pagination.current = 1;
}

const showImportModal = ref(false);
const importText = ref('');
const defaultKeywords = [
  '轻集料混凝土',
  'LC5.0轻集料混凝土',
  'LC7.5轻集料混凝土',
  'LC10轻集料混凝土',
  'LC15轻集料混凝土',
  'LC20轻集料混凝土',
  '轻质混凝土',
  '泡沫混凝土',
  '陶粒混凝土',
  '保温混凝土',
];

const showHistoryModal = ref(false);
const historyData = ref([]);
const currentKeyword = ref(null);

const showEditModal = ref(false);
const editSaving = ref(false);
const editingRecord = ref(null);
const editForm = reactive({
  keyword: '',
  category: '',
});

// 表格列定义
const columns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword', width: 200 },
  { title: '搜索引擎', dataIndex: 'search_engine', key: 'search_engine', width: 100 },
  { title: '当前排名', key: 'current_position', width: 100 },
  { title: '变化', key: 'position_change', width: 80 },
  { title: '最佳排名', dataIndex: 'best_position', key: 'best_position', width: 100 },
  { title: '搜索量', dataIndex: 'search_volume', key: 'search_volume', width: 100 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
  { title: '最后更新', dataIndex: 'last_checked_at', key: 'last_checked_at', width: 160 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' },
];

// 图表配置
const chartOption = computed(() => applySnapCursor({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: historyData.value.map((h) => h.date),
  },
  yAxis: {
    type: 'value',
    inverse: true,
    min: 1,
    max: 100,
  },
  series: [
    {
      name: '排名',
      type: 'line',
      data: historyData.value.map((h) => h.position),
      smooth: true,
      lineStyle: { color: '#1890ff' },
      areaStyle: { color: 'rgba(24, 144, 255, 0.1)' },
    },
  ],
}));

// 方法
const loadKeywords = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      skip: String((pagination.current - 1) * pagination.pageSize),
      limit: String(pagination.pageSize),
    });

    if (filters.search_engine) params.append('search_engine', filters.search_engine);
    if (filters.category) params.append('category', filters.category);

    const response = await fetch(`${apiBase}?${params}`, {
      headers: authHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const raw = await response.json();
    const data = unwrapFetchedJson(raw);
    if (Array.isArray(data)) {
      keywords.value = data.map(wrapKeyword);
      pagination.total = data.length;
    } else if (data && typeof data === 'object' && Array.isArray(data.items)) {
      keywords.value = data.items.map(wrapKeyword);
      pagination.total = data.total ?? data.items.length;
    } else {
      keywords.value = [];
      pagination.total = 0;
    }
    recomputeSummaryFromKeywords(keywords.value);
    dataTrust.value = 'live';
    hasSimulatedRank.value = keywords.value.some((k) => k.is_simulated === true);
  } catch (error) {
    if (import.meta.env.DEV) console.warn('关键词 API 不可用', error);
    keywords.value = [];
    pagination.total = 0;
    dataTrust.value = 'mock';
    hasSimulatedRank.value = false;
    recomputeSummaryFromKeywords(keywords.value);
  } finally {
    loading.value = false;
  }
};

const loadSummary = async () => {
  try {
    const response = await fetch(`${apiBase}/dashboard/summary`, {
      headers: authHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const s = unwrapFetchedJson(await response.json());
    if (s && typeof s === 'object' && s.total_keywords > 0) {
      Object.assign(summary.value, s);
    } else {
      recomputeSummaryFromKeywords(keywords.value);
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('加载摘要失败', error);
    recomputeSummaryFromKeywords(keywords.value);
  }
};

const refreshRankings = async () => {
  tracking.value = true;
  try {
    const response = await fetch(`${apiBase}/track`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        keywords: keywords.value.map((k) => k.keyword),
        search_engine: 'baidu',
      }),
    });
    const result = unwrapFetchedJson(await response.json());
    message.success(`已更新 ${result?.total ?? 0} 个关键词排名`);
    await loadKeywords();
    await loadSummary();
  } catch (error) {
    message.error('更新排名失败');
  } finally {
    tracking.value = false;
  }
};

const importKeywords = async () => {
  try {
    let keywordList = importText.value
      .trim()
      .split('\n')
      .filter((k) => k.trim());
    if (keywordList.length === 0) {
      keywordList = defaultKeywords;
    }

    const response = await fetch(`${apiBase}/batch-import-defaults`, {
      method: 'POST',
      headers: authHeaders(),
    });
    const result = unwrapFetchedJson(await response.json());
    message.success(result?.message ?? '导入完成');
    showImportModal.value = false;
    importText.value = '';
    await loadKeywords();
    await loadSummary();
  } catch (error) {
    message.error('导入失败');
  }
};

const deleteKeyword = async (id) => {
  try {
    await fetch(`${apiBase}/${id}`, { method: 'DELETE', headers: authHeaders() });
    message.success('删除成功');
    await loadKeywords();
    await loadSummary();
  } catch (error) {
    message.error('删除失败');
  }
};

const viewHistory = async (record) => {
  currentKeyword.value = record;
  showHistoryModal.value = true;

  try {
    const response = await fetch(`${apiBase}/${record.id}/history?days=30`, {
      headers: authHeaders(),
    });
    historyData.value = unwrapFetchedJson(await response.json());
  } catch (error) {
    message.error('加载历史失败');
  }
};

const editKeyword = (record) => {
  editingRecord.value = record;
  editForm.keyword = record.keyword ?? '';
  editForm.category = record.category ?? '';
  showEditModal.value = true;
};

async function submitKeywordEdit() {
  const r = editingRecord.value;
  if (!r || !editForm.keyword.trim()) {
    message.warning('请填写关键词');
    return Promise.reject(new Error('validation'));
  }
  editSaving.value = true;
  try {
    const res = await fetch(`${apiBase}/${r.id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        keyword: editForm.keyword.trim(),
        category: editForm.category.trim() || undefined,
      }),
    });
    if (res.ok) {
      message.success('已保存');
    } else {
      message.warning(`后端返回 ${res.status}，已同步更新本地表格`);
    }
  } catch {
    message.warning('请求失败，已同步更新本地表格');
  } finally {
    editSaving.value = false;
  }
  r.keyword = editForm.keyword.trim();
  r.category = editForm.category.trim() || r.category;
  showEditModal.value = false;
  editingRecord.value = null;
}

const resetFilters = () => {
  filters.search_engine = undefined;
  filters.category = undefined;
  loadKeywords();
};

const onPageChange = (p) => {
  pagination.current = p.current;
  pagination.pageSize = p.pageSize;
  loadKeywords();
};

const getPositionColor = (position) => {
  if (position <= 3) return 'success';
  if (position <= 10) return 'processing';
  if (position <= 50) return 'warning';
  return 'default';
};

const getPositionChangeClass = (record) => {
  if (record.position_improved()) return 'text-success';
  if (record.position_declined()) return 'text-danger';
  return 'text-muted';
};

const getDifficultyStatus = (difficulty) => {
  const map = { easy: 'success', medium: 'processing', hard: 'error', high: 'error' };
  return map[difficulty] || 'default';
};

onMounted(async () => {
  await loadKeywords();
  await loadSummary();
});
</script>

<style scoped lang="scss">
.keyword-ranking-page {
  .dashboard-cards {
    margin-bottom: 24px;
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .table-card {
    margin-bottom: 16px;
  }

  .leaderboard-tabs {
    margin-bottom: 8px;
  }

  .text-muted {
    color: #999;
  }
  .text-success {
    color: #52c41a;
  }
  .text-danger {
    color: #ff4d4f;
  }

  .import-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #999;
  }
}
</style>
