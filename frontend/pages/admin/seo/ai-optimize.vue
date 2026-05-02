<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      AI 内容优化
    </h1>

    <div class="bg-surface rounded-xl border border-border p-6 mb-6">
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-primary-900 mb-1.5">优化类型</label>
          <select
            v-model="form.opt_type"
            class="w-full px-3 py-2.5 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 bg-surface"
          >
            <option value="title">
              Meta 标题
            </option>
            <option value="description">
              Meta 描述
            </option>
            <option value="alt_text">
              图片 Alt 文本
            </option>
            <option value="content">
              正文内容
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-primary-900 mb-1.5">AI 模型</label>
          <select
            v-model="form.model"
            class="w-full px-3 py-2.5 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 bg-surface"
          >
            <option value="deepseek-chat">
              DeepSeek Chat
            </option>
            <option value="gpt-4o">
              GPT-4o
            </option>
          </select>
        </div>
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-primary-900 mb-1.5">关键词（逗号分隔）</label>
        <input
          v-model="keywordsInput"
          type="text"
          placeholder="如: 岩棉板, 保温材料, 厂家直销"
          class="w-full px-3 py-2.5 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 bg-surface"
        >
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-primary-900 mb-1.5">原始内容</label>
        <textarea
          v-model="form.content"
          rows="6"
          class="w-full px-3 py-2.5 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary-500 bg-surface"
          placeholder="输入要优化的内容..."
        />
      </div>
      <button
        :disabled="loading || !form.content || !keywordsInput"
        class="px-6 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-lg hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 transition-all"
        @click="optimize"
      >
        {{ loading ? '优化中...' : '开始优化' }}
      </button>
      <p
        v-if="!apiKeySet"
        class="text-xs text-warning mt-2"
      >
        ⚠️ AI_DEEPSEEK_API_KEY 未配置，请设置环境变量后使用
      </p>
    </div>

    <div
      v-if="result"
      class="bg-surface rounded-xl border border-border p-6"
    >
      <h2 class="text-lg font-semibold text-primary-900 mb-4">
        优化结果
      </h2>
      <div class="bg-accent/10 border border-accent/20 rounded-lg p-4 mb-4">
        <div class="text-sm text-accent">
          <span
            v-for="(change, i) in result.changes"
            :key="i"
            class="mr-3"
          >✓ {{ change }}</span>
        </div>
        <div class="text-xs text-accent/80 mt-1">
          消耗 tokens: {{ result.token_usage }} | 成本: ¥{{ result.cost }}
        </div>
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-primary-900 mb-1.5">技术参数保留</label>
        <span
          :class="result.technical_params_preserved ? 'text-accent' : 'text-danger'"
          class="text-sm font-medium"
        >
          {{ result.technical_params_preserved ? '✓ 已保留' : '✗ 有参数丢失（已自动恢复）' }}
        </span>
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-primary-900 mb-1.5">优化后内容</label>
        <div class="p-4 bg-surface-elevated rounded-lg text-sm text-primary-900 whitespace-pre-wrap">
          {{ result.optimized_content }}
        </div>
      </div>
    </div>

    <div
      v-if="error"
      class="bg-danger/10 border border-danger/20 rounded-lg p-4 text-danger text-sm mt-4"
    >
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: "admin" });

const form = ref({
  content: "",
  opt_type: "content",
  keywords: [] as string[],
  model: "deepseek-chat",
});
const keywordsInput = ref("");
const loading = ref(false);
const result = ref<any>(null);
const error = ref("");
const apiKeySet = ref(true);

onMounted(async () => {
  try {
    await $fetch("/api/v1/seo/extract-params", { method: "POST", body: { content: "test" } });
  } catch (e: any) {
    if (e?.data?.detail?.includes("API key") || e?.data?.detail?.includes("key")) {
      apiKeySet.value = false;
    }
  }
});

async function optimize() {
  loading.value = true;
  error.value = "";
  result.value = null;
  const keywords = keywordsInput.value.split(",").map(k => k.trim()).filter(Boolean);
  try {
    result.value = await $fetch("/api/v1/seo/optimize-content", {
      method: "POST",
      body: { ...form.value, keywords },
    });
  } catch (e: any) {
    error.value = e?.data?.detail || "优化失败，请检查API配置";
  } finally {
    loading.value = false;
  }
}
</script>
