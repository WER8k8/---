<template>
  <YdPage title="获客作战台" subtitle="谁在跟 · 货 · 物流 · 联系 · 交代 · 付款" surface="elevated">
    <template #actions>
      <a-space>
        <a-button type="primary" @click="showPreview = true">智能拆解预览</a-button>
        <a-button @click="reloadTips">刷新提醒</a-button>
      </a-space>
    </template>

    <div class="acq-ops space-y-4">
      <!-- 进线 / 选客户 -->
      <a-card size="small" title="1. 找到客户 / 进线">
        <div class="grid gap-3 md:grid-cols-4">
          <a-input v-model:value="form.inquiry_id" placeholder="询盘编号（如 INQ-001）" allow-clear />
          <a-input v-model:value="form.country" placeholder="国家二字码（如 SA / IN）" allow-clear />
          <a-select v-model:value="form.grade" placeholder="客户好坏（可选）" allow-clear style="width: 100%">
            <a-select-option :value="90">A · 深跟</a-select-option>
            <a-select-option :value="70">B · 标准跟</a-select-option>
            <a-select-option :value="50">C · 低成本</a-select-option>
            <a-select-option :value="20">D · 谨慎</a-select-option>
          </a-select>
          <a-input v-model:value="form.owner_user_id" placeholder="谁来跟（业务员）" allow-clear />
        </div>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <a-textarea
            v-model:value="form.message"
            :rows="2"
            placeholder="客户说了什么？（原样贴进来即可）"
          />
          <div class="flex flex-col gap-2">
            <a-button type="primary" :loading="loading" @click="onIngestReply">
              客户回复 → 建卡并记跟进
            </a-button>
            <a-button :loading="loading" @click="onLoadCard">打开跟单卡</a-button>
            <a-button :loading="translateLoading" @click="onTranslate">翻译成中文</a-button>
          </div>
        </div>
        <a-alert v-if="wallet" class="mt-3" :type="wallet.hard_block_enabled ? 'error' : 'info'" show-icon
          :message="wallet.message || '计费状态'" />
        <a-alert
          v-if="translateResult"
          class="mt-3"
          :type="translateResult.degraded ? 'warning' : 'success'"
          show-icon
          :message="`译文（${translateResult.provider}${translateResult.degraded ? ' · 降级' : ''}）`"
          :description="translateResult.translated"
        />
        <a-alert
          v-if="intentAnalysis"
          class="mt-3"
          :type="intentAnalysis.intent === 'reject_competitor' ? 'error' : 'info'"
          show-icon
          :message="`意图判断：${INTENT_LABELS[intentAnalysis.intent] || intentAnalysis.intent}（${intentAnalysis.confidence}）`"
          :description="`${intentAnalysis.reason} ｜ 建议阶段：${intentAnalysis.stage_suggestion} ｜ 下一步：${intentAnalysis.next_action}${intentAnalysis.talk_track ? ' ｜ 话术：' + intentAnalysis.talk_track : ''}`"
        />
        <a-alert v-if="alert" class="mt-3" :type="alertType" show-icon :message="alert" />
      </a-card>

      <a-card v-if="channels && channels.channels.length" size="small" title="获客渠道（红标=演示/未开通）">
        <div class="flex flex-wrap gap-2">
          <a-tag v-for="ch in channels.channels" :key="ch.id" :color="ch.is_mock ? 'error' : 'success'">
            {{ ch.name }}{{ ch.is_mock ? ' · 演示' : ' · 可用' }}
          </a-tag>
        </div>
        <div class="text-xs text-gray-500 mt-1">{{ channels.hint }}</div>
      </a-card>

      <!-- 今日待办 SLA -->
      <a-card size="small" title="今日待办（先逾期，后将到期）">
        <div class="flex items-center gap-2 mb-2">
          <a-tag v-if="followups" color="processing">共 {{ followups.total }}</a-tag>
          <a-tag v-if="followups && followups.overdue_count" color="error">逾期 {{ followups.overdue_count }}</a-tag>
          <a-button size="small" :loading="followupLoading" @click="loadFollowups">刷新待办</a-button>
        </div>
        <div v-if="!followups || !followups.items.length" class="text-gray-400 text-sm py-2">
          暂无待办。有客户回复或记录跟进后会出现在这里。
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="item in followups.items.slice(0, 8)"
            :key="item.inquiry_id"
            class="acq-follow"
            @click="openInquiry(item.inquiry_id)"
          >
            <div class="acq-follow-top">
              <b>{{ item.buyer_display || item.inquiry_id }}</b>
              <a-tag :color="item.sla.overdue ? 'error' : item.sla.sla === 'due' ? 'warning' : 'default'">
                {{ item.sla.overdue ? '逾期' : item.sla.sla === 'due' ? '将到期' : '待安排' }}
              </a-tag>
              <a-tag v-if="item.buyer_grade">{{ item.buyer_grade }}级</a-tag>
            </div>
            <div class="text-sm text-gray-600">{{ item.next_action || item.last_summary || '—' }}</div>
            <div class="text-xs text-gray-400">{{ item.sla.display }}</div>
          </div>
        </div>
      </a-card>

      <!-- Playbook 提醒 -->
      <a-card v-if="tips.length" size="small" title="2. 系统提醒（怎么聊）">
        <a-alert type="info" show-icon message="进线作战提示">
          <template #description>
            <ul class="acq-tips">
              <li v-for="(t, i) in tips" :key="i">{{ t }}</li>
            </ul>
          </template>
        </a-alert>
      </a-card>

      <!-- 跟单卡六组 -->
      <a-card size="small" title="3. 跟单作战卡（一眼看懂）">
        <div v-if="!card" class="text-center text-gray-400 py-8">
          还没有卡片。请在上方填询盘编号，点「客户回复 → 建卡」或「打开跟单卡」。
        </div>
        <template v-else>
          <div class="mb-3 flex flex-wrap items-center gap-2">
            <a-tag color="processing">{{ card.stage || '-' }}</a-tag>
            <a-tag v-if="card.buyer_grade" :color="gradeColor">{{ card.buyer_grade }}级</a-tag>
            <span v-if="card.buyer_display" class="text-gray-700 font-medium">{{ card.buyer_display }}</span>
            <span v-if="card.buyer_grade_reason" class="text-gray-500 text-sm">{{ card.buyer_grade_reason }}</span>
          </div>

          <div class="acq-grid">
            <div v-for="(val, key) in summary" :key="key" class="acq-cell">
              <div class="acq-label">{{ key }}</div>
              <div class="acq-value">{{ val || '—' }}</div>
            </div>
          </div>

          <a-alert
            v-if="card.playbook_tips && card.playbook_tips.length"
            class="mt-3"
            type="warning"
            show-icon
            message="注意"
          >
            <template #description>
              <ul class="acq-tips">
                <li v-for="(t, i) in card.playbook_tips" :key="i">{{ t }}</li>
              </ul>
            </template>
          </a-alert>

          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <div class="font-semibold mb-1">记一笔跟进</div>
              <a-textarea v-model:value="touch.summary" :rows="2" placeholder="例如：已读未回 / 已发报价 / 要求 CIF 吉达" />
              <a-input v-model:value="touch.next_action" class="mt-2" placeholder="下一步做什么" />
              <a-button class="mt-2" type="primary" :loading="loading" @click="onTouch">保存跟进</a-button>
            </div>
            <div>
              <div class="font-semibold mb-1">交代 / 备注</div>
              <a-textarea v-model:value="note.body" :rows="2" placeholder="客户要求、承诺事项…" />
              <a-button class="mt-2" :loading="loading" @click="onNote">添加备注</a-button>
              <div class="mt-3 font-semibold mb-1">流失原因（聊跑了）</div>
              <a-select
                v-model:value="loss.reasons"
                mode="multiple"
                placeholder="可多选"
                style="width: 100%"
                :options="lossOptions"
              />
              <a-input v-model:value="loss.note" class="mt-2" placeholder="补充说明（可空）" />
              <a-button class="mt-2" danger :loading="loading" @click="onLoss">登记流失</a-button>
            </div>
          </div>

          <div v-if="card.notes && card.notes.length" class="mt-4">
            <div class="font-semibold mb-1">交代记录</div>
            <div v-for="(n, i) in card.notes" :key="i" class="acq-note">
              <b>{{ n.author }}</b> · {{ n.at }}：{{ n.body }}
            </div>
          </div>
        </template>
      </a-card>
    </div>

    <!-- 智能拆解预览 -->
    <a-modal v-model:open="showPreview" title="智能调度预览（先看懂再干活）" width="720px" :footer="null">
      <div class="space-y-3">
        <a-alert type="info" show-icon message="输入想干什么，系统会拆成步骤。外发动作需人工确认，不会偷偷发。" />
        <a-select v-model:value="preview.intent" style="width: 100%">
          <a-select-option value="find_leads">找客户 + 写开发信</a-select-option>
          <a-select-option value="fulfillment">履约：询盘→PI→物流</a-select-option>
          <a-select-option value="whatsapp">社媒 / WhatsApp 拓客</a-select-option>
          <a-select-option value="generate_site">建站 + 内容分发</a-select-option>
          <a-select-option value="deep_research">市场调研</a-select-option>
        </a-select>
        <a-input v-model:value="preview.keyword" placeholder="关键词（如 rockwool / 石膏板）" />
        <a-input v-model:value="preview.country" placeholder="国家（如 SA / IN）" />
        <a-button type="primary" :loading="loading" block @click="onPreview">拆解给我看</a-button>
        <a-button
          v-if="previewResult"
          type="primary"
          :loading="dispatchLoading"
          danger
          block
          @click="onDispatch"
        >
          确认派发（写入任务图并调度）
        </a-button>
        <a-alert v-if="dispatchResult" class="mt-2" :type="dispatchResult.dispatched ? 'success' : 'info'" show-icon
          :message="dispatchResult.dispatched ? '已派发' : '已拆解（未派发）'"
          :description="`${dispatchResult.persistence_note || ''} plan=${dispatchResult.plan_id} source=${dispatchResult.graph_source}`" />
        <div v-if="previewResult">
          <div class="mb-2 text-sm text-gray-600">
            来源：{{ previewResult.source }} ｜ 策略：{{ previewResult.strategy }}
          </div>
          <a-table
            :data-source="previewResult.nodes"
            :columns="nodeCols"
            row-key="id"
            size="small"
            :pagination="false"
          />
          <a-alert
            v-if="previewResult.approval_required?.length"
            class="mt-2"
            type="warning"
            show-icon
            :message="`需要人工确认：${previewResult.approval_required.join('、')}`"
          />
        </div>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
