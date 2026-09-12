import { nextTick, onMounted, onUnmounted, ref, type Ref } from 'vue'

const STORAGE_KEY = 'caiwang_assistant_pos'
const DRAG_THRESHOLD = 5

type Point = { x: number; y: number }

function readSaved(): Point | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const p = JSON.parse(raw) as Point
    if (typeof p.x === 'number' && typeof p.y === 'number') return p
  } catch {
    /* ignore */
  }
  return null
}

type FloatingDragOptions = {
  onFabClick?: () => void
}

export function useFloatingDrag(
  rootEl: Ref<HTMLElement | null>,
  panelOpen: Ref<boolean>,
  options: FloatingDragOptions = {},
) {
  const pos = ref<Point>({ x: 0, y: 0 })
  const dragging = ref(false)
  let start = { x: 0, y: 0, originX: 0, originY: 0, moved: false }
  let clickTarget: 'fab' | 'header' | null = null

  function measureBounds() {
    const el = rootEl.value
    const width = el?.offsetWidth || (panelOpen.value ? 380 : 72)
    const height = el?.offsetHeight || (panelOpen.value ? 420 : 72)
    return { width, height }
  }

  function clamp(x: number, y: number): Point {
    const { width, height } = measureBounds()
    const maxX = Math.max(8, window.innerWidth - width - 8)
    const maxY = Math.max(8, window.innerHeight - height - 8)
    return {
      x: Math.min(Math.max(8, x), maxX),
      y: Math.min(Math.max(8, y), maxY),
    }
  }

  function defaultPos(): Point {
    const { width, height } = measureBounds()
    return clamp(window.innerWidth - width - 20, window.innerHeight - height - 20)
  }

  function initPosition() {
    const saved = readSaved()
    pos.value = saved ? clamp(saved.x, saved.y) : defaultPos()
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(pos.value))
  }

  function onPointerMove(e: PointerEvent) {
    if (!dragging.value) return
    const dx = e.clientX - start.x
    const dy = e.clientY - start.y
    if (Math.abs(dx) + Math.abs(dy) > DRAG_THRESHOLD) start.moved = true
    pos.value = clamp(start.originX + dx, start.originY + dy)
  }

  function finishDrag(): 'fab-click' | null {
    if (!dragging.value) return null
    dragging.value = false
    persist()
    pos.value = clamp(pos.value.x, pos.value.y)
    const target = clickTarget
    const wasClick = !start.moved
    clickTarget = null
    start.moved = false
    if (wasClick && target === 'fab') return 'fab-click'
    return null
  }

  function beginDrag(e: PointerEvent, target: 'fab' | 'header', handle: HTMLElement) {
    if (e.button !== 0) return
    if (target === 'header' && (e.target as HTMLElement).closest('button,a')) return
    e.preventDefault()
    dragging.value = true
    clickTarget = target
    start = {
      x: e.clientX,
      y: e.clientY,
      originX: pos.value.x,
      originY: pos.value.y,
      moved: false,
    }
    handle.setPointerCapture(e.pointerId)
  }

  function onWindowPointerUp() {
    const action = finishDrag()
    if (action === 'fab-click') options.onFabClick?.()
  }

  function onResize() {
    pos.value = clamp(pos.value.x, pos.value.y)
  }

  onMounted(async () => {
    await nextTick()
    initPosition()
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onWindowPointerUp)
    window.addEventListener('resize', onResize)
  })

  onUnmounted(() => {
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onWindowPointerUp)
    window.removeEventListener('resize', onResize)
  })

  return {
    pos,
    dragging,
    initPosition,
    beginDrag,
    finishDrag,
    clamp,
  }
}
