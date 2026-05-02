import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

interface DashboardData {
  total_keywords: number
  ranked_keywords: number
  avg_rank: number | null
  ai_optimized_pages: number
  llms_txt_generated: boolean
  last_audit_score: number | null
  keyword_trend: Array<{ date: string; avg_rank: number | null }>
  page_coverage: Array<{ type: string; count: number }>
}

export const useSeoStore = defineStore('seo', {
  state: () => ({
    dashboard: null as DashboardData | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    keywordCoverageRate: (state) => {
      if (!state.dashboard) return 0
      return state.dashboard.total_keywords > 0
        ? Math.round((state.dashboard.ranked_keywords / state.dashboard.total_keywords) * 100)
        : 0
    },
    auditHealth: (state) => {
      if (!state.dashboard || state.dashboard.last_audit_score === null) return 'unknown'
      const score = state.dashboard.last_audit_score
      if (score >= 80) return 'good'
      if (score >= 60) return 'medium'
      return 'poor'
    },
  },
  actions: {
    async fetchDashboard() {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        const data = await request<DashboardData>('/seo/dashboard')
        this.dashboard = data
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    clearError() {
      this.error = null
    },
  },
})
