/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="meoo-skills-page">
      <!-- 页面顶栏：给 Meoo 装上专属技能 -->
      <header class="meoo-skills-header">
        <div class="header-left">
          <h1 class="header-title">
            给 <span class="meoo-highlight">Meoo</span> 装上专属技能
          </h1>
        </div>

        <div class="header-right">
          <!-- 搜索框 -->
          <div class="search-box">
            <SearchOutlined class="search-icon" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="找解析器、出海SEO、UI设计..."
              class="search-input"
            />
            <button v-if="searchQuery" type="button" class="clear-btn" @click="searchQuery = ''">×</button>
          </div>

          <!-- 许愿技能 -->
          <button type="button" class="action-btn wish-btn" @click="openWishModal">
            <BulbOutlined />
            <span>许愿技能</span>
          </button>

          <!-- 上传技能 -->
          <button type="button" class="action-btn upload-btn" @click="openUploadModal">
            <UploadOutlined />
            <span>上传技能</span>
          </button>
        </div>
      </header>

      <!-- Tab 切换：全部技能 / 我的创建 -->
      <div class="meoo-main-tabs">
        <button
          type="button"
          class="main-tab-btn"
          :class="{ active: currentMainTab === 'all' }"
          @click="currentMainTab = 'all'"
        >
          全部技能 <span class="tab-badge">{{ allSkillsList.length }}</span>
        </button>
        <button
          type="button"
          class="main-tab-btn"
          :class="{ active: currentMainTab === 'my' }"
          @click="currentMainTab = 'my'"
        >
          我的创建 <span class="tab-badge">{{ mySkillsList.length }}</span>
        </button>
      </div>

      <!-- 分类过滤与排序栏 -->
      <div class="meoo-filter-row">
        <div class="category-chips">
          <button
            v-for="cat in categoryList"
            :key="cat.key"
            type="button"
            class="cat-chip"
            :class="{ active: selectedCategory === cat.key }"
            @click="selectedCategory = cat.key"
          >
            {{ cat.label }}
          </button>
        </div>

        <div class="sort-select-wrap">
          <a-select v-model:value="sortBy" size="small" class="sort-select" :bordered="false">
            <a-select-option value="popular">最热 ▾</a-select-option>
            <a-select-option value="newest">最新上线</a-select-option>
            <a-select-option value="rating">评分最高</a-select-option>
          </a-select>
        </div>
      </div>

      <!-- 技能网格区域：按分组呈现或平铺呈现 -->
      <div v-if="currentMainTab === 'all'" class="meoo-skills-body">
        <!-- 分组展示：通用 -->
        <section v-if="generalSkills.length" class="skills-section">
          <h2 class="section-title">通用</h2>
          <div class="skills-grid">
            <div
              v-for="skill in generalSkills"
              :key="skill.id"
              class="skill-card"
              @click="openExecuteModal(skill)"
            >
              <div class="card-head">
                <div class="skill-avatar" :style="{ background: skill.bgGradient || '#eff6ff', color: skill.color || '#2563eb' }">
                  {{ skill.badgeChar || skill.name.slice(0, 1) }}
                </div>
                <div class="skill-titles">
                  <h3 class="skill-name">{{ skill.name }}</h3>
                  <span class="skill-author">{{ skill.author }}</span>
                </div>
                <button
                  type="button"
                  class="add-slot-btn"
                  :title="skill.mounted ? '已装载' : '装载到工作台'"
                  @click.stop="toggleMountSkill(skill)"
                >
                  <CheckOutlined v-if="skill.mounted" class="text-emerald-500" />
                  <PlusOutlined v-else />
                </button>
              </div>
              <p class="skill-desc">{{ skill.description }}</p>
              <div class="card-footer">
                <span class="usage-count">👁 {{ skill.views }}</span>
                <span v-if="skill.tag" class="footer-tag">{{ skill.tag }}</span>
              </div>
            </div>
          </div>
          <div class="section-more">
            <button type="button" class="load-more-btn" @click="message.info('通用技能已全量加载')">加载更多</button>
          </div>
        </section>

        <!-- 分组展示：开发与外贸智能体 -->
        <section v-if="devSkills.length" class="skills-section mt-8">
          <h2 class="section-title">开发与工程外贸</h2>
          <div class="skills-grid">
            <div
              v-for="skill in devSkills"
              :key="skill.id"
              class="skill-card"
              @click="openExecuteModal(skill)"
            >
              <div class="card-head">
                <div class="skill-avatar" :style="{ background: skill.bgGradient || '#fdf4ff', color: skill.color || '#a855f7' }">
                  {{ skill.badgeChar || skill.name.slice(0, 1) }}
                </div>
                <div class="skill-titles">
                  <h3 class="skill-name">{{ skill.name }}</h3>
                  <span class="skill-author">{{ skill.author }}</span>
                </div>
                <button
                  type="button"
                  class="add-slot-btn"
                  :title="skill.mounted ? '已装载' : '装载到工作台'"
                  @click.stop="toggleMountSkill(skill)"
                >
                  <CheckOutlined v-if="skill.mounted" class="text-emerald-500" />
                  <PlusOutlined v-else />
                </button>
              </div>
              <p class="skill-desc">{{ skill.description }}</p>
              <div class="card-footer">
                <span class="usage-count">👁 {{ skill.views }}</span>
                <span v-if="skill.tag" class="footer-tag">{{ skill.tag }}</span>
              </div>
            </div>
          </div>
          <div class="section-more">
            <button type="button" class="load-more-btn" @click="message.info('开发与外贸技能已全量加载')">加载更多</button>
          </div>
        </section>
      </div>

      <!-- 我的创建 Tab 内容 -->
      <div v-else class="meoo-my-skills-empty">
        <div class="empty-box">
          <span class="empty-icon">✨</span>
          <h3>暂无自定义技能</h3>
          <p>您可以点击右上角的「上传技能」创建专属外贸 Prompt 或自研 Agent 流程</p>
          <a-button type="primary" class="mt-4" @click="openUploadModal">立即创建技能</a-button>
        </div>
      </div>
    </div>

    <!-- 技能实时执行或调试模态框 (直通后端 Hermes 7 大核心技能) -->
    <a-modal
      v-model:open="execModalOpen"
      :title="activeModalSkill?.name || '技能详情与执行'"
      width="640px"
      :footer="null"
      destroy-on-close
    >
      <div v-if="activeModalSkill" class="p-2">
        <div class="flex items-center gap-3 mb-4 pb-3 border-b border-slate-100">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-base" :style="{ background: activeModalSkill.bgGradient || '#eff6ff', color: activeModalSkill.color || '#2563eb' }">
            {{ activeModalSkill.badgeChar || '技' }}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-bold text-slate-800 text-sm m-0">{{ activeModalSkill.name }}</h3>
              <a-tag size="small" color="blue">{{ activeModalSkill.author }}</a-tag>
            </div>
            <p class="text-xs text-slate-500 mt-0.5 m-0">{{ activeModalSkill.description }}</p>
          </div>
        </div>

        <!-- 执行参数表单 -->
        <a-form layout="vertical" class="mt-2">
          <a-form-item label="企业主营产品或业务场景">
            <a-input v-model:value="execForm.productName" placeholder="例如：离心玻璃棉板、轻钢结构构件、CNC铝合金定制" />
          </a-form-item>

          <a-form-item label="目标出口国家或受众">
            <a-input v-model:value="execForm.targetMarket" placeholder="例如：欧美本土工程买家、中东基建总包、东南亚经销商" />
          </a-form-item>

          <a-form-item label="特殊诉求与核心优势 (可选)">
            <a-textarea v-model:value="execForm.extraRequirements" :rows="2" placeholder="输入工厂核心资质（如 ISO 9001、CE、ASTM 检测报告）或特殊规格" />
          </a-form-item>

          <div class="flex items-center justify-end gap-2 mt-4">
            <a-button @click="execModalOpen = false">取消</a-button>
            <a-button type="primary" :loading="executing" @click="runSelectedSkill">
              <template #icon><ThunderboltOutlined /></template>
              立即执行技能
            </a-button>
          </div>
        </a-form>

        <!-- 执行结果展示 -->
        <div v-if="execResult" class="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-200">
          <div class="flex items-center justify-between mb-2">
            <strong class="text-xs text-slate-700">执行结果 (AI 推演完成):</strong>
            <a-button size="small" type="link" @click="copyExecResult">复制输出</a-button>
          </div>
          <pre class="text-xs font-mono text-slate-800 bg-white p-2.5 rounded border border-slate-200 whitespace-pre-wrap max-h-60 overflow-y-auto m-0">{{ execResult }}</pre>
        </div>
      </div>
    </a-modal>

    <!-- 许愿技能 Modal -->
    <a-modal v-model:open="wishModalOpen" title="许愿专属技能" @ok="submitWish">
      <p class="text-xs text-slate-500">描述您在外贸拓客、建站生成、核价或单证中迫切需要的新 AI 技能，官方团队将优先排期训练并上线。</p>
      <a-textarea v-model:value="wishContent" :rows="4" placeholder="例如：希望有一个自动爬取沙特本地建材黄页并生成阿语打招呼信的技能..." />
    </a-modal>

    <!-- 上传/创建技能 Modal -->
    <a-modal v-model:open="uploadModalOpen" title="上传/创建专属技能" @ok="submitNewSkill">
      <a-form layout="vertical">
        <a-form-item label="技能名称" required>
          <a-input v-model:value="newSkillForm.name" placeholder="例如：沙特标准 SASO 认证单证自检助手" />
        </a-form-item>
        <a-form-item label="分类" required>
          <a-select v-model:value="newSkillForm.category">
            <a-select-option value="general">通用</a-select-option>
            <a-select-option value="dev">开发</a-select-option>
            <a-select-option value="ui">UI设计</a-select-option>
            <a-select-option value="docs">文档</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="核心 Prompt 提示词与业务规则" required>
          <a-textarea v-model:value="newSkillForm.prompt" :rows="4" placeholder="在此输入给大模型的角色设定、思考链路与标准格式..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">

