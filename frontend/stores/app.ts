export const useAppStore = defineStore('app', () => {
  // ===== 全局加载状态 =====
  const globalLoading = ref(false)
  const loadingCount = ref(0)

  function startLoading() {
    loadingCount.value++
    globalLoading.value = true
  }

  function stopLoading() {
    loadingCount.value = Math.max(0, loadingCount.value - 1)
    if (loadingCount.value === 0) {
      globalLoading.value = false
    }
  }

  // ===== Toast 消息 =====
  const toasts = ref<
    { id: number; message: string; type: 'success' | 'error' | 'warning' | 'info' }[]
  >([])

  let toastId = 0

  function showToast(
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    duration = 3000
  ) {
    if (import.meta.client) {
      const id = ++toastId
      toasts.value.push({ id, message, type })
      setTimeout(() => {
        toasts.value = toasts.value.filter((t) => t.id !== id)
      }, duration)
      return id
    }
    return 0
  }

  // ===== 网络状态 =====
  const isOnline = ref(true)

  function setOnline(online: boolean) {
    isOnline.value = online
  }

  // ===== 设备信息 =====
  const isMobile = ref(false)
  const viewportWidth = ref(0)

  function updateViewport(width: number) {
    viewportWidth.value = width
    isMobile.value = width < 768
  }

  // 初始化网络监听（仅客户端）
  if (import.meta.client) {
    isOnline.value = navigator.onLine
    window.addEventListener('online', () => setOnline(true))
    window.addEventListener('offline', () => setOnline(false))
  }

  return {
    globalLoading,
    loadingCount,
    startLoading,
    stopLoading,
    toasts,
    showToast,
    isOnline,
    setOnline,
    isMobile,
    viewportWidth,
    updateViewport,
  }
})
