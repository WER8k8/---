import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface SettingsData {
  site: {
    name: string;
    domain: string;
    description: string;
    keywords: string;
  };
  seo: {
    title_prefix: string;
    meta_description: string;
    google_analytics_id: string;
  };
  system: {
    maintenance_mode: boolean;
    max_upload_size: number;
    allowed_file_types: string[];
  };
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    settings: null as SettingsData | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchSettings() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.settings = await request<SettingsData>('/settings');
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateSiteSettings(data: Partial<SettingsData['site']>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/settings/site', { method: 'PUT', body: data });
        if (this.settings) {
          this.settings.site = { ...this.settings.site, ...data };
        }
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async updateSeoSettings(data: Partial<SettingsData['seo']>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/settings/seo', { method: 'PUT', body: data });
        if (this.settings) {
          this.settings.seo = { ...this.settings.seo, ...data };
        }
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
    async updateSystemSettings(data: Partial<SettingsData['system']>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/settings/system', { method: 'PUT', body: data });
        if (this.settings) {
          this.settings.system = { ...this.settings.system, ...data };
        }
      } catch (e: any) {
        this.error = e.message;
        throw e;
      } finally {
        this.loading = false;
      }
    },
  },
});
