/** 行业默认文案包 — 模板切换 / AI 同步时补全空字段 */

import type { SiteBuilderTemplateId, SiteContentSnapshot } from './types';
import { getTemplateMeta } from './index';

export type SiteLayoutKind = 'classic' | 'hero-banner' | 'industrial';

export const TEMPLATE_LAYOUT: Record<SiteBuilderTemplateId, SiteLayoutKind> = {
  'premium-b2b-v1': 'hero-banner',
  'insulation-classic': 'classic',
  'building-modern': 'classic',
  'export-pro': 'hero-banner',
  'fireproof-safety': 'industrial',
  'rubber-insulation': 'classic',
  'steel-structure': 'industrial',
  'ceramic-stone': 'hero-banner',
  'hvac-duct': 'classic',
};

interface IndustryPreset {
  trustBadges: string[];
  certs: string[];
  stats: Array<{ value: string; label: string }>;
  solutions: Array<{ segment: string; title: string; description?: string }>;
  applications: Array<{ title: string; description: string }>;
  advantages: Array<{ title: string; description: string }>;
  sectionDesc: string;
}

/** SITE-JTBD-01 · 行业无关 B2B 建站思维（任务导向，非工厂陈列） */
export interface JtbdHomePreset {
  primary_promise: string;
  heroTitle: string;
  heroDescription: string;
  inquiryHook: string;
  ctaPrimary: string;
  serviceStages: Array<{ stage: string; title: string; description?: string }>;
  knowledgeTopics: Array<{ title: string; hook?: string }>;
  trustBadges: string[];
  certs: string[];
  stats: Array<{ value: string; label: string }>;
  solutions: Array<{ segment: string; title: string; description?: string }>;
  advantages: Array<{ title: string; description: string }>;
  sectionDesc: string;
  sectionTitle: string;
}

const GENERIC_HERO_TITLES = new Set([
  '您的公司',
  '专业制造商',
  '专业建材制造商',
  'Professional Manufacturer',
  'Manufacturing Partner',
]);

function isGenericHeroTitle(title: unknown): boolean {
  const t = String(title || '').trim();
  if (!t) return true;
  if (GENERIC_HERO_TITLES.has(t)) return true;
  return /^专业.+制造商/.test(t) || /professional\s+manufacturer/i.test(t);
}

function mergeScalar(current: unknown, preset: string): string {
  const cur = String(current || '').trim();
  return cur || preset;
}

/** 通用 B2B JTBD 骨架 — 不含未核实 SLA 数字（no-fake-delivery） */
export const B2B_JTBD_PRESET: JtbdHomePreset = {
  primary_promise: 'One clear outcome site-wide: scoped quote, gated sampling, production you can audit.',
  heroTitle: 'Quote, sample, and scale — structured for buyers with a job to do',
  heroDescription:
    'Buyers arrive with drawings and deadlines, not curiosity tours. We answer by project stage: feasibility → sample → pilot → volume.',
  inquiryHook: 'Send specs or drawings — we reply with scope, lead-time assumptions, and next steps.',
  ctaPrimary: 'Request Quote',
  serviceStages: [
    { stage: '01', title: 'RFQ & feasibility', description: 'Material, tolerance, MOQ, and process fit review.' },
    { stage: '02', title: 'Prototype / sample', description: 'First articles, test reports, packaging sign-off.' },
    { stage: '03', title: 'Pilot batch', description: 'Small-run validation before volume commitment.' },
    { stage: '04', title: 'Volume production', description: 'Stable QC cadence, docs, and shipment rhythm.' },
  ],
  knowledgeTopics: [
    { title: 'How to package an RFQ buyers can quote fast', hook: 'Drawings, qty, destination, cert needs' },
    { title: 'Sample gate vs pilot batch: when to commit tooling', hook: 'Align buyer expectations with shop floor' },
    { title: 'Export documentation buyers expect on first order', hook: 'CO, HS codes, inspection booking' },
  ],
  trustBadges: ['Stage-gated workflow', 'Audit-ready QC', 'OEM / ODM', 'Export documentation'],
  certs: ['ISO 9001', 'Factory audit', 'Third-party test reports', 'Project submittals'],
  stats: [
    { value: 'RFQ→Scope', label: 'Structured quote workflow' },
    { value: 'Sample gate', label: 'Before volume commit' },
    { value: 'QC trail', label: 'Reports tied to batch' },
    { value: 'One CTA', label: 'Same promise everywhere' },
  ],
  solutions: [
    { segment: 'New product launch', title: 'DFM review + first-article program' },
    { segment: 'Cost-down redesign', title: 'Material/process alternatives with tolerance map' },
    { segment: 'Urgent replacement', title: 'Reverse spec match + expedited sampling' },
  ],
  advantages: [
    { title: 'Outcome-first pages', description: 'Hero, stats, and CTA repeat the same buyer promise.' },
    { title: 'Evidence over slogans', description: 'Certs, cases, and process gates — not adjective walls.' },
  ],
  sectionTitle: 'Why buyers shortlist us',
  sectionDesc: 'Capabilities mapped to how overseas buyers actually decide — not how our warehouse is organized.',
};

