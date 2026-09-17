/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="tech-radar">
      <!-- Header -->
      <section class="page-header">
        <div>
          <h1>GEO 技术雷达</h1>
          <p class="desc">自动抓取 GEO/SEO 最新技术论文、行业动态、开源工具，驱动系统自进化</p>
        </div>
        <a-space>
          <a-button @click="fetchRadar" :loading="loading">
            🔄 立即扫描
          </a-button>
          <a-button type="primary" @click="fetchHighRelevance">
            🎯 只看高相关
          </a-button>
        </a-space>
      </section>

      <!-- Stats -->
      <section class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ radarData.total || 0 }}</div>
          <div class="stat-label">发现总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ highRelevanceCount }}</div>
          <div class="stat-label">高相关 (≥0.5)</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ radarData.sources_ok || 0 }}/{{ radarData.sources_total || 0 }}</div>
          <div class="stat-label">数据源在线</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ radarData.categories_fetched?.length || 0 }}</div>
          <div class="stat-label">覆盖类别</div>
        </div>
      </section>

      <!-- Category Filter -->
      <section class="filter-bar">
        <a-segmented v-model:value="activeCategory" :options="categoryOptions" @change="filterByCategory" />
        <a-slider v-model:value="minRelevance" :min="0" :max="1" :step="0.1" style="width: 120px" @change="filterByCategory" />
        <span class="relevance-label">相关性 ≥ {{ minRelevance.toFixed(1) }}</span>
      </section>

      <!-- Radar Items -->
      <section class="radar-list">
        <template v-if="loading">
          <SkeletonCard variant="table" :rows="5" />
        </template>
        <template v-else>
          <div v-for="(item, idx) in filteredItems" :key="idx" class="radar-item" :class="{ 'high-relevance': item.relevance_score >= 0.5 }">
            <div class="radar-item-header">
              <a-tag :color="getCategoryColor(item.category)" size="small">{{ getCategoryLabel(item.category) }}</a-tag>
              <span class="radar-source">{{ item.source }}</span>
              <div class="relevance-badge" :style="{ background: getRelevanceColor(item.relevance_score) }">
                {{ (item.relevance_score * 100).toFixed(0) }}%
              </div>
            </div>
            <a :href="item.url" target="_blank" rel="noopener" class="radar-title">
              {{ item.title }}
            </a>
            <p v-if="item.summary" class="radar-summary">{{ item.summary.slice(0, 200) }}</p>
            <div class="radar-meta">
              <span v-if="item.published_at" class="radar-date">📅 {{ formatDate(item.published_at) }}</span>
              <span v-if="item.technique_extracted" class="radar-technique">🎯 {{ item.technique_extracted }}</span>
            </div>
          </div>

          <a-empty v-if="!loading && filteredItems.length === 0" description="暂无数据，点击「立即扫描」开始" />
        </template>
      </section>

      <!-- Errors -->
      <section v-if="radarData.errors?.length" class="error-section">
        <a-alert type="warning" show-icon>
          <template #message>
            {{ radarData.errors.length }} 个数据源抓取失败
          </template>
          <template #description>
            <div v-for="err in radarData.errors" :key="err" class="error-item">{{ err }}</div>
          </template>
        </a-alert>
      </section>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import YdPage from '@/components/youding/YdPage.vue'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet } from '@/utils/api'

interface RadarItem {
  title: string
  url: string
  source: string
  category: string
  published_at: string
  summary: string
  relevance_score: number
  technique_extracted: string
}

const loading = ref(false)
const radarData = ref<any>({})
const activeCategory = ref('all')
const minRelevance = ref(0)

const categoryOptions = [
  { label: '全部', value: 'all' },
  { label: '📄 论文', value: 'paper' },
  { label: '📝 行业博客', value: 'blog' },
  { label: '💬 论坛讨论', value: 'forum' },
  { label: '🤖 AI 厂商', value: 'ai_vendor' },
  { label: '✅ 白帽规范', value: 'whitehat' },
  { label: '🔧 开源工具', value: 'opensource' },
  { label: '🎯 GEO 专项', value: 'geo_resource' },
  { label: '🇨🇳 中文社区', value: 'cn_community' },
]

