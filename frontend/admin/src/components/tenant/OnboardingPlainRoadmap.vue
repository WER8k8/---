/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div v-if="phases.length" class="onboarding-roadmap rounded-2xl border border-slate-100 bg-white p-5">
    <div class="mb-4">
      <h2 class="text-base font-bold text-slate-900">{{ title }}</h2>
      <p v-if="subtitle" class="text-xs text-slate-500 mt-1">{{ subtitle }}</p>
    </div>

    <div v-for="phase in phases" :key="phase.id" class="roadmap-phase mb-4 last:mb-0">
      <div class="flex items-start justify-between gap-2 mb-2">
        <div>
          <p class="text-sm font-semibold text-slate-800">{{ phase.title }}</p>
          <p class="text-xs text-slate-500">{{ phase.summary }}</p>
        </div>
        <a-tag :color="phase.completed ? 'success' : phase.done > 0 ? 'processing' : 'default'" class="shrink-0">
          {{ phase.done }}/{{ phase.total }}
        </a-tag>
      </div>

      <ul class="space-y-2 pl-1">
        <li
          v-for="item in phase.items"
          :key="item.key"
          class="flex items-start justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2"
        >
          <div class="min-w-0 flex items-start gap-2">
            <YdCheckMark class="mt-0.5 shrink-0" :kind="statusKind(item.status)" />
            <div>
              <p class="text-sm text-slate-800">
                {{ item.title }}
                <span v-if="item.optional" class="text-xs text-slate-400">（可稍后）</span>
              </p>
              <p class="text-xs text-slate-500">{{ item.detail }}</p>
            </div>
          </div>
          <a-button
            v-if="item.route && item.status !== 'done'"
            size="small"
            type="link"
            class="shrink-0 px-0"
            @click="go(item.route)"
          >
            去弄
          </a-button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { YdCheckMark } from '@/components/youding'

export interface RoadmapChecklistItem {
  key: string
  title: string
  detail?: string
  status: string
  route?: string
  optional?: boolean
}

export interface RoadmapPhase {
  id: string
  title: string
  summary?: string
  done: number
  total: number
  completed: boolean
  items: RoadmapChecklistItem[]
}

withDefaults(
  defineProps<{
    phases: RoadmapPhase[]
    title?: string
    subtitle?: string
  }>(),
  {
    title: '开户后怎么走',
    subtitle: '按顺序做，不用懂电脑术语，点「去弄」就行',
  },
)

const router = useRouter()

function statusKind(status: string): 'pass' | 'warn' | 'pending' {
  if (status === 'done') return 'pass'
  if (status === 'partial') return 'warn'
  return 'pending'
}

function go(route: string) {
  const [path, hash] = route.split('#')
  router.push(hash ? { path, hash: `#${hash}` } : path)
}
</script>
