import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface AnalyticsData {
  overview: {
    total_visitors: number;
    page_views: number;
    bounce_rate: number;
    avg_session_duration: string;
  };
  conversions: {
    inquiries: number;
    conversion_rate: number;
  };
}

export const useAnalyticsStore = defineStore('analytics', {
  state: () => ({
    dashboard: null as AnalyticsData | null,
    traffic: [] as any[],
    productAnalytics: [] as any[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchDashboard() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.dashboard = await request<AnalyticsData>('/analytics');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchTraffic(period: string = '7d') {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request('/analytics/traffic', { params: { period } });
        this.traffic = response.data || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchProductAnalytics() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request('/analytics/products');
        this.productAnalytics = response.data || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async exportReport(format: string = 'csv') {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const result = await request('/analytics/export', { params: { format } });
        return result;
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
  },
});
