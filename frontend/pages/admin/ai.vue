<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      AI 工具
    </h1>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <NuxtLink
        to="/admin/seo/content-optimizer"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover hover:-translate-y-0.5 transition-all block"
      >
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          AI 内容优化
        </h2>
        <p class="text-sm text-text-secondary">
          使用 AI 优化页面标题、描述和正文内容，提升 SEO 表现。
        </p>
      </NuxtLink>
      <NuxtLink
        to="/admin/seo/llms-txt"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover hover:-translate-y-0.5 transition-all block"
      >
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          LLMs.txt 生成
        </h2>
        <p class="text-sm text-text-secondary">
          生成 LLMs.txt 文件，帮助 AI 模型更好地理解网站内容结构。
        </p>
      </NuxtLink>
      <NuxtLink
        to="/admin/seo/site-audit"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover hover:-translate-y-0.5 transition-all block"
      >
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          站点审计
        </h2>
        <p class="text-sm text-text-secondary">
          对网站进行全面 SEO 审计，发现并修复潜在问题。
        </p>
      </NuxtLink>
      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          更多 AI 工具
        </h2>
        <p class="text-sm text-text-muted">
          更多 AI 驱动的功能正在开发中，敬请期待。
        </p>
      </div>
    </div>
  </div>
</template>
