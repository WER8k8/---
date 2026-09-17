/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 产品页 AI 生成 — 拼 prompt 走 /api/v1/ai/generate（NVIDIA NIM） */

export type ProductAiGenerateParams = {
  content_type?: string;
  keywords?: string[];
  product_name?: string;
  category_name?: string;
  density?: number | null;
  strength_grade?: string;
  thermal_conductivity?: number | null;
  fire_rating?: string;
  existing_description?: string;
};

function infoBlock(p: ProductAiGenerateParams): string {
  const lines: string[] = [];
  if (p.product_name) lines.push(`产品名称：${p.product_name}`);
  if (p.category_name) lines.push(`产品分类：${p.category_name}`);
  if (p.density) lines.push(`干密度：${p.density} kg/m³`);
  if (p.strength_grade) lines.push(`强度等级：${p.strength_grade}`);
  if (p.thermal_conductivity) lines.push(`导热系数：${p.thermal_conductivity} W/m·K`);
  if (p.fire_rating) lines.push(`防火等级：${p.fire_rating}`);
  return lines.join('\n');
}

export function buildProductAiPrompt(p: ProductAiGenerateParams): string {
  const type = p.content_type || 'product';
  const info = infoBlock(p);
  const kw = (p.keywords || []).filter(Boolean).join('、') || p.product_name || '';

  if (type === 'seo_title') {
    return `请根据以下建材产品信息生成 SEO 标题（30-60 字，一行，不要引号）：\n\n${info}\n\n要求：含核心关键词；突出卖点；适合 B2B 官网；诚实不夸大。`;
  }
  if (type === 'seo_description') {
    return `请根据以下建材产品信息生成 SEO 描述（80-160 字，一段）：\n\n${info}\n产品描述：${(p.existing_description || '').slice(0, 300)}\n\n要求：自然融入关键词；突出规格与优势；诚实不夸大。`;
  }
  return `请为以下建材产品生成专业产品描述（300-500 字，分段）：\n\n${info}\n关键词：${kw}\n\n要求：含技术参数；适合 B2B 出口官网；引用常见行业标准表述；诚实不夸大。`;
}
