<template>
  <YdPage title="视频管理中心" subtitle="AI 视频生成工厂 · 管理所有生成的视频与音频文件" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="showGen = true" type="primary" size="large">+ 一键生成视频</a-button>
        <a-button @click="showUpload = true" size="large">⬆ 上传视频</a-button>
      </a-space>
    </template>
  <div class="space-y-6">
    <!-- Stats -->
    <div class="grid grid-cols-5 gap-4">
      <a-card size="small"><a-statistic title="已生成视频" :value="stats.total" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
      <a-card size="small"><a-statistic title="渲染中" :value="stats.rendering" :value-style="{ color: '#f59e0b' }"/></a-card>
      <a-card size="small"><a-statistic title="总时长" :value="stats.duration" suffix="分钟"/></a-card>
      <a-card size="small"><a-statistic title="今日生成" :value="stats.today" :value-style="{ color: '#22c55e' }"/></a-card>
      <a-card size="small"><a-statistic title="存储" :value="stats.storage" suffix="GB"/></a-card>
    </div>

    <a-alert
      v-if="isPlatformAdmin && !tenantScopeFilter"
      type="warning"
      show-icon
      message="平台超管：上传或筛选前请先选择「租户分组」，否则媒体会写入 platform 公共目录"
    />

    <!-- Filter Tabs -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div class="flex items-center gap-2 flex-wrap">
        <a-button
          :type="mediaFilter === 'all' ? 'primary' : 'default'"
          size="small"
          @click="mediaFilter = 'all'"
        >全部 ({{ filteredList.length }})</a-button>
        <a-button
          :type="mediaFilter === 'video' ? 'primary' : 'default'"
          size="small"
          @click="mediaFilter = 'video'"
        >视频</a-button>
        <a-button
          :type="mediaFilter === 'audio' ? 'primary' : 'default'"
          size="small"
          @click="mediaFilter = 'audio'"
        >音频</a-button>
        <a-select
          v-if="isPlatformAdmin"
          v-model:value="tenantScopeFilter"
          style="width: 220px"
          placeholder="租户分组"
          allow-clear
          show-search
          option-filter-prop="label"
          size="small"
          @change="handleTenantScopeFilter"
        >
          <a-select-option
            v-for="opt in tenantScopeOptions"
            :key="opt.tenant_id"
            :value="opt.tenant_id"
            :label="tenantScopeLabel(opt.tenant_id)"
          >
            {{ tenantScopeLabel(opt.tenant_id) }}（{{ opt.file_count }}）
          </a-select-option>
        </a-select>
      </div>
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索视频名称..."
        style="width: 240px"
        size="small"
        allow-clear
      />
    </div>

    <!-- Video Grid -->
    <div v-if="filteredList.length === 0" class="text-center py-16 text-gray-400">
      <YdIllustration icon="VideoCameraOutlined" size="lg" class="mb-4" />
      <p class="text-lg">暂无{{ mediaFilter === 'audio' ? '音频' : '视频' }}文件</p>
      <p class="text-sm mt-1">点击「上传视频」或「一键生成视频」开始创建</p>
    </div>

    <a-row :gutter="[16, 16]" v-else>
      <a-col v-for="item in filteredList" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
        <a-card
          class="media-card"
          hoverable
          size="small"
          @click="openPlayer(item)"
        >
          <!-- Thumbnail -->
          <div class="media-thumbnail">
            <div class="thumbnail-placeholder" :class="item.type">
              <PlayCircleOutlined v-if="item.type === 'video'" class="thumbnail-icon" />
              <SoundOutlined v-else class="thumbnail-icon" />
              <span class="duration-badge">{{ item.durationLabel }}</span>
            </div>
          </div>
          <!-- Info -->
          <div class="media-info">
            <div class="media-title" :title="item.title">{{ item.title }}</div>
            <div class="media-meta">
              <span>{{ item.type === 'video' ? '视频' : '音频' }}</span>
              <span>·</span>
              <span>{{ item.createdAt }}</span>
              <a-tag v-if="item.cloud_upload_status" size="small" class="ml-1">
                {{ cloudLabel(item.cloud_upload_status) }}
              </a-tag>
              <a-tag v-if="isPlatformAdmin && item.tenant_id" size="small" class="ml-1">
                {{ tenantScopeLabel(item.tenant_id) }}
              </a-tag>
            </div>
            <a
              v-if="item.tenant_landing_url"
              :href="item.tenant_landing_url"
              target="_blank"
              rel="noopener"
              class="text-xs text-primary-600 hover:underline mt-1 inline-block"
              @click.stop
            >
              官网落地页 →
            </a>
          </div>
          <!-- Actions -->
          <template #actions>
            <PlayCircleOutlined @click.stop="openPlayer(item)" />
            <DownloadOutlined @click.stop="handleDownload(item)" />
            <DeleteOutlined @click.stop="handleDelete(item)" />
          </template>
        </a-card>
      </a-col>
    </a-row>

    <!-- Video Player Modal -->
    <VideoPlayer
      v-model:open="showPlayer"
      :src="currentVideoSrc"
      :title="currentVideoTitle"
    />

    <!-- Upload Modal -->
    <a-modal
      v-model:open="showUpload"
      title="上传视频文件"
      :footer="null"
      width="500px"
      destroy-on-close
    >
      <a-upload-dragger
        :before-upload="handleBeforeUpload"
        :show-upload-list="true"
        accept="video/*,audio/*"
        :multiple="false"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">支持 MP4, AVI, MOV, WebM 等视频格式及 MP3, WAV 等音频格式，单文件最大 500MB</p>
      </a-upload-dragger>
    </a-modal>

    <!-- MoneyPrinter Style Creation Modal (kept from original) -->
    <a-modal v-model:open="showGen" title="一键生成视频 · MoneyPrinter 模式" width="720px" @ok="createTask" okText="开始生成">
      <a-steps :current="step" size="small" class="mb-4">
        <a-step title="输入文案"/><a-step title="配音设置"/><a-step title="素材配置"/><a-step title="生成预览"/>
      </a-steps>

      <!-- Step 1: 文案 -->
      <div v-if="step===0">
        <a-form-item label="视频文案 (核心)" required><a-textarea v-model:value="gen.script" :rows="8" placeholder="输入你的视频文案，AI 将自动拆分为场景并匹配画面...
