/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** SITE-DESIGN-01 · Tier1 12 语（与 backend im_locale_service.SUPPORTED_LANGUAGES 对齐） */

export const L_PRO_TIER1_LOCALES = [
  { label: '简体中文', value: 'zh-CN', code: 'zh' },
  { label: 'English', value: 'en-US', code: 'en' },
  { label: 'العربية', value: 'ar', code: 'ar' },
  { label: 'Español', value: 'es', code: 'es' },
  { label: 'Português', value: 'pt', code: 'pt' },
  { label: 'Русский', value: 'ru', code: 'ru' },
  { label: 'ไทย', value: 'th', code: 'th' },
  { label: 'Tiếng Việt', value: 'vi', code: 'vi' },
  { label: 'Bahasa Indonesia', value: 'id', code: 'id' },
  { label: 'Bahasa Melayu', value: 'ms', code: 'ms' },
  { label: '日本語', value: 'ja', code: 'ja' },
  { label: '한국어', value: 'ko', code: 'ko' },
] as const;

export const L_PRO_TIER1_SELECT_OPTIONS = L_PRO_TIER1_LOCALES.map((row) => ({
  label: row.label,
  value: row.value,
}));
