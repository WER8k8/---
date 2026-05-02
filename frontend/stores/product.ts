import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

interface ProductCategory {
  id: string
  name: string
  slug: string
  description: string | null
  parent_id: string | null
  sort_order: number
  is_active: boolean
  created_at: string
}

interface Product {
  id: string
  category_id: string
  name: string
  slug: string
  subtitle: string | null
  description: string | null
  technical_params: string | null
  application_scenarios: string | null
  advantages: string | null
  specifications: string | null
  density: string | null
  strength: string | null
  thermal_conductivity: string | null
  unit_weight: string | null
  image_url: string | null
  meta_title: string | null
  meta_description: string | null
  sort_order: number
  is_active: boolean
  view_count: number
  created_at: string
}

export const useProductStore = defineStore('product', {
  state: () => ({
    categories: [] as ProductCategory[],
    products: [] as Product[],
    currentProduct: null as Product | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    activeProducts: (state) => state.products.filter((p) => p.is_active),
    categoryMap: (state) => {
      const map: Record<string, ProductCategory> = {}
      for (const cat of state.categories) {
        map[cat.id] = cat
      }
      return map
    },
  },
  actions: {
    async fetchCategories() {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        this.categories = await request<ProductCategory[]>('/products/categories')
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async fetchProducts(categoryId?: string) {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        const response = await request<{ items: Product[], total: number }>('/products', {
          params: categoryId ? { category_id: categoryId } : undefined,
        })
        this.products = response.items || []
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async fetchProductBySlug(slug: string) {
      this.loading = true
      this.error = null
      try {
        const { request } = useApi()
        this.currentProduct = await request<Product>(`/products/by-slug/${slug}`)
      } catch (e: any) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  },
})
