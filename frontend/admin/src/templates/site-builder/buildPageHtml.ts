import { buildEnterpriseSiteCss, type SiteThemePack } from './enterpriseSiteStyles';
import { buildSiteChrome, type ShellContext, type VisualSitePage } from './buildPageShell';
import {
  applyIndustryPresets,
  presetCertsForTemplate,
  syncHeroFromAssets,
  TEMPLATE_LAYOUT,
} from './industryPresets';
import type { SiteBuilderTemplateId, SiteContentSnapshot } from './types';

export { esc, sectionHead, listItems, pickTheme, buildHero };

function esc(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function listItems(items: unknown[], render: (item: unknown, i: number) => string): string {
  if (!Array.isArray(items) || !items.length) return '';
  return items.map(render).join('');
}

export interface ThemePack extends SiteThemePack {
  layout: 'classic' | 'hero-banner' | 'industrial';
}

export const THEMES: Record<SiteBuilderTemplateId, ThemePack> = {
  'premium-b2b-v1': {
    primary: '#0c4a6e',
    heroBg: '#f0f9ff',
    headerBg: '#0c4a6e',
    footerBg: '#082f49',
    accent: '#0284c7',
    layout: 'hero-banner',
  },
  'insulation-classic': {
    primary: '#1e3a5f',
    heroBg: '#f1f5f9',
    headerBg: '#1e293b',
    footerBg: '#1e293b',
    accent: '#4a9b8c',
    layout: 'classic',
  },
  'building-modern': {
    primary: '#0f766e',
    heroBg: '#ecfdf5',
    headerBg: '#115e59',
    footerBg: '#134e4a',
    accent: '#14b8a6',
    layout: 'classic',
  },
  'export-pro': {
    primary: '#1d4ed8',
    heroBg: '#eff6ff',
    headerBg: '#1e40af',
    footerBg: '#172554',
    accent: '#4a9b8c',
    layout: 'hero-banner',
  },
  'fireproof-safety': {
    primary: '#991b1b',
    heroBg: '#fef2f2',
    headerBg: '#7f1d1d',
    footerBg: '#450a0a',
    accent: '#dc2626',
    layout: 'industrial',
  },
  'rubber-insulation': {
    primary: '#14532d',
    heroBg: '#f0fdf4',
    headerBg: '#166534',
    footerBg: '#052e16',
    accent: '#16a34a',
    layout: 'classic',
  },
  'steel-structure': {
    primary: '#334155',
    heroBg: '#f8fafc',
    headerBg: '#1e293b',
    footerBg: '#0f172a',
    accent: '#64748b',
    layout: 'industrial',
  },
  'ceramic-stone': {
    primary: '#57534e',
    heroBg: '#fafaf9',
    headerBg: '#44403c',
    footerBg: '#292524',
    accent: '#78716c',
    layout: 'hero-banner',
  },
  'hvac-duct': {
    primary: '#0369a1',
    heroBg: '#f0f9ff',
    headerBg: '#075985',
    footerBg: '#0c4a6e',
    accent: '#0ea5e9',
    layout: 'classic',
  },
};

function sectionHead(eyebrow: string, title: string, desc?: string): string {
  return `<div class="sb-section-head">
    <p class="sb-section-eyebrow">${eyebrow}</p>
    <h2 class="sb-section-title">${title}</h2>
    ${desc ? `<p class="sb-section-desc">${esc(desc)}</p>` : ''}
  </div>`;
}

function buildHero(
  theme: ThemePack,
  opts: {
    heroTitle: string;
    heroDesc: string;
    heroImage: string;
    ctaPrimary: string;
    ctaSecondary: string;
    trustHtml: string;
    year: string;
    primaryPromise?: string;
  },
): string {
  const actions = `<div class="sb-hero-actions">
    <a class="sb-cta" href="/tenant/contact" style="background:${theme.accent}">${opts.ctaPrimary}</a>
    <a class="sb-cta sb-cta--ghost" href="/tenant/products">${opts.ctaSecondary}</a>
  </div>`;

  const visual = opts.heroImage
    ? `<div class="sb-hero-visual"><img src="${opts.heroImage}" alt="${opts.heroTitle}"/></div>`
    : `<div class="sb-hero-visual sb-hero-visual--placeholder">RFQ · Sample · Production</div>`;

  const kicker = opts.primaryPromise
    ? esc(opts.primaryPromise)
    : `B2B Export · Project stages${opts.year ? ` · Est. ${opts.year}` : ''}`;

  const inner = `<p class="sb-kicker">${kicker}</p>
    <h1 class="sb-hero-title">${opts.heroTitle}</h1>
    <p class="sb-hero-desc">${opts.heroDesc}</p>
    ${actions}
    ${opts.trustHtml}`;

  if (theme.layout === 'hero-banner' && opts.heroImage) {
    return `<section id="hero" class="sb-hero sb-hero--banner" style="background-image:url('${opts.heroImage}')">
      <div class="sb-hero-overlay"><div class="sb-container">${inner}</div></div>
    </section>`;
  }

  return `<section id="hero" class="sb-hero" style="background:${theme.heroBg}">
    <div class="sb-container sb-hero-grid">
      <div>${inner}</div>
      ${visual}
    </div>
  </section>`;
}

export function prepareSiteSnapshot(
  templateId: SiteBuilderTemplateId,
  data: SiteContentSnapshot,
): SiteContentSnapshot {
  return syncHeroFromAssets(applyIndustryPresets(templateId, data));
}

export function buildShellContext(
  data: SiteContentSnapshot,
  theme: ThemePack,
  activePage: VisualSitePage,
): ShellContext {
  const home = (data.pages?.home || {}) as Record<string, unknown>;
  const contact = (data.pages?.contact || {}) as Record<string, unknown>;

  return {
    brandName: esc(data.brand?.name || '您的公司'),
    tagline: esc(
      home.primary_promise || data.brand?.tagline || 'Scoped quote · Gated sampling · Auditable production',
    ),
    phone: esc(contact.phone || home.phone || '+86-571-0000-0000'),
    email: esc(contact.email || home.email || 'sales@example.com'),
    address: esc(contact.address || home.address || '中国 · 工厂地址'),
    footerText: esc(
      data.footer?.text || `© ${new Date().getFullYear()} ${data.brand?.name || 'Company'}. All rights reserved.`,
    ),
    year: esc(home.establishedYear || ''),
    ctaPrimary: esc(home.ctaPrimary || 'Request Quote'),
    theme: { headerBg: theme.headerBg, footerBg: theme.footerBg, accent: theme.accent },
    activePage,
  };
}

export function buildPageHtml(
  templateId: SiteBuilderTemplateId,
  rawData: SiteContentSnapshot,
): { html: string; css: string } {
  const data = prepareSiteSnapshot(templateId, rawData);
  const theme: ThemePack = { ...THEMES[templateId], layout: TEMPLATE_LAYOUT[templateId], ...pickTheme(data.theme) };
  const home = (data.pages?.home || {}) as Record<string, unknown>;
  const products = (data.pages?.products || {}) as Record<string, unknown>;
  const about = (data.pages?.about || {}) as Record<string, unknown>;
  const contact = (data.pages?.contact || {}) as Record<string, unknown>;

  const heroTitle = esc(home.title || data.brand?.name || '您的公司');
  const heroDesc = esc(home.description || data.brand?.tagline || '');
  const primaryPromise = esc(String(home.primary_promise || ''));
  const sectionTitle = esc(home.sectionTitle || 'Why buyers shortlist us');
  const sectionDesc = esc(home.sectionDesc || '');
  const aboutText = esc(about.aboutText || '');
  const ctaSecondary = esc(home.ctaSecondary || '查看产品');
  const ctaPrimary = esc(home.ctaPrimary || 'Request Quote');
  const inquiryHook = esc(
    home.inquiryHook || primaryPromise || 'Send specs or drawings — we reply with scope and next steps.',
  );
  const productsTitle = esc(products.title || '主打产品');
  const productsDesc = esc(products.description || '');

  const whatsappRaw = String(contact.whatsapp || '8613800000000');
  const whatsapp = esc(whatsappRaw.replace(/[^0-9]/g, ''));
  const heroImage = esc(String(home.heroImage || pickFirstProductImage(products) || ''));

  const trustBadges = (home.trustBadges as string[]) || [];
  const trustHtml = trustBadges.length
    ? `<div class="sb-trust-row">${trustBadges.map((b) => `<span class="sb-trust-pill">${esc(b)}</span>`).join('')}</div>`
    : '';

  const stats = (home.stats as Array<{ value?: string; label?: string }>) || [];
  const statsHtml = listItems(stats, (s) => {
    const row = s as { value?: string; label?: string };
    return `<div class="sb-stat"><div class="sb-stat-val">${esc(row.value)}</div><div class="sb-stat-lbl">${esc(row.label)}</div></div>`;
  });

  const advantages = (home.advantages as Array<{ title?: string; description?: string }>) || [];
  const advHtml = listItems(advantages, (a) => {
    const row = a as { title?: string; description?: string };
    return `<div class="sb-card"><h4>${esc(row.title)}</h4><p>${esc(row.description)}</p></div>`;
  });

  const categories = (home.categories as Array<{ name?: string; description?: string } | string>) || [];
  const catHtml = listItems(categories, (c) => {
    if (typeof c === 'string') return `<div class="sb-card"><h4>${esc(c)}</h4></div>`;
    const row = c as { name?: string; description?: string };
    return `<div class="sb-card"><h4>${esc(row.name)}</h4><p>${esc(row.description)}</p></div>`;
  });

  const solutions = (home.solutions as Array<{ segment?: string; title?: string; description?: string }>) || [];
  const solHtml = listItems(solutions, (s) => {
    const row = s as { segment?: string; title?: string; description?: string };
    const desc = row.description ? `<p>${esc(row.description)}</p>` : '';
    return `<div class="sb-solution"><div class="sb-solution-seg">${esc(row.segment || 'Use case')}</div><h4>${esc(row.title)}</h4>${desc}</div>`;
  });

  const serviceStages =
    (home.serviceStages as Array<{ stage?: string; title?: string; description?: string }>) || [];
  const stagesHtml = listItems(serviceStages, (s, i) => {
    const row = s as { stage?: string; title?: string; description?: string };
    const num = esc(row.stage || String(i + 1).padStart(2, '0'));
    return `<div class="sb-process-step" data-yd-block="service-stage">
      <div class="sb-process-num">${num}</div>
      <h4>${esc(row.title)}</h4>
      <p>${esc(row.description)}</p>
    </div>`;
  });

  const knowledgeTopics =
    (home.knowledgeTopics as Array<{ title?: string; hook?: string }>) || [];
  const knowledgeHtml = listItems(knowledgeTopics.slice(0, 6), (k) => {
    const row = k as { title?: string; hook?: string };
    return `<article class="sb-knowledge-card" data-yd-block="knowledge-topic">
      <h4>${esc(row.title)}</h4>
      ${row.hook ? `<p>${esc(row.hook)}</p>` : ''}
      <a class="sb-prod-link" href="/tenant/contact">Discuss your specs →</a>
    </article>`;
  });

  const applications = (home.applications as Array<{ title?: string; description?: string }>) || [];
  const appHtml = listItems(applications, (a) => {
    const row = a as { title?: string; description?: string };
    return `<div class="sb-app"><h4>${esc(row.title)}</h4><p>${esc(row.description)}</p></div>`;
  });

  const productItems =
    (products.productItems as Array<{ name?: string; summary?: string; image?: string }>) || [];
  const prodHtml = listItems(productItems.slice(0, 6), (p) => {
    const row = p as { name?: string; summary?: string; image?: string };
    const img = row.image
      ? `<img src="${esc(row.image)}" alt="${esc(row.name)}" class="sb-prod-img"/>`
      : '<div class="sb-prod-ph">Product Image</div>';
    return `<div class="sb-prod">${img}<h4>${esc(row.name)}</h4><p>${esc(row.summary)}</p><a class="sb-prod-link" href="/tenant/contact">Inquiry →</a></div>`;
  });

  const certList = presetCertsForTemplate(templateId);
  const certHtml = certList.map((c) => `<div class="sb-cert-item">${esc(c)}</div>`).join('');

  const mission = esc(about.mission || '');
  const vision = esc(about.vision || '');
  const capacity = esc(about.capacitySummary || '');
  const aboutSide = [
    mission ? `<div class="sb-mv-card"><div class="sb-mv-label">Mission</div><p class="sb-mv-text">${mission}</p></div>` : '',
    vision ? `<div class="sb-mv-card"><div class="sb-mv-label">Vision</div><p class="sb-mv-text">${vision}</p></div>` : '',
    capacity ? `<div class="sb-mv-card"><div class="sb-mv-label">Capacity</div><p class="sb-mv-text">${capacity}</p></div>` : '',
  ].filter(Boolean).join('');

  const shell = buildSiteChrome(buildShellContext(data, theme, 'home'));
  const ctx = buildShellContext(data, theme, 'home');
  const heroBlock = buildHero(theme, {
    heroTitle,
    heroDesc,
    heroImage,
    ctaPrimary,
    ctaSecondary,
    trustHtml,
    year: esc(home.establishedYear || ''),
    primaryPromise: primaryPromise || undefined,
  });

  const promiseBand = primaryPromise
    ? `<section class="sb-promise-band sb-container" data-yd-block="primary-promise">
        <p class="sb-promise-label">Our promise</p>
        <p class="sb-promise-text">${primaryPromise}</p>
      </section>`
    : '';

  const html = `
<section class="sb-page" data-gjs-type="wrapper">
  ${shell.top}
  ${shell.header}
  ${heroBlock}
  ${promiseBand}
  <div class="sb-container sb-cert-strip">${certHtml}</div>
  ${statsHtml ? `<section class="sb-stats sb-container sb-stats--flat" data-yd-block="stats">${statsHtml}</section>` : ''}
  ${stagesHtml ? `<section class="sb-section sb-section--alt sb-container" data-yd-block="service-stages">
    ${sectionHead('Project path', 'Can you take my order at this stage?', 'Structured gates from RFQ through volume — not a factory tour.')}
    <div class="sb-process">${stagesHtml}</div>
  </section>` : ''}
  ${solHtml ? `<section class="sb-section sb-container">
    ${sectionHead('Buyer jobs', 'Solutions by task', 'Mapped to what visitors need to finish — not your warehouse aisles.')}
    <div class="sb-grid-3">${solHtml}</div>
  </section>` : ''}
  ${advHtml ? `<section class="sb-section sb-section--alt sb-container">
    ${sectionHead('Evidence', sectionTitle, sectionDesc)}
    <div class="sb-grid-2">${advHtml}</div>
  </section>` : ''}
  ${productItems.length ? `<section id="products" class="sb-section sb-container">
    ${sectionHead('Catalog', productsTitle, productsDesc)}
    <div class="sb-grid-3">${prodHtml}</div>
  </section>` : ''}
  ${knowledgeHtml ? `<section class="sb-section sb-section--alt sb-container" data-yd-block="knowledge-hub">
    ${sectionHead('Technical content', 'Answer search intent before the RFQ', 'Guides that prove you understand the buyer\'s spec — then route to inquiry.')}
    <div class="sb-grid-3">${knowledgeHtml}</div>
  </section>` : ''}
  ${catHtml ? `<section class="sb-section sb-container">
    ${sectionHead('Catalog', 'Product Categories', 'Browse by material and application.')}
    <div class="sb-grid-3">${catHtml}</div>
  </section>` : ''}
  ${appHtml ? `<section class="sb-section sb-section--alt sb-container">
    ${sectionHead('Use Cases', 'Typical applications', 'Where our materials and processes fit.')}
    <div class="sb-grid-4">${appHtml}</div>
  </section>` : ''}
  <section id="about" class="sb-section sb-container">
    ${sectionHead('Company', 'About Us', 'Manufacturing partner for qualified B2B programs.')}
    <div class="sb-about-grid">
      <p class="sb-about">${aboutText}</p>
      ${aboutSide ? `<div class="sb-about-side">${aboutSide}</div>` : ''}
    </div>
  </section>
  <section class="sb-cta-band" data-yd-block="cta-band">
    <div class="sb-container">
      <h2>Ready to start?</h2>
      <p>${inquiryHook}</p>
      <a class="sb-cta" href="/tenant/contact" style="background:${theme.accent}">${ctaPrimary}</a>
    </div>
  </section>
  <section id="contact" class="sb-section sb-container sb-contact">
    ${sectionHead('联系', '联系我们', '请填写数量、规格与目的港，我们将在 24 小时内回复。')}
    <div class="sb-contact-grid">
      <div class="sb-contact-info">
        <h3>工厂联系方式</h3>
        <p>Tel: ${ctx.phone}</p>
        <p>Email: ${ctx.email}</p>
        <p>Address: ${ctx.address}</p>
        <a class="sb-wa-btn" href="https://wa.me/${whatsapp}" target="_blank" rel="noopener">WhatsApp Chat</a>
      </div>
      ${buildInquiryForm(theme.accent)}
    </div>
  </section>
  ${shell.footer}
</section>`;

  return { html: html.trim(), css: buildEnterpriseSiteCss(theme) };
}

export function buildInquiryForm(accent: string): string {
  return `<form class="sb-inquiry-form" data-yd-block="inquiry">
        <h3 class="sb-inquiry-title">Send Inquiry</h3>
        <p class="sb-inquiry-sub">MOQ, destination port & delivery time welcome.</p>
        <input type="text" name="name" placeholder="Your Name *" class="sb-inquiry-input"/>
        <input type="email" name="email" placeholder="Email" class="sb-inquiry-input"/>
        <input type="text" name="phone" placeholder="Phone / WhatsApp *" class="sb-inquiry-input"/>
        <input type="text" name="product" placeholder="Product / Specs" class="sb-inquiry-input"/>
        <textarea name="message" placeholder="Quantity, destination port, required certs..." rows="4" class="sb-inquiry-input"></textarea>
        <button type="submit" class="sb-inquiry-submit" style="background:${accent}">Submit Inquiry</button>
      </form>`;
}

export function pickFirstProductImage(products: Record<string, unknown>): string {
  const items = products.productItems as Array<{ image?: string }> | undefined;
  if (!Array.isArray(items)) return '';
  const hit = items.find((i) => i?.image);
  return hit?.image ? String(hit.image) : '';
}

function pickTheme(raw?: SiteContentSnapshot['theme']): Partial<ThemePack> {
  if (!raw) return {};
  const out: Partial<ThemePack> = {};
  if (raw.headerBg) out.headerBg = raw.headerBg;
  if (raw.heroBg) out.heroBg = raw.heroBg;
  if (raw.footerBg) out.footerBg = raw.footerBg;
  return out;
}
