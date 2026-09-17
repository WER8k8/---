/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="reviews-page">
    <!-- Loading State -->
    <div v-if="loading" class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12">
      <div class="animate-pulse">
        <div class="h-8 sm:h-10 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div class="h-4 sm:h-5 bg-gray-200 rounded w-1/2 mb-8"></div>
        <div class="space-y-4">
          <div class="h-32 bg-gray-200 rounded-2xl"></div>
          <div class="h-32 bg-gray-200 rounded-2xl"></div>
          <div class="h-32 bg-gray-200 rounded-2xl"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12 text-center">
      <div class="text-red-500 text-lg sm:text-xl font-semibold mb-4">{{ error }}</div>
      <NuxtLink to="/products" class="btn-primary">{{ $t('common.backToProducts') }}</NuxtLink>
    </div>

    <!-- Reviews Content -->
    <div v-else class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12">
      <!-- Breadcrumb -->
      <nav class="mb-4 sm:mb-6">
        <ol class="flex items-center space-x-2 text-sm text-text-secondary">
          <li><NuxtLink to="/" class="hover:text-primary">{{ $t('common.home') }}</NuxtLink></li>
          <li>/</li>
          <li><NuxtLink to="/products" class="hover:text-primary">{{ $t('common.products') }}</NuxtLink></li>
          <li>/</li>
          <li><NuxtLink :to="`/products/${productId}`" class="hover:text-primary">{{ productName }}</NuxtLink></li>
          <li>/</li>
          <li class="text-text-primary font-medium">{{ $t('reviews.title') }}</li>
        </ol>
      </nav>

      <!-- Page Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 sm:mb-8">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-2">{{ $t('reviews.title') }}</h1>
          <p class="text-text-secondary">{{ $t('reviews.subtitle') }}</p>
        </div>
        <button 
          @click="showReviewForm = true" 
          class="btn-primary mt-4 sm:mt-0"
          :disabled="!canReview"
        >
          {{ $t('reviews.writeReview') }}
        </button>
      </div>

      <!-- Review Stats -->
      <div class="bg-surface-elevated rounded-2xl p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Average Rating -->
          <div class="text-center">
            <div class="text-5xl font-bold text-primary mb-2">{{ averageRating }}</div>
            <div class="flex justify-center mb-2">
              <span v-for="star in 5" :key="star" class="text-yellow-400 text-xl">
                {{ star <= Math.round(averageRating) ? '★' : '☆' }}
              </span>
            </div>
            <div class="text-text-secondary">{{ $t('reviews.basedOn', { count: totalReviews }) }}</div>
          </div>

          <!-- Rating Distribution -->
          <div class="space-y-2">
            <div v-for="rating in [5, 4, 3, 2, 1]" :key="rating" class="flex items-center gap-2">
              <span class="text-sm text-text-secondary w-8">{{ rating }}★</span>
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  class="bg-yellow-400 h-2 rounded-full" 
                  :style="{ width: `${getRatingPercentage(rating)}%` }"
                ></div>
              </div>
              <span class="text-sm text-text-secondary w-8 text-right">{{ getRatingCount(rating) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Review Form Modal -->
      <div v-if="showReviewForm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="p-6">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-2xl font-bold text-text-primary">{{ $t('reviews.writeReview') }}</h2>
              <button @click="showReviewForm = false" class="text-text-secondary hover:text-text-primary">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form @submit.prevent="submitReview" class="space-y-6">
              <!-- Rating -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('reviews.rating') }}</label>
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
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('reviews.content') }}</label>
                <textarea
                  v-model="reviewForm.content"
                  rows="4"
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  :placeholder="$t('reviews.contentPlaceholder')"
                ></textarea>
              </div>

              <!-- Images -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('reviews.images') }}</label>
                <div class="flex items-center justify-center w-full">
                  <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                    <div class="flex flex-col items-center justify-center pt-5 pb-6">
                      <svg class="w-8 h-8 mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p class="mb-2 text-sm text-gray-500"><span class="font-semibold">{{ $t('common.upload') }}</span></p>
                      <p class="text-xs text-gray-500">PNG, JPG (MAX. 5MB)</p>
                    </div>
                    <input type="file" class="hidden" multiple accept="image/*" @change="handleImageUpload" />
                  </label>
                </div>
                <!-- Image Previews -->
                <div v-if="reviewForm.images.length > 0" class="flex gap-2 mt-4">
                  <div v-for="(image, index) in reviewForm.images" :key="index" class="relative">
                    <img :src="image" alt="Preview" class="w-20 h-20 object-cover rounded-lg" />
                    <button
                      type="button"
                      @click="removeImage(index)"
                      class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>

              <!-- Submit Button -->
              <div class="flex gap-4">
                <button
                  type="submit"
                  class="btn-primary flex-1"
                  :disabled="submitting"
                >
                  {{ submitting ? $t('common.submitting') : $t('common.submit') }}
                </button>
                <button
                  type="button"
                  @click="showReviewForm = false"
                  class="btn-outline"
                >
                  {{ $t('common.cancel') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Reviews List -->
      <div class="space-y-6">
        <div v-if="reviews.length === 0" class="text-center py-12 text-text-secondary">
          {{ $t('reviews.noReviews') }}
        </div>

        <div v-for="review in reviews" :key="review.id" class="bg-surface-elevated rounded-2xl p-6">
          <div class="flex justify-between items-start mb-4">
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-semibold">
                {{ getInitials(review.user_id) }}
              </div>
              <div>
                <div class="font-semibold text-text-primary">{{ $t('reviews.user') }} {{ review.user_id.slice(0, 8) }}</div>
                <div class="text-sm text-text-secondary">{{ formatDate(review.created_at) }}</div>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <span v-for="star in 5" :key="star" class="text-yellow-400">
                {{ star <= review.rating ? '★' : '☆' }}
              </span>
            </div>
          </div>

          <p class="text-text-primary mb-4">{{ review.content }}</p>

          <!-- Review Images -->
          <div v-if="review.images" class="flex gap-2 mb-4">
            <img 
              v-for="(image, index) in parseImages(review.images)" 
              :key="index" 
              :src="image" 
              alt="Review image" 
              class="w-20 h-20 object-cover rounded-lg cursor-pointer hover:opacity-80"
              @click="openImagePreview(image)"
            />
          </div>

          <!-- Review Actions -->
          <div class="flex items-center gap-4 text-sm">
            <button 
              v-if="canEditReview(review)" 
              @click="editReview(review)"
              class="text-primary hover:text-primary-dark"
            >
              {{ $t('common.edit') }}
            </button>
            <button 
              v-if="canDeleteReview(review)" 
              @click="deleteReview(review.id)"
              class="text-red-500 hover:text-red-700"
            >
              {{ $t('common.delete') }}
            </button>
            <span v-if="review.status === 'pending'" class="text-yellow-600">{{ $t('reviews.pending') }}</span>
            <span v-if="review.status === 'rejected'" class="text-red-600">{{ $t('reviews.rejected') }}</span>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-8">
          <button
            v-for="page in totalPages"
            :key="page"
            @click="currentPage = page"
            :class="[
              'px-4 py-2 rounded-lg',
              currentPage === page ? 'bg-primary text-white' : 'bg-surface-elevated text-text-primary hover:bg-surface-hover'
            ]"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="previewImage" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click="previewImage = null">
      <img :src="previewImage" alt="Preview" class="max-w-full max-h-full object-contain" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { getAuthToken } = useApi()

// State
const loading = ref(true)
const error = ref(null)
const productId = ref(route.params.id)
const productName = ref('')
const reviews = ref([])
const totalReviews = ref(0)
const averageRating = ref(0)
const ratingDistribution = ref({ 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 })
const currentPage = ref(1)
const totalPages = ref(1)
const showReviewForm = ref(false)
const submitting = ref(false)
const previewImage = ref(null)

// Current user state
const currentUserId = ref<string | null>(null)
const currentUserRole = ref<string | null>(null)

// Review form
const reviewForm = ref({
  rating: 5,
  content: '',
  images: []
})

// Computed
const canReview = computed(() => {
  const token = getAuthToken()
  if (!token) return false
  if (!currentUserId.value) return false
  return !reviews.value.some(r => r.user_id === currentUserId.value)
})

// Methods
const fetchCurrentUser = async () => {
  const token = getAuthToken()
  if (!token) return

  try {
    const { request } = useApi()
    const user = await request<{ id: string; role: string }>('/auth/me')
    if (user) {
      currentUserId.value = user.id
      currentUserRole.value = user.role
    }
  } catch (err) {
    console.error('Failed to fetch current user:', err)
  }
}

const fetchReviews = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await $fetch(`/api/v1/reviews/products/${productId.value}/reviews`, {
      params: {
        page: currentPage.value,
        page_size: 10
      }
    })

    if (response.code === 0) {
      reviews.value = response.data
      totalReviews.value = response.meta.total
      totalPages.value = response.meta.total_pages
    } else {
      error.value = response.message || t('reviews.fetchError')
    }
  } catch (err) {
    error.value = err.message || t('reviews.fetchError')
  } finally {
    loading.value = false
  }
}

