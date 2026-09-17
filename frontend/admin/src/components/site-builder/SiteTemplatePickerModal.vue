/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-modal
    v-model:open="open"
    title=""
    width="1120px"
    :footer="null"
    destroy-on-close
    class="meoo-template-modal"
    :body-style="{ padding: '0px' }"
  >
    <!-- Modal 顶栏：Meoo 沉浸式标题与宣传条 -->
    <div class="meoo-modal-header">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="meoo-avatar-brand">
            <span class="text-xl">🐱</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-bold text-slate-900 m-0">秒悟 · 外贸独立站灵感模板库</h2>
              <span class="meoo-badge-top20">
                Top20 优选 · Google EEAT 满分架构
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-1 m-0">
              工业级通用出海独立站集群 · 预置西方采购商 RFQ 决策流 · 一键导入或调优 AI 提示词
            </p>
          </div>
        </div>
      </div>

      <!-- Meoo 风格：分类胶囊导航 + 搜索与排序栏 -->
      <div class="meoo-filter-bar mt-5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
        <!-- 分类切换 -->
        <div class="flex items-center gap-1.5 overflow-x-auto py-1">
          <button
            v-for="cat in categories"
            :key="cat.key"
            type="button"
            class="meoo-chip-btn"
            :class="{ active: currentCategory === cat.key }"
            @click="currentCategory = cat.key"
          >
            {{ cat.label }}
            <span v-if="cat.count !== undefined" class="meoo-chip-count">{{ cat.count }}</span>
          </button>
        </div>

        <!-- 搜索框与排序器 -->
        <div class="flex items-center gap-3">
          <div class="relative w-64">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索模板、关键词或行业..."
              class="meoo-search-input"
            />
            <span class="absolute left-3 top-2 text-slate-400 text-xs">🔍</span>
            <button
              v-if="searchQuery"
              type="button"
              class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600 text-xs"
              @click="searchQuery = ''"
            >
              ×
            </button>
          </div>

          <a-select
            v-model:value="sortBy"
            size="small"
            class="w-28 text-xs"
            :dropdown-match-select-width="false"
          >
            <a-select-option value="popular">最多点赞</a-select-option>
            <a-select-option value="views">最高浏览</a-select-option>
            <a-select-option value="recommended">谷歌权重</a-select-option>
          </a-select>
        </div>
      </div>
    </div>

    <!-- 模板卡片展示区 -->
    <div class="meoo-modal-body">
      <div v-if="filteredTemplates.length" class="meoo-card-grid">
        <div
          v-for="tpl in filteredTemplates"
          :key="tpl.id"
          class="meoo-card group"
          :class="{ 'meoo-card--selected': tpl.id === selectedId }"
          @click="pick(tpl.id)"
        >
          <!-- 封面图容器 -->
          <div class="meoo-cover-wrap">
            <img
              :src="tpl.coverUrl || fallbackCover(tpl.id)"
              :alt="tpl.name"
              class="meoo-cover-img"
              loading="lazy"
            />
            <div class="meoo-cover-overlay">
              <div class="flex items-center gap-2">
                <a-button
                  size="small"
                  type="primary"
                  class="meoo-overlay-btn"
                  @click.stop="pick(tpl.id)"
                >
                  套用此模板
                </a-button>
                <a-button
                  v-if="tpl.prompt"
                  size="small"
                  class="meoo-overlay-prompt-btn"
                  @click.stop="showPromptModal(tpl)"
                >
                  查看 Prompt
                </a-button>
              </div>
            </div>

            <!-- 角标 -->
            <div class="meoo-card-badges">
              <span class="meoo-badge-cat">{{ tpl.categoryLabel || 'B2B 官网' }}</span>
              <span v-if="tpl.id === selectedId" class="meoo-badge-active">正在使用</span>
            </div>
          </div>

          <!-- 卡片正文与作者信息 (对齐秒悟) -->
          <div class="meoo-card-info">
            <div class="flex items-start justify-between gap-2">
              <h3 class="meoo-card-title truncate" :title="tpl.name">
                {{ tpl.name }}
              </h3>
            </div>
            <p class="meoo-card-desc" :title="tpl.description">
              {{ tpl.description }}
            </p>

            <!-- 标签行 -->
            <div v-if="tpl.tags?.length" class="meoo-tags-row">
              <span v-for="tag in tpl.tags" :key="tag" class="meoo-mini-tag">
                #{{ tag }}
              </span>
            </div>

            <!-- 底栏：创作者 + 热度/点赞统计 -->
            <div class="meoo-card-footer">
              <div class="meoo-author-box">
                <img
                  :src="tpl.authorAvatar || defaultAvatar"
                  alt=""
                  class="meoo-author-avatar"
                />
                <span class="meoo-author-name truncate">{{ tpl.author || '出海创新团队' }}</span>
              </div>
              <div class="meoo-stats-box">
                <span class="meoo-stat-item">
                  <span class="text-[11px]">👁</span> {{ tpl.views || '12.5k' }}
                </span>
                <span
                  class="meoo-stat-item meoo-like-btn"
                  :class="{ liked: likedMap[tpl.id] }"
                  @click.stop="toggleLike(tpl.id)"
                >
                  <span class="text-[11px]">{{ likedMap[tpl.id] ? '❤️' : '🤍' }}</span>
                  {{ (tpl.likes || 60) + (likedMap[tpl.id] ? 1 : 0) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="meoo-empty-box">
        <span class="text-4xl mb-3">🔍</span>
        <h4 class="text-sm font-semibold text-slate-700">未找到相关建站模板</h4>
        <p class="text-xs text-slate-400 mt-1">换个搜索词或点击“全部”查看全部精选模板</p>
        <button type="button" class="meoo-reset-btn" @click="resetFilters">
          清空搜索条件
        </button>
      </div>
    </div>

    <!-- AI 提示词与构建参数详情弹窗 -->
    <a-modal
      v-model:open="promptModalOpen"
      title="阿里秒悟 · 谷歌 Top-3 智能建站提示词"
      width="640px"
      :footer="null"
      destroy-on-close
    >
      <div v-if="activeTpl" class="p-2 space-y-4">
        <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-700">模板架构: {{ activeTpl.name }}</span>
            <span class="text-[11px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-medium">已验证 EEAT 权威度</span>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed m-0 font-sans select-all whitespace-pre-wrap">
            {{ activeTpl.prompt }}
          </p>
        </div>

        <div class="flex items-center justify-end gap-3 pt-2">
          <a-button @click="copyPrompt(activeTpl.prompt)">
            复制提示词
          </a-button>
          <a-button type="primary" class="bg-blue-600" @click="applyPromptAndTemplate(activeTpl)">
            一键套用模板并注入生成器
          </a-button>
        </div>
      </div>
    </a-modal>
  </a-modal>
</template>



<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  SITE_BUILDER_TEMPLATES,
  type SiteBuilderTemplateId,
  type SiteBuilderTemplateMeta,
} from '@/templates/site-builder'

const open = defineModel<boolean>('open', { default: false })
const selectedId = defineModel<SiteBuilderTemplateId>('templateId', { required: true })

const emit = defineEmits<{
  select: [id: SiteBuilderTemplateId]
  applyPrompt: [prompt: string, id: SiteBuilderTemplateId]
}>()

const defaultAvatar = 'https://gw.alicdn.com/imgextra/i4/O1CN01MxUXzS1xYRjMwA2la_!!6000000006455-2-tps-184-184.png'

const currentCategory = ref<string>('all')
const searchQuery = ref<string>('')
const sortBy = ref<'popular' | 'views' | 'recommended'>('popular')
const promptModalOpen = ref(false)
const activeTpl = ref<SiteBuilderTemplateMeta | null>(null)
const likedMap = reactive<Record<string, boolean>>({})

const categories = computed(() => {
  const all = SITE_BUILDER_TEMPLATES.length
  const portal = SITE_BUILDER_TEMPLATES.filter((t) => t.category === 'portal').length
  const tools = SITE_BUILDER_TEMPLATES.filter((t) => t.category === 'tools').length
  const h5 = SITE_BUILDER_TEMPLATES.filter((t) => t.category === 'h5').length
  return [
    { key: 'all', label: '全部', count: all },
    { key: 'featured', label: '精选高权重' },
    { key: 'portal', label: '外贸官网', count: portal },
    { key: 'h5', label: '高转化营销', count: h5 },
    { key: 'tools', label: '计算器与工具', count: tools },
    { key: 'liked', label: '我喜欢的' },
  ]
})

function fallbackCover(id: SiteBuilderTemplateId): string {
  const covers: Record<string, string> = {
    'premium-b2b-v1': 'https://img.alicdn.com/imgextra/i4/O1CN01n6BUtq1iXmxBFROO9_!!6000000004423-2-tps-1681-936.png',
    'insulation-classic': 'https://img.alicdn.com/imgextra/i3/O1CN01TnanNh1ukPFprNgDn_!!6000000006075-2-tps-1432-1098.png',
    'building-modern': 'https://img.alicdn.com/imgextra/i2/O1CN01l1Snij1M6Nhpl0gUk_!!6000000001385-2-tps-1433-1098.png',
    'export-pro': 'https://img.alicdn.com/imgextra/i3/O1CN01DoEVsC1zk0zkFw1xk_!!6000000006751-2-tps-1432-1098.png',
    'fireproof-safety': 'https://img.alicdn.com/imgextra/i4/O1CN01V81XIS1GtwsKUoBbB_!!6000000000681-2-tps-1586-992.png',
    'rubber-insulation': 'https://img.alicdn.com/imgextra/i2/O1CN01ui7JMb1ynOITp0fmE_!!6000000006623-2-tps-2880-1600.png',
    'steel-structure': 'https://img.alicdn.com/imgextra/i4/O1CN01EBqYv920osouyHqEj_!!6000000006897-2-tps-2880-1600.png',
    'ceramic-stone': 'https://img.alicdn.com/imgextra/i1/O1CN01IDDcPi1be11nj5e50_!!6000000003489-2-tps-1681-935.png',
    'hvac-duct': 'https://img.alicdn.com/imgextra/i2/O1CN0139B7r71uJqHaCYQ6a_!!6000000006017-2-tps-1433-1098.png',
  }
  return covers[id] || 'https://img.alicdn.com/imgextra/i4/O1CN01n6BUtq1iXmxBFROO9_!!6000000004423-2-tps-1681-936.png'
}

const filteredTemplates = computed(() => {
  let list = [...SITE_BUILDER_TEMPLATES]

  // 分类筛选
  if (currentCategory.value === 'portal') {
    list = list.filter((t) => t.category === 'portal')
  } else if (currentCategory.value === 'h5') {
    list = list.filter((t) => t.category === 'h5')
  } else if (currentCategory.value === 'tools') {
    list = list.filter((t) => t.category === 'tools')
  } else if (currentCategory.value === 'featured') {
    list = list.filter((t) => (t.likes || 0) >= 80)
  } else if (currentCategory.value === 'liked') {
    list = list.filter((t) => Boolean(likedMap[t.id]))
  }

  // 搜索关键词
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags?.some((tag) => tag.toLowerCase().includes(q)),
    )
  }

  // 排序
  if (sortBy.value === 'popular') {
    list.sort((a, b) => (b.likes || 0) - (a.likes || 0))
  } else if (sortBy.value === 'views') {
    list.sort((a, b) => parseFloat(b.views || '0') - parseFloat(a.views || '0'))
  }

  return list
})

