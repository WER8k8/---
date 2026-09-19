/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <!-- 手风琴标题（点击展开/收起） -->
    <button
      @click="isOpen = !isOpen"
      class="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
    >
      <span class="font-semibold text-gray-800 text-base">{{ title }}</span>
      <span
        class="text-gray-400 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      >▼</span>
    </button>

    <!-- 手风琴内容 -->
    <Transition name="accordion">
      <div
        v-if="isOpen"
        class="p-4 space-y-3"
      >
        <!-- 技术参数表格 -->
        <table
          v-if="specs && specs.length"
          class="w-full text-sm"
        >
          <thead>
            <tr class="border-b border-gray-200">
              <th class="text-left py-2 text-gray-500 font-medium">
                {{ t('product.spec_param') }}
              </th>
              <th class="text-right py-2 text-gray-500 font-medium">
                {{ t('product.spec_value') }}
              </th>
              <th class="text-right py-2 text-gray-500 font-medium">
                {{ t('product.spec_unit') }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(spec, idx) in specs"
              :key="idx"
              class="border-b border-gray-50 last:border-0"
            >
              <td class="py-2.5 text-gray-700">
                {{ spec.key }}
              </td>
              <td class="py-2.5 text-right font-semibold text-gray-900">
                {{ spec.value }}
              </td>
              <td class="py-2.5 text-right text-gray-500">
                {{ currentUnit === 'imperial' ? spec.imperial_unit : spec.metric_unit }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 证书徽章 -->
        <div
          v-if="badges && badges.length"
          class="flex flex-wrap gap-2 pt-2"
        >
          <span
            v-for="badge in badges"
            :key="badge"
            class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
          >
            ✓ {{ badge }}
          </span>
        </div>

        <!-- 无数据时显示提示 -->
        <div
          v-if="(!specs || !specs.length) && (!badges || !badges.length)"
          class="text-center text-gray-400 text-sm py-4"
        >
          {{ t('product.no_specs') || 'No specifications available' }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  title: string
  specs: Array<{ key: string; value: string; metric_unit: string; imperial_unit?: string }>
  badges: string[]
  defaultOpen?: boolean
}>()

const isOpen = ref(props.defaultOpen || false)

// 单位切换（公制/英制）
const currentUnit = ref<'metric' | 'imperial'>('metric')

const toggleUnit = () => {
  currentUnit.value = currentUnit.value === 'metric' ? 'imperial' : 'metric'
}
</script>

<style scoped>
.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.accordion-enter-from,
.accordion-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.accordion-enter-to,
.accordion-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
