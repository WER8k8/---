<template>
  <YdPage title="外贸 AI 技能台" subtitle="7 个核心外贸技能，一键执行" surface="elevated">
    <div class="skill-console">
      <!-- 技能卡片网格 -->
      <div class="skill-grid">
        <div
          v-for="skill in skills"
          :key="skill.name"
          class="skill-card"
          :class="{ active: selectedSkill?.name === skill.name }"
          @click="selectSkill(skill)"
        >
          <div class="card-icon">
            <component :is="getIcon(skill.icon)" />
          </div>
          <div class="card-info">
            <h4>{{ skill.display_name }}</h4>
            <p>{{ skill.description }}</p>
          </div>
          <a-tag :color="getCategoryColor(skill.category)" size="small">
            {{ getCategoryLabel(skill.category) }}
          </a-tag>
        </div>
      </div>

      <!-- 参数输入 + 执行 -->
      <a-card v-if="selectedSkill" :title="selectedSkill.display_name" class="execute-panel">
        <template #extra>
          <a-tag :color="getCategoryColor(selectedSkill.category)">
            {{ getCategoryLabel(selectedSkill.category) }}
          </a-tag>
        </template>

        <p class="skill-desc">{{ selectedSkill.description }}</p>

        <a-form layout="vertical" class="skill-form">
          <a-form-item
            v-for="(field, key) in selectedSkill.input_schema"
            :key="key"
            :label="field.label"
            :required="field.required"
          >
            <a-textarea
              v-if="field.type === 'string' && field.label.includes('优势') || field.label.includes('信息')"
              v-model="form[key]"
              :placeholder="field.default || `请输入${field.label}`"
              :rows="3"
            />
            <a-input
              v-else
              v-model="form[key]"
              :placeholder="field.default || `请输入${field.label}`"
            />
          </a-form-item>

          <a-form-item>
            <a-space>
              <a-button type="primary" :loading="executing" @click="executeSkill">
                <ThunderboltOutlined />
                执行技能
              </a-button>
              <a-button @click="resetForm">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>

      <!-- 执行结果 -->
      <a-card v-if="result" title="执行结果" class="result-panel">
        <template #extra>
          <a-space>
            <a-tag color="green">成功</a-tag>
            <span class="model-tag">模型: {{ result.model_used }}</span>
          </a-space>
        </template>

        <div class="result-content">
          <!-- JSON 结果 -->
          <pre v-if="typeof result.result === 'object'" class="result-json">{{ JSON.stringify(result.result, null, 2) }}</pre>
          <!-- 文本结果 -->
          <div v-else class="result-text" v-html="formatResult(result.result)" />
        </div>

        <div class="result-actions">
          <a-space>
            <a-button size="small" @click="copyResult">
              <CopyOutlined />
              复制结果
            </a-button>
            <a-button size="small" @click="exportResult">
              <ExportOutlined />
              导出 JSON
            </a-button>
          </a-space>
        </div>
      </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ThunderboltOutlined,
  CopyOutlined,
  ExportOutlined,
  SearchOutlined,
  MailOutlined,
  FileSearchOutlined,
  AimOutlined,
  BarChartOutlined,
  GlobalOutlined,
  EditOutlined
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost } from '@/utils/api'

// 技能类型
interface Skill {
  name: string
  display_name: string
  description: string
  category: string
  icon: string
  input_schema: Record<string, {
    type: string
    required: boolean
    label: string
    default?: string
  }>
}

// 状态
const skills = ref<Skill[]>([])
const selectedSkill = ref<Skill | null>(null)
const form = reactive<Record<string, string>>({})
const executing = ref(false)
const result = ref<any>(null)

// 初始化
onMounted(async () => {
  try {
    const res = await apiGet('/skills')
    skills.value = res.skills || []
  } catch (error) {
    console.error('加载技能失败:', error)
  }
})

// 选择技能
function selectSkill(skill: Skill) {
  selectedSkill.value = skill
  result.value = null
  // 填充默认值
  Object.keys(skill.input_schema).forEach(key => {
    form[key] = skill.input_schema[key].default || ''
  })
}

// 执行技能
async function executeSkill() {
  if (!selectedSkill.value) return
  executing.value = true
  try {
    const res = await apiPost(`/skills/${selectedSkill.value.name}`, form)
    result.value = res
    message.success(`${selectedSkill.value.display_name} 执行成功`)
  } catch (error: any) {
    message.error(error?.message || '执行失败')
  } finally {
    executing.value = false
  }
}

// 重置
function resetForm() {
  Object.keys(form).forEach(key => form[key] = '')
  result.value = null
}

// 复制结果
async function copyResult() {
  const text = typeof result.value?.result === 'object'
    ? JSON.stringify(result.value.result, null, 2)
    : String(result.value?.result)
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}

// 导出 JSON
function exportResult() {
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedSkill.value?.name || 'skill'}-result.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 格式化结果
function formatResult(text: string): string {
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

// 图标映射
function getIcon(icon: string) {
  const map: Record<string, any> = {
    search: SearchOutlined,
    mail: MailOutlined,
    globe: GlobalOutlined,
    target: AimOutlined,
    presentation: BarChartOutlined,
    edit: EditOutlined,
    file: FileSearchOutlined,
  }
  return map[icon] || SearchOutlined
}

// 分类颜色
function getCategoryColor(cat: string): string {
  const map: Record<string, string> = {
    prospect: 'blue',
    outreach: 'green',
    research: 'purple',
    competitor: 'red',
    enablement: 'orange',
    seo: 'cyan',
    content: 'magenta',
  }
  return map[cat] || 'default'
}

function getCategoryLabel(cat: string): string {
  const map: Record<string, string> = {
    prospect: '获客',
    outreach: '触达',
    research: '调研',
    competitor: '竞品',
    enablement: '赋能',
    seo: 'SEO',
    content: '内容',
  }
  return map[cat] || cat
}
</script>

<style scoped lang="scss">
.skill-console {
  .skill-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .skill-card {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: #1890ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    }

    &.active {
      border-color: #1890ff;
      background: #f6f8ff;
    }

    .card-icon {
      font-size: 24px;
      color: #1890ff;
      margin-bottom: 8px;
    }

    .card-info {
      h4 {
        margin: 0 0 4px;
        font-size: 14px;
      }

      p {
        margin: 0;
        font-size: 12px;
        color: #888;
        line-height: 1.4;
      }
    }
  }

  .execute-panel {
    margin-bottom: 24px;

    .skill-desc {
      color: #666;
      margin-bottom: 16px;
    }
  }

  .result-panel {
    .result-content {
      background: #f5f5f5;
      border-radius: 4px;
      padding: 16px;
      max-height: 500px;
      overflow-y: auto;

      .result-json {
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 12px;
        white-space: pre-wrap;
        margin: 0;
      }

      .result-text {
        font-size: 14px;
        line-height: 1.6;
      }
    }

    .result-actions {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;
    }

    .model-tag {
      font-size: 12px;
      color: #888;
    }
  }
}
</style>
