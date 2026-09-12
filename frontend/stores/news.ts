import { defineStore } from 'pinia';
import { useApi } from '~/composables/useApi';

export interface News {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  content: string | null;
  image_url: string | null;
  cover_image: string | null;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  category: string;
  published_at: string | null;
  created_at: string;
}

export const useNewsStore = defineStore('news', {
  state: () => ({
    news: [] as News[],
    currentNews: null as News | null,
    currentArticle: null as News | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    activeNews: (state) => state.news.filter((n) => n.is_active),
    articles: (state) => state.news.filter((n) => n.is_active),
  },
  actions: {
    async fetchArticles() {
      return this.fetchNews();
    },
    async fetchNews() {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const response = await request<{ items: News[]; total: number }>('/news');
        this.news = response.items || [];
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchNewsItem(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        this.currentNews = await request<News>(`/news/${id}`);
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchArticleBySlug(slug: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        const article = await request<News>(`/news/${slug}`, { params: { slug } });
        this.currentArticle = article as any;
        this.currentNews = article as any;
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async createNews(data: Partial<News>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request('/news', { method: 'POST', body: data });
        await this.fetchNews();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async updateNews(id: string, data: Partial<News>) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/news/${id}`, { method: 'PUT', body: data });
        await this.fetchNews();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    async deleteNews(id: string) {
      this.loading = true;
      this.error = null;
      try {
        const { request } = useApi();
        await request(`/news/${id}`, { method: 'DELETE' });
        await this.fetchNews();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
