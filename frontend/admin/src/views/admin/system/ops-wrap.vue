<template>
  <YdPage title="运维收尾批处理" subtitle="到期冻结 · AI 成本归集 · 发布队列（蜂群收尾一键触发）" surface="elevated">
    <template #actions>
      <a-space>
        <a-button type="primary" :loading="running" @click="runAll(false)">执行全部</a-button>
        <a-button :loading="running" @click="runAll(true)">演练（dry-run）</a-button>
      </a-space>
    </template>

    <a-card v-if="result" title="执行结果" size="small">
      <pre class="text-xs overflow-auto max-h-96">{{ JSON.stringify(result, null, 2) }}</pre>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiPost } from '@/utils/api'

const running = ref(false)
const result = ref<Record<string, unknown> | null>(null)

async function runAll(dryRun: boolean) {
  running.value = true
  try {
    result.value = await apiPost(`/ops/jobs/run-all?dry_run=${dryRun}&publish_limit=30`)
    message.success(dryRun ? '演练完成' : '批处理完成')
  } catch (e: unknown) {
    message.error((e as Error)?.message || '执行失败')
  } finally {
    running.value = false
  }
}
</script>
