<template>
  <Card class="p-5">
    <h2 class="text-lg font-semibold text-gray-900 mb-4">运费快速测算</h2>

    <!-- 距离输入 -->
    <div class="mb-4">
      <label class="block text-sm font-semibold text-gray-700 mb-2">工地距离（公里）</label>
      <Input v-model.number="localDistance" type="number" placeholder="例如 50" />
      <p v-if="distanceHint" class="mt-1 text-xs text-gray-400">{{ distanceHint }}</p>
    </div>

    <!-- 采购量滑块 -->
    <div class="mb-4">
      <label class="flex justify-between items-center mb-2 text-sm font-semibold text-gray-700">
        <span>采购量（立方）</span>
        <span class="text-lg font-bold text-teal-600">{{ localQuantity || 0 }}m³</span>
      </label>
      <input
        type="range"
        min="1"
        max="500"
        step="1"
        :value="localQuantity || 0"
        class="w-full h-1.5 rounded-full bg-gray-200 appearance-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-7 [&::-webkit-slider-thumb]:h-7
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-teal-600
          [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:transition-transform
          [&::-webkit-slider-thumb]:active:scale-115"
        @input="handleSliderChange"
      />
      <div class="flex justify-between mt-1 text-xs text-gray-400">
        <span>1m³</span>
        <span>500m³</span>
      </div>
      <div v-if="hasDiscount" class="mt-2 px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold inline-block">已享批量优惠 -¥8/m³</div>
    </div>

    <!-- 预估结果 -->
    <Transition name="slide-up">
      <div v-if="estimatedPrice !== null" class="mt-4 p-4 rounded-lg bg-teal-50 text-center">
        <div class="text-sm text-gray-500 mb-2">预估到场价</div>
        <div class="mb-2">
          <PriceDisplay :amount="estimatedPrice" unit="m³" large />
        </div>
        <div class="text-xs text-gray-400">实际报价以当天调度确认为准</div>
        <div v-if="hasDiscount" class="mt-3 px-3 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold inline-block">批量优惠 ¥8/m³</div>
      </div>
    </Transition>
  </Card>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  factoryPrice?: number
  modelDistance?: number | null
  modelQuantity?: number | null
}>(), {
  factoryPrice: 0,
  modelDistance: null,
  modelQuantity: null
})

const emit = defineEmits<{
  'update:modelDistance': [value: number | null]
  'update:modelQuantity': [value: number | null]
  'calculate': [result: number]
}>()

const localDistance = ref<number | null>(props.modelDistance ?? null)
const localQuantity = ref<number | null>(props.modelQuantity ?? null)
const estimatedPrice = ref<number | null>(null)

const hasDiscount = computed(() => (localQuantity.value ?? 0) >= 100)

const distanceHint = computed(() => {
  if (!localDistance.value) return ''
  const freight = (localDistance.value * 1.5).toFixed(2)
  return `预估运费 ¥${freight}`
})

function calculate() {
  const km = localDistance.value ?? 0
  const vol = localQuantity.value ?? 0
  const discount = vol >= 100 ? 8 : 0
  const result = Math.round((props.factoryPrice + km * 1.5 - discount) * 100) / 100
  estimatedPrice.value = result
  emit('calculate', result)
}

watch(localDistance, (val) => {
  emit('update:modelDistance', val)
  calculate()
})

watch(localQuantity, (val) => {
  emit('update:modelQuantity', val)
  calculate()
})

function handleSliderChange(e: Event) {
  const target = e.target as HTMLInputElement
  localQuantity.value = Number(target.value)
}
</script>

<style scoped>
.slide-up-enter-active { transition: all 0.3s ease-out; }
.slide-up-leave-active { transition: all 0.2s ease-in; }
.slide-up-enter-from { opacity: 0; transform: translateY(8px); }
.slide-up-leave-to { opacity: 0; transform: translateY(8px); }
</style>
