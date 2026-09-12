<template>
  <YdPage title="询盘管理" subtitle="管理客户咨询和询价信息" surface="elevated">
    <template #actions>
      <YdTableColumnSettings
        :columns="orderedInquiryColumns"
        :hidden-keys="hiddenColumnKeys"
        @toggle="toggleColumnVisibility"
        @move-up="moveColumnUp"
        @move-down="moveColumnDown"
        @reset="resetColumnLayout"
      />
      <a-dropdown trigger="click">
        <a-button>
          更多
          <DownOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item key="export-csv" @click="exportInquiries">
              <DownloadOutlined />
              导出 CSV
            </a-menu-item>
            <a-menu-item key="audit-preview" @click="openAuditPreview">审计预览</a-menu-item>
            <a-menu-item key="audit-export" @click="exportAssignmentAudit">导出改派审计</a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </template>

    <a-alert
      class="mb-3"
      type="info"
      show-icon
      message="语言桥：展开询盘可生成「中文摘要」和「英文回复草稿」，发送前请人工核对。"
    />

    <YdStatsRow :cols="4" class="inquiries-kpi-row">
      <YdStatsCard label="今日新询盘" :value="stats.today" tone="blue" compact />
      <YdStatsCard label="待处理" :value="stats.pending" tone="amber" compact />
      <YdStatsCard label="本月累计" :value="stats.month" compact />
      <YdStatsCard label="转化率" :value="stats.rate" hint="%" tone="green" compact />
    </YdStatsRow>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <template v-if="initialLoading">
        <SkeletonCard variant="table" :rows="6" />
      </template>
      <template v-else>
      <div class="panel-head mb-3">
        <a-space wrap>
          <a-radio-group v-model:value="filterTab" button-style="solid" @change="loadData">
            <a-radio-button value="">全部</a-radio-button>
            <a-radio-button value="pending">待处理</a-radio-button>
            <a-radio-button value="quoted">处理中</a-radio-button>
            <a-radio-button value="accepted">已完成</a-radio-button>
          </a-radio-group>
          <a-select
            v-model:value="sourceFilter"
            allow-clear
            placeholder="来源渠道"
            style="width: 180px"
            @change="loadData"
          >
            <a-select-option value="platform_landing">平台落地页</a-select-option>
          </a-select>
        </a-space>
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          :show-export="true"
          @refresh="loadData"
          @export="exportInquiries"
        />
      </div>

      <YdDataTable
        :columns="visibleInquiryColumns"
        :data-source="list"
        :loading="loading"
        :table-props="{ size: 'small', rowKey: 'id', onExpand }"
      >
        <template #expandedRowRender="{ record }">
          <div class="p-3 bg-gray-50 rounded space-y-3">
            <div v-if="record.intent_level" class="intent-panel">
              <p class="text-sm font-medium text-gray-800">
                意向：
                <a-tag :color="intentColor(record.intent_level)">{{ record.intent_label || record.intent_level }}</a-tag>
              </p>
              <p v-if="record.intent_next_action" class="text-xs text-indigo-700 mt-1">
                建议：{{ record.intent_next_action }}
              </p>
              <ul v-if="record.intent_reasons?.length" class="text-xs text-gray-600 mt-1 list-disc pl-4">
                <li v-for="(r, i) in record.intent_reasons" :key="i">{{ r }}</li>
              </ul>
            </div>
            <div v-if="record.discovery_questions?.length" class="discovery-panel">
              <p class="text-gray-500 text-sm mb-1">Discovery 追问（建议电话/企微确认）：</p>
              <ol class="text-sm text-gray-800 space-y-1 list-decimal pl-4">
                <li v-for="q in record.discovery_questions" :key="q.id">{{ q.question }}</li>
              </ol>
              <a-button size="small" class="mt-2" @click="copyDiscovery(record)">复制追问话术</a-button>
            </div>
            <div class="bridge-panel border-t border-gray-200 pt-2">
              <p class="text-sm font-medium text-gray-800 mb-1">语言桥</p>
              <a-space wrap class="mb-2">
                <a-button
                  size="small"
                  :loading="bridgeLoadingId === record.id && bridgeMode === 'summary'"
                  @click="runBridgeSummary(record)"
                >
                  中文摘要
                </a-button>
              </a-space>
              <div v-if="bridgeCache[record.id]?.summary_zh" class="text-xs bg-amber-50 p-2 rounded mb-2">
                {{ bridgeCache[record.id].summary_zh }}
              </div>
              <a-textarea
                v-model:value="bridgeBossZh[record.id]"
                :rows="2"
                placeholder="用中文写回复要点…"
              />
              <a-button
                size="small"
                type="primary"
                class="mt-2"
                :loading="bridgeLoadingId === record.id && bridgeMode === 'reply'"
                @click="runReplyDraft(record)"
              >
                生成英文草稿
              </a-button>
              <pre
                v-if="bridgeCache[record.id]?.body_en"
                class="text-xs bg-green-50 p-2 rounded mt-2 whitespace-pre-wrap"
              >{{ bridgeCache[record.id].body_en }}</pre>
            </div>
            <div>
              <p class="text-gray-500 text-sm mb-1">完整留言内容：</p>
              <p class="text-gray-800 whitespace-pre-wrap">{{ record.message_clean || record.message }}</p>
            </div>
            <div v-if="historyMap[record.id]?.length">
              <p class="text-gray-500 text-sm mb-1">负责人变更记录：</p>
              <ul class="text-sm text-gray-700 space-y-1">
                <li v-for="h in historyMap[record.id]" :key="h.id">
                  {{ formatHistory(h) }}
                </li>
              </ul>
            </div>
            <p v-else-if="historyLoading === record.id" class="text-xs text-gray-400">加载审计…</p>
          </div>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'phone'">
            <a :href="`tel:${record.phone}`" class="phone-link" v-if="record.phone">
              <PhoneOutlined />
              {{ record.phone }}
            </a>
            <span v-else class="text-muted">—</span>
          </template>
          <template v-if="column.key === 'wechat'">
            <span v-if="record.wechat" class="wechat-cell">
              <WechatOutlined />
              {{ record.wechat }}
              <a-button type="link" size="small" @click="copyWechat(record.wechat)" title="复制微信号">
                <CopyOutlined />
              </a-button>
            </span>
            <span v-else class="text-muted">—</span>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'intent'">
            <a-tag v-if="record.intent_level" :color="intentColor(record.intent_level)">
              {{ record.intent_label || record.intent_level }}
            </a-tag>
            <span v-else class="text-muted">—</span>
          </template>
          <template v-if="column.key === 'source'">
            <a-tag v-if="record.source_channel">{{ record.source_channel }}</a-tag>
            <span v-else class="text-muted">—</span>
          </template>
          <template v-if="column.key === 'assignee'">
            <a-select
              v-if="canAssign"
              :value="record.assigned_to || undefined"
              allow-clear
              placeholder="分配"
              size="small"
              style="width: 110px"
              :loading="assigningId === record.id"
              @change="(uid) => assignInquiry(record, uid as string)"
            >
              <a-select-option v-for="u in assignees" :key="u.id" :value="u.id">
                {{ u.username }}
              </a-select-option>
            </a-select>
            <span v-else>{{ record.assigned_to_name || '—' }}</span>
          </template>
          <template v-if="column.key === 'msg'">
            {{ (record.message||'').length>30 ? (record.message||'').slice(0,30)+'...' : record.message }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space :size="4">
              <a-button size="small" @click="markStatus(record,'quoted')" :disabled="record.status!=='pending'">标记处理中</a-button>
              <a-button size="small" @click="markStatus(record,'accepted')" :disabled="record.status==='accepted'" type="primary" ghost>完成</a-button>
              <a-dropdown trigger="click">
                <a-button size="small" @click.prevent>更多</a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="openReply(record)">快速回复</a-menu-item>
                    <a-menu-item danger @click="del(record)">删除</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </YdDataTable>
      </template>
    </div>

    <a-drawer v-model:open="auditPreviewOpen" title="改派审计预览" width="720">
      <a-space class="mb-3" wrap>
        <a-range-picker
          v-model:value="auditDateRange"
          value-format="YYYY-MM-DD"
          :placeholder="['起始', '结束']"
          @change="() => loadAuditPreview(1)"
        />
        <a-select
          v-model:value="auditActorId"
          allow-clear
          placeholder="操作人"
          style="width: 140px"
          @change="() => loadAuditPreview(1)"
        >
          <a-select-option v-for="u in assignees" :key="'a-' + u.id" :value="u.id">
            {{ u.username }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="auditToAssigneeId"
          allow-clear
          placeholder="改派目标"
          style="width: 140px"
          @change="() => loadAuditPreview(1)"
        >
          <a-select-option v-for="u in assignees" :key="'t-' + u.id" :value="u.id">
            {{ u.username }}
          </a-select-option>
        </a-select>
      </a-space>
      <a-table
        :columns="auditCols"
        :data-source="auditRows"
        :loading="auditLoading"
        row-key="log_id"
        size="small"
        :pagination="{
          current: auditPage,
          pageSize: auditPageSize,
          total: auditTotal,
          showSizeChanger: false,
          onChange: loadAuditPreview,
        }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'assign'">
            {{ record.from_assignee_name || '—' }} → {{ record.to_assignee_name || '—' }}
          </template>
        </template>
      </a-table>
      <p class="text-xs text-gray-400 mt-3">
        CSV 导出列：log_id, created_at, action, mode, inquiry_id, inquiry_name, source_channel,
        from_assignee_name, to_assignee_name, <strong>actor_user_name</strong>, actor_user_id, ip_address
        （姓名列在 ID 列之前；无姓名时回退为 ID）
      </p>
    </a-drawer>

    <a-modal v-model:open="replyOpen" title="快速回复" @ok="sendReply" ok-text="发送">
      <a-form layout="vertical">
        <a-form-item label="收件人邮箱">
          <a-input v-model="replyForm.email" />
        </a-form-item>
        <a-form-item label="回复内容">
          <a-textarea v-model="replyForm.content" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  Table as ATable, Tag as ATag,
  Button as AButton, Space as ASpace, Modal as AModal, Form as AForm,
  FormItem as AFormItem, Input as AInput, Textarea as ATextarea,
  RadioGroup as ARadioGroup, RadioButton as ARadioButton,
  Select as ASelect, SelectOption as ASelectOption,
  RangePicker as ARangePicker, Drawer as ADrawer,
  Dropdown as ADropdown, Menu as AMenu, MenuItem as AMenuItem,
  Alert as AAlert,
} from 'ant-design-vue'
import {
  DownloadOutlined,
  DownOutlined,
  PhoneOutlined,
  WechatOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue'
import { getAuthToken } from '@/utils/api'
import { ydConfirm } from '@/utils/ydModal'
import { inquiryBridgeSummary, inquiryReplyDraft } from '@/api/cross-border'
import { useAuthStore } from '@/stores/auth'
import { YdPage, YdStatsCard, YdStatsRow, YdTableColumnSettings, YdTableToolbar, YdDataTable } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { useYoudingColumnLayout } from '@/composables/useYoudingTableBridge'

const authStore = useAuthStore()
const canAssign = computed(() =>
  ['admin', 'super_admin', 'tenant_admin'].includes(authStore.currentRole || '')
)

const list = ref<any[]>([])
const loading = ref(false)
const initialLoading = ref(true)
const tablePanelRef = ref<HTMLElement | null>(null)
const assignees = ref<Array<{ id: string; username: string; role: string }>>([])
const assigningId = ref('')
const historyMap = ref<Record<string, Array<Record<string, string>>>>({})
const historyLoading = ref('')
const filterTab = ref('')
const sourceFilter = ref<string | undefined>(undefined)
const auditDateRange = ref<[string, string] | undefined>(undefined)
const auditPreviewOpen = ref(false)
const auditLoading = ref(false)
const auditRows = ref<Record<string, string>[]>([])
const auditPage = ref(1)
const auditPageSize = ref(20)
const auditTotal = ref(0)
const auditActorId = ref<string | undefined>()
const auditToAssigneeId = ref<string | undefined>()
const bridgeCache = reactive<Record<string, { summary_zh?: string; body_en?: string }>>({})
const bridgeBossZh = reactive<Record<string, string>>({})
const bridgeLoadingId = ref('')
const bridgeMode = ref<'summary' | 'reply' | ''>('')
const auditCols = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作人', dataIndex: 'actor_user_name', key: 'actor_user_name', width: 100 },
  { title: '模式', dataIndex: 'mode', key: 'mode', width: 90 },
  { title: '询盘', dataIndex: 'inquiry_name', key: 'inquiry_name', ellipsis: true },
  { title: '来源', dataIndex: 'source_channel', key: 'source_channel', width: 120 },
  { title: '改派', key: 'assign', width: 180 },
]
const replyOpen = ref(false)
const replyForm = reactive({ email: '', content: '' })
const stats = reactive({ today: 0, pending: 0, month: 0, rate: 0 })

const baseInquiryColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80, ellipsis: true },
  { title: '姓名', dataIndex: 'customer_name', key: 'customer_name', width: 100 },
  { title: '电话', key: 'phone', width: 140 },
  { title: '邮箱', dataIndex: 'email', key: 'email', width: 160 },
  { title: '产品/公司', dataIndex: 'product_interest', key: 'product_interest', width: 120 },
  { title: '意向', key: 'intent', width: 88 },
  { title: '来源', key: 'source', width: 120 },
  { title: '负责人', key: 'assignee', width: 100 },
  { title: '留言', key: 'msg', width: 160 },
  { title: '状态', key: 'status', width: 90 },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
  { title: '操作', key: 'actions', width: 220 },
]

const {
  orderedColumns: orderedInquiryColumns,
  visibleColumns: visibleInquiryColumns,
  hiddenColumnKeys,
  toggleColumnVisibility,
  moveColumnUp,
  moveColumnDown,
  resetColumnLayout,
} = useYoudingColumnLayout(baseInquiryColumns, 'admin-inquiries-cols')

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    quoted: '处理中',
    accepted: '已完成',
    rejected: '已关闭',
  }
  return map[status] || status
}

function statusColor(status: string) {
  if (status === 'pending') return 'blue'
  if (status === 'quoted') return 'orange'
  if (status === 'accepted') return 'green'
  return 'default'
}

