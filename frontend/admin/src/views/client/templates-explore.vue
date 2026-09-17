/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="workspace-page">
      <div class="workspace-topline">
        <div class="breadcrumb">
          <span>租户工作台</span>
          <span class="breadcrumb-separator">/</span>
          <strong>资源中枢</strong>
        </div>
        <div class="topline-actions">
          <span class="system-status"><span class="status-dot" /> 系统运行正常</span>
          <button type="button" class="topline-link" @click="router.push('/client/site-editor')">查看我的网站 <ArrowRightOutlined /></button>
        </div>
      </div>

      <section class="command-hero" aria-labelledby="workspace-title">
        <div class="hero-copy">
          <div class="eyebrow"><span class="eyebrow-line" /> TENANT WORKSPACE <span class="eyebrow-index">01</span></div>
          <h1 id="workspace-title">让每一次访问，都成为下一条询盘</h1>
          <p>从独立站、产品资产到内容分发，优丁把出海经营所需的关键动作，收拢在一个可持续增长的工作台里。</p>
          <div class="hero-actions">
            <button type="button" class="primary-action" @click="router.push('/client/site-editor')">
              <RocketOutlined /> 开始创建站点
            </button>
            <button type="button" class="secondary-action" @click="scrollToLibrary">
              浏览资源库 <ArrowRightOutlined />
            </button>
          </div>
          <div class="hero-proof"><SafetyCertificateOutlined /> 已为 {{ tenantName }} 保存本月经营快照</div>
        </div>
        <div class="hero-visual" aria-label="租户资源健康度">
          <div class="visual-orbit visual-orbit--outer" />
          <div class="visual-orbit visual-orbit--inner" />
          <div class="signal-card signal-card--primary">
            <div class="signal-card__label">WORKSPACE HEALTH</div>
            <div class="signal-card__value">92<span>/100</span></div>
            <div class="signal-card__trend"><span class="trend-arrow">↗</span> 较上周 +8.4%</div>
          </div>
          <div class="signal-card signal-card--secondary">
            <span class="signal-icon"><GlobalOutlined /></span>
            <div><strong>3 个站点</strong><small>均已连接域名</small></div>
          </div>
          <div class="hero-grid-mark" />
        </div>
      </section>

      <section class="metric-grid" aria-label="经营概览">
        <article v-for="metric in metrics" :key="metric.label" class="metric-card">
          <div class="metric-card__head"><span>{{ metric.label }}</span><span class="metric-icon"><component :is="metric.icon" /></span></div>
          <div class="metric-card__value">{{ metric.value }}</div>
          <div class="metric-card__foot"><span class="metric-change" :class="metric.tone">{{ metric.change }}</span><span>{{ metric.note }}</span></div>
          <div class="metric-spark" :class="`metric-spark--${metric.tone}`"><i v-for="(bar, index) in metric.bars" :key="index" :style="{ height: `${bar}%` }" /></div>
        </article>
      </section>

      <section class="workspace-grid">
        <article class="panel pulse-panel">
          <div class="panel-header">
            <div><span class="section-kicker">BUSINESS PULSE</span><h2>经营脉搏</h2><p>过去 7 天的租户工作台活动与商机信号</p></div>
            <button type="button" class="quiet-button" @click="router.push('/client/dashboard')">查看完整报告 <ArrowRightOutlined /></button>
          </div>
          <div class="pulse-chart" aria-label="过去七天经营活动趋势">
            <div class="chart-y-axis"><span>高</span><span>中</span><span>低</span></div>
            <div class="chart-area">
              <div class="chart-grid-line chart-grid-line--one" /><div class="chart-grid-line chart-grid-line--two" /><div class="chart-grid-line chart-grid-line--three" />
              <div class="chart-bars"><div v-for="point in pulsePoints" :key="point.day" class="chart-column"><div class="bar-group"><i class="bar bar--reach" :style="{ height: `${point.reach}%` }" /><i class="bar bar--leads" :style="{ height: `${point.leads}%` }" /></div><span>{{ point.day }}</span></div></div>
            </div>
            <div class="chart-legend"><span><i class="legend-dot legend-dot--reach" /> 触达量</span><span><i class="legend-dot legend-dot--leads" /> 有效询盘</span></div>
          </div>
          <div class="pipeline-row">
            <div class="pipeline-intro"><span class="section-kicker">LEAD PIPELINE</span><strong>询盘转化链</strong><small>本月累计 326 条有效线索</small></div>
            <div v-for="stage in pipeline" :key="stage.label" class="pipeline-stage"><div class="pipeline-stage__top"><strong>{{ stage.value }}</strong><span>{{ stage.rate }}</span></div><div class="pipeline-track"><i :style="{ width: `${stage.progress}%`, background: stage.color }" /></div><small>{{ stage.label }}</small></div>
          </div>
        </article>

        <aside class="panel quick-panel">
          <div class="panel-header panel-header--compact"><div><span class="section-kicker">QUICK ACTIONS</span><h2>下一步做什么</h2></div><span class="panel-count">04</span></div>
          <div class="quick-list">
            <button v-for="action in quickActions" :key="action.label" type="button" class="quick-item" @click="router.push(action.path)">
              <span class="quick-item__icon"><component :is="action.icon" /></span><span class="quick-item__copy"><strong>{{ action.label }}</strong><small>{{ action.description }}</small></span><ArrowRightOutlined class="quick-item__arrow" />
            </button>
          </div>
          <div class="plan-card"><div class="plan-card__head"><span>PRO 出海方案</span><span class="plan-badge">ACTIVE</span></div><div class="plan-card__value">本周期资源使用率 <strong>72%</strong></div><div class="plan-track"><i style="width: 72%" /></div><button type="button" @click="router.push('/client/billing')">查看套餐与额度 <ArrowRightOutlined /></button></div>
        </aside>
      </section>

      <section class="resource-section" id="resource-library">
        <div class="resource-header"><div><span class="section-kicker">RESOURCE LIBRARY</span><h2>让资产成为增长基础设施</h2><p>挑选合适的工作流、模板与技能，快速进入下一次发布。</p></div><div class="resource-summary"><span><strong>{{ exploreData.length }}</strong> 个资源</span><span class="summary-divider" /><span>本月新增 <strong>12</strong> 个</span></div></div>
        <div class="resource-toolbar"><div class="tab-chips-group"><button v-for="tab in tabs" :key="tab.value" type="button" class="tab-chip-btn" :class="{ active: activeTab === tab.value }" @click="activeTab = tab.value">{{ tab.label }} <span>{{ tab.count }}</span></button></div><div class="control-right"><label class="search-input-wrap"><SearchOutlined class="search-icon" /><input v-model="searchQuery" type="search" placeholder="搜索资源、场景或行业" class="search-input" /><button v-if="searchQuery" type="button" class="clear-btn" aria-label="清空搜索" @click="searchQuery = ''">×</button></label><a-select v-model:value="sortBy" size="small" class="sort-select" :bordered="false" aria-label="排序方式"><a-select-option value="popular">按热度</a-select-option><a-select-option value="views">按浏览</a-select-option><a-select-option value="newest">最新加入</a-select-option></a-select></div></div>

        <div v-if="displayList.length" class="resource-grid">
          <article v-for="(item, index) in displayList" :key="item.id" class="resource-card" :style="{ '--card-delay': `${Math.min(index, 8) * 45}ms` }" tabindex="0" role="button" @click="openDetail(item)" @keydown.enter="openDetail(item)" @keydown.space.prevent="openDetail(item)">
            <div class="resource-card__cover"><img :src="item.coverUrl" :alt="item.title" loading="lazy" decoding="async" /><div class="cover-shade" /><span v-if="item.badgeText" class="cover-badge"><CheckCircleFilled /> {{ item.badgeText }}</span><span class="cover-category">{{ item.categoryLabel }}</span><div class="cover-actions"><button type="button" class="cover-action cover-action--primary" @click.stop="applyToSiteBuilder(item)">套用到建站</button><button type="button" class="cover-action" @click.stop="openDetail(item)">查看详情</button></div></div>
            <div class="resource-card__body"><div class="resource-card__title-row"><h3>{{ item.title }}</h3><button type="button" class="like-button" :class="{ liked: item.isLiked }" :aria-label="item.isLiked ? '取消收藏' : '收藏资源'" @click.stop="toggleLike(item)"><HeartFilled v-if="item.isLiked" /><HeartOutlined v-else /></button></div><p>{{ item.description }}</p><div class="resource-card__meta"><span class="author"><span class="author-avatar">{{ item.author.slice(0, 1) }}</span>{{ item.author }}</span><span class="resource-stats"><EyeOutlined /> {{ item.views }} <HeartOutlined /> {{ item.likes }}</span></div></div>
          </article>
        </div>
        <div v-else class="empty-state"><div class="empty-state__icon"><SearchOutlined /></div><h3>没有找到匹配的资源</h3><p>换一个关键词，或清除搜索条件继续浏览。</p><button type="button" class="secondary-action" @click="searchQuery = ''; activeTab = 'all'">清除筛选</button></div>
      </section>
    </div>

    <a-drawer v-model:open="detailDrawerOpen" :title="activeDetailItem?.title || '资源详情'" width="560px" placement="right">
      <div v-if="activeDetailItem" class="drawer-inner">
        <div class="cover-preview-large"><img :src="activeDetailItem.coverUrl" :alt="activeDetailItem.title" /><div class="drawer-cover-label">{{ activeDetailItem.categoryLabel }} · 优丁资源库</div></div>
        <div class="drawer-heading"><div><span class="section-kicker">WORKFLOW RESOURCE</span><h3>{{ activeDetailItem.title }}</h3></div><span class="drawer-author">{{ activeDetailItem.author }}</span></div>
        <p class="drawer-description">{{ activeDetailItem.description }}</p>
        <div class="drawer-stats"><span><EyeOutlined /> {{ activeDetailItem.views }} 浏览</span><span><HeartOutlined /> {{ activeDetailItem.likes }} 收藏</span><span><MessageOutlined /> {{ activeDetailItem.comments || 0 }} 评论</span></div>
        <div class="prompt-panel"><div class="prompt-panel__head"><strong>AI 工作流提示词</strong><button type="button" @click="copyPrompt">复制 Prompt</button></div><p>{{ activeDetailItem.prompt }}</p></div>
        <button type="button" class="primary-action primary-action--full" @click="applyToSiteBuilder(activeDetailItem)"><RocketOutlined /> 一键套入建站中枢 <ArrowRightOutlined /></button>
      </div>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">