function pick(id: SiteBuilderTemplateId) {
  emit('select', id)
  open.value = false
}

function showPromptModal(tpl: SiteBuilderTemplateMeta) {
  activeTpl.value = tpl
  promptModalOpen.value = true
}

function copyPrompt(text?: string) {
  if (!text) return
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
    message.success('提示词已复制到剪贴板')
  } else {
    message.info('请手动选中文本进行复制')
  }
}

function applyPromptAndTemplate(tpl: SiteBuilderTemplateMeta) {
  if (tpl.prompt) {
    emit('applyPrompt', tpl.prompt, tpl.id)
  }
  pick(tpl.id)
  promptModalOpen.value = false
}

function toggleLike(id: string) {
  likedMap[id] = !likedMap[id]
}

function resetFilters() {
  currentCategory.value = 'all'
  searchQuery.value = ''
}
</script>

<style scoped lang="scss">
.meoo-template-modal {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.meoo-modal-header {
  padding: 24px 28px 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border-bottom: 1px solid #f1f5f9;
}

.meoo-avatar-brand {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.meoo-badge-top20 {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 2px 8px;
  border-radius: 999px;
}

.meoo-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid transparent;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.16s ease;

  &:hover {
    background: #e2e8f0;
    color: #1e293b;
  }

  &.active {
    background: #0f172a;
    color: #ffffff;
    font-weight: 600;
  }
}

.meoo-chip-count {
  font-size: 10.5px;
  opacity: 0.7;
}

.meoo-search-input {
  width: 100%;
  height: 32px;
  padding: 0 28px 0 28px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  font-size: 12.5px;
  color: #1e293b;
  transition: border-color 0.15s, box-shadow 0.15s;

  &:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
  }
}

