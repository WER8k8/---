/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="建材行业知识库" subtitle="基于建材行业国家标准、产品参数与施工规范的智能知识问答" surface="elevated">
  <div class="knowledge-base">

    <!-- Search Bar -->
    <div class="search-section">
      <a-card class="search-card" :bordered="false">
        <div class="search-row">
          <a-input-search
            v-model:value="question"
            placeholder="输入您的建材行业问题，例如：陶粒混凝土的密度是多少？"
            enter-button="搜索"
            size="large"
            :loading="loading"
            @search="handleSearch"
          />
        </div>
      </a-card>
    </div>

    <!-- Category Tags -->
    <div class="category-section">
      <span class="category-label">热门分类：</span>
      <a-tag
        v-for="cat in categories"
        :key="cat.id"
        :color="activeCategory === cat.id ? 'blue' : 'default'"
        class="category-tag"
        @click="filterByCategory(cat.id)"
      >
        {{ cat.name }}
        <span class="tag-count">({{ cat.count }})</span>
      </a-tag>
    </div>

    <!-- Answer Area -->
    <div class="answer-section" v-if="answer || loading">
      <!-- Loading -->
      <a-card v-if="loading" class="answer-card">
        <div class="loading-placeholder">
          <a-skeleton active :paragraph="{ rows: 4 }" />
          <p class="loading-hint">正在检索知识库...</p>
        </div>
      </a-card>

      <!-- Answer Result -->
      <a-card v-else class="answer-card">
        <div class="qa-item">
          <div class="q-label">
            <UserOutlined class="q-icon" />
            <span class="q-text">{{ lastQuestion }}</span>
          </div>
          <div class="a-label">
            <RobotOutlined class="a-icon" />
            <div class="a-content" v-html="sanitizeHtml(renderMarkdown(answer))"></div>
          </div>

          <!-- Sources -->
          <div class="sources-section" v-if="sources.length > 0">
            <div class="sources-title">
              <LinkOutlined />
              参考来源
            </div>
            <div class="sources-list">
              <div
                v-for="(src, idx) in sources"
                :key="idx"
                class="source-item"
              >
                <FileTextOutlined class="source-icon" />
                <span class="source-name">{{ src.title }}</span>
                <span class="source-file">{{ src.file }}</span>
              </div>
            </div>
          </div>
        </div>
      </a-card>
    </div>

    <!-- Empty State -->
    <div class="empty-section" v-else>
      <div class="empty-hints">
        <a-card class="hint-card" :bordered="false">
          <template #title>
            <span class="hint-card-title">
              <BulbOutlined />
              您可以尝试以下问题
            </span>
          </template>
          <div class="hint-list">
            <div
              v-for="(hint, idx) in sampleQuestions"
              :key="idx"
              class="hint-item"
              @click="selectHint(hint)"
            >
              <span class="hint-icon">{{ idx + 1 }}</span>
              <span>{{ hint }}</span>
            </div>
          </div>
        </a-card>

        <a-row :gutter="16" class="info-cards">
          <a-col :span="8">
            <a-card class="info-card" :bordered="false">
              <a-statistic
                title="知识文档"
                :value="stats.total_files"
                suffix="篇"
                :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"
              />
              <template #extra><FileTextOutlined /></template>
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card class="info-card" :bordered="false">
              <a-statistic
                title="知识段落"
                :value="stats.total_segments"
                suffix="段"
                :value-style="{ color: '#22c55e' }"
              />
              <template #extra><NodeIndexOutlined /></template>
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card class="info-card" :bordered="false">
              <a-statistic
                title="覆盖标准"
                :value="stats.categories.length"
                suffix="类"
                :value-style="{ color: '#f59e0b' }"
              />
              <template #extra><BookOutlined /></template>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  UserOutlined, RobotOutlined, LinkOutlined,
  FileTextOutlined, BulbOutlined, NodeIndexOutlined, BookOutlined,
} from '@ant-design/icons-vue'
import { useSanitize } from '@/composables/useSanitize'

const { sanitizeHtml } = useSanitize()

// ========== 状态 ==========
const question = ref('')
const lastQuestion = ref('')
const answer = ref('')
const sources = ref<{ file: string; title: string }[]>([])
const loading = ref(false)
const activeCategory = ref<string | null>(null)

const categories = ref<{ id: string; name: string; count: number }[]>([])
const stats = ref({
  total_files: 0,
  total_segments: 0,
  categories: [] as { id: string; name: string; count: number }[],
})

const sampleQuestions = [
  '陶粒混凝土的密度是多少？',
  '轻集料混凝土的配合比怎么设计？',
  '保温材料燃烧性能等级有哪些？',
  '保温砂浆的施工工艺是什么？',
  '陶粒混凝土有哪些强度等级？',
]

// ========== 初始化 ==========
onMounted(async () => {
  try {
    const [catRes, infoRes] = await Promise.all([
      fetch('/api/v1/knowledge/categories'),
      fetch('/api/v1/knowledge/info'),
    ])
    const catData = await catRes.json()
    const infoData = await infoRes.json()
    categories.value = catData?.data?.categories || []
    stats.value = infoData?.data || { total_files: 0, total_segments: 0, categories: [] }
  } catch (e: unknown) {
    categories.value = []
    stats.value = { total_files: 0, total_segments: 0, categories: [] }
    message.warning(e instanceof Error ? e.message : '知识库信息加载失败')
  }
})

