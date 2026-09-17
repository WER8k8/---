/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, computed } from 'vue';
import { getAuthToken } from '@/utils/api';

export type ClientPlanSnapshot = {
  loaded: boolean;
  planName: string;
  planExpiry: string;
  aiUsed: number;
  aiMax: number;
  pendingInquiries: number;
  publishInProgress: number;
};

const snapshot = ref<ClientPlanSnapshot>({
  loaded: false,
  planName: '体验版',
  planExpiry: '',
  aiUsed: 0,
  aiMax: 1000,
  pendingInquiries: 0,
  publishInProgress: 0,
});

let loadPromise: Promise<void> | null = null;

function planTagColor(name: string): string {
  if (/企业|enterprise/i.test(name)) return 'purple';
  if (/专业|pro/i.test(name)) return 'blue';
  if (/启航|starter/i.test(name)) return 'blue';
  return 'default';
}

function formatExpiry(raw: string | null | undefined): string {
  if (!raw) return '';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return '';
  const days = Math.ceil((d.getTime() - Date.now()) / 86400000);
  if (days < 0) return '已到期';
  if (days === 0) return '今日到期';
  return `剩 ${days} 天`;
}

export function useClientPlanSnapshot() {
  const aiPct = computed(() => {
    const max = snapshot.value.aiMax || 1;
    return Math.min(100, Math.round((snapshot.value.aiUsed / max) * 100));
  });

  const showUpgrade = computed(() => aiPct.value >= 80);

  async function refresh(force = false) {
    if (!force && snapshot.value.loaded) return;
    const tk = getAuthToken();
    if (!tk) return;

    if (!loadPromise || force) {
      loadPromise = (async () => {
        try {
          const res = await fetch('/api/v1/client/dashboard', {
            headers: { Authorization: `Bearer ${tk}` },
          });
          const body = await res.json();
          const data = body.data || body;
          snapshot.value = {
            loaded: true,
            planName: data.plan_name || '体验版',
            planExpiry: formatExpiry(data.plan_expiry),
            aiUsed: data.ai_quota_used || 0,
            aiMax: data.ai_quota_total || 1000,
            pendingInquiries: data.stats?.pending_inquiries ?? 0,
            publishInProgress: Number(data.publish_in_progress ?? 0),
          };
        } catch {
          snapshot.value = { ...snapshot.value, loaded: true };
        }
      })();
    }
    await loadPromise;
  }

  return {
    snapshot,
    aiPct,
    showUpgrade,
    planTagColor,
    refresh,
  };
}