const filteredItems = computed(() => {
  let items = radarData.value.items || []
  if (activeCategory.value !== 'all') {
    items = items.filter((i: RadarItem) => i.category === activeCategory.value)
  }
  if (minRelevance.value > 0) {
    items = items.filter((i: RadarItem) => i.relevance_score >= minRelevance.value)
  }
  return items
})

const highRelevanceCount = computed(() =>
  (radarData.value.items || []).filter((i: RadarItem) => i.relevance_score >= 0.5).length
)

function getCategoryColor(cat: string): string {
  const map: Record<string, string> = {
    paper: 'purple', blog: 'blue', opensource: 'green',
    ai_vendor: 'orange', whitehat: 'cyan', cn_community: 'red',
    forum: 'magenta', geo_resource: 'geekblue',
  }
  return map[cat] || 'default'
}

function getCategoryLabel(cat: string): string {
  const map: Record<string, string> = {
    paper: '论文', blog: '博客', opensource: '开源',
    ai_vendor: 'AI厂商', whitehat: '白帽规范', cn_community: '中文社区',
    forum: '论坛', geo_resource: 'GEO专项',
  }
  return map[cat] || cat
}

function getRelevanceColor(score: number): string {
  if (score >= 0.7) return '#22c55e'
  if (score >= 0.5) return '#4a9b8c'
  if (score >= 0.3) return '#f59e0b'
  return '#9ca3af'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return dateStr.slice(0, 10)
  }
}

async function fetchRadar() {
  loading.value = true
  try {
    const res = await apiGet('/tech-radar', { limit: 5 })
    radarData.value = res || {}
    message.success(`扫描完成，发现 ${radarData.value.total || 0} 条技术动态`)
  } catch (e: any) {
    message.error(`扫描失败: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function fetchHighRelevance() {
  loading.value = true
  try {
    const res = await apiGet('/tech-radar/latest-techniques')
    radarData.value = res || {}
    minRelevance.value = 0.3
    message.success(`发现 ${radarData.value.total || 0} 条高相关技术`)
  } catch (e: any) {
    message.error(`扫描失败: ${e.message}`)
  } finally {
    loading.value = false
  }
}

function filterByCategory() {
  // computed 自动响应
}

onMounted(fetchRadar)
</script>

<style scoped>
.tech-radar { max-width: 1200px; }

.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
}
.page-header h1 { font-size: 20px; font-weight: 700; color: #111827; margin: 0; }
.desc { font-size: 13px; color: #6b7280; margin: 4px 0 0; }

.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px;
}
.stat-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px 20px;
}
.stat-value { font-size: 28px; font-weight: 800; color: #111827; }
.stat-label { font-size: 13px; color: #6b7280; margin-top: 4px; }

.filter-bar {
  display: flex; align-items: center; gap: 16px; margin-bottom: 16px;
}
.relevance-label { font-size: 12px; color: #6b7280; white-space: nowrap; }

.radar-list { min-height: 200px; }

.radar-item {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 16px 20px; margin-bottom: 12px; transition: all 0.2s;
}
.radar-item:hover { border-color: var(--uj-brand, #4a9b8c); box-shadow: 0 2px 8px rgb(74 155 140 / 0.1); }
.radar-item.high-relevance { border-left: 3px solid var(--uj-brand, #4a9b8c); }

.radar-item-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.radar-source { font-size: 12px; color: #9ca3af; flex: 1; }
.relevance-badge {
  font-size: 11px; font-weight: 600; color: #fff; padding: 2px 8px;
  border-radius: 10px; min-width: 40px; text-align: center;
}

.radar-title {
  font-size: 15px; font-weight: 600; color: #111827; text-decoration: none;
  display: block; margin-bottom: 6px;
}
.radar-title:hover { color: var(--uj-brand, #4a9b8c); }

.radar-summary {
  font-size: 13px; color: #6b7280; line-height: 1.6; margin-bottom: 8px;
}

.radar-meta {
  display: flex; gap: 16px; font-size: 12px; color: #9ca3af;
}

.error-section { margin-top: 20px; }
.error-item { font-size: 12px; color: #92400e; margin: 2px 0; }
</style>
