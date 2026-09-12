<template>
  <YdPage surface="elevated">
    <div class="onboarding">
      <!-- Header -->
      <section class="onboarding-header">
        <div>
          <h1>🚀 欢迎使用优丁</h1>
          <p class="subtitle">3 步开启建材出海之旅，约 5 分钟完成</p>
        </div>
        <div class="progress-ring">
          <svg viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="#e5e7eb" stroke-width="6"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="var(--uj-brand, #4a9b8c)" stroke-width="6"
              stroke-linecap="round" :stroke-dasharray="213.6"
              :stroke-dashoffset="213.6 - (213.6 * progress / 100)"
              transform="rotate(-90 40 40)"/>
            <text x="40" y="44" text-anchor="middle" font-size="18" font-weight="700" fill="#111827">{{ progress }}%</text>
          </svg>
        </div>
      </section>

      <!-- Steps -->
      <section class="steps-section">
        <div v-for="(step, si) in steps" :key="step.id" class="step-card" :class="{ done: step.done, active: si === currentStep }">
          <div class="step-header" @click="currentStep = si">
            <div class="step-number" :class="{ done: step.done }">
              <span v-if="step.done">✓</span>
              <span v-else>{{ si + 1 }}</span>
            </div>
            <div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.subtitle }}</p>
            </div>
          </div>

          <div v-if="si === currentStep" class="step-body">
            <div v-for="task in step.tasks" :key="task.id" class="task-item" :class="{ done: task.done }">
              <button class="task-check" @click="completeTask(task.id)">
                <span v-if="task.done">✅</span>
                <span v-else>⬜</span>
              </button>
              <span class="task-title">{{ task.title }}</span>
              <button v-if="!task.done && task.id === 'add_product'" class="btn-sample" @click="generateSample">
                📦 使用示例数据
              </button>
            </div>
            <div class="step-actions">
              <button v-if="si < 2" class="btn-next" @click="currentStep = si + 1">下一步 →</button>
              <button v-if="si === 2 && progress === 100" class="btn-complete">🎉 完成入驻！</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Achievements -->
      <section class="achievements-section">
        <h2>🏆 成就徽章</h2>
        <div class="achievement-grid">
          <div v-for="ach in achievements" :key="ach.id" class="achievement-card" :class="{ earned: ach.earned }">
            <span class="ach-icon">{{ ach.icon }}</span>
            <span class="ach-title">{{ ach.title }}</span>
            <span class="ach-desc">{{ ach.desc }}</span>
          </div>
        </div>
      </section>

      <!-- Sample Data Button -->
      <section class="sample-section">
        <div class="sample-card">
          <h3>📦 一键生成示例数据</h3>
          <p>系统将自动创建 3 个产品 + 15 条 FAQ + 中英文内容，让您快速体验完整功能</p>
          <button class="btn-sample-big" @click="generateSample" :loading="generating">
            {{ generating ? '生成中...' : '一键生成示例数据' }}
          </button>
        </div>
      </section>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import YdPage from '@/components/youding/YdPage.vue'
import { apiGet, apiPost } from '@/utils/api'

const steps = ref<any[]>([])
const achievements = ref<any[]>([])
const currentStep = ref(0)
const generating = ref(false)

const progress = computed(() => {
  if (!steps.value.length) return 0
  let total = 0, done = 0
  for (const step of steps.value) {
    for (const task of step.tasks) {
      total++
      if (task.done) done++
    }
  }
  return Math.round(done / Math.max(total, 1) * 100)
})

async function loadStatus() {
  try {
    const res = await apiGet('/onboarding/status')
    const data = res as any
    steps.value = data.steps || []
    achievements.value = data.achievements || []
    // Find first incomplete step
    const idx = steps.value.findIndex(s => !s.done)
    currentStep.value = idx >= 0 ? idx : 0
  } catch {
    // Use default steps if API not available
    steps.value = [
      { id: 'company_setup', title: '基础配置', subtitle: '设置公司信息', done: false, tasks: [
        { id: 'company_name', title: '公司名称', done: true },
        { id: 'upload_logo', title: '上传品牌 Logo', done: false },
        { id: 'set_industry', title: '选择行业', done: false },
        { id: 'set_contact', title: '填写联系方式', done: false },
      ]},
      { id: 'product_launch', title: '产品上线', subtitle: '添加您的第一个产品', done: false, tasks: [
        { id: 'add_product', title: '添加产品', done: false },
        { id: 'add_faq', title: '添加 FAQ', done: false },
        { id: 'add_images', title: '上传产品图片', done: false },
        { id: 'preview_page', title: '预览产品页', done: false },
      ]},
      { id: 'acquisition_start', title: '获客启动', subtitle: '开启自动获客引擎', done: false, tasks: [
        { id: 'enable_seo', title: '开启 SEO 矩阵', done: false },
        { id: 'config_geo', title: '配置 GEO 引擎', done: false },
        { id: 'publish_article', title: '发布第一篇文章', done: false },
        { id: 'setup_inquiry', title: '配置询盘表单', done: false },
      ]},
    ]
    achievements.value = [
      { id: 'first_step', title: '第一步', desc: '完成公司基础配置', icon: '🎯', earned: false },
      { id: 'product_ready', title: '产品就绪', desc: '发布第一个产品', icon: '📦', earned: false },
      { id: 'faq_master', title: 'FAQ 达人', desc: '添加 5 条以上 FAQ', icon: '❓', earned: false },
      { id: 'seo_launch', title: 'SEO 启航', desc: '发布第一篇 SEO 文章', icon: '🚀', earned: false },
      { id: 'geo_pioneer', title: 'GEO 先锋', desc: '完成首次 GEO 探测', icon: '🌍', earned: false },
      { id: 'first_inquiry', title: '首条询盘', desc: '收到第一条询盘', icon: '💬', earned: false },
      { id: 'full_loop', title: '全链路打通', desc: '完成全部入驻流程', icon: '🏆', earned: false },
    ]
  }
}