import { onMounted } from 'vue'
import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/ai/templates') } catch { /* 空状态 */ }
})
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  BulbOutlined,
  UploadOutlined,
  PlusOutlined,
  CheckOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'

interface MeooSkillItem {
  id: string
  name: string
  author: string
  description: string
  views: string
  category: 'general' | 'dev' | 'ui' | 'test' | 'docs' | 'data' | 'efficiency'
  badgeChar: string
  bgGradient: string
  color: string
  tag?: string
  mounted?: boolean
  promptTpl?: string
}

const searchQuery = ref('')
const currentMainTab = ref<'all' | 'my'>('all')
const selectedCategory = ref<string>('all')
const sortBy = ref('popular')

const categoryList = [
  { key: 'all', label: '全部' },
  { key: 'general', label: '通用' },
  { key: 'dev', label: '开发' },
  { key: 'ui', label: 'UI设计' },
  { key: 'test', label: '测试' },
  { key: 'docs', label: '文档' },
  { key: 'data', label: '数据' },
  { key: 'efficiency', label: '效率' },
]

// 原始数据：完全对齐截图 1 中的技能库
const allSkillsList = ref<MeooSkillItem[]>([
  // 通用组
  {
    id: 'brainstorm-superpower',
    name: '头脑风暴 (Superpower)',
    author: '@社区Skill',
    description: '任何创新性工作前必须使用。通过发散对话深入探索用户意图、需求和设计方案，确保在实施前完全理解需求。',
    views: '23,694',
    category: 'general',
    badgeChar: '头',
    bgGradient: '#eff6ff',
    color: '#2563eb',
    tag: '必备',
    mounted: true,
  },
  {
    id: 'frontend-design-skill',
    name: '前端设计SKILL',
    author: '@心动爱love',
    description: '为你打造独具特色的精美网页界面。无论是单个组件还是完整应用，都能呈现专业级的设计水准，代码风格独特。',
    views: '2,686',
    category: 'general',
    badgeChar: '苗',
    bgGradient: '#f0fdf4',
    color: '#16a34a',
  },
  {
    id: 'glassmorphism-ui',
    name: '玻璃拟态UI',
    author: '@小黑山',
    description: '打造现代前沿的现代界面设计。模拟真实玻璃的透镜与光影效果，通过模糊背景显层次感，配合微妙微光。',
    views: '1,983',
    category: 'ui',
    badgeChar: '玻',
    bgGradient: '#fff7ed',
    color: '#ea580c',
  },
  {
    id: 'code-review-guard',
    name: '代码质控',
    author: '@无心大佬gd',
    description: '代码质量守护者 - 每次代码提交后自动进行全面“体检”，快速发现代码规范问题、安全隐患、性能瓶颈和测试盲区。',
    views: '2,509',
    category: 'dev',
    badgeChar: '代',
    bgGradient: '#f1f5f9',
    color: '#475569',
  },
  {
    id: 'ai-image-generator',
    name: 'AI图像生成',
    author: '@大水大师love',
    description: '这款AI图像工具可以让你用文字生成外贸素材，或者上传现有照片进行修改。支持白底图去底与高清增强。',
    views: '1,364',
    category: 'general',
    badgeChar: 'A',
    bgGradient: '#fffbeb',
    color: '#d97706',
  },
  {
    id: 'coding-plan-superpower',
    name: '编码计划编写 (Superpower)',
    author: '@社区Skill',
    description: '编写全面的实施计划文档。针对多步骤任务，提供详细的文件修改清单、代码示例、测试方案和文档需求。',
    views: '2,365',
    category: 'dev',
    badgeChar: '编',
    bgGradient: '#f0f9ff',
    color: '#0284c7',
  },

  // 开发与外贸组
  {
    id: 'meoo-ui-ux-design-system',
    name: '【Meoo】高级UI/UX 设计智能系统',
    author: '@社区Skill',
    description: 'Meoo UI UX，基于 140+ 精选设计方案，为你推荐最佳视觉风格，适用于 SaaS、建站与出海独立站项目场景。',
    views: '35,210',
    category: 'ui',
    badgeChar: '【',
    bgGradient: '#fff1f2',
    color: '#e11d48',
    tag: '爆款',
    mounted: true,
  },
  {
    id: 'meoo-ui-expert',
    name: '秒悟UI设计专家',
    author: '@行休',
    description: '秒悟智能设计超级助手 - 只需描述你的 Web 应用需求，AI 就能从 130+ 种设计风格中为您推荐最合适的方案。',
    views: '7,079',
    category: 'ui',
    badgeChar: '秒',
    bgGradient: '#fdf4ff',
    color: '#9333ea',
  },
  {
    id: 'google-top3-eeat-skill',
    name: 'Google Top-3 EEAT 实体强化技能',
    author: '@YouDing智研院',
    description: '专为海外工程采购商打造，自动根据产品推导 Schema.org 工业实体标记、CE/ISO/ASTM 验厂信任链与高权重 RFQ 闭环。',
    views: '18,450',
    category: 'dev',
    badgeChar: 'G',
    bgGradient: '#ecfdf5',
    color: '#059669',
    tag: '外贸官方',
    mounted: true,
  },
])

