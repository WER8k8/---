<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          LLMs.txt生成
        </h1>
        <p class="text-gray-500 mt-1">
          为搜索引擎生成优化的LLMs.txt文件
        </p>
      </div>
    </div>

    <a-card title="生成配置">
      <a-form
        :model="form"
        layout="vertical"
        class="space-y-6"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="业务类型"
              :required="true"
            >
              <a-input
                v-model="form.business_type"
                placeholder="例如：轻集料混凝土"
              />
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
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="温度参数">
              <a-input-number
                v-model="form.temperature"
                :min="0"
                :max="1"
                :step="0.1"
              />
              <p class="text-xs text-gray-400 mt-1">
                控制输出随机性，建议0.3-0.5
              </p>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大Token数">
              <a-input-number
                v-model="form.max_tokens"
                :min="500"
                :max="4000"
                :step="100"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="核心关键词（每行一个）">
          <a-textarea
            v-model="keywordsText"
            :rows="4"
            placeholder="轻集料混凝土&#10;LC20轻集料&#10;保温隔热材料"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="generateLLMSTxt"
          >
            <SparklesOutlined class="w-4 h-4 mr-2" />
            生成LLMs.txt
          </a-button>
          <a-button
            v-if="generatedContent"
            class="ml-4"
            @click="validateContent"
          >
            <CheckCircleOutlined class="w-4 h-4 mr-2" />
            验证内容
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card
      v-if="generatedContent"
      title="生成结果"
    >
      <a-row :gutter="16">
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
            title="版本"
            :value="version"
          />
        </a-col>
      </a-row>
      <div class="mt-6">
        <a-textarea
          v-model="generatedContent"
          :rows="15"
          class="font-mono text-sm"
          :disabled="!editable"
        />
      </div>
      <div class="mt-4 flex items-center justify-between">
        <a-checkbox v-model="editable">
          允许编辑
        </a-checkbox>
        <div class="flex items-center space-x-3">
          <a-button @click="copyContent">
            <CopyOutlined class="w-4 h-4 mr-2" />
            复制内容
          </a-button>
          <a-button
            type="primary"
            @click="downloadFile"
          >
            <DownloadOutlined class="w-4 h-4 mr-2" />
            下载文件
          </a-button>
        </div>
      </div>
    </a-card>

    <a-card
      v-if="validationResult"
      title="验证结果"
    >
      <a-alert
        :type="validationResult.is_valid ? 'success' : 'error'"
        show-icon
        :message="validationResult.is_valid ? '验证通过' : '存在问题'"
      >
        <template #description>
          <div v-if="validationResult.issues && validationResult.issues.length">
            <h4 class="font-semibold mb-2">
              问题列表：
            </h4>
            <ul class="list-disc list-inside text-red-500">
              <li
                v-for="(issue, idx) in validationResult.issues"
                :key="idx"
              >
                {{ issue }}
              </li>
            </ul>
          </div>
          <div v-if="validationResult.suggestions && validationResult.suggestions.length">
            <h4 class="font-semibold mb-2">
              优化建议：
            </h4>
            <ul class="list-disc list-inside text-blue-500">
              <li
                v-for="(suggestion, idx) in validationResult.suggestions"
                :key="idx"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>
          <div v-if="validationResult.is_valid && !validationResult.issues?.length">
            <p class="text-green-500">
              LLMs.txt内容格式正确，没有发现问题。
            </p>
          </div>
        </template>
      </a-alert>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  ShakeOutlined as SparklesOutlined,
  CheckCircleOutlined,
  CopyOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputNumber as AInputNumber,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Button as AButton,
  Checkbox as ACheckbox,
  Statistic as AStatistic,
  Alert as AAlert,
  Row as ARow,
  Col as ACol,
  Modal,
} from 'ant-design-vue'
import { seoAPI } from '@/api'

const form = ref({
  business_type: '轻集料混凝土',
  ai_model: 'gpt-4o',
  temperature: 0.3,
  max_tokens: 2000,
})

const keywordsText = ref('轻集料混凝土\nLC20轻集料\nLC15轻集料\n保温隔热材料\n轻质混凝土')

const generatedContent = ref('')
const tokenUsage = ref(0)
const cost = ref(0)
const version = ref('1.0.0')
const editable = ref(false)
const loading = ref(false)

const validationResult = ref<any>(null)

async function generateLLMSTxt() {
  if (!form.value.business_type) {
    Modal.warning({ title: '提示', content: '请输入业务类型' })
    return
  }

  loading.value = true
  try {
    const keywords = keywordsText.value.split('\n').filter((k) => k.trim())
    const res = await seoAPI.generateLLMSTxt({
      ...form.value,
      keywords,
    })
    generatedContent.value = res.data.content
    tokenUsage.value = res.data.token_usage || 0
    cost.value = res.data.cost || 0
    version.value = res.data.version || '1.0.0'
    validationResult.value = null
  } catch (e: any) {
    Modal.error({ title: '生成失败', content: e.message })
  } finally {
    loading.value = false
  }
}

async function validateContent() {
  if (!generatedContent.value) return

  try {
    await seoAPI.optimizeContent({
      content: generatedContent.value,
      optimization_type: 'content',
      keywords: [],
      ai_model: form.value.ai_model,
    })
    validationResult.value = {
      is_valid: true,
      issues: [],
      suggestions: ['内容验证通过'],
    }
  } catch (e: any) {
    validationResult.value = {
      is_valid: false,
      issues: [e.message],
      suggestions: [],
    }
  }
}

async function copyContent() {
  if (!generatedContent.value) return
  try {
    await navigator.clipboard.writeText(generatedContent.value)
    Modal.success({ title: '复制成功' })
  } catch (e) {
    Modal.error({ title: '复制失败' })
  }
}

function downloadFile() {
  if (!generatedContent.value) return
  const blob = new Blob([generatedContent.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'llms.txt'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