/**
 * 获客作战台 —— 唯一目标：智能获客，傻子都行。
 * 硬锁：仅挂在 /client/* 租户壳；不新建登录页；主色走全局令牌。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import YdPage from '@/components/youding/YdPage.vue'
import {
  addOpsCardNote,
  dispatchAcquisition,
  getOpsCard,
  getWalletStatus,
  ingestReply,
  listPlaybooks,
  listAcquisitionChannels,
  listFollowups,
  materializeOpsCard,
  previewIntent,
  recordOpsCardLoss,
  touchOpsCard,
  translateAcquisition,
  type IntentPreviewResponse,
  type OpsCardPayload,
  type OpsCardResponse,
  type OpsCardSummary,
} from '@/api/acquisition'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const alert = ref('')
const alertType = ref<'success' | 'error' | 'info' | 'warning'>('info')
const card = ref<OpsCardPayload | null>(null)
const summary = ref<Partial<OpsCardSummary>>({})
const tips = ref<string[]>([])
const tenantId = ref('demo')

/** 回复意图展示标签（与 backend intent_classifier 枚举对齐） */
const INTENT_LABELS: Record<string, string> = {
  price_haggling: '压价议价',
  request_quote: '索取报价',
  request_sample: '索要样品',
  payment_discuss: '付款谈判',
  cert_insist: '认证要求',
  quantity_port: '数量/港口',
  reject_competitor: '已选同行/流失风险',
  generic_interest: '泛意向',
  unknown: '未识别',
}
const intentAnalysis = ref<{
  intent: string
  stage_suggestion: string
  confidence: number
  reason: string
  next_action: string
  talk_track: string
} | null>(null)

