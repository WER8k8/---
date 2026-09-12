<template>
  <YdPage title="内容分发中心" subtitle="输入 → 生成 → 一键发布到已绑平台" surface="elevated">
    <a-alert
      v-if="overseasHandoff.ready"
      type="success"
      show-icon
      class="mb-4"
      message="已从「中文片出海」带入成片"
    >
      <template #description>
        <span>{{ overseasHandoff.summary }}</span>
        <a-button v-if="overseasHandoff.outputUrl" type="link" size="small" @click="openOverseasOutput">
          预览成片
        </a-button>
      </template>
    </a-alert>

    <a-alert
      v-if="overseasHandoff.ready && overseasHandoff.hasVideoOutput && !hasVideoPlatforms"
      type="warning"
      show-icon
      class="mb-4"
      message="出海成片已就绪，但尚未绑定视频平台"
      description="请先在下方完成视频平台绑号（AiToEarn 或 OAuth），再点「发布出海成片」。仅发官网可选择任意已绑平台或联系运维开启租户官网视频页。"
    >
      <template #action>
        <a-button size="small" @click="scrollToBind">去绑号</a-button>
      </template>
    </a-alert>

    <PublishReadinessBar ref="readinessRef" @action="onReadinessAction" @loaded="onReadinessLoaded" />

    <AitoearnCapabilityBar ref="capabilityRef" />

    <div v-if="showBindSection" id="bind-section" class="mb-4">
      <VideoPublishBindHub ref="bindHubRef" @connect="goConnectPlatform" />
    </div>

    <a-card title="① 输入内容" class="mb-4">
      <a-radio-group v-model:value="contentKind" class="mb-3">
        <a-radio-button value="article">发文章</a-radio-button>
        <a-radio-button value="video">发视频</a-radio-button>
      </a-radio-group>

      <a-tabs v-model:active-key="inputMode">
        <a-tab-pane key="brief" tab="提要求">
          <a-textarea
            v-model:value="briefText"
            :rows="4"
            placeholder="例如：写一篇英文产品介绍，突出 A1 防火与出口认证，适合 LinkedIn 和百家号"
          />
        </a-tab-pane>
        <a-tab-pane key="copy" tab="粘贴文案">
          <a-textarea
            v-model:value="copyText"
            :rows="8"
            placeholder="粘贴已有文章或视频解说词…"
          />
        </a-tab-pane>
        <a-tab-pane key="images" tab="产品图片">
          <p class="hint">上传产品图可用于建站素材；发视频时建议配合文案说明产品卖点。</p>
          <input ref="imageInputRef" type="file" accept="image/*" multiple class="hidden" @change="onImagesPick" />
          <a-button :loading="imagesUploading" @click="imageInputRef?.click()">上传图片</a-button>
          <div v-if="productImages.length" class="img-chips">
            <a-tag v-for="img in productImages" :key="img.url">{{ img.name || '产品图' }}</a-tag>
          </div>
          <a-textarea v-model:value="copyText" class="mt-3" :rows="4" placeholder="补充一句产品说明（用于生成视频脚本）" />
        </a-tab-pane>
      </a-tabs>

      <a-space class="mt-3" wrap>
        <a-button type="primary" :loading="generating" @click="handleGenerate">
          {{ contentKind === 'video' ? '生成视频脚本' : 'AI 生成文章' }}
        </a-button>
        <a-button v-if="contentKind === 'video' && generatedBody" @click="goVideoPipeline">
          继续渲染视频 →
        </a-button>
      </a-space>
    </a-card>

    <a-card v-if="generatedBody" title="② 预览与编辑" class="mb-4">
      <a-input v-model:value="titleText" placeholder="标题" class="mb-2" />
      <a-textarea v-model:value="generatedBody" :rows="10" />
    </a-card>

    <a-card title="③ 选择平台 · 一键分发">
      <p v-if="!boundPlatforms.length" class="hint warn">
        暂无已绑平台。请先完成上方绑号（AiToEarn 一次绑多平台，或逐个 OAuth/Cookie 连接）。
      </p>
      <a-checkbox-group v-else v-model:value="selectedPlatformIds" class="platform-checks">
        <a-checkbox v-for="p in boundPlatforms" :key="p.id" :value="p.id">
          {{ p.name }}
          <a-tag v-if="p.kind === 'video'" size="small" color="blue">视频</a-tag>
        </a-checkbox>
      </a-checkbox-group>

      <div v-if="contentKind === 'video' || overseasHandoff.hasVideoOutput" class="schedule-row mt-3">
        <span class="schedule-label">定时发布（可选）</span>
        <a-date-picker
          v-model:value="scheduleAt"
          show-time
          format="YYYY-MM-DD HH:mm"
          placeholder="留空则立即发布"
          style="min-width: 220px"
        />
      </div>

      <a-space class="mt-4" wrap>
        <a-button
          type="primary"
          size="large"
          :loading="publishing"
          :disabled="publishDisabled"
          @click="handlePublish"
        >
          {{ publishButtonLabel }}
        </a-button>
        <a-button @click="selectAllBound">全选已绑平台</a-button>
        <router-link to="/client/queues/publish">发布队列 →</router-link>
      </a-space>

      <a-alert v-if="publishSummary" class="mt-3" :type="publishSummary.ok ? 'success' : 'warning'" show-icon :message="publishSummary.text" />
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import PublishReadinessBar, { type ReadinessAction } from '@/components/tenant/PublishReadinessBar.vue'
import VideoPublishBindHub from '@/components/tenant/VideoPublishBindHub.vue'
import AitoearnCapabilityBar from '@/components/tenant/AitoearnCapabilityBar.vue'
import type { Dayjs } from 'dayjs'

