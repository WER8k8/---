/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 今日三步 — 只认后端真数据，失败显示空态，不注入假大盘。
 */
import { computed, ref } from 'vue';
import { apiGet } from '@/utils/api';

export type TodayThreeStep = {
  id: string;
  order: number;
  title: string;
  subtitle: string;
  done: boolean;
  route: string;
  alt_route?: string;
  cta: string;
  hint: string;
};

export type TodayThreeWeekly = {
  received?: number;
  followed?: number;
  pending?: number;
  with_phone?: number;
  all_pending?: number;
  honest_note?: string;
};

export type TodayThreeWin = {
  buyer?: string;
  amount?: number;
  currency?: string;
  note?: string;
};

export type TradeOverviewStats = {
  active_inquiries: number;
  pending_response: number;
  active_fulfillment_orders: number;
  total_orders: number;
  won_count: number;
  won_amount: number;
};

export type TodayThreePayload = {
  steps?: TodayThreeStep[];
  done_count?: number;
  total_steps?: number;
  next_step_id?: string;
  next_route?: string;
  headline?: string;
  region_label?: string;
  product_count?: number;
  weekly_inquiries?: TodayThreeWeekly;
  trade_stats?: TradeOverviewStats;
  recent_inquiries?: Array<Record<string, unknown>>;
  win_loss?: {
    won_count?: number;
    lost_count?: number;
    won_amount?: number;
    plain_summary?: string;
  };
  recent_wins?: TodayThreeWin[];
};

const payload = ref<TodayThreePayload>({});
let inflight: Promise<void> | null = null;

function emptyPayload(): TodayThreePayload {
  return {
    headline: '先做这 3 件事',
    done_count: 0,
    total_steps: 3,
    next_step_id: 'product',
    steps: [
      {
        id: 'product',
        order: 1,
        title: '把产品放上去',
        subtitle: '客户才能看到你在卖什么',
        done: false,
        route: '/client/products',
        cta: '去发品',
        hint: '产品少也可以先发 1 个，不求全。',
      },
      {
        id: 'content',
        order: 2,
        title: '让别人找到你',
        subtitle: '发内容 / 分发到多端',
        done: false,
        route: '/client/distribute',
        cta: '去分发',
        hint: '有内容才有人进站、来询盘。',
      },
      {
        id: 'inquiry',
        order: 3,
        title: '回复客户询盘',
        subtitle: '有人问了就回，回了才可能成单',
        done: false,
        route: '/client/inquiries',
        cta: '去回复',
        hint: '不会写？点进去让系统帮你起一版。',
      },
    ],
    trade_stats: {
      active_inquiries: 0,
      pending_response: 0,
      active_fulfillment_orders: 0,
      total_orders: 0,
      won_count: 0,
      won_amount: 0,
    },
    recent_inquiries: [],
    recent_wins: [],
    win_loss: { won_count: 0, lost_count: 0, won_amount: 0 },
  };
}

/** 租户「今日三步」共享状态 — 工作台 / 今日页 / 摘要条共用一次请求 */
export function useClientTodayThree() {
  const steps = computed(() => payload.value.steps || []);
  const nextStep = computed(
    () =>
      steps.value.find((s) => s.id === payload.value.next_step_id)
      ?? steps.value.find((s) => !s.done)
      ?? null,
  );
  const allDone = computed(
    () => (payload.value.done_count ?? 0) >= (payload.value.total_steps ?? 3),
  );
  const progressPct = computed(() => {
    const total = payload.value.total_steps || 3;
    const done = payload.value.done_count || 0;
    return Math.min(100, Math.round((done / total) * 100));
  });
  const weekly = computed(() => payload.value.weekly_inquiries);
  const tradeStats = computed(
    () => payload.value.trade_stats || emptyPayload().trade_stats!,
  );
  const recentInquiries = computed(
    () => payload.value.recent_inquiries || [],
  );
  const recentWins = computed(() => payload.value.recent_wins || []);
  const winLoss = computed(() => payload.value.win_loss);

  async function load(force = false) {
    if (inflight && !force) return inflight;
    inflight = (async () => {
      try {
        const res = await apiGet<TodayThreePayload>('/client/today-three');
        payload.value = {
          ...emptyPayload(),
          ...res,
          trade_stats: {
            ...emptyPayload().trade_stats!,
            ...(res?.trade_stats || {}),
          },
          recent_inquiries: res?.recent_inquiries || [],
          recent_wins: res?.recent_wins || [],
          win_loss: res?.win_loss || { won_count: 0, lost_count: 0, won_amount: 0 },
        };
      } catch {
        payload.value = emptyPayload();
      }
    })();
    try {
      await inflight;
    } finally {
      inflight = null;
    }
  }

  async function refresh() {
    return load(true);
  }

  return {
    payload,
    steps,
    nextStep,
    allDone,
    progressPct,
    weekly,
    tradeStats,
    recentInquiries,
    recentWins,
    winLoss,
    load,
    refresh,
  };
}
