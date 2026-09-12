import { useApi } from "~/composables/useApi";

export interface Notification {
  id: number;
  title: string;
  content: string;
  type?: string;
  read: boolean;
  createdAt: string;
}

export const useNotificationStore = defineStore("notification", () => {
  const api = useApi();

  const notifications = ref<Notification[]>([]);
  const unreadCount = computed(() =>
    notifications.value.filter((n) => !n.read).length
  );
  const loading = ref(false);

  async function fetchNotifications(params: Record<string, unknown> = {}) {
    loading.value = true;
    try {
      const response = await api.get<{ items: Notification[] }>(
        "/notifications",
        params
      );
      notifications.value = response.items || [];
      return response;
    } finally {
      loading.value = false;
    }
  }

  async function markAsRead(notificationId: number) {
    await api.post(`/notifications/${notificationId}/read`);
    const notification = notifications.value.find((n) => n.id === notificationId);
    if (notification) {
      notification.read = true;
    }
  }

  async function markAllAsRead() {
    await api.post("/notifications/read-all");
    notifications.value.forEach((n) => {
      n.read = true;
    });
  }

  return {
    notifications,
    unreadCount,
    loading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  };
});
