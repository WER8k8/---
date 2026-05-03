<template>
  <header 
    class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
    :class="isScrolled ? 'bg-white/95 backdrop-blur-md shadow-sm' : 'bg-transparent'"
  >
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 lg:h-20 items-center">
        <NuxtLink
          to="/"
          class="flex items-center space-x-3 group"
        >
          <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-105">
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
          <span class="text-xl lg:text-2xl font-bold text-text-primary">优丁建材</span>
        </NuxtLink>
        
        <div class="hidden lg:flex items-center space-x-1">
          <NuxtLink 
            v-for="item in navItems" 
            :key="item.to" 
            :to="item.to"
            class="relative px-4 py-2 text-text-secondary font-medium rounded-lg transition-all duration-200 cursor-pointer"
            :class="isActive(item.to) ? 'text-primary bg-primary/5' : 'hover:text-primary hover:bg-surface-hover'"
          >
            {{ item.label }}
            <span 
              v-if="isActive(item.to)"
              class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-primary rounded-full"
            />
          </NuxtLink>
        </div>
        
        <div class="flex items-center space-x-4">
          <a 
            :href="'tel:' + phone" 
            class="hidden sm:flex items-center space-x-2 px-4 py-2 bg-primary/10 text-primary font-semibold rounded-lg hover:bg-primary hover:text-white transition-all duration-200"
          >
            <svg
              class="w-4 h-4"
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
            <span>{{ phone }}</span>
          </a>
          
          <button 
            class="lg:hidden p-2 text-text-secondary hover:text-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            @click="toggleMobileMenu"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                v-if="!isMobileMenuOpen"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
      
      <div 
        v-if="isMobileMenuOpen"
        class="lg:hidden py-4 border-t border-border animate-slide-up bg-white/95 backdrop-blur-md"
      >
        <div class="flex flex-col space-y-1 px-2">
          <NuxtLink 
            v-for="item in navItems" 
            :key="item.to" 
            :to="item.to"
            class="px-4 py-3 text-text-secondary font-medium rounded-lg transition-all duration-200 cursor-pointer active:bg-primary/5"
            :class="isActive(item.to) ? 'text-primary bg-primary/5' : 'hover:text-primary hover:bg-surface-hover'"
            @click="isMobileMenuOpen = false"
            @touchstart="handleTouchStart"
            @touchend="handleTouchEnd"
          >
            {{ item.label }}
          </NuxtLink>
          <a 
            :href="'tel:' + phone" 
            class="mt-2 px-4 py-3 bg-gradient-to-r from-primary to-primary-dark text-white font-semibold rounded-lg text-center active:opacity-90"
            @click="isMobileMenuOpen = false"
          >
            📞 {{ phone }}
          </a>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const phone = '400-888-8888'
const isScrolled = ref(false)
const isMobileMenuOpen = ref(false)

const navItems = [
  { to: '/', label: '首页' },
  { to: '/products', label: '产品中心' },
  { to: '/cases', label: '工程案例' },
  { to: '/about', label: '关于我们' },
  { to: '/news', label: '新闻资讯' },
  { to: '/contact', label: '联系我们' },
]

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

function handleScroll() {
  isScrolled.value = window.scrollY > 20
}

function handleTouchStart(e: TouchEvent) {
  const target = e.currentTarget as HTMLElement
  if (target) target.style.transform = 'scale(0.98)'
}

function handleTouchEnd(e: TouchEvent) {
  const target = e.currentTarget as HTMLElement
  if (target) target.style.transform = 'scale(1)'
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>
