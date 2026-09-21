/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="mb-4">
    <label class="block text-sm font-semibold text-gray-700 mb-2">
      {{ label }}
      <span
        v-if="required"
        class="text-red-500"
      >*</span>
    </label>
    <div
      class="flex items-center min-h-[48px] px-4 border-1.5 border-gray-200 rounded-lg bg-white cursor-pointer transition-colors active:border-teal-600"
      @click="showPicker = true"
    >
      <span
        v-if="selectedLabel"
        class="flex-1 text-base text-gray-900"
      >{{ selectedLabel }}</span>
      <span
        v-else
        class="flex-1 text-base text-gray-400"
      >{{ placeholder }}</span>
      <span class="text-[10px] text-gray-400">&#9660;</span>
    </div>

    <Modal
      :visible="showPicker"
      title="选择地区"
      @update:visible="showPicker = $event"
    >
      <!-- 省份列表 -->
      <div
        v-if="!selectedProvince"
        class="max-h-[400px] overflow-y-auto -mx-5 -mt-5"
      >
        <button
          v-for="province in provinces"
          :key="province.name"
          class="flex items-center justify-between w-full min-h-[48px] px-5 border-b border-gray-100 text-base text-gray-900 text-left active:bg-gray-50 transition-colors"
          @click="selectProvince(province)"
        >
          <span>{{ province.name }}</span>
          <span class="text-xl text-gray-400">&#8250;</span>
        </button>
      </div>

      <!-- 城市列表 -->
      <div
        v-else
        class="max-h-[400px] overflow-y-auto -mx-5 -mt-5"
      >
        <button
          class="w-full min-h-[44px] px-5 border-b border-gray-100 text-sm text-teal-600 font-semibold text-left"
          @click="selectedProvince = null"
        >
          &#8592; 返回省份
        </button>
        <div class="px-5 py-3 text-sm font-bold text-gray-500 border-b border-gray-100">
          {{ selectedProvince.name }}
        </div>
        <button
          v-for="city in selectedProvince.cities"
          :key="city.name"
          class="w-full min-h-[48px] px-5 border-b border-gray-100 text-base text-gray-900 text-left active:bg-gray-50 transition-colors"
          @click="selectCity(city)"
        >
          {{ city.name }}
        </button>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { regions, type Province } from '~/utils/regions'

const props = withDefaults(defineProps<{
  modelValue?: string
  label?: string
  placeholder?: string
  required?: boolean
}>(), {
  modelValue: '',
  label: '项目地区',
  placeholder: '请选择省份/城市',
  required: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const showPicker = ref(false)
const selectedProvince = ref<Province | null>(null)
const selectedLabel = computed(() => props.modelValue || '')

const provinces = regions

function selectProvince(province: Province) {
  if (province.cities.length === 1) {
    emit('update:modelValue', `${province.name}${province.cities[0].name}`)
    showPicker.value = false
    selectedProvince.value = null
  } else {
    selectedProvince.value = province
  }
}

function selectCity(city: { name: string }) {
  if (selectedProvince.value) {
    emit('update:modelValue', `${selectedProvince.value.name}${city.name}`)
    showPicker.value = false
    selectedProvince.value = null
  }
}
</script>
