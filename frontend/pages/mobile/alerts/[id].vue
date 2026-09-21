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
        <h1 class="ml-2 text-base font-semibold text-gray-900 truncate">
          {{ t('mobile.alerts.detail') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="px-4 py-6 space-y-4"
    >
      <div class="bg-white rounded-2xl p-4 animate-pulse">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 bg-gray-200 rounded-full" />
          <div class="flex-1">
            <div class="h-5 bg-gray-200 rounded w-1/2 mb-2" />
            <div class="h-4 bg-gray-200 rounded w-3/4" />
          </div>
        </div>
        <div class="space-y-2">
          <div class="h-4 bg-gray-200 rounded w-full" />
          <div class="h-4 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="px-4 py-20 text-center"
    >
      <div class="text-red-500 text-base font-medium mb-2">
        {{ t('mobile.alerts.fetchError') }}
      </div>
      <p class="text-sm text-gray-500 mb-4">
        {{ error }}
      </p>
      <button
        class="mobile-btn-primary px-6 py-3 rounded-full"
        @click="fetchAlert"
      >
        {{ t('mobile.common.retry') }}
      </button>
    </div>

    <!-- Not Found State -->
    <div
      v-else-if="!alert"
      class="px-4 py-20 text-center"
    >
      <div class="text-gray-500 text-base font-medium mb-4">
        {{ t('mobile.alerts.notFound') }}
      </div>
      <button
        class="mobile-btn-primary px-6 py-3 rounded-full"
        @click="router.back()"
      >
        {{ t('mobile.common.goBack') }}
      </button>
    </div>

    <!-- Alert Detail -->
    <div
      v-else
      class="pb-24"
    >
      <!-- Alert Header Card -->
      <div class="px-4 pt-4">
        <div class="bg-white rounded-2xl p-4 relative">
          <!-- Severity Icon -->
          <div
            :class="[
              'w-12 h-12 rounded-full flex items-center justify-center mb-3',
              alert.severity === 'critical' ? 'bg-red-100 text-red-600' :
              alert.severity === 'error' ? 'bg-red-100 text-red-600' :
              alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-600' :
              'bg-blue-100 text-blue-600'
            ]"
          >
            <svg
              v-if="alert.severity === 'critical' || alert.severity === 'error'"
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2m7-2a9 9 0 11-18 0 9 9 0 01 18 0z"
              />
            </svg>
            <svg
              v-else
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m-1-4h.01M21 12a9 9 0 11-18 0 9 9 0 01 18 0z"
              />
            </svg>
          </div>

          <h2 class="text-lg font-bold text-gray-900 mb-2">
            {{ alert.title }}
          </h2>

          <!-- Status & Severity Badges -->
          <div class="flex flex-wrap gap-2 mb-3">
            <span
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-medium',
                alert.status === 'active' ? 'bg-red-100 text-red-800' :
                alert.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              ]"
            >
              {{ getStatusText(alert.status) }}
            </span>
            <span
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-medium',
                alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                alert.severity === 'error' ? 'bg-red-100 text-red-800' :
                alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              ]"
            >
              {{ getSeverityText(alert.severity) }}
            </span>
            <span class="px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-medium">
              {{ getTypeText(alert.alert_type) }}
            </span>
          </div>

          <p class="text-xs text-gray-500">
            {{ formatTime(alert.created_at) }}
          </p>

          <!-- Action Buttons -->
          <div
            v-if="alert.status !== 'resolved'"
            class="flex gap-2 mt-4"
          >
            <button
              v-if="alert.status !== 'acknowledged'"
              @click="showAckModal = true"
              class="flex-1 py-2.5 rounded-xl border-2 border-blue-300 text-blue-600 text-sm font-medium"
            >
              {{ t('mobile.alerts.acknowledge') }}
            </button>
            <button
              @click="showResolveModal = true"
              class="flex-1 mobile-btn-primary py-2.5 rounded-xl text-sm font-medium"
            >
              {{ t('mobile.alerts.resolve') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div class="px-4 pt-3">
        <div class="bg-white rounded-2xl p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-2">
            {{ t('mobile.alerts.description') }}
          </h3>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">
            {{ alert.description }}
          </p>
        </div>
      </div>

      <!-- Impact Scope -->
      <div
        v-if="alert.impact_scope"
        class="px-4 pt-3"
      >
        <div class="bg-white rounded-2xl p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-2">
            {{ t('mobile.alerts.impactScope') }}
          </h3>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">
            {{ alert.impact_scope }}
          </p>
        </div>
      </div>

      <!-- Proposed Solution -->
      <div
        v-if="alert.proposed_solution"
        class="px-4 pt-3"
      >
        <div class="bg-white rounded-2xl p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-2">
            {{ t('mobile.alerts.proposedSolution') }}
          </h3>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">
            {{ alert.proposed_solution }}
          </p>
        </div>
      </div>

      <!-- History -->
      <div
        v-if="histories.length > 0"
        class="px-4 pt-3"
      >
        <div class="bg-white rounded-2xl p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-3">
            {{ t('mobile.alerts.history') }}
          </h3>
          <div class="space-y-3">
            <div
              v-for="h in histories"
              :key="h.id"
              class="flex gap-3"
            >
              <div class="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg
                  class="w-3.5 h-3.5"
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
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">
                  {{ getActionText(h.action_type) }}
                </p>
                <p
                  v-if="h.action_notes"
                  class="text-xs text-gray-500 mt-0.5"
                >
                  {{ h.action_notes }}
                </p>
                <p class="text-xs text-gray-400 mt-0.5">
                  {{ formatTime(h.created_at) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Acknowledge Modal -->
    <div
      v-if="showAckModal"
      class="fixed inset-0 z-50 bg-black/50 flex items-end justify-center"
    >
      <div class="bg-white w-full max-h-[80vh] rounded-t-2xl overflow-y-auto">
        <div class="p-5">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold text-gray-900">
              {{ t('mobile.alerts.acknowledge') }}
            </h2>
            <button
              @click="showAckModal = false"
              class="p-1"
            >
              <svg
                class="w-6 h-6 text-gray-400"
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
          <form
            @submit.prevent="acknowledge"
            class="space-y-4"
          >
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.acknowledgedBy') }}</label>
              <input
                v-model="ackForm.acknowledged_by"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                :placeholder="t('mobile.alerts.acknowledgedByPlaceholder')"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.notes') }}</label>
              <textarea
                v-model="ackForm.notes"
                rows="3"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 resize-none"
                :placeholder="t('mobile.alerts.notesPlaceholder')"
              />
            </div>
            <div class="flex gap-3 pt-4">
              <button
                type="submit"
                :disabled="acking"
                class="flex-1 mobile-btn-primary py-3 rounded-xl font-semibold"
              >
                {{ acking ? t('mobile.common.saving') : t('mobile.alerts.confirm') }}
              </button>
              <button
                type="button"
                @click="showAckModal = false"
                class="flex-1 mobile-btn-outline py-3 rounded-xl font-semibold"
              >
                {{ t('mobile.common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Resolve Modal -->
    <div
      v-if="showResolveModal"
      class="fixed inset-0 z-50 bg-black/50 flex items-end justify-center"
    >
      <div class="bg-white w-full max-h-[80vh] rounded-t-2xl overflow-y-auto">
        <div class="p-5">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold text-gray-900">
              {{ t('mobile.alerts.resolve') }}
            </h2>
            <button
              @click="showResolveModal = false"
              class="p-1"
            >
              <svg
                class="w-6 h-6 text-gray-400"
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
          <form
            @submit.prevent="resolve"
            class="space-y-4"
          >
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.resolvedBy') }}</label>
              <input
                v-model="resolveForm.resolved_by"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                :placeholder="t('mobile.alerts.resolvedByPlaceholder')"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.resolutionNotes') }}</label>
              <textarea
                v-model="resolveForm.resolution_notes"
                rows="4"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 resize-none"
                :placeholder="t('mobile.alerts.resolutionNotesPlaceholder')"
              />
            </div>
            <div class="flex gap-3 pt-4">
              <button
                type="submit"
                :disabled="resolving"
                class="flex-1 mobile-btn-primary py-3 rounded-xl font-semibold"
              >
                {{ resolving ? t('mobile.common.saving') : t('mobile.alerts.confirm') }}
              </button>
              <button
                type="button"
                @click="showResolveModal = false"
                class="flex-1 mobile-btn-outline py-3 rounded-xl font-semibold"
              >
                {{ t('mobile.common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const alert = ref<any>(null)
const histories = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const showAckModal = ref(false)
const showResolveModal = ref(false)
const acking = ref(false)
const resolving = ref(false)

const ackForm = ref({ acknowledged_by: '', notes: '' })
const resolveForm = ref({ resolved_by: '', resolution_notes: '' })

// Fetch alert
const fetchAlert = async () => {
  loading.value = true
  error.value = null
  try {
    const id = route.params.id as string
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = token ? { 'Authorization': `Bearer ${token}` } : {}

    const [alertRes, histRes] = await Promise.all([
      fetch(`/api/v1/alerts/${id}`, { headers }),
      fetch(`/api/v1/alerts/${id}/histories`, { headers })
    ])

    if (alertRes.ok) {
      const alertData = await alertRes.json()
      alert.value = alertData.data || alertData
    } else {
      throw new Error(`Failed to fetch alert: ${alertRes.status}`)
    }

    if (histRes.ok) {
      const histData = await histRes.json()
      histories.value = histData.data || histData || []
    }
  } catch (err: any) {
    console.error('Failed to fetch alert:', err)
    error.value = err.message || t('mobile.alerts.fetchError')
    alert.value = null
  } finally {
    loading.value = false
  }
}

// Acknowledge
const acknowledge = async () => {
  acking.value = true
  try {
    const id = route.params.id as string
    const token = localStorage.getItem('token')

    const response = await fetch(`/api/v1/alerts/${id}/acknowledge`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ackForm.value),
    })

    if (response.ok) {
      showAckModal.value = false
      ackForm.value = { acknowledged_by: '', notes: '' }
      await fetchAlert()
    } else {
      throw new Error(`Failed to acknowledge: ${response.status}`)
    }
  } catch (err: any) {
    console.error('Failed to acknowledge:', err)
    alert(err.message || t('mobile.alerts.acknowledgeError'))
  } finally {
    acking.value = false
  }
}

// Resolve
const resolve = async () => {
  resolving.value = true
  try {
    const id = route.params.id as string
    const token = localStorage.getItem('token')

    const response = await fetch(`/api/v1/alerts/${id}/resolve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(resolveForm.value),
    })

    if (response.ok) {
      showResolveModal.value = false
      resolveForm.value = { resolved_by: '', resolution_notes: '' }
      await fetchAlert()
    } else {
      throw new Error(`Failed to resolve: ${response.status}`)
    }
  } catch (err: any) {
    console.error('Failed to resolve:', err)
    alert(err.message || t('mobile.alerts.resolveError'))
  } finally {
    resolving.value = false
  }
}

// Helpers
const getStatusText = (status: string): string => {
  const m: Record<string, string> = {
    active: t('mobile.alerts.statusActive'),
    acknowledged: t('mobile.alerts.statusAcknowledged'),
    resolved: t('mobile.alerts.statusResolved'),
    dismissed: t('mobile.alerts.statusDismissed'),
  }
  return m[status] || status
}

const getSeverityText = (severity: string): string => {
  const m: Record<string, string> = {
    info: t('mobile.alerts.severityInfo'),
    warning: t('mobile.alerts.severityWarning'),
    error: t('mobile.alerts.severityError'),
    critical: t('mobile.alerts.severityCritical'),
  }
  return m[severity] || severity
}

const getTypeText = (type: string): string => {
  const m: Record<string, string> = {
    system: t('mobile.alerts.typeSystem'),
    performance: t('mobile.alerts.typePerformance'),
    availability: t('mobile.alerts.typeAvailability'),
    data_quality: t('mobile.alerts.typeDataQuality'),
    security: t('mobile.alerts.typeSecurity'),
  }
  return m[type] || type
}

const getActionText = (action: string): string => {
  const m: Record<string, string> = {
    created: t('mobile.alerts.actionCreated'),
    acknowledged: t('mobile.alerts.actionAcknowledged'),
    resolved: t('mobile.alerts.actionResolved'),
  }
  return m[action] || action
}

const formatTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return t('mobile.alerts.justNow')
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${d.getMonth()+1}/${d.getDate()}`
}

// Page meta
useHead({
  title: computed(() => alert.value?.title || t('mobile.alerts.detail')),
})

onMounted(() => {
  fetchAlert()
})
</script>
