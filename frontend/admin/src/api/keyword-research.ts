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

export interface PitfallDiagnostic {
  pitfall_id: string;
  name: string;
  risk_level: string;
  hazard_description: string;
  aeos_mitigation: string;
  status: string;
}

export interface NavigationItem {
  item_id: string;
  nav_title: string;
  page_type: string;
  slug: string;
  target_intent: string;
  google_search_volume: number;
  /** 后端 A1 新增：搜索量取数来源（semrush_live_api | google_benchmark_db） */
  data_source?: string;
  /** 后端 A1 新增：取数状态（matched_exact | estimated | ...），estimated 表示算法估算而非真实词 */
  raw_status?: string;
  /** 后端 A1 新增：该导航项实际绑定的核验关键词 */
  target_keyword?: string;
  conversion_rationale: string;
  sub_items?: Array<{ title: string; slug: string; intent: string }>;
}

export interface PillarSolution {
  title: string;
  application_scene: string;
  target_keyword: string;
  target_buyer: string;
  url: string;
  value_hook: string;
}

export interface PillarVsSubstitute {
  vs_title: string;
  old_material: string;
  our_product: string;
  target_search_term: string;
  pain_point_resolved: string;
  url: string;
  comparison_points: string[];
}

export interface PillarStandard {
  standard_code: string;
  standard_name: string;
  target_region: string;
  target_keyword: string;
  url: string;
  compliance_highlights: string[];
}

export interface PillarFaq {
  question: string;
  answer: string;
  search_trigger: string;
  schema_type: string;
}

export interface FivePillars {
  pillar_1_solutions: PillarSolution[];
  pillar_2_vs_substitutes: PillarVsSubstitute[];
  pillar_3_standards: PillarStandard[];
  pillar_4_faqs: PillarFaq[];
  pillar_5_multilingual_matrix: MultilingualMatrixItem[];
}

export interface PageTopologyItem {
  page_id: string;
  level: string;
  page_type: string;
  flat_url: string;
  page_title: string;
  primary_keyword: string;
  secondary_keywords: string[];
  long_tail_models: string[];
  buyer_intent: string;
  schema_type: string;
  internal_link_in: string;
  internal_link_out: string;
  priority: string;
}

export interface ExecutionPhase {
  day_range: string;
  focus: string;
  daily_page_output: string;
  action_items: string[];
  schema_deliverables: string[];
}

export interface ExecutionRoadmap {
  strategy: string;
  daily_cadence: string;
  target_total_pages: number;
  daily_phases: ExecutionPhase[];
  performance_milestones: {
    google_crawl_window: string;
    initial_indexing_window: string;
    monthly_inquiry_projection: string;
    bounce_rate_reduction: string;
  };
}

export interface CompetitorDeconstruction {
  mode: string;
  analyzed_sites: string[];
  extracted_core_categories: string[];
  extracted_selling_points: string[];
  extracted_buyer_demands: string[];
  differentiation_edge: string;
}

export interface FullSiteBlueprintResult {
  status: string;
  engine: string;
  product_name: string;
  english_base_keyword: string;
  localized_keyword: string;
  target_country: string;
  target_country_name: string;
  target_market: string;
  /** 行业判定（A5）：insulation | sealing | tiles_stone | doors_windows */
  industry_key?: string;
  /** 模板作用域（A5）：rock_wool（建材岩棉保留模板）| generic（非建材已降级） */
  template_scope?: string;
  mode: 'TEMPLATE_FALLBACK_NO_CRAWL' | 'BLUE_OCEAN_FIVE_PILLARS';
  mode_description: string;
  /** 诚实声明（A4）：传 competitor_urls 时提示未真实抓取 */
  honesty_note?: string;
  pitfall_diagnostics: PitfallDiagnostic[];
  navigation_architecture: NavigationItem[];
  five_pillars: FivePillars;
  competitor_deconstruction?: CompetitorDeconstruction;
  page_topology_matrix: PageTopologyItem[];
  execution_roadmap: ExecutionRoadmap;
  /** 超出蓝图职责的部署/运维建议（A6），由部署侧执行 */
  advisory_actions?: AdvisoryAction[];
}

export interface AdvisoryAction {
  action: string;
  owner_hint: string;
  note: string;
}

export interface FullSiteBlueprintParams {
  product_name: string;
  product_parameters?: string;
  substitute_products?: string;
  industry_standards?: string;
  customer_faqs?: string;
  competitor_urls?: string[];
  target_country?: string;
  target_market?: string;
}

/** 生成全站 SEO 关键词布局与避坑拓扑蓝图（含 4 大避坑诊断、五维推演与扁平拓扑排期） */
export async function getFullSiteBlueprint(
  params: FullSiteBlueprintParams
): Promise<FullSiteBlueprintResult> {
  const res = await apiPost<any>('/keyword-research/full-site-blueprint', params);
  return (res?.data || res) as FullSiteBlueprintResult;
}



