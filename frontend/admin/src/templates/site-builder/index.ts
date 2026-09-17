/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import type { SiteBuilderTemplateMeta } from './types';

export type { SiteBuilderTemplateId, SiteBuilderTemplateMeta, SiteContentSnapshot, VisualEditorPayload, SiteSeoFields } from './types';
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
    name: 'L-Pro 旗舰外贸站 (Google Top-3)',
    description: 'ydalison 信任叙事 + T-Global 多模态产品中心，内嵌 EEAT 认证与询盘七步闭环',
    industry: 'export',
    category: 'portal',
    categoryLabel: '外贸官网',
    author: 'Meoo出海精研室',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01MxUXzS1xYRjMwA2la_!!6000000006455-2-tps-184-184.png',
    views: '18.6k',
    likes: 192,
    tags: ['Google SEO', 'EEAT认证', '高转化RFQ'],
    prompt: '帮我设计一套具备 Google Top-3 权重的工业外贸旗舰独立站，包含：顶栏国际认证条与多币种询价、Hero 首屏工厂实景与 3D 悬浮信任徽章、四大核心解决方案网格（支持查看 CAD 与技术规格）、工程案例故事（带项目地点与客户评价）、符合西方采购商习惯的多步骤 RFQ 形式发票询盘表单，以及多栏合规页脚。整体风格极简奢雅，符合国际买家审美。',
    coverUrl: 'https://img.alicdn.com/imgextra/i4/O1CN01n6BUtq1iXmxBFROO9_!!6000000004423-2-tps-1681-936.png',
  },
  {
    id: 'insulation-classic',
    name: '保温节能建材 · 国际工程站',
    description: '经典深空蓝工程风 + ASTM/CE 标准数据条，适合离心玻璃棉、岩棉、橡塑等材料出口',
    industry: 'insulation',
    category: 'portal',
    categoryLabel: '外贸官网',
    author: 'YouDing工业设计组',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01Da0Hgd1C32ej0JRrG_!!6000000000024-2-tps-114-96.png',
    views: '14.2k',
    likes: 85,
    tags: ['ASTM检测', '集装箱配载', '工程直供'],
    prompt: '创建一个面向欧美与中东大型工程承包商的保温材料出口企业官网。首屏展示工厂智能连续生产线大图与年产能数据（50,000+ 吨），中间包含四大工程应用场景（建筑屋面、暖通风管、冷库冷链、船舶海工），产品展示区突出 R-value 热阻值与防火等级，底部附带海关出口包装规格表与 WhatsApp 一键直连专家。',
    coverUrl: 'https://img.alicdn.com/imgextra/i3/O1CN01TnanNh1ukPFprNgDn_!!6000000006075-2-tps-1432-1098.png',
  },
  {
    id: 'building-modern',
    name: '绿色轻集料 · 现代环保站',
    description: '清爽冷灰底与科技微光，突出 LEED 绿色建筑认证与低碳足迹',
    industry: 'lightweight',
    category: 'portal',
    categoryLabel: '外贸官网',
    author: 'Nordic Studio',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i3/O1CN01c8a29H1i7DxHezYAf_!!6000000004365-49-tps-240-240.webp',
    views: '9.8k',
    likes: 64,
    tags: ['绿色低碳', 'LEED认证', '现代极简'],
    prompt: '帮我制作一个现代北欧风的绿色建筑材料国际站。界面宽阔大气、富有呼吸感，以低饱和环保绿为主色，重点展示轻集料混凝土与陶粒制品的减重抗震性能。包含碳足迹核算器组件、国际第三方检测报告下载中心，以及全球样板工程互动地图。',
    coverUrl: 'https://img.alicdn.com/imgextra/i2/O1CN01l1Snij1M6Nhpl0gUk_!!6000000001385-2-tps-1433-1098.png',
  },
  {
    id: 'export-pro',
    name: '全域出海拓客 · 营销高转化站',
    description: '全幅流光 Hero + 动态资质走字条 + 跨境样品申请，专为跨境获客与社媒承接打造',
    industry: 'export',
    category: 'h5',
    categoryLabel: '高转化营销',
    author: 'GrowthHacker',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01MxUXzS1xYRjMwA2la_!!6000000006455-2-tps-184-184.png',
    views: '16.5k',
    likes: 128,
    tags: ['社媒导流', '样品免费寄送', '快速成交'],
    prompt: '设计一个专为社媒与海外买家精准投放打造的高转化独立站 Landing Page。首屏以强烈视觉冲击力的出海主标与快速样品申请弹窗（Free Sample Request），中部为买家评测视频与开箱实拍，底部提供实时库存查询与 WhatsApp 实时博弈谈判入口。',
    coverUrl: 'https://img.alicdn.com/imgextra/i3/O1CN01DoEVsC1zk0zkFw1xk_!!6000000006751-2-tps-1432-1098.png',
  },
  {
    id: 'fireproof-safety',
    name: '耐火特种材料 · 安全合规站',
    description: '严谨工业灰搭配警示红金，权威呈现 UL94/EN13501 防火阻燃认证',
    industry: 'fireproof',
    category: 'portal',
    categoryLabel: '行业垂直',
    author: 'FireLab Lab',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01Da0Hgd1C32ej0JRrG_!!6000000000024-2-tps-114-96.png',
    views: '7.2k',
    likes: 49,
    tags: ['UL94', 'EN13501', '特种防护'],
    prompt: '创建一个面向欧美高安全等级建筑的防火隔热特种材料官网。色彩以深灰与安全红为主，核心突出燃烧测试实验视频、耐火极限时数（1-4小时对比表），以及全球船级社（DNV/CCS）与建筑行业权威认证证书网格。',
    coverUrl: 'https://img.alicdn.com/imgextra/i4/O1CN01V81XIS1GtwsKUoBbB_!!6000000000681-2-tps-1586-992.png',
  },
  {
    id: 'rubber-insulation',
    name: '橡塑保温工程 · 暖通配套站',
    description: '工程级深墨绿，聚焦 B1 级橡塑绝热管材、板材与洁净室管道配套',
    industry: 'rubber',
    category: 'portal',
    categoryLabel: '行业垂直',
    author: 'HVAC Engineer',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i3/O1CN01c8a29H1i7DxHezYAf_!!6000000004365-49-tps-240-240.webp',
    views: '8.4k',
    likes: 56,
    tags: ['B1难燃', '防结露', '管系工程'],
    prompt: '搭建一个专业暖通空调橡塑保温工程官网。重点解析导热系数、湿阻因子与防结露设计，配有工程选型计算器（厚度计算与能耗节省预估），并提供一键获取施工安装指南和技术数据单（TDS）功能。',
    coverUrl: 'https://img.alicdn.com/imgextra/i2/O1CN01ui7JMb1ynOITp0fmE_!!6000000006623-2-tps-2880-1600.png',
  },
  {
    id: 'steel-structure',
    name: '装配式钢结构 · 重工总包站',
    description: '工业蓝灰硬派工程风格，全景展示厂房、网架、光伏支架与重型钢构装配',
    industry: 'steel',
    category: 'portal',
    categoryLabel: '行业垂直',
    author: 'SteelTech Global',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01MxUXzS1xYRjMwA2la_!!6000000006455-2-tps-184-184.png',
    views: '11.3k',
    likes: 78,
    tags: ['装配式', 'AISC标准', '集装箱散件'],
    prompt: '创建一个装配式重钢结构与工程总包国际站。页面呈现大型车间航拍大图与钢构节点 3D 渲染，详细列明车间起吊吨位、数控切割精度与探伤检测标准，支持海外工程客户上传建筑图纸一键生成 BOQ 概算。',
    coverUrl: 'https://img.alicdn.com/imgextra/i4/O1CN01EBqYv920osouyHqEj_!!6000000006897-2-tps-2880-1600.png',
  },
  {
    id: 'ceramic-stone',
    name: '奢石岩板 · 建筑美学展示站',
    description: '艺术画廊级大版幅排版，呈现高级瓷砖、大理石与通体岩板的光影质感',
    industry: 'ceramic',
    category: 'portal',
    categoryLabel: '外贸官网',
    author: 'ArchDaily Studio',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i4/O1CN01Da0Hgd1C32ej0JRrG_!!6000000000024-2-tps-114-96.png',
    views: '15.1k',
    likes: 110,
    tags: ['奢石岩板', '建筑美学', '全景画廊'],
    prompt: '制作一个具有意大利顶级设计展美学风格的高端岩板石材官网。首屏采用全屏沉浸式无缝铺贴视差效果，产品中心支持按纹理色彩、厚度规格与应用场景（厨房岛台/幕墙/卫浴）丝滑过滤，并支持高清无压缩原纹理纹样下载。',
    coverUrl: 'https://img.alicdn.com/imgextra/i1/O1CN01IDDcPi1be11nj5e50_!!6000000003489-2-tps-1681-935.png',
  },
  {
    id: 'hvac-duct',
    name: '暖通风系统 · 节能设备综合站',
    description: '现代科技蓝绿配调，风管、复合保温管件、消音系统全集成商',
    industry: 'hvac',
    category: 'tools',
    categoryLabel: '外贸官网',
    author: 'HVAC Master',
    authorAvatar: 'https://gw.alicdn.com/imgextra/i3/O1CN01c8a29H1i7DxHezYAf_!!6000000004365-49-tps-240-240.webp',
    views: '10.7k',
    likes: 72,
    tags: ['SMACNA', '消音风管', '气密性检测'],
    prompt: '帮我做一个暖通节能管网与消音降噪系统综合官网。符合 SMACNA 国际风管规范，首屏清晰陈列系统拓扑图与风量风阻测试数据，支持在线定制尺寸与直发集装箱海运模拟。',
    coverUrl: 'https://img.alicdn.com/imgextra/i2/O1CN0139B7r71uJqHaCYQ6a_!!6000000006017-2-tps-1433-1098.png',
  },
];

export const DEFAULT_TEMPLATE_ID = SITE_BUILDER_TEMPLATES[0].id;

export function getTemplateMeta(id: string): SiteBuilderTemplateMeta | undefined {
  return SITE_BUILDER_TEMPLATES.find((t) => t.id === id);
}
