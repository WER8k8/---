import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface CaseStudy {
  id: string;
  project_name: string;
  slug: string;
  location: string | null;
  description: string | null;
  content: string | null;
  image_url: string | null;
  cover_image: string | null;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  construction_area: string | null;
  project_date: string | null;
  status: string;
  created_at: string;
}

export const useCaseStore = defineStore('case', {
  state: () => ({
    cases: [] as CaseStudy[],
    currentCase: null as CaseStudy | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    activeCases: (state) => state.cases.filter((c) => c.is_active),
    publishedCases: (state) => state.cases.filter((c) => c.is_active),
  },
  actions: {
    async fetchCases() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request<{ items: CaseStudy[]; total: number }>('/case-studies');
        this.cases = response.items || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchCase(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.currentCase = await request<CaseStudy>(`/case-studies/${id}`);
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createCase(data: Partial<CaseStudy>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/case-studies', { method: 'POST', body: data });
        await this.fetchCases();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateCase(id: string, data: Partial<CaseStudy>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/case-studies/${id}`, { method: 'PUT', body: data });
        await this.fetchCases();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async deleteCase(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/case-studies/${id}`, { method: 'DELETE' });
        await this.fetchCases();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