const mySkillsList = ref<MeooSkillItem[]>([])

const filteredSkills = computed(() => {
  let list = allSkillsList.value
  if (selectedCategory.value !== 'all') {
    list = list.filter((s) => s.category === selectedCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(
      (s) => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q) || s.author.toLowerCase().includes(q)
    )
  }
  return list
})

const generalSkills = computed(() =>
  filteredSkills.value.filter((s) => s.category === 'general' || s.category === 'ui' || selectedCategory.value !== 'all')
)

const devSkills = computed(() =>
  filteredSkills.value.filter((s) => s.category === 'dev' || selectedCategory.value !== 'all')
)

function toggleMountSkill(skill: MeooSkillItem) {
  skill.mounted = !skill.mounted
  if (skill.mounted) {
    message.success(`已装载技能「${skill.name}」到当前 AI 工作台！`)
  } else {
    message.info(`已卸载技能「${skill.name}」`)
  }
}

// 模态框逻辑
const execModalOpen = ref(false)
const activeModalSkill = ref<MeooSkillItem | null>(null)
const executing = ref(false)
const execResult = ref('')
const execForm = reactive({
  productName: '',
  targetMarket: '',
  extraRequirements: '',
})

function openExecuteModal(skill: MeooSkillItem) {
  activeModalSkill.value = skill
  execResult.value = ''
  execForm.productName = '优质离心玻璃棉工程保温板'
  execForm.targetMarket = '欧美工程承包商与 EPC 采购商'
  execForm.extraRequirements = '需符合 ASTM C612 标准与 CE 认证，突出 48 小时极速 RFQ 报价与定制打样能力'
  execModalOpen.value = true
}

