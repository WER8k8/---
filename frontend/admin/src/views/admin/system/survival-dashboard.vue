/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="Survival 真钱台账" subtitle="财迷疯生存基金 · WorldFirst · 与租户账单隔离" surface="elevated">
    <template #actions>
      <a-space>
        <router-link to="/admin/system/greedy-cumulative">
          <a-button>摸金累计</a-button>
        </router-link>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <template v-if="snap">
      <div class="stat-row">
        <a-statistic title="今日实收" :value="todayCny" prefix="¥" :precision="2" />
        <a-statistic title="目标进度" :value="progressPct" suffix="%" />
        <a-statistic title="终身余额" :value="balanceCny" prefix="¥" :precision="2" />
        <a-statistic title="runway" :value="runwayDays" suffix="天" />
      </div>

      <a-alert
        :type="threatType"
        show-icon
        :message="pulse.headline || '生存脉搏'"
        :description="`mood: ${pulse.mood || '—'} · threat: ${pulse.threat_level || '—'}`"
        class="mb-3"
      />

      <a-tabs v-model:activeKey="recordTab" class="mb-3">
        <a-tab-pane key="worldfirst" tab="WorldFirst">
          <a-row :gutter="12">
            <a-col :xs="24" :lg="12">
              <a-card size="small" title="WorldFirst 手工入账">
                <a-form layout="vertical" @finish="submitWf">
                  <a-form-item label="金额" required>
                    <a-input-number v-model:value="wfForm.amount" :min="0.01" :precision="2" style="width: 100%" />
                  </a-form-item>
                  <a-form-item label="币种">
                    <a-select v-model:value="wfForm.currency">
                      <a-select-option value="USD">USD</a-select-option>
                      <a-select-option value="EUR">EUR</a-select-option>
                      <a-select-option value="CNY">CNY</a-select-option>
                      <a-select-option value="JPY">JPY</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="万里汇流水号" required>
                    <a-input v-model:value="wfForm.transaction_id" />
                  </a-form-item>
                  <a-form-item label="入账类型">
                    <a-select v-model:value="wfForm.inbound_type">
                      <a-select-option value="b2b_tt">b2b_tt</a-select-option>
                      <a-select-option value="marketplace">marketplace</a-select-option>
                      <a-select-option value="service_fee">service_fee</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="备注"><a-input v-model:value="wfForm.note" /></a-form-item>
                  <a-button type="primary" html-type="submit" :loading="wfSubmitting" block>确认入账</a-button>
                </a-form>
              </a-card>
            </a-col>
            <a-col :xs="24" :lg="12">
              <a-card size="small" title="WorldFirst 接入提示">
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item v-for="(v, k) in wfRows" :key="k" :label="k">{{ v }}</a-descriptions-item>
                </a-descriptions>
              </a-card>
            </a-col>
          </a-row>
        </a-tab-pane>
        <a-tab-pane key="generic" tab="通用真钱入账">
          <a-card size="small" title="其他通道（PayPal/电汇/线下等）">
            <a-form layout="vertical" @finish="submitGeneric">
              <a-row :gutter="12">
                <a-col :span="12">
                  <a-form-item label="金额" required>
                    <a-input-number v-model:value="genForm.amount" :min="0.01" :precision="2" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="币种">
                    <a-select v-model:value="genForm.currency">
                      <a-select-option value="CNY">CNY</a-select-option>
                      <a-select-option value="USD">USD</a-select-option>
                      <a-select-option value="EUR">EUR</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="渠道" required>
                    <a-input v-model:value="genForm.channel" placeholder="如 paypal_tt / wire" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="支付方" required>
                    <a-input v-model:value="genForm.payment_provider" placeholder="如 paypal / bank" />
                  </a-form-item>
                </a-col>
                <a-col :span="24">
                  <a-form-item label="流水号（幂等）" required>
                    <a-input v-model:value="genForm.provider_payment_id" />
                  </a-form-item>
                </a-col>
                <a-col :span="24">
                  <a-form-item label="备注"><a-input v-model:value="genForm.note" /></a-form-item>
                </a-col>
              </a-row>
              <a-button type="primary" html-type="submit" :loading="genSubmitting" block>通用入账</a-button>
            </a-form>
          </a-card>
        </a-tab-pane>
      </a-tabs>

      <a-card size="small" title="收款通道" class="mb-3">
        <div class="meta">主通道：{{ snap.primary_rail || 'worldfirst' }}</div>
        <div class="meta">charter：{{ snap.charter_version || '—' }}</div>
        <div class="meta">Webhook：POST /api/v1/hermes/ops/survival/worldfirst/webhook</div>
      </a-card>

      <a-table
        :loading="loading"
        :data-source="entries"
        :columns="entryCols"
        row-key="id"
        size="small"
        :pagination="{ pageSize: 15 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount'">
            ¥{{ ((record.amount_base_minor || record.amount_minor || 0) / 100).toFixed(2) }}
            <span class="sub">{{ record.currency }}</span>
          </template>
        </template>
      </a-table>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { fetchSurvivalStatus, recordSurvivalSettlement, recordWorldfirstInbound } from '@/api/hermesGreedy'

