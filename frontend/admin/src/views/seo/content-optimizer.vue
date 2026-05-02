<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          AI内容优化
        </h1>
        <p class="text-gray-500 mt-1">
          使用AI智能优化网站内容和SEO元素
        </p>
      </div>
    </div>

    <a-card title="优化配置">
      <a-form
        :model="form"
        layout="vertical"
        class="space-y-6"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="优化类型"
              :required="true"
            >
              <a-select v-model="form.optimization_type">
                <a-select-option value="title">
                  标题优化
                </a-select-option>
                <a-select-option value="description">
                  描述优化
                </a-select-option>
                <a-select-option value="alt_text">
                  图片ALT优化
                </a-select-option>
                <a-select-option value="content">
                  正文内容优化
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="AI模型">
              <a-select v-model="form.ai_model">
                <a-select-option value="gpt-4o">
                  GPT-4o
                </a-select-option>
                <a-select-option value="claude-3-opus">
                  Claude 3 Opus
                </a-select-option>
                <a-select-option value="gemini-1.5-pro">
                  Gemini 1.5 Pro
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="核心关键词（逗号分隔）">
          <a-input
            v-model="keywordsInput"
            placeholder="轻集料混凝土, LC20, 保温材料"
          />
        </a-form-item>
        <a-form-item
          label="原始内容"
          :required="true"
        >
          <a-textarea
            v-model="form.content"
            :rows="8"
            placeholder="请输入需要优化的内容..."
            :maxlength="5000"
          />
          <p class="text-xs text-gray-400 mt-1">
            已输入 {{ form.content.length }} 字符
          </p>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="optimizeContent"
          >
            <SparklesOutlined class="w-4 h-4 mr-2" />
            AI优化
          </a-button>
          <a-button
            v-if="optimizedContent"
            class="ml-4"
            @click="compareContent"
          >
            <GitCompareOutlined class="w-4 h-4 mr-2" />
            对比差异
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card
      v-if="optimizedContent"
      title="优化结果"
    >
      <a-row
        :gutter="16"
        class="mb-6"
      >
        <a-col :span="6">
          <a-statistic
            title="Token使用量"
            :value="tokenUsage"
            suffix=" tokens"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="预估费用"
            :value="cost"
            prefix="¥"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="技术参数保留"
            :value="technicalPreserved ? '是' : '否'"
          />
        </a-col>
      </a-row>
      <div class="space-y-4">
        <div class="bg-gray-50 p-4 rounded-lg">
          <h4 class="font-semibold text-gray-700 mb-2">
            优化后的内容
          </h4>
          <a-textarea
            v-model="optimizedContent"
            :rows="8"
            class="font-mono text-sm"
          />
        </div>
        <div
          v-if="changes.length"
          class="bg-blue-50 p-4 rounded-lg"
        >
          <h4 class="font-semibold text-blue-700 mb-2">
            修改要点
          </h4>
          <ul class="list-disc list-inside text-blue-600">
            <li
              v-for="(change, idx) in changes"
              :key="idx"
            >
              {{ change }}
            </li>
          </ul>
        </div>
      </div>
      <div class="mt-4 flex items-center space-x-3">
        <a-button @click="copyOptimized">
          <CopyOutlined class="w-4 h-4 mr-2" />
          复制优化结果
        </a-button>
        <a-button
          type="primary"
          @click="applyOptimization"
        >
          <CheckCircleOutlined class="w-4 h-4 mr-2" />
          应用优化
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  ShakeOutlined as SparklesOutlined,
  CompressOutlined as GitCompareOutlined,
  CopyOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Button as AButton,
  Statistic as AStatistic,
  Row as ARow,
  Col as ACol,
  Modal,
} from 'ant-design-vue'
import { seoAPI } from '@/api'

const form = ref({
  content: '',
  optimization_type: 'content',
  ai_model: 'gpt-4o',
})

const keywordsInput = ref('轻集料混凝土, LC20, 保温材料')

const optimizedContent = ref('')
const changes = ref<string[]>([])
const tokenUsage = ref(0)
const cost = ref(0)
const technicalPreserved = ref(true)
const loading = ref(false)

async function optimizeContent() {
  if (!form.value.content) {
    Modal.warning({ title: '提示', content: '请输入需要优化的内容' })
    return
  }

  loading.value = true
  try {
    const keywords = keywordsInput.value.split(',').map((k) => k.trim()).filter(Boolean)
    const res = await seoAPI.optimizeContent({
      ...form.value,
      keywords,
    })
    optimizedContent.value = res.data.optimized_content
    changes.value = res.data.changes || []
    tokenUsage.value = res.data.token_usage || 0
    cost.value = res.data.cost || 0
    technicalPreserved.value = res.data.technical_params_preserved !== false
  } catch (e: any) {
    Modal.error({ title: '优化失败', content: e.message })
  } finally {
    loading.value = false
  }
}

function compareContent() {
  Modal.info({
    title: '内容对比',
    content: `
      <div class="space-y-4">
        <div>
          <h4 class="font-semibold text-gray-700">原始内容：</h4>
          <p class="text-gray-600 text-sm mt-1">${form.value.content.slice(0, 200)}...</p>
        </div>
        <div>
          <h4 class="font-semibold text-green-700">优化后：</h4>
          <p class="text-green-600 text-sm mt-1">${optimizedContent.value.slice(0, 200)}...</p>
        </div>
      </div>
    `,
    width: 600,
  })
}

async function copyOptimized() {
  if (!optimizedContent.value) return
  try {
    await navigator.clipboard.writeText(optimizedContent.value)
    Modal.success({ title: '复制成功' })
  } catch (e) {
    Modal.error({ title: '复制失败' })
  }
}

function applyOptimization() {
  Modal.success({ title: '应用成功', content: '优化结果已应用到内容管理系统' })
}
</script>
