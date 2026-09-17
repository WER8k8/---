/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="平台凭证与真发就绪"
    subtitle="各平台要哪些凭证、当前缺什么、会话是否过期（凭证只显字段名与掩码）"
    surface="elevated"
  >
    <div class="mb-4 flex flex-wrap gap-3 items-center">
      <a-select
        v-model:value="filterPlatform"
        allow-clear
        show-search
        option-filter-prop="label"
        placeholder="按平台筛选"
        style="min-width: 200px"
        :options="platformOptions"
        @change="loadAccounts"
      />
      <a-button type="primary" :loading="loading" @click="loadAll">刷新</a-button>
      <a-button :loading="patrolling" @click="runPatrol(true)">试跑会话巡检</a-button>
      <a-tooltip title="把判定过期的账号真正置为 expired；置后不会自动恢复，须重绑再手动改回">
        <a-button danger :loading="patrolling" @click="runPatrol(false)">执行巡检</a-button>
      </a-tooltip>
      <a-tag v-if="staleDays" color="default">cookie 老化阈值 {{ staleDays }} 天</a-tag>
    </div>

    <div class="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="border rounded-lg p-3">
        <div class="text-xs text-gray-500">平台账号</div>
        <div class="text-xl font-semibold">{{ rows.length }}</div>
      </div>
      <div class="border rounded-lg p-3">
        <div class="text-xs text-gray-500">可真发</div>
        <div class="text-xl font-semibold">{{ countBy((r) => Boolean(r.credential_status?.publish_ready)) }}</div>
      </div>
      <div class="border rounded-lg p-3">
        <div class="text-xs text-gray-500">缺凭证字段</div>
        <div class="text-xl font-semibold">{{ countBy((r) => (r.credential_status?.missing_fields?.length ?? 0) > 0) }}</div>
      </div>
      <div class="border rounded-lg p-3">
        <div class="text-xs text-gray-500">会话已过期</div>
        <div class="text-xl font-semibold">{{ countBy((r) => r.login_status === 'expired') }}</div>
      </div>
    </div>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      row-key="id"
      size="middle"
      :pagination="{ pageSize: 20, showTotal: (t: number) => `共 ${t} 条` }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'login_status'">
          <a-tag :color="statusColor(record.login_status)">{{ statusLabel(record.login_status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'publish_ready'">
          <a-tag :color="record.credential_status?.publish_ready ? 'green' : 'orange'">
            {{ record.credential_status?.publish_ready ? '就绪' : '未就绪' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'fields'">
          <span v-if="!record.credential_status?.credential_fields?.length" class="text-xs text-gray-400">
            无任何凭证
          </span>
          <a-tag v-for="f in record.credential_status?.credential_fields || []" :key="f.name" class="mb-1">
            {{ f.name }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'missing'">
          <span v-if="!record.credential_status?.missing_fields?.length" class="text-xs text-gray-400">—</span>
          <a-tag v-for="m in record.credential_status?.missing_fields || []" :key="m" color="red" class="mb-1">
            {{ m }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-button size="small" @click="openEditor(record as AccountRow)">填凭证</a-button>
        </template>
      </template>
    </a-table>

    <a-divider orientation="left">环境变量类凭证（改 backend/.env，不走本面板）</a-divider>
    <a-table
      :columns="envColumns"
      :data-source="envRows"
      row-key="env"
      size="small"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'configured'">
          <a-tag :color="record.configured ? 'green' : 'default'">
            {{ record.configured ? '已配置' : '未配置' }}
          </a-tag>
        </template>
      </template>
    </a-table>
    <p class="mt-2 text-xs text-gray-500">{{ storageNote }}</p>

    <a-drawer v-model:open="editorOpen" :title="editorTitle" width="560" :body-style="{ paddingBottom: 80 }">
      <a-alert
        v-if="editorGuide"
        type="info"
        show-icon
        class="mb-3"
        :message="editorGuide.label"
        :description="guideHint(editorGuide)"
      />
      <a-alert
        v-else
        type="warning"
        show-icon
        class="mb-3"
        message="该平台未登记凭证指引"
        description="仍可直接填 cookie 或 token_data；保存后系统按「有无凭证」判定就绪，不做字段级校验。"
      />

      <a-form layout="vertical">
        <a-form-item label="登录 Cookie 串">
          <a-textarea v-model:value="form.cookie" :rows="3" placeholder="整条 request cookie，留空表示不改动" />
        </a-form-item>
        <a-form-item label="token_data（JSON）">
          <a-textarea
            v-model:value="form.tokenData"
            :rows="4"
            placeholder='{"app_id":"...","app_secret":"..."}，按键合并，不整体覆盖'
          />
        </a-form-item>
        <a-form-item label="configs（运营参数）">
          <div v-for="(row, idx) in form.configs" :key="idx" class="flex gap-2 mb-2">
            <a-input v-model:value="row.k" placeholder="键" style="width: 40%" />
            <a-input v-model:value="row.v" placeholder="值" style="flex: 1" />
            <a-button size="small" @click="form.configs.splice(idx, 1)">删</a-button>
          </div>
          <a-button size="small" @click="form.configs.push({ k: '', v: '' })">加一项</a-button>
        </a-form-item>
        <a-form-item label="会话状态">
          <a-select v-model:value="form.loginStatus" :options="statusOptions" style="width: 200px" />
          <div class="text-xs text-gray-500 mt-1">巡检只负责摘出过期号，重绑完成后需在此改回 logged_in。</div>
        </a-form-item>
      </a-form>

      <div class="drawer-footer">
        <a-button @click="editorOpen = false">取消</a-button>
        <a-button type="primary" :loading="saving" @click="save">保存凭证</a-button>
      </div>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { seoMatrixAPI } from '@/api'

interface CredField { name: string; masked: string }
interface CredentialStatus {
  has_credentials: boolean
  credential_fields: CredField[]
  missing_fields: string[]
  publish_ready: boolean
  guide_key?: string | null
  credential_source?: string | null
}
interface AccountRow {
  id: string
  platform_id: string
  platform_name?: string
  account_name?: string
  login_status?: string
  credential_status?: CredentialStatus
}
interface Guide {
  key: string
  label: string
  storage?: string
  platform_names?: string[]
  env?: string[]
  steps?: string[]
  caveats?: string[]
  fields?: { name: string; label?: string; apply?: string; apply_url?: string }[]
}

const loading = ref(false)
const patrolling = ref(false)
const saving = ref(false)
const rows = ref<AccountRow[]>([])
const guides = ref<Guide[]>([])
const envRows = ref<{ env: string; configured: boolean }[]>([])
const storageNote = ref('')
const staleDays = ref(14)
const filterPlatform = ref<string | undefined>()
const editorOpen = ref(false)
const editorRow = ref<AccountRow | null>(null)
const form = reactive({
  cookie: '',
  tokenData: '',
  configs: [] as { k: string; v: string }[],
  loginStatus: 'logged_in',
})

const statusOptions = [
  { value: 'logged_in', label: 'logged_in（有效）' },
  { value: 'expired', label: 'expired（已过期）' },
  { value: 'pending', label: 'pending（待绑定）' },
  { value: 'failed', label: 'failed（绑定失败）' },
]

const columns = [
  { title: '平台', dataIndex: 'platform_name', key: 'platform_name', width: 150 },
  { title: '账号', dataIndex: 'account_name', key: 'account_name', width: 160, ellipsis: true },
  { title: '会话', key: 'login_status', width: 110 },
  { title: '真发', key: 'publish_ready', width: 90 },
  { title: '已有字段（掩码）', key: 'fields', ellipsis: true },
  { title: '缺失必填', key: 'missing', width: 200 },
  { title: '操作', key: 'action', width: 90 },
]

const envColumns = [
  { title: '环境变量', dataIndex: 'env', key: 'env', width: 260 },
  { title: '状态', key: 'configured', width: 120 },
  {
    title: '申请入口',
    key: 'apply',
    customRender: ({ record }: { record: { env: string } }) => applyUrlFor(record.env) || '—',
  },
]

const platformOptions = computed(() => {
  const seen = new Map<string, string>()
  rows.value.forEach((r) => {
    const name = r.platform_name || r.platform_id
    if (name) seen.set(r.platform_id, name)
  })
  return [...seen.entries()].map(([value, label]) => ({ value, label }))
})

const editorTitle = computed(() => {
  const r = editorRow.value
  return r ? `${r.platform_name || ''} · ${r.account_name || r.id}` : '填写凭证'
})

const editorGuide = computed<Guide | undefined>(() => {
  const key = editorRow.value?.credential_status?.guide_key
  if (!key) return undefined
  return guides.value.find((g) => g.key === key)
})

function countBy(pred: (r: AccountRow) => boolean) {
  return rows.value.filter(pred).length
}

function statusLabel(s?: string) {
  return (
    { logged_in: '有效', expired: '已过期', pending: '待绑定', failed: '失败' }[s || ''] || s || '未知'
  )
}

function statusColor(s?: string) {
  if (s === 'logged_in') return 'green'
  if (s === 'expired') return 'red'
  if (s === 'failed') return 'orange'
  return 'default'
}

function applyUrlFor(envName: string) {
  for (const g of guides.value) {
    const hit = (g.env || []).includes(envName)
    if (!hit) continue
    const field = (g.fields || []).find((f) => f.name === envName)
    return field?.apply_url || ''
  }
  return ''
}

function guideHint(g: Guide) {
  const parts: string[] = []
  if (g.steps?.length) parts.push(`步骤：${g.steps.join('；')}`)
  if (g.caveats?.length) parts.push(`注意：${g.caveats.join('；')}`)
  return parts.join(' | ')
}

async function loadGuides() {
  const res = await seoMatrixAPI.getPlatformCredentialGuide()
  const raw = res as unknown as { data?: Record<string, unknown> }
  const data = (raw.data || raw) as Record<string, unknown>
  guides.value = ((data.guides as Guide[]) || []).filter(Boolean)
  envRows.value = ((data.env_status as { env: string; configured: boolean }[]) || []).filter(Boolean)
  storageNote.value = String(data.storage_note || '')
}

async function loadAccounts() {
  loading.value = true
  try {
    const res = await seoMatrixAPI.getPlatformAccounts()
    const data = (res as { data?: unknown }).data ?? res
    let list = Array.isArray(data) ? data : ((data as { items?: AccountRow[] })?.items ?? [])
    if (filterPlatform.value) {
      list = (list as AccountRow[]).filter((r) => r.platform_id === filterPlatform.value)
    }
    rows.value = list as AccountRow[]
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载平台账号失败')
  } finally {
    loading.value = false
  }
}

function openEditor(row: AccountRow) {
  editorRow.value = row
  form.cookie = ''
  form.tokenData = ''
  form.configs = []
  form.loginStatus = row.login_status || 'logged_in'
  editorOpen.value = true
}

async function save() {
  const row = editorRow.value
  if (!row) return
  const payload: Record<string, unknown> = { login_status: form.loginStatus }
  if (form.cookie.trim()) payload.cookie_data = form.cookie.trim()
  if (form.tokenData.trim()) {
    try {
      payload.token_data = JSON.parse(form.tokenData)
    } catch {
      message.error('token_data 不是合法 JSON，请检查后重试')
      return
    }
  }
  const configs: Record<string, string> = {}
  form.configs.forEach((c) => {
    if (c.k.trim() && c.v.trim()) configs[c.k.trim()] = c.v.trim()
  })
  if (Object.keys(configs).length) payload.configs = configs

  saving.value = true
  try {
    const res = await seoMatrixAPI.updatePlatformAccount(row.id, payload)
    const data = (res as { data?: { credential_fields_written?: number } }).data
    const written = data?.credential_fields_written ?? 0
    message.success(written ? `已写入 ${written} 个凭证字段` : '已保存（本次未写入凭证字段）')
    editorOpen.value = false
    await loadAccounts()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function runPatrol(dryRun: boolean) {
  patrolling.value = true
  try {
    const res = await seoMatrixAPI.patrolPlatformSessions({ dry_run: dryRun })
    const data = ((res as { data?: Record<string, unknown> }).data || res) as Record<string, unknown>
    staleDays.value = Number(data.cookie_stale_days) || staleDays.value
    const findings = (data.findings as unknown[]) || []
    if (dryRun) {
      message.info(
        findings.length ? `试跑：${findings.length} 个账号会被判过期（未改库）` : '试跑：无账号命中',
      )
    } else {
      message.info(
        findings.length ? `巡检完成，已置 expired ${data.expired_marked ?? 0} 个` : '巡检完成，无账号命中',
      )
    }
    await loadAccounts()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '巡检失败')
  } finally {
    patrolling.value = false
  }
}

async function loadAll() {
  await Promise.all([loadGuides(), loadAccounts()])
}

onMounted(loadAll)
</script>

<style scoped>
.drawer-footer {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  gap: 8px;
}
</style>
