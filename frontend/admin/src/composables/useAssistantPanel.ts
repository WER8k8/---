import { ref } from 'vue'

/** 全局悬浮助手面板开关（任意页面可唤起） */
const panelOpen = ref(false)

export function useAssistantPanel() {
  return {
    isOpen: panelOpen,
    open: () => {
      panelOpen.value = true
    },
    close: () => {
      panelOpen.value = false
    },
    toggle: () => {
      panelOpen.value = !panelOpen.value
    },
  }
}
