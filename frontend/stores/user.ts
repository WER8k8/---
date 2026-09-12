import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [] as User[],
    currentUser: null as User | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    activeUsers: (state) => state.users.filter((u) => u.is_active),
    roles: () => ['super_admin', 'admin', 'editor', 'sales', 'viewer'],
  },
  actions: {
    async fetchUsers() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request<{ items: User[]; total: number }>('/users');
        this.users = response.items || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchUser(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.currentUser = await request<User>(`/users/${id}`);
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createUser(data: Partial<User>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/users', { method: 'POST', body: data });
        await this.fetchUsers();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateUser(id: string, data: Partial<User>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/users/${id}`, { method: 'PUT', body: data });
        await this.fetchUsers();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async deleteUser(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/users/${id}`, { method: 'DELETE' });
        await this.fetchUsers();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
