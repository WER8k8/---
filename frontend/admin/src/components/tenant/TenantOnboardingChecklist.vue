/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div v-if="checklist.length" class="rounded-2xl border border-gray-100 bg-white p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-bold text-gray-900">{{ title }}</h2>
      <span class="text-xs text-gray-500">{{ doneCount }}/{{ checklist.length }} 已完成</span>
    </div>
    <ul class="space-y-3">
      <li
        v-for="item in checklist"
        :key="item.key"
        class="flex items-start gap-3 rounded-xl border border-gray-50 p-3"
      >
        <YdCheckMark class="mt-0.5" :kind="statusKind(item.status)" :aria-label="item.status" />
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-gray-900">{{ item.title }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ item.detail }}</p>
          <RouterLink
            v-if="linkFor(item.key)"
            :to="linkFor(item.key)"
            class="inline-block mt-2 text-xs text-primary-600 hover:underline"
          >
            {{ linkLabel(item.key) }} →
          </RouterLink>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { YdCheckMark } from '@/components/youding'

export interface ChecklistItem {
  key: string
  title: string
  status: string
  detail?: string
}

const props = withDefaults(
  defineProps<{
    checklist: ChecklistItem[]
    title?: string
  }>(),
  { title: '开户清单' },
)

const doneCount = computed(() =>
  props.checklist.filter(c => c.status === 'done').length,
)

function statusKind(status: string): 'pass' | 'warn' | 'pending' {
  if (status === 'done') return 'pass'
  if (status === 'partial') return 'warn'
  return 'pending'
}

function linkFor(key: string): string {
  const map: Record<string, string> = {
    site: '/client/onboarding',
    domain: '/client/billing',
    product: '/client/products',
    publish: '/client/queues/publish',
    platforms: '/client/distribute',
    storage: '/client/settings',
    ai: '/client/ai-scenarios',
    egress: '/client/egress',
    inquiry_im: '/inquiries/im-routing',
    wecom_push: '/inquiries/im-routing#wecom-push',
    douyin_worker: '/sales/auto-negotiator',
  }
  return map[key] || ''
}

function linkLabel(key: string): string {
  const map: Record<string, string> = {
    site: '去做官网',
    domain: '去绑网址',
    product: '去上架产品',
    publish: '去看发布队列',
    platforms: '去绑抖音等平台',
    storage: '去设视频存放',
    ai: '去看写文案',
    egress: '去看发布网络',
    inquiry_im: '去设客户留言',
    wecom_push: '去设销售通知',
    douyin_worker: '去看自动谈单',
  }
  return map[key] || '去弄'
}
</script>
