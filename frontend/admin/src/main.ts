/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { createApp } from 'vue';
import { createPinia } from 'pinia';
/** Ant Design Vue 4：组件样式走 CSS-in-JS，全局仅需 reset */
import 'ant-design-vue/dist/reset.css';
import './styles/design-tokens-v3.scss';
/** v4 马卡龙薄荷增补层（纯新增令牌，不覆写既有令牌；详见 docs/超管后台设计与配色视觉统一规范-2026-09-20.md） */
import './styles/design-tokens-v4-macaron.scss';
import './styles/adaptive-tokens.scss';
import './styles/mint-glass-shell.scss';
import './styles/shell-theme-dark.scss';
import './styles/coachpro-mint-motion.scss';
import './styles/shell-motion.scss';
/** motion v4 微交互层（纯增补 opt-in 类 + 统一降级门禁；详见 docs/微交互特效选型与落地判定-2026-09-20.md） */
import './styles/motion-v4-macaron.scss';
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
if (import.meta.env.DEV && typeof window !== 'undefined') {
  (window as unknown as { __ROUTER__: typeof router }).__ROUTER__ = router;
}

void useAuthStore().ensureAuthInitialized();

if (import.meta.env.DEV && 'serviceWorker' in navigator) {
  void navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => void r.unregister());
  });
} else if ('serviceWorker' in navigator && location.pathname.startsWith('/client')) {
  navigator.serviceWorker.register('/sw.js').catch(() => undefined);
}

app.mount('#app');
