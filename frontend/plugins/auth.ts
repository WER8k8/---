/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineNuxtPlugin } from '#app';
import { useAuthStore } from '~/stores/auth';

export default defineNuxtPlugin(() => {
  if (import.meta.client) {
    const auth = useAuthStore();
    auth.initFromStorage();
  }
});