/** JTBD-01e · 精密制造词包（CNC/注塑/钣金/3D 打印），复用同一骨架 */
export const PRECISION_MANUFACTURING_JTBD: JtbdHomePreset = {
  ...B2B_JTBD_PRESET,
  heroTitle: 'From drawing to shipped parts — CNC, molding, sheet metal & additive',
  heroDescription:
    'Machining, molding, fabrication, and 3D print programs under one RFQ → sample → production path.',
  solutions: [
    { segment: 'CNC machining', title: 'Aluminum, steel & stainless precision parts' },
    { segment: 'Injection molding', title: 'Tooling program + molded components' },
    { segment: 'Sheet metal', title: 'Laser, bend, weld & powder-coat assemblies' },
    { segment: '3D printing', title: 'Rapid prototypes → small-series production' },
  ],
  knowledgeTopics: [
    { title: 'CNC tolerance bands that affect quote speed', hook: 'GD&T packages buyers should attach' },
    { title: 'Injection mold steel vs aluminum tooling trade-offs', hook: 'When to gate with T0/T1 shots' },
    { title: 'Sheet metal bend radii & PEM hardware pitfalls', hook: 'DFM notes for overseas buyers' },
    { title: 'Additive vs subtractive for first article', hook: 'Material, finish, and MOQ fit' },
  ],
  trustBadges: ['CNC · Molding · Sheet metal · 3DP', 'First-article reports', 'OEM programs', 'Export packing'],
};

