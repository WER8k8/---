/**
 * HTML 内容净化 composable — 基于 DOMPurify
 * 用于 v-html 场景的 XSS 防护
 */
import DOMPurify from 'dompurify';

const PURIFY_CONFIG: DOMPurify.Config = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 'a', 'span',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'video', 'source', 'audio',
    'blockquote', 'pre', 'code', 'div', 'section', 'article',
    'figure', 'figcaption', 'hr', 'sub', 'sup', 'mark',
  ],
  ALLOWED_ATTR: [
    'href', 'target', 'rel', 'src', 'alt', 'width', 'height',
    'class', 'id', 'style', 'title', 'colspan', 'rowspan',
    'controls', 'autoplay', 'loop', 'muted', 'poster',
    'loading', 'decoding',
  ],
  ALLOW_DATA_ATTR: false,
  ADD_ATTR: [['target', '_blank']],
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'textarea', 'select'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
};

/**
 * 净化 HTML 内容用于 v-html 渲染
 * 基于 DOMPurify，保留基本格式标签，移除所有 XSS 向量
 */
export function useSanitize() {
  function sanitizeHtml(html: string | null | undefined): string {
    if (!html) return '';
    if (typeof window !== 'undefined') {
      return DOMPurify.sanitize(html, PURIFY_CONFIG);
    }
    // SSR fallback — 简单过滤
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
      .replace(/\s+on\w+\s*=\s*(['"]).*?\1/gi, '')
      .replace(/\s+on\w+\s*=\s*[^\s>]+/gi, '');
  }

  return { sanitizeHtml };
}
