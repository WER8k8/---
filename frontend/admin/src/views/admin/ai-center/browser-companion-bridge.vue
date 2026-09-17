/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="浏览器伴侣工作台" subtitle="优丁平台专属 · 内容仅来自本平台任务">
    <a-alert
      v-if="blocked"
      type="error"
      show-icon
      class="mb-4"
      message="请从优丁视频/内容分发入口打开"
      description="浏览器伴侣不能独立使用。请返回「文章转视频 → 视频引流发布」或 SEO 矩阵，点击「打开伴侣工作台」。"
    />
    <template v-else>
      <a-alert type="info" show-icon class="mb-4" message="优丁平台专属">
        <template #description>
          <p>{{ payload?.usage_notice || '内容载荷由优丁 API 下发，请勿复制到外站单独使用。' }}</p>
        </template>
      </a-alert>

      <a-card v-if="loading" loading />

      <a-card v-else-if="payload" title="任务内容">
        <p><strong>标题：</strong>{{ payload.title }}</p>
        <p v-if="payload.launch_kind === 'video'"><strong>视频：</strong>
          <a :href="payload.video_url" target="_blank" rel="noopener">{{ payload.video_url }}</a>
        </p>
        <p v-if="payload.body || payload.body_html" class="mt-2 whitespace-pre-wrap text-sm text-gray-600">
          {{ payload.body || payload.body_html }}
        </p>
        <div v-if="payload.launch_kind === 'article'" class="mt-4 p-4 border rounded bg-gray-50 prose prose-sm max-w-none">
          <div v-html="sanitizeHtml(payload.body_html)" />
        </div>
        <div class="mt-4 flex flex-wrap gap-2">
          <a-button v-if="isMultipost" type="primary" :loading="busy" @click="trustAndPublish">
            授权并打开 MultiPost 发布
          </a-button>
          <a-button v-if="isWechatsync" @click="copyForSync">复制正文（在本页用 Wechatsync 同步）</a-button>
          <router-link to="/admin/ai-center/article-to-video">
            <a-button>返回视频任务</a-button>
          </router-link>
        </div>
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'
import {
  openMultipostPublish,
  requestMultipostTrustDomain,
} from '@/utils/multipostBridge'
import { useSanitize } from '@/composables/useSanitize'

const { sanitizeHtml } = useSanitize()

const LAUNCH_KEY = 'youding_companion_launch'

const route = useRoute()
const loading = ref(true)
const busy = ref(false)
const blocked = ref(false)
const payload = ref<Record<string, any> | null>(null)

const companionId = computed(() => String(route.query.companion || 'browser_companion_multipost'))
const mediaTaskId = computed(() => String(route.query.media_task_id || ''))
const contentId = computed(() => String(route.query.content_id || ''))
const isMultipost = computed(() => companionId.value.includes('multipost'))
const isWechatsync = computed(() => companionId.value.includes('wechatsync'))

function authHeaders(): Record<string, string> {
  const tk = getAuthToken()
  return tk ? { Authorization: `Bearer ${tk}` } : {}
}

function assertPlatformLaunch(): boolean {
  const from = route.query.from
  if (from !== 'youding') return false
  try {
    const raw = sessionStorage.getItem(LAUNCH_KEY)
    if (!raw) return false
    const ctx = JSON.parse(raw) as { ts?: number; media_task_id?: string; content_id?: string }
    if (!ctx.ts || Date.now() - ctx.ts > 15 * 60 * 1000) return false
    if (mediaTaskId.value && ctx.media_task_id !== mediaTaskId.value) return false
    if (contentId.value && ctx.content_id !== contentId.value) return false
    return true
  } catch {
    return false
  }
}

async function loadPayload() {
  if (!assertPlatformLaunch()) {
    blocked.value = true
    loading.value = false
    return
  }
  const params = new URLSearchParams({ companion_id: companionId.value })
  if (mediaTaskId.value) params.set('media_task_id', mediaTaskId.value)
  if (contentId.value) params.set('content_id', contentId.value)
  const res = await fetch(`/api/v1/publish/companion/payload?${params}`, { headers: authHeaders() })
  const body = await res.json()
  if (!res.ok || (body.code && body.code !== 0)) {
    blocked.value = true
    message.error(body.message || '无法加载优丁专属内容')
    loading.value = false
    return
  }
  payload.value = (body.data || body).payload || null
  loading.value = false
}

async function trustAndPublish() {
  if (!payload.value?.multipost?.sync) {
    message.warning('无 MultiPost 同步载荷')
    return
  }
  busy.value = true
  try {
    await requestMultipostTrustDomain()
    await openMultipostPublish(payload.value.multipost.sync as Record<string, unknown>)
    message.success('已打开 MultiPost 发布窗口，请在扩展内选择平台并发草稿')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'MultiPost 调用失败')
  } finally {
    busy.value = false
  }
}

async function copyForSync() {
  const text = payload.value?.body_html || payload.value?.body || ''
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制正文；请在本页打开 Wechatsync 扩展同步到草稿')
  } catch {
    message.warning('复制失败，请手动选择正文')
  }
}

onMounted(() => {
  void loadPayload()
})
</script>