import { apiGet, apiPost, getAuthToken } from '@/utils/api'
import { uploadSiteProductImages, type UploadedProductImage } from '@/utils/siteProductImages'
import { unwrapFetchedJson } from '@/api'
import { fetchMediaStudioProject } from '@/api/cross-border'
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl'

const router = useRouter()
const route = useRoute()

const readinessRef = ref<InstanceType<typeof PublishReadinessBar> | null>(null)
const capabilityRef = ref<InstanceType<typeof AitoearnCapabilityBar> | null>(null)
const bindHubRef = ref<InstanceType<typeof VideoPublishBindHub> | null>(null)
const imageInputRef = ref<HTMLInputElement>()

const contentKind = ref<'article' | 'video'>('article')
const inputMode = ref('brief')
const briefText = ref('')
const copyText = ref('')
const titleText = ref('')
const generatedBody = ref('')
const generating = ref(false)
const publishing = ref(false)
const publishSummary = ref<{ ok: boolean; text: string } | null>(null)
const scheduleAt = ref<Dayjs | undefined>(undefined)
const showBindSection = ref(true)
const productImages = ref<UploadedProductImage[]>([])
const imagesUploading = ref(false)

type BoundPlatform = { id: string; name: string; kind: 'article' | 'video' }
const boundPlatforms = ref<BoundPlatform[]>([])
const selectedPlatformIds = ref<string[]>([])

const overseasMediaTaskId = ref('')
const overseasHandoff = ref({
  ready: false,
  summary: '',
  outputUrl: '',
  hasVideoOutput: false,
})

const effectiveInput = computed(() => {
  if (inputMode.value === 'brief') return briefText.value.trim()
  return copyText.value.trim()
})

const publishButtonLabel = computed(() => {
  if (overseasHandoff.value.ready && overseasHandoff.value.hasVideoOutput) {
    return '发布出海成片到已选平台'
  }
  return '一键分发'
})

const publishDisabled = computed(() => {
  if (overseasHandoff.value.ready && overseasHandoff.value.hasVideoOutput) {
    return !overseasMediaTaskId.value
  }
  return !generatedBody.value || !selectedPlatformIds.value.length
})

const hasVideoPlatforms = computed(() =>
  boundPlatforms.value.some((p) => p.kind === 'video'),
)

function scrollToBind() {
  showBindSection.value = true
  nextTick(() => {
    document.getElementById('bind-section')?.scrollIntoView({ behavior: 'smooth' })
  })
}

function openOverseasOutput() {
  const url = resolveMediaAssetUrl(overseasHandoff.value.outputUrl)
  if (url) window.open(url, '_blank')
}

