<template>
  <div class="notifications-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          {{ t('notifications.title') }}
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          {{ t('notifications.subtitle') }}
        </p>
      </div>
    </section>

    <!-- Notifications List -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Header with stats and actions -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-6 sm:mb-8">
          <div class="flex items-center gap-4 mb-4 sm:mb-0">
            <h2 class="text-xl sm:text-2xl font-bold text-text-primary">
              {{ t('notifications.myNotifications') }}
            </h2>
            <span
              v-if="stats.unread > 0"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
            >
              {{ stats.unread }} {{ t('notifications.unread') }}
            </span>
          </div>
          <div class="flex items-center gap-3">
            <button
              v-if="stats.unread > 0"
              @click="markAllAsRead"
              class="text-sm text-primary hover:text-primary-dark transition-colors"
            >
              {{ t('notifications.markAllAsRead') }}
            </button>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="flex items-center gap-2 mb-6 sm:mb-8 overflow-x-auto">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key; fetchNotifications()"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200',
              activeFilter === filter.key
                ? 'bg-primary text-white'
                : 'bg-surface text-text-secondary hover:bg-surface-elevated hover:text-text-primary'
            ]"
          >
            {{ filter.label }}
            <span
              v-if="filter.count !== undefined"
              class="ml-2 px-2 py-0.5 rounded-full text-xs"
              :class="activeFilter === filter.key ? 'bg-white/20' : 'bg-gray-200'"
            >
              {{ filter.count }}
            </span>
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="space-y-4">
          <div v-for="i in 5" :key="i" class="animate-pulse bg-surface rounded-2xl p-6">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
              <div class="flex-1">
                <div class="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div class="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div class="h-3 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="notifications.length === 0" class="text-center py-10 sm:py-16">
          <svg class="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">{{ t('notifications.noNotifications') }}</h3>
          <p class="text-sm text-text-secondary">{{ t('notifications.noNotificationsDesc') }}</p>
        </div>

        <!-- Notifications List -->
        <div v-else class="space-y-4">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            :class="[
              'bg-surface rounded-2xl shadow-card p-6 sm:p-8 hover:shadow-card-hover transition-all duration-300',
              !notification.is_read ? 'border-l-4 border-primary' : ''
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-start gap-4 flex-1">
                <!-- Notification Icon -->
                <div
                  :class="[
                    'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                    notification.type === 'success' ? 'bg-green-100 text-green-600' :
                    notification.type === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                    notification.type === 'error' ? 'bg-red-100 text-red-600' :
                    'bg-blue-100 text-blue-600'
                  ]"
                >
                  <svg v-if="notification.type === 'success'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else-if="notification.type === 'warning'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <svg v-else-if="notification.type === 'error'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>

                <!-- Notification Content -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h3
                      :class="[
                        'text-sm sm:text-base font-semibold',
                        !notification.is_read ? 'text-text-primary' : 'text-text-secondary'
                      ]"
                    >
                      {{ notification.title }}
                    </h3>
                    <span
                      v-if="!notification.is_read"
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {{ t('notifications.new') }}
                    </span>
                  </div>
                  <p class="text-sm text-text-secondary mb-2 line-clamp-2">
                    {{ notification.content }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    {{ formatDate(notification.created_at) }}
                  </p>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center gap-2 ml-4">
                <button
                  v-if="!notification.is_read"
                  @click="markAsRead(notification.id)"
                  class="p-2 text-text-secondary hover:text-primary transition-colors"
                  :title="t('notifications.markAsRead')"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  @click="deleteNotification(notification.id)"
                  class="p-2 text-text-secondary hover:text-red-600 transition-colors"
                  :title="t('notifications.delete')"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="notifications.length > 0 && totalPages > 1" class="flex justify-center mt-8 sm:mt-10">
          <nav class="flex items-center gap-2">
            <button
              @click="changePage(currentPage - 1)"
              :disabled="currentPage === 1"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              {{ t('common.previous') }}
            </button>
            <button
              v-for="page in displayedPages"
              :key="page"
              @click="changePage(page)"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === page
                  ? 'bg-primary text-white'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              {{ page }}
            </button>
            <button
              @click="changePage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              {{ t('common.next') }}
            </button>
          </nav>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const notifications = ref([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const stats = ref({ total: 0, unread: 0, read: 0 });
const activeFilter = ref('all');

const filters = computed(() => [
  { key: 'all', label: t('notifications.all'), count: stats.value.total },
  { key: 'unread', label: t('notifications.unread'), count: stats.value.unread },
  { key: 'read', label: t('notifications.read'), count: stats.value.read },
]);

const totalPages = computed(() => Math.ceil(total.value / pageSize.value));

const displayedPages = computed(() => {
  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages.value, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
});

// 获取通知列表
const fetchNotifications = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
    });

    if (activeFilter.value === 'unread') {
      params.append('is_read', 'false');
    } else if (activeFilter.value === 'read') {
      params.append('is_read', 'true');
    }

    const response = await fetch(`/api/v1/notifications/?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      notifications.value = data.data.items || [];
      total.value = data.data.total || 0;
    }
  } catch (err) {
    console.error('Failed to fetch notifications:', err);
  } finally {
    loading.value = false;
  }
};

// 获取通知统计
const fetchStats = async () => {
  try {
    const response = await fetch('/api/v1/notifications/stats/summary', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      stats.value = data.data;
    }
  } catch (err) {
    console.error('Failed to fetch stats:', err);
  }
};

// 标记通知为已读
const markAsRead = async (notificationId: string) => {
  try {
    const response = await fetch(`/api/v1/notifications/${notificationId}/read`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      await fetchNotifications();
      await fetchStats();
    }
  } catch (err) {
    console.error('Failed to mark as read:', err);
  }
};

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    const response = await fetch('/api/v1/notifications/read-all', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      await fetchNotifications();
      await fetchStats();
    }
  } catch (err) {
    console.error('Failed to mark all as read:', err);
  }
};

// 删除通知
const deleteNotification = async (notificationId: string) => {
  if (!confirm(t('notifications.confirmDelete'))) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      await fetchNotifications();
      await fetchStats();
    }
  } catch (err) {
    console.error('Failed to delete notification:', err);
  }
};

// 切换页码
const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchNotifications();
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return t('notifications.justNow');
  if (diffMins < 60) return `${diffMins} ${t('notifications.minutesAgo')}`;
  if (diffHours < 24) return `${diffHours} ${t('notifications.hoursAgo')}`;
  if (diffDays < 7) return `${diffDays} ${t('notifications.daysAgo')}`;

  return date.toLocaleDateString();
};

// SEO元数据
useHead({
  title: computed(() => `${t('notifications.title')} - ${t('common.companyName')}`),
  meta: [
    { name: 'description', content: t('notifications.subtitle') },
  ],
});

onMounted(() => {
  fetchNotifications();
  fetchStats();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}
</style>
