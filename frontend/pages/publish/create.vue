<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <div class="flex items-center h-14">
        <button
          class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="router.back()"
        >
          <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 class="ml-2 text-base font-semibold text-gray-900">{{ $t('publish.createTitle') }}</h1>
      </div>
    </MobileNavbar>

    <!-- Create Form -->
    <div class="px-4 py-6 space-y-6">
      <!-- Platform Selection -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">{{ $t('publish.selectPlatform') }}</h2>
        <div class="grid grid-cols-3 gap-3">
          <button
            v-for="platform in platforms"
            :key="platform.id"
            class="p-3 rounded-xl border-2 text-center"
            :class="selectedPlatform === platform.id ? 'border-blue-600 bg-blue-50' : 'border-gray-200'"
            @click="selectedPlatform = platform.id"
          >
            <div class="text-xs font-medium text-gray-900">{{ platform.name }}</div>
          </button>
        </div>
      </div>

      <!-- Content Editor -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">{{ $t('publish.content') }}</h2>
        <form @submit.prevent="createTask" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('publish.title') }}</label>
            <input
              v-model="form.title"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              :placeholder="$t('publish.titlePlaceholder')"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('publish.body') }}</label>
            <textarea
              v-model="form.body"
              rows="6"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              :placeholder="$t('publish.bodyPlaceholder')"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('publish.mediaUrls') }}</label>
            <input
              v-model="form.media_urls"
              type="text"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="https://example.com/image.jpg"
            />
          </div>

          <!-- Schedule -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('publish.schedule') }}</label>
            <input
              v-model="form.scheduled_at"
              type="datetime-local"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="!selectedPlatform || pending"
            class="w-full px-6 py-3 bg-blue-600 text-white rounded-full text-sm font-medium disabled:bg-gray-300"
          >
            {{ pending ? $t('publish.creating') : $t('publish.create') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useFetch } from '#app'

const router = useRouter()
const { t } = useI18n()

const platforms = ref([])
const selectedPlatform = ref('')
const pending = ref(false)

const form = ref({
  title: '',
  body: '',
  media_urls: '',
  scheduled_at: '',
  content_id: '00000000-0000-0000-0000-000000000001', // Stub
  tenant_id: '00000000-0000-0000-0000-000000000001', // Stub
  created_by: '00000000-0000-0000-0000-000000000001', // Stub
})

const fetchPlatforms = async () => {
  try {
    const { useApi } = await import('~/composables/useApi')
    const api = useApi()
    const data = await api.get('/platforms')
    platforms.value = data?.items || data || []
  } catch (err) {
    console.error('Failed to fetch platforms:', err)
    // Stub data
    platforms.value = [
      { id: 'facebook', name: 'Facebook' },
      { id: 'instagram', name: 'Instagram' },
      { id: 'twitter', name: 'Twitter' },
      { id: 'linkedin', name: 'LinkedIn' },
    ]
  }
}

const createTask = async () => {
  if (!selectedPlatform.value) return

  pending.value = true
  try {
    const res = await fetch('/api/v1/publish-tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: form.value.tenant_id,
        content_id: form.value.content_id,
        platform_id: selectedPlatform.value,
        content_data: {
          title: form.value.title,
          body: form.value.body,
          media_urls: form.value.media_urls ? [form.value.media_urls] : [],
        },
        scheduled_at: form.value.scheduled_at || null,
        created_by: form.value.created_by,
      }),
    })

    if (res.ok) {
      const task = await res.json()
      router.push(`/publish/${task.id}`)
    } else {
      alert('Failed to create task')
    }
  } catch (err) {
    console.error('Failed to create task:', err)
    alert('Failed to create task')
  } finally {
    pending.value = false
  }
}

onMounted(() => {
  fetchPlatforms()
})
</script>
