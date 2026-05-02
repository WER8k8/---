<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      SEO 批量管理
    </h1>

    <div class="bg-surface rounded-xl border border-border p-4 mb-6">
      <div class="flex gap-4 mb-4">
        <input
          v-model="search"
          type="text"
          placeholder="搜索产品/案例/页面..."
          class="flex-1 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 bg-surface"
          @input="debouncedSearch"
        >
      </div>
      <div class="border-t border-border-light pt-4">
        <h3 class="text-sm font-semibold text-primary-900 mb-3">
          批量 SEO 规则
        </h3>
        <div class="grid grid-cols-4 gap-3">
          <div>
            <label class="block text-xs text-text-secondary mb-1">资源类型</label>
            <select
              v-model="ruleResourceType"
              class="w-full px-2 py-2 border border-border rounded-lg text-sm bg-surface"
            >
              <option value="">
                全部
              </option>
              <option value="product">
                产品
              </option>
              <option value="case">
                案例
              </option>
              <option value="page">
                页面
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-text-secondary mb-1">规则类型</label>
            <select
              v-model="ruleType"
              class="w-full px-2 py-2 border border-border rounded-lg text-sm bg-surface"
            >
              <option value="suffix_title">
                标题追加后缀
              </option>
              <option value="prefix_title">
                标题添加前缀
              </option>
              <option value="set_description">
                统一描述
              </option>
              <option value="set_keywords">
                统一关键词
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-text-secondary mb-1">规则值</label>
            <input
              v-model="ruleValue"
              type="text"
              placeholder="如: - 厂家直供"
              class="w-full px-2 py-2 border border-border rounded-lg text-sm bg-surface"
            >
          </div>
          <div class="flex items-end">
            <button
              class="w-full px-4 py-2 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-lg hover:from-secondary-600 hover:to-secondary-700 transition-all text-sm"
              @click="applyRule"
            >
              应用规则
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-surface rounded-xl border border-border overflow-hidden">
      <table class="w-full">
        <thead class="bg-surface-elevated">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">
              类型
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">
              名称
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">
              SEO 标题
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">
              SEO 描述
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">
              关键词
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-light">
          <tr
            v-for="item in list"
            :key="item.resource_type + '-' + item.resource_id"
            class="hover:bg-surface-hover transition-colors"
          >
            <td class="px-4 py-3">
              <span
                class="text-xs px-2 py-1 rounded-lg"
                :class="typeBadge(item.resource_type)"
              >{{ typeLabel(item.resource_type) }}</span>
            </td>
            <td class="px-4 py-3 text-sm font-medium text-primary-900">
              {{ item.title }}
            </td>
            <td class="px-4 py-3">
              <input
                v-model="item.current_meta_title"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-border-light rounded-md bg-surface-focus focus:border-secondary-500 focus:ring-1 focus:ring-secondary-500"
              >
            </td>
            <td class="px-4 py-3 max-w-xs">
              <input
                v-model="item.current_meta_description"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-border-light rounded-md bg-surface-focus focus:border-secondary-500 focus:ring-1 focus:ring-secondary-500"
              >
            </td>
            <td class="px-4 py-3">
              <input
                v-model="item.current_meta_keywords"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-border-light rounded-md bg-surface-focus focus:border-secondary-500 focus:ring-1 focus:ring-secondary-500"
              >
            </td>
          </tr>
          <tr v-if="!list.length">
            <td
              colspan="5"
              class="px-4 py-8 text-center text-text-muted"
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
import { ref, onMounted } from 'vue'

definePageMeta({ layout: "admin", title: "SEO批量管理" });

const search = ref("");
const list = ref<any[]>([]);
const ruleResourceType = ref("");
const ruleType = ref("suffix_title");
const ruleValue = ref("");

let debounceTimer: ReturnType<typeof setTimeout>;

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadData, 300);
}

function typeLabel(t: string) {
  const map: Record<string, string> = { product: "产品", case: "案例", page: "页面" };
  return map[t] || t;
}

function typeBadge(t: string) {
  const map: Record<string, string> = {
    product: "bg-blue-50 text-blue-700",
    case: "bg-green-50 text-green-700",
    page: "bg-purple-50 text-purple-700",
  };
  return map[t] || "bg-gray-50 text-gray-600";
}

async function loadData() {
  const params = new URLSearchParams();
  if (search.value) params.set("search", search.value);
  list.value = await $fetch(`/api/v1/seo/seo-batch-list?${params.toString()}`);
}

async function applyRule() {
  if (!ruleValue.value) { alert("请输入规则值"); return; }
  await $fetch("/api/v1/seo/seo-batch-apply-rule", {
    method: "POST",
    body: {
      resource_type: ruleResourceType.value,
      rule_type: ruleType.value,
      value: ruleValue.value,
    },
  });
  await loadData();
}

onMounted(loadData);
</script>
