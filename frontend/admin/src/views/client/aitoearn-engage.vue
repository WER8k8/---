/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>

  <YdPage title="评论互动" subtitle="拉评 · AI 草稿 · AiToEarn 真回复" surface="elevated">

    <AitoearnCapabilityBar ref="capabilityRef" />



    <a-space class="mb-4" wrap>

      <a-button :loading="pulling" type="primary" @click="pullComments">拉取抖音评论</a-button>

      <a-button @click="loadInteractions">刷新列表</a-button>

      <router-link to="/client/distribute">← 内容分发</router-link>

    </a-space>



    <a-empty

      v-if="!loading && !items.length"

      :description="emptyHint"

    >

      <a-button type="primary" @click="pullComments">拉取评论</a-button>

    </a-empty>



    <a-table

      v-else

      :loading="loading"

      :columns="columns"

      :data-source="items"

      row-key="id"

      :pagination="{ pageSize: 10 }"

    >

      <template #bodyCell="{ column, record }">

        <template v-if="column.key === 'content'">

          <div class="engage-content">{{ record.content }}</div>

          <a-textarea

            v-if="canEditReply(record)"

            v-model:value="replyEdits[record.id]"

            :rows="2"

            class="engage-reply-edit"

            placeholder="编辑回复后发送"

          />

          <div v-else-if="record.draft_reply || record.final_reply" class="engage-draft">

            草稿：{{ record.final_reply || record.draft_reply }}

          </div>

        </template>

        <template v-else-if="column.key === 'status'">

          <a-tag>{{ record.status }}</a-tag>

        </template>

        <template v-else-if="column.key === 'actions'">

          <a-space>

            <a-button

              size="small"

              :disabled="!canRegenerate(record)"

              :loading="regeneratingId === record.id"

              @click="regenerateDraft(record)"

            >

              重生成

            </a-button>

            <a-button

              size="small"

              type="primary"

              :disabled="!canAutoSend(record)"

              :loading="sendingId === record.id"

              @click="approveAndSend(record)"

            >

              AiToEarn 发送

            </a-button>

          </a-space>

        </template>

      </template>

    </a-table>

  </YdPage>

</template>



<script setup lang="ts">

import { computed, onMounted, reactive, ref } from 'vue'

import { message } from 'ant-design-vue'

import { YdPage } from '@/components/youding'

import AitoearnCapabilityBar from '@/components/tenant/AitoearnCapabilityBar.vue'

import { apiGet, apiPost, getAuthToken } from '@/utils/api'

import { unwrapFetchedJson } from '@/api'



type InteractionRow = {

  id: string

  content?: string

  draft_reply?: string

  final_reply?: string

  status?: string

  platform?: string

}



const loading = ref(false)

const pulling = ref(false)

const sendingId = ref('')

const regeneratingId = ref('')

const items = ref<InteractionRow[]>([])

const replyEdits = reactive<Record<string, string>>({})

const capabilityRef = ref<InstanceType<typeof AitoearnCapabilityBar> | null>(null)

const engageAvailable = ref(false)



const emptyHint = computed(() =>

  engageAvailable.value

    ? '暂无待处理评论，可点击「拉取抖音评论」同步'

    : 'AiToEarn 未配置或未分配矩阵号 — 自动回评不可用，请先完成运维配置',

)



const columns = [

  { title: '平台', dataIndex: 'platform', width: 90 },

  { title: '内容', key: 'content' },

  { title: '状态', key: 'status', width: 120 },

  { title: '操作', key: 'actions', width: 200 },

]



function canAutoSend(record: { status?: string }) {

  return ['draft_ready', 'failed'].includes(String(record.status || ''))

}



function canRegenerate(record: { status?: string }) {

  return !['sent', 'skipped', 'sending'].includes(String(record.status || ''))

}



function canEditReply(record: { status?: string }) {

  return canAutoSend(record)

}



function replyText(record: { id: string; final_reply?: string; draft_reply?: string }) {

  return replyEdits[record.id] || record.final_reply || record.draft_reply || ''

}



async function loadInteractions() {

  loading.value = true

  try {

    const data = await apiGet<{ items?: InteractionRow[] }>('/social-interactions/')

    items.value = data?.items || []

    for (const row of items.value) {

      if (!replyEdits[row.id]) {

        replyEdits[row.id] = row.final_reply || row.draft_reply || ''

      }

    }

  } catch (e: unknown) {

    message.error(e instanceof Error ? e.message : '加载失败')

  } finally {

    loading.value = false

  }

}



async function pullComments() {

  pulling.value = true

  try {

    const res = await fetch('/api/v1/client/douyin-comments/pull', {

      method: 'POST',

      headers: { Authorization: `Bearer ${getAuthToken()}` },

    })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message || '拉取失败')

    const data = unwrapFetchedJson<{ ingested?: number; hint?: string }>(body)

    message.success(data?.hint || `已入库 ${data?.ingested ?? 0} 条`)

    await loadInteractions()

  } catch (e: unknown) {

    message.error(e instanceof Error ? e.message : '拉取失败')

  } finally {

    pulling.value = false

  }

}



async function regenerateDraft(record: Record<string, unknown>) {

  const id = String(record.id || '')

  regeneratingId.value = id

  try {

    const row = await apiPost<InteractionRow>(

      `/social-interactions/${id}/regenerate-draft`,

      {},

    )

    replyEdits[id] = row?.draft_reply || row?.final_reply || ''

    message.success('草稿已重新生成')

    await loadInteractions()

  } catch (e: unknown) {

    message.error(e instanceof Error ? e.message : '重生成失败')

  } finally {

    regeneratingId.value = ''

  }

}



async function approveAndSend(record: Record<string, unknown>) {

  const id = String(record.id || '')

  sendingId.value = id

  try {

    await apiPost(`/social-interactions/${id}/approve`, {

      final_reply: replyText({

        id,

        final_reply: record.final_reply as string | undefined,

        draft_reply: record.draft_reply as string | undefined,

      }),

      auto_send_via_aitoearn: true,

    })

    message.success('已通过 AiToEarn 发送')

    await loadInteractions()

    void capabilityRef.value?.reload?.()

  } catch (e: unknown) {

    message.error(e instanceof Error ? e.message : '发送失败')

  } finally {

    sendingId.value = ''

  }

}



async function loadEngageCapability() {

  try {

    const data = await apiGet<{ modules?: { engage?: { available?: boolean } } }>(

      '/aitoearn/hub/capabilities',

    )

    engageAvailable.value = Boolean(data?.modules?.engage?.available)

  } catch {

    engageAvailable.value = false

  }

}



onMounted(() => {

  void loadEngageCapability()

  void loadInteractions()

})

</script>



<style scoped>

.mb-4 { margin-bottom: 16px; }

.engage-content { font-weight: 500; }

.engage-draft { margin-top: 4px; color: var(--uj-text-secondary, #64748b); font-size: 12px; }

.engage-reply-edit { margin-top: 8px; }

</style>

