<template>
  <footer class="bg-gray-900 text-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="py-12 lg:py-16">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          <div class="lg:col-span-1">
            <div class="flex items-center space-x-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
                <svg
                  class="w-6 h-6 text-white"
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
              <span class="text-xl font-bold">优丁建材</span>
            </div>
            <p class="text-gray-400 leading-relaxed mb-6">
              专业轻集料混凝土生产企业，致力于新型建筑材料的研发与生产，为客户提供高品质的建筑解决方案。
            </p>
            <div class="flex space-x-4">
              <a
                href="#"
                class="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:bg-primary hover:text-white transition-all duration-200"
              >
                <svg
                  class="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <a
                href="#"
                class="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:bg-primary hover:text-white transition-all duration-200"
              >
                <svg
                  class="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
              <a
                href="#"
                class="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:bg-primary hover:text-white transition-all duration-200"
              >
                <svg
                  class="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.58 3.898-2.96-.924c-.64-.203-.658-.64.135-.957l10.166-4.463c.538-.239 1.006.192.832.913z" />
                </svg>
              </a>
            </div>
          </div>
          
          <div>
            <h4 class="text-lg font-semibold mb-6 text-white">
              产品中心
            </h4>
            <ul class="space-y-3">
              <li
                v-for="item in productLinks"
                :key="item.label"
              >
                <NuxtLink 
                  :to="item.to" 
                  class="text-gray-400 hover:text-white transition-colors duration-200 flex items-center group"
                >
                  <svg
                    class="w-4 h-4 mr-2 text-gray-500 group-hover:text-primary transition-colors"
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
                </NuxtLink>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-lg font-semibold mb-6 text-white">
              快速链接
            </h4>
            <ul class="space-y-3">
              <li
                v-for="item in quickLinks"
                :key="item.label"
              >
                <NuxtLink 
                  :to="item.to" 
                  class="text-gray-400 hover:text-white transition-colors duration-200 flex items-center group"
                >
                  <svg
                    class="w-4 h-4 mr-2 text-gray-500 group-hover:text-primary transition-colors"
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
                </NuxtLink>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-lg font-semibold mb-6 text-white">
              联系我们
            </h4>
            <ul class="space-y-4">
              <li class="flex items-start space-x-3">
                <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg
                    class="w-4 h-4 text-primary"
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
                  <p class="text-gray-400 text-sm">
                    销售热线
                  </p>
                  <a
                    :href="'tel:' + phone"
                    class="text-white font-semibold hover:text-primary transition-colors"
                  >{{ phone }}</a>
                </div>
              </li>
              <li class="flex items-start space-x-3">
                <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg
                    class="w-4 h-4 text-primary"
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
                  <p class="text-gray-400 text-sm">
                    电子邮箱
                  </p>
                  <a
                    :href="'mailto:' + email"
                    class="text-white font-semibold hover:text-primary transition-colors"
                  >{{ email }}</a>
                </div>
              </li>
              <li class="flex items-start space-x-3">
                <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg
                    class="w-4 h-4 text-primary"
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
                  <p class="text-gray-400 text-sm">
                    公司地址
                  </p>
                  <p class="text-white">
                    {{ address }}
                  </p>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <div class="border-t border-gray-800 py-6">
        <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <p class="text-gray-500 text-sm">
            &copy; {{ currentYear }} 优丁建材 版权所有 | 粤ICP备2024000001号
          </p>
          <div class="flex space-x-6">
            <NuxtLink
              to="/privacy"
              class="text-gray-500 text-sm hover:text-white transition-colors"
            >
              隐私政策
            </NuxtLink>
            <NuxtLink
              to="/terms"
              class="text-gray-500 text-sm hover:text-white transition-colors"
            >
              服务条款
            </NuxtLink>
            <NuxtLink
              to="/sitemap.xml"
              class="text-gray-500 text-sm hover:text-white transition-colors"
            >
              网站地图
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const phone = '400-888-8888'
const email = 'info@youding.com'
const address = '中国广东省佛山市建材产业园区优丁大厦'
const currentYear = new Date().getFullYear()

const productLinks = [
  { to: '/products', label: '轻集料混凝土' },
  { to: '/products', label: '陶粒混凝土' },
  { to: '/products', label: '加气混凝土' },
  { to: '/products', label: '保温砂浆' },
]

const quickLinks = [
  { to: '/about', label: '关于我们' },
  { to: '/news', label: '新闻资讯' },
  { to: '/cases', label: '工程案例' },
  { to: '/contact', label: '联系我们' },
]
</script>
