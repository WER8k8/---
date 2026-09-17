/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-card class="search-syntax-preview" size="small" :bordered="false">
    <template #title>
      <div class="preview-title">
        <SearchOutlined />
        <span>搜索语法预览</span>
      </div>
    </template>

    <!-- 搜索语法展示 -->
    <div class="syntax-block">
      <div class="syntax-label">生成搜索语法：</div>
      <div class="syntax-content">
        <code class="syntax-code">{{ generatedSyntax }}</code>
        <a-button
          class="copy-btn"
          size="small"
          @click="copySyntax"
          :type="copied ? 'primary' : 'default'"
        >
          {{ copied ? '✓ 已复制' : '复制' }}
        </a-button>
      </div>
    </div>

    <!-- 搜索来源预览 -->
    <div class="sources-block" v-if="searchSources.length > 0">
      <div class="syntax-label">搜索来源：</div>
      <div class="source-chips">
        <a-tag
          v-for="source in searchSources"
          :key="source.name"
          :color="source.enabled ? 'blue' : 'default'"
          class="source-chip"
        >
          <template #icon>
            <component :is="source.icon" v-if="source.icon" />
          </template>
          {{ source.name }}
        </a-tag>
      </div>
    </div>

    <!-- 预期结果预览 -->
    <div class="expectations-block">
      <div class="syntax-label">预期结果：</div>
      <a-row :gutter="16" class="expectations-grid">
        <a-col :span="8" v-for="expect in expectations" :key="expect.type">
          <a-statistic
            :title="expect.type"
            :value="expect.count"
            :value-style="{ fontSize: '16px', color: '#1890ff' }"
          >
            <template #prefix><component :is="expect.icon" /></template>
          </a-statistic>
        </a-col>
      </a-row>
    </div>

    <!-- 搜索意图说明 -->
    <div class="intent-block" v-if="intentExplanation">
      <div class="syntax-label">搜索意图：</div>
      <div class="intent-text">{{ intentExplanation }}</div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  SearchOutlined,
  GlobalOutlined,
  BankOutlined,
  TeamOutlined,
  ShopOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'

// Props
interface Props {
  keywords: string[]
  countries: string[]
  customerType?: string
  searchSource?: string
  excludeWords?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  keywords: () => [],
  countries: () => [],
  customerType: '',
  searchSource: 'google',
  excludeWords: () => ['job', 'used', 'repair', 'school', 'news']
})

// Emits
const emit = defineEmits<{
  (e: 'syntax-generated', syntax: string): void
  (e: 'copy'): void
}>()

// 状态
const copied = ref(false)

// 客户类型映射
const customerTypeMap: Record<string, string> = {
  'distributor': 'Distributor',
  'integrator': 'System Integrator',
  'oem': 'OEM',
  'epc': 'EPC Contractor',
  'mro': 'MRO Service',
  'factory': 'End-user Factory'
}

// 搜索来源配置
const searchSources = computed(() => [
  {
    name: 'Google/Web',
    icon: GlobalOutlined,
    enabled: props.searchSource === 'google' || props.searchSource === 'all',
    syntax: 'site:google.com'
  },
  {
    name: 'Alibaba RFQ',
    icon: BankOutlined,
    enabled: props.searchSource === 'alibaba' || props.searchSource === 'all',
    syntax: 'site:alibaba.com/rfq'
  },
  {
    name: 'Made-in-China',
    icon: ShopOutlined,
    enabled: props.searchSource === 'made-in-china' || props.searchSource === 'all',
    syntax: 'site:made-in-china.com'
  },
  {
    name: 'Global Sources',
    icon: ShopOutlined,
    enabled: props.searchSource === 'global-sources' || props.searchSource === 'all',
    syntax: 'site:globalsources.com'
  },
  {
    name: 'LinkedIn',
    icon: TeamOutlined,
    enabled: props.searchSource === 'linkedin' || props.searchSource === 'all',
    syntax: 'site:linkedin.com'
  }
])

// 生成搜索语法
const generatedSyntax = computed(() => {
  const parts: string[] = []

  // 产品关键词
  if (props.keywords.length > 0) {
    parts.push(props.keywords.join(', '))
  }

  // 市场/国家
  if (props.countries.length > 0) {
    parts.push(props.countries.join(', '))
  }

  // 客户类型
  if (props.customerType && customerTypeMap[props.customerType]) {
    parts.push(customerTypeMap[props.customerType])
  }

  // 搜索目标
  parts.push('company website')

  // 排除词
  if (props.excludeWords.length > 0) {
    const excludePart = props.excludeWords.map(w => `-${w}`).join(' ')
    parts.push(excludePart)
  }

  return parts.join(' ')
})

// 预期结果统计
const expectations = computed(() => [
  {
    type: '候选公司',
    count: '~20',
    icon: BankOutlined
  },
  {
    type: '联系方式',
    count: '~15',
    icon: TeamOutlined
  },
  {
    type: '高价值线索',
    count: '~5',
    icon: GlobalOutlined
  }
])

// 意图解释
const intentExplanation = computed(() => {
  if (props.keywords.length === 0 && props.countries.length === 0) {
    return '请先输入产品关键词和选择目标市场，系统将自动优化搜索策略。'
  }

  const parts: string[] = []

  if (props.keywords.length > 0) {
    parts.push(`聚焦"${props.keywords.join('、')}"品类`)
  }

  if (props.countries.length > 0) {
    parts.push(`定向${props.countries.join('、')}市场`)
  }

  if (props.customerType && customerTypeMap[props.customerType]) {
    parts.push(`匹配${customerTypeMap[props.customerType]}客户类型`)
  }

  parts.push('排除招聘、二手、新闻等无关结果')

  return parts.join('，')
})

// 复制语法
const copySyntax = async () => {
  try {
    await navigator.clipboard.writeText(generatedSyntax.value)
    copied.value = true
    emit('copy')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}

// 监听语法变化
watch(generatedSyntax, (newSyntax) => {
  emit('syntax-generated', newSyntax)
}, { immediate: true })
</script>

<style scoped lang="scss">
.search-syntax-preview {
  background: linear-gradient(135deg, #f6f8ff 0%, #f0f5ff 100%);
  border-left: 3px solid #1890ff;
  border-radius: 6px;

  .preview-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #1890ff;
  }

  .syntax-block {
    margin-bottom: 16px;

    .syntax-content {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-top: 8px;
    }

    .syntax-code {
      flex: 1;
      background: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      padding: 12px;
      font-family: 'SF Mono', Monaco, Consolas, monospace;
      font-size: 13px;
      color: #333;
      word-break: break-all;
      line-height: 1.6;
      white-space: pre-wrap;
    }

    .copy-btn {
      flex-shrink: 0;
    }
  }

  .sources-block {
    margin-bottom: 16px;

    .source-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }
  }

  .expectations-block {
    margin-bottom: 16px;

    .expectations-grid {
      margin-top: 8px;
    }
  }

  .intent-block {
    .intent-text {
      background: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      padding: 10px 12px;
      margin-top: 8px;
      font-size: 13px;
      color: #555;
      line-height: 1.6;
    }
  }

  .syntax-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
  }
}
</style>
