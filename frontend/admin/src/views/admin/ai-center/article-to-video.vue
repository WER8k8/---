/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="文章转视频" subtitle="文章 → 分镜脚本 → Cosmos 渲染队列 → 成品视频" surface="elevated">
    <template #actions>
      <a-space wrap>
        <a-tag v-if="mockRender" color="orange">Mock 渲染（本地验证）</a-tag>
        <a-button type="link" @click="router.push('/admin/ai-center/scenario-models')">场景模型</a-button>
        <a-button type="link" @click="router.push('/media-factory/render-queue')">渲染队列</a-button>
      </a-space>
    </template>
  <div class="article-to-video-page space-y-6 animate-fade-in">

    <a-steps :current="currentStep" size="small" class="bg-white p-4 rounded-lg">
      <a-step title="输入文章" />
      <a-step title="生成脚本" />
      <a-step title="提交渲染" />
      <a-step title="任务状态" />
      <a-step title="剪辑调试" />
    </a-steps>

    <a-card v-if="currentStep === 0" title="步骤 1：输入文章或主题">
      <a-form layout="vertical">
        <a-form-item label="视频标题（可选）">
          <a-input v-model:value="form.title" placeholder="例如：轻集料混凝土应用介绍" />
        </a-form-item>
        <a-form-item label="文章内容" required>
          <a-textarea
            v-model:value="form.article"
            :rows="12"
            placeholder="粘贴完整文章，或输入主题与要点…"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="分辨率">
              <a-select v-model:value="form.resolution">
                <a-select-option value="1080p">1080p</a-select-option>
                <a-select-option value="720p">720p</a-select-option>
                <a-select-option value="480p">480p</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="画幅">
              <a-select v-model:value="form.aspect">
                <a-select-option value="16:9">16:9 横屏</a-select-option>
                <a-select-option value="9:16">9:16 竖屏</a-select-option>
                <a-select-option value="1:1">1:1 方形</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <a-button type="primary" size="large" :loading="generatingScript" @click="generateScript">
        生成视频脚本
      </a-button>
    </a-card>

    <a-card v-if="currentStep >= 1" title="步骤 2：分镜脚本（可编辑）">
      <a-textarea v-model:value="script" :rows="14" />
      <div class="mt-4 flex gap-3">
        <a-button @click="currentStep = 0">上一步</a-button>
        <a-button type="primary" :disabled="!script.trim()" @click="currentStep = 2">下一步：提交渲染</a-button>
      </div>
    </a-card>

    <a-card v-if="currentStep === 2" title="步骤 3：提交渲染任务">
      <a-alert
        type="info"
        show-icon
        class="mb-4"
        message="将使用「脚本→视频」场景模型（Cosmos Predict）。未配置 GPU NIM 时，开发环境可走 Mock 渲染验证流程。"
        description="Mock 模式会生成约 2 秒的深色预览片（非真实 AI 画面）；真实视频需部署 Cosmos NIM 并关闭 Mock。"
      />
      <a-button type="primary" size="large" :loading="submitting" @click="submitRender">
        加入渲染队列并开始渲染
      </a-button>
    </a-card>

    <a-card v-if="currentStep === 3 && task" title="步骤 4：任务状态">
      <a-alert
        v-if="task.storage_note"
        :type="task.file_purged ? 'warning' : 'info'"
        show-icon
        class="mb-4"
        :message="retentionTitle"
        :description="task.storage_note"
      />

      <a-descriptions bordered size="small" :column="1">
        <a-descriptions-item label="任务 ID">{{ task.id }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColor(task.raw_status)">{{ task.status }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="模型">{{ task.video_model || '-' }}</a-descriptions-item>
        <a-descriptions-item label="进度">
          <a-progress :percent="task.progress" :status="task.raw_status === 'failed' ? 'exception' : undefined" />
        </a-descriptions-item>
        <a-descriptions-item v-if="countdownLabel" label="成品保留">{{ countdownLabel }}</a-descriptions-item>
        <a-descriptions-item v-if="task.error_message" label="错误">{{ task.error_message }}</a-descriptions-item>
        <a-descriptions-item v-if="task.result_url" label="成品">
          <a :href="task.result_url" target="_blank" rel="noopener">下载 / 预览视频</a>
        </a-descriptions-item>
        <a-descriptions-item label="上云状态">
          <a-tag :color="cloudTagColor">{{ task.cloud_upload_status || 'pending' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item v-if="task.tenant_landing_url" label="官网落地页">
          <a :href="task.tenant_landing_url" target="_blank" rel="noopener">{{ task.tenant_landing_url }}</a>
        </a-descriptions-item>
        <a-descriptions-item v-if="task.publish_video_url" label="海外播放">
          <a :href="task.publish_video_url" target="_blank" rel="noopener">R2 / 外链</a>
        </a-descriptions-item>
        <a-descriptions-item v-if="task.cloud_backup_url" label="灾备直链">
          <a :href="task.cloud_backup_url" target="_blank" rel="noopener">棱束链备份</a>
        </a-descriptions-item>
      </a-descriptions>

      <div v-if="task.preview_url && task.raw_status === 'done'" class="mt-4">
        <video :src="task.preview_url" controls class="max-w-full rounded border" style="max-height: 360px" />
      </div>

      <div v-if="task.raw_status === 'done'" class="mt-4 flex flex-wrap gap-3">
        <a-button
          type="primary"
          :loading="trafficLoading"
          :disabled="task.cloud_upload_status !== 'done' && !task.publish_video_url"
          @click="openTrafficModal"
        >
          引流发布（官网 + 视频平台）
        </a-button>
        <a-button v-if="task.preview_url && !task.file_purged" @click="confirmHandoff('downloaded')">
          确认已下载
        </a-button>
        <a-button v-if="task.preview_url && !task.file_purged" @click="openPublishModal">
          登记外链
        </a-button>
      </div>

      <div class="mt-4 flex gap-3">
        <a-button @click="pollTask" :loading="polling">刷新状态</a-button>
        <a-button
          v-if="task.raw_status === 'done' && task.preview_url"
          type="primary"
          @click="openEditor"
        >
          进入剪辑调试
        </a-button>
        <a-button @click="resetFlow">新建任务</a-button>
      </div>
    </a-card>

    <a-card v-if="currentStep === 4 && task" title="步骤 5：剪辑调试">
      <a-row :gutter="16">
        <a-col :xs="24" :lg="14">
          <video
            v-if="editPreviewUrl"
            ref="videoRef"
            :src="editPreviewUrl"
            controls
            class="w-full rounded border bg-black"
            style="max-height: 360px"
            @loadedmetadata="onVideoMeta"
          />
          <a-empty v-else description="暂无可预览成片" />

          <div v-if="videoDuration > 0" class="mt-4 space-y-3">
            <div class="text-sm text-gray-600">
              时长 {{ videoDuration.toFixed(1) }}s · 选中
              {{ clipRange[0].toFixed(1) }}s - {{ clipRange[1].toFixed(1) }}s
            </div>
            <a-slider
              v-model:value="clipRange"
              range
              :min="0"
              :max="videoDuration"
              :step="0.1"
              :tooltip-formatter="(v: number) => `${v?.toFixed(1)}s`"
            />
            <a-space wrap>
              <a-button :loading="clipLoading" type="primary" @click="applyClip">
                应用剪辑
              </a-button>
              <a-tag v-if="task.edited_result_url" color="green">已生成剪辑版</a-tag>
            </a-space>
          </div>
        </a-col>

        <a-col :xs="24" :lg="10">
          <div class="text-sm font-medium mb-2">分镜脚本（可改后重渲）</div>
          <div v-for="(shot, idx) in editShots" :key="idx" class="mb-3 p-2 border rounded">
            <div class="text-xs text-gray-400 mb-1">镜头 {{ shot.index }}</div>
            <a-input v-model:value="shot.visual" placeholder="画面描述" class="mb-2" />
            <a-input v-model:value="shot.narration" placeholder="旁白文案" />
          </div>
          <a-textarea v-model:value="editScript" :rows="8" placeholder="或直接编辑完整脚本" class="mt-2" />
          <div class="mt-4 flex flex-wrap gap-2">
            <a-button :loading="saveScriptLoading" @click="saveScript">保存脚本</a-button>
            <a-button type="primary" :loading="rerenderLoading" @click="rerenderVideo">
              按脚本重新渲染
            </a-button>
            <a-button @click="currentStep = 3">返回状态</a-button>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <a-modal v-model:open="publishOpen" title="登记发布" ok-text="确认" @ok="submitPublish">
      <p class="text-sm text-gray-500 mb-3">登记后成品将在约 1 小时内自动删除，脚本仍保留。</p>
      <a-input v-model:value="publishUrl" placeholder="发布链接（可选）" />
    </a-modal>

    <a-modal
      v-model:open="trafficOpen"
      title="视频引流发布"
      ok-text="开始发布"
      :confirm-loading="trafficLoading"
      @ok="submitTrafficPublish"
    >
      <p class="text-sm text-gray-500 mb-3">
        将自动：登记租户官网视频页（SEO/GEO）+ 可选发布到视频网站（需已上云）。
      </p>
      <a-alert
        v-if="publishPreflight?.dual_line?.dual_line_ready"
        type="success"
        show-icon
        class="mb-3"
        message="Hermes 双线真发已就绪"
        :description="publishPreflightHint"
      />
      <a-alert
        v-else
        type="warning"
        show-icon
        class="mb-3"
        message="外站真发未就绪"
        :description="publishPreflight?.workers?.sau?.hint || publishPreflight?.reason || '请配置 SAU / biliup / 小红书 MCP 或 AITOEARN_API_KEY；未就绪时仅登记租户官网。'"
      />
      <a-alert
        v-if="browserCompanionHint?.items?.length"
        type="info"
        show-icon
        class="mb-3"
        :message="browserCompanionHint.title || '优丁专属浏览器伴侣'"
      >
        <template #description>
          <p class="text-xs mb-2">{{ browserCompanionHint.message }}</p>
          <p class="text-xs text-amber-700 mb-2">伴侣不能脱离优丁单独使用；须从本页进入「伴侣工作台」。</p>
          <a-button
            v-if="task?.id"
            size="small"
            type="primary"
            ghost
            class="mb-2"
            @click="openCompanionWorkbench('browser_companion_multipost')"
          >
            打开 MultiPost 伴侣工作台
          </a-button>
          <div>
            <router-link to="/client/plugin-market?category=浏览器伴侣" class="text-primary-600 text-xs">
              插件市场 · 首次安装扩展 →
            </router-link>
          </div>
        </template>
      </a-alert>
      <a-checkbox-group v-model:value="trafficPlatforms" class="flex flex-col gap-2">
        <a-checkbox
          v-for="p in trafficPlatformOptions"
          :key="p.value"
          :value="p.value"
          :disabled="!p.selectable"
        >
          <span>{{ p.label }}</span>
          <a-tag
            v-if="p.videoLabel"
            size="small"
            :color="p.selectable ? 'processing' : 'default'"
            class="ml-2"
          >
            {{ p.videoLabel }}
          </a-tag>
          <a-tag v-if="boundAccountIds.has(p.value)" size="small" color="success" class="ml-2">
            已绑定
          </a-tag>
          <a-tag v-else-if="p.selectable" size="small" color="warning" class="ml-2">未绑定</a-tag>
        </a-checkbox>
      </a-checkbox-group>
      <p v-if="unboundSelectedCount > 0" class="text-xs text-amber-600 mt-2">
        {{ unboundSelectedCount }} 个平台未绑定，发布时将跳过；请先
        <a class="text-primary-600" @click.prevent="goBindPlatforms">前往视频绑号入口</a>。
      </p>
      <p v-if="!trafficPlatformOptions.length" class="text-xs text-amber-600 mt-2">
        未配置平台；将仅发布到租户官网。
      </p>
      <ul v-if="trafficPublishSummary.length" class="mt-3 text-xs space-y-1 border-t pt-2">
        <li v-for="(r, i) in trafficPublishSummary" :key="i">
          <span :class="isVerifiedPublish(r) ? 'text-green-600' : 'text-red-500'">
            {{ r.platform_name || r.platform_id }} — {{ isVerifiedPublish(r) ? '验真成功' : (r.error_message || '失败') }}
          </span>
          <a
            v-if="isVerifiedPublish(r) && r.platform_post_url"
            :href="r.platform_post_url"
            target="_blank"
            rel="noopener"
            class="text-primary-600 ml-1"
          >后台核对链接</a>
          <span v-else-if="r.flow_id" class="text-gray-500 ml-1">flow: {{ r.flow_id }}</span>
          <span v-if="r.verify_hint && !r.success" class="text-amber-600 ml-1">{{ r.verify_hint }}</span>
          <span v-if="r.via" class="text-gray-400 ml-1">({{ r.via }})</span>
          <a-tag v-if="r.failover" size="small" color="orange" class="ml-1">备路救回</a-tag>
        </li>
      </ul>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const router = useRouter()
const currentStep = ref(0)
const generatingScript = ref(false)
const submitting = ref(false)
const polling = ref(false)
const mockRender = ref(false)
const script = ref('')
const task = ref<any>(null)
const handoffLoading = ref('')
const publishOpen = ref(false)
const publishUrl = ref('')
const trafficOpen = ref(false)
const trafficLoading = ref(false)
const trafficPlatforms = ref<string[]>([])
const trafficPlatformOptions = ref<
  {
    label: string
    value: string
    selectable: boolean
    videoLabel: string
    reason?: string
  }[]
>([])
const boundAccountIds = ref<Set<string>>(new Set())
const trafficPublishSummary = ref<
  {
    platform_id?: string
    platform_name?: string
    success?: boolean
    error_message?: string
    platform_post_url?: string
    flow_id?: string
    verify_hint?: string
    via?: string
    verified?: boolean
    failover?: boolean
  }[]
>([])

/** 成功 = 验真且带 http 作品链接 */
function isVerifiedPublish(r: {
  success?: boolean
  verified?: boolean
  platform_post_url?: string
}) {
  if (r.verified === false) return false
  if (!(r.platform_post_url || '').trim().startsWith('http')) return false
  return r.success === true || r.verified === true
}

const publishWorkerReady = ref(false)
const publishPreflight = ref<{
  ready?: boolean
  reason?: string
  dual_line?: {
    dual_line_ready?: boolean
    primary_line_ready?: boolean
    fallback_line_ready?: boolean
    warnings?: string[]
  }
  workers?: Record<string, { enabled?: boolean; ready?: boolean; account_count?: number; hint?: string }>
  browser_companion_hint?: {
    title?: string
    message?: string
    items?: {
      id?: string
      name?: string
      tagline?: string
      install?: { chrome?: string; edge?: string; website?: string; github?: string }
    }[]
  }
} | null>(null)

const browserCompanionHint = computed(() => publishPreflight.value?.browser_companion_hint)

const publishPreflightHint = computed(() => {
  const dl = publishPreflight.value?.dual_line
  if (dl?.dual_line_ready) {
    return '双线就绪：主路 SAU 自托管 + 备路 AiToEarn；主路失败自动切备路，成功须带作品链接。'
  }
  const w = publishPreflight.value?.workers || {}
  const parts: string[] = []
  if (w.sau?.enabled) parts.push('主路 SAU ✓')
  else parts.push('主路 SAU ✗')
  if (w.aitoearn?.ready) parts.push(`备路 AiToEarn ✓(${w.aitoearn.account_count || 0}号)`)
  else parts.push('备路 AiToEarn ✗')
  const warn = (dl?.warnings || [])[0]
  return `${parts.join(' · ')}。${warn || '建议双线同时配齐，避免主路故障时客户发不出去。'}`
})

const unboundSelectedCount = computed(() =>
  trafficPlatforms.value.filter(id => !boundAccountIds.value.has(id)).length,
)
const editShots = ref<any[]>([])
const editScript = ref('')
const clipRange = ref<[number, number]>([0, 0])
const videoDuration = ref(0)
const clipLoading = ref(false)
const saveScriptLoading = ref(false)
const rerenderLoading = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const editPreviewUrl = computed(() => task.value?.preview_url || task.value?.edited_result_url || task.value?.result_url || '')

const cloudTagColor = computed(() => {
  const s = task.value?.cloud_upload_status
  if (s === 'done') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'uploading') return 'processing'
  return 'default'
})

const retentionTitle = computed(() => {
  if (!task.value) return ''
  if (task.value.file_purged) return '成品已过期'
  if (task.value.handoff_type === 'published') return '已登记发布，即将删除成品'
  if (task.value.handoff_type === 'downloaded') return '已登记下载，即将删除成品'
  return `预览保留约 ${task.value.retention_hours || 72} 小时`
})

const countdownLabel = computed(() => {
  const sec = task.value?.seconds_until_purge
  if (sec == null || task.value?.file_purged) return ''
  if (sec <= 0) return '即将删除'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (h > 0) return `剩余约 ${h} 小时 ${m} 分钟`
  return `剩余约 ${m} 分钟`
})

const form = ref({
  title: '',
  article: '',
  resolution: '1080p',
  aspect: '16:9',
})

function authHeaders() {
  return { Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' }
}

async function loadOverview() {
  try {
    const res = await fetch('/api/v1/media-factory/', { headers: authHeaders() })
    const body = await res.json()
    mockRender.value = !!(body.data?.mock_render)
  } catch {
    mockRender.value = false
  }
}

loadOverview()

async function loadPublishPreflight() {
  try {
    const res = await fetch('/api/v1/publish/video/preflight', { headers: authHeaders() })
    const body = await res.json()
    publishPreflight.value = body.data || body
    publishWorkerReady.value = !!(body.data || body)?.ready
  } catch {
    publishPreflight.value = { ready: false, reason: '预检请求失败' }
    publishWorkerReady.value = false
  }
}

async function loadTrafficPlatforms() {
  try {
    const [tenantRes, capRes] = await Promise.all([
      fetch('/api/v1/tenants/current', { headers: authHeaders() }),
      fetch('/api/v1/publish/video/capabilities', { headers: authHeaders() }),
    ])
    const tenantBody = await tenantRes.json()
    const capBody = await capRes.json()
    const capData = capBody.data || capBody
    publishWorkerReady.value = !!capData.any_worker_ready
    const capList = (capData.platforms || []) as {
      platform_id: string
      platform_name: string
      selectable?: boolean
      label?: string
      reason?: string
    }[]
    const capById = new Map(capList.map(p => [String(p.platform_id), p]))
    const slots = (tenantBody.data || tenantBody)?.onboarding?.platforms || []
    const videoNames = new Set(capList.map(p => p.platform_name))
    trafficPlatformOptions.value = slots
      .filter((p: { platform_name?: string; content_type?: string; platform_id?: string }) =>
        videoNames.has(p.platform_name || '') ||
        capById.has(String(p.platform_id || '')) ||
        (p.content_type || '').includes('video'),
      )
      .filter((p: { platform_id?: string }) => !!p.platform_id)
      .map((p: { platform_id?: string; platform_name?: string }) => {
        const cap = capById.get(String(p.platform_id))
        const selectable = cap?.selectable === true
        return {
          label: p.platform_name || cap?.platform_name || '',
          value: p.platform_id as string,
          selectable,
          videoLabel: cap?.label || (selectable ? 'API 真发' : '未接入真发'),
          reason: cap?.reason,
        }
      })
    trafficPlatforms.value = trafficPlatformOptions.value
      .filter(p => p.selectable)
      .map(p => p.value)
  } catch {
    trafficPlatformOptions.value = []
    trafficPlatforms.value = []
    publishWorkerReady.value = false
  }
}

async function loadBoundAccounts() {
  try {
    const res = await fetch('/api/v1/seo-matrix/accounts', { headers: authHeaders() })
    const body = await res.json()
    const list = (body.data || []) as { platform?: string; status?: string; login_status?: string }[]
    boundAccountIds.value = new Set(
      list
        .filter(a => a.login_status === 'logged_in')
        .map(a => String(a.platform || ''))
        .filter(Boolean),
    )
  } catch {
    boundAccountIds.value = new Set()
  }
}

function goBindPlatforms() {
  trafficOpen.value = false
  router.push({ path: '/client/distribute', query: { focus: 'bind' } })
}

const COMPANION_LAUNCH_KEY = 'youding_companion_launch'

function openCompanionWorkbench(companionId: string) {
  if (!task.value?.id) {
    message.warning('请先完成视频渲染')
    return
  }
  sessionStorage.setItem(
    COMPANION_LAUNCH_KEY,
    JSON.stringify({ ts: Date.now(), media_task_id: task.value.id, companion: companionId }),
  )
  trafficOpen.value = false
  router.push({
    path: '/admin/ai-center/browser-companion',
    query: {
      from: 'youding',
      companion: companionId,
      media_task_id: task.value.id,
    },
  })
}

onMounted(() => {
  loadTrafficPlatforms()
  loadBoundAccounts()
})

function hydrateFromArticleGenerator() {
  const raw = sessionStorage.getItem('article_to_video_payload')
  if (!raw) return
  try {
    const payload = JSON.parse(raw)
    if (payload.article) form.value.article = payload.article
    if (payload.title) form.value.title = payload.title
    sessionStorage.removeItem('article_to_video_payload')
  } catch {
    /* ignore */
  }
}

hydrateFromArticleGenerator()

function statusColor(raw: string) {
  if (raw === 'done') return 'success'
  if (raw === 'rendering') return 'processing'
  if (raw === 'failed') return 'error'
  if (raw === 'queued') return 'warning'
  return 'default'
}

async function generateScript() {
  const article = form.value.article.trim()
  if (!article) {
    message.warning('请先输入文章内容')
    return
  }
  generatingScript.value = true
  try {
    const res = await fetch('/api/v1/media-factory/ai-write', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        prompt: article,
        contentType: 'video-script',
        scenario: 'article_to_video_script',
      }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '脚本生成失败')
    const data = body.data || body
    script.value = (data.content || data.text || '').trim()
    if (!script.value) throw new Error('模型未返回脚本')
    currentStep.value = 1
    message.success('脚本已生成')
  } catch (err: any) {
    message.error(err.message || '脚本生成失败')
  } finally {
    generatingScript.value = false
  }
}

async function submitRender() {
  if (!script.value.trim()) {
    message.warning('脚本不能为空')
    return
  }
  submitting.value = true
  try {
    const res = await fetch('/api/v1/media-factory/generate', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        script: script.value,
        title: form.value.title || undefined,
        resolution: form.value.resolution,
        aspect: form.value.aspect,
        auto_render: true,
      }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '入队失败')
    task.value = body.data || body
    currentStep.value = 3
    startPolling()
    message.success('已加入渲染队列')
  } catch (err: any) {
    message.error(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function pollTask() {
  if (!task.value?.id) return
  polling.value = true
  try {
    const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}`, { headers: authHeaders() })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '查询失败')
    task.value = body.data || body
    if (['done', 'failed'].includes(task.value.raw_status)) stopPolling()
    if (task.value.raw_status === 'done') syncEditFromTask()
  } catch (err: any) {
    message.error(err.message || '刷新失败')
  } finally {
    polling.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollTask, 2500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function loadEditState() {
  if (!task.value?.id) return
  const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}/edit`, { headers: authHeaders() })
  const body = await res.json()
  if (body.code && body.code !== 0) throw new Error(body.message || '加载剪辑数据失败')
  const data = body.data || body
  editScript.value = data.script || task.value.script || ''
  editShots.value = (data.shots || []).map((s: any) => ({ ...s }))
  const dur = Number(data.source_duration_sec || 0)
  if (dur > 0) {
    videoDuration.value = dur
    clipRange.value = [
      Number(data.clip_start_sec || 0),
      Number(data.clip_end_sec || dur),
    ]
  }
  if (data.task) task.value = { ...task.value, ...data.task }
}

function syncEditFromTask() {
  editScript.value = task.value?.script || script.value || ''
  const cfg = task.value?.edit_config || {}
  const dur = Number(cfg.source_duration_sec || 0)
  if (dur > 0) {
    videoDuration.value = dur
    clipRange.value = [Number(cfg.clip_start_sec || 0), Number(cfg.clip_end_sec || dur)]
  }
}

async function openEditor() {
  try {
    await loadEditState()
    currentStep.value = 4
  } catch (err: any) {
    message.error(err.message || '无法打开剪辑器')
  }
}

function onVideoMeta() {
  const el = videoRef.value
  if (!el || !Number.isFinite(el.duration)) return
  if (videoDuration.value <= 0) {
    videoDuration.value = el.duration
    clipRange.value = [0, el.duration]
  }
}

async function applyClip() {
  if (!task.value?.id) return
  clipLoading.value = true
  try {
    const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}/clip`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ start_sec: clipRange.value[0], end_sec: clipRange.value[1] }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '剪辑失败')
    task.value = body.data || body
    message.success('剪辑版已生成，预览已切换')
  } catch (err: any) {
    message.error(err.message || '剪辑失败')
  } finally {
    clipLoading.value = false
  }
}

async function saveScript() {
  if (!task.value?.id) return
  saveScriptLoading.value = true
  try {
    const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}/script`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ script: editScript.value, shots: editShots.value }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '保存失败')
    task.value = body.data || body
    editScript.value = task.value.script || editScript.value
    script.value = editScript.value
    message.success('脚本已保存')
  } catch (err: any) {
    message.error(err.message || '保存失败')
  } finally {
    saveScriptLoading.value = false
  }
}

