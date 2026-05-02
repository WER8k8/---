<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-gray-900">
      产品参数
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">导热系数 (W/m·K)</label>
        <input
          :value="modelValue?.thermal_conductivity"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="如: 0.035"
          @input="updateParam('thermal_conductivity', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">密度 (kg/m³)</label>
        <input
          :value="modelValue?.density"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="如: 120"
          @input="updateParam('density', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">抗压强度 (MPa)</label>
        <input
          :value="modelValue?.strength"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="如: 0.5"
          @input="updateParam('strength', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">单位重量 (kg/m²)</label>
        <input
          :value="modelValue?.unit_weight"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="如: 15.5"
          @input="updateParam('unit_weight', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">燃烧性能（防火等级）</label>
        <select
          :value="modelValue?.fire_rating"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          @change="updateParam('fire_rating', ($event.target as HTMLSelectElement).value)"
        >
          <option value="">
            请选择防火等级
          </option>
          <option value="A级">
            A级（不燃）
          </option>
          <option value="B1级">
            B1级（难燃）
          </option>
          <option value="B2级">
            B2级（可燃）
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">规格尺寸</label>
        <input
          :value="modelValue?.specifications_text"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
          placeholder="如: 1200×600×50mm"
          @input="updateParam('specifications_text', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </div>

    <div class="border-t border-gray-200 pt-6">
      <div class="flex items-center justify-between mb-4">
        <h4 class="text-md font-semibold text-gray-800">
          自定义参数
        </h4>
        <button
          class="inline-flex items-center px-3 py-1.5 bg-brand-blue text-white text-sm rounded-lg hover:bg-blue-800 transition-colors"
          @click="addParam"
        >
          + 添加参数
        </button>
      </div>

      <p class="text-sm text-gray-500 mb-4">
        可自由添加键值对参数，如：导热系数: 0.034、吸水率: ≤1.5%
      </p>

      <div
        v-if="customParams.length === 0"
        class="text-center py-8 bg-gray-50 rounded-lg"
      >
        <p class="text-gray-400 text-sm">
          暂无自定义参数，点击上方按钮添加
        </p>
      </div>

      <div
        v-else
        class="space-y-3"
      >
        <div
          v-for="(param, index) in customParams"
          :key="index"
          class="flex items-center gap-3 bg-gray-50 rounded-lg px-4 py-3"
        >
          <div class="flex-1 grid grid-cols-2 gap-3">
            <input
              v-model="param.key"
              class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="参数名称，如：导热系数"
              @input="syncCustomParams"
            >
            <input
              v-model="param.value"
              class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-blue focus:border-transparent"
              placeholder="参数值，如：0.034"
              @input="syncCustomParams"
            >
          </div>
          <button
            class="text-red-400 hover:text-red-600 transition-colors p-1"
            title="删除此参数"
            @click="removeParam(index)"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>

      <div
        v-if="customParams.length > 0"
        class="mt-4 p-4 bg-blue-50 rounded-lg"
      >
        <p class="text-xs text-blue-600 font-medium mb-2">
          参数预览（JSON格式）
        </p>
        <pre class="text-xs text-blue-800 font-mono whitespace-pre-wrap">{{ JSON.stringify(specificationsDict, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface ProductParams {
  density: string
  strength: string
  thermal_conductivity: string
  unit_weight: string
  fire_rating: string
  specifications_text: string
  specifications: Record<string, string>
}

interface CustomParam {
  key: string
  value: string
}

const props = defineProps<{
  modelValue: ProductParams
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: ProductParams): void
}>()

const customParams = ref<CustomParam[]>([])

function updateParam<K extends keyof ProductParams>(key: K, value: ProductParams[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

const specificationsDict = computed(() => {
  const dict: Record<string, string> = {}
  for (const param of customParams.value) {
    if (param.key.trim()) {
      dict[param.key.trim()] = param.value.trim()
    }
  }
  return dict
})

function initCustomParams() {
  const specs = props.modelValue.specifications
  if (specs && typeof specs === 'object' && Object.keys(specs).length > 0) {
    customParams.value = Object.entries(specs).map(([key, value]) => ({
      key,
      value: String(value),
    }))
  } else {
    customParams.value = []
  }
}

initCustomParams()

watch(() => props.modelValue.specifications, () => {
  initCustomParams()
}, { deep: true })

function addParam() {
  customParams.value.push({ key: '', value: '' })
}

function removeParam(index: number) {
  customParams.value.splice(index, 1)
  syncCustomParams()
}

function syncCustomParams() {
  const updated = { ...props.modelValue }
  updated.specifications = specificationsDict.value
  emit('update:modelValue', updated)
}
</script>
