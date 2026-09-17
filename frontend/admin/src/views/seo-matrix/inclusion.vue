/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="收录监控" subtitle="实时监控内容收录状态，追踪百度排名变化" surface="elevated">
    <YdHonestDataBanner
      v-if="probeConfig && !probeConfig.real_probe_enabled"
      level="dev-stub"
      title="收录探测未开启真实模式"
      :description="probeConfig.hint"
    />
    <template #actions>
      <a-button @click="refreshData">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新
      </a-button>
      <a-button type="primary" class="gradient-primary" @click="checkInclusion">
        <SearchOutlined class="w-4 h-4 mr-2" />
        检查收录
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-5">
      <div class="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-primary-100 text-sm font-medium">
              监控总数
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ totalCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <FileTextOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-success-500 to-success-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-success-100 text-sm font-medium">
              已收录
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ includedCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <CheckCircleOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-warning-500 to-warning-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-warning-100 text-sm font-medium">
              未收录
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ notIncludedCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <ClockCircleOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm font-medium">
              收录率
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ inclusionRate }}%
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <LineChartOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                收录状态列表
              </h3>
            </div>
            <div class="flex items-center space-x-3">
              <a-select
                v-model:value="statusFilter"
                placeholder="状态筛选"
                class="w-36"
              >
                <a-select-option value="">
                  全部
                </a-select-option>
                <a-select-option value="included">
                  已收录
                </a-select-option>
                <a-select-option value="not_included">
                  未收录
                </a-select-option>
                <a-select-option value="checking">
                  检查中
                </a-select-option>
              </a-select>
              <a-select
                v-model:value="keywordFilter"
                placeholder="关键词筛选"
                class="w-48"
              >
                <a-select-option value="">
                  全部关键词
                </a-select-option>
                <a-select-option
                  v-for="k in recentKeywords"
                  :key="k"
                  :value="k"
                >
                  {{ k }}
                </a-select-option>
              </a-select>
            </div>
          </div>

          <a-table
            :columns="columns"
            :data-source="inclusionList"
            :pagination="pagination"
            :loading="loading"
            row-key="id"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'keyword'">
                <span class="font-medium text-gray-900">{{ record.keyword }}</span>
              </template>
              <template v-if="column.key === 'url'">
                <a-button
                  type="link"
                  :href="record.url"
                  target="_blank"
                  class="text-left p-0 h-auto"
                >
                  <span
                    class="text-primary-500 text-sm truncate max-w-xs"
                    :title="record.url"
                  >{{
                    record.url
                  }}</span>
                </a-button>
              </template>
              <template v-if="column.key === 'is_included'">
                <span
                  :class="
                    record.is_included
                      ? 'bg-success-50 text-success-600'
                      : 'bg-warning-50 text-warning-600'
                  "
                  class="px-3 py-1 rounded-full text-sm font-medium"
                >
                  {{ record.is_included ? '已收录' : '未收录' }}
                </span>
              </template>
              <template v-if="column.key === 'probe_mode'">
                <span class="text-gray-500 text-xs">{{ record.probe_mode || '—' }}</span>
              </template>
              <template v-if="column.key === 'rank'">
                <span
                  v-if="record.rank && record.rank > 0"
                  class="text-success-600 font-medium"
                >第 {{ record.rank }} 名</span>
                <span
                  v-else-if="record.rank === 0"
                  class="text-primary-600 font-medium"
                >首页</span>
                <span
                  v-else
                  class="text-gray-400"
                >-</span>
              </template>
              <template v-if="column.key === 'last_check_time'">
                <span class="text-gray-500 text-sm">{{ formatTime(record.last_check_time) }}</span>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space :size="8">
                  <a-button
                    size="small"
                    @click="viewDetail(record)"
                  >
                    详情
                  </a-button>
                  <a-button
                    size="small"
                    @click="recheckInclusion(record)"
                  >
                    重新检查
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </div>

      <div class="lg:col-span-1 space-y-6">
        <div class="bg-white rounded-2xl shadow-card p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChartOutlined class="w-5 h-5 mr-2 text-primary-500" />
            收录趋势
          </h3>
          <div class="h-48">
            <div class="flex items-end justify-between h-full gap-2">
              <div
                v-for="(item, index) in trendData"
                :key="index"
                class="flex-1 flex flex-col items-center"
              >
                <div
                  class="w-full bg-gradient-to-t from-primary-500 to-primary-400 rounded-t-md transition-all hover:from-primary-600 hover:to-primary-500"
                  :style="{ height: item.percent + '%' }"
                />
                <span class="text-xs text-gray-500 mt-1">{{ item.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-card p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <SearchOutlined class="w-5 h-5 mr-2 text-primary-500" />
            热门关键词
          </h3>
          <div class="space-y-3">
            <div
              v-for="(item, index) in hotKeywords"
              :key="index"
              class="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center">
                <span
                  :class="[
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium mr-2',
                    index < 3 ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-600',
                  ]"
                >{{ index + 1 }}</span>
                <span class="text-gray-900">{{ item.keyword }}</span>
              </div>
              <span class="text-sm text-gray-500">{{
                item.rank > 0 ? '第' + item.rank + '名' : '未收录'
              }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-card p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BellOutlined class="w-5 h-5 mr-2 text-primary-500" />
            监控设置
          </h3>
          <a-space
            direction="vertical"
            class="w-full"
          >
            <label class="flex items-center justify-between w-full">
              <span>自动检查收录</span>
              <a-switch v-model:checked="autoCheckEnabled" />
            </label>
            <label class="flex items-center justify-between w-full">
              <span>收录提醒</span>
              <a-switch v-model:checked="alertEnabled" />
            </label>
            <label class="flex items-center justify-between w-full">
              <span>排名变化提醒</span>
              <a-switch v-model:checked="rankAlertEnabled" />
            </label>
          </a-space>
          <a-button
            block
            type="primary"
            class="mt-4"
            @click="saveSettings"
          >
            保存设置
          </a-button>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showDetailModal"
      :title="detailData?.keyword + ' - 收录详情'"
      width="700px"
      :footer="false"
    >
      <div
        v-if="detailData"
        class="space-y-4"
      >
        <div class="grid grid-cols-2 gap-4">
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-500">
              关键词
            </p>
            <p class="font-medium text-gray-900 mt-1">
              {{ detailData.keyword }}
            </p>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-500">
              收录状态
            </p>
            <p
              :class="detailData.is_included ? 'text-success-600' : 'text-warning-600'"
              class="font-medium mt-1"
            >
              {{ detailData.is_included ? '已收录' : '未收录' }}
            </p>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-500">
              排名
            </p>
            <p class="font-medium text-gray-900 mt-1">
              {{
                detailData.rank && detailData.rank > 0
                  ? '第 ' + detailData.rank + ' 名'
                  : '未进入前100'
              }}
            </p>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-500">
              检查时间
            </p>
            <p class="font-medium text-gray-900 mt-1">
              {{ formatTime(detailData.last_check_time) }}
            </p>
          </div>
        </div>
        <div class="p-3 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-500">
            URL
          </p>
          <a
            :href="detailData.url"
            target="_blank"
            class="text-primary-500 mt-1 block truncate"
          >{{
            detailData.url
          }}</a>
        </div>
        <div class="p-3 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-500">
            页面标题
          </p>
          <p class="font-medium text-gray-900 mt-1">
            {{ detailData.page_title || '-' }}
          </p>
        </div>
      </div>
      <div class="flex justify-end mt-6">
        <a-button @click="showDetailModal = false">
          关闭
        </a-button>
      </div>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onActivated } from 'vue';
import {
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LineChartOutlined,
  BarChartOutlined,
  BellOutlined,
} from '@ant-design/icons-vue';
import { YdPage, YdHonestDataBanner } from '@/components/youding';
import { seoMatrixAPI, unwrapApiData } from '@/api';

const inclusionList = ref<any[]>([]);
const statusFilter = ref('');
const keywordFilter = ref('');
const loading = ref(false);
const showDetailModal = ref(false);
const detailData = ref<any>(null);

const autoCheckEnabled = ref(true);
const alertEnabled = ref(true);
const rankAlertEnabled = ref(true);

const probeConfig = ref<{ real_probe_enabled?: boolean; hint?: string; environment?: string } | null>(
  null,
);

const inclusionDevStub = computed(
  () =>
    !probeConfig.value?.real_probe_enabled
    || import.meta.env.DEV
    || inclusionList.value.some((i) => i.probe_mode === 'skip'),
);

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { title: '关键词', key: 'keyword', width: 180 },
  { title: 'URL', key: 'url', width: 300 },
  { title: '收录状态', key: 'is_included', width: 100 },
  { title: '探测', key: 'probe_mode', width: 110 },
  { title: '排名', key: 'rank', width: 80 },
  { title: '最后检查', key: 'last_check_time', width: 150 },
  { title: '操作', key: 'actions', width: 140 },
];

