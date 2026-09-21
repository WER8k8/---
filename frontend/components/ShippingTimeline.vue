/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
    <h3 class="text-lg font-bold text-gray-800 mb-4">
      {{ t('shipping.step1') || 'Shipping Timeline' }}
    </h3>

    <div class="space-y-0">
      <!-- Step 1 -->
      <div class="flex gap-4 pb-6 relative">
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center text-sm font-bold z-10 relative">
            1
          </div>
          <div class="w-0.5 flex-1 bg-green-200 mt-2" />
        </div>
        <div class="flex-1 pb-2">
          <div class="font-semibold text-gray-800">
            {{ timeline?.steps?.[0]?.title || t('shipping.step1') }}
          </div>
          <div class="text-sm text-gray-500 mt-1">
            {{ timeline?.steps?.[0]?.desc || t('shipping.step1_desc') }}
          </div>
          <div class="inline-block mt-2 px-2 py-0.5 bg-green-50 text-green-700 text-xs font-medium rounded">
            {{ timeline?.steps?.[0]?.days || t('shipping.step1_days') }}
          </div>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="flex gap-4 pb-6 relative">
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold z-10 relative">
            2
          </div>
          <div class="w-0.5 flex-1 bg-blue-200 mt-2" />
        </div>
        <div class="flex-1 pb-2">
          <div class="font-semibold text-gray-800">
            {{ timeline?.steps?.[1]?.title || t('shipping.step2') }}
          </div>
          <div class="text-sm text-gray-500 mt-1">
            {{ timeline?.steps?.[1]?.desc || t('shipping.step2_desc') }}
          </div>
          <div class="inline-block mt-2 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded">
            {{ timeline?.steps?.[1]?.days || t('shipping.step2_days') }}
          </div>
          <div
            v-if="timeline?.steps?.[1]?.badge"
            class="inline-block mt-1 ml-2 px-2 py-0.5 bg-orange-50 text-orange-700 text-xs font-medium rounded"
          >
            {{ timeline?.steps[1].badge }}
          </div>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="flex gap-4 pb-6 relative">
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center text-sm font-bold z-10 relative">
            3
          </div>
          <div class="w-0.5 flex-1 bg-purple-200 mt-2" />
        </div>
        <div class="flex-1 pb-2">
          <div class="font-semibold text-gray-800">
            {{ timeline?.steps?.[2]?.title || t('shipping.step3') }}
          </div>
          <div class="text-sm text-gray-500 mt-1">
            {{ timeline?.steps?.[2]?.desc || t('shipping.step3_desc') }}
          </div>
          <div class="inline-block mt-2 px-2 py-0.5 bg-purple-50 text-purple-700 text-xs font-medium rounded">
            {{ timeline?.steps?.[2]?.days || t('shipping.step3_days') }}
          </div>
        </div>
      </div>

      <!-- Step 4 -->
      <div class="flex gap-4">
        <div class="flex flex-col items-center">
          <div class="w-8 h-8 rounded-full bg-gray-400 text-white flex items-center justify-center text-sm font-bold z-10 relative">
            4
          </div>
        </div>
        <div class="flex-1">
          <div class="font-semibold text-gray-800">
            {{ timeline?.steps?.[3]?.title || t('shipping.step4') }}
          </div>
          <div class="text-sm text-gray-500 mt-1">
            {{ timeline?.steps?.[3]?.desc || t('shipping.step4_desc') }}
          </div>
          <div class="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded">
            {{ timeline?.steps?.[3]?.days || t('shipping.step4_days') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{
  countryCode?: string
}>()

const timeline = ref<any>(null)

const fetchTimeline = async () => {
  try {
    const res = await $fetch('/api/v1/v1/shipping/timeline', {
      params: {
        country_code: props.countryCode || route.query.country || 'US',
        merchant_id: 'default'
      }
    })
    timeline.value = res
  } catch (e) {
    console.error('Failed to fetch shipping timeline:', e)
  }
}

onMounted(() => {
  fetchTimeline()
})
</script>
