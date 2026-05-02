<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      LLMs.txt 生成器
    </h1>
    <p class="text-sm text-text-secondary mb-6">
      为AI搜索引擎（如GPT、Claude、Gemini等）生成结构化网站描述文件，
      提升AI搜索场景下的品牌曝光和内容理解准确度。
    </p>
    <LLMSTxtGenerator />
  </div>
</template>

<script setup lang="ts">
import LLMSTxtGenerator from '~/components/seo/LLMSTxtGenerator.vue'
definePageMeta({ layout: 'admin' })
</script>
