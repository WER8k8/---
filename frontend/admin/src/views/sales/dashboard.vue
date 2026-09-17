/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="sales-dashboard">
    <!-- 顶部统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="stat-card bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700">
        <div class="relative z-10">
          <p class="text-white/80 text-sm font-medium">今日新增询盘</p>
          <p class="text-3xl font-bold text-white mt-2">{{ stats.todayInquiries }}</p>
          <p class="text-white/60 text-xs mt-1">较昨日 {{ stats.inquiryTrend > 0 ? '+' : '' }}{{ stats.inquiryTrend }}%</p>
        </div>
      </div>
      <div class="stat-card bg-gradient-to-br from-emerald-500 via-emerald-600 to-emerald-700">
        <div class="relative z-10">
          <p class="text-white/80 text-sm font-medium">本月处理询盘</p>
          <p class="text-3xl font-bold text-white mt-2">{{ stats.monthlyProcessed }}</p>
          <p class="text-white/60 text-xs mt-1">完成率 {{ stats.processRate }}%</p>
        </div>
      </div>
      <div class="stat-card bg-gradient-to-br from-amber-500 via-amber-600 to-amber-700">
        <div class="relative z-10">
          <p class="text-white/80 text-sm font-medium">本月转化数</p>
          <p class="text-3xl font-bold text-white mt-2">{{ stats.monthlyConversion }}</p>
          <p class="text-white/60 text-xs mt-1">转化率 {{ stats.conversionRate }}%</p>
        </div>
      </div>
      <div class="stat-card bg-gradient-to-br from-purple-500 via-purple-600 to-purple-700">
        <div class="relative z-10">
          <p class="text-white/80 text-sm font-medium">累计客户线索</p>
          <p class="text-3xl font-bold text-white mt-2">{{ stats.totalLeads }}</p>
          <p class="text-white/60 text-xs mt-1">新增 {{ stats.newLeadsThisMonth }} 条本月</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 待跟进客户列表 -->
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">待跟进客户</h3>
            <p class="text-sm text-gray-400">共 {{ pendingLeads.length }} 位客户待联系</p>
          </div>
        </div>
        <div class="space-y-3">
          <div v-for="(lead, index) in pendingLeads" :key="index"
            class="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100">
            <div class="flex items-center gap-4 min-w-0 flex-1">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center flex-shrink-0">
                <span class="font-bold text-blue-600 text-sm">{{ lead.name.charAt(0) }}</span>
              </div>
              <div class="min-w-0 flex-1">
                <p class="font-medium text-gray-900 truncate">{{ lead.name }}</p>
                <p class="text-xs text-gray-400">{{ lead.phone }}</p>
              </div>
              <div class="hidden sm:block min-w-0 flex-1">
                <p class="text-sm text-gray-600 truncate">{{ lead.product }}</p>
                <p class="text-xs text-gray-400">{{ lead.time }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <a :href="`tel:${lead.phone}`" class="inline-flex px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors items-center gap-1 no-underline" @click.stop>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                拨号
              </a>
              <button class="px-3 py-1.5 text-xs font-medium rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors flex items-center gap-1" @click="copyWechat(lead.wechat)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                微信
              </button>
            </div>
          </div>
          <div v-if="!pendingLeads.length" class="text-center py-8 text-gray-400 text-sm">
            暂无待跟进客户
          </div>
        </div>
      </div>

      <!-- 本月业绩统计 -->
      <div class="bg-white rounded-2xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">本月业绩</h3>
            <p class="text-sm text-gray-400">{{ currentMonth }} 月统计</p>
          </div>
        </div>
        <div class="space-y-5">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">询盘处理</span>
              <span class="font-medium text-gray-900">{{ stats.monthlyProcessed }} / {{ stats.monthlyInquiryTarget }}</span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-blue-500 transition-all" :style="{ width: monthlyProcessPercent + '%' }"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">客户转化</span>
              <span class="font-medium text-gray-900">{{ stats.monthlyConversion }} / {{ stats.monthlyConversionTarget }}</span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500 transition-all" :style="{ width: monthlyConversionPercent + '%' }"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">线索新增</span>
              <span class="font-medium text-gray-900">{{ stats.newLeadsThisMonth }}</span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-amber-500 transition-all" :style="{ width: '100%' }"></div>
            </div>
          </div>
        </div>
        <div class="mt-6 pt-6 border-t border-gray-100">
          <div class="grid grid-cols-2 gap-4 text-center">
            <div>
              <p class="text-2xl font-bold text-gray-900">{{ stats.avgResponseTime }}</p>
              <p class="text-xs text-gray-400 mt-1">平均响应</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-gray-900">{{ stats.satisfaction }}</p>
              <p class="text-xs text-gray-400 mt-1">客户满意度</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

interface Lead {
  name: string
  phone: string
  wechat: string
  product: string
  time: string
  status: string
}

const tk = () => getAuthToken()
const authHeaders = () => ({ Authorization: `Bearer ${tk()}` })

const currentMonth = computed(() => new Date().getMonth() + 1)

const stats = ref({
  todayInquiries: 0,
  inquiryTrend: 0,
  monthlyProcessed: 0,
  monthlyInquiryTarget: 120,
  processRate: 0,
  monthlyConversion: 0,
  monthlyConversionTarget: 30,
  conversionRate: 0,
  totalLeads: 0,
  newLeadsThisMonth: 0,
  avgResponseTime: '—',
  satisfaction: '—',
})

const monthlyProcessPercent = computed(() =>
  Math.min(100, Math.round((stats.value.monthlyProcessed / stats.value.monthlyInquiryTarget) * 100))
)
const monthlyConversionPercent = computed(() =>
  Math.min(100, Math.round((stats.value.monthlyConversion / stats.value.monthlyConversionTarget) * 100))
)

const pendingLeads = ref<Lead[]>([])

// ===== API 数据加载 =====
async function fetchPendingInquiries() {
  try {
    const res = await fetch('/api/v1/inquiries/?status=pending', { headers: authHeaders() })
    const body = await res.json()
    if (body.code === 0 && Array.isArray(body.data)) {
      pendingLeads.value = body.data.map((item: any) => ({
        name: item.name || item.contact_name || '',
        phone: item.phone || item.mobile || '',
        wechat: item.wechat || '',
        product: item.product || item.product_name || '',
        time: item.time || item.created_at || '',
        status: item.status || 'new',
      }))
    }
  } catch { /* 静默处理 */ }
}

async function fetchProcessingInquiries() {
  // 拉取处理中的询盘（当 pending 不足时也可作为数据源）
  try {
    const res = await fetch('/api/v1/inquiries/?status=processing', { headers: authHeaders() })
    const body = await res.json()
    if (body.code === 0 && Array.isArray(body.data) && pendingLeads.value.length === 0) {
      pendingLeads.value = body.data.map((item: any) => ({
        name: item.name || item.contact_name || '',
        phone: item.phone || item.mobile || '',
        wechat: item.wechat || '',
        product: item.product || item.product_name || '',
        time: item.time || item.created_at || '',
        status: item.status || 'processing',
      }))
    }
  } catch { /* 静默处理 */ }
}

async function fetchSalesStats() {
  try {
    const res = await fetch('/api/v1/analytics/sales', { headers: authHeaders() })
    const body = await res.json()
    if (body.code === 0 && body.data) {
      const d = body.data
      stats.value = {
        todayInquiries: d.todayInquiries ?? stats.value.todayInquiries,
        inquiryTrend: d.inquiryTrend ?? stats.value.inquiryTrend,
        monthlyProcessed: d.monthlyProcessed ?? stats.value.monthlyProcessed,
        monthlyInquiryTarget: d.monthlyInquiryTarget ?? stats.value.monthlyInquiryTarget,
        processRate: d.processRate ?? stats.value.processRate,
        monthlyConversion: d.monthlyConversion ?? stats.value.monthlyConversion,
        monthlyConversionTarget: d.monthlyConversionTarget ?? stats.value.monthlyConversionTarget,
        conversionRate: d.conversionRate ?? stats.value.conversionRate,
        totalLeads: d.totalLeads ?? stats.value.totalLeads,
        newLeadsThisMonth: d.newLeadsThisMonth ?? stats.value.newLeadsThisMonth,
        avgResponseTime: d.avgResponseTime ?? stats.value.avgResponseTime,
        satisfaction: d.satisfaction ?? stats.value.satisfaction,
      }
    }
  } catch { /* 静默处理 */ }
}

function callLead(phone: string) {
  if (phone) {
    window.location.href = `tel:${phone}`
  } else {
    message.warning('无电话号码')
  }
}

function copyWechat(wechat: string) {
  navigator.clipboard.writeText(wechat).then(() => {
    message.success(`微信号已复制: ${wechat}`)
  }).catch(() => {
    message.success(`微信号: ${wechat}`)
  })
}

onMounted(async () => {
  await Promise.all([
    fetchPendingInquiries(),
    fetchProcessingInquiries(),
    fetchSalesStats(),
  ])
})
</script>

<style scoped>
.sales-dashboard {
  animation: pageIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes pageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.stat-card {
  position: relative;
  padding: 1.5rem;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
.no-underline { text-decoration: none; }
</style>
