/**
 * useUndoDelete — 删除后 5 秒内可撤销
 *
 * 用法:
 *   const { deleteWithUndo } = useUndoDelete()
 *   await deleteWithUndo({
 *     api: () => api.delete(`/products/${id}`),
 *     undoApi: () => api.post(`/products/${id}/restore`),
 *     label: '产品「轻集料混凝土」',
 *     onSuccess: () => loadData(),
 *   })
 */
import { message } from 'ant-design-vue'
import { ref } from 'vue'

interface UndoDeleteOptions {
  /** 删除 API 调用 */
  api: () => Promise<any>
  /** 撤销 API 调用 */
  undoApi: () => Promise<any>
  /** 删除项的显示名称 */
  label: string
  /** 删除成功后的回调 */
  onSuccess?: () => void
  /** 撤销成功后的回调 */
  onUndo?: () => void
  /** 倒计时秒数，默认 5 */
  seconds?: number
}

const pendingUndos = ref<Map<string, { timer: ReturnType<typeof setTimeout>; undoFn: () => Promise<void> }>>(new Map())

let undoCounter = 0

export function useUndoDelete() {
  async function deleteWithUndo(opts: UndoDeleteOptions) {
    const seconds = opts.seconds ?? 5
    const undoId = `undo-${++undoCounter}`

    try {
      await opts.api()
    } catch (e: any) {
      message.error(`删除失败: ${e.message || '未知错误'}`)
      return
    }

    // 创建撤销函数
    let cancelled = false
    const undoFn = async () => {
      if (cancelled) return
      cancelled = true
      try {
        await opts.undoApi()
        message.success(`已恢复 ${opts.label}`)
        opts.onUndo?.()
      } catch (e: any) {
        message.error(`恢复失败: ${e.message || '未知错误'}`)
      }
    }

    // 显示带撤销按钮的 toast
    const key = `undo-${undoId}`
    message.open({
      key,
      content: () => {
        return h('span', [
          `已删除 ${opts.label}，`,
          h('a', {
            style: 'color: #4a9b8c; font-weight: 600; cursor: pointer; text-decoration: underline;',
            onClick: async () => {
              message.destroy(key)
              clearTimeout(timer)
              pendingUndos.value.delete(undoId)
              await undoFn()
            },
          }, '点击撤销'),
          `（${seconds}秒）`,
        ])
      },
      duration: seconds,
      type: 'info',
    })

    // 倒计时结束后执行真正的回调
    const timer = setTimeout(() => {
      pendingUndos.value.delete(undoId)
      if (!cancelled) {
        cancelled = true
        opts.onSuccess?.()
      }
    }, seconds * 1000)

    pendingUndos.value.set(undoId, { timer, undoFn })
  }

  /** 取消所有待确认的撤销 */
  function cancelAll() {
    for (const [id, { timer }] of pendingUndos.value) {
      clearTimeout(timer)
    }
    pendingUndos.value.clear()
  }

  return { deleteWithUndo, cancelAll, pendingUndos }
}

// 需要 import h from vue
import { h } from 'vue'