示例：轻集料混凝土是一种新型环保建材，具有轻质高强的特点。广泛用于高层建筑、桥梁隧道等工程。今天我们来了解它的生产工艺和应用场景..."/></a-form-item>
        <a-form-item label="文案来源"><a-radio-group v-model:value="gen.source"><a-radio value="manual">手动输入</a-radio><a-radio value="url">文章链接</a-radio><a-radio value="ai">AI 帮写</a-radio></a-radio-group></a-form-item>
        <div v-if="gen.source==='ai'" class="mb-3"><a-input v-model:value="gen.aiPrompt" placeholder="告诉AI你要写什么..."/><a-button class="mt-2" @click="aiWrite" :loading="aiWriting">AI 生成文案</a-button></div>
      </div>

      <!-- Step 2: 配音 -->
      <div v-if="step===1">
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="配音员"><a-select v-model:value="gen.voice"><a-select-option value="male-1">男声-沉稳</a-select-option><a-select-option value="male-2">男声-激情</a-select-option><a-select-option value="female-1">女声-温柔</a-select-option><a-select-option value="female-2">女声-活泼</a-select-option><a-select-option value="child">童声-可爱</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="语速"><a-slider v-model:value="gen.speed" :min="50" :max="150"/></a-form-item></a-col>
        </a-row>
        <a-form-item label="背景音乐"><a-select v-model:value="gen.bgm"><a-select-option value="none">无</a-select-option><a-select-option value="corporate">企业宣传</a-select-option><a-select-option value="tech">科技感</a-select-option><a-select-option value="relax">轻松愉悦</a-select-option><a-select-option value="epic">大气磅礴</a-select-option></a-select></a-form-item>
      </div>

      <!-- Step 3: 素材 -->
      <div v-if="step===2">
        <a-form-item label="画面素材"><a-radio-group v-model:value="gen.material"><a-radio value="search">自动搜索匹配</a-radio><a-radio value="local">本地上传</a-radio><a-radio value="ai">AI生成画面</a-radio></a-radio-group></a-form-item>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="分辨率"><a-select v-model:value="gen.resolution"><a-select-option value="1080p">1080p</a-select-option><a-select-option value="720p">720p</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="视频比例"><a-select v-model:value="gen.aspect"><a-select-option value="16:9">16:9 横屏</a-select-option><a-select-option value="9:16">9:16 竖屏(抖音)</a-select-option><a-select-option value="1:1">1:1 方形</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="字幕"><a-switch v-model:checked="gen.subtitle"/> 自动生成字幕</a-form-item></a-col>
        </a-row>
      </div>

      <!-- Step 4: Preview -->
      <div v-if="step===3" class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
        <div>文案: {{ gen.script.slice(0, 100) }}...</div>
        <div>配音: {{ { 'male-1':'男声-沉稳','male-2':'男声-激情','female-1':'女声-温柔','female-2':'女声-活泼','child':'童声-可爱' }[gen.voice] }}</div>
        <div>分辨率: {{ gen.resolution }} · {{ gen.aspect }}</div>
        <div>BGM: {{ gen.bgm==='none'?'无':gen.bgm }}</div>
        <div>预估大小: ~12MB · 预估时间: 3分钟</div>
      </div>

      <div class="flex justify-between mt-4"><a-button v-if="step>0" @click="step--">上一步</a-button><span v-else></span><a-button type="primary" v-if="step<3" @click="step++">下一步</a-button></div>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdIllustration, YdPage } from '@/components/youding';