const followupLoading = ref(false)
const channels = ref<Awaited<ReturnType<typeof listAcquisitionChannels>> | null>(null)

async function loadChannels() {
  try { channels.value = await listAcquisitionChannels() } catch { channels.value = null }
}
const followups = ref<Awaited<ReturnType<typeof listFollowups>> | null>(null)

async function loadFollowups() {
  followupLoading.value = true
  try {
    const tenant = await resolveTenantId()
    followups.value = await listFollowups(tenant)
  } catch {
    followups.value = null
  } finally {
    followupLoading.value = false
  }
}

function openInquiry(id: string) {
  form.inquiry_id = id
  void onLoadCard()
}

async function resolveTenantId(): Promise<string> {
  if (tenantId.value && tenantId.value !== 'demo') return tenantId.value
  try {
    const dash = await apiGet<{ tenant_id?: string; tenant?: { id?: string } }>('/client/dashboard')
    const tid = dash?.tenant_id || dash?.tenant?.id
    if (tid) {
      tenantId.value = String(tid)
      return tenantId.value
    }
  } catch {
    /* 后端未起时保留 demo，演示仍可用；生产登录后应能取到真租户 */
  }
  return tenantId.value || 'demo'
}

const form = reactive({
  inquiry_id: '',
  country: '',
  grade: undefined as number | undefined,
  owner_user_id: '',
  message: '',
})

