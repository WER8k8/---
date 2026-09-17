/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="Token 用量" subtitle="监控 AI 调用消耗、配额与告警配置" surface="elevated">
  <div class="usage-page">
    <!-- 统计卡 -->
    <div class="stat-grid">
      <a-card class="stat-card" :bordered="false">
        <a-statistic
          title="本月消耗 (Tokens)"
          :value="monthlyTokens"
          :precision="1"
          suffix="K"
          :value-style="{ color: '#722ed1', fontWeight: 700 }"
        >
          <template #prefix>
            <NumberOutlined class="stat-icon purple" />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic
          title="今日消耗 (Tokens)"
          :value="todayTokens"
          :precision="1"
          suffix="K"
          :value-style="{ color: 'var(--uj-brand, #4a9b8c)', fontWeight: 700 }"
        >
          <template #prefix>
            <ClockCircleOutlined class="stat-icon blue" />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic
          title="预估费用"
          :value="estimatedCost"
          :precision="2"
          prefix="¥"
          :value-style="{ color: '#f59e0b', fontWeight: 700 }"
        >
          <template #prefix>
            <DollarOutlined class="stat-icon amber" />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <a-statistic
          title="剩余配额"
          :value="remainingQuota"
          :precision="0"
          suffix="K"
          :value-style="{ color: '#10b981', fontWeight: 700 }"
        >
          <template #prefix>
            <RocketOutlined class="stat-icon green" />
          </template>
        </a-statistic>
        <div class="stat-trend">{{ quotaPercent }}%</div>
        <a-progress
          :percent="quotaPercent"
          :strokeColor="quotaPercent > 80 ? '#ef4444' : quotaPercent > 50 ? '#f59e0b' : '#10b981'"
          size="small"
          style="margin-top: 8px"
        />
      </a-card>
    </div>

    <!-- 30天趋势 -->
    <a-card title="近30天Token消耗趋势" class="section-card" :bordered="false">
      <a-empty v-if="!trendData.length" description="暂无调用记录" />
      <div v-else class="bar-chart">
        <div
          v-for="(item, i) in trendData"
          :key="i"
          class="bar-item"
          :title="`${item.date}: ${item.value}K`"
        >
          <div class="bar-label">{{ i % 5 === 0 ? item.date.slice(5) : '' }}</div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ height: (item.value / maxTrend) * 100 + '%', background: barColor(item.value) }"
            ></div>
          </div>
          <div class="bar-value" v-if="item.value > maxTrend * 0.7">{{ item.value }}</div>
        </div>
      </div>
    </a-card>

    <!-- 模型用量排行 -->
    <a-card title="模型用量排行" class="section-card" :bordered="false" style="margin-top: 16px">
      <a-empty v-if="!modelRanking.length" description="暂无模型调用记录" />
      <a-table
        v-else
        :dataSource="modelRanking"
        :columns="modelColumns"
        :pagination="{ pageSize: 8 }"
        size="middle"
        bordered
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'rank'">
            <a-tag v-if="record.rank === 1" color="gold">#1</a-tag>
            <a-tag v-else-if="record.rank === 2" color="silver">#2</a-tag>
            <a-tag v-else-if="record.rank === 3" color="bronze">#3</a-tag>
            <span v-else>#{{ record.rank }}</span>
          </template>
          <template v-if="column.key === 'progress'">
            <a-progress
              :percent="record.percent"
              :strokeColor="['#722ed1', '#a78bfa']"
              size="small"
              :showInfo="false"
            />
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 告警配置 -->
    <a-card title="用量告警配置" class="section-card" :bordered="false" style="margin-top: 16px">
      <a-form layout="inline">
        <a-form-item label="50% 阈值">
          <a-switch v-model:checked="alarmThresholds.level50" checked-children="开" un-checked-children="关" />
        </a-form-item>
        <a-form-item label="80% 阈值">
          <a-switch v-model:checked="alarmThresholds.level80" checked-children="开" un-checked-children="关" />
        </a-form-item>
        <a-form-item label="90% 阈值">
          <a-switch v-model:checked="alarmThresholds.level90" checked-children="开" un-checked-children="关" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="saveAlarmConfig">
            <SaveOutlined /> 保存配置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 最近告警 -->
    <a-card title="最近告警记录" class="section-card" :bordered="false" style="margin-top: 16px">
      <a-empty v-if="!recentAlarms.length" description="暂无告警" />
      <a-table
        v-else
        :dataSource="recentAlarms"
        :columns="alarmColumns"
        :pagination="{ pageSize: 5 }"
        size="middle"
        bordered
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'level'">
            <a-tag v-if="record.level === 'critical'" color="error">严重</a-tag>
            <a-tag v-else-if="record.level === 'warning'" color="warning">警告</a-tag>
            <a-tag v-else color="default">提示</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'
