/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div ref="root" class="yd-rt">
    <!-- 桌面端：正常表格 -->
    <table v-if="!isMobile" class="yd-rt__table">
      <thead><tr><th v-for="c in columns" :key="c.key">{{ c.title }}</th></tr></thead>
      <tbody><tr v-for="(row, i) in data" :key="i"><td v-for="c in columns" :key="c.key"><slot :name="c.key" :row="row" :value="row[c.key]">{{ row[c.key] }}</slot></td></tr></tbody>
    </table>
    <!-- 移动端：卡片化 -->
    <div v-else class="yd-rt__cards">
      <div v-for="(row, i) in data" :key="i" class="yd-rt__card">
        <div v-for="c in columns" :key="c.key" class="yd-rt__field">
          <span class="yd-rt__label">{{ c.title }}</span>
          <span class="yd-rt__value"><slot :name="c.key" :row="row" :value="row[c.key]">{{ row[c.key] }}</slot></span>
        </div>
      </div>
    </div>
    <div v-if="!data?.length" class="yd-rt__empty"><slot name="empty">暂无数据</slot></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
interface Column { key: string; title: string }
const props = withDefaults(defineProps<{ columns: Column[]; data: Record<string, any>[]; mobileBreakpoint?: number }>(), { mobileBreakpoint: 768 })
const root = ref<HTMLElement>()
const isMobile = ref(false)
let observer: ResizeObserver | null = null
onMounted(() => {
  const check = () => { isMobile.value = (root.value?.offsetWidth ?? window.innerWidth) < props.mobileBreakpoint }
  check()
  observer = new ResizeObserver(check)
  if (root.value) observer.observe(root.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.yd-rt__table { width: 100%; border-collapse: collapse; }
.yd-rt__table th, .yd-rt__table td { padding: 12px 16px; text-align: start; border-block-end: 1px solid #e5e7eb; }
.yd-rt__table th { font-weight: 600; background: #f9fafb; }
.yd-rt__cards { display: flex; flex-direction: column; gap: 12px; }
.yd-rt__card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
.yd-rt__field { display: flex; justify-content: space-between; padding: 6px 0; border-block-end: 1px solid #f3f4f6; }
.yd-rt__field:last-child { border-block-end: none; }
.yd-rt__label { font-weight: 600; color: #6b7280; font-size: 13px; flex-shrink: 0; margin-inline-end: 12px; }
.yd-rt__value { text-align: end; word-break: break-all; }
.yd-rt__empty { text-align: center; padding: 32px; color: #9ca3af; }
</style>
