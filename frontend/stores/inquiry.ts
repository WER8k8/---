import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface Inquiry {
  id: string;
  name: string;
  company: string | null;
  phone: string | null;
  email: string | null;
  product: string | null;
  quantity: string | null;
  message: string | null;
  status: string;
  is_active: boolean;
  created_at: string;
}

export const useInquiryStore = defineStore('inquiry', {
  state: () => ({
    inquiries: [] as Inquiry[],
    currentInquiry: null as Inquiry | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    activeInquiries: (state) => state.inquiries.filter((i) => i.is_active),
    pendingInquiries: (state) => state.inquiries.filter((i) => i.status === 'pending'),
  },
  actions: {
    async fetchInquiries() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request<{ items: Inquiry[]; total: number }>('/inquiries');
        this.inquiries = response.items || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchInquiry(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.currentInquiry = await request<Inquiry>(`/inquiries/${id}`);
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createInquiry(data: Partial<Inquiry>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/inquiries', { method: 'POST', body: data, skipAuth: true });
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateInquiry(id: string, data: Partial<Inquiry>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/inquiries/${id}`, { method: 'PUT', body: data });
        await this.fetchInquiries();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async deleteInquiry(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/inquiries/${id}`, { method: 'DELETE' });
        await this.fetchInquiries();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
