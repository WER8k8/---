<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        案例管理
      </h1>
      <NuxtLink
        to="/admin/cases/edit/new"
        class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
      >
        + 新建案例
      </NuxtLink>
    </div>

    <div class="bg-surface rounded-xl border border-border">
      <div class="p-4 border-b border-border">
        <div class="flex flex-wrap items-center gap-3">
          <input
            v-model="search"
            type="text"
            placeholder="搜索案例名称..."
            class="px-4 py-2.5 bg-surface-elevated border border-border rounded-xl text-sm text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all w-64"
            @input="onSearch"
          >
          <select
            v-model="statusFilter"
            class="px-4 py-2.5 bg-surface-elevated border border-border rounded-xl text-sm text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            @change="fetchCases"
          >
            <option value="">
              全部状态
            </option>
            <option value="draft">
              草稿
            </option>
            <option value="published">
              已发布
            </option>
          </select>
        </div>
      </div>

      <table class="w-full">
        <thead class="bg-surface-elevated">
          <tr>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              项目名称
            </th>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              客户
            </th>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              施工面积
            </th>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              状态
            </th>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              浏览量
            </th>
            <th class="text-left px-6 py-4 text-sm font-semibold text-text-secondary">
              创建时间
            </th>
            <th class="text-right px-6 py-4 text-sm font-semibold text-text-secondary">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-light">
          <tr
            v-for="item in cases"
            :key="item.id"
            class="hover:bg-surface-hover/50 transition-colors"
          >
            <td class="px-6 py-4 text-sm font-medium text-primary-900">
              {{ item.project_name }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ item.client_name || '-' }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ item.construction_area || '-' }}
            </td>
            <td class="px-6 py-4">
              <span
                :class="item.status === 'published' ? 'bg-accent/10 text-accent' : 'bg-warning/10 text-warning'"
                class="px-3 py-1 rounded-full text-xs font-medium"
              >
                {{ item.status === 'published' ? '已发布' : '草稿' }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ item.view_count }}
            </td>
            <td class="px-6 py-4 text-sm text-text-muted">
              {{ formatDate(item.created_at) }}
            </td>
            <td class="px-6 py-4 text-right">
              <NuxtLink
                :to="`/admin/cases/edit/${item.id}`"
                class="text-secondary hover:text-secondary/80 text-sm font-medium mr-3"
              >
                编辑
              </NuxtLink>
              <button
                class="text-danger hover:text-danger/80 text-sm font-medium"
                @click="deleteCase(item.id)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!cases.length">
            <td
              colspan="7"
              class="px-6 py-12 text-center text-text-muted text-sm"
            >
              暂无数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: "admin",
  title: "案例管理",
});

const search = ref("");
const statusFilter = ref("");
const cases = ref<any[]>([]);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(fetchCases, 300);
}

async function fetchCases() {
  const params = new URLSearchParams();
  if (search.value) params.set("search", search.value);
  if (statusFilter.value) params.set("status", statusFilter.value);
  const { data } = await useFetch(`/api/v1/cases?${params}`);
  cases.value = (data.value as any[]) || [];
}

async function deleteCase(id: string) {
  if (!confirm("确定删除该案例？")) return;
  try {
    await $fetch(`/api/v1/cases/${id}`, { method: "DELETE" });
    cases.value = cases.value.filter((c: any) => c.id !== id);
  } catch (e) {
    alert("删除失败");
  }
}

function formatDate(d: string) {
  if (!d) return "-";
  return new Date(d).toLocaleDateString("zh-CN");
}

fetchCases();
</script>