async function rerenderVideo() {
  if (!task.value?.id) return
  rerenderLoading.value = true
  try {
    await saveScript()
    const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}/re-render`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ shots: editShots.value, auto_render: true }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '重渲失败')
    task.value = body.data || body
    currentStep.value = 3
    startPolling()
    message.success('已按新脚本重新渲染')
  } catch (err: any) {
    message.error(err.message || '重渲失败')
  } finally {
    rerenderLoading.value = false
  }
}

function resetFlow() {
  stopPolling()
  currentStep.value = 0
  script.value = ''
  task.value = null
  publishUrl.value = ''
  editShots.value = []
  editScript.value = ''
  clipRange.value = [0, 0]
  videoDuration.value = 0
}

async function confirmHandoff(action: 'downloaded' | 'published', externalUrl?: string) {
  if (!task.value?.id) return
  handoffLoading.value = action
  try {
    const res = await fetch(`/api/v1/media-factory/tasks/${task.value.id}/handoff`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ action, external_url: externalUrl || undefined }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '登记失败')
    task.value = body.data || body
    message.success(action === 'published' ? '已登记发布' : '已登记下载')
  } catch (err: any) {
    message.error(err.message || '登记失败')
  } finally {
    handoffLoading.value = ''
  }
}

function openPublishModal() {
  publishUrl.value = ''
  publishOpen.value = true
}

async function submitPublish() {
  publishOpen.value = false
  await confirmHandoff('published', publishUrl.value.trim() || undefined)
}

function openTrafficModal() {
  trafficPublishSummary.value = []
  loadTrafficPlatforms()
  loadBoundAccounts()
  loadPublishPreflight()
  trafficOpen.value = true
}

async function submitTrafficPublish() {
  if (!task.value?.id) return
  const selectableIds = new Set(trafficPlatformOptions.value.filter(p => p.selectable).map(p => p.value))
  const boundIds = trafficPlatforms.value.filter(id => {
    const opt = trafficPlatformOptions.value.find(p => p.value === id)
    if (!opt?.selectable) return false
    if (publishWorkerReady.value && opt.selectable && (opt.videoLabel || '').includes('真发')) return true
    return boundAccountIds.value.has(id)
  })
  const skippedUnbound = trafficPlatforms.value.filter(
    id => selectableIds.has(id) && !boundAccountIds.value.has(id),
  )
  const blockedSelected = trafficPlatforms.value.filter(id => !selectableIds.has(id))
  if (blockedSelected.length) {
    message.warning('已忽略未接入真发的平台（抖音/快手等），避免客户后台查无此文')
  }
  if (skippedUnbound.length) {
    const names = trafficPlatformOptions.value
      .filter(p => skippedUnbound.includes(p.value))
      .map(p => p.label)
      .join('、')
    message.warning(names ? `已跳过未绑定平台：${names}` : '部分平台未绑定，已跳过')
  }
  trafficLoading.value = true
  try {
    const res = await fetch('/api/v1/publish/video/distribute', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        media_task_id: task.value.id,
        platform_ids: boundIds,
        include_tenant_site: true,
      }),
    })
    const body = await res.json()
    if (body.code && body.code !== 0) throw new Error(body.message || '发布失败')
    const data = body.data || body
    if (data.tenant_landing_url) {
      task.value = { ...task.value, tenant_landing_url: data.tenant_landing_url }
    }
    trafficPublishSummary.value = Array.isArray(data.results) ? data.results : []
    const siteOk = data.tenant_site?.published
    const okN = trafficPublishSummary.value.filter(r => isVerifiedPublish(r)).length
    const failN = trafficPublishSummary.value.filter(r => !isVerifiedPublish(r)).length
    if (siteOk && okN === 0 && failN === 0) {
      message.success('已登记租户官网落地页')
    } else if (okN > 0) {
      message.success(`官网已发布；${okN} 个平台成功${failN ? `，${failN} 个失败` : ''}`)
    } else if (failN > 0) {
      message.warning(`官网已处理；${failN} 个平台发布失败，见下方明细`)
    } else if (siteOk) {
      message.success('已登记租户官网落地页（未选择外站或外站未返回链接）')
    } else {
      message.warning('引流发布未完成：请检查租户配置或平台绑定')
    }
    await pollTask()
  } catch (err: any) {
    message.error(err.message || '引流发布失败')
  } finally {
    trafficLoading.value = false
  }
}

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.article-to-video-page {
  padding: 4px 0;
}
</style>
