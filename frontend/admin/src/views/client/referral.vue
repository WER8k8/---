/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="呼朋唤友" subtitle="分享邀请链接，好友首单付费后获得 AI 流量奖励" surface="elevated">
  <div class="client-referral coachpro-tertiary coachpro-tertiary--client p-4 max-w-xl mx-auto">
    <template v-if="loading">
      <SkeletonCard variant="kpi" />
    </template>
    <template v-else>
      <a-card size="small">
        <div class="mb-3 text-sm text-gray-600">我的邀请码</div>
        <div class="text-2xl font-mono font-bold tracking-widest mb-4">{{ code || '—' }}</div>
        <a-input-group compact>
          <a-input :value="inviteLink" readonly style="width: calc(100% - 88px)" />
          <a-button type="primary" @click="copyLink">复制链接</a-button>
        </a-input-group>
        <a-statistic class="mt-4" title="累计邀请" :value="totalReferred" />
      </a-card>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { apiGet } from '@/utils/api';

const loading = ref(false)
const code = ref('')
const inviteLink = ref('')
const totalReferred = ref(0)

async function load() {
  loading.value = true
  try {
    const d = await apiGet('/referral/my-code')
    code.value = d.code || ''
    inviteLink.value = d.invite_link || ''
    totalReferred.value = d.total_referred ?? 0
  } catch (e: unknown) {
    message.error((e as Error)?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function copyLink() {
  if (!inviteLink.value) return
  navigator.clipboard.writeText(inviteLink.value).then(() => message.success('已复制邀请链接'))
}

onMounted(load)
</script>
