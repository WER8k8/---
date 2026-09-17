/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * XSS 防护 composable — 基于 DOMPurify
 * 对 v-html 渲染内容进行安全过滤
 */
import DOMPurify from 'dompurify';

export function useSanitize() {
  function sanitizeHtml(html: string | null | undefined): string {
    if (!html) return '';
    if (typeof window !== 'undefined') {
      return DOMPurify.sanitize(String(html), {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 'a', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img', 'div', 'section', 'blockquote', 'pre', 'code', 'hr'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'width', 'height', 'class', 'id', 'style', 'title'],
        ALLOW_DATA_ATTR: false,
        FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
      });
    }
    // SSR fallback
    return String(html)
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, '')
      .replace(/\bon\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]*)/gi, '');
  }

  return { sanitizeHtml };
}
