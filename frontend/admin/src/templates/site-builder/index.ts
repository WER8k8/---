import type { SiteBuilderTemplateMeta } from './types';

export type { SiteBuilderTemplateId, SiteContentSnapshot, VisualEditorPayload, SiteSeoFields } from './types';
export { buildPageHtml } from './buildPageHtml';
export { buildVisualSiteBundle, buildVisualSubPage } from './buildVisualSiteBundle';
export { applyIndustryPresets, applyJtbdPresets, resolveJtbdPreset, syncHeroFromAssets, TEMPLATE_LAYOUT } from './industryPresets';
export { layoutLabel, layoutKind, tenantNavHref } from './buildPageShell';
export { snapshotToSeo, applySeoToSnapshot } from './seoSync';
export { TEMPLATE_PREVIEW_COLORS } from './templatePreview';
export { parseVisualHtmlToSnapshot, mergeParsedIntoSnapshot } from './parseVisualHtml';

export const SITE_BUILDER_TEMPLATES: SiteBuilderTemplateMeta[] = [
  {
    id: 'premium-b2b-v1',
    name: 'L-Pro 外贸专业站',
    description: 'ydalison 信任叙事 + T-Global 产品中心 · 多页路由 · 询盘转化',
    industry: 'export',
  },
  {
    id: 'insulation-classic',
    name: '保温建材 · 经典',
    description: '深色顶栏 + 数据条，适合保温棉、纤维类出口站',
    industry: 'insulation',
  },
  {
    id: 'building-modern',
    name: '轻集料 · 现代',
    description: '薄荷工业风，适合轻集料混凝土、环保建材',
    industry: 'lightweight',
  },
  {
    id: 'export-pro',
    name: '外贸 Pro',
    description: '全幅 Hero + 认证条 + 多栏页脚，B2B 询盘转化型',
    industry: 'export',
  },
  {
    id: 'fireproof-safety',
    name: '防火材料 · 安全',
    description: '红灰工业风，突出防火等级与认证徽章',
    industry: 'fireproof',
  },
  {
    id: 'rubber-insulation',
    name: '橡塑保温 · 工程',
    description: '深绿工程风，适合 B1 橡塑板、管材项目站',
    industry: 'rubber',
  },
  {
    id: 'steel-structure',
    name: '钢结构 · 重工',
    description: '钢蓝配色，适合型钢、板材、装配式构件',
    industry: 'steel',
  },
  {
    id: 'ceramic-stone',
    name: '瓷砖石材 · 展示',
    description: '大图 Hero 横幅 + 产品网格，适合瓷砖/岩板展示型',
    industry: 'ceramic',
  },
  {
    id: 'hvac-duct',
    name: '暖通风管 · 系统',
    description: '清爽蓝绿，风管、岩棉、消音材料系统商',
    industry: 'hvac',
  },
];

export const DEFAULT_TEMPLATE_ID = SITE_BUILDER_TEMPLATES[0].id;

export function getTemplateMeta(id: string): SiteBuilderTemplateMeta | undefined {
  return SITE_BUILDER_TEMPLATES.find((t) => t.id === id);
}
