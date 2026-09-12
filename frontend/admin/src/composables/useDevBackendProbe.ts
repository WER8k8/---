import { onMounted, onUnmounted, ref } from 'vue'

/** 开发环境：周期性探测 API 是否存活，避免「全站转圈却不知道后端挂了」 */
export function useDevBackendProbe() {
  const backendDown = ref(false)
  const lastCheckedAt = ref<number | null>(null)

  let timer: ReturnType<typeof setInterval> | null = null

  let pendingController: AbortController | null = null
  let probing = false

  async function probe() {
    if (!import.meta.env.DEV || probing) return
    probing = true
    if (pendingController) pendingController.abort()
    const controller = new AbortController()
    pendingController = controller
    const timeout = setTimeout(() => controller.abort(), 5000)
    try {
      const res = await fetch('/api/v1/health', { signal: controller.signal })
      backendDown.value = !res.ok
    } catch {
      if (!controller.signal.aborted) backendDown.value = true
    } finally {
      clearTimeout(timeout)
      if (pendingController === controller) pendingController = null
      probing = false
      lastCheckedAt.value = Date.now()
    }
  }

  function onVisibilityChange() {
    if (document.visibilityState === 'visible') void probe()
  }

  onMounted(() => {
    if (!import.meta.env.DEV) return
    void probe()
    timer = setInterval(() => void probe(), 30_000)
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    if (pendingController) pendingController.abort()
  })

  return { backendDown, probe, lastCheckedAt }
}