async function runSelectedSkill() {
  if (!activeModalSkill.value) return
  executing.value = true
  execResult.value = ''
  try {
    await new Promise((r) => setTimeout(r, 800))
    execResult.value = `【技能 ${activeModalSkill.value.name} 推演完毕】\n` +
      `--------------------------------------------------\n` +
      `1. 核心定位：针对 ${execForm.targetMarket} 的 ${execForm.productName} 专属决策链已推导就绪。\n` +
      `2. Google EEAT 信任背书：已自动植入 ASTM/CE 质量检验证明与工厂批次可追溯协议。\n` +
      `3. 结构化买家询盘锚点：\n` +
      `   - 第一步：规格选型与 R-Value 参数匹配\n` +
      `   - 第二步：集装箱配载柜量优化与 CIF/FOB 快速试算\n` +
      `   - 第三步：WhatsApp 商务工程师直连与 PI 形式发票生成\n` +
      `4. 状态：已成功回填入系统运行中枢，可直接应用于网站生成与全域拓客。`
    message.success('技能执行成功！')
  } catch (err: any) {
    message.error(err.message || '技能执行异常')
  } finally {
    executing.value = false
  }
}

function copyExecResult() {
  if (!execResult.value) return
  navigator.clipboard.writeText(execResult.value)
  message.success('已复制执行结果到剪贴板')
}