function intentColor(level: string) {
  if (level === 'high') return 'red'
  if (level === 'medium') return 'orange'
  return 'default'
}

async function runBridgeSummary(record: Record<string, unknown>) {
  const id = String(record.id || '')
  if (!id) return
  bridgeLoadingId.value = id
  bridgeMode.value = 'summary'
  try {
    const res = await inquiryBridgeSummary(id)
    bridgeCache[id] = { ...(bridgeCache[id] || {}), summary_zh: res.summary_zh }
    if (res.mode === 'mock') {
      message.warning('未接 AI Key：当前为占位摘要，请配置 Key 后重试')
    } else {
      message.success('中文摘要已生成')
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '摘要失败')
  } finally {
    bridgeLoadingId.value = ''
    bridgeMode.value = ''
  }
}

async function runReplyDraft(record: Record<string, unknown>) {
  const id = String(record.id || '')
  const zh = (bridgeBossZh[id] || '').trim()
  if (!id || !zh) {
    message.warning('请先填写中文回复要点')
    return
  }
  bridgeLoadingId.value = id
  bridgeMode.value = 'reply'
  try {
    const res = await inquiryReplyDraft(id, zh)
    bridgeCache[id] = { ...(bridgeCache[id] || {}), body_en: res.body_en }
    if (res.mode === 'mock') {
      message.warning('未接 AI Key：当前为占位草稿，禁止直接发送')
    } else {
      message.success('英文草稿已生成')
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '草稿失败')
  } finally {
    bridgeLoadingId.value = ''
    bridgeMode.value = ''
  }
}

