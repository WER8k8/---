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
};

const payload = ref<TodayThreePayload>({});
let inflight: Promise<void> | null = null;

function fallbackPayload(): TodayThreePayload {
  return {
    headline: '今天先做：填好产品',
    done_count: 0,
    total_steps: 3,
    next_step_id: 'product',
    steps: [
      {
        id: 'product',
        order: 1,
        title: '填好产品',
        subtitle: '写清品名、规格、产地',
        done: false,
        route: '/client/products',
        cta: '去产品库',
        hint: '至少 1 个真实产品，开发信和发布才能引用',
        alt_route: '/client/product-candidates',
      },
      {
        id: 'content',
        order: 2,
        title: '发一批内容',
        subtitle: '让人看见你的厂',
        done: false,
        route: '/client/video-overseas',
        cta: '中文片出海',
        hint: '绑平台后发一条，进度看得见',
        alt_route: '/client/distribute',
      },
      {
        id: 'inquiry',
        order: 3,
        title: '看询盘回电话',
        subtitle: '有人问了要回',
        done: false,
        route: '/client/inquiries',
        cta: '去询盘列表',
        hint: '0 条也正常，不是假数据',
      },
    ],
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

  async function load(force = false) {
    if (inflight && !force) return inflight;
    inflight = (async () => {
      try {
        payload.value = await apiGet<TodayThreePayload>('/client/today-three');
      } catch {
        payload.value = fallbackPayload();
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
    load,
    refresh,
  };
}
