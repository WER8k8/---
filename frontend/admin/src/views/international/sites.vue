<template>
  <YdPage
    class="intl-sites"
    title="目标网站"
    subtitle="配置需要爬取的国际B2B/贸易平台，系统将自动采集国外客户询盘"
    surface="elevated"
  >
    <template #actions>
      <a-button type="primary" @click="openAdd">
        <template #icon><PlusOutlined /></template>
        添加网站
      </a-button>
    </template>

    <a-card size="small">
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="loading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="loadData"
          />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="list"
          :loading="loading"
          :pagination="{ current: 1, pageSize: 20, total }"
          :table-props="{ size: tableSize, rowKey: 'id', scroll: { x: 1100 } }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'region'">
              <span>{{ record.region }}</span>
            </template>
            <template v-if="column.key === 'url'">
              <a :href="record.url" target="_blank" class="text-blue-600 hover:underline text-xs">{{ record.url }}</a>
            </template>
            <template v-if="column.key === 'status'">
              <a-switch
                :checked="record.status === 'active'"
                @change="(checked) => toggleSite(record, checked as boolean)"
                :loading="record.toggling"
              />
              <span class="ml-2 text-xs" :class="record.status === 'active' ? 'text-green-600' : 'text-gray-400'">
                {{ record.status === 'active' ? '采集中' : '已暂停' }}
              </span>
            </template>
            <template v-if="column.key === 'actions'">
              <a-space>
                <a-button size="small" @click="openEdit(record)">编辑</a-button>
                <a-button size="small" type="primary" ghost @click="triggerScrape(record)" :loading="record.scraping">手动采集</a-button>
                <a-button size="small" danger @click="confirmDel(record)">删除</a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>

    <!-- 添加/编辑弹窗 -->
    <a-modal
      v-model:open="modalOpen"
      :title="editingId ? '编辑目标网站' : '添加目标网站'"
      @ok="handleSave"
      ok-text="保存"
      :confirm-loading="saving"
    >
      <a-form layout="vertical">
        <a-form-item label="网站名称" required>
          <a-input v-model:value="form.name" placeholder="例如：阿里巴巴国际站" />
        </a-form-item>
        <a-form-item label="网站 URL" required>
          <a-input v-model:value="form.url" placeholder="请输入网站地址" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="地区" required>
              <a-select v-model:value="form.region" placeholder="选择目标地区">
                <a-select-option v-for="r in regionOptions" :key="r.value" :value="r.value">{{ r.label }} ({{ r.value }})</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="语言">
              <a-select v-model:value="form.lang" placeholder="网站主要语言">
                <a-select-option value="English">English</a-select-option>
                <a-select-option value="Deutsch">Deutsch</a-select-option>
                <a-select-option value="Français">Français</a-select-option>
                <a-select-option value="العربية">العربية</a-select-option>
                <a-select-option value="हिन्दी">हिन्दी</a-select-option>
                <a-select-option value="Bahasa Indonesia">Bahasa Indonesia</a-select-option>
                <a-select-option value="Português">Português</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="采集频率">
              <a-select v-model:value="form.frequency" placeholder="采集频率">
                <a-select-option value="every_1h">每小时</a-select-option>
                <a-select-option value="every_3h">每 3 小时</a-select-option>
                <a-select-option value="every_6h">每 6 小时</a-select-option>
                <a-select-option value="every_12h">每 12 小时</a-select-option>
                <a-select-option value="every_24h">每天</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态">
              <a-switch v-model:checked="form.active" checked-children="启用" un-checked-children="暂停" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  Card as ACard, Button as AButton, Space as ASpace,
  Modal as AModal, Form as AForm, FormItem as AFormItem,
  Input as AInput, Select as ASelect, SelectOption as ASelectOption,
  Switch as ASwitch, Row as ARow, Col as ACol,
} from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api'
import { apiErrorMessage } from '@/utils/aiConfigHelpers'
import { adaptPaginatedResponse } from '@/utils/ydTableUtils'
import { ydConfirm } from '@/utils/ydModal'
import { COUNTRY_OPTIONS } from '@/constants/countryOptions'

type IntlSiteRow = {
  id: string
  name: string
  url: string
  region: string
  regionCode: string
  lang: string
  freqLabel: string
  lastScrape: string
  status: string
  toggling?: boolean
  scraping?: boolean
}

const FREQ_TO_MINUTES: Record<string, number> = {
  every_1h: 60,
  every_3h: 180,
  every_6h: 360,
  every_12h: 720,
  every_24h: 1440,
}

const MINUTES_TO_FREQ: Record<number, string> = {
  60: 'every_1h',
  180: 'every_3h',
  360: 'every_6h',
  720: 'every_12h',
  1440: 'every_24h',
}

const FREQ_LABELS: Record<string, string> = {
  every_1h: '每小时',
  every_3h: '每 3 小时',
  every_6h: '每 6 小时',
  every_12h: '每 12 小时',
  every_24h: '每天',
}

const LANG_TO_CODE: Record<string, string> = {
  English: 'en',
  Deutsch: 'de',
  Français: 'fr',
  العربية: 'ar',
  'हिन्दी': 'hi',
  'Bahasa Indonesia': 'id',
  Português: 'pt',
}

