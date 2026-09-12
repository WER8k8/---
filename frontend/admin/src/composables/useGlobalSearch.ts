import { ref } from 'vue'

const paletteOpen = ref(false)

/** 顶栏 Ctrl+K / 全局搜索面板 — 跨 layout 与 GlobalSearch 共享状态 */
export function useGlobalSearch() {
  function openSearch() {
    paletteOpen.value = true
  }

  function closeSearch() {
    paletteOpen.value = false
  }

  function toggleSearch() {
    paletteOpen.value = !paletteOpen.value
  }

  return {
    paletteOpen,
    openSearch,
    closeSearch,
    toggleSearch,
  }
}
