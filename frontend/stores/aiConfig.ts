import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface AIProvider {
  id: string;
  name: string;
  enabled: boolean;
}

export interface AIQuota {
  daily_limit: number;
  used_today: number;
  remaining: number;
}

export interface AIConfigData {
  providers: AIProvider[];
  default_provider: string;
  quota: AIQuota;
}

export const useAiConfigStore = defineStore('aiConfig', {
  state: () => ({
    config: null as AIConfigData | null,
    stats: null as any,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchConfig() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.config = await request<AIConfigData>('/ai-config');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateConfig(data: Partial<AIConfigData>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/ai-config', { method: 'PUT', body: data });
        if (this.config) {
          this.config = { ...this.config, ...data };
        }
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async toggleProvider(providerId: string, enabled: boolean) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/ai-config/provider/${providerId}/toggle`, {
          method: 'POST',
          body: { enabled },
        });
        if (this.config) {
          const provider = this.config.providers.find((p) => p.id === providerId);
          if (provider) {
            provider.enabled = enabled;
          }
        }
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async fetchStats() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.stats = await request('/ai-config/stats');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
