import type { SiteContentSnapshot } from './types';

/** 从 GrapesJS 导出的 HTML 反向提取关键文案（保存时同步结构化字段） */
export function parseVisualHtmlToSnapshot(html: string): Partial<SiteContentSnapshot> {
  if (!html?.trim() || typeof DOMParser === 'undefined') return {};

  const doc = new DOMParser().parseFromString(html, 'text/html');
  const out: Partial<SiteContentSnapshot> = {
    brand: {},
    pages: { home: {}, contact: {} },
  };
  const home = out.pages!.home as Record<string, unknown>;

  const brandName = doc.querySelector('.sb-logo')?.textContent?.trim();
  const tagline = doc.querySelector('.sb-tag')?.textContent?.trim();
  if (brandName) out.brand!.name = brandName;
  if (tagline) out.brand!.tagline = tagline;

  const promiseText = doc.querySelector('.sb-promise-text')?.textContent?.trim();
  if (promiseText) {
    home.primary_promise = promiseText;
    out.brand!.tagline = promiseText;
  }

  const kicker = doc.querySelector('.sb-kicker')?.textContent?.trim();
  if (kicker && !promiseText) {
    home.primary_promise = kicker;
  }

  const heroTitle = doc.querySelector('.sb-hero-title')?.textContent?.trim();
  const heroDesc = doc.querySelector('.sb-hero-desc')?.textContent?.trim();
  if (heroTitle) home.title = heroTitle;
  if (heroDesc) home.description = heroDesc;

  const sinceText = doc.querySelector('.sb-topbar-since')?.textContent?.trim() || '';
  const yearMatch = sinceText.match(/(?:Established|Est\.?|自)\s*(\d{4})/i);
  if (yearMatch?.[1]) home.establishedYear = yearMatch[1];

  const ctaBand = doc.querySelector('.sb-cta-band p')?.textContent?.trim();
  if (ctaBand) home.inquiryHook = ctaBand;

  const stageNodes = doc.querySelectorAll('[data-yd-block="service-stage"], .sb-process-step');
  if (stageNodes.length) {
    home.serviceStages = Array.from(stageNodes).map((node, i) => {
      const num = node.querySelector('.sb-process-num')?.textContent?.trim();
      const title = node.querySelector('h4')?.textContent?.trim();
      const desc = node.querySelector('p')?.textContent?.trim();
      return {
        stage: num || String(i + 1).padStart(2, '0'),
        title: title || '',
        description: desc || '',
      };
    }).filter((s) => s.title);
  }

  const knowledgeNodes = doc.querySelectorAll('[data-yd-block="knowledge-topic"], .sb-knowledge-card');
  if (knowledgeNodes.length) {
    home.knowledgeTopics = Array.from(knowledgeNodes).map((node) => {
      const title = node.querySelector('h4')?.textContent?.trim();
      const hook = node.querySelector('p')?.textContent?.trim();
      return { title: title || '', hook: hook || '' };
    }).filter((k) => k.title);
  }

  const contactParas = doc.querySelectorAll('.sb-contact-info p');
  contactParas.forEach((p) => {
    const text = p.textContent?.trim() || '';
    if (text.startsWith('电话') || text.startsWith('Phone')) {
      (out.pages!.contact as Record<string, string>).phone = text.replace(/^[^:：]+[:：]\s*/, '');
    } else if (text.startsWith('邮箱') || text.startsWith('Email')) {
      (out.pages!.contact as Record<string, string>).email = text.replace(/^[^:：]+[:：]\s*/, '');
    } else if (text.startsWith('地址') || text.startsWith('Address')) {
      (out.pages!.contact as Record<string, string>).address = text.replace(/^[^:：]+[:：]\s*/, '');
    }
  });

  const footerText = doc.querySelector('.sb-footer')?.textContent?.trim();
  if (footerText) out.footer = { text: footerText };

  return out;
}

export function mergeParsedIntoSnapshot(
  snapshot: SiteContentSnapshot,
  parsed: Partial<SiteContentSnapshot>,
): SiteContentSnapshot {
  const parsedHome = (parsed.pages?.home || {}) as Record<string, unknown>;
  const home = { ...snapshot.pages?.home, ...parsedHome };
  return {
    ...snapshot,
    brand: { ...snapshot.brand, ...parsed.brand },
    footer: { ...snapshot.footer, ...parsed.footer },
    pages: {
      ...snapshot.pages,
      home,
      contact: { ...snapshot.pages?.contact, ...parsed.pages?.contact },
    },
  };
}
