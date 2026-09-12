/**
 * extractor.ts — NLP + 规则引擎信息提取
 *
 * 功能：
 * - 正则规则引擎：提取邮箱、电话（含国际区号）、URL
 * - 建材行业关键词库（20+ 中英文关键词）
 * - 表单字段分析（HTML form 提取字段名/值）
 * - 询盘段落检测（inquiry / contact / quote / message / order 等关键词）
 * - 语言检测（Unicode 字符范围）
 * - 结构化输出：字段 + 置信度 0-1 + 整体置信度
 */

export interface ExtractedEmail {
  email: string;
  confidence: number;
}

export interface ExtractedPhone {
  phone: string;
  formatted: string;
  confidence: number;
}

export interface ExtractedUrl {
  url: string;
  confidence: number;
}

export interface FormField {
  name: string;
  type: string;
  placeholder: string;
  required: boolean;
}

export interface InquiryParagraph {
  text: string;
  matchedKeywords: string[];
  relevance: number;
}

export interface InquiryInfo {
  emails: ExtractedEmail[];
  phones: ExtractedPhone[];
  urls: ExtractedUrl[];
  formFields: FormField[];
  inquiryParagraphs: InquiryParagraph[];
  detectedLanguage: string;
  languageConfidence: number;
  overallConfidence: number;
  contactSectionFound: boolean;
}

// ===== 建材行业关键词库（20+ 中英文） =====

export const BUILDING_MATERIALS_KEYWORDS: string[] = [
  // 英文关键词
  'cement', 'concrete', 'steel', 'tile', 'insulation', 'brick',
  'timber', 'lumber', 'plywood', 'granite', 'marble', 'ceramic',
  'pvc', 'uPVC', 'aluminum', 'aluminium', 'glass', 'fiberglass',
  'asphalt', 'roofing', 'flooring', 'plumbing', 'fitting', 'valve',
  'pipe', 'piping', 'sealant', 'adhesive', 'mortar', 'grout',
  'reinforcement', 'rebar', 'scaffolding', 'formwork', 'conduit',
  'HVAC', 'duct', 'ventilation', 'waterproof', 'waterproofing',
  'coating', 'paint', 'primer', 'varnish', 'lacquer',
  'hardware', 'fastener', 'screw', 'bolt', 'nut', 'washer',
  'anchor', 'bracket', 'hinge', 'lock', 'handle',
  'sanitary', 'faucet', 'basin', 'toilet', 'shower', 'bathtub',
  'lamp', 'lighting', 'fixture', 'socket', 'switch',
  'door', 'window', 'frame', 'shutter', 'fence', 'gate',
  // 中文关键词
  '水泥', '混凝土', '钢材', '瓷砖', '保温', '砖',
  '木材', '胶合板', '大理石', '陶瓷', '铝合金',
  '玻璃', '玻璃钢', '沥青', '屋顶', '地板', '管道',
  '密封胶', '粘合剂', '砂浆', '钢筋', '脚手架',
  '防水', '涂料', '油漆', '五金', '紧固件', '螺丝',
  '卫浴', '水龙头', '洗手盆', '马桶', '淋浴', '浴缸',
  '灯具', '照明', '开关', '插座', '门窗',
];

// ===== 询盘检测关键词 =====

export const INQUIRY_KEYWORDS: string[] = [
  'inquiry', 'enquiry', 'contact', 'quote', 'quotation', 'price',
  'order', 'purchase', 'buy', 'request', 'RFQ', 'estimate',
  'message', 'get a quote', 'send us', 'reach out', 'get in touch',
  '询盘', '询价', '联系', '报价', '订购', '购买',
  '发给我们', '获取报价', '联系我们',
];

// ===== 正则规则引擎 =====

/** 邮箱正则（覆盖绝大多数格式，含国际化域名） */
const EMAIL_REGEX = /\b[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}\b/g;

