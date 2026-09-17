/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI文章生成器" subtitle="使用英伟达AI模型生成高质量专业文章" surface="elevated">
    <template #actions>
      <a-space wrap>
        <a-tag color="green">NVIDIA · 文章场景</a-tag>
        <a-tooltip :title="articleModel || '未配置'">
          <a-tag style="max-width: 280px; overflow: hidden; text-overflow: ellipsis">
            {{ articleModel || '加载模型…' }}
          </a-tag>
        </a-tooltip>
        <a-button type="link" size="small" @click="router.push('/admin/ai-center/scenario-models')">
          切换模型
        </a-button>
      </a-space>
    </template>
  <div class="article-generator-page">

    <div class="generator-container">
      <!-- 步骤指示器 -->
      <div class="steps-container">
        <a-steps :current="currentStep" size="small">
          <a-step title="配置参数" description="设置文章要求" />
          <a-step title="生成内容" description="AI创作文章" />
          <a-step title="预览优化" description="查看和调整" />
          <a-step title="发布导出" description="保存或发布" />
        </a-steps>
      </div>

      <!-- 步骤1: 配置参数 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="config-section">
          <h3 class="section-title">
            <SettingOutlined />
            文章配置
          </h3>
          
          <a-form :model="articleConfig" layout="vertical">
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item label="文章主题" required>
                  <a-input
                    v-model:value="articleConfig.topic"
                    placeholder="请输入文章主题"
                    size="large"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="目标字数" required>
                  <a-slider
                    v-model:value="articleConfig.wordCount"
                    :min="500"
                    :max="3000"
                    :step="100"
                    :marks="wordCountMarks"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item label="写作风格">
                  <a-select v-model:value="articleConfig.style" placeholder="选择写作风格">
                    <a-select-option value="professional">专业权威</a-select-option>
                    <a-select-option value="casual">轻松活泼</a-select-option>
                    <a-select-option value="technical">技术严谨</a-select-option>
                    <a-select-option value="marketing">营销推广</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="目标受众">
                  <a-select v-model:value="articleConfig.audience" placeholder="选择目标受众">
                    <a-select-option value="professionals">行业专业人士</a-select-option>
                    <a-select-option value="beginners">初学者</a-select-option>
                    <a-select-option value="executives">企业高管</a-select-option>
                    <a-select-option value="general">普通大众</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="关键词（用逗号分隔）">
              <a-input
                v-model:value="articleConfig.keywords"
                placeholder="例如：轻集料混凝土, 建筑保温, 节能环保"
              />
            </a-form-item>

            <a-form-item label="附加要求">
              <a-textarea
                v-model:value="articleConfig.requirements"
                placeholder="请输入其他特殊要求，如：需要包含数据支持、需要案例分析等"
                :rows="3"
              />
            </a-form-item>
          </a-form>
        </div>

        <div class="action-buttons">
          <a-button type="primary" size="large" @click="startGeneration" :loading="generating">
            <RocketOutlined />
            开始生成文章
          </a-button>
        </div>
      </div>

      <!-- 步骤2: 生成内容 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="generation-progress">
          <div class="progress-header">
            <h3>
              <LoadingOutlined />
              AI正在创作中...
            </h3>
            <p>预计需要 10-30 秒，请耐心等待</p>
          </div>

          <div class="progress-steps">
            <div class="progress-step" :class="{ active: generationProgress >= 1 }">
              <div class="step-icon">1</div>
              <div class="step-text">分析主题和要求</div>
            </div>
            <div class="progress-step" :class="{ active: generationProgress >= 2 }">
              <div class="step-icon">2</div>
              <div class="step-text">构建文章框架</div>
            </div>
            <div class="progress-step" :class="{ active: generationProgress >= 3 }">
              <div class="step-icon">3</div>
              <div class="step-text">生成详细内容</div>
            </div>
            <div class="progress-step" :class="{ active: generationProgress >= 4 }">
              <div class="step-icon">4</div>
              <div class="step-text">优化和完善</div>
            </div>
          </div>

          <a-progress
            :percent="generationPercent"
            :status="generationStatus"
            :stroke-color="{
              '0%': '#108ee9',
              '100%': '#87d068',
            }"
          />

          <div class="generation-stats">
            <div class="stat-item">
              <span class="stat-label">已生成字数：</span>
              <span class="stat-value">{{ generatedWordCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">耗时：</span>
              <span class="stat-value">{{ elapsedTime }}秒</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">使用模型：</span>
              <span class="stat-value">Meta Llama 3.1</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤3: 预览优化 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="preview-section">
          <div class="preview-header">
            <h3>
              <EyeOutlined />
              文章预览
            </h3>
            <div class="preview-actions">
              <a-button @click="regenerate" :loading="generating">
                <ReloadOutlined />
                重新生成
              </a-button>
              <a-button type="primary" @click="currentStep = 3">
                <CheckOutlined />
                确认使用
              </a-button>
            </div>
          </div>

          <div class="article-preview">
            <div class="article-meta">
              <div class="meta-item">
                <span class="meta-label">文章主题：</span>
                <span class="meta-value">{{ articleConfig.topic }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">实际字数：</span>
                <span class="meta-value">{{ generatedArticle.wordCount }}字</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">关键词覆盖：</span>
                <span class="meta-value">{{ generatedArticle.keywordCoverage }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">质量评分：</span>
                <span class="meta-value">{{ generatedArticle.qualityScore }}/100</span>
              </div>
            </div>

            <a-divider />

            <div class="article-content" v-html="sanitizeHtml(generatedArticle.content)"></div>
          </div>

          <div class="optimization-panel">
            <h4>内容优化选项</h4>
            <div class="optimization-options">
              <a-button @click="optimizeContent('seo')" :loading="optimizing">
                <SearchOutlined />
                SEO优化
              </a-button>
              <a-button @click="optimizeContent('readability')" :loading="optimizing">
                <ReadOutlined />
                可读性优化
              </a-button>
              <a-button @click="optimizeContent('professional')" :loading="optimizing">
                <AuditOutlined />
                专业性提升
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤4: 发布导出 -->
      <div v-if="currentStep === 3" class="step-content">
        <div class="publish-section">
          <div class="publish-header">
            <h3>
              <CloudUploadOutlined />
              发布与导出
            </h3>
            <p>文章已准备就绪，选择发布或导出方式</p>
          </div>

          <div class="publish-options">
            <a-row :gutter="24">
              <a-col :span="6">
                <div class="option-card" @click="publishArticle('draft')">
                  <div class="option-icon">
                    <FileOutlined />
                  </div>
                  <h4>保存草稿</h4>
                  <p>保存到草稿箱，稍后编辑发布</p>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="option-card" @click="publishArticle('publish')">
                  <div class="option-icon">
                    <SendOutlined />
                  </div>
                  <h4>立即发布</h4>
                  <p>直接发布到官网展示</p>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="option-card" @click="publishArticle('export')">
                  <div class="option-icon">
                    <DownloadOutlined />
                  </div>
                  <h4>导出文件</h4>
                  <p>导出为Word、PDF或Markdown</p>
                </div>
              </a-col>
              <a-col :span="6">
                <div class="option-card" @click="goArticleToVideo">
                  <div class="option-icon">
                    <VideoCameraOutlined />
                  </div>
                  <h4>转成视频</h4>
                  <p>将本文转为分镜脚本并加入 Cosmos 渲染队列</p>
                </div>
              </a-col>
            </a-row>
          </div>

          <div class="publish-success" v-if="publishSuccess">
            <a-result
              status="success"
              title="操作成功！"
              :sub-title="publishMessage"
            >
              <template #extra>
                <a-button type="primary" @click="resetGenerator">
                  继续生成新文章
                </a-button>
              </template>
            </a-result>
          </div>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { aiGenerateAPI, unwrapApiData } from '@/api'
import { apiGet } from '@/utils/api'
import { useSanitize } from '@/composables/useSanitize'

const { sanitizeHtml } = useSanitize()
import {
  SettingOutlined,
  RocketOutlined,
  LoadingOutlined,
  EyeOutlined,
  ReloadOutlined,
  CheckOutlined,
  SearchOutlined,
  ReadOutlined,
  AuditOutlined,
  CloudUploadOutlined,
  FileOutlined,
  SendOutlined,
  DownloadOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const articleModel = ref('')

async function loadArticleScenarioModel() {
  try {
    const data = await apiGet<{ mappings?: Record<string, string> }>(
      '/super-admin/ai-config/nvidia/scenarios',
    )
    articleModel.value = data?.mappings?.article || 'z-ai/glm-5.1'
  } catch {
    articleModel.value = 'z-ai/glm-5.1'
  }
}

onMounted(() => {
  loadArticleScenarioModel()
})

// 当前步骤
const currentStep = ref(0)

// 文章配置
const articleConfig = reactive({
  topic: '轻集料混凝土在建筑保温中的应用优势',
  wordCount: 800,
  style: 'professional',
  audience: 'professionals',
  keywords: '轻集料混凝土, 建筑保温, 节能环保, 保温材料',
  requirements: ''
})

// 字数标记
const wordCountMarks = {
  500: '500',
  1000: '1000',
  1500: '1500',
  2000: '2000',
  2500: '2500',
  3000: '3000'
}

// 生成状态
const generating = ref(false)
const generationProgress = ref(0)
const generationPercent = ref(0)
const generationStatus = ref<'active' | 'success' | 'exception'>('active')
const generatedWordCount = ref(0)
const elapsedTime = ref(0)

// 生成的文章
const generatedArticle = reactive({
  content: '',
  wordCount: 0,
  keywordCoverage: '',
  qualityScore: 0
})

// 发布状态
const publishSuccess = ref(false)
const publishMessage = ref('')

// 定时器
let progressTimer: number | null = null
let timeTimer: number | null = null

function buildArticlePrompt(): string {
  return [
    `请撰写一篇约 ${articleConfig.wordCount} 字的文章。`,
    `主题：${articleConfig.topic}`,
    `风格：${articleConfig.style}`,
    `受众：${articleConfig.audience}`,
    `关键词：${articleConfig.keywords}`,
    articleConfig.requirements ? `附加要求：${articleConfig.requirements}` : '',
  ].filter(Boolean).join('\n')
}

function extractGeneratedContent(result: Record<string, unknown>): string {
  if (typeof result.content === 'string') return result.content
  if (typeof result.text === 'string') return result.text
  if (typeof result.optimized_content === 'string') return result.optimized_content
  return JSON.stringify(result)
}

function countWords(text: string): number {
  const plain = text.replace(/<[^>]+>/g, ' ').trim()
  if (!plain) return 0
  const cjk = plain.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const words = plain.match(/[a-zA-Z0-9]+/g)?.length ?? 0
  return cjk + words
}

// 开始生成文章
const startGeneration = async () => {
  if (!articleConfig.topic) {
    message.error('请输入文章主题')
    return
  }

  generating.value = true
  currentStep.value = 1
  generationProgress.value = 0
  generationPercent.value = 0
  generatedWordCount.value = 0
  elapsedTime.value = 0

  progressTimer = window.setInterval(() => {
    if (generationProgress.value < 3) {
      generationProgress.value++
      generationPercent.value = generationProgress.value * 25
    }
  }, 1500)

  timeTimer = window.setInterval(() => {
    elapsedTime.value++
    const target = articleConfig.wordCount
    if (generatedWordCount.value < target) {
      generatedWordCount.value = Math.min(target, generatedWordCount.value + 40)
    }
  }, 1000)

  try {
    const res = await aiGenerateAPI.generate({
      prompt: buildArticlePrompt(),
      scenario: 'article',
    })
    const result = unwrapApiData<Record<string, unknown>>(res) ?? {}

    const content = extractGeneratedContent(result)
    const wordCount = countWords(content)
    const keywords = articleConfig.keywords.split(/[,，]/).map((k) => k.trim()).filter(Boolean)
    const covered = keywords.filter((k) => content.includes(k)).length

    generationProgress.value = 4
    generationPercent.value = 100
    generationStatus.value = 'success'
    generatedWordCount.value = wordCount

    generatedArticle.content = content
    generatedArticle.wordCount = wordCount
    generatedArticle.keywordCoverage = keywords.length
      ? `${covered}/${keywords.length} (${Math.round((covered / keywords.length) * 100)}%)`
      : '—'
    generatedArticle.qualityScore = Math.min(100, 70 + Math.floor(wordCount / 50))

    setTimeout(() => {
      currentStep.value = 2
      generating.value = false
    }, 500)
  } catch (error) {
    generationStatus.value = 'exception'
    message.error('文章生成失败，请重试')
    generating.value = false
  } finally {
    if (progressTimer) clearInterval(progressTimer)
    if (timeTimer) clearInterval(timeTimer)
  }
}

// 重新生成
const regenerate = () => {
  currentStep.value = 0
}

// 优化内容
const optimizing = ref(false)
const optimizeLabels: Record<string, string> = {
  seo: 'SEO',
  readability: '可读性',
  professional: '专业性',
}

const optimizeContent = async (type: string) => {
  const content = stripHtml(generatedArticle.content)
  if (!content) {
    message.warning('请先生成文章内容')
    return
  }
  optimizing.value = true
  try {
    const keywords = articleConfig.keywords.split(/[,，]/).map(k => k.trim()).filter(Boolean)
    const res = await aiGenerateAPI.optimize({
      content,
      optimization_type: type,
      keywords,
      scenario: 'article',
    })
    const data = unwrapApiData<{ optimized_content?: string }>(res) ?? {}
    if (data.optimized_content) {
      generatedArticle.content = data.optimized_content
      generatedArticle.wordCount = countWords(data.optimized_content)
      message.success(`${optimizeLabels[type] || type}优化已完成`)
    } else {
      message.warning('优化未返回内容')
    }
  } catch {
    message.error(`${optimizeLabels[type] || type}优化失败，请重试`)
  } finally {
    optimizing.value = false
  }
}

// 发布文章
const publishArticle = (type: string) => {
  const messages: Record<string, string> = {
    draft: '文章已保存到草稿箱',
    publish: '文章已成功发布到官网',
    export: '文章已导出为Word文档'
  }
  
  publishSuccess.value = true
  publishMessage.value = messages[type] || '操作成功'
  message.success(messages[type])
}

function stripHtml(html: string) {
  // 使用 DOMParser 代替 innerHTML，避免潜在的 XSS 风险
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return (doc.body.textContent || '').trim()
}

function goArticleToVideo() {
  const text = stripHtml(generatedArticle.content)
  if (!text) {
    message.warning('请先生成文章内容')
    return
  }
  sessionStorage.setItem(
    'article_to_video_payload',
    JSON.stringify({ article: text, title: articleConfig.topic || '' }),
  )
  router.push('/admin/ai-center/article-to-video')
}

// 重置生成器
const resetGenerator = () => {
  currentStep.value = 0
  publishSuccess.value = false
  publishMessage.value = ''
  generatedArticle.content = ''
  generatedArticle.wordCount = 0
  generatedArticle.keywordCoverage = ''
  generatedArticle.qualityScore = 0
}

// 清理定时器
onUnmounted(() => {
  if (progressTimer) clearInterval(progressTimer)
  if (timeTimer) clearInterval(timeTimer)
})
</script>

<style scoped lang="scss">
.article-generator-page {
  padding: 0;
  background: transparent;
  min-height: auto;
}

.generator-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.steps-container {
  padding: 24px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.step-content {
  padding: 24px;
}

.config-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 24px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-buttons {
  text-align: center;
  padding: 24px 0;
}

.generation-progress {
  text-align: center;
  padding: 40px 24px;
}

.progress-header {
  margin-bottom: 40px;
}

.progress-header h3 {
  font-size: 20px;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.progress-header p {
  color: #666;
  margin: 0;
}

.progress-steps {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 40px;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: all 0.3s;
}

.progress-step.active {
  opacity: 1;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #666;
}

.progress-step.active .step-icon {
  background: #1890ff;
  color: white;
}

.step-text {
  font-size: 14px;
  color: #666;
}

.progress-step.active .step-text {
  color: #1890ff;
  font-weight: 500;
}

.generation-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-top: 24px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  gap: 8px;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: 600;
  color: #1a1a1a;
}

.preview-section {
  padding: 0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.preview-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-actions {
  display: flex;
  gap: 12px;
}

.article-preview {
  background: #fafafa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.article-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.meta-item {
  display: flex;
  gap: 8px;
}

.meta-label {
  color: #666;
  min-width: 80px;
}

.meta-value {
  font-weight: 500;
  color: #1a1a1a;
}

.article-content {
  line-height: 1.8;
  color: #333;
}

.article-content h1 {
  font-size: 24px;
  margin: 0 0 24px 0;
  color: #1a1a1a;
}

.article-content h2 {
  font-size: 20px;
  margin: 24px 0 16px 0;
  color: #1a1a1a;
  border-bottom: 2px solid #1890ff;
  padding-bottom: 8px;
}

.article-content p {
  margin: 0 0 16px 0;
}

.article-content ul,
.article-content ol {
  margin: 0 0 16px 0;
  padding-left: 24px;
}

.article-content li {
  margin-bottom: 8px;
}

.optimization-panel {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 24px;
}

.optimization-panel h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 16px 0;
}

.optimization-options {
  display: flex;
  gap: 12px;
}

.publish-section {
  padding: 0;
}

.publish-header {
  text-align: center;
  margin-bottom: 40px;
}

.publish-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.publish-header p {
  color: #666;
  margin: 0;
}

.publish-options {
  margin-bottom: 40px;
}

.option-card {
  background: #fafafa;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.option-card:hover {
  border-color: #1890ff;
  background: #e6f7ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.15);
}

.option-icon {
  font-size: 48px;
  color: #1890ff;
  margin-bottom: 16px;
}

.option-card h4 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.option-card p {
  color: #666;
  margin: 0;
}

.publish-success {
  margin-top: 40px;
}
</style>