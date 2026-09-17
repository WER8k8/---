/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export function useToast() {
  const appStore = useAppStore()

  function show(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration?: number) {
    return appStore.showToast(message, type, duration)
  }

  function success(message: string) {
    return appStore.showToast(message, 'success')
  }

  function error(message: string) {
    return appStore.showToast(message, 'error')
  }

  function warning(message: string) {
    return appStore.showToast(message, 'warning')
  }

  function info(message: string) {
    return appStore.showToast(message, 'info')
  }

  return {
    toasts: computed(() => appStore.toasts),
    show,
    success,
    error,
    warning,
    info,
  }
}