import { PlayCircleOutlined, SoundOutlined, DownloadOutlined, DeleteOutlined, InboxOutlined } from '@ant-design/icons-vue';
import { apiGet, apiPost, getAuthToken } from '@/utils/api';
import { useAuthStore } from '@/stores/auth';
import VideoPlayer from '@/components/media/VideoPlayer.vue'

const authStore = useAuthStore();
const isPlatformAdmin = computed(() =>
  ['admin', 'super_admin'].includes(authStore.currentRole || ''),
);

interface TenantScopeOption {
  tenant_id: string;
  file_count: number;
}

const tenantScopeFilter = ref<string | undefined>(undefined);
const tenantScopeOptions = ref<TenantScopeOption[]>([]);
const tenantNameMap = ref<Record<string, string>>({});

function tenantScopeLabel(tenantId?: string): string {
  if (!tenantId) return '未分组';
  if (tenantId === 'platform') return '平台公共';
  const name = tenantNameMap.value[tenantId];
  if (name) return name;
  return tenantId.length > 12 ? `${tenantId.slice(0, 8)}…` : tenantId;
}

async function loadTenantNameMap() {
  if (!isPlatformAdmin.value) return;
  try {
    const res = await apiGet<{ recent_tenants?: { id: string; name: string }[] }>('/tenants', {
      page: 1,
      page_size: 200,
    });
    const rows = res?.recent_tenants ?? (res as { items?: { id: string; name: string }[] })?.items ?? [];
    const map: Record<string, string> = { platform: '平台公共' };
    for (const row of rows) {
      if (row?.id) map[row.id] = row.name || row.id;
    }
    tenantNameMap.value = map;
  } catch {
    tenantNameMap.value = { platform: '平台公共' };
  }
}

function listParams(): Record<string, string> {
  const params: Record<string, string> = {};
  if (isPlatformAdmin.value && tenantScopeFilter.value) {
    params.tenant_id = tenantScopeFilter.value;
  }
  return params;
}

// ── Stats ──
const stats = reactive({ total: 0, rendering: 0, duration: '0', today: 0, storage: '0' })

// ── Media Data ──
interface MediaItem {
  id: string
  title: string
  type: 'video' | 'audio'
  src: string
  durationLabel: string
  durationSeconds: number
  createdAt: string
  size: string
  tenant_id?: string
  raw_status?: string
  cloud_upload_status?: string
  tenant_landing_url?: string
}