const recentKeywords = ref(['保温材料', '外墙保温', '聚氨酯保温', '岩棉板', '保温工程']);

const trendData = ref([
  { label: '周一', percent: 65 },
  { label: '周二', percent: 72 },
  { label: '周三', percent: 68 },
  { label: '周四', percent: 80 },
  { label: '周五', percent: 75 },
  { label: '周六', percent: 85 },
  { label: '周日', percent: 88 },
]);

const hotKeywords = ref([
  { keyword: '保温材料厂家', rank: 3 },
  { keyword: '外墙保温施工', rank: 8 },
  { keyword: '聚氨酯保温板', rank: 12 },
  { keyword: '岩棉保温材料', rank: 15 },
  { keyword: '保温工程公司', rank: 0 },
]);

const totalCount = computed(() => pagination.value.total || inclusionList.value.length);
const includedCount = computed(() => inclusionList.value.filter((i) => i.is_included).length);
const notIncludedCount = computed(() => inclusionList.value.filter((i) => !i.is_included).length);
const inclusionRate = computed(() => {
  if (totalCount.value === 0) return 0;
  return Math.round((includedCount.value / totalCount.value) * 100);
});

function formatTime(timeStr: string) {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function fetchInclusionList() {
  loading.value = true;
  try {
    const params: Record<string, unknown> = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (statusFilter.value && statusFilter.value !== 'checking') {
      params.status = statusFilter.value;
    }
    if (keywordFilter.value) params.keyword = keywordFilter.value;
    const res = await seoMatrixAPI.getInclusionStatus(params);
    const page = unwrapApiData<{ items?: any[]; total?: number }>(res);
    inclusionList.value = (page?.items || []).map((r: any) => ({
      ...r,
      rank: r.ranking,
      last_check_time: r.last_checked_at,
    }));
    pagination.value.total = page?.total || 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch inclusion list:', e);
  } finally {
    loading.value = false;
  }
}

function handleTableChange(paginationInfo: any) {
  pagination.value.current = paginationInfo.current;
  pagination.value.pageSize = paginationInfo.pageSize;
  fetchInclusionList();
}

async function checkInclusion() {
  try {
    await seoMatrixAPI.checkInclusion();
    fetchInclusionList();
    alert('检查任务已创建');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to check inclusion:', e);
    alert('检查失败');
  }
}

function viewDetail(record: any) {
  detailData.value = record;
  showDetailModal.value = true;
}

async function recheckInclusion(record: any) {
  try {
    const res = await seoMatrixAPI.recheckInclusion(record.id);
    const report = unwrapApiData<{ samples?: Array<{ probe_mode?: string; task_id?: string }> }>(res);
    const sample = (report?.samples || []).find((s) => s.task_id === record.task_id) || report?.samples?.[0];
    fetchInclusionList();
    const mode = sample?.probe_mode ? ` (${sample.probe_mode})` : '';
    alert(`重新检查完成${mode}`);
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to recheck:', e);
    alert('重新检查失败');
  }
}

async function saveSettings() {
  try {
    await seoMatrixAPI.saveInclusionSettings({
      auto_check_enabled: autoCheckEnabled.value,
      alert_enabled: alertEnabled.value,
      rank_alert_enabled: rankAlertEnabled.value,
    });
    alert('设置保存成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to save settings:', e);
    alert('保存失败');
  }
}

function refreshData() {
  fetchInclusionList();
  seoMatrixAPI
    .getInclusionProbeConfig()
    .then((res) => {
      probeConfig.value = unwrapApiData(res) as typeof probeConfig.value;
    })
    .catch(() => {
      probeConfig.value = null;
    });
}

onActivated(() => {
  refreshData();
});
</script>
