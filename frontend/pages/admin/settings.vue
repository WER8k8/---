<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      系统设置
    </h1>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          基础信息
        </h2>
        <div class="space-y-3">
          <div class="flex justify-between py-3 border-b border-border-light">
            <span class="text-sm text-text-secondary">网站名称</span>
            <span class="text-sm font-medium text-primary-900">优丁保温建材</span>
          </div>
          <div class="flex justify-between py-3 border-b border-border-light">
            <span class="text-sm text-text-secondary">网站域名</span>
            <span class="text-sm font-medium text-primary-900">youding.com</span>
          </div>
          <div class="flex justify-between py-3 border-b border-border-light">
            <span class="text-sm text-text-secondary">后端版本</span>
            <span class="text-sm font-medium text-primary-900">v1.0.0</span>
          </div>
          <div class="flex justify-between py-3">
            <span class="text-sm text-text-secondary">前端版本</span>
            <span class="text-sm font-medium text-primary-900">Nuxt 3.21.4</span>
          </div>
        </div>
      </div>
      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          SEO 默认值
        </h2>
        <div class="space-y-3">
          <div class="flex justify-between py-3 border-b border-border-light">
            <span class="text-sm text-text-secondary">默认标题</span>
            <span class="text-sm font-medium text-primary-900">优丁保温建材 - 专业保温材料供应商</span>
          </div>
          <div class="flex justify-between py-3 border-b border-border-light">
            <span class="text-sm text-text-secondary">默认描述</span>
            <span class="text-sm font-medium text-primary-900 truncate max-w-[200px]">优丁保温建材致力于提供高品质保温材料...</span>
          </div>
          <div class="flex justify-between py-3">
            <span class="text-sm text-text-secondary">AI 模型</span>
            <span class="text-sm font-medium text-primary-900">GPT-4 (默认)</span>
          </div>
        </div>
      </div>
    </div>
    <div class="mt-6 bg-surface rounded-xl border border-border p-6 text-center text-text-muted">
      详细设置功能正在开发中，后续将支持更多配置项。
    </div>
  </div>
</template>
