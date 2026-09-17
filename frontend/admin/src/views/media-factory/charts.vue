/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="动态图表引擎" subtitle="AI 数据可视化与动画图表生成" surface="elevated">
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="图表配置">
        <a-form layout="vertical">
          <a-form-item label="图表类型">
            <a-select v-model:value="chartType">
              <a-select-option value="line">折线图</a-select-option>
              <a-select-option value="bar">柱状图</a-select-option>
              <a-select-option value="pie">饼图</a-select-option>
              <a-select-option value="area">面积图</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="图表标题">
            <a-input v-model:value="chartTitle" placeholder="输入图表标题..." />
          </a-form-item>
          <a-form-item label="数据输入">
            <a-textarea v-model:value="rawData" :rows="6" placeholder="格式: 月份,销售额\n1月,120\n2月,200\n3月,150" />
          </a-form-item>
          <a-button type="primary" @click="generateChart" :loading="generating">生成图表</a-button>
        </a-form>
      </a-card>
      <a-card :title="chartTitle || '图表预览'">
        <div v-if="chartData.length === 0" class="flex items-center justify-center h-64 text-gray-300 text-lg">
          请在左侧输入数据并生成图表
        </div>
        <div v-else-if="chartType === 'bar'" class="bar-chart">
          <div v-for="(d, i) in chartData" :key="i" class="bar-row">
            <span class="bar-label">{{ d.label }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: barWidth(d.value) + '%', background: barColor(i) }">
              </div>
            </div>
            <span class="bar-val">{{ d.value }}</span>
          </div>
        </div>
        <div v-else-if="chartType === 'line' || chartType === 'area'" class="line-chart">
          <div class="chart-area">
            <div v-for="(d, i) in chartData" :key="i" class="line-point-wrapper" :style="{ left: (i / (chartData.length - 1 || 1)) * 100 + '%', bottom: (d.value / maxVal) * 100 + '%' }">
              <div class="line-dot" :style="{ background: 'var(--uj-brand, #4a9b8c)' }" :title="`${d.label}: ${d.value}`"></div>
              <span class="line-label">{{ d.label }}</span>
              <span class="line-val">{{ d.value }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="chartType === 'pie'" class="pie-chart">
          <div class="pie-legend">
            <div v-for="(d, i) in chartData" :key="i" class="pie-legend-item">
              <span class="pie-dot" :style="{ background: barColor(i) }"></span>
              <span>{{ d.label }}</span>
              <span>{{ d.value }} ({{ piePercent(d.value) }}%)</span>
            </div>
          </div>
        </div>
      </a-card>
    </div>
    <a-card title="已生成图表">
      <a-table :columns="gcol" :data-source="generated" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'typeTag'">
            <a-tag :color="typeColor(record.type)">{{ record.type }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="viewChart(record)">查看</a-button>
              <a-button size="small" type="link" @click="exportChart(record)">导出</a-button>
              <a-button size="small" type="link" danger @click="deleteChart(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { getAuthToken } from '@/utils/api';

const chartType = ref('bar')
const chartTitle = ref('')
const rawData = ref('')
const generating = ref(false)
const chartData = ref<{ label: string; value: number }[]>([])

const generated = ref<any[]>([])

async function fetchCharts() {
  try {
    const res = await fetch('/api/v1/media-factory/charts', { headers: { Authorization: `Bearer ${getAuthToken()}` } })
    const body = await res.json()
    const data = body.data || body
    if (data.list) generated.value = data.list
  } catch {
    generated.value = []
  }
}

onMounted(() => { fetchCharts() })

const gcol = [
  { title: '图表名称', dataIndex: 'name' },
  { title: '类型', key: 'typeTag', width: 80 },
  { title: '数据来源', dataIndex: 'source', width: 120 },
  { title: '生成时间', dataIndex: 'time', width: 160 },
  { title: '操作', key: 'action', width: 180 },
]

const maxVal = computed(() => Math.max(...chartData.value.map(d => d.value), 1))
const total = computed(() => chartData.value.reduce((s, d) => s + d.value, 0))

function barWidth(v: number) { return (v / maxVal.value) * 100 }
function barColor(i: number) {
  const colors = ['#4a9b8c', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']
  return colors[i % colors.length]
}
function piePercent(v: number) { return total.value > 0 ? Math.round((v / total.value) * 100) : 0 }
function typeColor(t: string) {
  const m: Record<string, string> = { '折线图': 'blue', '柱状图': 'green', '饼图': 'orange', '面积图': 'purple' }
  return m[t] || 'default'
}

async function generateChart() {
  if (!chartTitle.value.trim()) { message.warning('请输入图表标题'); return }
  if (!rawData.value.trim()) { message.warning('请输入数据'); return }
  const lines = rawData.value.trim().split('\n')
  if (lines.length < 2) { message.warning('至少需要标题行和一行数据'); return }
  generating.value = true
  await new Promise(r => setTimeout(r, 800))
  chartData.value = lines.slice(1).map(line => {
    const [label, val] = line.split(/[,，\t]/)
    return { label: (label || '').trim(), value: parseFloat(val) || 0 }
  }).filter(d => d.label)
  generated.value.unshift({
    id: Date.now(),
    name: chartTitle.value,
    type: chartType.value === 'line' ? '折线图' : chartType.value === 'bar' ? '柱状图' : chartType.value === 'pie' ? '饼图' : '面积图',
    source: '手动输入',
    time: new Date().toLocaleString('zh-CN'),
  })
  // 同步到后端
  try {
    await fetch('/api/v1/media-factory/charts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ name: chartTitle.value, type: chartType.value, data: chartData.value }),
    })
  } catch {}
  generating.value = false
  message.success('图表生成成功')
}

function viewChart(r: any) {
  chartTitle.value = r.name
  chartType.value = r.type === '折线图' ? 'line' : r.type === '柱状图' ? 'bar' : r.type === '饼图' ? 'pie' : 'area'
  message.success(`已加载图表「${r.name}」到预览区`)
}
function exportChart(r: any) { message.success(`导出图表: ${r.name}`) }
function deleteChart(id: number) { generated.value = generated.value.filter(g => g.id !== id); message.success('已删除') }
</script>
<style scoped>
.bar-chart { display: flex; flex-direction: column; gap: 12px; padding: 16px 0; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 48px; font-size: 12px; color: #6b7280; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 24px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; min-width: 4px; display: flex; align-items: center; padding-left: 6px; font-size: 11px; color: #fff; }
.bar-val { width: 40px; font-size: 12px; color: #374151; font-weight: 500; }
.line-chart { padding: 24px 0; }
.chart-area { position: relative; height: 200px; border-left: 2px solid #e5e7eb; border-bottom: 2px solid #e5e7eb; margin-left: 36px; margin-bottom: 30px; }
.line-point-wrapper { position: absolute; transform: translateX(-50%); }
.line-dot { width: 10px; height: 10px; border-radius: 50%; cursor: pointer; border: 2px solid #fff; box-shadow: 0 0 0 2px var(--uj-brand, #4a9b8c); }
.line-label { position: absolute; bottom: -22px; left: 50%; transform: translateX(-50%); font-size: 11px; color: #6b7280; white-space: nowrap; }
.line-val { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: 500; color: #374151; }
.pie-chart { padding: 16px 0; }
.pie-legend { display: flex; flex-direction: column; gap: 12px; }
.pie-legend-item { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.pie-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
</style>
