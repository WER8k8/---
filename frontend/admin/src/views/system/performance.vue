<template>
  <div class="p-6 space-y-6">
    <!-- 标签页切换 -->
    <div class="flex items-center gap-3 mb-6">
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'metrics'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
      <!-- 系统健康状态 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="text-lg font-semibold mb-4">
          系统健康状态
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center p-4 bg-green-50 rounded-lg">
            <div class="text-3xl font-bold text-green-600">
              {{ healthStatus.status }}
            </div>
            <div class="text-sm text-gray-600 mt-1">
              当前状态
            </div>
          </div>
          <div class="text-center p-4 bg-blue-50 rounded-lg">
            <div class="text-3xl font-bold text-blue-600">
              {{ healthStatus.metrics?.total_requests || 0 }}
            </div>
            <div class="text-sm text-gray-600 mt-1">
              总请求数
            </div>
          </div>
          <div class="text-center p-4 bg-yellow-50 rounded-lg">
            <div class="text-3xl font-bold text-yellow-600">
              {{ healthStatus.metrics?.error_rate || 0 }}%
            </div>
            <div class="text-sm text-gray-600 mt-1">
              错误率
            </div>
          </div>
          <div class="text-center p-4 bg-purple-50 rounded-lg">
            <div class="text-3xl font-bold text-purple-600">
              {{ healthStatus.metrics?.slow_queries_count || 0 }}
            </div>
            <div class="text-sm text-gray-600 mt-1">
              慢查询数
            </div>
          </div>
        </div>
        <div
          v-if="healthStatus.issues?.length > 0"
          class="mt-4"
        >
          <h4 class="text-sm font-medium text-red-600 mb-2">
            存在的问题:
          </h4>
          <ul class="list-disc list-inside text-sm text-gray-600">
            <li
              v-for="(issue, index) in healthStatus.issues"
              :key="index"
            >
              {{ issue }}
            </li>
          </ul>
        </div>
      </div>

      <!-- 端点性能统计 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">
            API端点性能统计
          </h3>
          <button
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
            @click="loadMetrics"
          >
            刷新
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left">
                  端点
                </th>
                <th class="px-4 py-3 text-center">
                  请求数
                </th>
                <th class="px-4 py-3 text-center">
                  平均(ms)
                </th>
                <th class="px-4 py-3 text-center">
                  P95(ms)
                </th>
                <th class="px-4 py-3 text-center">
                  P99(ms)
                </th>
                <th class="px-4 py-3 text-center">
                  错误数
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ep in metrics.endpoints"
                :key="ep.endpoint"
                class="border-t"
              >
                <td class="px-4 py-3 font-mono text-xs">
                  {{ ep.endpoint }}
                </td>
                <td class="px-4 py-3 text-center">
                  {{ ep.count }}
                </td>
                <td
                  class="px-4 py-3 text-center"
                  :class="getResponseTimeClass(ep.avg_time)"
                >
                  {{ ep.avg_time }}
                </td>
                <td class="px-4 py-3 text-center">
                  {{ ep.p95_time }}
                </td>
                <td
                  class="px-4 py-3 text-center"
                  :class="getResponseTimeClass(ep.p99_time)"
                >
                  {{ ep.p99_time }}
                </td>
                <td class="px-4 py-3 text-center text-red-600">
                  {{ ep.error_count }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 安全审计 -->
    <div
      v-if="activeTab === 'security'"
      class="space-y-6"
    >
      <!-- 安全评分 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="text-lg font-semibold mb-4">
          安全评分
        </h3>
        <div class="flex items-center justify-center">
          <div class="relative w-48 h-48">
            <svg
              class="w-full h-full"
              viewBox="0 0 36 36"
            >
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#eee"
                stroke-width="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                :stroke="getScoreColor(securityReport.security_score)"
                stroke-width="3"
                :stroke-dasharray="`${securityReport.security_score}, 100`"
                stroke-linecap="round"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <div
                class="text-4xl font-bold"
                :style="{ color: getScoreColor(securityReport.security_score) }"
              >
                {{ securityReport.security_score }}
              </div>
              <div class="text-2xl font-bold mt-1">
                {{ securityReport.grade }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                {{ securityReport.risk_level }} risk
              </div>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-600">
              {{ securityReport.latest_scan?.critical_count || 0 }}
            </div>
            <div class="text-xs text-gray-600">
              严重
            </div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">
              {{ securityReport.latest_scan?.high_count || 0 }}
            </div>
            <div class="text-xs text-gray-600">
              高
            </div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-yellow-600">
              {{ securityReport.latest_scan?.medium_count || 0 }}
            </div>
            <div class="text-xs text-gray-600">
              中
            </div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">
              {{ securityReport.latest_scan?.low_count || 0 }}
            </div>
            <div class="text-xs text-gray-600">
              低
            </div>
          </div>
        </div>
      </div>

      <!-- 安全问题列表 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">
            安全问题列表
          </h3>
          <button
            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
            @click="runSecurityAudit"
            :disabled="auditing"
          >
            {{ auditing ? '审计中...' : '执行安全审计' }}
          </button>
        </div>
        <div
          v-if="securityIssues.length > 0"
          class="space-y-3"
        >
          <div
            v-for="issue in securityIssues"
            :key="issue.title"
            class="p-4 border rounded-lg"
            :class="getIssueBorderClass(issue.severity)"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span :class="getSeverityBadgeClass(issue.severity)">{{ issue.severity }}</span>
                  <span class="text-xs text-gray-500">{{ issue.category }}</span>
                  <span
                    v-if="issue.cwe_id"
                    class="text-xs text-gray-500"
                  >{{ issue.cwe_id }}</span>
                </div>
                <h4 class="font-medium mb-1">
                  {{ issue.title }}
                </h4>
                <p class="text-sm text-gray-600 mb-2">
                  {{ issue.description }}
                </p>
                <div class="text-sm">
                  <span class="font-medium text-green-600">建议:</span>
                  <span class="text-gray-600 ml-1">{{ issue.recommendation }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          v-else
          class="text-center py-8 text-gray-500"
        >
          暂无安全问题，点击上方按钮执行审计
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const activeTab = ref('metrics')
const healthStatus = ref({})
const metrics = ref({ endpoints: [] })
const securityReport = ref({})
const securityIssues = ref([])
const auditing = ref(false)

const API_BASE = '/api/v1'

async function loadMetrics() {
  try {
    const [healthRes, metricsRes] = await Promise.all([
      axios.get(`${API_BASE}/performance/health`),
      axios.get(`${API_BASE}/performance/metrics`)
    ])
    healthStatus.value = healthRes.data
    metrics.value = metricsRes.data
  } catch (error) {
    console.error('Failed to load metrics:', error)
  }
}

async function loadSecurityReport() {
  try {
    const reportRes = await axios.get(`${API_BASE}/performance/security/report`)
    securityReport.value = reportRes.data
    
    const issuesRes = await axios.get(`${API_BASE}/performance/security/issues`)
    securityIssues.value = issuesRes.data.issues || []
  } catch (error) {
    console.error('Failed to load security report:', error)
  }
}

async function runSecurityAudit() {
  auditing.value = true
  try {
    await axios.post(`${API_BASE}/performance/security/audit`)
    await loadSecurityReport()
  } catch (error) {
    console.error('Security audit failed:', error)
    alert('安全审计失败')
  } finally {
    auditing.value = false
  }
}

function getResponseTimeClass(time) {
  if (time > 500) return 'text-red-600'
  if (time > 200) return 'text-yellow-600'
  return 'text-green-600'
}

function getScoreColor(score) {
  if (score >= 90) return '#10b981'
  if (score >= 80) return '#3b82f6'
  if (score >= 70) return '#f59e0b'
  if (score >= 60) return '#f97316'
  return '#ef4444'
}

function getIssueBorderClass(severity) {
  switch (severity) {
    case 'critical': return 'border-red-300 bg-red-50'
    case 'high': return 'border-orange-300 bg-orange-50'
    case 'medium': return 'border-yellow-300 bg-yellow-50'
    default: return 'border-blue-300 bg-blue-50'
  }
}

function getSeverityBadgeClass(severity) {
  switch (severity) {
    case 'critical': return 'px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium'
    case 'high': return 'px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium'
    case 'medium': return 'px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-medium'
    default: return 'px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium'
  }
}

onMounted(() => {
  loadMetrics()
  loadSecurityReport()
})
</script>
