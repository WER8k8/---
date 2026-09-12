import { ref, type Ref } from 'vue'
import { apiGet } from '@/utils/api'

export type PageDataMode = 'live' | 'demo' | 'empty' | 'error'

export interface UsePageDataResult<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  mode: Ref<PageDataMode>
  error: Ref<string | null>
  load: () => Promise<void>
}

/** 统一页面数据加载：仅真实 API，失败为空态 */
export function usePageData<T>(
  fetcher: () => Promise<T>,
): UsePageDataResult<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const mode = ref<PageDataMode>('empty')
  const error = ref<string | null>(null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      data.value = await fetcher()
      mode.value = 'live'
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载失败'
      error.value = msg
      data.value = null
      mode.value = 'empty'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, mode, error, load }
}

/** 快捷 GET 封装 */
export async function pageGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  return apiGet<T>(path, params)
}
