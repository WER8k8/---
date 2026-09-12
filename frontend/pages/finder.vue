<template>
  <div class="finder-page">
    <!-- Hero -->
    <section class="finder-hero">
      <div class="finder-hero-inner">
        <h1 class="finder-title">产品匹配引擎</h1>
        <p class="finder-sub">
          输入应用场景与技术约束，系统基于真实产品参数做硬过滤 + 加权评分，
          给出可解释的推荐结果（不编造认证或测试数据）。
        </p>
      </div>
    </section>

    <section class="finder-body">
      <!-- 查询表单 -->
      <a-card class="finder-form-card" :bordered="false">
        <form class="finder-form" @submit.prevent="onSubmit">
          <div class="field field-full">
            <label class="field-label">应用场景 <span class="req">*</span></label>
            <a-input
              v-model:value="form.application"
              placeholder="如：管道保温、外墙保温、屋面找坡"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">最低防火等级</label>
            <a-input
              v-model:value="form.fire_rating"
              placeholder="如 A2（低于此等级将被排除）"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">导热系数上限 W/(m·K)</label>
            <a-input-number
              v-model:value="form.max_thermal_conductivity"
              :min="0"
              :step="0.001"
              placeholder="如 0.05"
              style="width: 100%"
            />
          </div>

          <div class="field">
            <label class="field-label">执行标准 / 认证</label>
            <a-input
              v-model:value="form.standard"
              placeholder="如 EN 14303 / GB/T 25975"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">使用环境</label>
            <a-input
              v-model:value="form.environment"
              placeholder="如 高温 / 潮湿 / 腐蚀"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">目标国家 / 市场</label>
            <a-input
              v-model:value="form.country"
              placeholder="如 德国 / 美国"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">安装方式</label>
            <a-input
              v-model:value="form.installation"
              placeholder="如 粘贴 / 干挂 / 装配式"
              allow-clear
            />
          </div>

          <div class="field">
            <label class="field-label">返回条数 (top_n)</label>
            <a-input-number
              v-model:value="form.top_n"
              :min="1"
              :max="50"
              :step="1"
              style="width: 100%"
            />
          </div>

          <div class="field-full form-actions">
            <a-button type="primary" html-type="submit" :loading="loading" block>
              开始匹配
            </a-button>
          </div>
        </form>
      </a-card>

      <!-- 错误提示 -->
      <a-alert
        v-if="apiError"
        type="error"
        :message="apiError"
        show-icon
        class="finder-alert"
      />

      <!-- 结果区 -->
      <a-spin :spinning="loading" tip="匹配计算中...">
        <div v-if="result" class="finder-results">
          <div class="result-summary">
            共 <b>{{ result.total_products }}</b> 个在售产品参与匹配，
            推荐 <b>{{ result.matches.length }}</b> 条，
            排除 <b>{{ result.rejected.length }}</b> 条。
          </div>

          <!-- 匹配结果 -->
          <a-empty
            v-if="result.matches.length === 0"
            description="未找到满足条件且达到推荐阈值的产品，请放宽约束后重试"
          />

          <a-card
            v-for="m in result.matches"
            :key="m.product_id"
            class="match-card"
            :bordered="false"
          >
            <div class="match-head">
              <div class="match-head-main">
                <h3 class="match-name">{{ m.name }}</h3>
                <div class="match-meta">
                  <a-tag :color="tierColor(m.tier)">{{ m.tier }}</a-tag>
                  <span class="match-score">综合分 <b>{{ m.score }}</b> / 100</span>
                </div>
                <div class="match-fields">
                  <span v-if="m.fire_rating">防火：{{ m.fire_rating }}</span>
                  <span v-if="m.thermal_conductivity">导热：{{ m.thermal_conductivity }}</span>
                  <span v-if="m.slug">slug：{{ m.slug }}</span>
                </div>
              </div>
              <div v-if="m.image_url" class="match-img">
                <img :src="m.image_url" :alt="m.name" loading="lazy" />
              </div>
            </div>

            <div class="dims">
              <div v-for="(val, key) in m.dimensions" :key="key" class="dim">
                <span class="dim-label">{{ dimLabel(key as string) }}</span>
                <a-progress
                  :percent="Math.round(val as number)"
                  :show-info="false"
                  size="small"
                  :stroke-color="dimColor(val as number)"
                />
                <span class="dim-val">{{ Math.round(val as number) }}</span>
              </div>
            </div>

            <a-divider style="margin: 10px 0" />

            <div class="evidence">
              <div v-for="(e, i) in m.evidence" :key="i" class="evidence-item">• {{ e }}</div>
            </div>

            <a-alert
              v-if="m.explanation"
              type="info"
              :message="m.explanation"
              show-icon
              class="explanation"
            />
          </a-card>

          <!-- 被拒绝的产品 -->
          <a-card
            v-if="result.rejected.length"
            class="rejected-card"
            :bordered="false"
            title="未通过硬条件过滤的产品"
          >
            <div v-for="(r, i) in result.rejected" :key="i" class="rejected-item">
              <span class="rejected-name">{{ r.name }}</span>
              <span class="rejected-reason">{{ r.reason }}</span>
            </div>
          </a-card>
        </div>
      </a-spin>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  Alert as AAlert,
  Button as AButton,
  Card as ACard,
  Divider as ADivider,
  Empty as AEmpty,
  Input as AInput,
  InputNumber as AInputNumber,
  Progress as AProgress,
  Spin as ASpin,
  Tag as ATag,
} from 'ant-design-vue'
import { useApi } from '~/composables/useApi'
import { useSeoMeta } from '#imports'

