/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>

  <YdPage

    title="询盘与 IM 渠道"

    subtitle="海外访客怎么联系您：按国家配置 WhatsApp、Telegram、LINE 或表单"

    surface="elevated"

  >

    <template #actions>

      <a-button type="primary" @click="openCreate">新增国家渠道</a-button>

    </template>



    <a-alert type="success" show-icon class="mb-3" style="margin-bottom: 12px">
      <template #message>开户第 5 步 · 销售怎么收消息</template>
      <template #description>
        <span>① 客户留言进系统（5a）— 下面「国内留言入站」复制链接给技术同事</span>
        <br />
        <span>② 销售手机收到通知（5b，</span>
        <a href="#wecom-push">点这里配置</a>
        <span>）</span>
        <br />
        <a-button type="link" size="small" class="px-0" @click="router.push('/sales/auto-negotiator')">
          ③ 抖音评论自动谈单（5c）→
        </a-button>
        <a-button type="link" size="small" class="px-0" @click="router.push('/client/onboarding')">
          看完整开户路线 →
        </a-button>
      </template>
    </a-alert>

    <a-card title="国内留言入站（企微 / 抖音）" class="webhook-card" style="margin-bottom: 12px">
      <a-alert
        type="info"
        show-icon
        message="客户留言进系统 ≠ 销售手机自动收到；5b 企微推送需单独配置。"
        style="margin-bottom: 12px"
      />
      <a-alert
        v-if="webhookConfig"
        :type="webhookConfig.secret_configured ? 'success' : 'warning'"
        show-icon
        :message="webhookConfig.secret_configured ? '入站验签密钥已配置' : '生产环境建议配置验签密钥（开发可跳过）'"
        style="margin-bottom: 12px"
      />
      <div v-if="webhookConfig?.channels?.length" class="webhook-channels">
        <div v-for="ch in webhookConfig.channels" :key="ch.id" class="webhook-row">
          <div>
            <strong>{{ ch.label }}</strong>
            <p class="webhook-url">{{ ch.url }}</p>
          </div>
          <a-button size="small" @click="copyText(ch.url)">复制 URL</a-button>
        </div>
      </div>
      <a-collapse v-if="webhookConfig?.channels?.length" ghost>
        <a-collapse-panel v-for="ch in webhookConfig.channels" :key="ch.id + '-curl'" :header="`${ch.label} · cURL 示例`">
          <pre class="curl-block">{{ ch.curl_example }}</pre>
          <a-button size="small" type="link" @click="copyText(ch.curl_example)">复制 cURL</a-button>
        </a-collapse-panel>
      </a-collapse>
      <a-button size="small" class="mt-2" :loading="rehearsal5aLoading" @click="runRehearsal5a">
        一键测试入站（5a）
      </a-button>
    </a-card>

    <a-card id="wecom-push" title="企微销售推送（本企业配置）" class="webhook-card" style="margin-bottom: 12px">
      <a-alert
        type="info"
        show-icon
        message="推送接收人是您公司企微里的销售 UserID，由您自行填写；平台不会代填客户人员。"
        style="margin-bottom: 12px"
      />
      <a-form layout="vertical">
        <a-form-item label="启用企微推送">
          <a-switch v-model:checked="wecomForm.enabled" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="CorpID">
              <a-input v-model:value="wecomForm.corp_id" placeholder="企业微信 CorpID" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="AgentId">
              <a-input v-model:value="wecomForm.agent_id" placeholder="应用 AgentId" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="AgentSecret">
          <a-input-password
            v-model:value="wecomForm.agent_secret"
            :placeholder="wecomForm.agent_secret_set ? '已配置，留空则不修改' : '应用 Secret'"
          />
        </a-form-item>
        <a-form-item label="销售 UserID（多个用 | 分隔）">
          <a-input v-model:value="wecomForm.push_userids_text" placeholder="ZhangSan|LiSi" />
        </a-form-item>
        <a-form-item label="销售群机器人 Webhook（可选）">
          <a-input v-model:value="wecomForm.webhook_url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
        </a-form-item>
        <a-space wrap>
          <a-button type="primary" :loading="wecomSaving" @click="saveWecomPush">保存企微推送配置</a-button>
          <a-button :loading="rehearsal5bLoading" @click="runRehearsal5b">发送测试通知（5b）</a-button>
        </a-space>
      </a-form>
    </a-card>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">

      <div class="panel-head mb-3">

        <YdTableToolbar

          :loading="loading"

          :target-ref="tablePanelRef"

          :show-export="false"

          @refresh="load"

        />

      </div>

      <YdDataTable

        :columns="cols"

        :data-source="rows"

        :loading="loading"

        :pagination="false"

        :table-props="{ size: tableSize, rowKey: 'id' }"

      >

        <template #bodyCell="{ column, record }">

          <template v-if="column.key === 'active'">

            <a-tag :color="record.is_active ? 'green' : 'default'">

              {{ record.is_active ? '启用' : '停用' }}

            </a-tag>

          </template>

          <template v-else-if="column.key === 'actions'">

            <a-space>

              <a-button size="small" @click="editRow(record)">编辑</a-button>

              <a-popconfirm title="确认删除？" @confirm="removeRow(record.id)">

                <a-button size="small" danger>删除</a-button>

              </a-popconfirm>

            </a-space>

          </template>

        </template>

      </YdDataTable>

    </div>



    <a-modal v-model:open="modalOpen" :title="editId ? '编辑路由' : '新增路由'" @ok="save">

      <a-form layout="vertical">

        <a-form-item label="国家代码 (ISO-2)">

          <a-input v-model:value="form.country_code" placeholder="US / CN / SA" />

        </a-form-item>

        <a-form-item label="渠道类型">

          <a-select v-model:value="form.channel_type" :options="channelOptions" />

        </a-form-item>

        <a-form-item label="账号 / ID">

          <a-input v-model:value="form.account_id" />

        </a-form-item>

        <a-form-item label="预填文案">

          <a-textarea v-model:value="form.prefilled_text" :rows="2" />

        </a-form-item>

        <a-form-item label="启用">

          <a-switch v-model:checked="form.is_active" />

        </a-form-item>

      </a-form>

    </a-modal>

  </YdPage>

