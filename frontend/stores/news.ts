import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

interface NewsArticle {
  id: string
  title: string
  slug: string
  subtitle: string | null
  summary: string | null
  content: string | null
  cover_image: string | null
  category: string
  tags: string | null
  author: string | null
  source: string | null
  view_count: number
  published_at: string | null
  created_at: string | null
  updated_at: string | null
}

interface NewsCategory {
  id: string
  name: string
  slug: string
  description: string | null
}

export const useNewsStore = defineStore('news', {
  state: () => ({
    articles: [] as NewsArticle[],
    currentArticle: null as NewsArticle | null,
    categories: [] as NewsCategory[],
    loading: false,
    error: null as string | null,
  }),
  getters: {
    publishedArticles: (state) => state.articles.filter((a) => a.published_at),
  },
  actions: {
    async fetchArticles(category?: string) {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        const params: Record<string, any> = { page: 1, page_size: 100 }
        if (category) params.category = category
        const response = await request<{ items: NewsArticle[], total: number }>('/news', { params })
        this.articles = response.items || []
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async fetchArticleBySlug(slug: string) {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        this.currentArticle = await request<NewsArticle>(`/news/slug/${slug}`)
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async fetchCategories() {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        this.categories = await request<NewsCategory[]>('/news/categories')
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  },
})