const touch = reactive({ summary: '', next_action: '' })
const note = reactive({ body: '' })
const loss = reactive({ reasons: [] as string[], note: '' })
const lossOptions = [
  { label: '价格高', value: '价格高' },
  { label: '认证不够', value: '认证不够' },
  { label: '交期不合适', value: '交期不合适' },
  { label: '付款方式冲突', value: '付款方式冲突' },
  { label: '已选同行', value: '已选同行' },
  { label: '无回复/原因未知', value: '无回复' },
  { label: 'MOQ/规格不合', value: 'MOQ不合' },
  { label: '其他', value: '其他' },
]

const showPreview = ref(false)
const preview = reactive({ intent: 'find_leads', keyword: '', country: '' })
const previewResult = ref<IntentPreviewResponse | null>(null)
const dispatchLoading = ref(false)
const dispatchResult = ref<{
  plan_id: string
  graph_source: string
  node_count: number
  dispatched: boolean
  persistence_note: string
  dispatch_error: string
  card?: OpsCardPayload | null
} | null>(null)
const nodeCols = [
  { title: '步骤', dataIndex: 'id', width: 60 },
  { title: '谁来做', dataIndex: 'executor', width: 120 },
  { title: '做什么', dataIndex: 'capability' },
  {
    title: '人工确认',
    dataIndex: 'approval_required',
    width: 90,
  },
]

const gradeColor = computed(() => {
  const g = card.value?.buyer_grade
  if (g === 'A') return 'success'
  if (g === 'B') return 'processing'
  if (g === 'C') return 'warning'
  if (g === 'D') return 'error'
  return 'default'
})

function applyCard(resp: OpsCardResponse | null) {
  if (!resp) return
  card.value = resp.card || null
  summary.value = resp.summary || {}
}

function setAlert(text: string, type: typeof alertType.value = 'info') {
  alert.value = text
  alertType.value = type
}

async function reloadTips() {
  if (!form.country) {
    tips.value = []
    return
  }
  try {
    const r = await listPlaybooks(form.country, 'new')
    const all: string[] = []
    for (const p of r.playbooks || []) {
      all.push(...(p.tips || []), ...(p.warnings || []))
    }
    tips.value = Array.from(new Set(all)).slice(0, 8)
  } catch {
    tips.value = []
  }
}

async function onIngestReply() {
  if (!form.inquiry_id) {
    message.warning('请先填写询盘编号')
    return
  }
  loading.value = true
  try {
    const tenant = await resolveTenantId()
    const resp = await ingestReply({
      tenant_id: tenant,
      inquiry_id: form.inquiry_id,
      channel: 'inbound',
      message: form.message || '（无正文）',
      country: form.country,
      grade: form.grade,
      owner_user_id: form.owner_user_id,
    })
    applyCard(resp)
    intentAnalysis.value = resp.intent_analysis || null
    if (resp.playbook_tips && resp.playbook_tips.length) {
      tips.value = resp.playbook_tips.slice(0, 8)
    } else {
      await reloadTips()
    }
    if (resp.alerts && resp.alerts.length) {
      setAlert(resp.alerts.join('；'), 'warning')
    } else if (resp.intent_analysis) {
      const lab = INTENT_LABELS[resp.intent_analysis.intent] || resp.intent_analysis.intent
      setAlert(
        `已建卡。意图：${lab}。下一步：${resp.intent_analysis.next_action}`,
        resp.intent_analysis.intent === 'reject_competitor' ? 'warning' : 'success',
      )
    } else {
      setAlert('已建卡并记录跟进。请看下方六格信息。', 'success')
    }
    void loadFollowups()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    setAlert(`保存失败：${msg}。请确认后端已启动，或稍后重试。`, 'error')
  } finally {
    loading.value = false
  }
}

async function onLoadCard() {
  if (!form.inquiry_id) {
    message.warning('请先填写询盘编号')
    return
  }
  loading.value = true
  try {
    const resp = await getOpsCard(form.inquiry_id)
    applyCard(resp)
    setAlert('已打开跟单卡。', 'success')
  } catch {
    // 没有卡则尝试生成
    try {
      const resp = await materializeOpsCard({
        tenant_id: await resolveTenantId(),
        inquiry_id: form.inquiry_id,
        owner_user_id: form.owner_user_id,
        grade: form.grade || 0,
      })
      applyCard(resp)
      setAlert('该询盘尚无卡片，已为你新建一张。', 'info')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setAlert(`打不开：${msg}`, 'error')
    }
  } finally {
    loading.value = false
  }
}

