<template>
  <!-- 页脚：墨色体系（与 RFQ 区同色，避免突然黑块）+ 建筑橙收边线作为有意收尾 -->
  <footer class="bg-[#17191c] border-t-4 border-primary text-white">
    <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
      <div class="py-6 sm:py-8 lg:py-12">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
          <div class="sm:col-span-2 lg:col-span-1">
            <div class="flex items-center space-x-2 sm:space-x-3 mb-3 sm:mb-6">
              <div
                class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-primary flex items-center justify-center"
              >
                <svg
                  class="w-5 h-5 sm:w-6 sm:h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                  />
                </svg>
              </div>
              <span class="text-base sm:text-lg lg:text-xl font-bold">{{ $t('common.companyName') }}</span>
            </div>
            <p class="text-white/70 text-xs sm:text-sm leading-relaxed mb-3 sm:mb-6">
              {{ $t('footer.companySlogan') }}
            </p>
            <div class="flex space-x-3 sm:space-x-4">
              <!-- China-specific social links (hidden on non-zh locales) -->
              <template v-if="isZhLocale">
                <!-- WeChat：button + 页内提示（替代 alert，键盘/读屏可访问） -->
                <div class="relative">
                  <button
                    type="button"
                    class="w-11 h-11 rounded bg-white/10 flex items-center justify-center text-white/70 hover:bg-primary hover:text-white transition-colors duration-200"
                    :aria-label="t('footer.wechat')"
                    :aria-expanded="showWechatId"
                    @click="showWechatId = !showWechatId"
                  >
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178A1.17 1.17 0 014.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178 1.17 1.17 0 01-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 01.598.082l1.584.926a.272.272 0 00.14.045c.133 0 .24-.11.24-.245 0-.06-.024-.12-.04-.178l-.325-1.233a.492.492 0 01.178-.554C23.028 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-7.062-6.122zm-2.18 2.909c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.97-.982zm4.36 0c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.97-.982z" />
                    </svg>
                  </button>
                  <div
                    v-if="showWechatId"
                    class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-white text-primary-900 text-xs sm:text-sm whitespace-nowrap shadow-lg border border-border"
                    role="status"
                  >
                    {{ t('footer.wechat') }}: youding-builder
                  </div>
                </div>
                <!-- Weibo -->
                <a
                  href="https://weibo.com/youdingjiancai"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="w-11 h-11 rounded bg-white/10 flex items-center justify-center text-white/70 hover:bg-primary hover:text-white transition-colors duration-200"
                  :aria-label="t('footer.weibo')"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M10.098 20.323c-3.977.391-7.414-1.406-7.672-4.02-.259-2.609 2.759-5.047 6.74-5.441 3.979-.394 7.413 1.404 7.671 4.018.259 2.6-2.759 5.049-6.739 5.443zM20.196 9.4a6.905 6.905 0 00-1.294-1.482 5.91 5.91 0 00-.576-.413c-.424-.275-.527-.745-.236-1.052.291-.308.772-.334 1.196-.065.25.16.494.345.73.554.558.492 1.004 1.095 1.309 1.782.304.686.416 1.401.37 2.108-.018.265-.25.47-.52.458-.27-.012-.478-.237-.462-.502a4.28 4.28 0 00-.19-1.214 4.27 4.27 0 00-.357-.769c-.004-.002-.004-.002 0 0zM20.785 5.77a11.4 11.4 0 00-1.395-1.123c-.772-.527-1.642-.877-2.484-.885-.429 0-.777-.339-.777-.757 0-.419.348-.758.777-.758 1.137.01 2.25.451 3.231 1.123.554.381 1.047.83 1.463 1.334.26.334.2.808-.136 1.064-.337.256-.814.197-1.076-.136L20.785 5.77zM9.244 17.508c1.882.297 3.389-.437 3.418-1.627.028-1.2-1.468-2.389-3.34-2.674-1.887-.285-3.39.434-3.418 1.634-.028 1.188 1.459 2.377 3.34 2.667z" />
                  </svg>
                </a>
                <!-- Douyin -->
                <a
                  href="https://www.douyin.com/user/youding"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="w-11 h-11 rounded bg-white/10 flex items-center justify-center text-white/70 hover:bg-primary hover:text-white transition-colors duration-200"
                  :aria-label="t('footer.douyin')"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" />
                  </svg>
                </a>
              </template>
              <!-- International social links (non-zh locales) -->
              <template v-else>
                <!-- WhatsApp -->
                <a
                  :href="'https://wa.me/' + phone.replace(/[^0-9]/g, '')"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="w-11 h-11 rounded bg-white/10 flex items-center justify-center text-white/70 hover:bg-primary hover:text-white transition-colors duration-200"
                  aria-label="WhatsApp"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.51 5.26l-.999 3.648 3.978-1.621zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/>
                  </svg>
                </a>
                <!-- Email -->
                <a
                  :href="'mailto:' + email"
                  class="w-11 h-11 rounded bg-white/10 flex items-center justify-center text-white/70 hover:bg-primary hover:text-white transition-colors duration-200"
                  :aria-label="t('footer.email')"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </a>
              </template>
            </div>
          </div>

          <div>
            <h4 class="text-sm sm:text-base lg:text-lg font-semibold mb-3 sm:mb-6 text-white">
              {{ $t('footer.productCenter') }}
            </h4>
            <ul class="space-y-2 sm:space-y-3">
              <li
                v-for="item in productLinks"
                :key="item.label"
              >
                <router-link
                  :to="item.to"
                  class="text-white/70 text-xs sm:text-sm hover:text-white transition-colors duration-200 flex items-center group"
                >
                  <svg
                    class="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-white/40 group-hover:text-primary transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  {{ item.label }}
                </router-link>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-sm sm:text-base lg:text-lg font-semibold mb-3 sm:mb-6 text-white">
              {{ $t('footer.quickLinks') }}
            </h4>
            <ul class="space-y-2 sm:space-y-3">
              <li
                v-for="item in quickLinks"
                :key="item.label"
              >
                <router-link
                  :to="item.to"
                  class="text-white/70 text-xs sm:text-sm hover:text-white transition-colors duration-200 flex items-center group"
                >
                  <svg
                    class="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-white/40 group-hover:text-primary transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  {{ item.label }}
                </router-link>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-sm sm:text-base lg:text-lg font-semibold mb-3 sm:mb-6 text-white">
              {{ $t('footer.buyerServices') }}
            </h4>
            <ul class="space-y-2 sm:space-y-3">
              <li
                v-for="item in buyerLinks"
                :key="item.label"
              >
                <router-link
                  :to="item.to"
                  class="text-white/70 text-xs sm:text-sm hover:text-white transition-colors duration-200 flex items-center group"
                >
                  <svg
                    class="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-white/40 group-hover:text-primary transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  {{ item.label }}
                </router-link>
              </li>
            </ul>
          </div>
        </div>

        <div class="mt-6 sm:mt-8 lg:mt-0 lg:col-span-4 border-t border-white/10 pt-6 sm:pt-8">
          <h4 class="text-sm sm:text-base lg:text-lg font-semibold mb-4 sm:mb-6 text-white">
            {{ $t('footer.contactUs') }}
          </h4>
          <ul class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
            <li class="flex items-start space-x-2 sm:space-x-3">
              <div
                class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0"
              >
                <svg
                  class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-white/60 text-xs sm:text-sm">
                  {{ $t('footer.salesHotline') }}
                </p>
                <a
                  :href="'tel:' + phone"
                  class="text-white text-xs sm:text-sm font-semibold hover:text-primary transition-colors"
                >{{ phone }}</a>
              </div>
            </li>
            <li class="flex items-start space-x-2 sm:space-x-3">
              <div
                class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0"
              >
                <svg
                  class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-white/60 text-xs sm:text-sm">
                  {{ $t('footer.email') }}
                </p>
                <a
                  :href="'mailto:' + email"
                  class="text-white text-xs sm:text-sm font-semibold hover:text-primary transition-colors"
                >{{ email }}</a>
              </div>
            </li>
            <li
              class="flex items-start space-x-2 sm:space-x-3 col-span-1 sm:col-span-3 sm:text-left"
            >
              <div
                class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0"
              >
                <svg
                  class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-white/60 text-xs sm:text-sm">
                  {{ $t('footer.address') }}
                </p>
                <p class="text-white text-xs sm:text-sm">
                  {{ address }}
                </p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div class="border-t border-white/10 py-4 sm:py-6">
        <div class="flex flex-col sm:flex-row justify-between items-center space-y-3 sm:space-y-0">
          <p class="text-white/50 text-xs sm:text-sm text-center sm:text-left">
            &copy; {{ currentYear }} {{ $t('common.copyright') }} | {{ $t('footer.icp') }} ｜ {{ $t('footer.beian') }}
          </p>
          <div class="flex flex-wrap justify-center gap-3 sm:gap-6">
            <router-link
              to="/privacy"
              class="text-white/50 text-xs sm:text-sm hover:text-white transition-colors"
            >
              {{ $t('footer.privacy') }}
            </router-link>
            <router-link
              to="/terms"
              class="text-white/50 text-xs sm:text-sm hover:text-white transition-colors"
            >
              {{ $t('footer.terms') }}
            </router-link>
            <a
              href="/sitemap.xml"
              class="text-white/50 text-xs sm:text-sm hover:text-white transition-colors"
            >
              {{ $t('footer.sitemap') }}
            </a>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { SITE_CONFIG } from '~/config/site';