import { onMounted } from 'vue'
import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/ai/templates') } catch { /* 空状态 */ }
})
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowRightOutlined,
  CheckCircleFilled,
  CloudServerOutlined,
  DatabaseOutlined,
  EditOutlined,
  EyeOutlined,
  GlobalOutlined,
  HeartFilled,
  HeartOutlined,
  LineChartOutlined,
  MessageOutlined,
  RocketOutlined,
  SearchOutlined,
  SendOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ThunderboltFilled,
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'

const router = useRouter()
const tenantName = ref('当前租户')
const activeTab = ref<'all' | 'curated' | 'templates' | 'liked' | 'my'>('all')
const searchQuery = ref('')
const sortBy = ref<'popular' | 'views' | 'newest'>('popular')

const metrics = [
  { label: '本月站点访问', value: '128.4K', change: '+18.6%', note: '较上月', tone: 'positive', icon: LineChartOutlined, bars: [38, 48, 42, 63, 57, 78, 70, 88] },
  { label: '有效询盘', value: '326', change: '+12.4%', note: '转化率 4.8%', tone: 'positive', icon: TeamOutlined, bars: [35, 42, 56, 49, 72, 60, 76, 82] },
  { label: '已发布内容', value: '48', change: '86%', note: '本月完成度', tone: 'brand', icon: SendOutlined, bars: [22, 35, 31, 55, 48, 66, 72, 86] },
  { label: 'AI Token 余额', value: '72%', change: '充足', note: '预计可用 18 天', tone: 'warm', icon: ThunderboltFilled, bars: [78, 74, 72, 70, 68, 66, 64, 62] },
]

