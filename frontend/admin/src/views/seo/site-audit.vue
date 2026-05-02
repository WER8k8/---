<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          站点审计
        </h1>
        <p class="text-gray-500 mt-1">
          检测网站SEO问题并获取优化建议
        </p>
      </div>
    </div>

    <a-card title="审计配置">
      <a-form
        :model="form"
        layout="vertical"
        class="space-y-6"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="网站URL"
              :required="true"
            >
              <a-input
                v-model="form.url"
                placeholder="https://www.youding.com"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="审计类型">
              <a-select v-model="form.audit_type">
                <a-select-option value="quick">
                  快速审计
                </a-select-option>
                <a-select-option value="full">
                  完整审计
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="handleStartAudit"
          >
            <PlayCircleOutlined class="w-4 h-4 mr-2" />
            开始审计
          </a-button>
          <a-button
            v-if="auditId"
            class="ml-4"
            @click="handleRefreshStatus"
          >
            <RestOutlined class="w-4 h-4 mr-2" />
            刷新状态
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card
      v-if="auditStatus"
      title="审计状态"
    >
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic
            title="审计状态"
            :value="getStatusText(auditStatus.status)"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="审计得分"
            :value="auditStatus.score || 0"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="检测问题数"
            :value="auditStatus.issue_count || 0"
          />
        </a-col>
      </a-row>
      <div
        v-if="auditStatus.status === 'running'"
        class="mt-4"
      >
        <a-progress
          :percent="progressPercent"
          :status="progressStatus"
        />
        <p class="text-center text-gray-500 mt-2">
          {{ progressText }}
        </p>
      </div>
    </a-card>

    <a-card
      v-if="auditResult && auditStatus.status === 'completed'"
      title="审计结果"
    >
      <div class="mb-6">
        <div class="flex items-center justify-center">
          <div class="text-center">
            <div
              class="w-24 h-24 rounded-full flex items-center justify-center text-4xl font-bold"
              :class="getScoreClass(auditResult.score)"
            >
              {{ auditResult.score }}
            </div>
            <p class="mt-2 text-gray-600">
              综合评分
            </p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div
          v-for="category in ['技术合规', '内容质量', '链接结构']"
          :key="category"
          class="bg-gray-50 rounded-lg p-4"
        >
          <h4 class="font-semibold text-gray-700">
            {{ category }}
          </h4>
          <div class="mt-2 flex items-center">
            <div class="flex-1">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-600">得分</span>
                <span class="font-semibold">{{ getCategoryScore(category) }}</span>
              </div>
              <a-progress
                :percent="getCategoryScore(category)"
                :show-info="false"
              />
            </div>
          </div>
        </div>
      </div>

      <a-card
        title="问题列表"
        class="mb-6"
      >
        <a-table
          :columns="issueColumns"
          :data-source="auditResult.issues"
          :pagination="false"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'severity'">
              <a-tag :color="getSeverityColor(record.severity)">
                {{ getSeverityText(record.severity) }}
              </a-tag>
            </template>
            <template v-if="column.key === 'recommendation'">
              <p class="text-sm text-blue-600">
                {{ record.recommendation }}
              </p>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card title="优化建议">
        <a-list :data-source="auditResult.recommendations">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>
                  <span class="font-semibold">优先级 {{ item.priority }} - {{ item.action }}</span>
                </template>
                <template #description>
                  <span class="text-sm">
                    难度: <a-tag :color="getEffortColor(item.effort)">{{ item.effort }}</a-tag>
                    <span class="ml-4">影响: <a-tag color="blue">{{ item.impact }}</a-tag></span>
                  </span>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </a-card>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  PlayCircleOutlined,
  RestOutlined,
} from '@ant-design/icons-vue'
import { Modal } from 'ant-design-vue'
import { seoAPI } from '@/api'

const form = ref({
  url: 'https://www.youding.com',
  audit_type: 'quick',
})

const auditId = ref('')
const auditStatus = ref<any>(null)
const auditResult = ref<any>(null)
const loading = ref(false)
const progressPercent = ref(0)
const progressText = ref('初始化...')

const issueColumns = [
  { title: '类别', key: 'category', width: 150 },
  { title: '严重程度', key: 'severity', width: 100 },
  { title: '问题描述', key: 'description' },
  { title: '建议', key: 'recommendation' },
]

const progressStatus = computed(() => {
  if (progressPercent.value >= 100) return 'success'
  return 'active'
})

function getStatusText(status: string) {
  if (status === 'running') return '运行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  return status
}

function getScoreClass(score: number) {
  if (score >= 80) return 'bg-green-100 text-green-700'
  if (score >= 60) return 'bg-yellow-100 text-yellow-700'
  return 'bg-red-100 text-red-700'
}

function getSeverityColor(severity: string) {
  if (severity === 'high') return 'red'
  if (severity === 'medium') return 'orange'
  if (severity === 'low') return 'gold'
  return 'default'
}

function getSeverityText(severity: string) {
  if (severity === 'high') return '高'
  if (severity === 'medium') return '中'
  if (severity === 'low') return '低'
  return severity
}

function getEffortColor(effort: string) {
  if (effort === 'low') return 'green'
  if (effort === 'medium') return 'gold'
  if (effort === 'high') return 'red'
  return 'default'
}

function getCategoryScore(category: string) {
  if (!auditResult.value) return 0
  const categoryScores: Record<string, number> = {
    '技术合规': 85,
    '内容质量': 78,
    '链接结构': 90,
  }
  return categoryScores[category] || 0
}

async function handleStartAudit() {
  if (!form.value.url) {
    Modal.warning({ title: '提示', content: '请输入网站URL' })
    return
  }

  loading.value = true
  try {
    const res = await seoAPI.audit(form.value)
    auditId.value = res.data.audit_id
    auditStatus.value = { status: 'running', score: 0, issue_count: 0 }
    progressPercent.value = 0
    await pollAuditStatus()
  } catch (e: any) {
    Modal.error({ title: '审计失败', content: e.message })
  } finally {
    loading.value = false
  }
}

async function pollAuditStatus() {
  if (!auditId.value) return

  const progressSteps = [
    { percent: 10, text: '正在连接网站...' },
    { percent: 30, text: '抓取页面内容...' },
    { percent: 50, text: '分析技术指标...' },
    { percent: 70, text: '评估内容质量...' },
    { percent: 90, text: '生成报告...' },
  ]

  let step = 0
  const interval = setInterval(async () => {
    if (step < progressSteps.length) {
      progressPercent.value = progressSteps[step].percent
      progressText.value = progressSteps[step].text
      step++
    }

    try {
      const res = await seoAPI.getAudit(auditId.value)
      auditStatus.value = res.data

      if (res.data.status === 'completed') {
        auditResult.value = res.data
        progressPercent.value = 100
        progressText.value = '审计完成'
        clearInterval(interval)
      } else if (res.data.status === 'failed') {
        clearInterval(interval)
        Modal.error({ title: '审计失败', content: '网站审计过程中出现错误' })
      }
    } catch (e) {
      console.error('Failed to get audit status:', e)
    }
  }, 1000)
}

async function handleRefreshStatus() {
  if (!auditId.value) return
  try {
    const res = await seoAPI.getAudit(auditId.value)
    auditStatus.value = res.data
    if (res.data.status === 'completed') {
      auditResult.value = res.data
    }
  } catch (e: any) {
    Modal.error({ title: '获取状态失败', content: e.message })
  }
}
</script>
