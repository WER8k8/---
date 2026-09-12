import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface SystemInfo {
  version: string;
  environment: string;
  uptime: string;
  last_deploy: string;
}

export interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  api_requests_per_minute: number;
}

export const useSystemStore = defineStore('system', {
  state: () => ({
    health: null as any,
    info: null as SystemInfo | null,
    stats: null as SystemStats | null,
    logs: [] as any[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchHealth() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.health = await request('/system/health', { skipAuth: true });
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchInfo() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.info = await request<SystemInfo>('/system/info');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchStats() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.stats = await request<SystemStats>('/system/stats');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchLogs(page: number = 1, pageSize: number = 50, level?: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request('/system/logs', {
          params: { page, page_size: pageSize, level },
        });
        this.logs = response.items || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async clearCache() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/system/cache/clear', { method: 'POST' });
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async restartServices(service: string = 'all') {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/system/restart', { method: 'POST', params: { service } });
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
  },
});