const pulsePoints = [
  { day: '周一', reach: 42, leads: 34 }, { day: '周二', reach: 56, leads: 43 }, { day: '周三', reach: 48, leads: 38 }, { day: '周四', reach: 68, leads: 51 }, { day: '周五', reach: 74, leads: 58 }, { day: '周六', reach: 62, leads: 46 }, { day: '周日', reach: 86, leads: 69 },
]

const pipeline = [
  { label: '新访问', value: '12.8K', rate: '100%', progress: 100, color: '#4a9b8c' },
  { label: '内容互动', value: '2.4K', rate: '19%', progress: 76, color: '#6cb8a6' },
  { label: '有效询盘', value: '326', rate: '4.8%', progress: 48, color: '#d29b52' },
]

const quickActions = [
  { label: '搭建一个新站点', description: 'AI 生成结构与页面', path: '/client/site-editor', icon: EditOutlined },
  { label: '补全产品资料', description: '让产品更容易被发现', path: '/client/products', icon: DatabaseOutlined },
  { label: '处理待跟进询盘', description: '今日有 8 条待处理', path: '/client/inquiries', icon: TeamOutlined },
  { label: '检查分发队列', description: '3 个渠道等待发布', path: '/client/distribute', icon: CloudServerOutlined },
]

interface GalleryItem {
  id: string
  title: string
  author: string
  views: string
  likes: number
  comments?: number
  coverUrl: string
  category: string
  categoryLabel: string
  badgeText?: string
  description: string
  prompt: string
  isLiked?: boolean
  isCurated?: boolean
  isTemplate?: boolean
  createdAt: number
}

const exploreData = ref<GalleryItem[]>([
  { id: 'graphic-portfolio', title: '平面设计作品集 · 极简黑曜', author: 'Meoo编辑部', views: '3.0k', likes: 20, comments: 2, coverUrl: 'https://gw.alicdn.com/imgextra/i4/O1CN01n6BUtq1iXmxBFROO9_!!6000000004423-2-tps-1681-936.png', category: 'portfolio', categoryLabel: '作品集', isCurated: true, isTemplate: true, createdAt: 11, description: '设计不止于好看，更要被记住。极简黑金高雅配色，适合出海工业品展示与高奢品牌站。', prompt: '为我打造一个黑曜质感的出海品牌官方展厅，突出产品 3D 悬浮微光与极简现代字体排版，具备多语言与国际询盘入口。' },
  { id: 'dessert-order-site', title: '甜品店订位&下单网站', author: '子虚', views: '2.7k', likes: 46, comments: 6, badgeText: '精选', coverUrl: 'https://gw.alicdn.com/imgextra/i3/O1CN01TnanNh1ukPFprNgDn_!!6000000006075-2-tps-1432-1098.png', category: 'order', categoryLabel: '零售预约', isCurated: true, isTemplate: true, createdAt: 10, description: '把季节做成一口甜。温暖米白底色，适合轻工业建材、定制家居或跨境消费品展示。', prompt: '创建一个温暖、清晰、富有亲和力的海外独立站，包含快速订位表单、产品画册与 WhatsApp 一键加群交流。' },
  { id: 'meoo-arena-game', title: 'Meoo大乱斗 · 游戏概念站', author: '夕尘', views: '2.3k', likes: 21, comments: 9, badgeText: '精选', coverUrl: 'https://gw.alicdn.com/imgextra/i4/O1CN01V81XIS1GtwsKUoBbB_!!6000000000681-2-tps-1586-992.png', category: 'game', categoryLabel: '暗黑潮流', isCurated: true, isTemplate: true, createdAt: 9, description: '暗黑电竞科技风格，搭载角色英雄网格与数据指标走马灯，适合需要强记忆点的品牌发布。', prompt: '构建一个高冲击力的科技电竞风格独立站，突出黑金荧光元素、动态角色卡片与全球对战排行榜。' },
  { id: 'liquid-glass-studio', title: 'Liquid Glass Studio 视觉展示应用', author: 'Meoo编辑部', views: '9.2k', likes: 84, comments: 12, coverUrl: 'https://gw.alicdn.com/imgextra/i2/O1CN01l1Snij1M6Nhpl0gUk_!!6000000001385-2-tps-1433-1098.png', category: 'app', categoryLabel: '流体视觉', isCurated: true, isTemplate: true, createdAt: 8, description: 'Apple 风格液态玻璃透镜动效，适合现代高级 SaaS 官网与精密产品展示。', prompt: '帮我设计一个 Apple 风格的液态玻璃拟态出海官网，包含高斯模糊材质、透镜折射光泽与极致极简交互。' },
  { id: 'real-shoot-game', title: '真实射击 · 交互落地页', author: '夕尘', views: '850', likes: 14, comments: 4, badgeText: '精选', coverUrl: 'https://gw.alicdn.com/imgextra/i3/O1CN01DoEVsC1zk0zkFw1xk_!!6000000006751-2-tps-1432-1098.png', category: 'landing', categoryLabel: '创意落地页', isCurated: true, isTemplate: false, createdAt: 7, description: '实景沉浸式 360 度视角探索，适合大型工厂全景实拍、验厂展厅与仓储园区虚拟漫游。', prompt: '打造一个支持海外采购商 360 度全景虚拟验厂的沉浸式页面，包含工厂生产线大图、仓库现货盘点与实时连线。' },
  { id: 'cine-capsule', title: 'CineCapsule · 胶囊时光网', author: 'TenwithTen', views: '35.7k', likes: 31, comments: 8, coverUrl: 'https://gw.alicdn.com/imgextra/i4/O1CN01MxUXzS1xYRjMwA2la_!!6000000006455-2-tps-184-184.png', category: 'app', categoryLabel: '胶囊应用', isCurated: true, isTemplate: true, createdAt: 6, description: '暖白复古奶油风，精致圆角胶囊组件，带来轻松愉悦的高转化视觉感受。', prompt: '设计一套暖奶油色的外贸独立站产品库，具备卡片式分类抽屉、高精度尺寸标注与快速一键索样功能。' },
  { id: 'vfx-visual-skill', title: 'VFX 技能鉴赏 · 粒子暗夜', author: '夕尘', views: '384', likes: 15, comments: 7, badgeText: '精选', coverUrl: 'https://gw.alicdn.com/imgextra/i4/O1CN01n6BUtq1iXmxBFROO9_!!6000000004423-2-tps-1681-936.png', category: 'vfx', categoryLabel: '粒子特效', isCurated: true, isTemplate: false, createdAt: 5, description: '暗夜流光与粒子汇聚动效，适合前沿材料、光伏新能源与高端智能制造品牌出海。', prompt: '创建一个新能源与高精尖出海官网，主打暗色调粒子流光背景与碳减排数据指标动态仪表盘。' },
  { id: 'meoo-art-school', title: 'Meoo 创新艺术学院官网', author: 'Meoo编辑部', views: '4.5k', likes: 20, comments: 3, isCurated: true, isTemplate: true, createdAt: 4, coverUrl: 'https://gw.alicdn.com/imgextra/i3/O1CN01TnanNh1ukPFprNgDn_!!6000000006075-2-tps-1432-1098.png', category: 'portal', categoryLabel: '学院机构', description: '走向未来的从美丽到灵图。层次分明的排版体系与大师级作品画廊，突出版权与权威性。', prompt: '为国际学术或行业权威协会打造一套严谨大气的门户站，包含论文检测报告、全球会员认证与年度峰会报名。' },
  { id: 'ai-movie-display', title: 'AI 电影展示网站', author: 'Meoo编辑部', views: '7.3k', likes: 28, comments: 5, isCurated: true, isTemplate: true, createdAt: 3, coverUrl: 'https://gw.alicdn.com/imgextra/i2/O1CN01l1Snij1M6Nhpl0gUk_!!6000000001385-2-tps-1433-1098.png', category: 'video', categoryLabel: '影音展示', description: '电影级景深虚化与大字报式叙事封面，抓住海外客户停留时长。', prompt: '设计一套电影质感的外贸品牌故事站，以创始人匠心传承与大型工程施工实录为主线，建立海外深度信任。' },
])

