/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineEventHandler, setHeader } from 'h3';
import { SITE_CONFIG } from '~/config/site';

/**
 * 动态 Sitemap — 包含所有产品页 + 图片扩展 + 视频扩展
 * 
 * Google 支持的 sitemap 扩展：
 * - xmlns:image 用于图片搜索收录
 * - xmlns:video 用于视频搜索收录
 */

interface Product {
  slug: string;
  name: string;
  description?: string;
  image_url?: string;
  updated_at?: string;
  images?: Array<{ image_url: string; alt_text?: string }>;
  video_url?: string;
  video_title?: string;
  video_description?: string;
  video_thumbnail?: string;
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const apiBase = (config.public as any)?.apiBase || 'http://127.0.0.1:8001';
  const baseUrl = (config.public as any)?.siteUrl || SITE_CONFIG.url;

  // 静态页面
  const pages = [
    { path: '/', priority: '1.0', changefreq: 'daily' },
    { path: '/products', priority: '0.9', changefreq: 'weekly' },
    { path: '/cases', priority: '0.8', changefreq: 'weekly' },
    { path: '/about', priority: '0.7', changefreq: 'monthly' },
    { path: '/news', priority: '0.8', changefreq: 'daily' },
    { path: '/contact', priority: '0.6', changefreq: 'monthly' },
    { path: '/privacy', priority: '0.5', changefreq: 'yearly' },
    { path: '/terms', priority: '0.5', changefreq: 'yearly' },
  ];

  // 动态获取产品列表
  let products: Product[] = [];
  try {
    const res = await fetch(`${apiBase}/api/v1/products/sitemap-feed?limit=500`, {
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      products = Array.isArray(data) ? data : (data?.data || data?.items || []);
    }
  } catch {
    // 产品获取失败时 sitemap 仍包含静态页面
  }

  const today = new Date().toISOString().split('T')[0];

  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n';
  xml += '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"\n';
  xml += '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n';

  // 静态页面
  pages.forEach((page) => {
    xml += '  <url>\n';
    xml += `    <loc>${escapeXml(baseUrl + page.path)}</loc>\n`;
    xml += `    <lastmod>${today}</lastmod>\n`;
    xml += `    <changefreq>${page.changefreq}</changefreq>\n`;
    xml += `    <priority>${page.priority}</priority>\n`;
    xml += '  </url>\n';
  });

  // 产品详情页（含图片扩展 + 视频扩展）
  products.forEach((product) => {
    if (!product.slug) return;
    const productUrl = `${baseUrl}/products/${product.slug}`;
    const lastmod = product.updated_at
      ? new Date(product.updated_at).toISOString().split('T')[0]
      : today;

    xml += '  <url>\n';
    xml += `    <loc>${escapeXml(productUrl)}</loc>\n`;
    xml += `    <lastmod>${lastmod}</lastmod>\n`;
    xml += '    <changefreq>weekly</changefreq>\n';
    xml += '    <priority>0.8</priority>\n';

    // 图片扩展 — 产品主图
    if (product.image_url) {
      xml += '    <image:image>\n';
      xml += `      <image:loc>${escapeXml(product.image_url)}</image:loc>\n`;
      xml += `      <image:title>${escapeXml(product.name)}</image:title>\n`;
      if (product.description) {
        xml += `      <image:caption>${escapeXml(product.description.substring(0, 200))}</image:caption>\n`;
      }
      xml += '    </image:image>\n';
    }

    // 图片扩展 — 产品附加图片
    if (product.images && Array.isArray(product.images)) {
      product.images.forEach((img) => {
        if (!img.image_url) return;
        xml += '    <image:image>\n';
        xml += `      <image:loc>${escapeXml(img.image_url)}</image:loc>\n`;
        xml += `      <image:title>${escapeXml(img.alt_text || product.name)}</image:title>\n`;
        xml += '    </image:image>\n';
      });
    }

    // 视频扩展 — 产品关联视频
    if (product.video_url) {
      xml += '    <video:video>\n';
      xml += `      <video:thumbnail_loc>${escapeXml(product.video_thumbnail || product.image_url || '')}</video:thumbnail_loc>\n`;
      xml += `      <video:title>${escapeXml(product.video_title || product.name)}</video:title>\n`;
      xml += `      <video:description>${escapeXml(product.video_description || product.description || product.name)}</video:description>\n`;
      xml += `      <video:content_loc>${escapeXml(product.video_url)}</video:content_loc>\n`;
      xml += '    </video:video>\n';
    }

    xml += '  </url>\n';
  });

  xml += '</urlset>';

  setHeader(event, 'Content-Type', 'application/xml; charset=utf-8');
  setHeader(event, 'Cache-Control', 'public, max-age=3600, s-maxage=7200');
  return xml;
});
