/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="搜客执行台" subtitle="从产品词到可运营客户机会的完整工作流" surface="elevated">
 <template #actions>
 <a-button type="primary" @click="currentStep = 0">
 <SearchOutlined />
 新建搜客
</a-button>
 <a-button @click="exportResults">
 <ExportOutlined />
 导出结果
</a-button>
</template>

 <div class="prospecting-workspace">
 <!-- 步骤条 -->
 <a-steps :current="currentStep" class="workspace-steps" size="small">
 <a-step title="搜客条件" description="输入产品词和市场" />
 <a-step title="候选结果" description="查看线索列表" />
 <a-step title="发开发信" description="写信并发送" />
 <a-step title="追踪状态" description="打开/回复追踪" />
</a-steps>

 <!-- Step 1: 搜客条件 -->
 <div v-if="currentStep === 0" class="step-panel">
 <a-row :gutter="24">
 <a-col :span="16">
 <a-card title="搜客条件" size="small">
 <a-form :model="searchForm" layout="vertical">
 <a-form-item label="产品关键词" required>
 <a-select
 v-model:value="searchForm.keywords"
 mode="tags"
 placeholder="输入产品关键词，如：pressure transmitter, flow meter"
 />
</a-form-item>
 <a-row :gutter="16">
 <a-col :span="12">
 <a-form-item label="目标市场">
 <a-select
 v-model:value="searchForm.countries"
 mode="multiple"
 placeholder="选择目标市场"
 :options="countryOptions"
 />
</a-form-item>
</a-col>
 <a-col :span="12">
 <a-form-item label="客户类型">
 <a-select v-model:value="searchForm.customerType" placeholder="选择客户类型">
 <a-select-option value="distributor">经销商</a-select-option>
 <a-select-option value="integrator">系统集成商</a-select-option>
 <a-select-option value="oem">OEM 设备厂</a-select-option>
 <a-select-option value="epc">EPC 工程承包商</a-select-option>
 <a-select-option value="factory">终端工厂</a-select-option>
</a-select>
</a-form-item>
</a-col>
</a-row>
 <a-form-item label="排除词">
 <a-select
 v-model:value="searchForm.excludeWords"
 mode="tags"
 placeholder="输入排除词"
 :default-value="['job', 'used', 'repair', 'school', 'news']"
 />
</a-form-item>
 <a-form-item>
 <a-space>
 <a-button type="primary" :loading="searching" @click="startSearch">
 <SearchOutlined />
 开始搜客
</a-button>
 <a-button @click="resetSearchForm">重置</a-button>
</a-space>
</a-form-item>
</a-form>
</a-card>
</a-col>
 <a-col :span="8">
 <SearchSyntaxPreview
 :keywords="searchForm.keywords"
 :countries="searchForm.countries"
 :customer-type="searchForm.customerType"
 :search-source="searchForm.searchSource"
 @syntax-generated="onSyntaxGenerated"
 />
</a-col>
</a-row>
</div>

 <!-- Step 2: 候选结果 -->
 <div v-if="currentStep === 1" class="step-panel">
 <a-card title="候选线索" size="small">
 <template #extra>
 <a-space>
 <a-input-search
 v-model:value="resultFilter"
 placeholder="搜索公司名/国家/行业"
 style="width: 250px"
 @search="filterResults"
 />
 <a-select v-model:value="resultSort" style="width: 150px">
 <a-select-option value="score">按评分</a-select-option>
 <a-select-option value="recent">按时间</a-select-option>
 <a-select-option value="country">按国家</a-select-option>
</a-select>
</a-space>
</template>

 <a-spin :spinning="loadingResults">
 <div class="result-list">
 <div
 v-for="lead in filteredLeads"
 :key="lead.id"
 class="result-card"
 :class="{ 'selected': selectedLeads.includes(lead.id) }"
 @click="toggleSelect(lead.id)"
 >
 <div class="card-header">
 <div class="card-info">
 <a-checkbox :checked="selectedLeads.includes(lead.id)" />
 <div class="company-info">
 <div class="company-name">{{ lead.companyName }}</div>
 <div class="company-meta">
 <a-tag size="small">{{ lead.country }}</a-tag>
 <span>{{ lead.industry }}</span>
</div>
</div>
</div>
 <div class="card-score">
 <a-progress
 type="circle"
 :percent="lead.overallScore"
 :size="50"
 :stroke-color="getScoreColor(lead.overallScore)"
 />
