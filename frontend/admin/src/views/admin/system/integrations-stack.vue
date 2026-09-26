/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 集成栈状态 — 每行带好坏说明（level + label + hint）
 */
<template>
 <YdPage title="集成栈状态" subtitle="FastAPI 主栈与可选 Node seo-backend 健康一览" surface="elevated">
 <template #actions>
 <a-button type="primary" :loading="loading" @click="load">刷新</a-button>
</template>
 <template v-if="loading">
 <SkeletonCard variant="card" />
</template>
 <template v-else>
 <a-alert
 v-if="overall"
 :type="alertType(overall.level)"
 show-icon
 class="mb-4"
 :message="`综合判定：${overall.label}`"
 :description="overall.hint"
 />

 <a-card v-if="status" size="small" title="主栈与 SEO 集成">
 <div class="check-rows">
 <div class="check-row">
 <div class="check-label">主栈</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <span class="font-mono">{{ status.primary }}</span>
 <LevelTag :check="checks.primary" />
</div>
 <div class="check-hint">{{ checks.primary?.hint }}</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">SEO 矩阵路由数</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <span class="font-mono text-base">{{ status.fastapi_routes?.seo_matrix ?? '—' }}</span>
 <LevelTag :check="checks.seo_matrix_routes" />
</div>
 <div class="check-hint">{{ checks.seo_matrix_routes?.hint }}</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">高级 SEO 路由数</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <span class="font-mono text-base">{{ status.fastapi_routes?.seo_advanced ?? '—' }}</span>
 <LevelTag :check="checks.seo_advanced_routes" />
</div>
 <div class="check-hint">{{ checks.seo_advanced_routes?.hint }}</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">API 路由总数（/api）</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <span class="font-mono">{{ status.fastapi_routes?.total_api ?? '—' }}</span>
 <a-tag v-if="(status.fastapi_routes?.total_api || 0) > 0" color="success">有响应</a-tag>
 <a-tag v-else color="error">异常</a-tag>
</div>
 <div class="check-hint">总路由数仅作规模参考；是否“好”以各业务前缀是否挂载为准。</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">seo-backend URL</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <span class="font-mono">{{ status.seo_backend?.url }}</span>
</div>
 <div class="check-hint">
 Node 旁路地址。本机 SEO 服务常见为 <code>http://localhost:3001</code>；
 <code>:3000</code> 多为官网 Vite，易混淆。
</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">seo-backend 状态</div>
 <div class="check-value">
 <div class="flex flex-wrap items-center gap-2">
 <a-tag :color="nodeColor">{{ nodeLabel }}</a-tag>
 <LevelTag :check="checks.seo_backend" />
 <span v-if="status.seo_backend?.detail" class="text-gray-500 text-xs">
 {{ status.seo_backend.detail }}
</span>
</div>
 <div class="check-hint">{{ checks.seo_backend?.hint }}</div>
</div>
</div>

 <div class="check-row">
 <div class="check-label">代理路径</div>
 <div class="check-value">
 <span class="font-mono">{{ status.seo_backend?.proxy_path }}</span>
 <div class="check-hint">
 FastAPI 将该前缀请求转发到 seo-backend；未启用 Node 时此路径会 502/失败，属预期。
</div>
</div>
</div>
</div>
</a-card>

 <a-card v-if="status?.acquisition_panel" class="mt-4" size="small">
 <template #title>
 <div class="flex items-center justify-between">
 <span>{{ status.acquisition_panel.name }}</span>
 <div class="flex items-center gap-2">
 <a-tag :color="acquisitionStatusColor">
 {{ status.acquisition_panel.status_label }}
 （{{ status.acquisition_panel.configured }}/{{ status.acquisition_panel.total }}）
</a-tag>
 <a-tag :color="levelTagColor(status.acquisition_panel.status_level)">
 {{ levelTagText(status.acquisition_panel.status_level) }}
</a-tag>
</div>
</div>
</template>
 <a-alert type="info" show-icon class="mb-3" :message="status.acquisition_panel.overall_hint" />
 <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
 <div
 v-for="m in status.acquisition_panel.modules"
 :key="m.id"
 class="p-3 rounded-lg border bg-white hover:shadow-sm transition-shadow"
 :class="m.status === 'configured' ? 'border-green-200 bg-green-50/30' : 'border-amber-200 bg-amber-50/30'"
 >
 <div class="flex items-center justify-between gap-2 mb-2">
 <span class="font-medium text-sm text-slate-800">{{ m.name }}</span>
 <a-tag
 size="small"
 :color="m.status === 'configured' ? 'success' : 'warning'"
 >
 {{ m.status === 'configured' ? '已配置（好）' : '待配置（未就绪）' }}
</a-tag>
</div>
 <p class="text-xs text-slate-500 mb-2">{{ m.hint }}</p>
 <div class="text-xs text-slate-400 mb-2">
 <span class="font-mono bg-slate-100 px-1.5 py-0.5 rounded">{{ m.env_key }}</span>
</div>
 <div class="flex items-center justify-between">
 <span class="text-xs text-slate-400">{{ m.category }}</span>
 <a
 :href="m.doc_link"
 target="_blank"
 class="text-xs text-teal-600 hover:text-teal-700"
 >
 获取 Key →
