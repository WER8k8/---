import { defineNuxtPlugin } from '#app';
import { useAuthStore } from '~/stores/auth';

export default defineNuxtPlugin(() => {
  if (import.meta.client) {
    const auth = useAuthStore();
    auth.initFromStorage();
  }
});