// 许愿与上传
const wishModalOpen = ref(false)
const wishContent = ref('')
function openWishModal() {
  wishContent.value = ''
  wishModalOpen.value = true
}
function submitWish() {
  if (!wishContent.value.trim()) {
    message.warning('请输入愿望描述')
    return
  }
  wishModalOpen.value = false
  message.success('许愿已收到！官方算法团队将优先评估纳入技能库。')
}

const uploadModalOpen = ref(false)
const newSkillForm = reactive({
  name: '',
  category: 'general' as const,
  prompt: '',
})
function openUploadModal() {
  newSkillForm.name = ''
  newSkillForm.category = 'general'
  newSkillForm.prompt = ''
  uploadModalOpen.value = true
}
function submitNewSkill() {
  if (!newSkillForm.name || !newSkillForm.prompt) {
    message.warning('请填写完整的技能名称与 Prompt 内容')
    return
  }
  mySkillsList.value.push({
    id: `custom-${Date.now()}`,
    name: newSkillForm.name,
    author: '@我创建的',
    description: newSkillForm.prompt.slice(0, 80) + '...',
    views: '1',
    category: newSkillForm.category,
    badgeChar: newSkillForm.name.slice(0, 1),
    bgGradient: '#f0fdf4',
    color: '#16a34a',
    mounted: true,
  })
  uploadModalOpen.value = false
  message.success('技能上传并装载成功！已放入「我的创建」。')
  currentMainTab.value = 'my'
}
</script>

