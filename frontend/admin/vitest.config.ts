import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { configDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  test: {
    environment: 'happy-dom',
    exclude: [...configDefaults.exclude, 'tests/email_campaign.spec.ts'],
  },
});