async function onTouch() {
  if (!form.inquiry_id || !touch.summary) {
    message.warning('请填写跟进内容')
    return
  }
  loading.value = true
  try {
    const resp = await touchOpsCard(form.inquiry_id, {
      channel: 'manual',
      summary: touch.summary,
      next_action: touch.next_action,
    })
    applyCard(resp)
    touch.summary = ''
    setAlert('跟进已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onNote() {
  if (!form.inquiry_id || !note.body) {
    message.warning('请填写备注')
    return
  }
  loading.value = true
  try {
    const resp = await addOpsCardNote(form.inquiry_id, { author: '我', body: note.body })
    applyCard(resp)
    note.body = ''
    setAlert('备注已添加。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onLoss() {
  if (!form.inquiry_id || !loss.reasons.length) {
    message.warning('请选择流失原因')
    return
  }
  loading.value = true
  try {
    const resp = await recordOpsCardLoss(form.inquiry_id, { reasons: loss.reasons, note: loss.note })
    applyCard(resp)
    setAlert('流失已登记，系统会记下来供以后改玩法。', 'warning')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onPreview() {
  loading.value = true
  try {
    previewResult.value = await previewIntent({
      intent: preview.intent,
      tenant_id: await resolveTenantId(),
      payload: {
        keyword: preview.keyword,
        country: preview.country,
        message: preview.keyword,
        product_name: preview.keyword,
        topic: preview.keyword,
      },
    })
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '拆解失败')
    previewResult.value = null
  } finally {
    loading.value = false
  }
}

async function onDispatch() {
  dispatchLoading.value = true
  try {
    const tenant = await resolveTenantId()
    dispatchResult.value = await dispatchAcquisition({
      intent: preview.intent,
      tenant_id: tenant,
      payload: {
        keyword: preview.keyword,
        country: preview.country,
        message: preview.keyword,
        product_name: preview.keyword,
        topic: preview.keyword,
      },
      inquiry_id: form.inquiry_id || '',
      auto_dispatch: true,
    })
    if (form.inquiry_id) {
      try {
        const fresh = await getOpsCard(form.inquiry_id)
        applyCard(fresh)
      } catch {
        /* ignore */
      }
    }
    setAlert(
      dispatchResult.value.dispatched
        ? `已派发：${dispatchResult.value.node_count} 个步骤`
        : `已拆解未派发：${dispatchResult.value.persistence_note || dispatchResult.value.dispatch_error}`,
      dispatchResult.value.dispatched ? 'success' : 'info',
    )
  } catch (e: unknown) {
    dispatchResult.value = null
    message.error(e instanceof Error ? e.message : '派发失败')
  } finally {
    dispatchLoading.value = false
  }
}

onMounted(async () => {
  // 预置演示数据，降低空态焦虑（傻子都行）
  if (!form.inquiry_id) form.inquiry_id = 'INQ-DEMO-001'
  if (!form.country) form.country = 'SA'
  try {
    const tid = await resolveTenantId()
    wallet.value = await getWalletStatus(tid)
  } catch {
    wallet.value = {
      tenant_id: 'demo',
      token_balance: null,
      plan: null,
      hard_block_enabled: false,
      status: 'unknown',
      message: '后端未启动或计费未接入',
    }
  }
  await loadFollowups()
  void loadChannels()
})

const wallet = ref<{
  token_balance: number | null
  plan: string | null
  hard_block_enabled: boolean
  status: string
  message: string
} | null>(null)

async function onTranslate() {
  if (!form.message) {
    message.warning('请先粘贴客户原文')
    return
  }
  translateLoading.value = true
  try {
    translateResult.value = await translateAcquisition(form.message, 'auto', 'zh')
  } catch (e: unknown) {
    translateResult.value = null
    message.error(e instanceof Error ? e.message : '翻译失败')
  } finally {
    translateLoading.value = false
  }
}

const translateLoading = ref(false)
const translateResult = ref<{
  original: string
  translated: string
  provider: string
  degraded: boolean
  message: string
} | null>(null)
</script>

<style scoped>
.acq-ops {
  max-width: 1100px;
  margin: 0 auto;
}
.acq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.acq-cell {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px 14px;
  background: #fafafa;
  min-height: 84px;
}
.acq-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.acq-value {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  word-break: break-all;
  line-height: 1.4;
}
.acq-tips {
  margin: 0;
  padding-left: 1.1em;
  font-size: 13px;
  line-height: 1.6;
}
.acq-note {
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px dashed #e5e7eb;
}
.acq-follow {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  background: #fff;
}
.acq-follow:hover {
  border-color: #4a9b8c;
}
.acq-follow-top {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 4px;
}
</style>