const fetchReviewStats = async () => {
  try {
    const response = await $fetch(`/api/v1/reviews/stats`, {
      params: {
        product_id: productId.value
      }
    })

    if (response.code === 0) {
      averageRating.value = response.data.average_rating
      ratingDistribution.value = response.data.rating_distribution
      totalReviews.value = response.data.total_reviews
    }
  } catch (err) {
    console.error('Failed to fetch review stats:', err)
  }
}

const submitReview = async () => {
  try {
    submitting.value = true

    const payload = {
      product_id: productId.value,
      rating: reviewForm.value.rating,
      content: reviewForm.value.content,
      images: reviewForm.value.images
    }

    const response = await $fetch('/api/v1/reviews', {
      method: 'POST',
      body: payload
    })

    if (response.code === 0) {
      showReviewForm.value = false
      reviewForm.value = { rating: 5, content: '', images: [] }
      await fetchReviews()
      await fetchReviewStats()
    } else {
      alert(response.message || t('reviews.submitError'))
    }
  } catch (err) {
    alert(err.message || t('reviews.submitError'))
  } finally {
    submitting.value = false
  }
}

const editReview = (review) => {
  reviewForm.value = {
    rating: review.rating,
    content: review.content,
    images: parseImages(review.images)
  }
  showReviewForm.value = true
}