async function loadOverseasHandoff(mediaTaskId: string) {
  try {
    const studio = await fetchMediaStudioProject(mediaTaskId)
    const proj = (studio?.project || {}) as Record<string, unknown>
    const script = String(proj.script_en || proj.transcript_zh || '').trim()
    const output = String(proj.output_url || studio?.result_url || '').trim()
    if (!script && !output) {
      message.warning('该出海任务尚无脚本或成片，请先在「中文片出海」完成处理')
      return
    }
    overseasMediaTaskId.value = mediaTaskId
    contentKind.value = 'video'
    inputMode.value = 'copy'
    if (script) {
      copyText.value = script
      generatedBody.value = script
    }
    titleText.value = studio?.title || '出海产品视频'
    overseasHandoff.value = {
      ready: true,
      summary: script
        ? `任务 ${mediaTaskId.slice(0, 8)}… · 英文脚本已载入`
        : `任务 ${mediaTaskId.slice(0, 8)}…`,
      outputUrl: output,
      hasVideoOutput: Boolean(output),
    }
    const videoIds = boundPlatforms.value.filter((p) => p.kind === 'video').map((p) => p.id)
    if (videoIds.length) {
      selectedPlatformIds.value = videoIds
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载出海项目失败')
  }
}

function onReadinessAction(a: ReadinessAction) {
  if (a.path.includes('focus=bind')) {
    showBindSection.value = true
    nextTick(() => {
      document.getElementById('bind-section')?.scrollIntoView({ behavior: 'smooth' })
    })
    return
  }
  router.push(a.path)
}

function onReadinessLoaded() {
  /* 绑号区默认展示 */
}

function goConnectPlatform(platform: { id: string; name: string }) {
  router.push({
    path: '/client/seo-publish',
    query: { mode: 'video', connect: platform.id, connect_name: platform.name },
  })
}

async function loadBoundPlatforms() {
  try {
    const [accountsRes, platformsRes] = await Promise.all([
      fetch('/api/v1/seo-matrix/accounts', { headers: { Authorization: `Bearer ${getAuthToken()}` } }),
      fetch('/api/v1/seo-matrix/platforms', { headers: { Authorization: `Bearer ${getAuthToken()}` } }),
    ])
    const accountsBody = unwrapFetchedJson<{ platform?: string; status?: string; login_status?: string }[]>(
      await accountsRes.json(),
    )
    const platformRows = unwrapFetchedJson<{ id: string; name: string; content_type?: string }[]>(
      await platformsRes.json(),
    )
    const platMap = new Map((Array.isArray(platformRows) ? platformRows : []).map((p) => [String(p.id), p]))
    const bound = (Array.isArray(accountsBody) ? accountsBody : []).filter(
      (a) => a.login_status === 'logged_in' || a.status === 'active',
    )
    boundPlatforms.value = bound
      .map((a) => {
        const pid = String(a.platform || '')
        const row = platMap.get(pid)
        if (!row) return null
        const ctype = (row.content_type || '').toLowerCase()
        const kind: 'article' | 'video' = ctype.includes('video') ? 'video' : 'article'
        return { id: pid, name: row.name, kind }
      })
      .filter(Boolean) as BoundPlatform[]
    if (!selectedPlatformIds.value.length) {
      selectedPlatformIds.value = boundPlatforms.value.map((p) => p.id)
    }
  } catch {
    boundPlatforms.value = []
  }
}

function selectAllBound() {
  selectedPlatformIds.value = boundPlatforms.value.map((p) => p.id)
}

async function onImagesPick(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  input.value = ''
  if (!files.length) return
  imagesUploading.value = true
  try {
    productImages.value.push(...(await uploadSiteProductImages(files)))
    message.success(`已上传 ${files.length} 张图片`)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    imagesUploading.value = false
  }
}

async function handleGenerate() {
  const topic = effectiveInput.value
  if (!topic) {
    message.warning('请先输入要求或文案')
    return
  }
  generating.value = true
  publishSummary.value = null
  try {
    if (contentKind.value === 'video' && inputMode.value !== 'brief' && copyText.value.trim().length > 80) {
      generatedBody.value = copyText.value.trim()
      titleText.value = titleText.value || topic.slice(0, 40)
      message.success('已载入文案，可继续渲染视频')
      return
    }
    const res = await fetch('/api/v1/seo-matrix/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({
        topic,
        contentType: contentKind.value === 'video' ? 'product' : 'seo',
        style: 'marketing',
        language: 'zh-CN',
        wordCount: contentKind.value === 'video' ? '300' : '500',
      }),
    })
    const body = await res.json()
    if (!res.ok) throw new Error(body.message || '生成失败')
    const data = unwrapFetchedJson<{ content?: string; text?: string }>(body)
    generatedBody.value = data?.content || data?.text || ''
    titleText.value = topic.slice(0, 60)
    message.success(contentKind.value === 'video' ? '视频脚本草稿已生成' : '文章已生成')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'AI 生成失败')
  } finally {
    generating.value = false
  }
}