const tabs = computed(() => [
  { label: '全部资源', value: 'all' as const, count: exploreData.value.length },
  { label: '精选工作流', value: 'curated' as const, count: exploreData.value.filter((item) => item.isCurated).length },
  { label: '可套用模板', value: 'templates' as const, count: exploreData.value.filter((item) => item.isTemplate).length },
  { label: '我的收藏', value: 'liked' as const, count: exploreData.value.filter((item) => item.isLiked).length },
  { label: '我发布的', value: 'my' as const, count: exploreData.value.filter((item) => item.author.includes('我')).length },
])

const displayList = computed(() => {
  let list = [...exploreData.value]
  if (activeTab.value === 'curated') list = list.filter((item) => item.isCurated)
  if (activeTab.value === 'templates') list = list.filter((item) => item.isTemplate)
  if (activeTab.value === 'liked') list = list.filter((item) => item.isLiked)
  if (activeTab.value === 'my') list = list.filter((item) => item.author.includes('我'))
  const query = searchQuery.value.trim().toLowerCase()
  if (query) list = list.filter((item) => `${item.title} ${item.description} ${item.author} ${item.categoryLabel}`.toLowerCase().includes(query))
  if (sortBy.value === 'popular') list.sort((a, b) => b.likes - a.likes)
  if (sortBy.value === 'views') list.sort((a, b) => parseViews(b.views) - parseViews(a.views))
  if (sortBy.value === 'newest') list.sort((a, b) => b.createdAt - a.createdAt)
  return list
})

function parseViews(value: string) {
  const normalized = value.toLowerCase().replace('k', '')
  return Number(normalized) * (value.toLowerCase().includes('k') ? 1000 : 1)
}

function toggleLike(item: GalleryItem) {
  item.isLiked = !item.isLiked
  item.likes += item.isLiked ? 1 : -1
  if (item.isLiked) message.success(`已收藏「${item.title}」`)
}

