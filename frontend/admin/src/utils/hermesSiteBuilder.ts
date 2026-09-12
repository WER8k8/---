/**
 * Hermes 智能建站 — 统一走 ai_site_builder 插件，设计技能约束防跑偏。
 * 客户只需：产品名 + 可选产品白底图；文案/结构由 Hermes + 大模型生成。
 */
import { apiPost } from '@/utils/api';

export interface HermesSiteBuilderResult {
  siteContent: Record<string, unknown>;
  source: 'ai' | 'template';
  saved: boolean;
  reply: string;
  designSkillsApplied: string[];
  eccExpertsApplied?: string[];
  pipelineTrace?: Array<Record<string, unknown>>;
  lProPublishGate?: {
    publish_ready?: boolean;
    p0?: number;
    issues?: Array<{ check?: string; detail?: string }>;
  };
}

const SKILL_LABELS: Record<string, string> = {
  'ui-design-handoff': 'UI 设计令牌',
  'brand-copy-plain': '客户可读文案',
  'site-editor-schema': '站点编辑器结构',
  'customer-product-assets': '客户产品图挂接',
  'industry-giant-narrative': '行业巨头叙事',
  'corporate-about-us': '企业关于页',
  'insulation-giant-solutions': '保温全领域方案',
  'sme-acceptable-bar': '个人站合格线',
  'western-inquiry-conversion': '西方询盘转化',
  'anti-clutter-layout': '反拥挤排版',
  'jiushuo-sme-bar': '九硕式合格站',
};

export async function runHermesSiteBuilder(options: {
  productName: string;
  autoSave?: boolean;
  productImages?: string[];
  locationHint?: string;
  runProductResearch?: boolean;
  /** 默认跳过 11 语种 AI 翻译，显著缩短首屏建站（模板 i18n 仍会补全） */
  skipI18nAi?: boolean;
}): Promise<HermesSiteBuilderResult> {
  const productName = options.productName.trim();
  if (!productName) {
    throw new Error('请填写产品名称');
  }

  const images = (options.productImages || []).filter(Boolean);
  const locationHint = (options.locationHint || '').trim();

  const data = await apiPost<{
    site_content?: Record<string, unknown>;
    source?: string;
    saved?: boolean;
    design_skills_applied?: string[];
    product_profile?: Record<string, unknown>;
    l_pro_publish_gate?: {
      publish_ready?: boolean;
      p0?: number;
      issues?: Array<{ check?: string; detail?: string }>;
    };
  }>('/tenants/self/site-generate', {
    product_name: productName,
    auto_save: Boolean(options.autoSave),
    product_images: images,
    location_hint: locationHint || undefined,
    run_product_research: options.runProductResearch === true,
    skip_i18n_ai: options.skipI18nAi !== false,
  });

  const siteContent = data?.site_content;
  if (!siteContent) {
    throw new Error('建站未返回站点内容');
  }

  return {
    siteContent,
    source: data.source === 'ai' ? 'ai' : 'template',
    saved: Boolean(data.saved),
    reply: String(data.product_profile?.primary_product ? `已基于「${data.product_profile.primary_product}」生成官网` : '网站内容已生成'),
    designSkillsApplied: (data.design_skills_applied || []).map(
      (id) => SKILL_LABELS[id] || id,
    ),
    lProPublishGate: data.l_pro_publish_gate,
  };
}
