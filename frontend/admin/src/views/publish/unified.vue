<template>

  <YdPage title="统一发布台" subtitle="GEO 内容矩阵 → 母版人审 → 按平台变体发布" surface="elevated">

    <a-card title="① GEO 内容矩阵（AI 写稿 + 多平台变体）" class="mb-4">

      <a-form layout="vertical">

        <a-row :gutter="16">

          <a-col :span="12">

            <a-form-item label="业务领域 / 品类">

              <a-input v-model:value="geoForm.domain" placeholder="如：岩棉保温棉出口" />

            </a-form-item>

          </a-col>

          <a-col :span="12">

            <a-form-item label="核心关键词（逗号分隔）">

              <a-input v-model:value="geoForm.target_keywords" placeholder="rock wool, A1, B2B export" />

            </a-form-item>

          </a-col>

        </a-row>

        <a-form-item label="目标平台（变体将按平台名生成）">

          <a-checkbox-group v-model:value="geoForm.platforms" :options="geoPlatformOptions" />

        </a-form-item>

        <a-space wrap>

          <a-button type="primary" :loading="geoRunning" @click="runGeoMatrix">

            生成 GEO 内容矩阵

          </a-button>

          <a-button v-if="geoJobId" :loading="geoPolling" @click="pollGeoJob">刷新任务</a-button>

        </a-space>

      </a-form>

      <a-alert

        v-if="geoJobStatus"

        class="mt-3"

        :type="geoJobStatus === 'success' ? 'success' : geoJobStatus === 'failed' ? 'error' : 'info'"

        show-icon

        :message="geoJobMessage"

      />

      <ul v-if="geoDrafts.length" class="draft-list mt-3">

        <li v-for="d in geoDrafts" :key="d.id">

          <button type="button" class="draft-link" @click="selectDraft(d)">

            {{ d.title }}

          </button>

          <span class="draft-meta">{{ d.status }}</span>

        </li>

      </ul>

    </a-card>



    <a-card title="② 编辑 / 保存母版" class="mb-4">

      <a-form layout="vertical">

        <a-form-item v-if="!tenantId" label="租户 ID">

          <a-input v-model:value="form.tenant_id" placeholder="租户 UUID（未自动识别时填写）" />

        </a-form-item>

        <a-form-item label="标题">

          <a-input v-model:value="form.title" />

        </a-form-item>

        <a-form-item label="正文（Markdown）">

          <a-textarea v-model:value="form.body" :rows="8" />

        </a-form-item>

        <a-form-item label="落地页 URL（主链 / UTM）">

          <a-input v-model:value="form.tenant_canonical_url" placeholder="https://www.xxxx.com/..." />

        </a-form-item>

        <a-button type="primary" :loading="saving" @click="saveMaster">保存母版</a-button>

      </a-form>

      <div v-if="masterId" class="mt-3 text-green-700">当前母版 ID：{{ masterId }}</div>

    </a-card>



    <a-card v-if="masterId" title="②b 发布前人审清单（GW-G-CC-04）" class="mb-4">

      <p class="hint">勾选后系统才允许创建发布任务；含认证/数字/MOQ 表述时须全部确认。</p>

      <a-checkbox-group v-model:value="preflightChecked" class="preflight-checks">

        <a-checkbox value="moq_verified">MOQ / 起订量已核对</a-checkbox>

        <a-checkbox value="certification_claims_reviewed">认证表述已人审</a-checkbox>

        <a-checkbox value="numbers_reviewed">价格/数量/交期数字已核对</a-checkbox>

        <a-checkbox value="human_approved">我已批准对外发布</a-checkbox>

      </a-checkbox-group>

      <a-space class="mt-3" wrap>

        <a-button size="small" :loading="preflightScanning" @click="scanPreflight">扫描风险</a-button>

        <a-button size="small" :loading="preflightSaving" @click="savePreflightChecklist">保存清单</a-button>

      </a-space>

      <a-alert

        v-if="preflightResult"

        class="mt-3"

        :type="preflightResult.blocked ? 'warning' : 'success'"

        show-icon

        :message="preflightResult.message || (preflightResult.blocked ? '发布将被阻断' : '人审通过')"

      />

      <ul v-if="preflightResult?.content_risks?.length" class="risk-list mt-2">

        <li v-for="r in preflightResult.content_risks" :key="r.code">{{ r.message }}</li>

      </ul>

    </a-card>



    <a-card v-if="masterId || geoDraftIds.length" title="③ 人审通过 · 按平台变体发布">

      <a-alert
        v-if="platformBindWarning"
        type="warning"
        show-icon
        class="mb-3"
        message="部分平台账号未绑定"
        :description="platformBindWarning"
      />

      <p class="hint">

        勾选平台后点击「按变体创建发布任务」：系统会自动匹配标题以

        <code>[平台名]</code> 开头的草稿；若无变体则使用当前母版。

      </p>

      <a-checkbox-group v-model:value="selectedPlatforms" :options="platformOptions" />

      <a-space class="mt-4" wrap>

        <a-button type="primary" :loading="publishing" @click="submitPublish">

          单母版发布（全部平台同一正文）

        </a-button>

        <a-button type="default" :loading="publishingVariants" @click="submitAutoVariants">

          按变体创建发布任务

        </a-button>

      </a-space>

      <p v-if="lastResult" class="mt-3">{{ lastResult }}</p>

    </a-card>

  </YdPage>