/** 电话正则（覆盖含国际区号的多种格式） */
const PHONE_REGEXES: RegExp[] = [
  // 国际格式 +86 138-0013-8000 / +1 (555) 123-4567 / +44 20 7946 0958
  /\+\d{1,3}[\s-]?(?:\d[\s-]?){6,14}\d/g,
  // 无 + 但有明确国际区号括号格式 (86) 138-0013-8000
  /\(\+\d{1,3}\)[\s-]?\d[\s-]?(?:\d[\s-]?){5,13}\d/g,
  // 国内格式（中国 1xx xxxx xxxx）
  /1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}/g,
  // 国内格式（美国/加拿大 xxx-xxx-xxxx）
  /\b\d{3}[\s-]\d{3}[\s-]\d{4}\b/g,
  // 国内格式（欧洲/通用 xxx xxxx xxxx）
  /\b\d{3,4}[\s-]?\d{3}[\s-]?\d{3,4}\b/g,
  // 带国家区号括号格式: +86 10 1234 5678 / +86-10-12345678
  /\+\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}/g,
  // 带扩展名格式: +1-555-123-4567 ext. 123
  /\+\d{1,3}[\s-]\d{1,4}[\s-]\d{1,4}[\s-]\d{1,4}(?:\s*(?:ext|x|ext\.)\s*\d+)?/gi,
];