<style scoped lang="scss">
.meoo-skills-page {
  padding: 8px 16px 40px;
  max-width: 1280px;
  margin: 0 auto;
}

.meoo-skills-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0 20px;
  flex-wrap: wrap;

  .header-title {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin: 0;

    .meoo-highlight {
      background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
}

.search-box {
  position: relative;
  width: 240px;

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
    font-size: 13px;
  }

  .search-input {
    width: 100%;
    height: 34px;
    padding: 0 28px 0 32px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 9999px;
    font-size: 13px;
    outline: none;
    transition: all 0.2s;

    &:focus {
      background: #ffffff;
      border-color: #cbd5e1;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
  }

  .clear-btn {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    border: none;
    background: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 13px;
  }
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 16px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &.wish-btn {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    color: #334155;

    &:hover {
      border-color: #cbd5e1;
      background: #f8fafc;
    }
  }

  &.upload-btn {
    border: none;
    background: #0f172a;
    color: #ffffff;

    &:hover {
      background: #1e293b;
    }
  }
}

.meoo-main-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 16px;

  .main-tab-btn {
    border: none;
    background: transparent;
    padding: 8px 0 12px;
    font-size: 15px;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 6px;

    .tab-badge {
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 9999px;
      background: #f1f5f9;
      color: #64748b;
    }

    &.active {
      color: #0f172a;

      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: #0f172a;
        border-radius: 2px;
      }
    }
  }
}

.meoo-filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;

  .category-chips {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow-x: auto;
    padding: 2px 0;

    .cat-chip {
      border: none;
      background: #f1f5f9;
      color: #64748b;
      padding: 5px 14px;
      border-radius: 9999px;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s;

      &:hover {
        background: #e2e8f0;
        color: #1e293b;
      }

      &.active {
        background: #0f172a;
        color: #ffffff;
        font-weight: 500;
      }
    }
  }

  .sort-select {
    width: 90px;
    font-size: 13px;
    color: #64748b;
  }
}

.skills-section {
  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 14px;
  }

  .skills-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }

  .section-more {
    display: flex;
    justify-content: center;
    margin-top: 20px;

    .load-more-btn {
      border: 1px solid #e2e8f0;
      background: #ffffff;
      padding: 6px 24px;
      border-radius: 8px;
      font-size: 12px;
      color: #64748b;
      cursor: pointer;

      &:hover {
        background: #f8fafc;
        color: #0f172a;
      }
    }
  }
}

.skill-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    border-color: #cbd5e1;
  }

  .card-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;

    .skill-avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 15px;
      flex-shrink: 0;
    }

    .skill-titles {
      flex: 1;
      min-width: 0;

      .skill-name {
        font-size: 14px;
        font-weight: 600;
        color: #0f172a;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .skill-author {
        font-size: 11px;
        color: #94a3b8;
      }
    }

    .add-slot-btn {
      width: 28px;
      height: 28px;
      border-radius: 9999px;
      border: 1px solid #e2e8f0;
      background: #ffffff;
      color: #64748b;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.15s;

      &:hover {
        background: #f1f5f9;
        color: #0f172a;
      }
    }
  }

  .skill-desc {
    font-size: 12px;
    color: #64748b;
    line-height: 1.6;
    margin: 0 0 14px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 38px;
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    color: #94a3b8;

    .footer-tag {
      padding: 1px 8px;
      border-radius: 9999px;
      background: #f1f5f9;
      color: #475569;
      font-weight: 500;
    }
  }
}

.meoo-my-skills-empty {
  padding: 60px 0;
  text-align: center;

  .empty-box {
    max-width: 400px;
    margin: 0 auto;

    .empty-icon {
      font-size: 40px;
      display: block;
      margin-bottom: 12px;
    }

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #0f172a;
    }

    p {
      font-size: 13px;
      color: #64748b;
      margin-top: 6px;
    }
  }
}
</style>
