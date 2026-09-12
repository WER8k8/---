<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
      <span class="mr-3">🧬</span>AI 进化引擎
    </h1>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4 mb-8">
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <div class="text-sm text-gray-500">总执行次数</div>
        <div class="text-2xl font-bold text-gray-800">{{ stats.totalRecords }}</div>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
        <div class="text-sm text-gray-500">成功率</div>
        <div class="text-2xl font-bold text-green-600">{{ stats.successRate }}%</div>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
        <div class="text-sm text-gray-500">经验条目</div>
        <div class="text-2xl font-bold text-gray-800">{{ stats.experienceCount }}</div>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
        <div class="text-sm text-gray-500">待审批</div>
        <div class="text-2xl font-bold text-yellow-600">{{ stats.pendingApprovals }}</div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex space-x-3 mb-6">
      <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm" @click="extractExperiences">
        🔍 提取经验
      </button>
      <button class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm" @click="optimizeSkills">
        ⚡ 优化 Skill
      </button>
      <button class="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm" @click="showCanaryModal = true">
        🚀 灰度发布
      </button>
    </div>

    <!-- 经验库表格 -->
    <div class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b">
        <h2 class="text-lg font-semibold">经验库</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-4 py-3 text-left">类型</th>
              <th class="px-4 py-3 text-left">标题</th>
              <th class="px-4 py-3 text-left">置信度</th>
              <th class="px-4 py-3 text-left">出现次数</th>
              <th class="px-4 py-3 text-left">状态</th>
              <th class="px-4 py-3 text-left">时间</th>
              <th class="px-4 py-3 text-left">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="exp in experiences" :key="exp.id" class="hover:bg-gray-50">
              <td class="px-4 py-3">
                <span :class="getPatternClass(exp.pattern_type)">{{ exp.pattern_type }}</span>
              </td>
              <td class="px-4 py-3 font-medium">{{ exp.title }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center">
                  <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                    <div class="bg-blue-500 h-2 rounded-full" :style="{ width: (exp.confidence * 100) + '%' }"></div>
                  </div>
                  <span>{{ (exp.confidence * 100).toFixed(0) }}%</span>
                </div>
              </td>
              <td class="px-4 py-3">{{ exp.occurrence_count }}</td>
              <td class="px-4 py-3">
                <span :class="exp.applied ? 'text-green-600 bg-green-50 px-2 py-0.5 rounded' : 'text-gray-500 bg-gray-100 px-2 py-0.5 rounded'">
                  {{ exp.applied ? '已应用' : '未应用' }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ formatTime(exp.created_at) }}</td>
              <td class="px-4 py-3">
                <button class="text-blue-500 hover:underline mr-2" @click="viewExperience(exp)">查看</button>
                <button v-if="!exp.applied" class="text-green-500 hover:underline" @click="applyExperience(exp)">应用</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="experiences.length === 0" class="px-6 py-10 text-center text-gray-400">
        暂无经验记录，请先执行一些AI任务或点击"提取经验"
      </div>
    </div>

    <!-- 灰度发布Modal -->
    <div v-if="showCanaryModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 class="text-lg font-semibold mb-4">创建灰度发布</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">选择 Skill</label>
            <select v-model="canaryForm.skillId" class="w-full px-3 py-2 border rounded">
              <option value="">选择 Skill</option>
              <option v-for="skill in skills" :key="skill.id" :value="skill.id">{{ skill.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">灰度比例 (%)</label>
            <input v-model.number="canaryForm.percentage" type="number" min="1" max="100" class="w-full px-3 py-2 border rounded" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">目标租户 (可选)</label>
            <input v-model="canaryForm.tenantIds" type="text" class="w-full px-3 py-2 border rounded" placeholder="逗号分隔的租户ID，留空则按比例随机" />
          </div>
        </div>
        <div class="mt-6 flex justify-end space-x-3">
          <button class="px-4 py-2 border rounded hover:bg-gray-50" @click="showCanaryModal = false">取消</button>
          <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" @click="deployCanary">发布</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const stats = reactive({
  totalRecords: 0,
  successRate: 0,
  experienceCount: 0,
  pendingApprovals: 0,
})

const experiences = ref<any[]>([])
const skills = ref<any[]>([])
const showCanaryModal = ref(false)

const canaryForm = reactive({
  skillId: '',
  percentage: 10,
  tenantIds: '',
})

onMounted(() => {
  fetchStats()
  fetchExperiences()
  fetchSkills()
})

async function fetchStats() {
  try {
    const { data } = await axios.get('/api/v1/evolution/stats')
    Object.assign(stats, data)
  } catch {
    // 接口可能未实现，不影响页面
  }
}

async function fetchExperiences() {
  try {
    const { data } = await axios.get('/api/v1/evolution/experiences')
    experiences.value = data.items || []
  } catch {
    experiences.value = []
  }
}

async function fetchSkills() {
  try {
    const { data } = await axios.get('/api/v1/evolution/skills')
    skills.value = data.items || []
  } catch {
    skills.value = []
  }
}

function getPatternClass(type: string) {
  const classes: Record<string, string> = {
    success_pattern: 'text-green-600 bg-green-50 px-2 py-0.5 rounded',
    failure_pattern: 'text-red-600 bg-red-50 px-2 py-0.5 rounded',
    optimization_hint: 'text-blue-600 bg-blue-50 px-2 py-0.5 rounded',
  }
  return classes[type] || 'text-gray-600 bg-gray-100 px-2 py-0.5 rounded'
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function extractExperiences() {
  await axios.post('/api/v1/evolution/experiences/extract')
  fetchExperiences()
  fetchStats()
}

async function optimizeSkills() {
  await axios.post('/api/v1/evolution/skills/optimize')
  fetchSkills()
}

async function deployCanary() {
  await axios.post('/api/v1/evolution/deploy-canary', canaryForm)
  showCanaryModal.value = false
  fetchExperiences()
}

function viewExperience(exp: any) {
  alert(JSON.stringify(exp.pattern_data, null, 2))
}

async function applyExperience(exp: any) {
  await axios.post(`/api/v1/evolution/experiences/${exp.id}/apply`)
  fetchExperiences()
}
</script>
