/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export default defineNuxtPlugin(() => {
  const appStore = useAppStore()

  const toast = {
    show(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration?: number) {
      return appStore.showToast(message, type, duration)
    },
    success(message: string) {
      return appStore.showToast(message, 'success')
    },
    error(message: string) {
      return appStore.showToast(message, 'error')
    },
    warning(message: string) {
      return appStore.showToast(message, 'warning')
    },
    info(message: string) {
      return appStore.showToast(message, 'info')
    },
  }

  return {
    provide: { toast },
  }
})