function copyDiscovery(record: Record<string, unknown>) {
  const qs = (record.discovery_questions as Array<{ question?: string }>) || []
  const text = qs.map((q, i) => `${i + 1}. ${q.question || ''}`).join('\n')
  navigator.clipboard.writeText(text).then(() => {
    message.success('追问话术已复制')
  }).catch(() => {
    message.warning(text || '无追问内容')
  })
}

function mapRow(item: Record<string, unknown>) {
  return {
    ...item,
    customer_name: item.name || item.customer_name,
    product_interest: item.product || item.product_interest,
  }
}

async function loadAssignees() {
  if (!canAssign.value) return
  try {
    const r = await fetch('/api/v1/inquiries/assignees', {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    const d = await r.json()
    assignees.value = d.data || []
  } catch {
    assignees.value = []
  }
}

async function assignInquiry(record: Record<string, unknown>, userId: string) {
  const id = String(record.id ?? '')
  if (!id || !userId) return
  assigningId.value = id
  try {
    const r = await fetch(`/api/v1/inquiries/${id}/assign`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({ assigned_to: userId }),
    })
    const d = await r.json()
    if (!r.ok || d.code !== 0) throw new Error(d.message || '改派失败')
    message.success(`已改派给 ${d.data?.assigned_to_name || userId}`)
    delete historyMap.value[id]
    await loadData()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '改派失败')
  } finally {
    assigningId.value = ''
  }
}