</a>
</div>
</div>
</div>
 <ul v-if="status.acquisition_panel.usage_tips?.length" class="list-disc pl-5 text-xs text-slate-500 mt-4 mb-0 space-y-1">
 <li v-for="(tip, i) in status.acquisition_panel.usage_tips" :key="i">{{ tip }}</li>
</ul>
</a-card>

 <a-card v-if="crawlPanel" title="数据采集旁路" class="mt-4" size="small">
 <a-alert type="info" show-icon class="mb-3" :message="crawlPanel.overall_hint" />
 <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
 <div
 v-for="m in crawlPanel.modules || []"
 :key="m.id"
 class="p-3 rounded-lg border border-gray-100 bg-gray-50"
 >
 <div class="flex items-center justify-between gap-2">
 <span class="font-medium text-sm">{{ m.name }}</span>
 <a-tag size="small">{{ m.status }}</a-tag>
</div>
 <p class="text-xs text-gray-500 mt-2">{{ m.hint }}</p>
</div>
</div>
 <ul v-if="crawlPanel.usage_tips?.length" class="list-disc pl-5 text-xs text-gray-500 mt-3 mb-0">
 <li v-for="(tip, i) in crawlPanel.usage_tips" :key="i">{{ tip }}</li>
</ul>
</a-card>

 <a-card v-if="status?.guidance?.length" title="集成指引与图例" class="mt-4" size="small">
 <ul class="list-disc pl-5 text-sm text-gray-600">
 <li v-for="(g, i) in status.guidance" :key="i">{{ g }}</li>
</ul>
</a-card>
</template>
</YdPage>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const status = ref<any>(null)
const crawlPanel = ref<any>(null)

const LEVEL_COLOR: Record<string, string> = {
 ok: 'success',
 warn: 'warning',
 bad: 'error',
 info: 'default',
 skip: 'default',
}
const LEVEL_TEXT: Record<string, string> = {
 ok: '正常',
 warn: '需关注',
 bad: '异常',
 info: '可选/未启用',
 skip: '跳过',
}

function levelTagColor(level?: string) {
 return LEVEL_COLOR[level || 'info'] || 'default'
}
function levelTagText(level?: string) {
 return LEVEL_TEXT[level || 'info'] || (level || '—')
}
function alertType(level?: string) {
 if (level === 'bad') return 'error'
 if (level === 'warn') return 'warning'
 if (level === 'ok') return 'success'
 return 'info'
}

/** 行内状态标签 */
const LevelTag = defineComponent({
 props: { check: { type: Object, default: null } },
 setup(props) {
 return () => {
 const c = props.check as any
 if (!c) return h('span', { class: 'text-gray-400 text-xs' }, '—')
 return h(
 'a-tag',
 { color: LEVEL_COLOR[c.level] || 'default' },
 () => `${c.label || LEVEL_TEXT[c.level] || c.level}`
 )
 }
 },
})

const checks = computed(() => status.value?.checks || {})
const overall = computed(() => status.value?.overall || null)

const nodeColor = computed(() => {
 const s = status.value?.seo_backend?.status
 if (s === 'connected') return 'green'
 if (s === 'degraded') return 'orange'
 if (s === 'unreachable' || s === 'failed') return 'red'
 return 'default'
})

const nodeLabel = computed(() => {
 const s = status.value?.seo_backend?.status
 const map: Record<string, string> = {
 connected: 'connected · 已连通（好）',
 degraded: 'degraded · 降级（需关注）',
 unreachable: 'unreachable · 不可达（异常）',
 failed: 'failed · 失败（异常）',
 not_configured: 'not_configured · 未启用（可选）',
 }
 return map[s || ''] || s || '—'
})

const acquisitionStatusColor = computed(() => {
 const panel = status.value?.acquisition_panel
 if (!panel) return 'default'
 if (panel.configured === panel.total) return 'success'
 if (panel.configured > 0) return 'warning'
 return 'error'
})

async function load() {
 loading.value = true
 try {
 const [res, panelRes] = await Promise.all([
 apiGet('/integrations/status'),
 apiGet('/foreign-trade/integrations/ecommerce-crawlers/panel').catch(() => null),
 ])
 status.value = res?.data ?? res
 const panelData = panelRes?.data ?? panelRes
 crawlPanel.value = panelData?.data ?? panelData ?? null
 } catch (e: any) {
 message.error(e?.message || '加载失败')
 } finally {
 loading.value = false
 }
}

onMounted(load)
</script>

<style scoped>
.check-rows {
 display: flex;
 flex-direction: column;
 width: 100%;
}
.check-row {
 display: grid;
 grid-template-columns: minmax(120px, 180px) minmax(0, 1fr);
 gap: 12px 16px;
 padding: 12px 4px;
 border-bottom: 1px solid var(--uj-p-border, #e3efea);
 align-items: start;
}
.check-row:last-child { border-bottom: none; }
.check-label {
 font-size: 13px;
 color: #55706b;
 padding-top: 2px;
}
.check-value { min-width: 0; }
.check-hint {
 margin-top: 6px;
 font-size: 12px;
 line-height: 1.55;
 color: #55706b;
 max-width: 72ch;
}
.check-hint code {
 font-family: var(--font-num, ui-monospace, monospace);
 background: #f0f5f3;
 padding: 0 4px;
 border-radius: 4px;
}
@media (max-width: 640px) {
 .check-row { grid-template-columns: 1fr; gap: 4px; }
}
</style>
