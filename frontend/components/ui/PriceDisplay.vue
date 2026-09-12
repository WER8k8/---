<template>
  <span :class="[
    'inline-flex items-baseline text-gray-900 font-bold',
    { 'text-2xl bg-gradient-to-r from-teal-600 to-cyan-600 bg-clip-text text-transparent': large },
    { 'line-through text-gray-400 font-normal text-sm': strikethrough }
  ]">
    <span class="text-[0.7em]">¥</span>
    <span class="">{{ formattedAmount }}</span>
    <span v-if="unit" class="text-[0.6em] font-normal text-gray-500 ml-0.5">/{{ unit }}</span>
  </span>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  amount: number
  unit?: string
  large?: boolean
  strikethrough?: boolean
}>(), {
  amount: 0,
  unit: '',
  large: false,
  strikethrough: false
})

const formattedAmount = computed(() => {
  return props.amount.toFixed(2)
})
</script>