</div>
</div>

 <div class="card-body">
 <div class="evidence-summary">
 <span class="evidence-count">
 <FileSearchOutlined />
 {{ lead.evidenceCount || 0 }} 条证据
</span>
 <span v-if="lead.email" class="email-tag">
 <MailOutlined />
 {{ lead.email }}
</span>
</div>
</div>

 <div class="card-actions">
 <a-button size="small" @click.stop="viewLeadDetail(lead)">
 <EyeOutlined />
 详情
</a-button>
 <a-button size="small" type="primary" @click.stop="openOutreach(lead)">
 <SendOutlined />
 发信
</a-button>
 <a-button size="small" @click.stop="convertToCustomer(lead)">
 <SwapOutlined />
 转客户
</a-button>
</div>
</div>

 <a-empty v-if="filteredLeads.length === 0" description="暂无候选线索" />
</div>
</a-spin>

 <div class="batch-actions" v-if="selectedLeads.length > 0">
 <a-space>
 <span>已选 {{ selectedLeads.length }} 条</span>
 <a-button type="primary" size="small" @click="batchConvert">批量转客户</a-button>
 <a-button size="small" @click="batchExport">批量导出</a-button>
</a-space>
</div>
</a-card>

 <!-- 详情抽屉 -->
 <a-drawer
 v-model:open="showDetailDrawer"
 title="线索详情"
 width="640"
 placement="right"
 >
 <a-spin :spinning="detailLoading">
 <div v-if="detailError" class="detail-error">
 <a-alert type="error" show-icon :message="detailError" />
 <a-button size="small" class="detail-retry" @click="reloadDetail">重试</a-button>
 </div>

 <div v-if="currentLead" class="lead-detail">
 <div class="detail-header">
 <h3>{{ currentLead.companyName || '未命名线索' }}</h3>
 <a-space>
 <a-tag :color="currentLead.stageInfo.color">{{ currentLead.stageInfo.label }}</a-tag>
 <a-tag :color="getScoreColor(currentLead.overallScore)">
 {{ currentLead.overallScore }} 分
 </a-tag>
 </a-space>
 </div>

 <!-- 阶段进度：当前阶段在 7 段主链上的位置 -->
 <div v-if="currentLead.stageInfo.index >= 0" class="stage-track">
 <div
 v-for="(s, i) in STAGE_ORDER"
 :key="s"
 class="stage-node"
 :class="{
 'is-done': i < currentLead.stageInfo.index,
 'is-current': i === currentLead.stageInfo.index,
 }"
 >
 <span class="stage-dot"></span>
 <span class="stage-name">{{ STAGE_LABELS[s] }}</span>
 </div>
 </div>
 <a-alert
 v-else
 class="mt-2"
 type="warning"
 show-icon
 :message="`当前阶段：${currentLead.stageInfo.label}`"
 />

 <a-divider>来源与基本信息</a-divider>
 <a-descriptions :column="2" size="small" bordered>
 <a-descriptions-item label="来源">
 {{ SOURCE_LABELS[currentLead.source] || currentLead.source || '未知来源' }}
 </a-descriptions-item>
 <a-descriptions-item label="当前阶段">
 {{ currentLead.stageInfo.label }}
 </a-descriptions-item>
 <a-descriptions-item label="国家">{{ currentLead.country || '—' }}</a-descriptions-item>
 <a-descriptions-item label="行业">{{ currentLead.industry || '—' }}</a-descriptions-item>
 <a-descriptions-item label="邮箱">{{ currentLead.email || '—' }}</a-descriptions-item>
 <a-descriptions-item label="电话">{{ currentLead.phone || '—' }}</a-descriptions-item>
 <a-descriptions-item label="网站">{{ currentLead.website || '—' }}</a-descriptions-item>
 <a-descriptions-item label="LinkedIn">{{ currentLead.linkedinUrl || '—' }}</a-descriptions-item>
 </a-descriptions>

 <!-- 评分理由（4 维） -->
 <a-divider>评分理由（4 维）</a-divider>
 <ScoreRadar :scores="currentLead.scoreBreakdown" />

 <!-- 证据链 -->
 <a-divider>证据链</a-divider>
 <EvidenceChain :evidences="currentLead.evidenceChain" />

 <!-- 触达记录 -->
 <a-divider>触达记录</a-divider>
 <template v-if="currentLead.hasContactData">
 <a-descriptions :column="2" size="small" bordered>
 <a-descriptions-item label="触达次数">{{ fmtNum(currentLead.contactCount) }}</a-descriptions-item>
 <a-descriptions-item label="上次触达">{{ formatTime(currentLead.lastContactedAt) }}</a-descriptions-item>
 <a-descriptions-item label="上次触达渠道">{{ currentLead.lastContactedChannel || '—' }}</a-descriptions-item>
 <a-descriptions-item label="打开/点击">{{ fmtNum(currentLead.openCount) }} / {{ fmtNum(currentLead.clickCount) }}</a-descriptions-item>
 <a-descriptions-item label="回复次数">{{ fmtNum(currentLead.replyCount) }}</a-descriptions-item>
 <a-descriptions-item label="上次回复">{{ formatTime(currentLead.lastRepliedAt) }}</a-descriptions-item>
 </a-descriptions>
 </template>
 <a-empty
 v-else
 :image="null"
 description="后端未返回触达字段，暂无法展示（需接口补齐）"
 />
 </div>
 </a-spin>
 </a-drawer>
