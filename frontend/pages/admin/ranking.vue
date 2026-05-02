<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      关键词排名
    </h1>
    <div
      v-if="loading"
      class="text-center py-12 text-text-muted"
    >
      加载中...
    </div>
    <div
      v-else-if="error"
      class="text-center py-12 text-danger"
    >
      {{ error }}
    </div>
    <template v-else>
      <div
        v-if="groups && groups.length"
        class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
      >
        <div
          v-for="g in groups"
          :key="g.group"
          class="bg-surface rounded-xl border border-border p-6"
        >
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-primary-900">
              {{ g.group }}
            </h3>
            <span class="text-xs text-text-muted">{{ g.ranked }}/{{ g.count }}</span>
          </div>
          <div class="w-full bg-surface-elevated rounded-full h-2.5">
            <div
              class="bg-gradient-to-r from-secondary-500 to-secondary-600 h-2.5 rounded-full"
              :style="{ width: (g.count ? (g.ranked / g.count) * 100 : 0) + '%' }"
            />
          </div>
        </div>
      </div>
      <div
        v-else
        class="bg-surface rounded-xl border border-border p-6 text-center text-text-muted"
      >
        暂无关键词分组数据
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: 'admin' })

interface KeywordGroup {
  group: string
  count: number
  ranked: number
}

const groups = ref<KeywordGroup[] | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/seo/keyword-groups', {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`请求失败: ${res.status}`)
    groups.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
