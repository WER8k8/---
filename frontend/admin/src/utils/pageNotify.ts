import { message } from 'ant-design-vue'

type NotifyType = 'warning' | 'error' | 'info' | 'success'

const lastShown = new Map<string, number>()
const DEFAULT_DEDUP_MS = 8000

/** 同 key 在窗口期内只弹一次 toast，避免 keep-alive 多 tab 堆叠 */
export function notifyOnce(
  type: NotifyType,
  content: string,
  key?: string,
  dedupMs = DEFAULT_DEDUP_MS,
): void {
  const k = key ?? `${type}:${content}`
  const now = Date.now()
  const prev = lastShown.get(k)
  if (prev != null && now - prev < dedupMs) return
  lastShown.set(k, now)
  message[type]({ content, key: k, duration: 4 })
}

export function clearNotifyDedup(key?: string): void {
  if (key) lastShown.delete(key)
  else lastShown.clear()
}