type LedgerRow = {
  id: string
  entry_type?: string
  channel?: string
  amount_minor?: number
  amount_base_minor?: number
  currency?: string
  payment_provider?: string
  provider_payment_id?: string
  recorded_at?: string
}

const loading = ref(false)
const wfSubmitting = ref(false)
const genSubmitting = ref(false)
const recordTab = ref('worldfirst')
const snap = ref<Record<string, unknown> | null>(null)
const wfForm = ref({
  amount: undefined as number | undefined,
  currency: 'USD',
  transaction_id: '',
  inbound_type: 'b2b_tt',
  note: '',
})
const genForm = ref({
  amount: undefined as number | undefined,
  currency: 'CNY',
  channel: '',
  payment_provider: '',
  provider_payment_id: '',
  note: '',
})

const pulse = computed(() => (snap.value?.pulse as Record<string, unknown>) || {})
const todayCny = computed(() => Number(pulse.value.settled_today_display_cny ?? 0))
const progressPct = computed(() => Number(pulse.value.progress_pct ?? 0))
const balanceCny = computed(() => Number(pulse.value.lifetime_balance_display_cny ?? 0))
const runwayDays = computed(() => Number(pulse.value.runway_days ?? 0))
const entries = computed(() => (snap.value?.recent_entries as LedgerRow[]) || [])

const threatType = computed(() => {
  const t = pulse.value.threat_level
  if (t === 'critical') return 'error'
  if (t === 'warning') return 'warning'
  return 'success'
})

const wfRows = computed(() => {
  const wf = (snap.value?.worldfirst as Record<string, unknown>) || {}
  const rows: Record<string, string> = {}
  for (const [k, v] of Object.entries(wf)) {
    if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
      rows[k] = String(v)
    }
  }
  return rows
})

const entryCols = [
  { title: '类型', dataIndex: 'entry_type', key: 'entry_type', width: 80 },
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 100 },
  { title: '金额', key: 'amount', width: 120 },
  { title: 'provider', dataIndex: 'payment_provider', key: 'payment_provider', width: 100 },
  { title: '流水', dataIndex: 'provider_payment_id', key: 'provider_payment_id', ellipsis: true },
  { title: '入账时间', dataIndex: 'recorded_at', key: 'recorded_at', width: 180 },
]

async function load() {
  loading.value = true
  try {
    snap.value = await fetchSurvivalStatus()
  } catch (e: unknown) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function submitWf() {
  const amt = wfForm.value.amount
  const tx = wfForm.value.transaction_id.trim()
  if (!amt || amt <= 0 || !tx) {
    message.warning('请填写金额与流水号')
    return
  }
  wfSubmitting.value = true
  try {
    const result = await recordWorldfirstInbound({
      amount_minor: Math.round(amt * 100),
      currency: wfForm.value.currency,
      transaction_id: tx,
      inbound_type: wfForm.value.inbound_type,
      note: wfForm.value.note || undefined,
    })
    if (result.ok === false) {
      message.warning(String(result.error || '入账未成功'))
    } else {
      message.success(result.duplicate ? '流水号已存在（幂等）' : '万里汇已入账')
      wfForm.value.transaction_id = ''
      await load()
    }
  } catch (e: unknown) {
    message.error((e as Error).message || '入账失败')
  } finally {
    wfSubmitting.value = false
  }
}

async function submitGeneric() {
  const amt = genForm.value.amount
  const pid = genForm.value.provider_payment_id.trim()
  if (!amt || amt <= 0 || !pid || !genForm.value.channel.trim() || !genForm.value.payment_provider.trim()) {
    message.warning('请填写完整入账信息')
    return
  }
  genSubmitting.value = true
  try {
    const result = await recordSurvivalSettlement({
      amount_minor: Math.round(amt * 100),
      currency: genForm.value.currency,
      channel: genForm.value.channel.trim(),
      payment_provider: genForm.value.payment_provider.trim(),
      provider_payment_id: pid,
      note: genForm.value.note || undefined,
    })
    if (result.ok === false) {
      message.warning(String(result.error || '入账未成功'))
    } else {
      message.success(result.duplicate ? '流水号已存在' : '已入账')
      genForm.value.provider_payment_id = ''
      await load()
    }
  } catch (e: unknown) {
    message.error((e as Error).message || '入账失败')
  } finally {
    genSubmitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.mb-3 {
  margin-bottom: 12px;
}
.meta {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 6px;
  font-size: 13px;
}
.sub {
  color: rgba(0, 0, 0, 0.45);
  margin-left: 4px;
  font-size: 12px;
}
.mt-2 {
  margin-top: 8px;
}
</style>