// ========== 搜索与问答 ==========
async function handleSearch() {
  const q = question.value.trim()
  if (!q) {
    message.warning('请输入您的问题')
    return
  }

  loading.value = true
  lastQuestion.value = q

  try {
    const res = await fetch(`/api/v1/knowledge/ask?question=${encodeURIComponent(q)}`, {
      method: 'POST',
    })
    const data = await res.json()
    if (data?.data) {
      answer.value = data.data.answer
      sources.value = data.data.sources || []
    } else {
      // Fallback: try search
      answer.value = '知识库服务暂未返回结果，请稍后重试。'
      sources.value = []
    }
  } catch {
    answer.value = '知识库服务暂不可用，请确认后端已启动且已配置向量检索。'
    sources.value = []
  } finally {
    loading.value = false
  }
}

function filterByCategory(catId: string) {
  activeCategory.value = activeCategory.value === catId ? null : catId
  // 根据分类预置搜索关键词
  const categoryKeywords: Record<string, string> = {
    standards: '轻集料混凝土 国标规范',
    products: '陶粒混凝土 产品参数',
    construction: '施工工艺 保温砂浆',
  }
  if (activeCategory.value && categoryKeywords[catId]) {
    question.value = categoryKeywords[catId]
    handleSearch()
  }
}

function selectHint(hint: string) {
  question.value = hint
  handleSearch()
}

// ========== 工具函数 ==========
function renderMarkdown(text: string): string {
  if (!text) return ''
  // Simple render: convert \n to <br>, bold markers, etc.
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped lang="scss">
.knowledge-base {
  padding: 0;

  .search-section {
    margin-bottom: 16px;

    .search-card {
      border-radius: 12px;
      background: linear-gradient(135deg, #eff6ff 0%, #f0f4ff 100%);

      :deep(.ant-input-search) {
        .ant-input {
          border-radius: 10px 0 0 10px;
          border: 1px solid #dbeafe;
        }
        .ant-btn {
          border-radius: 0 10px 10px 0;
          background: var(--uj-brand, #4a9b8c);
          border-color: var(--uj-brand, #4a9b8c);
          height: 40px;
        }
      }
    }
  }

  .category-section {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;

    .category-label {
      font-size: 13px;
      color: #6b7280;
      font-weight: 500;
      white-space: nowrap;
    }

    .category-tag {
      cursor: pointer;
      padding: 4px 12px;
      font-size: 13px;
      border-radius: 16px;
      transition: all 0.2s;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(74, 155, 140, 0.15);
      }

      .tag-count {
        font-size: 11px;
        opacity: 0.7;
      }
    }
  }

  .answer-section {
    margin-bottom: 20px;

    .answer-card {
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);

      .loading-placeholder {
        padding: 8px 0;

        .loading-hint {
          text-align: center;
          color: #94a3b8;
          font-size: 13px;
          margin-top: 12px;
        }
      }

      .qa-item {
        .q-label {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #f3f4f6;

          .q-icon {
            font-size: 18px;
            color: var(--uj-brand, #4a9b8c);
            margin-top: 2px;
            flex-shrink: 0;
          }
          .q-text {
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
            line-height: 1.5;
          }
        }

        .a-label {
          display: flex;
          gap: 10px;
          align-items: flex-start;

          .a-icon {
            font-size: 18px;
            color: #22c55e;
            margin-top: 2px;
            flex-shrink: 0;
          }
          .a-content {
            font-size: 14px;
            color: #374151;
            line-height: 1.8;
            flex: 1;

            :deep(strong) {
              color: #1f2937;
              font-weight: 600;
            }
          }
        }

        .sources-section {
          margin-top: 20px;
          padding-top: 16px;
          border-top: 1px solid #f3f4f6;

          .sources-title {
            font-size: 13px;
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
          }

          .sources-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;

            .source-item {
              display: flex;
              align-items: center;
              gap: 6px;
              padding: 6px 12px;
              background: #f8fafc;
              border: 1px solid #e2e8f0;
              border-radius: 8px;
              font-size: 12px;
              color: #64748b;
              transition: all 0.2s;
              cursor: default;

              &:hover {
                background: #eff6ff;
                border-color: #bfdbfe;
              }

              .source-icon {
                color: var(--uj-brand, #4a9b8c);
                font-size: 14px;
              }
              .source-name {
                font-weight: 500;
                color: #475569;
              }
              .source-file {
                font-size: 11px;
                color: #94a3b8;
                margin-left: 4px;
              }
            }
          }
        }
      }
    }
  }

  .empty-section {
    .empty-hints {
      .hint-card {
        border-radius: 12px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #fafafa 0%, #f8fafc 100%);

        :deep(.ant-card-head) {
          border-bottom: 1px solid #f3f4f6;
          min-height: 48px;
        }

        .hint-card-title {
          font-size: 15px;
          font-weight: 600;
          color: #374151;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .hint-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 8px;

          .hint-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
            color: #374151;

            &:hover {
              border-color: var(--uj-brand, #4a9b8c);
              box-shadow: 0 2px 8px rgba(74, 155, 140, 0.1);
              transform: translateY(-1px);
            }

            .hint-icon {
              width: 24px;
              height: 24px;
              border-radius: 50%;
              background: #eff6ff;
              color: var(--uj-brand, #4a9b8c);
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              font-weight: 600;
              flex-shrink: 0;
            }
          }
        }
      }

      .info-cards {
        .info-card {
          border-radius: 12px;
          text-align: center;
          background: white;

          :deep(.ant-card-extra) {
            font-size: 24px;
            opacity: 0.15;
          }
        }
      }
    }
  }
}
</style>
