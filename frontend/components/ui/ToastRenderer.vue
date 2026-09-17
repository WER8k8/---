/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <ClientOnly>
    <Teleport to="body">
      <div class="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-2 max-w-md w-[calc(100%-2rem)] pointer-events-none">
        <TransitionGroup name="toast-slide">
          <div
            v-for="toast in appStore.toasts"
            :key="toast.id"
            class="flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium shadow-lg text-white pointer-events-auto"
            :class="typeClass(toast.type)"
          >
            <span class="font-bold flex-shrink-0">{{ iconMap[toast.type] }}</span>
            <span>{{ toast.message }}</span>
          </div>
        </TransitionGroup>
      </div>
    </Teleport>
    <template #fallback>
      <div />
    </template>
  </ClientOnly>
</template>

<script setup lang="ts">
const appStore = useAppStore()

const iconMap: Record<string, string> = {
  success: '\u2713',
  error: '\u2715',
  warning: '!',
  info: '\u2139',
}

function typeClass(type: string) {
  const map: Record<string, string> = {
    success: 'bg-green-700',
    error: 'bg-red-700',
    warning: 'bg-amber-700',
    info: 'bg-slate-700',
  }
  return map[type] || 'bg-slate-700'
}
</script>

<style scoped>
.toast-slide-enter-active {
  transition: all 0.3s ease-out;
}
.toast-slide-leave-active {
  transition: all 0.2s ease-in;
}
.toast-slide-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