const deleteReview = async (reviewId) => {
  if (!confirm(t('reviews.confirmDelete'))) {
    return
  }

  try {
    const response = await $fetch(`/api/v1/reviews/${reviewId}`, {
      method: 'DELETE'
    })

    if (response.code === 0) {
      await fetchReviews()
      await fetchReviewStats()
    } else {
      alert(response.message || t('reviews.deleteError'))
    }
  } catch (err) {
    alert(err.message || t('reviews.deleteError'))
  }
}

const canEditReview = (review) => {
  if (!getAuthToken()) return false
  if (!currentUserId.value) return false
  if (review.user_id === currentUserId.value) return true
  const adminRoles = ['super_admin', 'admin']
  return adminRoles.includes(currentUserRole.value || '')
}

const canDeleteReview = (review) => {
  if (!getAuthToken()) return false
  if (!currentUserId.value) return false
  if (review.user_id === currentUserId.value) return true
  const adminRoles = ['super_admin', 'admin']
  return adminRoles.includes(currentUserRole.value || '')
}

const handleImageUpload = (event) => {
  const files = event.target.files
  if (!files) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (file.size > 5 * 1024 * 1024) {
      alert(t('reviews.imageTooLarge'))
      continue
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      reviewForm.value.images.push(e.target.result)
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = (index) => {
  reviewForm.value.images.splice(index, 1)
}

const parseImages = (imagesJson) => {
  try {
    return JSON.parse(imagesJson) || []
  } catch {
    return []
  }
}

const getInitials = (userId) => {
  return userId.slice(0, 2).toUpperCase()
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const getRatingPercentage = (rating) => {
  if (totalReviews.value === 0) return 0
  return (ratingDistribution.value[rating] / totalReviews.value) * 100
}

const getRatingCount = (rating) => {
  return ratingDistribution.value[rating] || 0
}

const openImagePreview = (image) => {
  previewImage.value = image
}

// Lifecycle
onMounted(() => {
  fetchCurrentUser()
  fetchReviews()
  fetchReviewStats()
})

// Watch for page changes
watch(currentPage, () => {
  fetchReviews()
})
</script>

<style scoped>
.reviews-page {
  min-height: 100vh;
}

.bg-surface-elevated {
  background-color: #f8fafc;
}

.text-text-primary {
  color: #1e293b;
}

.text-text-secondary {
  color: #64748b;
}

.btn-primary {
  @apply bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors;
}

.btn-outline {
  @apply border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}
</style>
