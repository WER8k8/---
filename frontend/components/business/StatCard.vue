/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <Card
    :padding="padding"
    class="stat-card"
  >
    <div class="text-center relative">
      <!-- Top gradient accent bar -->
      <div
        class="absolute -top-3 left-1/2 -translate-x-1/2 w-10 h-[3px] rounded-sm"
        style="background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%); box-shadow: 0 0 6px 2px rgba(15, 118, 110, 0.25)"
      />
      <span class="block text-xs text-slate-500 uppercase tracking-wide mb-1">{{ label }}</span>
      <strong class="inline text-xl font-bold bg-gradient-to-r from-teal-700 to-green-500 bg-clip-text text-transparent">
        {{ value }}
      </strong>
      <span
        v-if="unit"
        class="text-xs text-slate-500 ml-0.5"
      >{{ unit }}</span>
    </div>
  </Card>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  label: string
  value: string | number
  unit?: string
  padding?: 'sm' | 'md'
}>(), {
  padding: 'sm',
})
</script>
