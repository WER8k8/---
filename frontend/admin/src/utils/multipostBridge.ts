/** MultiPost 扩展 API — 仅能从优丁已授权域名页唤起 */

export type MultipostResponse = {
  type?: string
  traceId?: string
  action?: string
  code?: number
  message?: string
  data?: unknown
}

function randomTraceId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `yd-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export function multipostRequest<T = unknown>(
  action: string,
  data: Record<string, unknown> = {},
  timeoutMs = 20000,
): Promise<MultipostResponse> {
  return new Promise((resolve, reject) => {
    const traceId = randomTraceId()
    const onMessage = (ev: MessageEvent) => {
      const msg = ev.data as MultipostResponse
      if (!msg || msg.type !== 'response' || msg.traceId !== traceId) return
      window.removeEventListener('message', onMessage)
      clearTimeout(timer)
      resolve(msg)
    }
    const timer = window.setTimeout(() => {
      window.removeEventListener('message', onMessage)
      reject(new Error('未检测到 MultiPost 扩展，请先安装并在本页授权优丁域名'))
    }, timeoutMs)
    window.addEventListener('message', onMessage)
    window.postMessage({ type: 'request', traceId, action, data }, '*')
  })
}

export async function requestMultipostTrustDomain(): Promise<boolean> {
  const res = await multipostRequest('MULTIPOST_EXTENSION_REQUEST_TRUST_DOMAIN', {})
  if (res.code === 403) {
    throw new Error('扩展未授权本站点，请在 MultiPost 弹窗中确认信任优丁')
  }
  const data = res.data as { trusted?: boolean; status?: string } | null
  return Boolean(data?.trusted || data?.status === 'confirm')
}

export async function openMultipostPublish(sync: Record<string, unknown>): Promise<void> {
  const res = await multipostRequest('MULTIPOST_EXTENSION_PUBLISH', { sync })
  if (res.code && res.code >= 400) {
    throw new Error(res.message || 'MultiPost 发布窗口打开失败')
  }
}