async function loadData() {
  loading.value = true
  try {
    const p = new URLSearchParams()
    p.set('page', '1')
    p.set('page_size', '200')
    if (filterTab.value) p.set('status', filterTab.value)
    if (sourceFilter.value) p.set('source_channel', sourceFilter.value)
    const r = await fetch('/api/v1/inquiries/unified?' + p.toString(), {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    const d = await r.json()
    const items = (d.data?.items || d.items || []).map(mapRow)
    list.value = items
    const today = new Date().toISOString().slice(0, 10)
    const month = new Date().toISOString().slice(0, 7)
    stats.today = items.filter((x: { created_at?: string }) => x.created_at?.startsWith(today)).length
    stats.pending = items.filter((x: { status?: string }) => x.status === 'pending').length
    stats.month = items.filter((x: { created_at?: string }) => x.created_at?.startsWith(month)).length
    stats.rate = stats.month > 0
      ? Math.round((items.filter((x: { status?: string }) => x.status === 'accepted').length / Math.max(stats.month, 1)) * 100)
      : 0
  } catch (e) { if (import.meta.env.DEV) console.error(e) }
  finally { loading.value = false; initialLoading.value = false }
}

function formatHistory(h: Record<string, string>) {
  const mode = h.mode === 'auto' ? '自动分配' : '手动改派'
  const from = h.from_assignee_name || '—'
  const to = h.to_assignee_name || h.to_assignee_id || '—'
  const actor = h.actor_user_name || h.actor_user_id || '—'
  const at = h.created_at ? h.created_at.replace('T', ' ').slice(0, 19) : ''
  return `${at} · ${mode} · 操作人 ${actor}：${from} → ${to}`
}

async function onExpand(expanded: boolean, record: { id: string }) {
  if (!expanded || historyMap.value[record.id]) return
  historyLoading.value = record.id
  try {
    const r = await fetch(`/api/v1/inquiries/${record.id}/assignment-history`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    const d = await r.json()
    historyMap.value[record.id] = d.data || []
  } catch {
    historyMap.value[record.id] = []
  } finally {
    historyLoading.value = ''
  }
}

async function markStatus(record: Record<string, unknown>, status: string) {
  const id = String(record.id ?? '')
  if (!id) return
  try {
    const r = await fetch(`/api/v1/inquiries/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ status }),
    })
    if (r.ok) { message.success('状态已更新'); loadData() } else { message.error('更新失败') }
  } catch (e: any) { message.error(e.message) }
}

function openReply(record: any) {
  replyForm.email = record.email || ''
  replyForm.content = `尊敬的${record.customer_name || '客户'}，\n\n感谢您对${record.product_interest || '我们产品'}的关注。\n\n我们将尽快与您联系，为您提供详细的产品资料和报价。\n\n祝商祺！`
  replyOpen.value = true
}

async function sendReply() {
  message.warning('邮件 SMTP 尚未接入：请用下方「语言桥」生成英文草稿后自行发送')
  replyOpen.value = false
}

function del(record: any) {
  ydConfirm({
    title: '确认删除', content: `确定删除「${record.customer_name}」的询盘？`, okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await fetch(`/api/v1/inquiries/${record.id}`, {
            method: 'DELETE', headers: { Authorization: `Bearer ${getAuthToken()}` }
          })
          message.success('已删除'); loadData()
        } catch (e: any) { message.error(e.message) }
      })();
    }
  })
}

function copyWechat(wechat: string) {
  navigator.clipboard.writeText(wechat).then(() => {
    message.success(`微信号已复制: ${wechat}`)
  }).catch(() => {
    message.success(`微信号: ${wechat}`)
  })
}

function exportInquiries() {
  const headers = ['姓名', '电话', '微信', '邮箱', '产品意向', '意向', '留言内容', '时间', '状态']
  const rows = list.value.map((item: any) => [
    item.customer_name || '',
    item.phone || '',
    item.wechat || '',
    item.email || '',
    item.product_interest || '',
    item.intent_label || '',
    (item.message_clean || item.message || '').replace(/"/g, '""'),
    item.created_at || '',
    item.status === 'new' ? '新询盘' : item.status === 'processing' ? '处理中' : '已完成',
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `询盘数据_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  message.success(`已导出 ${rows.length} 条询盘记录`)
}

async function exportAssignmentAudit() {
  if (!['admin', 'super_admin'].includes(authStore.currentRole || '')) {
    message.warning('仅管理员可导出改派审计')
    return
  }
  try {
    const params = new URLSearchParams()
    if (sourceFilter.value) params.set('source_channel', sourceFilter.value)
    if (auditDateRange.value?.[0]) params.set('start_at', auditDateRange.value[0])
    if (auditDateRange.value?.[1]) params.set('end_at', auditDateRange.value[1])
    if (auditActorId.value) params.set('actor_user_id', auditActorId.value)
    if (auditToAssigneeId.value) params.set('to_assignee_id', auditToAssigneeId.value)
    const qs = params.toString()
    const url = `/api/v1/inquiries/assignment-audit/export${qs ? `?${qs}` : ''}`
    const r = await fetch(url, { headers: { Authorization: `Bearer ${getAuthToken()}` } })
    if (!r.ok) {
      message.error('导出失败')
      return
    }
    const blob = await r.blob()
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = `inquiry_assignment_audit_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(objectUrl)
    message.success('改派审计 CSV 已下载')
  } catch (e) {
    message.error(e instanceof Error ? e.message : '导出失败')
  }
}

function openAuditPreview() {
  if (!['admin', 'super_admin'].includes(authStore.currentRole || '')) {
    message.warning('仅管理员可查看改派审计')
    return
  }
  auditPreviewOpen.value = true
  loadAuditPreview(1)
}

async function loadAuditPreview(page = 1) {
  auditLoading.value = true
  auditPage.value = page
  try {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(auditPageSize.value))
    if (sourceFilter.value) params.set('source_channel', sourceFilter.value)
    if (auditDateRange.value?.[0]) params.set('start_at', auditDateRange.value[0])
    if (auditDateRange.value?.[1]) params.set('end_at', auditDateRange.value[1])
    if (auditActorId.value) params.set('actor_user_id', auditActorId.value)
    if (auditToAssigneeId.value) params.set('to_assignee_id', auditToAssigneeId.value)
    const r = await fetch(`/api/v1/inquiries/assignment-audit?${params}`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '加载失败')
      return
    }
    auditRows.value = d.data?.items || []
    auditTotal.value = d.data?.total || 0
  } catch (e) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    auditLoading.value = false
  }
}

onMounted(async () => {
  await loadAssignees()
  await loadData()
})
</script>

<style scoped>
.inquiries-kpi-row {
  margin-bottom: 16px;
}
.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.inquiry-page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.header-actions { display: flex; gap: 8px; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.phone-link { color: #1890ff; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; }
.phone-link:hover { color: #40a9ff; text-decoration: underline; }
.wechat-cell { display: inline-flex; align-items: center; gap: 4px; }
.text-muted { color: #999; }
</style>