</div>

 <!-- Step 3: 发开发信（占位，跳转 OutreachEditor） -->
 <div v-if="currentStep === 2" class="step-panel">
 <a-result
 status="info"
 title="准备发开发信"
 sub-title="点击下方按钮跳转到写信工作台"
 >
 <template #extra>
 <a-space>
 <a-button type="primary" @click="goToOutreach">打开写信工作台</a-button>
 <a-button @click="currentStep = 1">返回结果</a-button>
</a-space>
</template>
</a-result>
</div>

 <!-- Step 4: 追踪状态 -->
 <div v-if="currentStep === 3" class="step-panel">
 <a-card title="邮件追踪" size="small">
 <a-table :columns="trackingColumns" :data-source="trackingData" size="small">
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'status'">
 <a-badge
 :status="record.opened ? 'success' : 'default'"
 :text="record.opened ? '已打开' : '未打开'"
 />
</template>
 <template v-else-if="column.key === 'openedAt'">
 {{ record.openedAt ? formatTime(record.openedAt) : '-' }}
</template>
</template>
</a-table>
</a-card>
</div>
</div>
</YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
 SearchOutlined,
 ExportOutlined,
 FileSearchOutlined,
 MailOutlined,
 EyeOutlined,
 SendOutlined,
 SwapOutlined
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import SearchSyntaxPreview from '@/components/whatsfinds/SearchSyntaxPreview.vue'
import ScoreRadar from '@/components/whatsfinds/ScoreRadar.vue'
import EvidenceChain from '@/components/whatsfinds/EvidenceChain.vue'
import { apiGet, apiPost } from '@/utils/api'

const router = useRouter()

// 步骤
const currentStep = ref(0)

// 搜索表单
const searchForm = reactive({
 keywords: [] as string[],
 countries: [] as string[],
 customerType: '',
 searchSource: 'google',
 excludeWords: ['job', 'used', 'repair', 'school', 'news']
})

// 搜索状态
const searching = ref(false)
const generatedSyntax = ref('')

// 结果
const loadingResults = ref(false)
const leads = ref<any[]>([])
const selectedLeads = ref<string[]>([])
const resultFilter = ref('')
const resultSort = ref('score')

// 详情
const showDetailDrawer = ref(false)
const currentLead = ref<any>(null)
const detailLoading = ref(false)
const detailError = ref('')
let detailAbort: AbortController | null = null

onUnmounted(() => {
  detailAbort?.abort()
})

// 线索来源（LeadSource 枚举）中文标签
const SOURCE_LABELS: Record<string, string> = {
  google_cse: 'Google 搜索',
  website_scrape: '网站抓取',
  hunter_io: 'Hunter.io',
  apollo_io: 'Apollo.io',
  linkedin: 'LinkedIn',
  whatsapp: 'WhatsApp',
  reddit: 'Reddit',
  tiktok: 'TikTok',
  quora: 'Quora',
  manual_import: '手动导入',
  referral: '客户推荐',
}

