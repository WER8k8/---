import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

interface CaseImage {
  id: string
  case_id: string
  image_url: string
  image_alt: string | null
  sort_order: number
  created_at: string
}

interface CaseStudy {
  id: string
  product_id: string | null
  project_name: string
  slug: string
  client_name: string | null
  materials_used: string | null
  construction_area: string | null
  project_date: string | null
  location: string | null
  project_address: string | null
  description: string | null
  cover_image: string | null
  status: string
  sort_order: number
  is_published: boolean
  view_count: number
  images: CaseImage[]
  created_at: string
  updated_at: string
}

export const useCaseStore = defineStore('case', {
  state: () => ({
    cases: [] as CaseStudy[],
    currentCase: null as CaseStudy | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    publishedCases: (state) => state.cases.filter((c) => c.status === 'published'),
  },
  actions: {
    async fetchCases() {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        const response = await request<{ items: CaseStudy[], total: number }>('/cases')
        this.cases = response.items || []
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async fetchCaseBySlug(slug: string) {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        this.currentCase = await request<CaseStudy>(`/cases/slug/${slug}`)
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  },
})
