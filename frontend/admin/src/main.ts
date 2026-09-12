import { createApp } from 'vue';
import { createPinia } from 'pinia';
/** Ant Design Vue 4：组件样式走 CSS-in-JS，全局仅需 reset */
import 'ant-design-vue/dist/reset.css';
import './styles/design-tokens-v3.scss';
import './styles/mint-glass-shell.scss';
import './styles/shell-theme-dark.scss';
import './styles/coachpro-mint-motion.scss';
import './styles/shell-motion.scss';
import './styles/coachpro-tertiary-pages.scss';
import './styles/admin-2026-global.scss';
import './styles/login-slide-trae.css';
import './style.css';
import App from './App.vue';
import router from './router';
import { useAuthStore } from '@/stores/auth';
import { initUiPreferencesWatch } from '@/stores/uiPreferences';

const app = createApp(App);

app.use(createPinia());
initUiPreferencesWatch();
app.use(router);

void useAuthStore().ensureAuthInitialized();

if (import.meta.env.DEV && 'serviceWorker' in navigator) {
  void navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => void r.unregister());
  });
} else if ('serviceWorker' in navigator && location.pathname.startsWith('/client')) {
  navigator.serviceWorker.register('/sw.js').catch(() => undefined);
}

app.mount('#app');
