/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="产业带 SEO 词库" subtitle="大城主材 · 河间配套" surface="elevated">
    <a-alert
      type="info"
      show-icon
      class="mb-4"
      :message="preview?.honest_note || '词库为产业带参考，请对照自家产品核对后再用'"
    />

    <a-card title="与你相关的产业带" class="mb-4" :loading="loading">
      <p v-if="preview?.region_label" class="text-sm mb-2">产地标签：{{ preview.region_label }}</p>
      <p v-if="preview?.primary_product" class="text-sm mb-3">主营：{{ preview.primary_product }}</p>
      <div v-for="belt in belts" :key="String(belt.belt_id)" class="belt-block">
        <h3 class="text-base font-medium">{{ belt.label }}</h3>
        <p class="text-xs text-gray-500 mt-1">产品词</p>
        <div class="tags">
          <a-tag v-for="p in belt.products" :key="p">{{ p }}</a-tag>
        </div>
        <p class="text-xs text-gray-500 mt-2">排名/地域词</p>
        <div class="tags">
          <a-tag v-for="k in belt.ranking_keywords" :key="k" color="blue">{{ k }}</a-tag>
        </div>
      </div>
    </a-card>

    <a-space>
      <a-button type="primary" :loading="seeding" @click="seed">导入到 SEO 矩阵</a-button>
      <a-button @click="router.push('/client/export-quote')">去出口报价 →</a-button>
    </a-space>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import { previewSeoKeywords, seedSeoKeywords } from '@/api/cross-border';

const router = useRouter();
const loading = ref(false);
const seeding = ref(false);
const preview = ref<Record<string, unknown> | null>(null);

const belts = computed(() => {
  const b = preview.value?.belts;
  return Array.isArray(b) ? b : [];
});

async function load() {
  loading.value = true;
  try {
    const res = await previewSeoKeywords();
    preview.value = res as Record<string, unknown>;
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

async function seed() {
  seeding.value = true;
  try {
    await seedSeoKeywords('all');
    message.success('词库已提交入库');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '入库失败');
  } finally {
    seeding.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.belt-block {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e2e8f0;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}
</style>
