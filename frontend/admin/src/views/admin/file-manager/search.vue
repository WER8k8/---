<template>
  <YdPage title="全局检索" subtitle="在文件概览收藏路径内做关键词过滤" surface="elevated">
    <template #actions>
      <router-link to="/admin/file-manager">
        <a-button type="primary">去维护收藏</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-input-search
      v-model:value="q"
      placeholder="过滤收藏路径"
      allow-clear
      style="max-width: 420px"
    />

    <a-list
      v-if="filtered.length"
      bordered
      :data-source="filtered"
      size="small"
    >
      <template #renderItem="{ item }">
        <a-list-item>
          <span class="mono">{{ item }}</span>
        </a-list-item>
      </template>
    </a-list>
    <a-empty
      v-else
      description="无匹配项或尚未添加收藏"
    />
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';

const STORAGE_KEY = 'admin-file-manager-bookmarks';
const q = ref('');
const bookmarks = ref<string[]>([]);

const filtered = computed(() => {
  const s = q.value.trim().toLowerCase();
  if (!s) return bookmarks.value;
  return bookmarks.value.filter((b) => b.toLowerCase().includes(s));
});

onMounted(async () => {
  try { await apiGet('/files'); } catch { /* 空状态 */ }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    bookmarks.value = raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    bookmarks.value = [];
  }
});
</script>

<style scoped>
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
}
</style>