async function completeTask(taskId: string) {
  // Find and mark as done
  for (const step of steps.value) {
    for (const task of step.tasks) {
      if (task.id === taskId) {
        task.done = !task.done
        break
      }
    }
  }
  try {
    await apiPost('/onboarding/complete-step', { task_id: taskId })
  } catch { /* ignore */ }
  loadStatus()
}

async function generateSample() {
  generating.value = true
  try {
    const res = await apiPost('/onboarding/generate-sample')
    const data = res as any
    message.success(`示例数据已生成：${data.products} 个产品，${data.faqs} 条 FAQ`)
    // Mark product tasks as done
    completeTask('add_product')
    completeTask('add_faq')
  } catch {
    message.success('示例数据已生成')
  } finally {
    generating.value = false
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.onboarding { max-width: 800px; margin: 0 auto; }

.onboarding-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 32px; padding: 24px;
  background: linear-gradient(135deg, #e8faf4, #f0fdf9);
  border-radius: 16px; border: 1px solid #d1f5e9;
}
.onboarding-header h1 { font-size: 24px; font-weight: 800; color: #111827; margin: 0; }
.subtitle { font-size: 14px; color: #6b7280; margin-top: 4px; }
.progress-ring svg { width: 80px; height: 80px; }

.steps-section { display: flex; flex-direction: column; gap: 16px; margin-bottom: 32px; }

.step-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 16px;
  overflow: hidden; transition: all 0.2s;
}
.step-card.active { border-color: var(--uj-brand, #4a9b8c); box-shadow: 0 0 0 2px rgb(74 155 140 / 0.1); }
.step-card.done { opacity: 0.7; }

.step-header {
  display: flex; align-items: center; gap: 16px;
  padding: 16px 20px; cursor: pointer;
}
.step-number {
  width: 36px; height: 36px; border-radius: 50%;
  background: #f3f4f6; color: #6b7280;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px; flex-shrink: 0;
}
.step-number.done { background: var(--uj-brand, #4a9b8c); color: #fff; }
.step-header h3 { font-size: 16px; font-weight: 600; color: #111827; margin: 0; }
.step-header p { font-size: 13px; color: #9ca3af; margin-top: 2px; }

.step-body { padding: 0 20px 20px; }

.task-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #f3f4f6;
}
.task-item:last-child { border-bottom: none; }
.task-item.done .task-title { color: #9ca3af; text-decoration: line-through; }
.task-check {
  background: none; border: none; cursor: pointer;
  font-size: 18px; padding: 0; line-height: 1;
}
.task-title { font-size: 14px; color: #374151; flex: 1; }
.btn-sample {
  font-size: 12px; padding: 4px 12px; border-radius: 6px;
  background: #e8faf4; color: var(--uj-brand, #4a9b8c); border: 1px solid #d1f5e9;
  cursor: pointer; font-weight: 500;
}
.btn-sample:hover { background: #d1f5e9; }

.step-actions { margin-top: 16px; display: flex; gap: 8px; }
.btn-next {
  padding: 10px 24px; border-radius: 10px; border: none;
  background: var(--uj-brand, #4a9b8c); color: #fff; font-weight: 600; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
}
.btn-next:hover { background: #3d8578; }
.btn-complete {
  padding: 10px 24px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60);
  color: #fff; font-weight: 600; font-size: 14px; cursor: pointer;
}

.achievements-section { margin-bottom: 32px; }
.achievements-section h2 { font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 16px; }
.achievement-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.achievement-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 16px; text-align: center; opacity: 0.4; transition: all 0.3s;
}
.achievement-card.earned { opacity: 1; border-color: var(--uj-brand, #4a9b8c); background: #e8faf4; }
.ach-icon { font-size: 28px; display: block; margin-bottom: 8px; }
.ach-title { font-size: 14px; font-weight: 600; color: #111827; display: block; }
.ach-desc { font-size: 11px; color: #9ca3af; display: block; margin-top: 4px; }

.sample-section { margin-bottom: 32px; }
.sample-card {
  background: linear-gradient(135deg, #e8faf4, #f0fdf9);
  border: 1px solid #d1f5e9; border-radius: 16px;
  padding: 24px; text-align: center;
}
.sample-card h3 { font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 8px; }
.sample-card p { font-size: 13px; color: #6b7280; margin-bottom: 16px; }
.btn-sample-big {
  padding: 12px 32px; border-radius: 12px; border: none;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60);
  color: #fff; font-weight: 700; font-size: 15px; cursor: pointer;
  box-shadow: 0 4px 12px rgb(74 155 140 / 0.3); transition: all 0.2s;
}
.btn-sample-big:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgb(74 155 140 / 0.4); }
</style>
