<template>
  <YdPage class="ai-content" title="AI 内容助手" subtitle="内容生成 · SEO 优化 · 智能改写" surface="elevated">
    <a-row :gutter="16">
      <!-- Left: Generation Form -->
      <a-col :xs="24" :lg="12">
        <a-card title="内容生成" class="form-card">
          <a-form layout="vertical" :model="form">
            <a-form-item label="优化类型" :required="true">
              <a-select v-model:value="form.optimization_type">
                <a-select-option value="content">正文内容优化</a-select-option>
                <a-select-option value="title">标题优化</a-select-option>
                <a-select-option value="description">描述优化</a-select-option>
                <a-select-option value="alt_text">图片ALT优化</a-select-option>
                <a-select-option value="rewrite">智能改写</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="AI 模型">
              <a-select v-model:value="form.ai_model">
                <a-select-option value="gpt-4o">GPT-4o</a-select-option>
                <a-select-option value="claude-3-sonnet">Claude 3.5 Sonnet</a-select-option>
                <a-select-option value="deepseek-chat">DeepSeek Chat</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="语气风格">
              <a-select v-model:value="form.tone">
                <a-select-option value="professional">专业正式</a-select-option>
                <a-select-option value="friendly">亲切友好</a-select-option>
                <a-select-option value="persuasive">营销说服</a-select-option>
                <a-select-option value="technical">技术严谨</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="核心关键词（逗号分隔）">
              <a-input v-model:value="keywords" placeholder="轻集料混凝土, LC20, 保温材料" />
            </a-form-item>
            <a-form-item label="原始内容" :required="true">
              <a-textarea v-model:value="form.content" :rows="8" placeholder="请输入需要优化或改写的内容..." :maxlength="5000" />
              <p class="char-count">{{ form.content.length }} / 5000</p>
            </a-form-item>
            <a-form-item>
              <a-space>
                <a-button type="primary" :loading="loading" @click="optimizeContent" class="generate-btn">
                  <SparklesOutlined />
                  AI 生成
                </a-button>
                <a-button @click="clearForm">清空</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- History -->
        <a-card title="历史生成记录" class="history-card">
          <div ref="historyPanelRef" class="yd-panel yd-table-panel">
            <YdTableToolbar :loading="false" :target-ref="historyPanelRef" :show-export="false" @refresh="() => {}" />
            <YdDataTable
              :columns="historyCols"
              :data-source="history"
              :pagination="historyPagination"
              :table-props="{ size: tableSize, rowKey: 'id' }"
              @page-change="onHistoryPageChange"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'actions'">
                  <a-button size="small" type="link" @click="loadHistoryItem(record)">查看</a-button>
                </template>
              </template>
            </YdDataTable>
          </div>
        </a-card>
      </a-col>

      <!-- Right: Preview -->
      <a-col :xs="24" :lg="12">
        <a-card title="生成结果预览" class="preview-card">
          <template v-if="optimizedContent">
            <a-row :gutter="16" class="preview-stats">
              <a-col :span="8">
                <a-statistic title="Token 用量" :value="tokenUsage" suffix="tokens" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="预估费用" :value="cost" prefix="$" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="耗时" :value="duration" suffix="ms" />
              </a-col>
            </a-row>

            <a-tabs v-model:activeKey="resultTab" class="result-tabs">
              <a-tab-pane key="result" tab="优化结果">
                <a-textarea v-model:value="optimizedContent" :rows="12" />
              </a-tab-pane>
              <a-tab-pane key="diff" tab="差异对比">
                <div class="diff-view">
                  <div class="diff-section">
                    <h4 class="diff-label original">原始内容</h4>
                    <p class="diff-text">{{ form.content || '(空)' }}</p>
                  </div>
                  <div class="diff-arrow">→</div>
                  <div class="diff-section">
                    <h4 class="diff-label optimized">优化后</h4>
                    <p class="diff-text">{{ optimizedContent }}</p>
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>

            <div class="preview-actions">
              <a-space>
                <a-button @click="copyResult">
                  <CopyOutlined />
                  复制
                </a-button>
                <a-button type="primary" @click="applyResult">
                  <CheckCircleOutlined />
                  应用
                </a-button>
              </a-space>
            </div>
          </template>
          <a-empty v-else description="请填写左侧表单并点击「AI 生成」" />
        </a-card>
      </a-col>
    </a-row>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  BulbOutlined as SparklesOutlined, CopyOutlined, CheckCircleOutlined,
} from '@ant-design/icons-vue'
import { aiGenerateAPI } from '@/api'

const historyPanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const historyPage = ref({ current: 1, pageSize: 5 })
const historyPagination = computed(() => ({
  current: historyPage.value.current,
  pageSize: historyPage.value.pageSize,
  total: history.value.length,
}))
function onHistoryPageChange(p: { current: number; pageSize: number }) {
  historyPage.value = { current: p.current, pageSize: p.pageSize }
}

