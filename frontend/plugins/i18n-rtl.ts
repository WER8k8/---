/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * RTL support plugin
 * Sets the dir attribute on <html> based on the current locale
 * Currently supports Arabic (ar) as RTL
 */
export default defineNuxtPlugin({
  hooks: {
    'i18n:beforeLocaleSwitch'() {
      // noop
    },
    'i18n:localeSwitched'(context: { newLocale: string }) {
      const rtlLocales = ['ar'];
      const dir = rtlLocales.includes(context.newLocale) ? 'rtl' : 'ltr';
      if (process.client) {
        document.documentElement.setAttribute('dir', dir);
        document.documentElement.setAttribute('lang', context.newLocale);
      }
    },
  },
});
