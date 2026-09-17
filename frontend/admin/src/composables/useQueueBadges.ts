/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { onMounted, onUnmounted, reactive } from 'vue';

import { apiGet } from '@/utils/api';
import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

export interface QueueBadgeState {
  inquiries: number;
  publish: number;
  fulfillment: number;
  loading: boolean;
}

export function useQueueBadges(pollMs = 60000) {
  const badges = reactive<QueueBadgeState>({
    inquiries: 0,
    publish: 0,
    fulfillment: 0,
    loading: false,
  });

  let timer: ReturnType<typeof setInterval> | null = null;

  async function loadInquiryCount() {
    try {
      const raw = await apiGet('/inquiries/unified', { page: 1, page_size: 1, status: 'pending' });
      const { total } = adaptPaginatedResponse(raw);
      badges.inquiries = total;
    } catch {
      badges.inquiries = 0;
    }
  }

  async function loadPublishCount() {
    try {
      const raw = await apiGet('/publish-tasks', { page: 1, page_size: 1, status: 'pending' });
      const { total } = adaptPaginatedResponse(raw);
      badges.publish = total;
    } catch {
      badges.publish = 0;
    }
  }

  async function loadFulfillmentCount() {
    try {
      const raw = await apiGet('/orders', { page: 1, page_size: 1, status: 'pending', role: 'merchant' });
      const { total } = adaptPaginatedResponse(raw);
      badges.fulfillment = total;
    } catch {
      badges.fulfillment = 0;
    }
  }

  async function refresh() {
    badges.loading = true;
    try {
      await Promise.all([loadInquiryCount(), loadPublishCount(), loadFulfillmentCount()]);
    } finally {
      badges.loading = false;
    }
  }

  onMounted(() => {
    void refresh();
    timer = setInterval(() => void refresh(), pollMs);
  });

  onUnmounted(() => {
    if (timer) clearInterval(timer);
  });

  return { badges, refresh };
}