function scrollToLibrary() {
  document.getElementById('resource-library')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const detailDrawerOpen = ref(false)
const activeDetailItem = ref<GalleryItem | null>(null)

function openDetail(item: GalleryItem) {
  activeDetailItem.value = item
  detailDrawerOpen.value = true
}

async function copyPrompt() {
  if (!activeDetailItem.value?.prompt) return
  await navigator.clipboard.writeText(activeDetailItem.value.prompt)
  message.success('Prompt 已复制到剪贴板')
}

function applyToSiteBuilder(item: GalleryItem) {
  detailDrawerOpen.value = false
  sessionStorage.setItem('meoo_apply_prompt', item.prompt)
  sessionStorage.setItem('meoo_apply_template_name', item.title)
  message.success(`已将「${item.title}」注入建站中枢`)
  router.push('/client/site-editor')
}
</script>

<style scoped lang="scss">
.workspace-page {
  --ink: #1d3936;
  --ink-soft: #5f7470;
  --muted: #8b9b98;
  --line: #dfe9e6;
  --surface: #ffffff;
  --page: #f5f8f7;
  --brand: #4a9b8c;
  --brand-deep: #2a6b60;
  --brand-soft: #e8faf4;
  --warm: #d29b52;
  max-width: 1440px;
  margin: 0 auto;
  padding: 4px 8px 48px;
  color: var(--ink);
}

.workspace-topline, .topline-actions, .breadcrumb, .hero-actions, .hero-proof, .resource-header, .resource-summary, .resource-toolbar, .control-right, .panel-header, .metric-card__head, .metric-card__foot, .resource-card__title-row, .resource-card__meta, .author, .resource-stats, .drawer-heading, .drawer-stats, .prompt-panel__head, .system-status, .topline-link { display: flex; align-items: center; }
.workspace-topline { justify-content: space-between; min-height: 36px; margin-bottom: 12px; font-size: 12px; color: var(--muted); }
.breadcrumb { gap: 9px; }.breadcrumb strong { color: var(--ink-soft); font-weight: 600; }.breadcrumb-separator { color: #b3c2bf; }.topline-actions { gap: 20px; }.system-status { gap: 7px; color: #508277; }.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #49ae82; box-shadow: 0 0 0 4px #e4f5ec; }.topline-link { gap: 5px; border: 0; background: transparent; color: var(--ink-soft); cursor: pointer; font: inherit; }.topline-link:hover { color: var(--brand-deep); }

.command-hero { position: relative; display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(360px, .92fr); min-height: 330px; overflow: hidden; border: 1px solid #274b47; border-radius: 20px; background: linear-gradient(118deg, #173f3a 0%, #24564d 58%, #2e6b60 100%); box-shadow: 0 18px 40px rgb(28 74 67 / 0.16); }
.hero-copy { position: relative; z-index: 2; padding: 44px 48px; }.eyebrow, .section-kicker { font-size: 10px; font-weight: 800; letter-spacing: .16em; }.eyebrow { display: flex; align-items: center; gap: 9px; color: #a9d4c8; }.eyebrow-line { width: 28px; height: 1px; background: #91c9bb; }.eyebrow-index { opacity: .6; margin-left: 5px; }.hero-copy h1 { max-width: 600px; margin: 22px 0 14px; color: #fff; font-size: clamp(29px, 3.3vw, 46px); line-height: 1.1; letter-spacing: -.045em; }.hero-copy p { max-width: 560px; margin: 0; color: #c5ded7; font-size: 14px; line-height: 1.8; }.hero-actions { gap: 12px; margin-top: 28px; }.primary-action, .secondary-action { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 0 17px; border-radius: 10px; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; transition: transform .18s ease, box-shadow .18s ease, background .18s ease; }.primary-action { border: 1px solid #72c5b2; background: #68b5a5; color: #11332e; box-shadow: 0 8px 18px rgb(11 44 38 / .2); }.primary-action:hover { transform: translateY(-1px); background: #82cdbd; box-shadow: 0 12px 24px rgb(11 44 38 / .28); }.secondary-action { border: 1px solid #b4d9d0; background: transparent; color: inherit; }.hero-actions .secondary-action { color: #f0fbf8; border-color: rgb(229 249 243 / .4); }.secondary-action:hover { background: rgb(255 255 255 / .1); }.hero-proof { gap: 7px; margin-top: 22px; color: #a7cec4; font-size: 11px; }
.hero-visual { position: relative; min-height: 330px; overflow: hidden; background: radial-gradient(circle at 56% 48%, rgb(116 208 187 / .24), transparent 32%), linear-gradient(135deg, transparent 35%, rgb(255 255 255 / .04) 35%, transparent 36%); }.hero-visual::before { content: ''; position: absolute; inset: 36px 36px 32px 8px; background: repeating-linear-gradient(90deg, rgb(214 244 237 / .1) 0 1px, transparent 1px 38px), repeating-linear-gradient(0deg, rgb(214 244 237 / .1) 0 1px, transparent 1px 38px); mask-image: linear-gradient(90deg, transparent, #000 35%, #000 75%, transparent); opacity: .65; }.visual-orbit { position: absolute; border: 1px solid rgb(194 242 229 / .28); border-radius: 50%; transform: rotate(-22deg); }.visual-orbit--outer { width: 390px; height: 190px; top: 54px; left: 50px; box-shadow: 0 0 44px rgb(113 206 181 / .12); }.visual-orbit--inner { width: 270px; height: 128px; top: 88px; left: 109px; border-color: rgb(194 242 229 / .42); }.hero-grid-mark { position: absolute; width: 80px; height: 80px; right: 42px; bottom: 32px; border: 1px solid rgb(184 233 220 / .38); transform: rotate(45deg); }.signal-card { position: absolute; z-index: 2; border: 1px solid rgb(216 249 239 / .26); background: rgb(18 56 51 / .72); box-shadow: 0 14px 28px rgb(8 38 32 / .2); backdrop-filter: blur(12px); }.signal-card--primary { top: 83px; left: 116px; width: 188px; padding: 19px; border-radius: 14px; animation: float-card 6s ease-in-out infinite; }.signal-card__label { color: #a5d4c8; font-size: 9px; font-weight: 800; letter-spacing: .14em; }.signal-card__value { margin: 8px 0 3px; color: #fff; font-size: 35px; font-weight: 700; letter-spacing: -.06em; }.signal-card__value span { margin-left: 3px; color: #9dc9be; font-size: 13px; font-weight: 500; letter-spacing: 0; }.signal-card__trend { color: #a9d9c9; font-size: 10px; }.trend-arrow { color: #81e0b2; font-size: 14px; }.signal-card--secondary { right: 28px; bottom: 55px; display: flex; align-items: center; gap: 10px; padding: 10px 13px; border-radius: 10px; animation: float-card 6s 1s ease-in-out infinite; }.signal-card--secondary strong, .signal-card--secondary small { display: block; }.signal-card--secondary strong { color: #fff; font-size: 12px; }.signal-card--secondary small { margin-top: 3px; color: #a8cec5; font-size: 10px; }.signal-icon { display: grid; place-items: center; width: 29px; height: 29px; border-radius: 8px; background: #69b9a7; color: #153d37; }

.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 16px 0; }.metric-card, .panel { border: 1px solid var(--line); border-radius: 14px; background: var(--surface); box-shadow: 0 5px 16px rgb(27 62 57 / .035); }.metric-card { position: relative; overflow: hidden; padding: 17px 18px 15px; }.metric-card__head { justify-content: space-between; color: var(--ink-soft); font-size: 12px; }.metric-icon { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: var(--brand-soft); color: var(--brand-deep); }.metric-card__value { margin: 14px 0 5px; color: var(--ink); font-size: 28px; font-weight: 750; letter-spacing: -.04em; }.metric-card__foot { gap: 7px; color: var(--muted); font-size: 11px; }.metric-change { font-weight: 750; }.metric-change.positive { color: #2e8d68; }.metric-change.brand { color: var(--brand-deep); }.metric-change.warm { color: #b07832; }.metric-spark { display: flex; align-items: end; gap: 3px; height: 30px; margin-top: 11px; opacity: .85; }.metric-spark i { flex: 1; min-height: 4px; border-radius: 3px 3px 1px 1px; background: #9fd6c7; }.metric-spark--warm i { background: #e5c491; }.metric-spark--brand i { background: #72b9ab; }

.workspace-grid { display: grid; grid-template-columns: minmax(0, 1.58fr) minmax(300px, .82fr); gap: 16px; }.panel { padding: 22px; }.panel-header { justify-content: space-between; align-items: flex-start; }.section-kicker { color: var(--brand); }.panel-header h2, .resource-header h2 { margin: 6px 0 4px; color: var(--ink); font-size: 19px; letter-spacing: -.03em; }.panel-header p, .resource-header p { margin: 0; color: var(--muted); font-size: 12px; }.quiet-button { display: inline-flex; align-items: center; gap: 5px; border: 0; background: transparent; color: var(--brand-deep); font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }.pulse-chart { position: relative; display: flex; min-height: 198px; margin-top: 19px; padding: 0 0 0 28px; }.chart-y-axis { position: absolute; left: 0; top: 5px; bottom: 25px; display: flex; flex-direction: column; justify-content: space-between; color: #a0afac; font-size: 9px; }.chart-area { position: relative; flex: 1; }.chart-grid-line { position: absolute; left: 0; right: 0; border-top: 1px dashed #e5eeeb; }.chart-grid-line--one { top: 5%; }.chart-grid-line--two { top: 50%; }.chart-grid-line--three { bottom: 24px; }.chart-bars { position: absolute; inset: 0 0 0 0; display: flex; align-items: stretch; justify-content: space-around; }.chart-column { position: relative; z-index: 1; display: flex; flex: 1; flex-direction: column; align-items: center; justify-content: flex-end; gap: 8px; color: #9aaba7; font-size: 10px; }.bar-group { display: flex; align-items: end; justify-content: center; gap: 4px; width: 100%; height: 154px; }.bar { width: 10px; border-radius: 5px 5px 2px 2px; transition: height .4s var(--client-ease, ease); }.bar--reach { background: linear-gradient(180deg, #6cb9aa, #4a9b8c); }.bar--leads { background: linear-gradient(180deg, #e2bb7f, #d29b52); }.chart-legend { position: absolute; right: 0; bottom: 0; display: flex; gap: 13px; color: var(--muted); font-size: 10px; }.chart-legend span { display: inline-flex; align-items: center; gap: 5px; }.legend-dot { width: 6px; height: 6px; border-radius: 50%; }.legend-dot--reach { background: var(--brand); }.legend-dot--leads { background: var(--warm); }.pipeline-row { display: grid; grid-template-columns: 1.15fr repeat(3, 1fr); gap: 16px; margin-top: 17px; padding-top: 18px; border-top: 1px solid #edf2f0; }.pipeline-intro strong, .pipeline-intro small { display: block; }.pipeline-intro strong { margin: 5px 0 3px; font-size: 13px; }.pipeline-intro small, .pipeline-stage small { color: var(--muted); font-size: 10px; }.pipeline-stage__top { display: flex; align-items: baseline; justify-content: space-between; }.pipeline-stage__top strong { color: var(--ink); font-size: 16px; }.pipeline-stage__top span { color: var(--brand-deep); font-size: 10px; font-weight: 700; }.pipeline-track, .plan-track { height: 5px; margin: 8px 0 7px; overflow: hidden; border-radius: 999px; background: #edf3f1; }.pipeline-track i, .plan-track i { display: block; height: 100%; border-radius: inherit; }

.panel-header--compact { align-items: center; }.panel-count { color: #a6b8b4; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; }.quick-list { margin-top: 13px; }.quick-item { display: flex; align-items: center; gap: 11px; width: 100%; min-height: 58px; padding: 8px 0; border: 0; border-bottom: 1px solid #edf2f0; background: transparent; text-align: left; cursor: pointer; }.quick-item:hover .quick-item__icon { background: var(--brand); color: #fff; transform: translateY(-1px); }.quick-item__icon { display: grid; place-items: center; flex: 0 0 31px; width: 31px; height: 31px; border-radius: 9px; background: var(--brand-soft); color: var(--brand-deep); transition: all .18s ease; }.quick-item__copy { display: block; flex: 1; min-width: 0; }.quick-item__copy strong, .quick-item__copy small { display: block; }.quick-item__copy strong { color: var(--ink); font-size: 12px; }.quick-item__copy small { margin-top: 3px; color: var(--muted); font-size: 10px; }.quick-item__arrow { color: #a6b8b4; font-size: 11px; }.plan-card { margin-top: 18px; padding: 14px; border: 1px solid #d6e9e2; border-radius: 11px; background: linear-gradient(145deg, #effaf6, #f8fbf7); }.plan-card__head, .plan-card__value { display: flex; justify-content: space-between; align-items: center; }.plan-card__head { color: var(--brand-deep); font-size: 10px; font-weight: 800; letter-spacing: .08em; }.plan-badge { padding: 3px 6px; border-radius: 4px; background: #d6f1e7; color: #328061; font-size: 8px; letter-spacing: .07em; }.plan-card__value { margin-top: 15px; color: var(--ink-soft); font-size: 10px; }.plan-card__value strong { color: var(--brand-deep); font-size: 18px; }.plan-card button { display: flex; align-items: center; gap: 5px; margin-top: 11px; padding: 0; border: 0; background: transparent; color: var(--brand-deep); font: inherit; font-size: 10px; font-weight: 700; cursor: pointer; }

.resource-section { scroll-margin-top: 24px; margin-top: 32px; }.resource-header { justify-content: space-between; align-items: flex-end; }.resource-summary { gap: 10px; color: var(--muted); font-size: 11px; }.resource-summary strong { color: var(--ink); font-size: 17px; }.summary-divider { width: 1px; height: 16px; background: var(--line); }.resource-toolbar { justify-content: space-between; gap: 16px; margin: 20px 0 16px; }.tab-chips-group { display: flex; flex-wrap: wrap; gap: 5px; }.tab-chip-btn { min-height: 34px; padding: 0 12px; border: 1px solid transparent; border-radius: 8px; background: transparent; color: var(--muted); font: inherit; font-size: 11px; cursor: pointer; transition: all .16s ease; }.tab-chip-btn span { margin-left: 4px; color: #a7b6b3; }.tab-chip-btn:hover { color: var(--brand-deep); background: var(--brand-soft); }.tab-chip-btn.active { border-color: #cfe6de; background: #fff; color: var(--brand-deep); box-shadow: 0 3px 10px rgb(27 62 57 / .06); font-weight: 700; }.tab-chip-btn.active span { color: var(--brand); }.control-right { gap: 10px; }.search-input-wrap { position: relative; display: block; width: min(280px, 32vw); }.search-icon { position: absolute; left: 12px; top: 50%; z-index: 1; transform: translateY(-50%); color: #a2b1ae; font-size: 12px; }.search-input { width: 100%; height: 36px; box-sizing: border-box; padding: 0 30px 0 32px; border: 1px solid var(--line); border-radius: 9px; outline: none; background: #fff; color: var(--ink); font: inherit; font-size: 11px; transition: border .16s ease, box-shadow .16s ease; }.search-input:focus { border-color: #82bdaf; box-shadow: 0 0 0 3px rgb(74 155 140 / .12); }.clear-btn { position: absolute; top: 50%; right: 9px; transform: translateY(-50%); border: 0; background: transparent; color: #9eaeab; cursor: pointer; }.sort-select { width: 96px; color: var(--ink-soft); font-size: 11px; }.resource-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }.resource-card { overflow: hidden; border: 1px solid var(--line); border-radius: 14px; background: #fff; cursor: pointer; box-shadow: 0 5px 16px rgb(27 62 57 / .035); animation: card-in .5s both; animation-delay: var(--card-delay); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }.resource-card:hover, .resource-card:focus-visible { border-color: #afd4c9; box-shadow: 0 14px 30px rgb(27 62 57 / .11); outline: none; transform: translateY(-3px); }.resource-card__cover { position: relative; aspect-ratio: 16 / 9; overflow: hidden; background: #1e3b38; }.resource-card__cover img { width: 100%; height: 100%; display: block; object-fit: cover; transition: transform .5s cubic-bezier(.16, 1, .3, 1); }.resource-card:hover .resource-card__cover img { transform: scale(1.045); }.cover-shade { position: absolute; inset: 0; background: linear-gradient(180deg, rgb(17 46 42 / .1), rgb(17 46 42 / .66)); }.cover-badge, .cover-category { position: absolute; top: 11px; display: inline-flex; align-items: center; gap: 4px; padding: 4px 7px; border-radius: 5px; font-size: 9px; }.cover-badge { left: 11px; background: #e4f7f0; color: var(--brand-deep); font-weight: 700; }.cover-category { right: 11px; border: 1px solid rgb(255 255 255 / .35); background: rgb(16 51 47 / .42); color: #edf8f5; }.cover-actions { position: absolute; right: 12px; bottom: 12px; left: 12px; display: flex; gap: 7px; opacity: 0; transform: translateY(5px); transition: opacity .2s ease, transform .2s ease; }.resource-card:hover .cover-actions, .resource-card:focus-visible .cover-actions { opacity: 1; transform: translateY(0); }.cover-action { flex: 1; min-height: 34px; border: 1px solid rgb(255 255 255 / .48); border-radius: 7px; background: rgb(255 255 255 / .13); color: #fff; font: inherit; font-size: 10px; font-weight: 700; cursor: pointer; backdrop-filter: blur(8px); }.cover-action--primary { border-color: #91d3c0; background: #72bdab; color: #173d37; }.resource-card__body { padding: 14px 15px 15px; }.resource-card__title-row { gap: 8px; justify-content: space-between; }.resource-card h3 { overflow: hidden; margin: 0; color: var(--ink); font-size: 13px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }.like-button { display: grid; place-items: center; flex: 0 0 28px; width: 28px; height: 28px; border: 0; border-radius: 7px; background: #f3f7f5; color: #a0b1ad; cursor: pointer; }.like-button:hover { background: #e9f7f2; color: var(--brand-deep); }.like-button.liked { color: #c66a64; background: #fff0ef; }.resource-card__body p { display: -webkit-box; overflow: hidden; min-height: 34px; margin: 8px 0 14px; color: var(--muted); font-size: 11px; line-height: 1.55; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.resource-card__meta { justify-content: space-between; padding-top: 10px; border-top: 1px solid #eff3f1; color: var(--muted); font-size: 10px; }.author { gap: 6px; min-width: 0; }.author-avatar { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 50%; background: #d9eee8; color: var(--brand-deep); font-size: 9px; font-weight: 800; }.resource-stats { gap: 7px; }.resource-stats svg { color: #a6b8b4; }.empty-state { padding: 72px 20px; border: 1px dashed #cbded8; border-radius: 14px; background: #fbfdfc; text-align: center; }.empty-state__icon { display: grid; place-items: center; width: 48px; height: 48px; margin: 0 auto 14px; border-radius: 50%; background: var(--brand-soft); color: var(--brand-deep); font-size: 18px; }.empty-state h3 { margin: 0 0 6px; font-size: 15px; }.empty-state p { margin: 0 0 17px; color: var(--muted); font-size: 11px; }.empty-state .secondary-action { border-color: var(--line); color: var(--brand-deep); }

.drawer-inner { padding-bottom: 28px; }.cover-preview-large { position: relative; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 12px; background: #1e3b38; }.cover-preview-large img { width: 100%; height: 100%; object-fit: cover; }.drawer-cover-label { position: absolute; right: 12px; bottom: 11px; padding: 5px 8px; border-radius: 5px; background: rgb(20 54 49 / .68); color: #e7f6f2; font-size: 10px; backdrop-filter: blur(8px); }.drawer-heading { justify-content: space-between; gap: 16px; margin-top: 22px; }.drawer-heading h3 { margin: 7px 0 0; color: var(--ink); font-size: 20px; line-height: 1.3; }.drawer-author { color: var(--muted); font-size: 11px; white-space: nowrap; }.drawer-description { margin: 14px 0; color: var(--ink-soft); font-size: 12px; line-height: 1.75; }.drawer-stats { gap: 14px; padding: 12px 0; border-top: 1px solid #edf2f0; border-bottom: 1px solid #edf2f0; color: var(--muted); font-size: 10px; }.drawer-stats span { display: inline-flex; align-items: center; gap: 5px; }.prompt-panel { margin-top: 18px; padding: 15px; border: 1px solid #dceae5; border-radius: 11px; background: #f7fbf9; }.prompt-panel__head { justify-content: space-between; }.prompt-panel__head strong { color: var(--ink); font-size: 11px; }.prompt-panel__head button { border: 0; background: transparent; color: var(--brand-deep); font: inherit; font-size: 10px; font-weight: 700; cursor: pointer; }.prompt-panel p { margin: 11px 0 0; color: var(--ink-soft); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; line-height: 1.7; white-space: pre-wrap; }.primary-action--full { width: 100%; margin-top: 20px; }

@keyframes float-card { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }@keyframes card-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 1160px) { .command-hero { grid-template-columns: minmax(0, 1fr) 360px; }.hero-copy { padding: 38px 34px; }.resource-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }.workspace-grid { grid-template-columns: 1fr; }.command-hero { grid-template-columns: 1fr; }.hero-visual { position: absolute; right: 0; width: 45%; opacity: .85; }.hero-copy { padding-right: 36%; }.pipeline-row { grid-template-columns: 1fr repeat(3, minmax(0, 1fr)); } }
@media (max-width: 680px) { .workspace-page { padding: 0 0 32px; }.workspace-topline { align-items: flex-start; flex-direction: column; gap: 10px; }.topline-actions { justify-content: space-between; width: 100%; }.command-hero { border-radius: 15px; }.hero-copy { padding: 30px 24px 28px; }.hero-copy h1 { margin-top: 17px; font-size: 30px; }.hero-copy p { font-size: 13px; }.hero-actions { align-items: stretch; flex-direction: column; }.hero-actions button { width: 100%; }.hero-visual { display: none; }.metric-grid { gap: 10px; }.metric-card { padding: 14px; }.metric-card__value { font-size: 23px; }.panel { padding: 17px; }.resource-header { align-items: flex-start; flex-direction: column; gap: 13px; }.resource-toolbar { align-items: stretch; flex-direction: column; }.control-right { width: 100%; }.search-input-wrap { width: 100%; }.resource-grid { grid-template-columns: 1fr; }.pipeline-row { grid-template-columns: 1fr; gap: 13px; }.pipeline-intro { margin-bottom: 2px; }.pipeline-stage__top { max-width: 220px; }.chart-legend { right: 2px; }.drawer-heading { align-items: flex-start; flex-direction: column; gap: 8px; } }
@media (prefers-reduced-motion: reduce) { .signal-card, .resource-card { animation: none !important; }.resource-card, .resource-card:hover, .resource-card:focus-visible, .primary-action, .resource-card__cover img, .cover-actions, .quick-item__icon { transition: none !important; }.resource-card:hover, .resource-card:focus-visible, .primary-action:hover { transform: none; } }
</style>