function goVideoPipeline() {
  if (!generatedBody.value) {
    message.warning('请先生成或粘贴文案')
    return
  }
  sessionStorage.setItem(
    'article_to_video_payload',
    JSON.stringify({ article: generatedBody.value, title: titleText.value || '产品视频' }),
  )
  router.push('/client/article-to-video')
}

async function handlePublish() {
  if (overseasHandoff.value.ready && overseasHandoff.value.hasVideoOutput && overseasMediaTaskId.value) {
    const videoIds = boundPlatforms.value.filter((p) => p.kind === 'video').map((p) => p.id)
    const platformIds = selectedPlatformIds.value.filter((id) => videoIds.includes(id))
    if (!platformIds.length && !hasVideoPlatforms.value) {
      message.info('未绑视频外站，将尝试仅登记租户官网视频页')
    }
    publishing.value = true
    publishSummary.value = null
    try {
      const res = await fetch('/api/v1/publish/video/distribute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
        body: JSON.stringify({
          media_task_id: overseasMediaTaskId.value,
          platform_ids: platformIds,
          include_tenant_site: true,
          scheduled_at: scheduleAt.value ? scheduleAt.value.toISOString() : undefined,
        }),
      })
      const body = await res.json()
      if (body.code && body.code !== 0) throw new Error(body.message || '视频分发失败')
      const data = body.data || body
      const results = (data.results || []) as { success?: boolean; platform_post_url?: string }[]
      const ok = results.filter((r) => r.success || r.platform_post_url).length
      const siteOk = data.tenant_site?.published
      publishSummary.value = {
        ok: ok > 0 || Boolean(siteOk),
        text: siteOk
          ? `官网已登记${ok ? `；${ok} 个外站成功` : ''}`
          : ok > 0
            ? `已发布到 ${ok} 个视频平台`
            : '分发未完成，请检查平台绑定或 Worker 配置',
      }
      message.success(publishSummary.value.text)
      void readinessRef.value?.reload?.()
      void capabilityRef.value?.reload?.()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '视频分发失败')
    } finally {
      publishing.value = false
    }
    return
  }

  if (contentKind.value === 'video') {
    goVideoPipeline()
    message.info('视频需先渲染完成，请在文章转视频页勾选平台后引流发布')
    return
  }
  if (!generatedBody.value) {
    message.warning('请先生成内容')
    return
  }
  if (!selectedPlatformIds.value.length) {
    message.warning('请至少选择一个已绑平台')
    return
  }
  publishing.value = true
  publishSummary.value = null
  try {
    const res = await fetch('/api/v1/seo-matrix/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({
        content: generatedBody.value,
        contentType: 'seo',
        platforms: selectedPlatformIds.value,
        title: titleText.value || undefined,
      }),
    })
    const body = await res.json()
    const data = body.data || body
    const results = (data.results || data.platforms || []) as { success?: boolean; platform_post_url?: string }[]
    const ok = results.filter((r) => r.success).length
    const fail = results.length - ok
    publishSummary.value = {
      ok: ok > 0,
      text: fail ? `成功 ${ok} 个，失败 ${fail} 个` : `已分发到 ${ok} 个平台`,
    }
    message.success(publishSummary.value.text)
    void readinessRef.value?.reload?.()
    void capabilityRef.value?.reload?.()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '分发失败')
  } finally {
    publishing.value = false
  }
}

onMounted(async () => {
  if (route.query.focus === 'bind') {
    showBindSection.value = true
    await nextTick()
    document.getElementById('bind-section')?.scrollIntoView({ behavior: 'smooth' })
  }
  const prefill = route.query.topic
  if (typeof prefill === 'string' && prefill) {
    briefText.value = prefill
  }
  await loadBoundPlatforms()
  const mediaTaskId = route.query.media_task_id
  if (typeof mediaTaskId === 'string' && mediaTaskId.trim()) {
    await loadOverseasHandoff(mediaTaskId.trim())
  }
})
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.schedule-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.schedule-label { color: var(--uj-text-secondary, #64748b); font-size: 13px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.hint { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.hint.warn { color: #b45309; }
.hidden { display: none; }
.img-chips { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.platform-checks { display: flex; flex-direction: column; gap: 8px; }
</style>