</template>



<script setup lang="ts">

import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { storeToRefs } from 'pinia'

import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'

import { useUiPreferencesStore } from '@/stores/uiPreferences'

import { message } from 'ant-design-vue'

import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/api'



const router = useRouter()
const loading = ref(false)

const rows = ref<any[]>([])

const webhookConfig = ref<{
  secret_configured?: boolean
  channels?: Array<{ id: string; label: string; url: string; curl_example: string }>
} | null>(null)

const wecomSaving = ref(false)
const rehearsal5aLoading = ref(false)
const rehearsal5bLoading = ref(false)
const wecomForm = ref({
  enabled: false,
  corp_id: '',
  agent_id: '',
  agent_secret: '',
  agent_secret_set: false,
  push_userids_text: '',
  webhook_url: '',
})

const tablePanelRef = ref<HTMLElement | null>(null)

const ui = useUiPreferencesStore()

const { antTableSize: tableSize } = storeToRefs(ui)

const modalOpen = ref(false)

const editId = ref<number | null>(null)

const form = ref({

  country_code: 'US',

  channel_type: 'whatsapp',

  account_id: '',

  prefilled_text: 'Hello! How can I help you?',

  is_active: true,

})



const channelOptions = [

  { label: 'WhatsApp', value: 'whatsapp' },

  { label: 'Telegram', value: 'telegram' },

  { label: 'LINE', value: 'line' },

  { label: 'Zalo', value: 'zalo' },

  { label: '在线客服', value: 'live_chat' },

  { label: '询盘表单', value: 'form' },

]



const cols = [

  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },

  { title: '国家', dataIndex: 'country_code', key: 'country_code', width: 80 },

  { title: '渠道', dataIndex: 'channel_type', key: 'channel_type', width: 120 },

  { title: '账号', dataIndex: 'account_id', key: 'account_id' },

  { title: '状态', key: 'active', width: 90 },

  { title: '操作', key: 'actions', width: 160 },

]



async function load() {

  loading.value = true

  try {

    rows.value = await apiGet('/im-routing/')

  } catch {

    message.error('加载 IM 路由失败')

  } finally {

    loading.value = false

  }

}



async function loadWebhookConfig() {

  try {

    webhookConfig.value = await apiGet('/inquiries/channels/config')

  } catch {

    webhookConfig.value = null

  }

}



