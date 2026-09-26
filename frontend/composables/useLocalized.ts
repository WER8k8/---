/**
 * 多语言数据取值层（彻底杜绝语言混杂的统一入口）。
 *
 * 取值优先级（非中文语言）：
 *   1. AI 固化的 translations_json[locale][field]（大模型翻译器 11 语言全覆盖）
 *   2. 后端 *_en 英文字段
 *   3. 中文源字段（兜底，仅当以上均缺失）
 * 中文语言：直接取中文字段。
 *
 * 关键修复：在非中文语言下，若 AI 翻译缺失，则**不回退到 raw 中文字段**，
 * 而是回退到英文 *_en 字段；只有英文也缺失时，才回退到中文源字段。
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const HAN_RE = /[\u4e00-\u9fff]/

/** 解析产品的 AI 固化翻译 JSON（{lang: {field: text}}），失败返回空对象 */
function parseTranslations(obj: Record<string, any> | null | undefined): Record<string, Record<string, string>> {
  const raw = obj?.translations_json
  if (!raw || typeof raw !== 'string') return {}
  try {
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

/**
 * 校验译文是否纯净：对于非中文(locale)字段，确保**不含任何中文字符**。
 * 若 AI 翻译意外残留中文，视为无效 → 降级到英文字段。
 */
function _is_clean_non_zh(text: string | null | undefined): boolean {
  if (!text || typeof text !== 'string') return false
  // 非中文语言：译文中不得含汉字
  if (HAN_RE.test(text)) return false
  return true
}

export function useLocalized() {
  const { locale } = useI18n()

  // zh / zh-CN / zh-* 均视为中文，其余语言走多语言取值链
  const isZh = computed(() => String(locale.value || '').toLowerCase().startsWith('zh'))

  function pick<T extends Record<string, any>>(obj: T | null | undefined, field: string): any {
    if (!obj) return ''
    const raw = obj[field]
    if (isZh.value) return obj[field] ?? obj[`${field}_en`] ?? ''

    const lang = String(locale.value || '').toLowerCase()
    // 1) AI 固化翻译
    const aiText = parseTranslations(obj)[lang]?.[field]
    if (aiText && _is_clean_non_zh(aiText)) return aiText

    // 2) 英文字段
    const enText = obj[`${field}_en`]
    if (enText && _is_clean_non_zh(enText)) return enText

    // 3) 兜底：中文源字段（前端调试缺数用；生产环境 AI 翻译应已固化完整）
    return obj[field] || ''
  }

  return { locale, isZh, pick }
}