/** URL 正则 */
const URL_REGEX = /\b(?:https?:\/\/|www\.)[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*(?:\/[^\s<>"']*)?/gi;

// ===== 工具函数 =====

/**
 * 对提取的原始 email 去重
 */
function deduplicate<T>(items: T[], keyFn: (item: T) => string): T[] {
  const seen = new Set<string>();
  return items.filter(item => {
    const key = keyFn(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * 格式化电话号码为 E.164（仅当包含国家区号时）
 */
function formatPhone(raw: string): string {
  const digits = raw.replace(/[^\d+]/g, '');
  if (digits.startsWith('+')) return digits;
  if (digits.startsWith('86') && digits.length >= 11) return '+' + digits;
  if (digits.length >= 10) return '+' + digits;
  return raw.trim();
}

/**
 * 计算电话置信度
 */
function phoneConfidence(raw: string): number {
  const digits = raw.replace(/\D/g, '');
  if (digits.length >= 10 && digits.length <= 15) return 0.9;
  if (digits.length >= 7 && digits.length <= 16) return 0.7;
  return 0.4;
}

/**
 * 计算 URL 置信度
 */
function urlConfidence(url: string): number {
  if (/^https?:\/\//i.test(url)) return 0.95;
  if (/^www\./i.test(url)) return 0.85;
  return 0.5;
}

// ===== 提取函数 =====

/**
 * 从文本中提取所有邮箱地址
 */
export function extractEmails(html: string): ExtractedEmail[] {
  // 先去掉 HTML 标签，在纯文本中搜索
  const text = html.replace(/<[^>]+>/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  const matches = new Map<string, number>();

  let match: RegExpExecArray | null;
  const regex = new RegExp(EMAIL_REGEX.source, 'gi');
  while ((match = regex.exec(text)) !== null) {
    const email = match[0].toLowerCase().trim();
    // 过滤明显无效的邮件
    if (email.endsWith('.') || email.includes('..')) continue;
    if (/\.(png|jpg|jpeg|gif|css|js|ico|svg)$/i.test(email)) continue;
    matches.set(email, (matches.get(email) || 0) + 1);
  }

  // 也从 mailto: 链接中提取
  const mailtoRegex = /href=["']mailto:([^"']+)["']/gi;
  while ((match = mailtoRegex.exec(html)) !== null) {
    const email = match[1].toLowerCase().trim().split('?')[0]; // 去掉 ?subject= 等
    if (/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) {
      matches.set(email, (matches.get(email) || 0) + 2);
    }
  }

  return Array.from(matches.entries()).map(([email, count]) => ({
    email,
    confidence: Math.min(0.5 + count * 0.15, 0.98),
  }));
}

/**
 * 从文本中提取所有电话号码
 */
export function extractPhones(html: string): ExtractedPhone[] {
  const text = html.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ');
  const seen = new Set<string>();
  const phones: ExtractedPhone[] = [];

  for (const regex of PHONE_REGEXES) {
    const re = new RegExp(regex.source, 'g');
    let match: RegExpExecArray | null;
    while ((match = re.exec(text)) !== null) {
      const raw = match[0].trim();
      // 跳过明显不是电话号码的匹配
      const digits = raw.replace(/\D/g, '');
      if (digits.length < 6 || digits.length > 16) continue;
      // 跳过纯年份或数字
      if (/^\d{4}$/.test(raw.trim())) continue;
      if (digits.length === 6 || digits.length === 7) {
        // 只保留含分隔符的 6-7 位数字（可能是日期或邮编）
        if (!/[-.\s]/.test(raw)) continue;
      }

      const normalized = raw.replace(/\s+/g, ' ').trim();
      if (seen.has(normalized)) continue;
      seen.add(normalized);

      phones.push({
        phone: normalized,
        formatted: formatPhone(normalized),
        confidence: phoneConfidence(normalized),
      });
    }
  }

  return phones;
}

/**
 * 从文本中提取所有 URL
 */
export function extractUrls(html: string): ExtractedUrl[] {
  const text = html.replace(/<[^>]+>/g, ' ');
  const matches = new Map<string, number>();

  // 从 href 提取
  const hrefRegex = /href=["']((?:https?:\/\/)?[^"']+)["']/gi;
  let match: RegExpExecArray | null;
  while ((match = hrefRegex.exec(html)) !== null) {
    let url = match[1].trim();
    if (/^(?:https?:\/\/|www\.)/i.test(url) && !url.startsWith('#')) {
      if (!/^(?:https?:\/\/)/i.test(url)) url = 'https://' + url;
      matches.set(url, (matches.get(url) || 0) + 1);
    }
  }

  // 从纯文本提取
  const regex = new RegExp(URL_REGEX.source, 'gi');
  while ((match = regex.exec(text)) !== null) {
    let url = match[0].trim();
    if (url.endsWith(')') && !url.startsWith('(')) url = url.slice(0, -1);
    if (url.endsWith('.')) url = url.slice(0, -1);
    if (!/^(?:https?:\/\/)/i.test(url)) url = 'https://' + url;
    matches.set(url, (matches.get(url) || 0) + 1);
  }

  return Array.from(matches.entries()).map(([url, count]) => ({
    url,
    confidence: Math.min(urlConfidence(url) + count * 0.05, 0.98),
  }));
}

/**
 * 从 HTML 中提取表单字段
 */
export function extractFormFields(html: string): FormField[] {
  const fields: FormField[] = [];
  const formRegex = /<form[\s\S]*?<\/form>/gi;
  let formMatch: RegExpExecArray | null;

  while ((formMatch = formRegex.exec(html)) !== null) {
    const formHtml = formMatch[0];

    // input 元素
    const inputRegex = /<input[^>]*>/gi;
    let inputMatch: RegExpExecArray | null;
    while ((inputMatch = inputRegex.exec(formHtml)) !== null) {
      const el = inputMatch[0];
      const name = (el.match(/name\s*=\s*["']([^"']*)["']/i) || [])[1] || '';
      const type = (el.match(/type\s*=\s*["']([^"']*)["']/i) || [])[1] || 'text';
      const placeholder = (el.match(/placeholder\s*=\s*["']([^"']*)["']/i) || [])[1] || '';
      const required = /required/i.test(el);
      if (type === 'hidden') continue;
      if (name || placeholder) {
        fields.push({ name, type, placeholder, required });
      }
    }

    // textarea 元素
    const textareaRegex = /<textarea[^>]*>/gi;
    while ((textareaMatch = textareaRegex.exec(formHtml)) !== null) {
      const el = textareaMatch[0];
      const name = (el.match(/name\s*=\s*["']([^"']*)["']/i) || [])[1] || '';
      const placeholder = (el.match(/placeholder\s*=\s*["']([^"']*)["']/i) || [])[1] || '';
      const required = /required/i.test(el);
      if (name || placeholder) {
        fields.push({ name, type: 'textarea', placeholder, required });
      }
    }

    // select 元素
    const selectRegex = /<select[^>]*>/gi;
    while ((selectMatch = selectRegex.exec(formHtml)) !== null) {
      const el = selectMatch[0];
      const name = (el.match(/name\s*=\s*["']([^"']*)["']/i) || [])[1] || '';
      const required = /required/i.test(el);
      if (name) {
        fields.push({ name, type: 'select', placeholder: '', required });
      }
    }
  }

  return fields;
}

/**
 * 查找包含询盘关键词的段落
 * 将 HTML 切分为段落（p, div, section, li, span 等标签内的文本），检测每个段落中的询盘关键词
 */
export function findInquirySection(html: string): InquiryParagraph[] {
  const paragraphs: InquiryParagraph[] = [];

  // 按常见块级标签切分
  const blockTags = ['p', 'div', 'section', 'li', 'article', 'span', 'td', 'th', 'label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
  const text = html.replace(/<br\s*\/?>/gi, '\n');

  for (const tag of blockTags) {
    const regex = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'gi');
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      const innerText = match[1].replace(/<[^>]+>/g, '').trim();
      if (innerText.length < 5 || innerText.length > 2000) continue;

      const matchedKeywords: string[] = [];
      for (const kw of INQUIRY_KEYWORDS) {
        const kwRegex = new RegExp('\\b' + kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'gi');
        if (kwRegex.test(innerText)) {
          matchedKeywords.push(kw);
        }
      }

      // 也检测建材关键词
      const buildingMatches: string[] = [];
      for (const kw of BUILDING_MATERIALS_KEYWORDS) {
        const kwRegex = new RegExp('\\b' + kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'gi');
        if (kwRegex.test(innerText)) {
          buildingMatches.push(kw);
        }
      }

      if (matchedKeywords.length > 0) {
        const relevance = Math.min(matchedKeywords.length * 0.2 + buildingMatches.length * 0.1, 0.98);
        paragraphs.push({
          text: innerText.substring(0, 500),
          matchedKeywords: [...matchedKeywords, ...buildingMatches],
          relevance: Math.round(relevance * 100) / 100,
        });
      }
    }
  }

  // 按相关性降序排列
  paragraphs.sort((a, b) => b.relevance - a.relevance);
  return paragraphs;
}

/**
 * 基于 Unicode 字符范围快速判断语言
 */
export function detectLanguage(html: string): { language: string; confidence: number } {
  const text = html.replace(/<[^>]+>/g, '').substring(0, 3000);

  let cjkCount = 0;
  let cyrillicCount = 0;
  let arabicCount = 0;
  let koreanCount = 0;
  let japaneseKanaCount = 0;
  let latinCount = 0;
  let totalChars = 0;

  for (const ch of text) {
    const code = ch.charCodeAt(0);
    // 只统计字母类字符
    if (ch.match(/[a-zA-Z\u00C0-\u024F]/)) { latinCount++; totalChars++; }
    else if (code >= 0x4E00 && code <= 0x9FFF) { cjkCount++; totalChars++; }
    else if (code >= 0x3400 && code <= 0x4DBF) { cjkCount++; totalChars++; }
    else if (code >= 0x0400 && code <= 0x04FF) { cyrillicCount++; totalChars++; }
    else if (code >= 0x0600 && code <= 0x06FF) { arabicCount++; totalChars++; }
    else if (code >= 0x0750 && code <= 0x077F) { arabicCount++; totalChars++; }
    else if (code >= 0xAC00 && code <= 0xD7AF) { koreanCount++; totalChars++; }
    else if (code >= 0x3040 && code <= 0x309F) { japaneseKanaCount++; totalChars++; }
    else if (code >= 0x30A0 && code <= 0x30FF) { japaneseKanaCount++; totalChars++; }
  }

  if (totalChars === 0) return { language: 'unknown', confidence: 0 };

  const latinRatio = latinCount / totalChars;
  const cjkRatio = cjkCount / totalChars;
  const cyrillicRatio = cyrillicCount / totalChars;
  const arabicRatio = arabicCount / totalChars;
  const koreanRatio = koreanCount / totalChars;
  const jpRatio = japaneseKanaCount / totalChars;

  if (arabicRatio > 0.3) return { language: 'ar', confidence: Math.min(arabicRatio + 0.2, 0.95) };
  if (cyrillicRatio > 0.3) return { language: 'ru', confidence: Math.min(cyrillicRatio + 0.2, 0.95) };
  if (koreanRatio > 0.15) return { language: 'ko', confidence: Math.min(koreanRatio + 0.3, 0.95) };
  if (jpRatio > 0.08) return { language: 'ja', confidence: Math.min(jpRatio + 0.4, 0.95) };
  if (cjkRatio > 0.2) {
    if (jpRatio > 0.03) return { language: 'ja', confidence: Math.min(cjkRatio + 0.2, 0.9) };
    return { language: 'zh', confidence: Math.min(cjkRatio + 0.3, 0.95) };
  }
  if (latinRatio > 0.5) return { language: 'en', confidence: Math.min(latinRatio + 0.1, 0.9) };

  return { language: 'unknown', confidence: 0.3 };
}

/**
 * 检测页面是否包含联系区（contact / about / inquiry 等 section）
 */
function hasContactSection(html: string): boolean {
  const contactPatterns = [
    'contact', 'contact-us', 'contactus', 'get-in-touch', 'inquiry',
    '联系我们', '联系我们', '询盘', '询价', '在线咨询',
    'leave a message', 'send message', 'send inquiry',
    'footer', '联系方式',
  ];
  for (const pattern of contactPatterns) {
    const regex = new RegExp(
      `id\\s*=\\s*["']${pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["']`,
      'i'
    );
    if (regex.test(html)) return true;

    const classRegex = new RegExp(
      `class\\s*=\\s*["'][^"']*${pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^"']*["']`,
      'i'
    );
    if (classRegex.test(html)) return true;
  }
  return false;
}

// ===== 核心提取函数 =====

/**
 * 综合提取函数：从 HTML 中提取所有询盘相关信息
 */
export function extractInquiryInfo(html: string): InquiryInfo {
  const emails = extractEmails(html);
  const phones = extractPhones(html);
  const urls = extractUrls(html);
  const formFields = extractFormFields(html);
  const inquiryParagraphs = findInquirySection(html);
  const langResult = detectLanguage(html);
  const contactSectionFound = hasContactSection(html) || formFields.length > 0;

  // 计算整体置信度
  let confidenceFactors: number[] = [];

  if (emails.length > 0) confidenceFactors.push(Math.min(emails.length * 0.15, 0.6));
  if (phones.length > 0) confidenceFactors.push(Math.min(phones.length * 0.1, 0.4));
  if (formFields.length > 0) confidenceFactors.push(Math.min(formFields.length * 0.12, 0.5));
  if (inquiryParagraphs.length > 0) {
    const avgRelevance = inquiryParagraphs.reduce((s, p) => s + p.relevance, 0) / inquiryParagraphs.length;
    confidenceFactors.push(avgRelevance * 0.6);
  }
  if (contactSectionFound) confidenceFactors.push(0.3);

  const overallConfidence = confidenceFactors.length > 0
    ? Math.round(Math.min(confidenceFactors.reduce((a, b) => a + b, 0) / Math.min(confidenceFactors.length, 3), 0.98) * 100) / 100
    : 0.05;

  return {
    emails,
    phones,
    urls: deduplicate(urls, u => u.url),
    formFields,
    inquiryParagraphs,
    detectedLanguage: langResult.language,
    languageConfidence: Math.round(langResult.confidence * 100) / 100,
    overallConfidence: Math.round(overallConfidence * 100) / 100,
    contactSectionFound,
  };
}
