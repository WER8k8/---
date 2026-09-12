<template>
  <a-card class="score-radar" size="small" :bordered="false">
    <template #title>
      <div class="radar-title">
        <RadarChartOutlined />
        <span>评分雷达图</span>
      </div>
    </template>

    <!-- 雷达图 -->
    <div class="radar-container" ref="chartRef" :style="{ height: '300px' }"></div>

    <!-- 评分明细 -->
    <div class="score-detail">
      <div class="detail-grid">
        <div class="detail-item" v-for="item in scoreItems" :key="item.label">
          <div class="detail-header">
            <span class="detail-label">{{ item.label }}</span>
            <span class="detail-score" :style="{ color: getScoreColor(item.value) }">
              {{ item.value }}分
            </span>
          </div>
          <a-progress
            :percent="item.value"
            :stroke-color="getScoreColor(item.value)"
            :show-info="false"
            size="small"
          />
          <div class="detail-desc">{{ item.description }}</div>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { RadarChartOutlined } from '@ant-design/icons-vue'

// 评分项定义
export interface ScoreItem {
  label: string
  value: number
  description: string
  weight?: number
}

// Props
interface Props {
  scores: ScoreItem[]
  title?: string
  maxValue?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '客户评分雷达图',
  maxValue: 100
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 评分项（直接从 props 计算）
const scoreItems = computed(() => props.scores)

// 初始化图表
onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    renderChart()
  }
})

// 监听数据变化
watch(() => props.scores, () => {
  renderChart()
}, { deep: true })

// 渲染雷达图
function renderChart() {
  if (!chartInstance || !scoreItems.value.length) return

  const option = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal',
        color: '#333'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const esc = (s: string) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        const values = params.value || []
        let html = `<div style="font-weight: bold; margin-bottom: 4px;">${esc(params.name || '评分')}</div>`
        scoreItems.value.forEach((item, index) => {
          html += `<div>${esc(item.label)}: ${values[index] || 0}分</div>`
        })
        return html
      }
    },
    radar: {
      indicator: scoreItems.value.map(item => ({
        name: item.label,
        max: props.maxValue,
        color: '#666'
      })),
      shape: 'circle',
      splitNumber: 4,
      name: {
        textStyle: {
          color: '#666',
          fontSize: 12
        }
      },
      splitLine: {
        lineStyle: {
          color: '#eee'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(24, 144, 255, 0.05)', 'rgba(24, 144, 255, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    series: [
      {
        name: '评分',
        type: 'radar',
        lineStyle: {
          color: '#1890ff',
          width: 2
        },
        areaStyle: {
          color: 'rgba(24, 144, 255, 0.2)'
        },
        itemStyle: {
          color: '#1890ff',
          borderColor: '#fff',
          borderWidth: 2
        },
        symbol: 'circle',
        symbolSize: 6,
        data: [
          {
            value: scoreItems.value.map(item => item.value),
            name: '评分'
          }
        ]
      }
    ]
  }

  chartInstance.setOption(option)
}

// 获取评分颜色
function getScoreColor(score: number): string {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
}

// resize 监听 + 卸载清理
const handleResize = () => chartInstance?.resize()

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped lang="scss">
.score-radar {
  .radar-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
  }

  .radar-container {
    margin-bottom: 16px;
  }

  .score-detail {
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      .detail-item {
        background: #fafafa;
        border-radius: 6px;
        padding: 12px;

        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .detail-label {
            font-size: 13px;
            color: #333;
            font-weight: 500;
          }

          .detail-score {
            font-size: 16px;
            font-weight: 600;
          }
        }

        .detail-desc {
          font-size: 12px;
          color: #888;
          margin-top: 4px;
          line-height: 1.4;
        }
      }
    }
  }
}
</style>