</template>



<script setup lang="ts">

import { onMounted, ref } from 'vue'

import { useRoute } from 'vue-router'

import { YdPage } from '@/components/youding'

import { message } from 'ant-design-vue'

import { apiGet, apiPost } from '@/utils/api'

import { publishPreflight, saveContentMasterPreflight } from '@/api/foreign-trade'



const route = useRoute()



type DraftRow = {
  id: string
  title: string
  status: string
  body?: string
  preflight_checklist?: Record<string, boolean>
  preflight_approved_at?: string | null
}



const tenantId = ref('')

const form = ref({

  tenant_id: '',

  title: '',

  body: '',

  tenant_canonical_url: '',

})

const masterId = ref('')

const saving = ref(false)

const publishing = ref(false)

const publishingVariants = ref(false)

const platformOptions = ref<{ label: string; value: string }[]>([])

const selectedPlatforms = ref<string[]>([])

const lastResult = ref('')



const geoForm = ref({

  domain: '',

  target_keywords: '',

  platforms: ['LinkedIn', '百家号', '抖音', '小红书'] as string[],

})

const geoPlatformOptions = ['LinkedIn', '百家号', '抖音', '小红书', '视频号', '知乎'].map((p) => ({

  label: p,

  value: p,

}))

const geoRunning = ref(false)

const geoPolling = ref(false)

const geoJobId = ref('')

const geoJobStatus = ref('')

const geoJobMessage = ref('')

const geoDrafts = ref<DraftRow[]>([])

const geoDraftIds = ref<string[]>([])

const platformBindWarning = ref('')

const preflightChecked = ref<string[]>([])

const preflightSaving = ref(false)

const preflightScanning = ref(false)

const preflightResult = ref<{

  blocked?: boolean

  message?: string

  content_risks?: Array<{ code: string; message: string }>

} | null>(null)

function preflightPayload() {

  const checklist: Record<string, boolean> = {}

  for (const k of preflightChecked.value) checklist[k] = true

  return checklist

}

function applyPreflightFromDraft(checklist?: Record<string, boolean>) {
  if (!checklist) {
    preflightChecked.value = []
    return
  }
  preflightChecked.value = Object.entries(checklist)
    .filter(([, v]) => v)
    .map(([k]) => k)
}

async function savePreflightChecklist() {
  if (!masterId.value) {
    message.warning('请先保存母版')
    return
  }
  preflightSaving.value = true
  try {
    await saveContentMasterPreflight(masterId.value, preflightPayload())
    message.success('人审清单已保存')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    preflightSaving.value = false
  }
}

async function scanPreflight() {

  if (!masterId.value) {

    message.warning('请先保存母版')

    return

  }

  preflightScanning.value = true

  try {

    preflightResult.value = await publishPreflight(masterId.value, preflightPayload())

  } catch (e: unknown) {

    message.error(e instanceof Error ? e.message : '扫描失败')

  } finally {

    preflightScanning.value = false

  }

}

