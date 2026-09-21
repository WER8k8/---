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
      <template #default>
        <div class="flex items-center justify-between h-14">
          <h1 class="text-base font-semibold text-gray-900">
            {{ t('mobile.alerts.title') }}
          </h1>
          <button
            class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            @click="showCreateAlert = true"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
          </button>
        </div>
      </template>
    </MobileNavbar>

    <!-- Stats Bar -->
    <div class="px-4 py-3 bg-white border-b border-gray-100 flex items-center gap-4 overflow-x-auto">
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <div class="w-2 h-2 rounded-full bg-red-500" />
        <span class="text-sm font-medium text-gray-900">{{ stats.active || 0 }}</span>
        <span class="text-xs text-gray-500">{{ t('mobile.alerts.active') }}</span>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <div class="w-2 h-2 rounded-full bg-blue-500" />
        <span class="text-sm font-medium text-gray-900">{{ stats.total || 0 }}</span>
        <span class="text-xs text-gray-500">{{ t('mobile.alerts.total') }}</span>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <div class="w-2 h-2 rounded-full bg-green-500" />
        <span class="text-sm font-medium text-gray-900">{{ stats.resolved_today || 0 }}</span>
        <span class="text-xs text-gray-500">{{ t('mobile.alerts.resolved') }}</span>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="px-4 py-2 bg-white flex gap-2 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key; fetchAlerts()"
        :class="[
          'px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap',
          activeTab === tab.key ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="px-4 py-4 space-y-3"
    >
      <div
        v-for="i in 5"
        :key="i"
        class="bg-white rounded-2xl p-4 animate-pulse"
      >
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 bg-gray-200 rounded-full" />
          <div class="flex-1">
            <div class="h-4 bg-gray-200 rounded w-1/3 mb-2" />
            <div class="h-3 bg-gray-200 rounded w-3/4" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="px-4 py-20 text-center"
    >
      <div class="text-6xl mb-4">
        😞
      </div>
      <h3 class="text-base font-medium text-gray-900 mb-2">
        {{ t('mobile.alerts.loadFailed') }}
      </h3>
      <p class="text-sm text-gray-500 mb-6">
        {{ error }}
      </p>
      <button
        class="mobile-btn-primary px-6 py-3 rounded-full"
        @click="fetchAlerts"
      >
        {{ t('mobile.alerts.retry') }}
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="alerts.length === 0"
      class="px-4 py-20 text-center"
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
          stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">
        {{ t('mobile.alerts.noAlerts') }}
      </h3>
      <p class="text-sm text-gray-500 mb-6">
        {{ t('mobile.alerts.noAlertsDesc') }}
      </p>
    </div>

    <!-- Alerts List -->
    <div
      v-else
      class="px-4 py-2 space-y-2 pb-20"
    >
      <div
        v-for="alert in alerts"
        :key="alert.id"
        :class="[
          'bg-white rounded-2xl p-4 border-l-4 cursor-pointer active:bg-gray-50 transition-colors',
          alert.severity === 'critical' ? 'border-red-500' :
          alert.severity === 'error' ? 'border-red-400' :
          alert.severity === 'warning' ? 'border-yellow-500' :
          'border-blue-500'
        ]"
        @click="router.push(`/mobile/alerts/${alert.id}`)"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="text-sm font-semibold text-gray-900 flex-1 truncate">
            {{ alert.title }}
          </h3>
          <span
            :class="[
              'ml-2 px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0',
              alert.status === 'active' ? 'bg-red-100 text-red-800' :
              alert.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            ]"
          >
            {{ getStatusLabel(alert.status) }}
          </span>
        </div>
        <p class="text-xs text-gray-500 mb-2 line-clamp-2">
          {{ alert.description }}
        </p>
        <div class="flex items-center justify-between text-xs text-gray-400">
          <span>{{ getTypeLabel(alert.alert_type) }}</span>
          <span>{{ formatTime(alert.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Create Alert Modal -->
    <div
      v-if="showCreateAlert"
      class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-end justify-center"
    >
      <div class="bg-white w-full max-h-[90vh] rounded-t-2xl overflow-y-auto">
        <div class="p-5">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold text-gray-900">
              {{ t('mobile.alerts.createAlert') }}
            </h2>
            <button
              @click="showCreateAlert = false"
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
            @submit.prevent="createAlert"
            class="space-y-4"
          >
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.alertType') }}</label>
              <select
                v-model="newAlert.alert_type"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white"
              >
                <option value="system">
                  System
                </option>
                <option value="performance">
                  Performance
                </option>
                <option value="availability">
                  Availability
                </option>
                <option value="data_quality">
                  Data Quality
                </option>
                <option value="security">
                  Security
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.severity') }}</label>
              <select
                v-model="newAlert.severity"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white"
              >
                <option value="info">
                  Info
                </option>
                <option value="warning">
                  Warning
                </option>
                <option value="error">
                  Error
                </option>
                <option value="critical">
                  Critical
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.titleLabel') }}</label>
              <input
                v-model="newAlert.title"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :placeholder="t('mobile.alerts.titlePlaceholder')"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.alerts.descriptionLabel') }}</label>
              <textarea
                v-model="newAlert.description"
                required
                rows="3"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                :placeholder="t('mobile.alerts.descriptionPlaceholder')"
              />
            </div>
            <div class="flex gap-3 pt-4">
              <button
                type="submit"
                :disabled="creating"
                class="flex-1 mobile-btn-primary py-3.5 rounded-xl font-semibold text-base"
              >
                {{ creating ? t('mobile.common.saving') : t('mobile.common.create') }}
              </button>
              <button
                type="button"
                @click="showCreateAlert = false"
                class="flex-1 mobile-btn-outline py-3.5 rounded-xl font-semibold text-base"
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
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const router = useRouter();
const { t } = useI18n();

const alerts = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const stats = ref({ active: 0, total: 0, resolved_today: 0 });
const activeTab = ref('active');
const showCreateAlert = ref(false);
const creating = ref(false);

const tabs = [
  { key: 'active', label: t('mobile.alerts.tabActive') },
  { key: 'all', label: t('mobile.alerts.tabAll') },
  { key: 'resolved', label: t('mobile.alerts.tabResolved') },
];

const newAlert = ref({
  alert_type: 'system',
  severity: 'warning',
  title: '',
  description: '',
});

// Fetch alerts
const fetchAlerts = async () => {
  loading.value = true;
  error.value = null;
  try {
    const params = new URLSearchParams();
    if (activeTab.value === 'active') params.append('status', 'active');
    if (activeTab.value === 'resolved') params.append('status', 'resolved');
    
    const response = await fetch(`/api/v1/alerts?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      alerts.value = data.data?.items || data.items || data || [];
    } else {
      throw new Error(`Failed to fetch: ${response.status}`);
    }
    // Also fetch stats
    const statsRes = await fetch('/api/v1/alerts/statistics', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (statsRes.ok) {
      stats.value = await statsRes.json();
    }
  } catch (err: any) {
    error.value = err.message || t('mobile.alerts.loadFailed');
    console.error('Failed to fetch alerts:', err);
  } finally {
    loading.value = false;
  }
};

// Create alert
const createAlert = async () => {
  creating.value = true;
  try {
    const response = await fetch('/api/v1/alerts', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newAlert.value),
    });
    if (response.ok) {
      showCreateAlert.value = false;
      newAlert.value = { alert_type: 'system', severity: 'warning', title: '', description: '' };
      await fetchAlerts();
    } else {
      throw new Error(`Failed to create: ${response.status}`);
    }
  } catch (err: any) {
    alert(err.message || t('mobile.alerts.createFailed'));
    console.error('Failed to create alert:', err);
  } finally {
    creating.value = false;
  }
};

// Get status label
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: t('mobile.alerts.statusActive'),
    acknowledged: t('mobile.alerts.statusAcknowledged'),
    resolved: t('mobile.alerts.statusResolved'),
    dismissed: t('mobile.alerts.statusDismissed'),
  };
  return labels[status] || status;
};

// Get type label
const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    system: 'System',
    performance: 'Performance',
    availability: 'Availability',
    data_quality: 'Data Quality',
    security: 'Security',
  };
  return labels[type] || type;
};

// Format time
const formatTime = (dateStr: string): string => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (mins < 1) return t('mobile.alerts.justNow');
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return `${date.getMonth() + 1}/${date.getDate()}`;
};

// Page meta
useHead({
  title: t('mobile.alerts.title'),
});

onMounted(() => {
  fetchAlerts();
});
</script>
