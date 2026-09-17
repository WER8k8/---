/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { buildEnterpriseSiteCss } from './enterpriseSiteStyles';
import {
  buildInquiryForm,
  buildPageHtml,
  buildShellContext,
  listItems,
  prepareSiteSnapshot,
  sectionHead,
  THEMES,
  esc,
  pickTheme,
  type ThemePack,
} from './buildPageHtml';
import { buildSiteChrome } from './buildPageShell';
import { TEMPLATE_LAYOUT } from './industryPresets';
import type { SiteBuilderTemplateId, SiteContentSnapshot, VisualEditorPayload } from './types';

export type VisualSubPageId = 'products' | 'about' | 'contact';

export function buildVisualSubPage(
  pageId: VisualSubPageId,
  templateId: SiteBuilderTemplateId,
  rawData: SiteContentSnapshot,
): { html: string; css: string } {
  const data = prepareSiteSnapshot(templateId, rawData);
  const theme: ThemePack = { ...THEMES[templateId], layout: TEMPLATE_LAYOUT[templateId], ...pickTheme(data.theme) };
  const shell = buildSiteChrome(buildShellContext(data, theme, pageId));
  const home = (data.pages?.home || {}) as Record<string, unknown>;
  const products = (data.pages?.products || {}) as Record<string, unknown>;
  const about = (data.pages?.about || {}) as Record<string, unknown>;
  const contact = (data.pages?.contact || {}) as Record<string, unknown>;

  let main = '';

  if (pageId === 'products') {
    const productItems =
      (products.productItems as Array<{ name?: string; summary?: string; image?: string }>) || [];
    const prodHtml = listItems(productItems, (p) => {
      const row = p as { name?: string; summary?: string; image?: string };
      const img = row.image
        ? `<img src="${esc(row.image)}" alt="${esc(row.name)}" class="sb-prod-img"/>`
        : '<div class="sb-prod-ph">Product Image</div>';
      return `<div class="sb-prod">${img}<h4>${esc(row.name)}</h4><p>${esc(row.summary)}</p><a class="sb-prod-link" href="/tenant/contact">Inquiry →</a></div>`;
    });
    const categories = (home.categories as Array<{ name?: string; description?: string } | string>) || [];
    const catHtml = listItems(categories, (c) => {
      if (typeof c === 'string') return `<div class="sb-card"><h4>${esc(c)}</h4></div>`;
      const row = c as { name?: string; description?: string };
      return `<div class="sb-card"><h4>${esc(row.name)}</h4><p>${esc(row.description)}</p></div>`;
    });
    main = `<section class="sb-section sb-container">
      ${sectionHead('Catalog', esc(products.title || 'Products'), esc(products.description || 'Export product lines for wholesale and projects.'))}
      <div class="sb-grid-3">${prodHtml || '<p class="sb-about">Products coming soon.</p>'}</div>
    </section>
    ${catHtml ? `<section class="sb-section sb-section--alt sb-container">
      ${sectionHead('Categories', 'Product Classification', '')}
      <div class="sb-grid-3">${catHtml}</div>
    </section>` : ''}`;
  }

  if (pageId === 'about') {
    const mission = esc(about.mission || '');
    const vision = esc(about.vision || '');
    const capacity = esc(about.capacitySummary || '');
    main = `<section class="sb-section sb-container">
      ${sectionHead('Company', 'About Us', 'Manufacturing partner for global distributors & EPC projects.')}
      <div class="sb-about-grid">
        <p class="sb-about">${esc(about.aboutText || '')}</p>
        <div class="sb-about-side">
          ${mission ? `<div class="sb-mv-card"><div class="sb-mv-label">Mission</div><p class="sb-mv-text">${mission}</p></div>` : ''}
          ${vision ? `<div class="sb-mv-card"><div class="sb-mv-label">Vision</div><p class="sb-mv-text">${vision}</p></div>` : ''}
          ${capacity ? `<div class="sb-mv-card"><div class="sb-mv-label">Capacity</div><p class="sb-mv-text">${capacity}</p></div>` : ''}
        </div>
      </div>
    </section>`;
  }

  if (pageId === 'contact') {
    const ctx = buildShellContext(data, theme, 'contact');
    const whatsapp = esc(String(contact.whatsapp || '8613800000000').replace(/[^0-9]/g, ''));
    main = `<section class="sb-section sb-container sb-contact">
      ${sectionHead('Contact', 'Get in Touch', 'Share quantity, specs & destination port — we reply within 24h.')}
      <div class="sb-contact-grid">
        <div class="sb-contact-info">
          <h3>Factory Contact</h3>
          <p>Tel: ${ctx.phone}</p>
          <p>Email: ${ctx.email}</p>
          <p>Address: ${ctx.address}</p>
          <a class="sb-wa-btn" href="https://wa.me/${whatsapp}" target="_blank" rel="noopener">WhatsApp Chat</a>
        </div>
        ${buildInquiryForm(theme.accent)}
      </div>
    </section>`;
  }

  const html = `<section class="sb-page" data-gjs-type="wrapper">
  ${shell.top}
  ${shell.header}
  ${main}
  ${shell.footer}
</section>`;

  const css = buildEnterpriseSiteCss(theme);
  return { html: html.trim(), css };
}

export function buildVisualSiteBundle(
  templateId: SiteBuilderTemplateId,
  data: SiteContentSnapshot,
): Pick<VisualEditorPayload, 'html' | 'css' | 'subPages' | 'multiPage'> {
  const home = buildPageHtml(templateId, data);
  const subPages = {
    products: buildVisualSubPage('products', templateId, data).html,
    about: buildVisualSubPage('about', templateId, data).html,
    contact: buildVisualSubPage('contact', templateId, data).html,
  };
  return {
    html: home.html,
    css: home.css,
    subPages,
    multiPage: true,
  };
}