const PRESETS: Record<string, IndustryPreset> = {
  insulation: {
    trustBadges: ['15+ Years in Insulation', 'OEM / ODM', 'ISO 9001', 'EN / ASTM Tested'],
    certs: ['ISO 9001', 'CE Mark', 'ASTM E84', 'Factory Audit'],
    stats: [
      { value: '80,000+', label: 'Tons / Year Capacity' },
      { value: '45+', label: 'Export Countries' },
      { value: '1,200+', label: 'Project Clients' },
      { value: '120+', label: 'SKU & Specs' },
    ],
    solutions: [
      { segment: 'Petrochemical', title: 'High-temp pipe & equipment insulation' },
      { segment: 'Power Plant', title: 'Boiler, turbine & duct lining systems' },
      { segment: 'HVAC', title: 'Chilled water & air duct thermal packs' },
    ],
    applications: [
      { title: 'Industrial Furnace', description: 'Lining for kilns and heat treatment lines' },
      { title: 'Cold Storage', description: 'Low thermal conductivity panel systems' },
      { title: 'Marine', description: 'Fire & thermal protection for engine rooms' },
    ],
    advantages: [
      { title: 'Low Thermal Conductivity', description: 'Stable λ-value across operating temperatures.' },
      { title: 'Export Documentation', description: 'CO, packing list, test reports & HS codes.' },
    ],
    sectionDesc: 'Integrated fiber & blanket supply for EPC and distributor channels.',
  },
  fireproof: {
    trustBadges: ['A1 / A2 Fire Class', 'Third-party Lab Reports', 'OEM Projects', 'Global Export'],
    certs: ['ISO 9001', 'CE EN 13501', 'BS 476', 'SGS Fire Test'],
    stats: [
      { value: '30,000+', label: 'Tons Fire Materials' },
      { value: '35+', label: 'Countries Served' },
      { value: '500+', label: 'Fire-rated SKUs' },
      { value: '24h', label: 'Quotation Response' },
    ],
    solutions: [
      { segment: 'Facade', title: 'Non-combustible cladding & board systems' },
      { segment: 'Tunnel', title: 'Fire protection boards for infrastructure' },
      { segment: 'Data Center', title: 'Fire barriers & cable tray protection' },
    ],
    applications: [
      { title: 'Commercial Building', description: 'Fire-rated partition & shaft walls' },
      { title: 'Oil & Gas', description: 'Passive fire protection for equipment' },
    ],
    advantages: [
      { title: 'Certified Fire Performance', description: 'Reports aligned with EU / UK / GCC requirements.' },
      { title: 'Project Technical Support', description: 'Spec matching, submittals & site samples.' },
    ],
    sectionDesc: 'Fire-rated materials with traceable test documentation for regulated markets.',
  },
  ceramic: {
    trustBadges: ['Large Format Slabs', 'OEM Private Label', 'Anti-slip Series', 'Container Export'],
    certs: ['ISO 9001', 'CE', 'SGS Abrasion Test', 'Water Absorption Report'],
    stats: [
      { value: '5M+', label: 'SQM / Year Output' },
      { value: '50+', label: 'Export Markets' },
      { value: '800+', label: 'Designs & Finishes' },
      { value: '7 Days', label: 'Sample Lead Time' },
    ],
    solutions: [
      { segment: 'Retail Chain', title: 'Private label tile collections' },
      { segment: 'Hotel Project', title: 'Slab & porcelain package supply' },
      { segment: 'Outdoor', title: 'Anti-slip patio & pool deck series' },
    ],
    applications: [
      { title: 'Living & Bedroom', description: 'Wood-look and stone-look porcelain' },
      { title: 'Commercial Floor', description: 'Heavy traffic polished & matt finishes' },
    ],
    advantages: [
      { title: 'Showroom-ready Imagery', description: 'High-res scene photos for your market.' },
      { title: 'Mixed Container Loading', description: 'Flexible MOQ for multi-SKU orders.' },
    ],
    sectionDesc: 'Visual-first catalog supply for distributors and project wholesalers.',
  },
  export: {
    trustBadges: ['B2B Export Focus', 'FOB / CIF Support', 'OEM / ODM', '24h Quote'],
    certs: ['ISO 9001', 'CE', 'Factory Audit', 'SGS Inspection'],
    stats: [
      { value: '50,000+', label: 'Tons Shipped / Year' },
      { value: '40+', label: 'Active Markets' },
      { value: '1,000+', label: 'B2B Buyers' },
      { value: '100+', label: 'Product Lines' },
    ],
    solutions: [
      { segment: 'Distributor', title: 'Wholesale catalog & private label' },
      { segment: 'EPC', title: 'Project spec & documentation pack' },
      { segment: 'E-commerce', title: 'Packaging & small-batch SKUs' },
    ],
    applications: [],
    advantages: [
      { title: 'Trade Terms Flexibility', description: 'FOB, CIF and door-to-door coordination.' },
      { title: 'Compliance Pack', description: 'HS code, CO and inspection booking support.' },
    ],
    sectionDesc: 'Conversion-oriented export site structure for qualified B2B leads.',
  },
};

const INDUSTRY_ALIAS: Record<string, keyof typeof PRESETS> = {
  insulation: 'insulation',
  lightweight: 'insulation',
  rubber: 'insulation',
  hvac: 'insulation',
  fireproof: 'fireproof',
  steel: 'export',
  ceramic: 'ceramic',
  export: 'export',
  'precision-manufacturing': 'export',
  'b2b-jtbd': 'export',
};

const JTBD_SKIN_BY_INDUSTRY: Record<string, 'precision' | 'b2b'> = {
  steel: 'precision',
  'precision-manufacturing': 'precision',
};

function mergeList<T>(current: unknown, preset: T[]): T[] {
  if (Array.isArray(current) && current.length) return current as T[];
  return preset;
}

export function resolveJtbdPreset(templateId: SiteBuilderTemplateId): JtbdHomePreset {
  const meta = getTemplateMeta(templateId);
  const skin = JTBD_SKIN_BY_INDUSTRY[meta?.industry || ''] || 'b2b';
  return skin === 'precision' ? PRECISION_MANUFACTURING_JTBD : B2B_JTBD_PRESET;
}

