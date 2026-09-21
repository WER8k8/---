/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar
      safe-area-top
      :blur="true"
    >
      <div class="flex items-center h-14">
        <button
          class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="router.back()"
        >
          <svg
            class="w-5 h-5 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <h1 class="ml-2 text-base font-semibold text-gray-900">
          {{ $t('publish.detailTitle') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Loading -->
    <div
      v-if="pending"
      class="px-4 py-20 text-center"
    >
      <div class="animate-pulse">
        <div class="h-6 bg-gray-200 rounded w-1/3 mx-auto mb-4" />
        <div class="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
      </div>
    </div>

    <!-- Task Detail -->
    <div
      v-else-if="task"
      class="px-4 py-6 space-y-6"
    >
      <!-- Status Card -->
      <div class="bg-white rounded-2xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <span
            class="px-3 py-1 rounded-full text-sm font-medium"
            :class="statusClass(task.status)"
          >
            {{ task.status }}
          </span>
          <button
            v-if="task.status === 'failed'"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
            @click="retryTask"
          >
            {{ $t('publish.retry') }}
          </button>
        </div>

        <h2 class="text-lg font-semibold text-gray-900 mb-2">
          {{ task.content_data?.title || $t('publish.untitled') }}
        </h2>
        <p class="text-sm text-gray-600 mb-4">
          {{ task.content_data?.body || '' }}
        </p>

        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-500">{{ $t('publish.platform') }}</span>
            <span class="text-gray-900 font-medium">{{ task.platform_id }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">{{ $t('publish.createdAt') }}</span>
            <span class="text-gray-900">{{ formatDate(task.created_at) }}</span>
          </div>
          <div
            v-if="task.started_at"
            class="flex justify-between"
          >
            <span class="text-gray-500">{{ $t('publish.startedAt') }}</span>
            <span class="text-gray-900">{{ formatDate(task.started_at) }}</span>
          </div>
          <div
            v-if="task.finished_at"
            class="flex justify-between"
          >
            <span class="text-gray-500">{{ $t('publish.finishedAt') }}</span>
            <span class="text-gray-900">{{ formatDate(task.finished_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Result Card -->
      <div
        v-if="task.platform_post_url || task.error_message"
        class="bg-white rounded-2xl p-5 shadow-sm"
      >
        <h3 class="text-sm font-semibold text-gray-900 mb-3">
          {{ $t('publish.result') }}
        </h3>

        <div
          v-if="task.platform_post_url"
          class="mb-3"
        >
          <a
            :href="task.platform_post_url"
            target="_blank"
            class="text-blue-600 hover:underline text-sm"
          >
            {{ $t('publish.viewPost') }} →
          </a>
        </div>

        <div
          v-if="task.error_message"
          class="text-red-600 text-sm bg-red-50 p-3 rounded-lg"
        >
          {{ task.error_message }}
        </div>
      </div>

      <!-- Execute Button -->
      <button
        v-if="task.status === 'pending'"
        class="w-full px-6 py-3 bg-blue-600 text-white rounded-full text-sm font-medium"
        @click="executeTask"
      >
        {{ $t('publish.execute') }}
      </button>
    </div>

    <!-- Error -->
    <div
      v-else
      class="px-4 py-20 text-center text-red-500"
    >
      {{ $t('publish.taskNotFound') }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const task = ref(null)
const pending = ref(true)

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
  return new Date(dateStr).toLocaleString()
}

const fetchTask = async () => {
  pending.value = true
  try {
    const res = await fetch(`/api/v1/publish-tasks/${route.params.id}`)
    if (res.ok) {
      task.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch task:', err)
  } finally {
    pending.value = false
  }
}

const executeTask = async () => {
  try {
    const res = await fetch(`/api/v1/publish-tasks/${route.params.id}/execute`, {
      method: 'POST',
    })
    if (res.ok) {
      alert(t('publish.executed'))
      fetchTask()
    }
  } catch (err) {
    console.error('Failed to execute task:', err)
    alert('Failed to execute task')
  }
}

const retryTask = async () => {
  try {
    const res = await fetch(`/api/v1/publish-tasks/${route.params.id}/retry`, {
      method: 'POST',
    })
    if (res.ok) {
      alert(t('publish.retried'))
      fetchTask()
    }
  } catch (err) {
    console.error('Failed to retry task:', err)
    alert('Failed to retry task')
  }
}

fetchTask()
</script>
