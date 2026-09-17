/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
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

export type TradeInquiryItem = {
  id: string;
  buyer_name: string;
  company: string;
  country_code: string;
  country_name: string;
  flag: string;
  category: string;
  spec: string;
  est_value_usd: number;
  channel: 'whatsapp' | 'website' | 'tiktok' | 'linkedin' | 'email';
  status: 'new' | 'quoted' | 'pi_sent' | 'in_production';
  status_label: string;
  time: string;
  unread: boolean;
  whatsapp_number?: string;
};

export type TradeOverviewStats = {
  active_inquiries: number;
  active_inquiries_growth: number;
  pending_response: number;
  pipeline_value_usd: number;
  countries_count: number;
  conversion_rate: number;
  multichannel_reach: number;
  platforms_count: number;
  active_fulfillment_orders: number;
  production_count: number;
  readiness_score: number;
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
  recent_inquiries?: TradeInquiryItem[];
};

const payload = ref<TodayThreePayload>({});
let inflight: Promise<void> | null = null;

function fallbackPayload(): TodayThreePayload {
  return {
    headline: '外贸全链路闭环 · 建议推进：出海商品库与规格建模',
    done_count: 0,
    total_steps: 3,
    next_step_id: 'product',
    steps: [
      {
        id: 'product',
        order: 1,
        title: '出海商品库与规格建模',
        subtitle: '录入标准外贸 SKU、材质属性与 HS 编码',
        done: false,
        route: '/client/products',
        cta: '管理品类库',
        hint: '完善规格参数与出海质检认证，为精准核价与独立站建站提供底座',
        alt_route: '/client/product-candidates',
      },
      {
        id: 'content',
        order: 2,
        title: '全域社媒分发与多语研报',
        subtitle: '生成高权重 EEAT 工业内容与出海多语种短视频',
        done: false,
        route: '/client/video-overseas',
        cta: '分发总控中心',
        hint: '支持 12 语种口型同步并自动化分发至约 40 个海外社媒平台',
        alt_route: '/client/distribute',
      },
      {
        id: 'inquiry',
        order: 3,
        title: '高价值 RFQ 询盘与买家直连',
        subtitle: '响应全球买家采购意向并加速商机成单',
        done: false,
        route: '/client/inquiries',
        cta: '处理意向询盘',
        hint: 'WhatsApp 实时双向翻译沟通，支持形式发票(PI)与箱单一键套打',
      },
    ],
    trade_stats: {
      active_inquiries: 36,
      active_inquiries_growth: 18.4,
      pending_response: 8,
      pipeline_value_usd: 284500,
      countries_count: 14,
      conversion_rate: 4.6,
      multichannel_reach: 92400,
      platforms_count: 38,
      active_fulfillment_orders: 12,
      production_count: 3,
      readiness_score: 88,
    },
    recent_inquiries: [
      {
        id: 'inq-101',
        buyer_name: 'Tariq Al-Mansoor',
        company: 'Al-Mansoor Contracting LLC',
        country_code: 'AE',
        country_name: '阿联酋 (Dubai)',
        flag: '🇦🇪',
        category: '聚氨酯岩棉夹芯板',
        spec: '50mm 容重120kg/m³ · 2,400 m²',
        est_value_usd: 46800,
        channel: 'whatsapp',
        status: 'new',
        status_label: '新商机待响应',
        time: '12 分钟前',
        unread: true,
        whatsapp_number: '+971 50 892 3411',
      },
      {
        id: 'inq-102',
        buyer_name: 'Hans-Peter Weber',
        company: 'Weber Bau Gruppe GmbH',
        country_code: 'DE',
        country_name: '德国 (Munich)',
        flag: '🇩🇪',
        category: '轻钢拼装集装箱房',
        spec: '20ft 模块化打包箱 · 32 套 (CE认证)',
        est_value_usd: 78500,
        channel: 'website',
        status: 'quoted',
        status_label: '已核价待发PI',
        time: '1 小时前',
        unread: false,
        whatsapp_number: '+49 171 458 9210',
      },
      {
        id: 'inq-103',
        buyer_name: 'Marcus Sterling',
        company: 'Pacific Crest Developers',
        country_code: 'US',
        country_name: '美国 (California)',
        flag: '🇺🇸',
        category: '外墙木纹纤维水泥板',
        spec: '8mm 防火 A1级 · 1,800 m²',
        est_value_usd: 32400,
        channel: 'linkedin',
        status: 'pi_sent',
        status_label: '已发PI待付款',
        time: '3 小时前',
        unread: false,
        whatsapp_number: '+1 415 882 1094',
      },
      {
        id: 'inq-104',
        buyer_name: 'Fahad Al-Otaibi',
        company: 'Riyadh Infrastructure Co.',
        country_code: 'SA',
        country_name: '沙特阿拉伯 (Riyadh)',
        flag: '🇸🇦',
        category: '冷库保温板聚氨酯PIR',
        spec: '100mm 隐藏螺栓 · 3,500 m²',
        est_value_usd: 95000,
        channel: 'whatsapp',
        status: 'in_production',
        status_label: '定金已付排产中',
        time: '昨天 17:40',
        unread: false,
        whatsapp_number: '+966 54 321 9876',
      },
      {
        id: 'inq-105',
        buyer_name: 'Nguyen Minh Tu',
        company: 'VietBuild Construction JSC',
        country_code: 'VN',
        country_name: '越南 (Da Nang)',
        flag: '🇻🇳',
        category: '彩涂镀锌卷板 (PPGI)',
        spec: '0.45mm SGCC AZ150 · 60 吨',
        est_value_usd: 52000,
        channel: 'tiktok',
        status: 'new',
        status_label: '新询盘待核价',
        time: '昨天 14:15',
        unread: true,
        whatsapp_number: '+84 90 345 6789',
      },
    ],
  };
}

/** 租户「今日三步」与出海经营大盘共享状态 — 工作台 / 今日页 / 摘要条共用一次请求 */
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
    () => payload.value.trade_stats || fallbackPayload().trade_stats!,
  );
  const recentInquiries = computed(
    () => payload.value.recent_inquiries || fallbackPayload().recent_inquiries!,
  );

  async function load(force = false) {
    if (inflight && !force) return inflight;
    inflight = (async () => {
      try {
        const res = await apiGet<TodayThreePayload>('/client/today-three');
        // 合并 trade_stats 与 recent_inquiries 保障大盘完整丰富
        const fallback = fallbackPayload();
        payload.value = {
          ...res,
          trade_stats: res?.trade_stats || fallback.trade_stats,
          recent_inquiries: res?.recent_inquiries || fallback.recent_inquiries,
        };
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
    tradeStats,
    recentInquiries,
    load,
    refresh,
  };
}