// 线索阶段（LeadStatus 枚举）中文标签 + 主链顺序
const STAGE_ORDER = ['discovered', 'enriched', 'verified', 'qualified', 'contacted', 'engaged', 'converted']
const STAGE_LABELS: Record<string, string> = {
  discovered: '刚发现',
  enriched: '已补全',
  verified: '已验证',
  qualified: '已认证',
  contacted: '已联系',
  engaged: '有互动',
  converted: '已转化',
  archived: '已归档',
  invalid: '无效',
}

function stageInfo(status?: string): { label: string; color: string; index: number } {
  const key = String(status || '').toLowerCase()
  const label = STAGE_LABELS[key] || key || '未知'
  const idx = STAGE_ORDER.indexOf(key)
  if (idx >= 0) {
    const colors = ['default', 'cyan', 'blue', 'geekblue', 'orange', 'purple', 'green']
    return { label, color: colors[idx] || 'default', index: idx }
  }
  // 归档 / 无效等离链终态
  return { label, color: key === 'invalid' ? 'error' : 'default', index: -1 }
}

// 证据链字段归一化：兼容后端 snake_case 与数值型置信度
function normalizeConfidence(raw: unknown): 'high' | 'medium' | 'low' {
  if (typeof raw === 'string') {
    const s = raw.toLowerCase()
    if (s === 'high' || s === 'medium' || s === 'low') return s
    if (s === 'high_confidence' || s === 'verified') return 'high'
    return 'medium'
  }
  if (typeof raw === 'number') {
    const v = raw > 1 ? raw / 100 : raw
    if (v >= 0.7) return 'high'
    if (v >= 0.4) return 'medium'
    return 'low'
  }
  return 'medium'
}

const EVIDENCE_TYPES = ['website', 'email', 'contact', 'certification', 'search', 'linkedin']
function normalizeEvidenceChain(raw: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(raw)) return []
  return raw.map((item) => {
    const it = (item || {}) as Record<string, unknown>
    const type = String(it.type || 'search')
    return {
      type: EVIDENCE_TYPES.includes(type) ? type : 'search',
      content: String(it.content || ''),
      sourceUrl: (it.sourceUrl as string) || (it.source_url as string) || '',
      confidence: normalizeConfidence(it.confidence),
      timestamp: (it.timestamp as string) || '',
      details: typeof it.details === 'string' ? it.details : it.details ? JSON.stringify(it.details) : '',
    }
  })
}

// 详情字段归一化：把 detail 接口返回的 {match,email,evidence,contact} 转成雷达图所需数组
function normalizeLeadDetail(d: any) {
  const sb = d?.scoreBreakdown || {}
  const scoreBreakdown = [
    { label: '匹配度', value: Number(sb.match ?? d?.scoreMatch ?? 0), description: '产品词 + 行业 + 国家匹配（权重 30%）' },
    { label: '邮箱可信度', value: Number(sb.email ?? d?.scoreEmail ?? 0), description: '邮箱验证状态（权重 25%）' },
    { label: '证据完整度', value: Number(sb.evidence ?? d?.scoreEvidence ?? 0), description: '证据链条数与置信度（权重 25%）' },
    { label: '联系人完整度', value: Number(sb.contact ?? d?.scoreContact ?? 0), description: '关键人可达性（权重 20%）' },
  ]
  // 触达字段是否由后端提供：全部缺省时如实提示，不伪造 0
  const hasContactData =
  d?.contactCount != null
    || d?.contact_count != null
    || d?.lastContactedAt != null
    || d?.last_contacted_at != null
    || d?.lastContactedChannel != null
    || d?.last_contacted_channel != null
    || d?.openCount != null
    || d?.open_count != null
    || d?.clickCount != null
    || d?.click_count != null
    || d?.replyCount != null
    || d?.reply_count != null
    || d?.lastRepliedAt != null
    || d?.last_replied_at != null
  return {
    ...d,
    overallScore: Number(d?.overallScore ?? sb.overall ?? 0),
    source: d?.source ?? '',
    status: d?.status ?? '',
    stageInfo: stageInfo(d?.status),
    scoreBreakdown,
    evidenceChain: normalizeEvidenceChain(d?.evidenceChain ?? d?.evidence_chain),
    hasContactData,
    contactCount: d?.contactCount ?? d?.contact_count ?? null,
    lastContactedAt: d?.lastContactedAt ?? d?.last_contacted_at ?? '',
    lastContactedChannel: d?.lastContactedChannel ?? d?.last_contacted_channel ?? '',
    openCount: d?.openCount ?? d?.open_count ?? null,
    clickCount: d?.clickCount ?? d?.click_count ?? null,
    replyCount: d?.replyCount ?? d?.reply_count ?? null,
    lastRepliedAt: d?.lastRepliedAt ?? d?.last_replied_at ?? '',
  }
}