export function applyJtbdPresets(
  templateId: SiteBuilderTemplateId,
  snapshot: SiteContentSnapshot,
): SiteContentSnapshot {
  const jtbd = resolveJtbdPreset(templateId);
  const home = { ...(snapshot.pages?.home || {}) };

  home.primary_promise = mergeScalar(home.primary_promise, jtbd.primary_promise);
  if (isGenericHeroTitle(home.title)) home.title = jtbd.heroTitle;
  if (!String(home.description || '').trim()) home.description = jtbd.heroDescription;
  home.inquiryHook = mergeScalar(home.inquiryHook, jtbd.inquiryHook);
  if (!String(home.ctaPrimary || '').trim()) home.ctaPrimary = jtbd.ctaPrimary;
  home.serviceStages = mergeList(home.serviceStages, jtbd.serviceStages);
  home.knowledgeTopics = mergeList(home.knowledgeTopics, jtbd.knowledgeTopics);
  home.trustBadges = mergeList(home.trustBadges, jtbd.trustBadges);
  home.stats = mergeList(home.stats, jtbd.stats);
  home.solutions = mergeList(home.solutions, jtbd.solutions);
  home.advantages = mergeList(home.advantages, jtbd.advantages);
  if (!home.sectionDesc) home.sectionDesc = jtbd.sectionDesc;
  if (!home.sectionTitle) home.sectionTitle = jtbd.sectionTitle;

  const brand = { ...(snapshot.brand || {}) };
  if (!String(brand.tagline || '').trim() || /专业.+制造商/.test(String(brand.tagline))) {
    brand.tagline = jtbd.primary_promise;
  }

  return {
    ...snapshot,
    brand,
    pages: {
      ...snapshot.pages,
      home,
    },
  };
}

export function applyIndustryPresets(
  templateId: SiteBuilderTemplateId,
  snapshot: SiteContentSnapshot,
): SiteContentSnapshot {
  const meta = getTemplateMeta(templateId);
  const key = INDUSTRY_ALIAS[meta?.industry || 'export'] || 'export';
  const preset = PRESETS[key];

  let next = snapshot;
  if (preset) {
    const home = { ...(next.pages?.home || {}) };
    const about = { ...(next.pages?.about || {}) };

    home.trustBadges = mergeList(home.trustBadges, preset.trustBadges);
    home.stats = mergeList(home.stats, preset.stats);
    home.solutions = mergeList(home.solutions, preset.solutions);
    home.applications = mergeList(home.applications, preset.applications);
    home.advantages = mergeList(home.advantages, preset.advantages);
    if (!home.sectionDesc) home.sectionDesc = preset.sectionDesc;

    next = {
      ...next,
      pages: {
        ...next.pages,
        home,
        about,
      },
    };
  }

  return applyJtbdPresets(templateId, next);
}

export function presetCertsForTemplate(templateId: SiteBuilderTemplateId): string[] {
  const meta = getTemplateMeta(templateId);
  const key = INDUSTRY_ALIAS[meta?.industry || 'export'] || 'export';
  return PRESETS[key]?.certs || [];
}

export function syncHeroFromAssets(snapshot: SiteContentSnapshot): SiteContentSnapshot {
  const home = { ...(snapshot.pages?.home || {}) };
  const products = { ...(snapshot.pages?.products || {}) };
  const assets = snapshot.assets;
  const assetUrls = (assets?.productImages || []).map((i) => String(i.url || '')).filter(Boolean);

  if (!home.heroImage && assetUrls[0]) {
    home.heroImage = assetUrls[0];
  }

  const items = Array.isArray(products.productItems)
    ? [...(products.productItems as Array<Record<string, unknown>>)]
    : [];

  assetUrls.forEach((url, i) => {
    if (items[i] && !items[i].image) {
      items[i] = { ...items[i], image: url };
    } else if (!items[i]) {
      items[i] = { name: `Product ${i + 1}`, summary: '', image: url };
    }
  });

  if (items.length) {
    products.productItems = items;
  }

  return {
    ...snapshot,
    pages: {
      ...snapshot.pages,
      home,
      products,
    },
  };
}