.meoo-modal-body {
  padding: 24px 28px 32px;
  max-height: 64vh;
  overflow-y: auto;
  background: #f8fafc;
}

.meoo-card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.meoo-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(37, 99, 235, 0.2);
    border-color: #93c5fd;
  }

  &--selected {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px #2563eb, 0 12px 28px -4px rgba(37, 99, 235, 0.2) !important;
  }
}

.meoo-cover-wrap {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 黄金视效比例 */
  background: #0f172a;
  overflow: hidden;
}

.meoo-cover-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;

  .meoo-card:hover & {
    transform: scale(1.04);
  }
}

.meoo-cover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;

  .meoo-card:hover & {
    opacity: 1;
  }
}

.meoo-overlay-btn {
  background: #2563eb;
  border: none;
  font-weight: 600;
  font-size: 12px;
  border-radius: 6px;
  padding: 0 14px;
}

.meoo-overlay-prompt-btn {
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  border: none;
  font-weight: 600;
  font-size: 12px;
  border-radius: 6px;
}

.meoo-card-badges {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
}

.meoo-badge-cat {
  font-size: 10.5px;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(4px);
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 6px;
}

.meoo-badge-active {
  font-size: 10.5px;
  font-weight: 700;
  background: #2563eb;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4);
}

.meoo-card-info {
  padding: 14px 16px 12px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.meoo-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px;
}

.meoo-card-desc {
  font-size: 12px;
  color: #64748b;
  margin: 0 0 10px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 35px;
}

.meoo-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.meoo-mini-tag {
  font-size: 10px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.meoo-card-footer {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11.5px;
}

.meoo-author-box {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 55%;
}

.meoo-author-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.meoo-author-name {
  color: #475569;
  font-size: 11.5px;
  font-weight: 500;
}

.meoo-stats-box {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #94a3b8;
}

.meoo-stat-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
}

.meoo-like-btn {
  cursor: pointer;
  transition: color 0.15s;

  &:hover {
    color: #ef4444;
  }

  &.liked {
    color: #ef4444;
    font-weight: 600;
  }
}

.meoo-empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
}

.meoo-reset-btn {
  margin-top: 14px;
  padding: 6px 14px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

@media (max-width: 900px) {
  .meoo-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .meoo-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>