const mediaList = ref<MediaItem[]>([])

async function fetchDashboard() {
  try {
    const params = listParams();
    const qs = new URLSearchParams(params).toString();
    const statsPath = qs ? `/media-factory/?${qs}` : '/media-factory/';
    const listPath = qs ? `/media-factory/videos?${qs}` : '/media-factory/videos';
    const [statsRes, listRes] = await Promise.all([
      apiGet<{ data?: Record<string, unknown> } & Record<string, unknown>>(statsPath).catch(() => null),
      apiGet<{ data?: MediaItem[] } & MediaItem[]>(listPath).catch(() => null),
    ]);
    const statsData = (statsRes as { data?: Record<string, unknown> })?.data ?? statsRes;
    const listData = (listRes as { data?: MediaItem[] })?.data ?? listRes;
    if (statsData && typeof statsData === 'object') {
      stats.total = Number(statsData.rendered_videos ?? statsData.total ?? 0)
      stats.rendering = Number(statsData.queued_videos ?? statsData.rendering ?? 0)
      stats.today = Number(statsData.today ?? 0)
      stats.duration = String(statsData.duration ?? '0')
      stats.storage = String(statsData.storage ?? '0')
      if (Array.isArray((statsData as { tenant_scopes?: TenantScopeOption[] }).tenant_scopes)) {
        tenantScopeOptions.value = (statsData as { tenant_scopes: TenantScopeOption[] }).tenant_scopes;
      }
    }
    if (Array.isArray(listData)) mediaList.value = listData
  } catch { /* API not available, show empty state */ }
}

function handleTenantScopeFilter() {
  fetchDashboard();
}

onMounted(() => {
  loadTenantNameMap();
  fetchDashboard();
});

// ── Filter & Search ──
const mediaFilter = ref<'all' | 'video' | 'audio'>('all')
const searchText = ref('')

const filteredList = computed(() => {
  let list = mediaList.value
  if (mediaFilter.value !== 'all') {
    list = list.filter(item => item.type === mediaFilter.value)
  }
  if (searchText.value.trim()) {
    const q = searchText.value.trim().toLowerCase()
    list = list.filter(item => item.title.toLowerCase().includes(q))
  }
  return list
})

// ── Player ──
const showPlayer = ref(false)
const currentVideoSrc = ref('')
const currentVideoTitle = ref('')

function openPlayer(item: MediaItem) {
  currentVideoSrc.value = item.src
  currentVideoTitle.value = item.title
  showPlayer.value = true
}

// ── Upload ──
const showUpload = ref(false)

function handleBeforeUpload(file: File): boolean {
  const maxSize = 500 * 1024 * 1024 // 500MB
  if (file.size > maxSize) {
    message.error('文件大小超过 500MB 限制')
    return false
  }
  const isVideo = file.type.startsWith('video/')
  const isAudio = file.type.startsWith('audio/')
  if (!isVideo && !isAudio) {
    message.error('仅支持视频和音频文件')
    return false
  }
  // Upload to API
  const formData = new FormData()
  formData.append('file', file)
  if (isPlatformAdmin.value && tenantScopeFilter.value) {
    formData.append('tenant_id', tenantScopeFilter.value)
  }
  fetch('/api/v1/media-factory/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${getAuthToken()}` },
    body: formData,
  }).then(async res => {
    if (res.ok) {
      const body = await res.json()
      const item = body.data || body
      if (item.id) {
        mediaList.value.unshift(item)
      }
      message.success(`"${file.name}" 上传成功`)
    } else {
      throw new Error('Upload failed')
    }
  }).catch(() => {
    message.error(`"${file.name}" 上传失败`)
  })
  showUpload.value = false
  return false
}

// ── Actions ──
function cloudLabel(status: string) {
  const map: Record<string, string> = {
    done: '已上云',
    partial: '部分上云',
    skipped: '本地预览',
    pending: '待上云',
    failed: '上云失败',
  }
  return map[status] || status
}

