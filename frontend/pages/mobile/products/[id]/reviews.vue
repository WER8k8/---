/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <MobileNavbar :title="t('mobile.reviews.title')" />

    <!-- Loading State -->
    <div v-if="pending && currentPage === 1" class="px-4 py-6">
      <div class="animate-pulse space-y-4">
        <div class="h-20 bg-gray-200 rounded-xl"></div>
        <div class="h-32 bg-gray-200 rounded-xl"></div>
        <div class="h-32 bg-gray-200 rounded-xl"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error && currentPage === 1" class="px-4 py-12 text-center">
      <div class="text-red-500 text-sm mb-4">{{ error.message || t('mobile.reviews.fetchError') }}</div>
      <button @click="refresh()" class="text-primary text-sm font-medium">
        {{ t('common.retry') }}
      </button>
    </div>

    <!-- Reviews Content -->
    <div v-else class="px-4 py-4">
      <!-- Review Stats Card -->
      <div class="bg-white rounded-xl p-4 mb-4 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <div>
            <div class="text-3xl font-bold text-primary">{{ averageRating }}</div>
            <div class="flex text-yellow-400 text-lg mt-1">
              <span v-for="star in 5" :key="star">{{ star <= Math.round(averageRating) ? '★' : '☆' }}</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm text-gray-500">{{ t('mobile.reviews.basedOn', { count: totalReviews }) }}</div>
          </div>
        </div>
        <!-- Rating Distribution -->
        <div class="space-y-1">
          <div v-for="rating in [5, 4, 3, 2, 1]" :key="rating" class="flex items-center gap-2">
            <span class="text-xs text-gray-500 w-6">{{ rating }}★</span>
            <div class="flex-1 bg-gray-100 rounded-full h-1.5">
              <div
                class="bg-yellow-400 h-1.5 rounded-full transition-all duration-300"
                :style="{ width: `${getRatingPercentage(rating)}%` }"
              ></div>
            </div>
            <span class="text-xs text-gray-400 w-6 text-right">{{ getRatingCount(rating) }}</span>
          </div>
        </div>
      </div>

      <!-- Reviews List -->
      <div v-if="reviews.length === 0 && !pending" class="text-center py-12 text-gray-400 text-sm">
        {{ t('mobile.reviews.noReviews') }}
      </div>

      <div v-else class="space-y-3">
        <div v-for="review in reviews" :key="review.id" class="bg-white rounded-xl p-4 shadow-sm">
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-xs font-semibold">
                {{ getInitials(review.user_id) }}
              </div>
              <div>
                <div class="text-sm font-medium text-gray-800">{{ t('mobile.reviews.user') }} {{ review.user_id.slice(0, 8) }}</div>
                <div class="text-xs text-gray-400">{{ formatDate(review.created_at) }}</div>
              </div>
            </div>
            <div class="flex text-yellow-400 text-sm">
              <span v-for="star in 5" :key="star">{{ star <= review.rating ? '★' : '☆' }}</span>
            </div>
          </div>

          <p class="text-sm text-gray-700 mb-2">{{ review.content }}</p>

          <!-- Review Images -->
          <div v-if="review.images" class="flex gap-2 mb-2">
            <img
              v-for="(image, index) in parseImages(review.images)"
              :key="index"
              :src="image"
              alt="Review image"
              class="w-16 h-16 object-cover rounded-lg cursor-pointer"
              @click="openImagePreview(image)"
            />
          </div>

          <!-- Review Status/Actions -->
          <div class="flex items-center gap-3 text-xs">
            <span v-if="review.status === 'pending'" class="text-yellow-600">{{ t('mobile.reviews.pending') }}</span>
            <span v-if="review.status === 'rejected'" class="text-red-600">{{ t('mobile.reviews.rejected') }}</span>
            <button
              v-if="canEditReview(review)"
              @click="editReview(review)"
              class="text-primary hover:text-primary-dark"
            >
              {{ t('common.edit') }}
            </button>
            <button
              v-if="canDeleteReview(review)"
              @click="deleteReview(review.id)"
              class="text-red-500 hover:text-red-700"
            >
              {{ t('common.delete') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Load More -->
      <button
        v-if="currentPage < totalPages && !pending"
        @click="loadMore()"
        class="w-full py-3 text-primary text-sm font-medium mt-4"
        :disabled="loadingMore"
      >
        {{ loadingMore ? t('common.loading') : t('common.loadMore') }}
      </button>
    </div>

    <!-- Fixed Write Review Button -->
    <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 safe-area-inset-bottom">
      <button
        @click="showReviewForm = true"
        class="w-full bg-primary text-white py-3 rounded-xl font-semibold text-sm"
        :disabled="!canReview"
      >
        {{ t('mobile.reviews.writeReview') }}
      </button>
    </div>

    <!-- Review Form Modal (Bottom Sheet) -->
    <div v-if="showReviewForm" class="fixed inset-0 bg-black bg-opacity-50 z-50" @click.self="showReviewForm = false">
      <div class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white rounded-t-2xl p-4 border-b border-gray-100 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">{{ t('mobile.reviews.writeReview') }}</h3>
          <button @click="showReviewForm = false" class="text-gray-400">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="submitReview" class="p-4 space-y-4">
          <!-- Rating -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('mobile.reviews.rating') }}</label>
            <div class="flex gap-2">
              <button
                v-for="star in 5"
                :key="star"
                type="button"
                @click="reviewForm.rating = star"
                class="text-3xl focus:outline-none"
                :class="star <= reviewForm.rating ? 'text-yellow-400' : 'text-gray-300'"
              >
                ★
              </button>
            </div>
          </div>

          <!-- Content -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('mobile.reviews.content') }}</label>
            <textarea
              v-model="reviewForm.content"
              rows="4"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
              :placeholder="t('mobile.reviews.contentPlaceholder')"
            ></textarea>
          </div>

          <!-- Images -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('mobile.reviews.images') }}</label>
            <label class="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
              <div class="flex flex-col items-center justify-center">
                <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p class="text-xs text-gray-500 mt-1">{{ t('common.upload') }}</p>
              </div>
              <input type="file" class="hidden" multiple accept="image/*" @change="handleImageUpload" />
            </label>
            <!-- Image Previews -->
            <div v-if="reviewForm.images.length > 0" class="flex gap-2 mt-2">
              <div v-for="(image, index) in reviewForm.images" :key="index" class="relative">
                <img :src="image" alt="Preview" class="w-16 h-16 object-cover rounded-lg" />
                <button
                  type="button"
                  @click="removeImage(index)"
                  class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                >
                  ×
                </button>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex gap-3 pt-2">
            <button
              type="submit"
              class="flex-1 bg-primary text-white py-3 rounded-xl font-semibold text-sm"
              :disabled="submitting"
            >
              {{ submitting ? t('common.submitting') : t('common.submit') }}
            </button>
            <button
              type="button"
              @click="showReviewForm = false"
              class="flex-1 border border-gray-300 text-gray-700 py-3 rounded-xl font-semibold text-sm"
            >
              {{ t('common.cancel') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="previewImage" class="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center" @click="previewImage = null">
      <img :src="previewImage" alt="Preview" class="max-w-full max-h-full object-contain" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import MobileNavbar from '~/components/MobileNavbar.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// State
const reviews = ref<any[]>([])
const totalReviews = ref(0)
const averageRating = ref(0)
const ratingDistribution = ref<Record<number, number>>({ 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 })
const currentPage = ref(1)
const totalPages = ref(1)
const loadingMore = ref(false)
const showReviewForm = ref(false)
const submitting = ref(false)
const previewImage = ref<string | null>(null)

// Current user state
const currentUserId = ref<string | null>(null)
const currentUserRole = ref<string | null>(null)

// Review form
const reviewForm = ref({
  rating: 5,
  content: '',
  images: [] as string[]
})

// Data fetching
const { data, pending, error, refresh } = await useFetch(() => `/api/v1/reviews/products/${route.params.id}/reviews`, {
  key: `mobile-reviews-${route.params.id}-${currentPage.value}`,
  lazy: true,
  params: {
    page: currentPage.value,
    page_size: 10
  },
  onResponse({ response }) {
    if (response.ok && response._data) {
      const newData = response._data
      if (newData && newData.code === 0) {
        if (currentPage.value === 1) {
          reviews.value = newData.data || []
        } else {
          reviews.value = [...reviews.value, ...(newData.data || [])]
        }
        totalReviews.value = newData.meta?.total || 0
        totalPages.value = newData.meta?.total_pages || 1
      }
    }
  },
  onRequestError({ error }) {
    console.error('Request error:', error)
  }
})

const { data: statsData, refresh: refreshStats } = await useFetch(() => `/api/v1/reviews/stats`, {
  key: `mobile-reviews-stats-${route.params.id}`,
  lazy: true,
  params: {
    product_id: route.params.id as string
  },
  onResponse({ response }) {
    if (response.ok && response._data) {
      const newData = response._data
      if (newData && newData.code === 0) {
        averageRating.value = newData.data?.average_rating || 0
        ratingDistribution.value = newData.data?.rating_distribution || { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
        totalReviews.value = newData.data?.total_reviews || 0
      }
    }
  }
})

// Computed
const canReview = computed(() => {
  const token = localStorage.getItem('token')
  if (!token) return false
  if (!currentUserId.value) return false
  return !reviews.value.some(r => r.user_id === currentUserId.value)
})

// Methods
const fetchCurrentUser = async () => {
  const token = localStorage.getItem('token')
  if (!token) return

  try {
    const { data: userData, error: userError } = await useFetch('/api/v1/auth/me', {
      key: 'mobile-current-user',
      headers: () => ({
        Authorization: `Bearer ${token}`
      })
    })

    if (userError.value) {
      console.error('Failed to fetch current user:', userError.value)
      return
    }

    if (userData.value && (userData.value as any).code === 0) {
      currentUserId.value = (userData.value as any).data?.id || null
      currentUserRole.value = (userData.value as any).data?.role || null
    }
  } catch (err) {
    console.error('Failed to fetch current user:', err)
  }
}

const loadMore = async () => {
  if (loadingMore.value || currentPage.value >= totalPages.value) return
  loadingMore.value = true
  currentPage.value++
  await refresh()
  loadingMore.value = false
}

const submitReview = async () => {
  try {
    submitting.value = true
    const token = localStorage.getItem('token')

    const response = await $fetch('/api/v1/reviews', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: {
        product_id: route.params.id,
        rating: reviewForm.value.rating,
        content: reviewForm.value.content,
        images: reviewForm.value.images
      }
    })

    if ((response as any).code === 0) {
      showReviewForm.value = false
      reviewForm.value = { rating: 5, content: '', images: [] }
      currentPage.value = 1
      await refresh()
      // Refresh stats
      await refreshStats()
    } else {
      alert((response as any).message || t('mobile.reviews.submitError'))
    }
  } catch (err: any) {
    console.error('Failed to submit review:', err)
    alert(err.message || t('mobile.reviews.submitError'))
  } finally {
    submitting.value = false
  }
}

const editReview = (review: any) => {
  reviewForm.value = {
    rating: review.rating,
    content: review.content,
    images: parseImages(review.images)
  }
  showReviewForm.value = true
}

const deleteReview = async (reviewId: string) => {
  if (!confirm(t('mobile.reviews.confirmDelete'))) return

  try {
    const token = localStorage.getItem('token')
    const response = await $fetch(`/api/v1/reviews/${reviewId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    if ((response as any).code === 0) {
      currentPage.value = 1
      await refresh()
      await refreshStats()
    } else {
      alert((response as any).message || t('mobile.reviews.deleteError'))
    }
  } catch (err: any) {
    console.error('Failed to delete review:', err)
    alert(err.message || t('mobile.reviews.deleteError'))
  }
}

const canEditReview = (review: any) => {
  const token = localStorage.getItem('token')
  if (!token) return false
  if (!currentUserId.value) return false
  if (review.user_id === currentUserId.value) return true
  const adminRoles = ['super_admin', 'admin']
  return adminRoles.includes(currentUserRole.value || '')
}

const canDeleteReview = (review: any) => {
  const token = localStorage.getItem('token')
  if (!token) return false
  if (!currentUserId.value) return false
  if (review.user_id === currentUserId.value) return true
  const adminRoles = ['super_admin', 'admin']
  return adminRoles.includes(currentUserRole.value || '')
}

const handleImageUpload = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (file.size > 5 * 1024 * 1024) {
      alert(t('mobile.reviews.imageTooLarge'))
      continue
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      reviewForm.value.images.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = (index: number) => {
  reviewForm.value.images.splice(index, 1)
}

const parseImages = (imagesJson: string) => {
  try {
    return JSON.parse(imagesJson) || []
  } catch {
    return []
  }
}

const getInitials = (userId: string) => {
  return userId.slice(0, 2).toUpperCase()
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const getRatingPercentage = (rating: number) => {
  if (totalReviews.value === 0) return 0
  return (ratingDistribution.value[rating] / totalReviews.value) * 100
}

const getRatingCount = (rating: number) => {
  return ratingDistribution.value[rating] || 0
}

const openImagePreview = (image: string) => {
  previewImage.value = image
}

// Lifecycle
onMounted(() => {
  fetchCurrentUser()
})

// SEO
useHead({
  title: computed(() => `${t('mobile.reviews.title')} - UJ`),
  meta: [
    { name: 'description', content: t('mobile.reviews.subtitle') }
  ]
})
</script>
