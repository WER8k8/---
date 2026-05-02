<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      数据分析
    </h1>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-surface rounded-xl border border-border p-6">
        <div class="text-sm text-text-secondary mb-1">
          总询盘数
        </div>
        <div class="text-3xl font-bold text-primary-900">
          {{ data?.inquiries?.total ?? '-' }}
        </div>
      </div>
      <div class="bg-surface rounded-xl border border-border p-6">
        <div class="text-sm text-text-secondary mb-1">
          待处理
        </div>
        <div class="text-3xl font-bold text-warning">
          {{ data?.inquiries?.pending ?? '-' }}
        </div>
      </div>
      <div class="bg-surface rounded-xl border border-border p-6">
        <div class="text-sm text-text-secondary mb-1">
          已联系
        </div>
        <div class="text-3xl font-bold text-accent">
          {{ data?.inquiries?.contacted ?? '-' }}
        </div>
      </div>
      <div class="bg-surface rounded-xl border border-border p-6">
        <div class="text-sm text-text-secondary mb-1">
          内容总量
        </div>
        <div class="text-3xl font-bold text-secondary">
          {{ totalContent }}
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          热门产品 TOP10
        </h2>
        <div
          v-if="data?.hot_products?.length"
          class="space-y-3"
        >
          <div
            v-for="(p, i) in data.hot_products"
            :key="p.id"
            class="flex items-center justify-between py-3 border-b border-border-light last:border-0 hover:bg-surface-hover/50 px-2 -mx-2 rounded-lg transition-colors"
          >
            <div class="flex items-center gap-3">
              <span
                class="text-sm font-bold"
                :class="i < 3 ? 'text-secondary' : 'text-text-muted'"
              >{{ i + 1 }}</span>
              <span class="text-sm text-primary-900">{{ p.name }}</span>
            </div>
            <span class="text-sm text-text-secondary">{{ p.view_count }} 次查看</span>
          </div>
        </div>
        <div
          v-else
          class="text-center text-text-muted py-8"
        >
          暂无数据
        </div>
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          热门案例 TOP10
        </h2>
        <div
          v-if="data?.hot_cases?.length"
          class="space-y-3"
        >
          <div
            v-for="(c, i) in data.hot_cases"
            :key="c.id"
            class="flex items-center justify-between py-3 border-b border-border-light last:border-0 hover:bg-surface-hover/50 px-2 -mx-2 rounded-lg transition-colors"
          >
            <div class="flex items-center gap-3">
              <span
                class="text-sm font-bold"
                :class="i < 3 ? 'text-secondary' : 'text-text-muted'"
              >{{ i + 1 }}</span>
              <span class="text-sm text-primary-900">{{ c.name }}</span>
            </div>
            <span class="text-sm text-text-secondary">{{ c.view_count }} 次查看</span>
          </div>
        </div>
        <div
          v-else
          class="text-center text-text-muted py-8"
        >
          暂无数据
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ layout: "admin" });

const data = ref<any>(null);
const totalContent = computed(() => {
  if (!data.value?.content) return "-";
  const c = data.value.content;
  return (c.total_products || 0) + (c.total_cases || 0) + (c.total_pages || 0);
});

onMounted(async () => {
  data.value = await $fetch("/api/v1/analytics/dashboard");
});
</script>
