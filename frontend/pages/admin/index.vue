<template>
  <div>
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-primary-900 mb-2">
        管理后台
      </h1>
      <p class="text-text-secondary">
        欢迎回来，这里是优丁建材内容管理系统
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <NuxtLink
        to="/admin/products"
        class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          📦
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          产品管理
        </h2>
        <p class="text-sm text-text-secondary">
          管理产品目录、分类、规格参数和技术文档
        </p>
      </NuxtLink>

      <NuxtLink
        to="/admin/cases"
        class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          🏗️
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          工程案例
        </h2>
        <p class="text-sm text-text-secondary">
          管理工程案例展示、项目详情和客户反馈
        </p>
      </NuxtLink>

      <NuxtLink
        to="/admin/content"
        class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          📝
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          内容管理
        </h2>
        <p class="text-sm text-text-secondary">
          管理新闻资讯、技术文章和页面内容
        </p>
      </NuxtLink>

      <NuxtLink
        to="/admin/inquiries"
        class="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          💬
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          询盘管理
        </h2>
        <p class="text-sm text-text-secondary">
          处理客户询盘、留言和咨询信息
        </p>
      </NuxtLink>

      <NuxtLink
        to="/admin/analytics"
        class="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl border border-cyan-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          📊
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          数据分析
        </h2>
        <p class="text-sm text-text-secondary">
          查看网站访问量、热门产品和用户行为分析
        </p>
      </NuxtLink>

      <NuxtLink
        to="/admin/seo"
        class="bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl border border-pink-200 p-6 hover:shadow-lg transition-all hover:-translate-y-1 group"
      >
        <div class="text-4xl mb-4 group-hover:scale-110 transition-transform">
          🔍
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          SEO优化
        </h2>
        <p class="text-sm text-text-secondary">
          关键词管理、站点审计和AI内容优化
        </p>
      </NuxtLink>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <NuxtLink
        to="/admin/seo/llms-txt"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="flex items-start space-x-4">
          <div class="text-3xl">
            📄
          </div>
          <div>
            <h2 class="text-lg font-semibold text-primary-900 mb-2">
              LLMs.txt 生成
            </h2>
            <p class="text-sm text-text-secondary">
              生成AI搜索引擎友好的LLMs.txt文件，优化AI抓取效果
            </p>
          </div>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/admin/seo/content-optimizer"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="flex items-start space-x-4">
          <div class="text-3xl">
            ✨
          </div>
          <div>
            <h2 class="text-lg font-semibold text-primary-900 mb-2">
              AI 内容优化
            </h2>
            <p class="text-sm text-text-secondary">
              利用AI技术优化网站内容，提升SEO排名和用户体验
            </p>
          </div>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/admin/seo/site-audit"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="flex items-start space-x-4">
          <div class="text-3xl">
            🔍
          </div>
          <div>
            <h2 class="text-lg font-semibold text-primary-900 mb-2">
              站点审计
            </h2>
            <p class="text-sm text-text-secondary">
              11维度全面审计网站SEO健康状况，发现优化机会
            </p>
          </div>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/admin/settings"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="flex items-start space-x-4">
          <div class="text-3xl">
            ⚙️
          </div>
          <div>
            <h2 class="text-lg font-semibold text-primary-900 mb-2">
              系统设置
            </h2>
            <p class="text-sm text-text-secondary">
              配置网站基本信息、SEO参数和系统选项
            </p>
          </div>
        </div>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>
