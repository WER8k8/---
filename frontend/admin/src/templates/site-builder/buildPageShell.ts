/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 企业站公共壳（顶栏 / 导航 / 页脚）与多页路由链接 */

import type { SiteBuilderTemplateId } from './types';
import { TEMPLATE_LAYOUT } from './industryPresets';

export type VisualSitePage = 'home' | 'products' | 'about' | 'contact';

export function tenantNavHref(page: VisualSitePage): string {
  if (page === 'home') return '/tenant';
  return `/tenant/${page}`;
}

export interface ShellContext {
  brandName: string;
  tagline: string;
  phone: string;
  email: string;
  address: string;
  footerText: string;
  year: string;
  ctaPrimary: string;
  theme: { headerBg: string; footerBg: string; accent: string };
  activePage: VisualSitePage;
}

export function buildSiteChrome(ctx: ShellContext): { top: string; header: string; footer: string } {
  const nav = (page: VisualSitePage, label: string) => {
    const href = tenantNavHref(page);
    const active = ctx.activePage === page ? ' sb-nav-link--active' : '';
    return `<a href="${href}" class="sb-nav-link${active}">${label}</a>`;
  };

  const top = `<div class="sb-topbar">
    <div class="sb-container sb-topbar-inner">
      <span class="sb-topbar-since">${ctx.year ? `成立于 ${ctx.year} 年` : '面向全球出口'}</span>
      <div class="sb-topbar-contacts">
        <a href="tel:${ctx.phone.replace(/\s/g, '')}">电话：${ctx.phone}</a>
        <a href="mailto:${ctx.email}">邮箱：${ctx.email}</a>
      </div>
    </div>
  </div>`;

  const header = `<header class="sb-header" style="background:${ctx.theme.headerBg}">
    <div class="sb-container sb-header-inner">
      <div class="sb-brand">
        <a href="${tenantNavHref('home')}" class="sb-logo sb-logo-link">${ctx.brandName}</a>
        <div class="sb-tag">${ctx.tagline}</div>
      </div>
      <nav class="sb-nav">
        ${nav('home', '首页')}
        ${nav('products', '产品')}
        ${nav('about', '关于')}
        ${nav('contact', '联系')}
      </nav>
      <a class="sb-header-cta" href="${tenantNavHref('contact')}">${ctx.ctaPrimary}</a>
    </div>
  </header>`;

  const footer = `<footer class="sb-footer" style="background:${ctx.theme.footerBg}">
    <div class="sb-container">
      <div class="sb-footer-grid">
        <div class="sb-footer-brand">
          <div class="sb-logo">${ctx.brandName}</div>
          <p>${ctx.tagline}</p>
        </div>
        <div class="sb-footer-col">
          <h4>快速链接</h4>
          <a href="${tenantNavHref('home')}">首页</a>
          <a href="${tenantNavHref('products')}">产品中心</a>
          <a href="${tenantNavHref('about')}">关于我们</a>
          <a href="${tenantNavHref('contact')}">联系我们</a>
        </div>
        <div class="sb-footer-col">
          <h4>联系方式</h4>
          <p>${ctx.phone}</p>
          <p>${ctx.email}</p>
          <p>${ctx.address}</p>
        </div>
      </div>
      <div class="sb-footer-copy">${ctx.footerText}</div>
    </div>
  </footer>`;

  return { top, header, footer };
}

export function layoutLabel(templateId: SiteBuilderTemplateId): string {
  const layout = TEMPLATE_LAYOUT[templateId];
  if (layout === 'hero-banner') return '大图 Hero';
  if (layout === 'industrial') return '工业风';
  return '经典双栏';
}

export function layoutKind(templateId: SiteBuilderTemplateId) {
  return TEMPLATE_LAYOUT[templateId];
}