function handleDownload(item: MediaItem) {
  if (!item.src) {
    message.warning('暂无可下载文件')
    return
  }
  const a = document.createElement('a')
  a.href = item.src
  a.download = item.title || 'video'
  a.rel = 'noopener'
  a.click()
}

async function handleDelete(item: MediaItem) {
  try {
    await fetch(`/api/v1/media-factory/render-queue/${item.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    mediaList.value = mediaList.value.filter(t => t.id !== item.id)
    message.success(`已删除: ${item.title}`)
  } catch {
    message.error('删除失败')
  }
}

// ── AI Generation (kept from original) ──
const showGen = ref(false)
const step = ref(0)
const aiWriting = ref(false)
const gen = reactive({
  script: '',
  source: 'manual',
  aiPrompt: '',
  voice: 'male-1',
  speed: 100,
  bgm: 'none',
  material: 'search',
  resolution: '1080p',
  aspect: '16:9',
  subtitle: true,
})

async function aiWrite() {
  if (!gen.aiPrompt.trim()) { message.warning('请输入AI写作提示'); return }
  aiWriting.value = true
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 12000)
  const hideLoading = message.loading('正在生成文案，通常 5–8 秒…', 0)
  try {
    const data = await apiPost<{ content?: string; text?: string; mock?: boolean }>(
      '/media-factory/ai-write',
      {
        prompt: gen.aiPrompt,
        contentType: 'video-script',
        scenario: 'article_to_video_script',
      },
      controller.signal,
    )
    gen.script = (data.content || data.text || '').trim()
    if (!gen.script) throw new Error('模型未返回文案')
    message.success(data.mock ? '文案已生成（网络较慢，已用模板，可编辑）' : '文案已生成')
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      message.error('生成超时，请重试或改用手动输入')
    } else {
      const msg = err instanceof Error ? err.message : ''
      message.error(msg.includes('503') ? 'AI 服务暂不可用，请检查模型配置' : 'AI 写作失败，请稍后重试')
    }
  } finally {
    hideLoading()
    window.clearTimeout(timer)
    aiWriting.value = false
  }
}

async function createTask() {
  if (!gen.script) {
    message.warning('请输入视频文案')
    return
  }
  try {
    const item = await apiPost<MediaItem & { id?: string }>('/media-factory/generate', {
      script: gen.script,
      voice: gen.voice,
      speed: gen.speed,
      bgm: gen.bgm,
      material: gen.material,
      resolution: gen.resolution,
      aspect: gen.aspect,
      subtitle: gen.subtitle,
      auto_render: true,
    })
    message.success('任务已加入渲染队列')
    showGen.value = false
    step.value = 0
    gen.script = ''
    await fetchDashboard()
    if (item?.id) {
      const mapped: MediaItem = {
        id: String(item.id),
        title: (item as { title?: string }).title || '新视频',
        type: 'video',
        src: (item as { preview_url?: string }).preview_url || '',
        durationLabel: '—',
        durationSeconds: 0,
        createdAt: new Date().toISOString().slice(0, 10),
        size: '',
      }
      if (!mediaList.value.some(v => v.id === mapped.id)) {
        mediaList.value.unshift(mapped)
      }
    }
  } catch {
    message.error('创建任务失败')
  }
}
</script>

<style scoped>
.media-card {
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.media-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
.media-card :deep(.ant-card-body) {
  padding: 0;
}

.media-thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  font-size: 14px;
}

.thumbnail-placeholder.video {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
}

.thumbnail-placeholder.audio {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
}

.thumbnail-icon {
  font-size: 40px;
  color: rgba(255, 255, 255, 0.25);
}

.duration-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0, 0, 0, 0.65);
  color: #e5e7eb;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  font-variant-numeric: tabular-nums;
  line-height: 1.5;
}

.media-info {
  padding: 10px 12px;
}

.media-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.media-meta {
  font-size: 12px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 4px;
}

.media-card :deep(.ant-card-actions) {
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
}

.media-card :deep(.ant-card-actions > li) {
  margin: 6px 0;
}

.media-card :deep(.ant-card-actions > li > span:hover) {
  color: var(--uj-brand, #4a9b8c);
}
</style>