async function loadPlatformBindStatus() {
  try {
    const snap = await apiGet<{
      platform_accounts_unbound?: number
      platform_accounts_total?: number
      platform_accounts_bound?: number
    }>('/ubrain/ops-snapshot')
    const unbound = snap?.platform_accounts_unbound ?? 0
    const total = snap?.platform_accounts_total ?? 0
    const bound = snap?.platform_accounts_bound ?? 0
    if (total > 0 && unbound > 0) {
      platformBindWarning.value = `已绑定 ${bound}/${total} 个平台账号，${unbound} 个未绑定。发布任务可能失败，请先在开户向导完成 OAuth/Cookie 绑定。`
    } else {
      platformBindWarning.value = ''
    }
  } catch {
    platformBindWarning.value = ''
  }
}

async function resolveTenant() {

  if (tenantId.value) return tenantId.value

  try {

    const dash = await apiGet<{ tenant_id?: string; tenant?: { id?: string } }>('/client/dashboard')

    const tid = dash?.tenant_id || dash?.tenant?.id

    if (tid) {

      tenantId.value = String(tid)

      form.value.tenant_id = tenantId.value

      return tenantId.value

    }

  } catch {

    /* ignore */

  }

  try {

    const cur = await apiGet<{ tenant?: { id?: string } }>('/tenants/current')

    const tid = cur?.tenant?.id

    if (tid) {

      tenantId.value = String(tid)

      form.value.tenant_id = tenantId.value

      return tenantId.value

    }

  } catch {

    /* ignore */

  }

  return form.value.tenant_id

}



async function loadPlatforms() {

  try {

    const res = await apiGet<{ items?: unknown[] }>('/platforms')

    const list = res?.items ?? res ?? []

    platformOptions.value = (list as { name?: string; id: string; region?: string }[]).map((p) => ({

      label: `${p.name} (${p.region || 'cn'})`,

      value: p.id,

    }))

  } catch {

    platformOptions.value = []

  }

}



async function loadDrafts() {

  const tid = await resolveTenant()

  if (!tid) return

  try {

    const res = await apiGet<{ items?: DraftRow[] }>('/content-masters', {

      tenant_id: tid,

      page: 1,

      page_size: 30,

    })

    geoDrafts.value = res?.items ?? []

  } catch {

    geoDrafts.value = []

  }

}



function selectDraft(d: DraftRow) {

  masterId.value = d.id

  form.value.title = d.title

  form.value.body = d.body || ''

  applyPreflightFromDraft(d.preflight_checklist)

  preflightResult.value = null

  message.info('已载入草稿，请人审后保存或发布')

}



async function runGeoMatrix() {

  geoRunning.value = true

  geoJobStatus.value = ''

  try {

    const msg = `GEO 内容矩阵 ${geoForm.value.domain || '建材出口'} 关键词 ${geoForm.value.target_keywords || ''}`.trim()

    const res = await apiPost<{

      job_id?: string

      job_status?: string

      cms_draft_count?: number

      masters?: { id?: string }[]

    }>('/ubrain/geo-content-matrix', {

      message: msg,

      domain: geoForm.value.domain || undefined,

      target_keywords: geoForm.value.target_keywords || undefined,

      platforms: geoForm.value.platforms,

      article_count: 1,

      async_job: false,

    })

    geoJobId.value = res?.job_id || ''

    geoJobStatus.value = res?.job_status || 'success'

    geoJobMessage.value = `已写入 ${res?.cms_draft_count ?? 0} 条草稿，请到下方人审。`

    geoDraftIds.value = (res?.masters || []).map((m) => m.id).filter(Boolean) as string[]

    message.success('GEO 内容矩阵完成')

    await loadDrafts()

  } catch (e: unknown) {

    const err = e as { message?: string }

    geoJobStatus.value = 'failed'

    geoJobMessage.value = err?.message || '生成失败'

    message.error(geoJobMessage.value)

  } finally {

    geoRunning.value = false

  }

}



