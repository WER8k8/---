<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <div class="flex items-center justify-between h-14">
        <h1 class="text-lg font-semibold text-gray-900">{{ $t('publish.title') }}</h1>
        <button
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="router.push('/publish/create')"
        >
          <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </MobileNavbar>

    <!-- Filter Tabs -->
    <div class="px-4 pt-4 pb-2">
      <div class="flex gap-2 overflow-x-auto">
        <button
          v-for="tab in filterTabs"
          :key="tab.value"
          class="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap"
          :class="activeFilter === tab.value ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'"
          @click="activeFilter = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Task List -->
    <div class="px-4 py-2 space-y-3">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="bg-white rounded-2xl p-4 shadow-sm"
        @click="router.push(`/publish/${task.id}`)"
      >
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <h3 class="text-sm font-semibold text-gray-900 truncate">{{ task.content_data?.title || $t('publish.untitled') }}</h3>
            <p class="text-xs text-gray-500 mt-1">{{ task.platform_id }} · {{ formatDate(task.created_at) }}</p>
          </div>
          <span
            class="px-2 py-1 rounded-full text-xs font-medium"
            :class="statusClass(task.status)"
          >
            {{ task.status }}
          </span>
        </div>

        <div class="flex items-center gap-2 text-xs text-gray-500">
          <span v-if="task.platform_post_url">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            {{ $t('publish.viewPost') }}
          </span>
          <span v-if="task.error_message" class="text-red-500">{{ task.error_message }}</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredTasks.length === 0" class="text-center py-20">
        <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-500">{{ $t('publish.noTasks') }}</p>
        <button
          class="mt-4 px-6 py-3 bg-blue-600 text-white rounded-full text-sm font-medium"
          @click="router.push('/publish/create')"
        >
          {{ $t('publish.createFirst') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t, locale } = useI18n()

const tasks = ref([])
const activeFilter = ref('all')
const pending = ref(true)

const filterTabs = [
  { label: t('publish.all'), value: 'all' },
  { label: t('publish.pending'), value: 'pending' },
  { label: t('publish.running'), value: 'running' },
  { label: t('publish.success'), value: 'success' },
  { label: t('publish.failed'), value: 'failed' },
]

const filteredTasks = computed(() => {
  if (activeFilter.value === 'all') return tasks.value
  return tasks.value.filter(t => t.status === activeFilter.value)
})

const statusClass = (status) => {
  const map = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(locale.value)
}

const fetchTasks = async () => {
  pending.value = true
  try {
    const res = await fetch('/api/v1/publish-tasks?tenant_id=00000000-0000-0000-0000-000000000001')
    tasks.value = await res.json()
  } catch (err) {
    console.error('Failed to fetch tasks:', err)
  } finally {
    pending.value = false
  }
}

onMounted(() => {
  fetchTasks()
})
</script>
