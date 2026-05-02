<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        询盘管理
      </h1>
      <button
        class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
        @click="exportCsv"
      >
        导出 Excel
      </button>
    </div>

    <div class="bg-surface rounded-xl border border-border p-4 mb-6">
      <div class="flex flex-wrap gap-4">
        <input
          v-model="search"
          type="text"
          placeholder="搜索姓名/电话/产品..."
          class="flex-1 min-w-[200px] px-4 py-2.5 bg-surface-elevated border border-border rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
          @input="debouncedSearch"
        >
        <select
          v-model="statusFilter"
          class="px-4 py-2.5 bg-surface-elevated border border-border rounded-xl focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
          @change="loadData"
        >
          <option value="">
            全部状态
          </option>
          <option value="pending">
            待处理
          </option>
          <option value="contacted">
            已联系
          </option>
          <option value="closed">
            已关闭
          </option>
          <option value="archived">
            已归档
          </option>
        </select>
      </div>
    </div>

    <div class="bg-surface rounded-xl border border-border overflow-hidden">
      <table class="w-full">
        <thead class="bg-surface-elevated">
          <tr>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              姓名
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              电话
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              产品
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              留言
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              状态
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              时间
            </th>
            <th class="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-light">
          <tr
            v-for="item in list"
            :key="item.id"
            class="hover:bg-surface-hover/50 transition-colors"
          >
            <td class="px-6 py-4 text-sm font-medium text-primary-900">
              {{ item.name }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ item.phone }}
            </td>
            <td class="px-6 py-4 text-sm text-text-secondary">
              {{ item.product || '-' }}
            </td>
            <td class="px-6 py-4 text-sm text-text-muted max-w-xs truncate">
              {{ item.message }}
            </td>
            <td class="px-6 py-4">
              <select
                :value="item.status"
                class="text-xs px-3 py-1.5 rounded-lg font-medium"
                :class="statusClass(item.status)"
                @change="updateStatus(item.id, ($event.target as HTMLSelectElement).value)"
              >
                <option
                  value="pending"
                  class="bg-surface"
                >
                  待处理
                </option>
                <option
                  value="contacted"
                  class="bg-surface"
                >
                  已联系
                </option>
                <option
                  value="closed"
                  class="bg-surface"
                >
                  已关闭
                </option>
                <option
                  value="archived"
                  class="bg-surface"
                >
                  已归档
                </option>
              </select>
            </td>
            <td class="px-6 py-4 text-sm text-text-muted">
              {{ formatTime(item.created_at) }}
            </td>
            <td class="px-6 py-4">
              <button
                class="text-danger hover:text-danger/80 text-sm font-medium transition-colors"
                @click="confirmDelete(item.id)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!list.length">
            <td
              colspan="7"
              class="px-6 py-12 text-center text-text-muted"
            >
              暂无询盘数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: "admin", title: "询盘管理" });

const search = ref("");
const statusFilter = ref("");
const list = ref<any[]>([]);

let debounceTimer: ReturnType<typeof setTimeout>;

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadData, 300);
}

function statusClass(status: string) {
  const map: Record<string, string> = {
    pending: "text-warning bg-warning/10 border-warning/20",
    contacted: "text-secondary bg-secondary/10 border-secondary/20",
    closed: "text-accent bg-accent/10 border-accent/20",
    archived: "text-text-muted bg-surface-hover border-border",
  };
  return map[status] || "";
}

function formatTime(t: string) {
  try { return new Date(t).toLocaleString("zh-CN"); } catch { return t; }
}

async function loadData() {
  const params = new URLSearchParams();
  if (search.value) params.set("search", search.value);
  if (statusFilter.value) params.set("status_filter", statusFilter.value);
  list.value = await $fetch(`/api/v1/inquiries?${params.toString()}`);
}

async function updateStatus(id: string, status: string) {
  await $fetch(`/api/v1/inquiries/${id}/status`, {
    method: "PUT",
    body: { status },
  });
  await loadData();
}

async function confirmDelete(id: string) {
  if (!confirm("确定删除此询盘？")) return;
  await $fetch(`/api/v1/inquiries/${id}`, { method: "DELETE" });
  await loadData();
}

function exportCsv() {
  const params = new URLSearchParams();
  if (statusFilter.value) params.set("status_filter", statusFilter.value);
  window.open(`/api/v1/inquiries/export?${params.toString()}`, "_blank");
}

onMounted(loadData);
</script>