// 追踪
const trackingData = ref<any[]>([])

// 选项
const countryOptions = [
 { value: 'Germany', label: '德国' },
 { value: 'UK', label: '英国' },
 { value: 'USA', label: '美国' },
 { value: 'UAE', label: '阿联酋' },
 { value: 'Turkey', label: '土耳其' },
 { value: 'Japan', label: '日本' },
 { value: 'India', label: '印度' },
 { value: 'Brazil', label: '巴西' }
]

const trackingColumns = [
 { title: '公司', dataIndex: 'companyName', key: 'companyName' },
 { title: '邮箱', dataIndex: 'email', key: 'email' },
 { title: '状态', key: 'status' },
 { title: '打开时间', key: 'openedAt' },
 { title: '打开次数', dataIndex: 'openCount', key: 'openCount' }
]

// 计算属性
const filteredLeads = computed(() => {
 let result = [...leads.value]
 if (resultFilter.value) {
 const filter = resultFilter.value.toLowerCase()
 result = result.filter(l =>
 (l.companyName || '').toLowerCase().includes(filter) ||
 (l.country || '').toLowerCase().includes(filter) ||
 (l.industry || '').toLowerCase().includes(filter)
 )
 }
 if (resultSort.value === 'score') {
 result.sort((a, b) => (b.overallScore || 0) - (a.overallScore || 0))
 } else if (resultSort.value === 'recent') {
 result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
 }
 return result
})

// 搜客
async function startSearch() {
 if (searchForm.keywords.length === 0) {
 message.warning('请输入至少一个产品关键词')
 return
 }
 searching.value = true
 try {
 const res = await apiPost('/workspace/prospecting/search', searchForm)
 leads.value = res.leads || []
 currentStep.value = 1
 message.success(`找到 ${leads.value.length} 条候选线索`)
 } catch (error) {
 message.error('搜客失败')
 } finally {
 searching.value = false
 }
}

function resetSearchForm() {
 searchForm.keywords = []
 searchForm.countries = []
 searchForm.customerType = ''
 searchForm.excludeWords = ['job', 'used', 'repair', 'school', 'news']
}

function onSyntaxGenerated(syntax: string) {
 generatedSyntax.value = syntax
}

// 结果操作
function toggleSelect(id: string) {
 const index = selectedLeads.value.indexOf(id)
 if (index === -1) {
 selectedLeads.value.push(id)
 } else {
 selectedLeads.value.splice(index, 1)
 }
}

function viewLeadDetail(lead: any) {
  // 先用列表行的真实字段即时渲染基础信息（不编造），再拉详情补全证据链/评分/触达
  currentLead.value = normalizeLeadDetail(lead)
  showDetailDrawer.value = true
  void loadLeadDetail(lead.id)
}

function reloadDetail() {
  if (currentLead.value?.id) void loadLeadDetail(currentLead.value.id)
}

async function loadLeadDetail(leadId: string) {
  detailLoading.value = true
  detailError.value = ''
  detailAbort?.abort()
  const controller = new AbortController()
  detailAbort = controller
  try {
    const res = await apiGet(`/workspace/prospecting/leads/${encodeURIComponent(leadId)}`, undefined, {
      signal: controller.signal,
    })
    if (controller.signal.aborted) return
    currentLead.value = normalizeLeadDetail(res)
  } catch (error) {
    if (controller.signal.aborted) return
    detailError.value = error instanceof Error ? error.message : '线索详情加载失败，请重试'
  } finally {
    if (detailAbort === controller) detailLoading.value = false
  }
}

function openOutreach(lead: any) {
 router.push({ path: '/workspace/outreach', query: { lead_id: lead.id } })
}

async function convertToCustomer(lead: any) {
 try {
 await apiPost(`/workspace/prospecting/leads/${lead.id}/convert`)
 message.success('已转为客户')
 leads.value = leads.value.filter(l => l.id !== lead.id)
 } catch (error) {
 message.error('转换失败')
 }
}

