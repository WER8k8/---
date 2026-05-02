<template>
  <div class="p-6">
    <!-- 标签页切换 -->
    <div class="flex items-center gap-3 mb-6">
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'authors'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
        @click="activeTab = 'authors'"
      >
        作者管理
      </button>
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'scoring'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
        @click="activeTab = 'scoring'"
      >
        EEAT评分
      </button>
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'trust-signals'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
        @click="activeTab = 'trust-signals'"
      >
        信任信号
      </button>
    </div>

    <!-- 作者管理 -->
    <div
      v-if="activeTab === 'authors'"
      class="space-y-6"
    >
      <!-- 搜索和添加 -->
      <div class="flex items-center justify-between">
        <div class="relative flex-1 max-w-md">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索作者..."
            class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
        </div>
        <button
          class="px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          @click="showAddAuthorModal = true"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          添加作者
        </button>
      </div>

      <!-- 作者列表 -->
      <div
        v-if="authors.length > 0"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        <div
          v-for="author in filteredAuthors"
          :key="author.id"
          class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <svg
                  class="w-6 h-6 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-gray-800">
                  {{ author.name }}
                </h3>
                <p class="text-sm text-gray-500">
                  {{ author.title }}
                </p>
              </div>
            </div>
            <span
              :class="[
                'px-2 py-1 text-xs rounded-full',
                author.is_verified ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
              ]"
            >
              {{ author.is_verified ? '已认证' : '未认证' }}
            </span>
          </div>
          
          <p class="text-sm text-gray-600 mb-3 line-clamp-2">
            {{ author.bio }}
          </p>
          
          <div class="flex items-center gap-2 mb-3">
            <div class="flex-1">
              <div class="text-xs text-gray-500 mb-1">
                信任评分
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2">
                <div
                  class="bg-blue-500 h-2 rounded-full transition-all"
                  :style="{ width: author.trust_score + '%' }"
                />
              </div>
              <div class="text-right text-xs text-gray-500 mt-1">
                {{ author.trust_score }}%
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              class="flex-1 px-3 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              @click="viewAuthor(author)"
            >
              详情
            </button>
            <button
              class="px-3 py-2 text-sm text-blue-600 hover:text-blue-700"
              @click="editAuthor(author)"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              class="px-3 py-2 text-sm text-red-600 hover:text-red-700"
              @click="deleteAuthor(author.id)"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div
        v-else
        class="py-16 text-center"
      >
        <svg
          class="w-16 h-16 mx-auto text-gray-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
        <p class="text-gray-500">
          暂无作者
        </p>
        <p class="text-sm text-gray-400 mt-1">
          点击上方按钮添加第一个作者
        </p>
      </div>
    </div>

    <!-- EEAT评分 -->
    <div
      v-if="activeTab === 'scoring'"
      class="space-y-6"
    >
      <!-- 评分表单 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">
          计算EEAT评分
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">内容ID</label>
            <input
              v-model="scoreForm.contentId"
              type="text"
              placeholder="输入内容ID"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">内容类型</label>
            <select
              v-model="scoreForm.contentType"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            >
              <option value="article">
                文章
              </option>
              <option value="page">
                页面
              </option>
              <option value="product">
                产品
              </option>
            </select>
          </div>
        </div>

        <!-- 评分参数 -->
        <div class="mt-6 space-y-4">
          <h4 class="text-sm font-medium text-gray-700">
            作者信息
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">从业年限（年）</label>
              <input
                v-model.number="scoreForm.authorExperience"
                type="number"
                min="0"
                max="50"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">专业认证数量</label>
              <input
                v-model.number="scoreForm.certifications"
                type="number"
                min="0"
                max="20"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">媒体引用次数</label>
              <input
                v-model.number="scoreForm.mediaMentions"
                type="number"
                min="0"
                max="100"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
          </div>

          <h4 class="text-sm font-medium text-gray-700 mt-4">
            内容信息
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">内容深度</label>
              <select
                v-model="scoreForm.contentDepth"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="basic">
                  基础
                </option>
                <option value="intermediate">
                  中级
                </option>
                <option value="advanced">
                  高级
                </option>
                <option value="expert">
                  专家
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">行业影响力</label>
              <select
                v-model="scoreForm.industryInfluence"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="low">
                  低
                </option>
                <option value="medium">
                  中
                </option>
                <option value="high">
                  高
                </option>
                <option value="very_high">
                  非常高
                </option>
              </select>
            </div>
          </div>

          <h4 class="text-sm font-medium text-gray-700 mt-4">
            信任信号
          </h4>
          <div class="flex flex-wrap gap-3">
            <label
              v-for="signal in positiveSignals"
              :key="signal"
              class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer hover:bg-gray-200"
            >
              <input
                type="checkbox"
                :checked="scoreForm.trustSignals.includes(signal)"
                class="w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
                @change="toggleTrustSignal(signal)"
              >
              <span class="text-sm text-gray-700">{{ signalLabels[signal] || signal }}</span>
            </label>
          </div>
        </div>

        <button
          :disabled="isCalculating"
          class="mt-6 px-6 py-3 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          @click="calculateScore"
        >
          <svg
            v-if="isCalculating"
            class="animate-spin h-5 w-5"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
              fill="none"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          {{ isCalculating ? '计算中...' : '计算评分' }}
        </button>
      </div>

      <!-- 评分结果 -->
      <div
        v-if="scoreResult"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-6"
      >
        <h3 class="text-lg font-semibold text-gray-800 mb-4">
          评分结果
        </h3>
        
        <!-- 总分 -->
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-blue-600">
            <div class="text-center">
              <div class="text-4xl font-bold text-white">
                {{ scoreResult.overall_score }}
              </div>
              <div class="text-xs text-blue-100">
                综合评分
              </div>
            </div>
          </div>
        </div>

        <!-- 分项分数 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-blue-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">
              {{ scoreResult.experience_score }}
            </div>
            <div class="text-sm text-blue-700 mt-1">
              Experience
            </div>
            <div class="text-xs text-gray-500">
              经验
            </div>
          </div>
          <div class="bg-green-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-green-600">
              {{ scoreResult.expertise_score }}
            </div>
            <div class="text-sm text-green-700 mt-1">
              Expertise
            </div>
            <div class="text-xs text-gray-500">
              专业知识
            </div>
          </div>
          <div class="bg-purple-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-600">
              {{ scoreResult.authoritativeness_score }}
            </div>
            <div class="text-sm text-purple-700 mt-1">
              Authoritativeness
            </div>
            <div class="text-xs text-gray-500">
              权威性
            </div>
          </div>
          <div class="bg-orange-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-orange-600">
              {{ scoreResult.trustworthiness_score }}
            </div>
            <div class="text-sm text-orange-700 mt-1">
              Trustworthiness
            </div>
            <div class="text-xs text-gray-500">
              可信度
            </div>
          </div>
        </div>

        <!-- 改进建议 -->
        <div v-if="scoreResult.recommendations && scoreResult.recommendations.length > 0">
          <h4 class="text-sm font-medium text-gray-700 mb-3">
            改进建议
          </h4>
          <ul class="space-y-2">
            <li
              v-for="(rec, index) in scoreResult.recommendations"
              :key="index"
              class="flex items-start gap-2 text-sm text-gray-600"
            >
              <svg
                class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              {{ rec }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 信任信号管理 -->
    <div
      v-if="activeTab === 'trust-signals'"
      class="space-y-6"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 正面信号 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 class="text-lg font-semibold text-green-700 mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            正面信任信号
          </h3>
          <div class="space-y-2">
            <div
              v-for="signal in positiveSignals"
              :key="signal"
              class="flex items-center justify-between px-4 py-3 bg-green-50 rounded-lg"
            >
              <span class="text-sm text-gray-700">{{ signalLabels[signal] || signal }}</span>
              <span class="text-xs text-green-600">+3分</span>
            </div>
          </div>
        </div>

        <!-- 负面信号 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 class="text-lg font-semibold text-red-700 mb-4 flex items-center gap-2">
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            负面信任信号
          </h3>
          <div class="space-y-2">
            <div
              v-for="signal in negativeSignals"
              :key="signal"
              class="flex items-center justify-between px-4 py-3 bg-red-50 rounded-lg"
            >
              <span class="text-sm text-gray-700">{{ signalLabels[signal] || signal }}</span>
              <span class="text-xs text-red-600">-5分</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑作者弹窗 -->
    <div
      v-if="showAddAuthorModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="closeAddAuthorModal"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-semibold text-gray-800">
            {{ isEditing ? '编辑作者' : '添加作者' }}
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="closeAddAuthorModal"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div class="p-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
            <input
              v-model="authorForm.name"
              type="text"
              placeholder="请输入姓名"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">职称</label>
            <input
              v-model="authorForm.title"
              type="text"
              placeholder="请输入职称"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">公司</label>
            <input
              v-model="authorForm.company"
              type="text"
              placeholder="请输入公司名称"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">简介</label>
            <textarea
              v-model="authorForm.bio"
              rows="3"
              placeholder="请输入作者简介"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">专业领域（逗号分隔）</label>
            <input
              v-model="authorForm.expertise"
              type="text"
              placeholder="轻集料混凝土,建筑材料,工程技术"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">已认证</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                v-model="authorForm.isVerified"
                type="checkbox"
                class="sr-only peer"
              >
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500" />
            </label>
          </div>
        </div>
        <div class="p-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            class="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            @click="closeAddAuthorModal"
          >
            取消
          </button>
          <button
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            @click="saveAuthor"
          >
            {{ isEditing ? '保存修改' : '添加作者' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { seoAPI } from '@/api'

const activeTab = ref('authors')
const searchQuery = ref('')
const authors = ref<Array<{
  id: string
  name: string
  title: string
  company: string
  bio: string
  expertise_areas: string[]
  is_verified: boolean
  trust_score: number
}>>([])

const showAddAuthorModal = ref(false)
const isEditing = ref(false)
const authorForm = ref({
  id: '',
  name: '',
  title: '',
  company: '',
  bio: '',
  expertise: '',
  isVerified: false,
})

const scoreForm = ref({
  contentId: '',
  contentType: 'article',
  authorExperience: 5,
  certifications: 2,
  mediaMentions: 5,
  contentDepth: 'advanced',
  industryInfluence: 'medium',
  trustSignals: [] as string[],
})

const isCalculating = ref(false)
const scoreResult = ref<{
  experience_score: number
  expertise_score: number
  authoritativeness_score: number
  trustworthiness_score: number
  overall_score: number
  recommendations: string[]
} | null>(null)

const positiveSignals = ref<string[]>([])
const negativeSignals = ref<string[]>([])

const signalLabels: Record<string, string> = {
  'has_about_page': '有关于页面',
  'has_contact_page': '有联系页面',
  'has_privacy_policy': '有隐私政策',
  'has_terms_of_service': '有服务条款',
  'has_author_bio': '有作者简介',
  'has_author_credentials': '有作者资质',
  'has_external_references': '有外部引用',
  'has_citations': '有引用来源',
  'has_updated_date': '有更新日期',
  'has_ssl_certificate': '有SSL证书',
  'has_secure_connection': '安全连接',
  'has_social_proof': '有社会证明',
  'has_media_mentions': '有媒体报道',
  'has_industry_awards': '有行业奖项',
  'has_expert_reviews': '有专家评价',
  'missing_about_page': '缺少关于页面',
  'missing_contact_info': '缺少联系信息',
  'no_author_credibility': '无作者可信度',
  'outdated_content': '内容过时',
  'spammy_keyword_stuffing': '关键词堆砌',
  'excessive_ads': '广告过多',
  'malicious_content': '恶意内容',
  'plagiarized_content': '抄袭内容',
  'broken_links': '断链',
  'poor_grammar': '语法错误',
  'inconsistent_branding': '品牌不一致',
}

const filteredAuthors = computed(() => {
  if (!searchQuery.value) return authors.value
  const query = searchQuery.value.toLowerCase()
  return authors.value.filter(
    author => author.name.toLowerCase().includes(query) ||
              author.title.toLowerCase().includes(query) ||
              author.company.toLowerCase().includes(query)
  )
})

const toggleTrustSignal = (signal: string) => {
  const index = scoreForm.value.trustSignals.indexOf(signal)
  if (index > -1) {
    scoreForm.value.trustSignals.splice(index, 1)
  } else {
    scoreForm.value.trustSignals.push(signal)
  }
}

const loadAuthors = async () => {
  try {
    const result = await seoAPI.authors()
    if (result.data.success) {
      authors.value = result.data.data
    }
  } catch (error) {
    console.error('获取作者列表失败:', error)
  }
}

const loadTrustSignals = async () => {
  try {
    const result = await seoAPI.trustSignals()
    if (result.data.success) {
      positiveSignals.value = result.data.categories.positive
      negativeSignals.value = result.data.categories.negative
    }
  } catch (error) {
    console.error('获取信任信号失败:', error)
  }
}

const addAuthor = async () => {
  try {
    const expertiseAreas = authorForm.value.expertise.split(',').map(s => s.trim()).filter(Boolean)
    
    await seoAPI.authorCreate({
      name: authorForm.value.name,
      title: authorForm.value.title,
      company: authorForm.value.company,
      bio: authorForm.value.bio,
      expertise_areas: expertiseAreas,
      is_verified: authorForm.value.isVerified,
    })
    
    await loadAuthors()
    closeAddAuthorModal()
  } catch (error) {
    console.error('添加作者失败:', error)
  }
}

const updateAuthor = async () => {
  try {
    const expertiseAreas = authorForm.value.expertise.split(',').map(s => s.trim()).filter(Boolean)
    
    await seoAPI.authorUpdate(authorForm.value.id, {
      name: authorForm.value.name,
      title: authorForm.value.title,
      company: authorForm.value.company,
      bio: authorForm.value.bio,
      expertise_areas: expertiseAreas,
      is_verified: authorForm.value.isVerified,
    })
    
    await loadAuthors()
    closeAddAuthorModal()
  } catch (error) {
    console.error('更新作者失败:', error)
  }
}

const saveAuthor = () => {
  if (isEditing.value) {
    updateAuthor()
  } else {
    addAuthor()
  }
}

const deleteAuthor = async (id: string) => {
  if (!confirm('确定要删除这个作者吗？')) return
  
  try {
    await seoAPI.authorDelete(id)
    await loadAuthors()
  } catch (error) {
    console.error('删除作者失败:', error)
  }
}

const editAuthor = (author: typeof authors.value[0]) => {
  isEditing.value = true
  authorForm.value = {
    id: author.id,
    name: author.name,
    title: author.title || '',
    company: author.company || '',
    bio: author.bio || '',
    expertise: author.expertise_areas?.join(', ') || '',
    isVerified: author.is_verified,
  }
  showAddAuthorModal.value = true
}

const viewAuthor = (author: typeof authors.value[0]) => {
  editAuthor(author)
}

const closeAddAuthorModal = () => {
  showAddAuthorModal.value = false
  isEditing.value = false
  authorForm.value = {
    id: '',
    name: '',
    title: '',
    company: '',
    bio: '',
    expertise: '',
    isVerified: false,
  }
}

const calculateScore = async () => {
  isCalculating.value = true
  
  try {
    const contentData = {
      author_experience_years: scoreForm.value.authorExperience,
      certifications: Array(scoreForm.value.certifications).fill('cert'),
      media_mentions: Array(scoreForm.value.mediaMentions).fill('mention'),
      content_depth: scoreForm.value.contentDepth,
      industry_influence: scoreForm.value.industryInfluence,
      trust_signals: scoreForm.value.trustSignals,
      has_privacy_policy: scoreForm.value.trustSignals.includes('has_privacy_policy'),
      has_terms_of_service: scoreForm.value.trustSignals.includes('has_terms_of_service'),
    }
    
    const result = await seoAPI.score({
      content_id: scoreForm.value.contentId || 'test-content',
      content_type: scoreForm.value.contentType,
      content_data: contentData,
    })
    
    if (result.data.success) {
      scoreResult.value = result.data.score
    }
  } catch (error) {
    console.error('计算评分失败:', error)
  } finally {
    isCalculating.value = false
  }
}

onMounted(() => {
  loadAuthors()
  loadTrustSignals()
})
</script>
