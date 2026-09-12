import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface SEOData {
  total_keywords: number;
  ranked_keywords: number;
  top_ranking: number;
  traffic_estimate: string;
  improvement_rate: number;
}

export const useSeoStore = defineStore('seo', {
  state: () => ({
    dashboard: null as SEOData | null,
    keywords: [] as any[],
    auditResult: null as any,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchDashboard() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.dashboard = await request<SEOData>('/seo/dashboard');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchKeywords() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request<any>('/seo/keywords');
        this.keywords = Array.isArray(response) ? response : (response?.items ?? []);
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async optimizeContent(data: any) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const result = await request('/seo/content-optimizer/optimize', {
          method: 'POST',
          body: data,
        });
        return result;
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async generateLLMsTxt(data: any) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const result = await request('/seo/llms-txt/generate', { method: 'POST', body: data });
        return result;
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async runSiteAudit() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.auditResult = await request('/seo/site-audit');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