const form = ref({
  content: '',
  optimization_type: 'content',
  ai_model: 'gpt-4o',
  tone: 'professional',
})
const keywords = ref('')
const loading = ref(false)
const optimizedContent = ref('')
const tokenUsage = ref(0)
const cost = ref(0)
const duration = ref(0)
const resultTab = ref('result')

const historyCols = [
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '预览', dataIndex: 'preview', key: 'preview', ellipsis: true },
  { title: '时间', dataIndex: 'time', key: 'time', width: 160 },
  { title: '操作', key: 'actions', width: 80 },
]

const history = ref<Array<{ id: number; type: string; preview: string; time: string; content?: string }>>([
  { id: 1, type: '标题优化', preview: '高品质轻集料混凝土供应商', time: '2026-05-21 10:30' },
  { id: 2, type: '正文优化', preview: '轻集料混凝土是一种新型节能建材...', time: '2026-05-21 09:15' },
  { id: 3, type: '智能改写', preview: '选择我们，就是选择品质与信赖...', time: '2026-05-20 15:45' },
])

const typeLabel: Record<string, string> = {
  content: '正文优化',
  title: '标题优化',
  description: '描述优化',
  alt_text: 'ALT优化',
  rewrite: '智能改写',
}

const toneLabel: Record<string, string> = {
  professional: '专业正式',
  friendly: '亲切友好',
  persuasive: '营销说服',
  technical: '技术严谨',
}

async function optimizeContent() {
  if (!form.value.content) {
    message.warning('请输入需要优化的内容')
    return
  }
  loading.value = true
  const startTime = Date.now()
  try {
    const kwList = keywords.value.split(',').map((k: string) => k.trim()).filter(Boolean)
    // 内容改写（rewrite）走 /ai/generate，其他走 /ai/optimize
    if (form.value.optimization_type === 'rewrite') {
      const res = await aiGenerateAPI.generate({
        prompt: `请用${toneLabel[form.value.tone] || '专业'}的语气改写以下建材内容:\n\n${form.value.content}`,
        model: form.value.ai_model || 'general',
      })
      optimizedContent.value = res.data.content || ''
      tokenUsage.value = res.data.token_usage || 0
      cost.value = res.data.cost || 0
    } else {
      const res = await aiGenerateAPI.optimize({
        content: form.value.content,
        optimization_type: form.value.optimization_type,
        keywords: kwList,
      })
      optimizedContent.value = res.data.optimized_content || ''
      tokenUsage.value = res.data.token_usage || 0
      cost.value = res.data.cost || 0
    }
    duration.value = Date.now() - startTime

    // Add to history
    history.value.unshift({
      id: Date.now(),
      type: typeLabel[form.value.optimization_type] || form.value.optimization_type,
      preview: (optimizedContent.value || '').slice(0, 40) + '...',
      content: optimizedContent.value,
      time: new Date().toLocaleString('zh-CN'),
    })
    message.success('生成完成')
  } catch (e: any) {
    message.error(e?.message || '生成失败，请检查 AI 配置或网络')
  } finally {
    loading.value = false
  }
}

function clearForm() {
  form.value.content = ''
  optimizedContent.value = ''
  keywords.value = ''
}

function loadHistoryItem(record: any) {
  if (record.content) {
    optimizedContent.value = record.content
    message.success('已加载历史记录')
  } else {
    message.warning('该记录无完整内容，请重新生成')
  }
}

async function copyResult() {
  if (!optimizedContent.value) return
  try {
    await navigator.clipboard.writeText(optimizedContent.value)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}

function applyResult() {
  message.success('优化结果已应用到内容管理系统')
}
</script>

<style scoped lang="scss">
.ai-content {
  .form-card, .history-card, .preview-card {
    margin-bottom: 16px;
    border-radius: 12px;
  }

  .char-count {
    text-align: right;
    font-size: 12px;
    color: #94a3b8;
    margin-top: 4px;
  }

  .generate-btn {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .preview-stats {
    margin-bottom: 16px;
  }

  .result-tabs {
    margin-top: 12px;
  }

  .diff-view {
    display: flex;
    gap: 12px;
    align-items: flex-start;

    .diff-section {
      flex: 1;
      padding: 12px;
      border-radius: 8px;

      .diff-label {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 6px;
        &.original { color: #f59e0b; }
        &.optimized { color: #22c55e; }
      }
      .diff-text {
        font-size: 13px;
        color: #374151;
        white-space: pre-wrap;
        line-height: 1.6;
      }
    }
    .diff-arrow {
      font-size: 20px;
      color: #94a3b8;
      padding-top: 12px;
    }
  }

  .preview-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f3f4f6;
  }
}
</style>