async function pollGeoJob() {

  if (!geoJobId.value) return

  geoPolling.value = true

  try {

    const res = await apiGet<{ status?: string; result?: { cms_draft_count?: number; masters?: { id?: string }[] } }>(

      `/ubrain/jobs/${geoJobId.value}`,

    )

    geoJobStatus.value = res?.status || ''

    const r = res?.result || {}

    geoJobMessage.value = `状态 ${res?.status} · 草稿 ${r.cms_draft_count ?? 0} 条`

    geoDraftIds.value = (r.masters || []).map((m) => m.id).filter(Boolean) as string[]

    if (res?.status === 'success') await loadDrafts()

  } catch (e: unknown) {

    const err = e as { message?: string }

    message.error(err?.message || '刷新失败')

  } finally {

    geoPolling.value = false

  }

}



async function saveMaster() {

  const tid = await resolveTenant()

  if (!tid || !form.value.title) {

    message.warning('请填写租户与标题')

    return

  }

  form.value.tenant_id = tid

  saving.value = true

  try {

    const res = await apiPost<{ id: string }>('/content-masters', form.value)

    masterId.value = res.id

    message.success('母版已保存')

    await loadDrafts()

  } catch (e: unknown) {

    const err = e as { message?: string }

    message.error(err?.message || '保存失败')

  } finally {

    saving.value = false

  }

}



async function submitPublish() {

  if (!masterId.value) {

    message.warning('请先保存或选择母版')

    return

  }

  if (!selectedPlatforms.value.length) {

    message.warning('请至少选择一个平台')

    return

  }

  publishing.value = true

  try {

    const res = await apiPost<{ count?: number }>(`/content-masters/${masterId.value}/publish`, {

      platform_ids: selectedPlatforms.value,

      primary_url: form.value.tenant_canonical_url,

      preflight_checklist: preflightPayload(),

    })

    lastResult.value = `已创建 ${res.count ?? 0} 条发布任务（同一母版）`

    message.success(lastResult.value)

  } catch (e: unknown) {

    const err = e as { message?: string }

    message.error(err?.message || '发布失败')

  } finally {

    publishing.value = false

  }

}



async function submitAutoVariants() {

  if (!selectedPlatforms.value.length) {

    message.warning('请至少选择一个平台')

    return

  }

  publishingVariants.value = true

  try {

    const res = await apiPost<{ count?: number; matches?: unknown[] }>('/content-masters/publish-auto-variants', {

      platform_ids: selectedPlatforms.value,

      draft_ids: geoDraftIds.value.length ? geoDraftIds.value : undefined,

      fallback_master_id: masterId.value || undefined,

      primary_url: form.value.tenant_canonical_url || undefined,

      preflight_checklist: preflightPayload(),

    })

    lastResult.value = `按变体匹配：已创建 ${res.count ?? 0} 条发布任务`
    const warn = (res.matches as { bind_warning?: string; platform_name?: string }[] | undefined)
      ?.filter((m) => m.bind_warning)
      .map((m) => m.platform_name)
      .filter(Boolean)
    if (warn?.length) {
      lastResult.value += `（${warn.join('、')} 账号未绑定，真发前请完成授权）`
    }
    message.success(lastResult.value)

  } catch (e: unknown) {

    const err = e as { message?: string }

    message.error(err?.message || '变体发布失败')

  } finally {

    publishingVariants.value = false

  }

}



onMounted(async () => {

  await resolveTenant()

  await loadPlatforms()

  await loadDrafts()

  await loadPlatformBindStatus()

  const qJob = route.query.job_id

  if (typeof qJob === 'string' && qJob) {

    geoJobId.value = qJob

    await pollGeoJob()

  }

})

</script>



<style scoped>

.mb-4 { margin-bottom: 16px; }

.mt-3 { margin-top: 12px; }

.mt-4 { margin-top: 16px; }

.hint { font-size: 13px; color: #64748b; margin-bottom: 12px; }

.draft-list { list-style: none; padding: 0; margin: 0; }

.draft-list li { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f1f5f9; }

.draft-link { background: none; border: none; color: #4f46e5; cursor: pointer; text-align: left; padding: 0; }

.draft-meta { font-size: 12px; color: #94a3b8; }

.preflight-checks { display: flex; flex-direction: column; gap: 8px; }

.risk-list { font-size: 12px; color: #b45309; padding-left: 18px; margin: 0; }

</style>

