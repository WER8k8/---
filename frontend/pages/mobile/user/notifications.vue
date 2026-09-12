<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar :title="t('mobile.notifications.title')" safe-area-top :blur="true">
      <template #right>
        <button
          v-if="notifications.length > 0"
          class="text-sm text-blue-600 font-medium"
          @click="markAllRead"
        >
          {{ t('mobile.notifications.markAllRead') }}
        </button>
      </template>
    </MobileNavbar>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center">
        <div class="text-6xl mb-4">😞</div>
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ t('mobile.notifications.loadFailed') }}
        </h2>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <button class="mobile-btn-primary inline-block px-6 py-3 rounded-full" @click="fetchNotifications">
          {{ t('mobile.notifications.retry') }}
        </button>
      </div>
    </div>

    <!-- Notifications List -->
    <div v-else class="pb-20">
      <!-- Empty State -->
      <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center min-h-[60vh] px-4">
        <div class="text-6xl mb-4">🔔</div>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">
          {{ t('mobile.notifications.noNotifications') }}
        </h3>
        <p class="text-sm text-gray-500 text-center">
          {{ t('mobile.notifications.noNotificationsDesc') }}
        </p>
      </div>

      <!-- List -->
      <div v-else class="px-4 py-4 space-y-3">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="bg-white rounded-xl shadow-sm p-4 cursor-pointer active:bg-gray-50 transition-colors"
          :class="{ 'border-l-4 border-blue-600': !notification.is_read }"
          @click="openNotification(notification)"
        >
          <div class="flex items-start gap-3">
            <!-- Icon -->
            <div class="flex-shrink-0 w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
              <span class="text-lg">{{ getNotificationIcon(notification.type) }}</span>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <h3
                  class="text-sm font-semibold text-gray-900 truncate"
                  :class="{ 'text-gray-900 font-semibold': !notification.is_read, 'text-gray-600': notification.is_read }"
                >
                  {{ notification.title }}
                </h3>
                <span class="text-xs text-gray-400 flex-shrink-0">
                  {{ formatTime(notification.created_at) }}
                </span>
              </div>
              <p class="text-sm text-gray-600 mt-1 line-clamp-2">
                {{ notification.message }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useNotificationStore } from '~/stores/notification';

const { t } = useI18n();
const notificationStore = useNotificationStore();

const notifications = computed(() => notificationStore.notifications);
const loading = computed(() => notificationStore.loading);
const error = computed(() => notificationStore.error);

async function fetchNotifications() {
  await notificationStore.fetchNotifications();
}

function markAllRead() {
  notificationStore.markAllRead();
}

function openNotification(notification: any) {
  if (!notification.is_read) {
    notificationStore.markAsRead(notification.id);
  }
  // Navigate to related content if available
  if (notification.link) {
    navigateTo(notification.link);
  }
}

function getNotificationIcon(type: string): string {
  const icons: Record<string, string> = {
    'inquiry': '📝',
    'order': '📦',
    'system': '🔔',
    'promotion': '🎉',
    'default': '📬',
  };
  return icons[type] || icons.default;
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

// Fetch on mount
await fetchNotifications();

useHead({
  title: t('mobile.notifications.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.notifications.seoDesc') },
  ],
});
</script>
