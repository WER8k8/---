<template>
  <YdPage class="baidu-tools-page" title="百度站长工具" subtitle="百度索引、抓取与搜索词数据管理" surface="elevated">
    <YdHonestDataBanner
      v-if="dataLevel !== 'real'"
      :level="dataLevel"
      title="未绑定百度 site_token — 下方数字不可当作真实收录"
      description="请在百度站长平台获取 site_token 并验证。未绑定前索引量、抓取、搜索词均为演示或为空。"
    />
    <a-descriptions size="small" :column="4" style="margin-bottom: 24px">
        <a-descriptions-item label="站点Token">
          <a-input-search
            v-model:value="siteToken"
            placeholder="输入百度站长平台 site_token"
            style="width: 280px"
            @search="verifyToken"
            enter-button="验证"
          />
        </a-descriptions-item>
        <a-descriptions-item label="站点URL">
          <a-input v-model:value="siteUrl" style="width: 240px" />
        </a-descriptions-item>
      </a-descriptions>

    <!-- 数据概览卡片 -->
    <a-row :gutter="16" style="margin-bottom: 24px">
      <a-col :span="6">
        <a-statistic title="索引量" :value="displayIndex.total_index" :suffix="displayIndex.total_index === '—' ? '' : '条'">
          <template #prefix>
            <SearchOutlined style="color: #1677ff" />
          </template>
        </a-statistic>
        <div v-if="hasRealIndex" style="font-size: 12px; color: #52c41a; margin-top: 4px">
          今日变动: +{{ indexData.daily_change }}
        </div>
      </a-col>
      <a-col :span="6">
        <a-statistic title="今日抓取" :value="displayIndex.today_crawl" :suffix="displayIndex.today_crawl === '—' ? '' : '次'">
          <template #prefix>
            <CloudDownloadOutlined style="color: #722ed1" />
          </template>
        </a-statistic>
        <div v-if="hasRealIndex" style="font-size: 12px; color: #999; margin-top: 4px">
          抓取频次: {{ indexData.crawl_frequency }}
        </div>
      </a-col>
      <a-col :span="6">
        <a-statistic title="累计展现" :value="displaySearch.total_impressions" :suffix="displaySearch.total_impressions === '—' ? '' : '次'">
          <template #prefix>
            <EyeOutlined style="color: #fa8c16" />
          </template>
        </a-statistic>
      </a-col>
      <a-col :span="6">
        <a-statistic
          title="累计点击"
          :value="displaySearch.total_clicks"
          :suffix="displaySearch.total_clicks === '—' ? '' : '次'"
          :precision="0"
        >
          <template #prefix>
            <MouseOutlined style="color: #eb2f96" />
          </template>
        </a-statistic>
      </a-col>
    </a-row>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <a-space>
        <a-button type="primary" @click="submitSitemap">提交Sitemap</a-button>
        <a-button @click="fetchIndexCount">查看索引</a-button>
        <a-button @click="fetchSearchQueries">搜索词分析</a-button>
      </a-space>
    </div>

    <!-- 搜索词列表 -->
    <a-card title="搜索词数据" style="margin-top: 16px">
      <a-empty v-if="!searchData.queries.length" description="绑定 site_token 并刷新后展示百度搜索词" />
      <YdDataTable
        v-else
        :columns="queryColumns"
        :data-source="searchData.queries"
        :pagination="false"
        :table-props="{ size: tableSize, rowKey: 'keyword' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'keyword'">
            <span style="font-weight: 500">{{ record.keyword }}</span>
          </template>
          <template v-if="column.key === 'ctr'">
            <a-tag :color="record.ctr > 4.2 ? 'green' : 'orange'">
              {{ record.ctr }}%
            </a-tag>
          </template>
          <template v-if="column.key === 'position'">
            <a-tag :color="record.position <= 5 ? 'blue' : 'default'">
              第{{ record.position }}位
            </a-tag>
          </template>
        </template>
      </YdDataTable>
    </a-card>

    <!-- 最近一次抓取 -->
    <div v-if="hasRealIndex" style="text-align: right; margin-top: 12px; color: #999; font-size: 12px">
      最近抓取时间: {{ indexData.last_crawl_time }}
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdHonestDataBanner } from '@/components/youding'
import type { HonestLevel } from '@/components/youding/YdHonestDataBanner.vue'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  SearchOutlined,
  CloudDownloadOutlined,
  EyeOutlined,
  MoreOutlined as MouseOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getAuthToken } from '@/utils/api'
import { unwrapFetchedJson } from '@/api'

const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const siteToken = ref('')
const siteUrl = ref('https://youding.com')
const dataLevel = ref<HonestLevel>('needs-config')
const hasRealIndex = ref(false)
const hasRealSearch = ref(false)

const indexData = reactive({
  total_index: 0,
  daily_change: 0,
  today_crawl: 0,
  crawl_frequency: '',
  last_crawl_time: '',
})

const searchData = reactive({
  total_impressions: 0,
  total_clicks: 0,
  avg_ctr: 0,
  days: 30,
  queries: [] as Array<Record<string, unknown>>,
})

