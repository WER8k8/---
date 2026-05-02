<template>
  <div
    class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all duration-300"
    :class="[
      hoverEffect ? 'hover:shadow-card-hover hover:border-blue-200 hover:-translate-y-1' : '',
      cardClass
    ]"
  >
    <!-- Image Section -->
    <div
      v-if="image"
      class="relative overflow-hidden"
      :class="imageContainerClass"
    >
      <img
        :src="image"
        :alt="imageAlt || title"
        :loading="loading"
        :decoding="decoding"
        class="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
      >
      
      <!-- Badge/Tag overlay -->
      <div
        v-if="badge"
        class="absolute top-3 left-3 px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full"
      >
        {{ badge }}
      </div>
      
      <!-- Action overlay (desktop only) -->
      <div
        v-if="showOverlay"
        class="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity duration-300 hidden md:flex items-center justify-center"
      >
        <button
          class="px-4 py-2 bg-white text-gray-900 font-medium rounded-lg transform translate-y-4 hover:translate-y-0 transition-transform"
          @click="$emit('action')"
        >
          {{ actionText || '查看详情' }}
        </button>
      </div>
    </div>

    <!-- Content Section -->
    <div
      class="p-4 sm:p-5 lg:p-6"
      :class="contentClass"
    >
      <!-- Category/Tag -->
      <div
        v-if="category"
        class="mb-3"
      >
        <span class="inline-block px-2 py-1 bg-blue-50 text-blue-600 text-xs font-medium rounded">
          {{ category }}
        </span>
      </div>

      <!-- Title -->
      <h3
        v-if="title"
        class="text-base sm:text-lg lg:text-xl font-semibold text-gray-900 mb-2 line-clamp-2"
      >
        <NuxtLink
          v-if="link"
          :to="link"
          class="hover:text-blue-600 transition-colors"
        >
          {{ title }}
        </NuxtLink>
        <template v-else>
          {{ title }}
        </template>
      </h3>

      <!-- Description -->
      <p
        v-if="description"
        class="text-sm sm:text-base text-gray-600 mb-4 line-clamp-3"
      >
        {{ description }}
      </p>

      <!-- Meta Info -->
      <div
        v-if="metaItems?.length"
        class="flex flex-wrap gap-3 mb-4"
      >
        <div
          v-for="(meta, index) in metaItems"
          :key="index"
          class="flex items-center gap-1 text-xs text-gray-500"
        >
          <svg
            v-if="meta.icon"
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              :d="meta.icon"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
            />
          </svg>
          <span>{{ meta.label }}</span>
        </div>
      </div>

      <!-- Footer/Actions -->
      <div
        v-if="showFooter"
        class="pt-4 border-t border-gray-100 flex items-center justify-between"
      >
        <div
          v-if="price"
          class="text-lg sm:text-xl font-bold text-blue-600"
        >
          ¥{{ price }}
        </div>
        
        <slot name="footer">
          <NuxtLink
            v-if="link"
            :to="link"
            class="inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors min-h-[44px] min-w-[44px] items-center"
          >
            {{ linkText || '了解更多' }}
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
                d="M9 5l7 7-7 7"
              />
            </svg>
          </NuxtLink>
        </slot>
      </div>

      <!-- Slot for custom content -->
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface MetaItem {
  label: string
  icon?: string
}

withDefaults(defineProps<{
  // Image props
  image?: string
  imageAlt?: string
  imageContainerClass?: string
  
  // Content props
  title?: string
  description?: string
  category?: string
  badge?: string
  
  // Link props
  link?: string
  linkText?: string
  
  // Style props
  hoverEffect?: boolean
  showOverlay?: boolean
  actionText?: string
  cardClass?: string
  contentClass?: string
  
  // Footer props
  showFooter?: boolean
  price?: number | string
  
  // Meta info
  metaItems?: MetaItem[]
  
  // Image loading
  loading?: 'lazy' | 'eager'
  decoding?: 'async' | 'sync' | 'auto'
}>(), {
  imageContainerClass: 'aspect-video',
  hoverEffect: true,
  showOverlay: false,
  showFooter: false,
  loading: 'lazy',
  decoding: 'async'
})

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