function copyText(text: string) {

  navigator.clipboard.writeText(text).then(() => {

    message.success('已复制')

  }).catch(() => {

    message.warning('复制失败，请手动选择')

  })

}



function openCreate() {

  editId.value = null

  form.value = {

    country_code: 'US',

    channel_type: 'whatsapp',

    account_id: '',

    prefilled_text: 'Hello! How can I help you?',

    is_active: true,

  }

  modalOpen.value = true

}



function editRow(r: any) {

  editId.value = r.id

  form.value = {

    country_code: r.country_code,

    channel_type: r.channel_type,

    account_id: r.account_id,

    prefilled_text: r.prefilled_text || '',

    is_active: r.is_active !== false,

  }

  modalOpen.value = true

}



async function save() {

  try {

    const body = { ...form.value, country_code: form.value.country_code.toUpperCase() }

    if (editId.value) await apiPut(`/im-routing/${editId.value}`, body)

    else await apiPost('/im-routing/', body)

    message.success('已保存')

    modalOpen.value = false

    await load()

  } catch {

    message.error('保存失败')

  }

}



async function removeRow(id: number) {

  try {

    await apiDelete(`/im-routing/${id}`)

    message.success('已删除')

    await load()

  } catch {

    message.error('删除失败')

  }

}



async function loadWecomPush() {
  try {
    const d = await apiGet('/client/wecom-push-config')
    if (d) {
      wecomForm.value = {
        enabled: !!d.enabled,
        corp_id: d.corp_id || '',
        agent_id: d.agent_id || '',
        agent_secret: '',
        agent_secret_set: !!d.agent_secret_set,
        push_userids_text: d.push_userids_text || (d.push_userids || []).join('|'),
        webhook_url: d.webhook_url || '',
      }
    }
  } catch {
    /* 租户未开通时忽略 */
  }
}

async function runRehearsal5a() {
  rehearsal5aLoading.value = true
  try {
    const d = await apiPost('/client/sales-channel-rehearsal/inbound')
    message.success(d?.inquiry_id ? `入站成功，询盘 ${d.inquiry_id}` : '入站彩排完成')
  } catch {
    message.error('入站测试失败')
  } finally {
    rehearsal5aLoading.value = false
  }
}

async function runRehearsal5b() {
  rehearsal5bLoading.value = true
  try {
    const d = await apiPost<{ ok?: boolean; status?: string }>('/client/sales-channel-rehearsal/wecom-push')
    if (d?.ok || d?.status === 'sent') {
      message.success('测试通知已发送，请查看销售企微')
    } else {
      message.warning('未发送：请先保存企微配置或配置开发环境 WECOM_*')
    }
  } catch {
    message.error('推送测试失败')
  } finally {
    rehearsal5bLoading.value = false
  }
}

async function saveWecomPush() {
  wecomSaving.value = true
  try {
    const body: Record<string, unknown> = {
      enabled: wecomForm.value.enabled,
      corp_id: wecomForm.value.corp_id,
      agent_id: wecomForm.value.agent_id,
      push_userids: wecomForm.value.push_userids_text,
      webhook_url: wecomForm.value.webhook_url,
    }
    if (wecomForm.value.agent_secret) {
      body.agent_secret = wecomForm.value.agent_secret
    }
    await apiPut('/client/wecom-push-config', body)
    message.success('企微推送配置已保存')
    await loadWecomPush()
  } catch {
    message.error('保存失败')
  } finally {
    wecomSaving.value = false
  }
}

onMounted(() => {

  void load()

  void loadWebhookConfig()

  void loadWecomPush()

})

</script>



<style scoped>

.panel-head {

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  justify-content: flex-end;

  gap: 8px;

}

.webhook-row {

  display: flex;

  justify-content: space-between;

  align-items: flex-start;

  gap: 12px;

  padding: 8px 0;

  border-bottom: 1px solid #f0f0f0;

}

.webhook-url {

  font-size: 12px;

  color: #64748b;

  word-break: break-all;

  margin: 4px 0 0;

}

.curl-block {

  font-size: 11px;

  background: #f8fafc;

  padding: 8px;

  border-radius: 6px;

  overflow-x: auto;

  white-space: pre-wrap;

}

</style>