import {
  NumberOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  RocketOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue'

const monthlyTokens = ref(0)
const todayTokens = ref(0)
const estimatedCost = ref(0)
const remainingQuota = ref(0)
const quotaPercent = ref(0)

const trendData = ref<Array<{ date: string; value: number }>>([])
const maxTrend = computed(() => Math.max(...trendData.value.map(d => d.value), 1))

function barColor(val: number): string {
  if (val > maxTrend.value * 0.8) return '#ef4444'
  if (val > maxTrend.value * 0.5) return '#f59e0b'
  return '#722ed1'
}

const modelRanking = ref<any[]>([])

const modelColumns = [
  { title: '排名', dataIndex: 'rank', key: 'rank', width: 60 },
  { title: '模型', dataIndex: 'model', key: 'model' },
  { title: '提供商', dataIndex: 'provider', key: 'provider' },
  { title: '消耗Tokens', dataIndex: 'tokens', key: 'tokens' },
  { title: '调用次数', dataIndex: 'calls', key: 'calls' },
  { title: '占比', dataIndex: 'percent', key: 'progress' },
]

const alarmThresholds = ref({ level50: true, level80: true, level90: false })
const recentAlarms = ref<any[]>([])

const alarmColumns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 160 },
  { title: '级别', dataIndex: 'level', key: 'level', width: 80 },
  { title: '告警内容', dataIndex: 'message', key: 'message' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
]

async function loadUsage() {
  try {
    const overview = await apiGet<any>('/ai-usage/overview')
    monthlyTokens.value = overview?.monthly_tokens ?? 0
    todayTokens.value = overview?.today_tokens ?? 0
    estimatedCost.value = overview?.estimated_cost ?? 0
    remainingQuota.value = overview?.remaining_quota ?? 0
    quotaPercent.value = overview?.quota_percent ?? 0
    modelRanking.value = (overview?.model_rankings || []).map((r: any, i: number) => ({
      rank: i + 1,
      model: r.model_name,
      provider: r.model_name?.split('/')[0] || '—',
      tokens: `${r.tokens}K`,
      calls: r.call_count,
      percent: r.percent,
    }))
  } catch { /* 空状态 */ }

  try {
    const daily = await apiGet<{ items: Array<{ date: string; value: number }> }>('/ai-usage/daily?days=30')
    trendData.value = daily?.items || []
  } catch { /* 空状态 */ }

  try {
    const alerts = await apiGet<{ items: any[] }>('/ai-usage/alerts')
    recentAlarms.value = alerts?.items || []
  } catch { /* 空状态 */ }

  try {
    const cfg = await apiGet<Record<string, boolean>>('/ai-usage/alerts/config')
    if (cfg) {
      alarmThresholds.value = {
        level50: cfg.level50 ?? true,
        level80: cfg.level80 ?? true,
        level90: cfg.level90 ?? false,
      }
    }
  } catch { /* 空状态 */ }
}

async function saveAlarmConfig() {
  try {
    const { apiPost } = await import('@/utils/api')
    await apiPost('/ai-usage/alerts/config', {
      enabled: true,
      thresholds: { '50': 50, '80': 80, '90': 90 },
      notify_methods: ['site'],
    })
    message.success('告警配置已保存')
  } catch {
    message.error('保存告警配置失败')
  }
}

onMounted(loadUsage)
</script>

<style scoped>
.usage-page {
  max-width: 1200px;
  margin: 0 auto;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.stat-icon {
  font-size: 1.1rem;
}
.stat-icon.purple { color: #722ed1; }
.stat-icon.blue { color: var(--uj-brand, #4a9b8c); }
.stat-icon.amber { color: #f59e0b; }
.stat-icon.green { color: #10b981; }
.stat-trend {
  font-size: 0.72rem;
  margin-top: 6px;
}
.stat-trend.positive { color: #10b981; }
.stat-trend.negative { color: #ef4444; }

.section-card {
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* Bar chart (pure div) */
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 200px;
  padding: 0 4px;
}
.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  height: 100%;
}
.bar-label {
  font-size: 0.55rem;
  color: #9ca3af;
  margin-top: 6px;
  white-space: nowrap;
}
.bar-track {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.bar-fill {
  width: 70%;
  max-width: 28px;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
  cursor: pointer;
}
.bar-fill:hover {
  opacity: 0.8;
}
.bar-value {
  font-size: 0.55rem;
  color: #6b7280;
  position: absolute;
  top: -14px;
}

@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .bar-chart {
    height: 140px;
  }
}
@media (max-width: 480px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
