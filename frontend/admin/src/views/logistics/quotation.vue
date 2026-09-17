/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="报价单生成" subtitle="建材物流报价单管理" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showCreate = true"><PlusOutlined /> 新建报价单</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-card>
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="tableLoading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="fetchQuotes"
          />
        </div>
        <YdDataTable
          :columns="cols"
          :data-source="quotes"
          :loading="tableLoading"
          :pagination="false"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'sent' ? 'processing' : record.status === 'approved' ? 'success' : 'default'">
                {{ record.status === 'sent' ? '已发送' : record.status === 'approved' ? '已确认' : '草稿' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button size="small" type="link" @click="previewQuote(record)">预览</a-button>
                <a-button size="small" type="link">导出</a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
    <!-- Create Modal -->
    <a-modal v-model:open="showCreate" title="新建报价单" @ok="add" ok-text="生成报价单" width="640">
      <a-form :model="f" layout="vertical">
        <a-form-item label="客户名称" required>
          <a-input v-model:value="f.customer" placeholder="例如：杭州绿城建设有限公司" />
        </a-form-item>
        <a-form-item label="产品类型" required>
          <a-select v-model:value="f.product">
            <a-select-option value="轻集料混凝土">轻集料混凝土</a-select-option>
            <a-select-option value="陶粒混凝土">陶粒混凝土</a-select-option>
            <a-select-option value="保温砂浆">保温砂浆</a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="货物重量(吨)">
              <a-input-number v-model:value="f.weight" :min="1" class="w-full" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="运输距离(公里)">
              <a-input-number v-model:value="f.distance" :min="10" class="w-full" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="始发地">
              <a-input v-model:value="f.origin" placeholder="上海仓库" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="目的地">
              <a-input v-model:value="f.destination" placeholder="杭州项目工地" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
    <!-- Preview Modal -->
    <a-modal v-model:open="previewModal.open" title="报价单预览" :footer="null" width="640">
      <a-card v-if="previewModal.record" class="bg-blue-50">
        <h3 class="text-lg font-bold text-center mb-4">物流报价单</h3>
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="报价单号">{{ previewModal.record.no }}</a-descriptions-item>
          <a-descriptions-item label="日期">{{ previewModal.record.date }}</a-descriptions-item>
          <a-descriptions-item label="客户">{{ previewModal.record.customer }}</a-descriptions-item>
          <a-descriptions-item label="产品">{{ previewModal.record.cargo }}</a-descriptions-item>
          <a-descriptions-item label="始发地">{{ previewModal.record.origin || '-' }}</a-descriptions-item>
          <a-descriptions-item label="目的地">{{ previewModal.record.destination || '-' }}</a-descriptions-item>
          <a-descriptions-item label="运费明细">基础运费 ¥{{ previewModal.record.base || 0 }}</a-descriptions-item>
          <a-descriptions-item label="附加费">¥{{ previewModal.record.surcharge || 0 }}</a-descriptions-item>
          <a-descriptions-item label="总价" :span="2">
            <span class="text-xl font-bold text-blue-600">{{ previewModal.record.amount }}</span>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Card, Tag, Button, Modal, Form, FormItem, Input, InputNumber,
  Select, SelectOption, Row, Col, Descriptions, DescriptionsItem, Space, message,
} from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { getAuthToken } from '@/utils/api'

const showCreate = ref(false)
const tablePanelRef = ref<HTMLElement | null>(null)
const tableLoading = ref(false)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const f = reactive({
  customer: '', product: '轻集料混凝土', weight: 20, distance: 400, origin: '', destination: '',
})

const previewModal = reactive({ open: false, record: null as any })

const cols = [
  { title: '报价单号', dataIndex: 'no', key: 'no' },
  { title: '客户', dataIndex: 'customer', key: 'customer' },
  { title: '货物', dataIndex: 'cargo', key: 'cargo', width: 160 },
  { title: '金额', dataIndex: 'amount', key: 'amount', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
  { title: '操作', key: 'action', width: 120 },
]

const quotes = ref<any[]>([])

async function fetchQuotes() {
  tableLoading.value = true
  try {
    const res = await fetch('/api/v1/logistics/quotation', { headers: { Authorization: `Bearer ${getAuthToken()}` } })
    const body = await res.json()
    const data = body.data || body
    if (data.list || Array.isArray(data)) quotes.value = data.list || data
  } catch {
    quotes.value = []
  }
  finally {
    tableLoading.value = false
  }
}

onMounted(() => { fetchQuotes() })

const priceMap: Record<string, number> = { '轻集料混凝土': 0.85, '陶粒混凝土': 1.10, '保温砂浆': 0.65 }

const initForm = () => Object.assign(f, { customer: '', product: '轻集料混凝土', weight: 20, distance: 400, origin: '', destination: '' })

async function add() {
  if (!f.customer.trim()) { message.warning('请输入客户名称'); return }
  const base = Math.round(f.weight * f.distance * (priceMap[f.product] || 0.85))
  const surcharge = Math.round(base * 0.15 + 350)
  const total = base + surcharge
  const dateStr = new Date().toISOString().slice(0, 10)
  const seq = String(quotes.value.length + 1).padStart(3, '0')
  quotes.value.unshift({
    id: Date.now(),
    no: `Q${dateStr.replace(/-/g, '')}${seq}`,
    customer: f.customer,
    cargo: `${f.product} ${f.weight}吨`,
    amount: `¥${total.toLocaleString()}`,
    status: 'draft',
    date: dateStr,
    origin: f.origin,
    destination: f.destination,
    base,
    surcharge,
  })
  // 同步到后端
  try {
    await fetch('/api/v1/logistics/quotation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ customer: f.customer, product: f.product, weight: f.weight, distance: f.distance, origin: f.origin, destination: f.destination }),
    })
  } catch {}
  showCreate.value = false
  initForm()
  message.success('报价单已生成')
}

function previewQuote(r: any) {
  previewModal.record = r
  previewModal.open = true
}
</script>