function goToOutreach() {
 router.push('/workspace/outreach')
}

async function exportResults() {
 message.warning('导出功能尚未开放')
}

function batchConvert() {
 message.warning('批量转换功能尚未开放')
}

function batchExport() {
 message.warning('批量导出功能尚未开放')
}

function filterResults() {}

function getScoreColor(score: number): string {
 if (score >= 80) return '#52c41a'
 if (score >= 60) return '#1890ff'
 if (score >= 40) return '#faad14'
 return '#ff4d4f'
}

function fmtNum(v: unknown): string {
  return v === null || v === undefined ? '—' : String(v)
}

function formatTime(timestamp: string): string {
 if (!timestamp) return '—'
 try {
 const date = new Date(timestamp)
 if (Number.isNaN(date.getTime())) return '—'
 return date.toLocaleString('zh-CN')
 } catch {
 return timestamp
 }
}

onMounted(() => {
 // 加载已有线索
 loadLeads()
})

async function loadLeads() {
 loadingResults.value = true
 try {
 const res = await apiGet('/workspace/prospecting/leads')
 leads.value = res.items || []
 } catch (error) {
 console.error('加载线索失败:', error)
 } finally {
 loadingResults.value = false
 }
}
</script>

<style scoped lang="scss">
.prospecting-workspace {
 .workspace-steps {
 margin-bottom: 24px;
 }

 .step-panel {
 min-height: 400px;
 }

 .result-list {
 display: flex;
 flex-direction: column;
 gap: 12px;
 }

 .result-card {
 border: 1px solid #f0f0f0;
 border-radius: 8px;
 padding: 16px;
 cursor: pointer;
 transition: all 0.2s;

 &:hover {
 border-color: #1890ff;
 box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
 }

 &.selected {
 border-color: #1890ff;
 background: #f6f8ff;
 }

 .card-header {
 display: flex;
 justify-content: space-between;
 align-items: center;
 margin-bottom: 12px;

 .card-info {
 display: flex;
 align-items: center;
 gap: 12px;

 .company-info {
 .company-name {
 font-weight: 500;
 font-size: 14px;
 color: #333;
 }

 .company-meta {
 display: flex;
 align-items: center;
 gap: 8px;
 margin-top: 4px;
 font-size: 12px;
 color: #888;
 }
 }
 }
 }

 .card-body {
 .evidence-summary {
 display: flex;
 align-items: center;
 gap: 16px;
 font-size: 12px;
 color: #666;

 .evidence-count,
 .email-tag {
 display: flex;
 align-items: center;
 gap: 4px;
 }
 }
 }

 .card-actions {
 display: flex;
 gap: 8px;
 margin-top: 12px;
 padding-top: 12px;
 border-top: 1px solid #f0f0f0;
 }
 }

 .batch-actions {
 margin-top: 16px;
 padding: 12px;
 background: #f6f8ff;
 border-radius: 6px;
 display: flex;
 justify-content: space-between;
 align-items: center;
 }

 .detail-error {
 margin-bottom: 12px;

 .detail-retry {
 margin-top: 8px;
 }
 }

 .lead-detail {
 .detail-header {
 display: flex;
 justify-content: space-between;
 align-items: center;
 gap: 8px;

 h3 {
 margin: 0;
 min-width: 0;
 overflow: hidden;
 text-overflow: ellipsis;
 white-space: nowrap;
 word-break: break-word;
 }
 }

 .stage-track {
 display: flex;
 flex-wrap: wrap;
 gap: 6px 12px;
 margin-top: 12px;
 padding: 10px 12px;
 background: #fafafa;
 border-radius: 6px;

 .stage-node {
 display: flex;
 align-items: center;
 gap: 6px;
 font-size: 12px;
 color: #999;

 .stage-dot {
 width: 8px;
 height: 8px;
 border-radius: 50%;
 background: #d9d9d9;
 flex-shrink: 0;
 }

 &.is-done {
 color: var(--uj-success, #52c41a);
 .stage-dot { background: var(--uj-success, #52c41a); }
 }

 &.is-current {
 color: var(--uj-brand, #4a9b8c);
 font-weight: 600;
 .stage-dot { background: var(--uj-brand, #4a9b8c); box-shadow: 0 0 0 3px var(--uj-brand-muted, rgb(74 155 140 / 0.18)); }
 }
 }
 }
 }
}
</style>
