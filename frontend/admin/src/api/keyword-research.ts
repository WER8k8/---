/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { apiGet, apiPost } from '@/utils/api';

export interface TrendPoint {
  month: string;
  volume: number;
  heat_index: number;
}

export interface RegionalDemand {
  region: string;
  code: string;
  share: number;
  growth: string;
}

export interface LongTailKeyword {
  keyword: string;
  intent: string;
  word_class: string;
  search_volume: number;
  competition: number;
  heat_index: number;
  cpc: string;
}

export interface AiInsights {
  buyer_intent: string;
  seo_recommendation: string;
  geo_recommendation: string;
  social_recommendation: string;
}

export interface MultilingualMatrixItem {
  country_code: string;
  country_name: string;
  flag: string;
  language_code: string;
  language_name: string;
  keyword: string;
  longtail: string;
  search_volume: number;
  kd: number;
  cpc: string;
  deployment_status: string;
}

export interface TransmutationData {
  is_transmuted: boolean;
  original_input: string;
  detected_language: string;
  target_country: string;
  target_country_name: string;
  target_language: string;
  target_language_name: string;
  transmuted_keyword: string;
  transmuted_longtail: string;
  transmutation_reason: string;
  multilingual_matrix: MultilingualMatrixItem[];
}

export interface ZeroVolumeGuardResult {
  keyword: string;
  is_zero_volume: boolean;
  is_prohibited: boolean;
  risk_level: 'critical' | 'safe';
  guard_status: 'BLOCKED' | 'PASS' | 'TRANSMUTED_PASS';
  title: string;
  message: string;
  reasons: string[];
  suggested_alternatives: Array<{
    keyword: string;
    search_volume: number;
    kd: number;
    cpc: string;
    intent: string;
    growth: string;
  }>;
  recommended_core_keyword: string;
  transmutation?: TransmutationData;
}

export interface KeywordResearchResult {
  keyword: string;
  search_term?: string;
  market: string;
  target_country?: string;
  target_country_name?: string;
  target_language?: string;
  target_language_name?: string;
  currency_symbol?: string;
  data_source: string;
  data_source_label: string;
  zero_volume_guard: ZeroVolumeGuardResult;
  transmutation?: TransmutationData;
  multilingual_matrix?: MultilingualMatrixItem[];
  heat_index: number;
  search_volume: number;
  competition_index: number;
  difficulty_level: 'low' | 'medium' | 'high';
  difficulty_label: string;
  cpc: string;
  cpc_value: number;
  cpc_currency: string;
  trends: TrendPoint[];
  regional_demand: RegionalDemand[];
  long_tail_keywords: LongTailKeyword[];
  ai_insights: AiInsights;
  analyzed_at: string;
}

export interface LeaderboardItem {
  rank: number;
  keyword: string;
  category: string;
  search_volume: number;
  kd: number;
  cpc: string;
  growth: string;
  intent: string;
}

export interface GoogleLeaderboardResponse {
  active_category: string;
  categories: Array<{ key: string; label: string }>;
  leaderboard: LeaderboardItem[];
  total: number;
  updated_at: string;
  source: string;
}

export interface PopularPresetCategory {
  category: string;
  keywords: string[];
}

export interface PopularPresetsResponse {
  market: string;
  categories: PopularPresetCategory[];
}

export interface TargetLocaleItem {
  code: string;
  country_name: string;
  language_code: string;
  language_name: string;
  currency: string;
  currency_code: string;
  flag: string;
}

/** 查询关键词热度与市场分析（含 SEMrush / Google 数据网关、多国母语自动置换与零搜索量熔断） */
export async function analyzeKeywordHeat(params: {
  keyword: string;
  market?: string;
  target_country?: string;
  target_language?: string;
  category?: string;
}): Promise<KeywordResearchResult> {
  const res = await apiPost<any>('/keyword-research/analyze', params);
  return (res?.data || res) as KeywordResearchResult;
}

/** 零搜索量硬性拦截门禁检测（中文自动置换为目标国采购母语词） */
export async function checkZeroVolumeGuard(
  keyword: string,
  target_country: string = 'US'
): Promise<ZeroVolumeGuardResult> {
  const res = await apiPost<any>('/keyword-research/check-zero-volume', { keyword, target_country });
  return (res?.data || res) as ZeroVolumeGuardResult;
}

/** 主动调用多国母语关键词置换引擎 */
export async function transmuteMultilingualKeywords(params: {
  keyword: string;
  target_country?: string;
  target_language?: string;
}): Promise<TransmutationData> {
  const res = await apiPost<any>('/keyword-research/transmute-multilingual', params);
  return (res?.data || res) as TransmutationData;
}

/** 获取支持的海外目标出口国与母语配置列表 */
export async function getTargetLocales(): Promise<TargetLocaleItem[]> {
  const res = await apiGet<any>('/keyword-research/target-locales');
  return (res?.data || res) as TargetLocaleItem[];
}

/** 获取 Google 全球外贸关键词热门排行榜 */
export async function getGoogleLeaderboard(category: string = 'all'): Promise<GoogleLeaderboardResponse> {
  const res = await apiGet<any>(`/keyword-research/google-leaderboard?category=${encodeURIComponent(category)}`);
  return (res?.data || res) as GoogleLeaderboardResponse;
}

/** 一键保存选中的关键词到租户专属词库 */
export async function saveKeywordsToLibrary(
  keywords: Array<{ keyword: string; intent?: string; word_class?: string; search_volume?: number; competition?: number; country_code?: string; language_code?: string }>
): Promise<{ saved_count: number; duplicate_count: number; total: number }> {
  const res = await apiPost<any>('/keyword-research/save-to-library', { keywords });
  return (res?.data || res) as { saved_count: number; duplicate_count: number; total: number };
}

/** 获取行业预设热词推荐 */
export async function getPopularPresets(market: string = 'global'): Promise<PopularPresetsResponse> {
  const res = await apiGet<any>(`/keyword-research/popular-presets?market=${encodeURIComponent(market)}`);
  return (res?.data || res) as PopularPresetsResponse;
}

export interface GoldenCluster {
  keyword: string;
  core_root: string;
  country_code?: string;
  country_name?: string;
  language_name?: string;
  buyer_intent: string;
  search_volume: number;
  conversion_score: number;
  cpc: string;
  recommended_page: string;
}

export interface WangcaiAutopilotResult {
  agent_name: string;
  engine: string;
  product_topic: string;
  market: string;
  target_country?: string;
  target_country_name?: string;
  transmutation?: TransmutationData;
  multilingual_matrix?: MultilingualMatrixItem[];
  executive_summary: string;
  metrics_projection: {
    total_potential_buyers: string;
    projected_inquiries_monthly: string;
    historical_conversion_rate: string;
    projected_deal_volume_usd: string;
    customer_effort_score: string;
  };
  golden_clusters: GoldenCluster[];
  auto_deploy_status: {
    tenant_library: { status: string; message: string };
    site_seo_meta: { status: string; message: string };
    geo_ai_answer_box: { status: string; message: string };
    outreach_radar: { status: string; message: string };
  };
  researched_at: string;
}

/** 旺财 × DeerFlow 2.0 全自动化深度研究托管（免除客户调研并自动置换多国母语） */
export async function runWangcaiAutopilotResearch(params: {
  product_or_topic: string;
  target_market?: string;
  target_country?: string;
  auto_apply?: boolean;
}): Promise<WangcaiAutopilotResult> {
  const res = await apiPost<any>('/keyword-research/wangcai-autopilot', params);
  return (res?.data || res) as WangcaiAutopilotResult;
}


