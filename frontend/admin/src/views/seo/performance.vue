/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="SEO 性能与安全监控" subtitle="网站性能指标、SEO健康检查与安全审计" surface="elevated">
    <YdHonestDataBanner
      v-if="dataTrust === 'empty'"
      level="needs-config"
      title="暂无性能监控数据"
      :description="loadError || '站点未上线或未跑过 PageSpeed/安全探测时，此处不会显示虚构指标。'"
    />
    <!-- 标签页切换 -->
    <div class="flex items-center gap-3 mb-6">
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'metrics'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="activeTab = 'metrics'"
      >
        性能指标
      </button>
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'security'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="activeTab = 'security'"
      >
        安全审计
      </button>
    </div>

    <!-- 性能指标 -->
    <div
      v-if="activeTab === 'metrics'"
      class="space-y-6"
    >
      <a-empty v-if="dataTrust === 'empty' && !hasMetrics()" description="暂无性能指标。请先对租户站点执行 SEO/性能探测。" />
      <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">
                PageSpeed 评分
              </p>
              <p class="text-3xl font-bold text-green-500">
                {{ pageSpeedScore ?? '—' }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span class="text-green-600 text-lg">{{ pageSpeedScore != null ? (pageSpeedScore >= 90 ? 'A' : pageSpeedScore >= 70 ? 'B' : 'C') : '—' }}</span>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">
                LCP (最大内容绘制)
              </p>
              <p class="text-3xl font-bold text-blue-500">
                {{ lcp ?? '—' }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <CheckOutlined class="text-blue-600 text-lg" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">
                FID (首次输入延迟)
              </p>
              <p class="text-3xl font-bold text-purple-500">
                {{ fid ?? '—' }}
              </p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <CheckOutlined class="text-purple-600 text-lg" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">
                CLS (累积布局偏移)
              </p>
              <p class="text-3xl font-bold text-orange-500">
                {{ cls ?? '—' }}
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <CheckOutlined class="text-orange-600 text-lg" />
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-lg font-semibold mb-4">
          SEO 健康检查
        </h3>
        <div class="space-y-3">
          <div v-for="check in seoChecks" :key="check.name" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span class="text-sm">{{ check.name }}</span>
            <span class="text-sm font-medium" :class="check.passed ? 'text-green-600' : 'text-yellow-600'">
              {{ check.passed ? '通过' : (check.label || '需更新') }}
            </span>
          </div>
        </div>
      </div>
      </template>
    </div>

    <!-- 安全审计 -->
    <div
      v-if="activeTab === 'security'"
      class="space-y-6"
    >
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <p class="text-sm text-gray-500">
            安全评分
          </p>
          <p class="text-3xl font-bold text-green-500">
            {{ securityScore }}
          </p>
          <p class="text-xs text-gray-400 mt-1">
            SSL Labs 评级
          </p>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <p class="text-sm text-gray-500">
            漏洞扫描
          </p>
          <p class="text-3xl font-bold text-blue-500">
            {{ vulnCount }}
          </p>
          <p class="text-xs text-gray-400 mt-1">
            已知漏洞
          </p>
        </div>
        <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <p class="text-sm text-gray-500">
            证书到期
          </p>
          <p class="text-3xl font-bold text-purple-500">
            {{ certDays }}天
          </p>
          <p class="text-xs text-gray-400 mt-1">
            剩余有效期
          </p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-lg font-semibold mb-4">
          安全审计日志
        </h3>
        <div class="space-y-2">
          <div v-for="(log, idx) in auditLogs" :key="idx" class="flex items-center gap-3 text-sm text-gray-500 p-2">
            <span class="w-32 text-gray-400">{{ log.date }}</span>
            <span class="w-16 px-2 py-0.5 rounded text-xs" :class="log.status === '通过' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">{{ log.status }}</span>
            <span>{{ log.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { CheckOutlined } from '@ant-design/icons-vue';
import { YdPage, YdHonestDataBanner } from '@/components/youding';
import { getAuthToken } from '@/utils/api';

const activeTab = ref('metrics');
const dataTrust = ref<'live' | 'empty'>('empty');
const loadError = ref('');

// 无实盘时展示空态，不预填示意数字
const pageSpeedScore = ref<number | null>(null)
const lcp = ref<string | null>(null)
const fid = ref<string | null>(null)
const cls = ref<string | null>(null)
const securityScore = ref<string | null>(null)
const vulnCount = ref<number | null>(null)
const certDays = ref<number | null>(null)
const seoChecks = ref<any[]>([])
const auditLogs = ref<any[]>([])

const hasMetrics = () =>
  pageSpeedScore.value != null ||
  lcp.value != null ||
  fid.value != null ||
  cls.value != null ||
  seoChecks.value.length > 0

async function fetchPerformance() {
  loadError.value = ''
  try {
    const res = await fetch('/api/v1/seo/performance', { headers: { Authorization: `Bearer ${getAuthToken()}` } })
    if (!res.ok) {
      dataTrust.value = 'empty'
      loadError.value = `性能接口不可用（HTTP ${res.status}）`
      return
    }
    const body = await res.json()
    const data = body.data || body
    const hasLive =
      data.page_speed_score != null ||
      data.lcp ||
      data.seo_checks?.length ||
      data.audit_logs?.length
    if (!hasLive) {
      dataTrust.value = 'empty'
      loadError.value = '站点未探测或无历史性能记录'
      return
    }
    dataTrust.value = 'live'
    if (data.page_speed_score != null) pageSpeedScore.value = data.page_speed_score
    if (data.lcp) lcp.value = data.lcp
    if (data.fid) fid.value = data.fid
    if (data.cls) cls.value = data.cls
    if (data.security_score) securityScore.value = data.security_score
    if (data.vuln_count != null) vulnCount.value = data.vuln_count
    if (data.cert_days != null) certDays.value = data.cert_days
    if (data.seo_checks) seoChecks.value = data.seo_checks
    if (data.audit_logs) auditLogs.value = data.audit_logs
  } catch {
    dataTrust.value = 'empty'
    loadError.value = '无法连接性能监控接口'
  }
}

onMounted(() => { fetchPerformance() })
</script>
