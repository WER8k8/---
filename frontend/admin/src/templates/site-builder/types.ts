/** 可视化建站 · 模板与导出结构（与 tenant site_content 对齐） */

export type SiteBuilderTemplateId =
  | 'premium-b2b-v1'
  | 'insulation-classic'
  | 'building-modern'
  | 'export-pro'
  | 'fireproof-safety'
  | 'rubber-insulation'
  | 'steel-structure'
  | 'ceramic-stone'
  | 'hvac-duct';

export interface SiteBuilderTemplateMeta {
  id: SiteBuilderTemplateId;
  name: string;
  description: string;
  industry: string;
}

export interface SiteContentSnapshot {
  brand: { name?: string; tagline?: string };
  footer: { text?: string };
  theme: { headerBg?: string; heroBg?: string; footerBg?: string };
  assets?: { productImages?: Array<{ url?: string; name?: string }> };
  /** 租户 SEO 策略：export / domestic / russia → hreflang x-default */
  seo?: { primaryMarket?: 'export' | 'domestic' | 'russia' };
  pages: Record<string, Record<string, unknown>>;
}

export interface VisualEditorPayload {
  templateId: SiteBuilderTemplateId;
  projectData?: Record<string, unknown>;
  html: string;
  css: string;
  updatedAt?: string;
  multiPage?: boolean;
  subPages?: Partial<Record<'products' | 'about' | 'contact', string>>;
}

export interface SiteSeoFields {
  /** Google / 海外：写入 pages.home 基字段（英文） */
  pageTitle: string;
  seoDescription: string;
  seoKeywords: string;
  /** 百度 / 国内：写入 pages.home.i18n.zh */
  domesticPageTitle: string;
  domesticSeoDescription: string;
  domesticSeoKeywords: string;
  /** Yandex / 俄罗斯：写入 pages.home.i18n.ru */
  russianPageTitle: string;
  russianSeoDescription: string;
  russianSeoKeywords: string;
  allowIndex: boolean;
  /** hreflang x-default：export(en) / domestic(zh) / russia(ru) */
  seoPrimaryMarket: 'export' | 'domestic' | 'russia';
}