const { t, locale } = useI18n();
const isZhLocale = computed(() => locale.value === 'zh');
const phone = SITE_CONFIG.phone;
const email = SITE_CONFIG.email;
const address = computed(() => t('footer.companyAddress'));
const currentYear = new Date().getFullYear();
/** 微信号页内提示开关（替代原 alert） */
const showWechatId = ref(false);

// 使用 computed 保证切换语言后链接文字实时更新
const productLinks = computed(() => [
  { to: '/products', label: t('footer.lightAggregate') },
  { to: '/products', label: t('footer.ceramsite') },
  { to: '/products', label: t('footer.insulationMortar') },
]);

const quickLinks = computed(() => [
  { to: '/about', label: t('footer.aboutUs') },
  { to: '/news', label: t('footer.newsInfo') },
  { to: '/cases', label: t('footer.caseStudies') },
  { to: '/markets', label: t('footer.markets') },
  { to: '/contact', label: t('footer.contactUs') },
  { to: '/platform', label: t('footer.saasPlatform') },
]);

const buyerLinks = computed(() => [
  { to: '/orders', label: t('footer.orderTracking') },
  { to: '/inquiries', label: t('footer.onlineInquiry') },
  { to: '/logistics', label: t('footer.shippingTracking') },
  { to: '/calculators', label: t('footer.engineeringCalculators') },
  { to: '/standards', label: t('footer.standardsAndCerts') },
  { to: '/resources', label: t('footer.whitepapersDocs') },
]);
</script>