const displayIndex = computed(() => ({
  total_index: hasRealIndex.value ? indexData.total_index : '—',
  today_crawl: hasRealIndex.value ? indexData.today_crawl : '—',
}))

const displaySearch = computed(() => ({
  total_impressions: hasRealSearch.value ? searchData.total_impressions : '—',
  total_clicks: hasRealSearch.value ? searchData.total_clicks : '—',
}))

function resetIndexData() {
  indexData.total_index = 0
  indexData.daily_change = 0
  indexData.today_crawl = 0
  indexData.crawl_frequency = ''
  indexData.last_crawl_time = ''
  hasRealIndex.value = false
}

function resetSearchData() {
  searchData.total_impressions = 0
  searchData.total_clicks = 0
  searchData.avg_ctr = 0
  searchData.queries = []
  hasRealSearch.value = false
}

function isMockPayload(data: unknown): boolean {
  return !!data && typeof data === 'object' && (data as Record<string, unknown>).mode === 'mock'
}

function syncDataLevel() {
  if (!siteToken.value.trim()) {
    dataLevel.value = 'needs-config'
    return
  }
  if (hasRealIndex.value || hasRealSearch.value) {
    dataLevel.value = 'real'
    return
  }
  dataLevel.value = 'needs-config'
}

const queryColumns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
  { title: '展现量', dataIndex: 'impressions', key: 'impressions' },
  { title: '点击量', dataIndex: 'clicks', key: 'clicks' },
  { title: '点击率', dataIndex: 'ctr', key: 'ctr' },
  { title: '平均排名', dataIndex: 'position', key: 'position' },
]

function verifyToken() {
  if (siteToken.value.trim()) {
    message.success('Token 已设置，将请求百度 API')
    void fetchIndexCount()
    void fetchSearchQueries()
  } else {
    resetIndexData()
    resetSearchData()
    syncDataLevel()
    message.warning('请先填写 site_token')
  }
}

async function fetchIndexCount() {
  if (!siteToken.value.trim()) {
    resetIndexData()
    syncDataLevel()
    return
  }
  try {
    const tk = getAuthToken()
    const params = new URLSearchParams({ site_url: siteUrl.value, token: siteToken.value })
    const res = await fetch(`/api/v1/baidu/index-count?${params}`, {
      headers: { Authorization: `Bearer ${tk}` },
    })
    const raw = await res.json()
    const data = unwrapFetchedJson(raw) as Record<string, unknown> | null
    if (!data || isMockPayload(data)) {
      resetIndexData()
      dataLevel.value = 'mock'
      return
    }
    Object.assign(indexData, data)
    hasRealIndex.value = true
    syncDataLevel()
  } catch {
    resetIndexData()
    syncDataLevel()
    message.error('索引量查询失败')
  }
}

async function fetchSearchQueries() {
  if (!siteToken.value.trim()) {
    resetSearchData()
    syncDataLevel()
    return
  }
  try {
    const tk = getAuthToken()
    const params = new URLSearchParams({ site_url: siteUrl.value, days: '30', token: siteToken.value })
    const res = await fetch(`/api/v1/baidu/search-queries?${params}`, {
      headers: { Authorization: `Bearer ${tk}` },
    })
    const raw = await res.json()
    const data = unwrapFetchedJson(raw) as Record<string, unknown> | null
    if (!data || isMockPayload(data)) {
      resetSearchData()
      dataLevel.value = 'mock'
      return
    }
    searchData.total_impressions = Number(data.total_impressions ?? 0)
    searchData.total_clicks = Number(data.total_clicks ?? 0)
    searchData.avg_ctr = Number(data.avg_ctr ?? 0)
    searchData.queries = Array.isArray(data.queries) ? data.queries : []
    hasRealSearch.value = true
    syncDataLevel()
  } catch {
    resetSearchData()
    syncDataLevel()
    message.error('搜索词查询失败')
  }
}

async function submitSitemap() {
  if (!siteToken.value.trim()) {
    message.warning('请先填写并验证 site_token')
    return
  }
  try {
    const tk = getAuthToken()
    const sitemap = `${siteUrl.value}/sitemap.xml`
    const params = new URLSearchParams({
      site_url: siteUrl.value,
      sitemap_url: sitemap,
      token: siteToken.value,
    })
    const res = await fetch(`/api/v1/baidu/sitemap/submit?${params}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${tk}` },
    })
    const raw = await res.json()
    const data = unwrapFetchedJson(raw) as { message?: string; mode?: string } | null
    if (data?.mode === 'mock') {
      message.warning('未接通百度 API，Sitemap 未真实提交')
      return
    }
    message.success(data?.message ?? `Sitemap 提交成功: ${sitemap}`)
  } catch {
    message.error('Sitemap 提交失败')
  }
}

onMounted(() => {
  resetIndexData()
  resetSearchData()
  syncDataLevel()
})
</script>

<style scoped>
.baidu-tools-page {
  /* layout handled by YdPage */
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
}

.mock-notice {
  font-size: 12px;
  color: #faad14;
  background: #fffbe6;
  padding: 4px 12px;
  border-radius: 4px;
  border: 1px solid #ffe58f;
}
</style>