useSeoMeta({
  title: '产品匹配引擎 - 优丁建材',
  description:
    '输入应用场景与防火、导热、标准等技术约束，基于真实产品参数智能匹配推荐建材产品。',
})

interface MatchItem {
  product_id: string
  name: string
  slug: string
  image_url?: string | null
  fire_rating?: string | null
  thermal_conductivity?: string | null
  score: number
  tier: string
  dimensions: Record<string, number>
  evidence: string[]
  explanation: string
}

interface RejectedItem {
  product_id: string
  name: string
  reason: string
}

interface MatchResult {
  query: Record<string, unknown>
  total_products: number
  matches: MatchItem[]
  rejected: RejectedItem[]
}

const api = useApi()

const form = reactive({
  application: '',
  fire_rating: '',
  max_thermal_conductivity: null as number | null,
  standard: '',
  environment: '',
  country: '',
  installation: '',
  top_n: 5,
})

const loading = ref(false)
const apiError = ref('')
const result = ref<MatchResult | null>(null)

const DIM_LABELS: Record<string, string> = {
  fireRating: '防火',
  standard: '标准',
  application: '应用',
  environment: '环境',
  market: '市场',
  installation: '安装',
  commercial: '商务',
  availability: '在售',
}

function dimLabel(key: string): string {
  return DIM_LABELS[key] || key
}

function tierColor(tier: string): string {
  if (tier === '推荐') return 'success'
  if (tier === '备选') return 'orange'
  return 'default'
}

function dimColor(val: number): string {
  if (val >= 75) return '#52c41a'
  if (val >= 55) return '#fa8c16'
  return '#ff4d4f'
}

async function onSubmit(): Promise<void> {
  if (!form.application.trim()) {
    apiError.value = '请填写应用场景（必填）'
    return
  }
  loading.value = true
  apiError.value = ''
  result.value = null
  try {
    const payload = {
      application: form.application.trim(),
      fire_rating: form.fire_rating || null,
      max_thermal_conductivity: form.max_thermal_conductivity ?? null,
      standard: form.standard || null,
      environment: form.environment || null,
      country: form.country || null,
      installation: form.installation || null,
      top_n: form.top_n || 5,
    }
    // useApi 自动解包 { code:0, data } 返回 data
    result.value = (await api.post<MatchResult>(
      '/matching/product-match',
      payload,
      { skipAuth: true },
    )) as MatchResult
  } catch (e: unknown) {
    apiError.value = e instanceof Error ? e.message : '匹配请求失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.finder-page {
  min-height: 100vh;
  background: var(--color-bg, #f5f7fa);
  padding-bottom: 64px;
}

.finder-hero {
  padding: 32px 16px 8px;
  background: var(--color-gradient-hero, linear-gradient(135deg, #ff6448, #3dead7));
}

.finder-hero-inner {
  max-width: 960px;
  margin: 0 auto;
  color: #fff;
}

.finder-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
}

.finder-sub {
  font-size: 14px;
  line-height: 1.7;
  opacity: 0.92;
  margin: 0;
}

.finder-body {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.finder-form-card {
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.finder-form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
}

.req {
  color: #ff4d4f;
}

.form-actions {
  margin-top: 4px;
}

.finder-alert {
  border-radius: var(--radius-md, 8px);
}

.result-summary {
  font-size: 14px;
  color: var(--color-text-secondary, #4b5563);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border-light, #eee);
  border-radius: var(--radius-md, 8px);
  padding: 12px 16px;
}

.match-card {
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.match-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.match-head-main {
  flex: 1;
  min-width: 0;
}

.match-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--color-text-primary, #1f2937);
}

.match-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.match-score {
  font-size: 13px;
  color: var(--color-text-secondary, #4b5563);
}

.match-score b {
  color: var(--color-primary, #ff6448);
  font-size: 15px;
}

.match-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-tertiary, #9ca3af);
}

.match-img {
  width: 96px;
  height: 96px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: #f0f0f0;
}

.match-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.dims {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 16px;
  margin: 4px 0;
}

.dim {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dim-label {
  width: 32px;
  font-size: 12px;
  color: var(--color-text-tertiary, #9ca3af);
  flex-shrink: 0;
}

.dim :deep(.ant-progress) {
  flex: 1;
}

.dim-val {
  width: 30px;
  text-align: right;
  font-size: 12px;
  color: var(--color-text-secondary, #4b5563);
  flex-shrink: 0;
}

.evidence {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--color-text-secondary, #4b5563);
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 10px 12px;
}

.explanation {
  margin-top: 10px;
  border-radius: 8px;
}

.rejected-card {
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.rejected-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-border-light, #eee);
  font-size: 13px;
}

.rejected-item:last-child {
  border-bottom: none;
}

.rejected-name {
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
}

.rejected-reason {
  color: #ff4d4f;
  text-align: right;
}

@media (max-width: 640px) {
  .finder-form {
    grid-template-columns: 1fr;
  }
  .dims {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