const CODE_TO_LANG: Record<string, string> = Object.fromEntries(
  Object.entries(LANG_TO_CODE).map(([label, code]) => [code, label]),
)

const loading = ref(false)
const list = ref<IntlSiteRow[]>([])
const total = ref(0)
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const modalOpen = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)

const form = reactive({
  name: '',
  url: '',
  region: '',
  lang: 'English',
  frequency: 'every_6h',
  active: true,
})

const regionOptions = COUNTRY_OPTIONS.map((c) => ({ value: c.value, label: c.label }))

const columns = [
  { title: '网站名称', dataIndex: 'name', width: 160 },
  { title: 'URL', key: 'url', width: 250 },
  { title: '地区', key: 'region', width: 100 },
  { title: '语言', dataIndex: 'lang', width: 90 },
  { title: '采集频率', dataIndex: 'freqLabel', width: 100 },
  { title: '最后采集', dataIndex: 'lastScrape', width: 150 },
  { title: '状态', key: 'status', width: 120 },
  { title: '操作', key: 'actions', width: 270, fixed: 'right' as const },
]

function regionLabel(code: string): string {
  return COUNTRY_OPTIONS.find((c) => c.value === code)?.label || code
}

function freqLabelFromMinutes(minutes: number): string {
  const key = MINUTES_TO_FREQ[minutes] || 'every_6h'
  return FREQ_LABELS[key] || `每 ${minutes} 分钟`
}

function formatScrapeTime(value: unknown): string {
  if (!value) return '—'
  const d = new Date(String(value))
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', { hour12: false })
}

function normalizeSite(raw: Record<string, unknown>): IntlSiteRow {
  const regionCode = String(raw.region || '')
  const minutes = Number(raw.crawl_interval ?? 360)
  const freqKey = MINUTES_TO_FREQ[minutes] || 'every_6h'
  const language = String(raw.language || 'en')
  return {
    id: String(raw.id),
    name: String(raw.name || ''),
    url: String(raw.url || ''),
    regionCode,
    region: regionLabel(regionCode),
    lang: CODE_TO_LANG[language] || language,
    freqLabel: FREQ_LABELS[freqKey] || freqLabelFromMinutes(minutes),
    lastScrape: formatScrapeTime(raw.last_crawled_at),
    status: String(raw.status || 'active'),
    toggling: false,
    scraping: false,
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await apiGet<{ items?: unknown[]; total?: number }>('/international/sites')
    const { rows, total: count } = adaptPaginatedResponse<Record<string, unknown>>(data)
    list.value = rows.map(normalizeSite)
    total.value = count
  } catch (e) {
    list.value = []
    total.value = 0
    message.error(apiErrorMessage(e, '加载失败，请确认后端已启动（:8001）'))
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.name = ''
  form.url = ''
  form.region = ''
  form.lang = 'English'
  form.frequency = 'every_6h'
  form.active = true
  modalOpen.value = true
}

function openEdit(record: IntlSiteRow) {
  editingId.value = record.id
  form.name = record.name
  form.url = record.url
  form.region = record.regionCode
  form.lang = record.lang
  form.frequency = Object.entries(FREQ_LABELS).find(([, label]) => label === record.freqLabel)?.[0] || 'every_6h'
  form.active = record.status === 'active'
  modalOpen.value = true
}

async function handleSave() {
  if (!form.name || !form.url || !form.region) {
    message.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name,
      url: form.url,
      region: form.region,
      language: LANG_TO_CODE[form.lang] || 'en',
      crawl_interval: FREQ_TO_MINUTES[form.frequency] || 360,
      status: form.active ? 'active' : 'paused',
    }
    if (editingId.value) {
      await apiPut(`/international/sites/${editingId.value}`, payload)
      message.success('已更新')
    } else {
      await apiPost('/international/sites', payload)
      message.success('已添加')
    }
    modalOpen.value = false
    await loadData()
  } catch (e) {
    message.error(apiErrorMessage(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function toggleSite(record: IntlSiteRow, checked: boolean) {
  record.toggling = true
  try {
    const newStatus = checked ? 'active' : 'paused'
    await apiPut(`/international/sites/${record.id}`, { status: newStatus })
    record.status = newStatus
    message.success(`${record.name} 已${checked ? '启用采集' : '暂停采集'}`)
  } catch {
    message.error('状态更新失败')
  } finally {
    record.toggling = false
  }
}

async function triggerScrape(record: IntlSiteRow) {
  record.scraping = true
  try {
    await apiPost(`/international/sites/${record.id}/scrape`)
    message.success(`已触发 ${record.name} 手动采集`)
    await loadData()
  } catch (e) {
    message.warning(apiErrorMessage(e, '手动采集尚未接入 Worker'))
  } finally {
    record.scraping = false
  }
}

function confirmDel(record: IntlSiteRow) {
  ydConfirm({
    title: '确认删除',
    content: `确定要删除目标网站「${record.name}」吗？`,
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await apiDelete(`/international/sites/${record.id}`)
          message.success('已删除')
          await loadData()
        } catch {
          message.error('删除失败')
        }
      })();
    },
  })
}

onMounted(() => loadData())
</script>

<style scoped>
.ml-2 { margin-left: 8px; }
</style>
