/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="template-gallery">
    <!-- Header -->
    <div class="gallery-header">
      <h1 class="gallery-title">仪表盘模板库</h1>
      <p class="gallery-desc">5 套不同风格的 B 端仪表盘设计模板，适用于各类 SaaS 后台数据展示场景。</p>
      <div class="gallery-meta">
        <a-tag color="blue">Ant Design Vue</a-tag>
        <a-tag color="green">CSS 趋势图</a-tag>
        <a-tag color="purple">Mock 数据</a-tag>
        <a-tag color="orange">响应式布局</a-tag>
      </div>
    </div>

    <!-- Template Cards Grid -->
    <div class="gallery-grid">
      <div
        v-for="tpl in templates"
        :key="tpl.id"
        class="gallery-card"
        @click="goToTemplate(tpl.route)"
      >
        <!-- Card Preview -->
        <div class="card-preview" :class="tpl.previewClass">
          <div class="preview-mock">
            <!-- Mini preview of the dashboard -->
            <div class="preview-mini">
              <div class="mini-topbar" :style="{ background: tpl.accent }" />
              <div class="mini-content">
                <div class="mini-kpis" v-for="i in 3" :key="i">
                  <div class="mini-kpi-bar" :style="{ background: tpl.accent, opacity: 0.5 - i * 0.12 }" />
                </div>
                <div class="mini-chart">
                  <div class="mini-chart-bar" v-for="j in 5" :key="j"
                    :style="{ height: (20 + Math.sin(j * 1.2) * 15 + 10) + 'px', background: tpl.accent, opacity: 0.3 + j * 0.08 }"
                  />
                </div>
                <div class="mini-table">
                  <div class="mini-table-row" v-for="k in 2" :key="k">
                    <div class="mini-cell" v-for="l in 3" :key="l"
                      :style="{ background: tpl.accent, opacity: 0.1 + l * 0.04 }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- Hover overlay -->
          <div class="card-overlay">
            <EyeOutlined class="overlay-icon" />
            <span>查看详情</span>
          </div>
        </div>

        <!-- Card Info -->
        <div class="card-info">
          <div class="card-title-row">
            <span class="card-index">0{{ tpl.id }}</span>
            <h3 class="card-title">{{ tpl.title }}</h3>
          </div>
          <p class="card-desc">{{ tpl.desc }}</p>
          <div class="card-tags">
            <a-tag v-for="tag in tpl.tags" :key="tag" color="processing" size="small">{{ tag }}</a-tag>
          </div>
          <div class="card-ref">
            <span class="ref-label">设计参考</span>
            <span class="ref-name">{{ tpl.reference }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { EyeOutlined } from '@ant-design/icons-vue';

const router = useRouter();

const templates = [
  {
    id: 1,
    title: '数据驾驶舱',
    desc: '深色侧边栏 + 浅色内容区，高对比度设计。左右双栏布局、超大数字展示核心指标，适合数据密集型管理场景。',
    tags: ['深色/浅色', '70/30 布局', '渐变卡片', '全局搜索'],
    reference: 'King Liu 风格',
    route: '/templates/data-cockpit',
    accent: '#7265e6',
    previewClass: 'preview-cockpit',
  },
  {
    id: 2,
    title: '企业后台实战',
    desc: '全白色调极简分割线，4 列统计布局。数据表格为主体，支持分页/排序/筛选，快速操作浮层一键新增导入导出。',
    tags: ['纯白设计', '面包屑导航', '数据表格', '快捷操作'],
    reference: 'UI821 风格',
    route: '/templates/enterprise',
    accent: '#165dff',
    previewClass: 'preview-enterprise',
  },
  {
    id: 3,
    title: '大厂极简风',
    desc: '极简白色大量留白，圆角卡片柔和阴影。超大圆环进度图、CSS 趋势折线、时间线动态，色彩克制只用主色+中性灰。',
    tags: ['极简白', '圆环进度', '时间线', 'Tag Cloud'],
    reference: 'Tencent 风格',
    route: '/templates/tencent',
    accent: '#0052d9',
    previewClass: 'preview-tencent',
  },
  {
    id: 4,
    title: 'SaaS 系统风',
    desc: '多租户切换器、MRR/ARR/流失率/续费率核心指标。白色卡片边框分割，客户列表+活动日志+到期提醒全套 SaaS 功能。',
    tags: ['多租户', 'MRR/ARR', '客户列表', '到期提醒'],
    reference: 'SaaS B 端风格',
    route: '/templates/saas',
    accent: '#1677ff',
    previewClass: 'preview-saas',
  },
  {
    id: 5,
    title: '数据大屏',
    desc: '深蓝渐变背景、发光数字、实时时钟。左右排名列表+趋势图、底部滚动消息，半透明玻璃效果卡片全方位数据可视化。',
    tags: ['深蓝渐变', '发光数字', '实时时钟', '玻璃效果'],
    reference: '字节 B 端风格',
    route: '/templates/data-screen',
    accent: '#00d4ff',
    previewClass: 'preview-datav',
  },
];

function goToTemplate(route: string) {
  router.push(route);
}
</script>

<style scoped>
/* ===== Template Gallery ===== */
.template-gallery {
  min-height: 100vh;
  background: #f5f6f7;
  padding: 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* -- Header -- */
.gallery-header {
  text-align: center;
  margin-bottom: 48px;
}
.gallery-title {
  margin: 0 0 12px;
  font-size: 36px;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: -1px;
}
.gallery-desc {
  margin: 0 auto 16px;
  max-width: 600px;
  font-size: 15px;
  color: #8c8c8c;
  line-height: 1.6;
}
.gallery-meta {
  display: flex;
  justify-content: center;
  gap: 8px;
}

/* -- Grid -- */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 28px;
  max-width: 1400px;
  margin: 0 auto;
}

/* -- Card -- */
.gallery-card {
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
}
.gallery-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
}

/* -- Preview Area -- */
.card-preview {
  position: relative;
  height: 220px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.3s;
}
.gallery-card:hover .card-overlay {
  opacity: 1;
}
.overlay-icon {
  font-size: 36px;
}

/* -- Mini Preview Mock -- */
.preview-mock {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
}
.preview-mini {
  width: 100%;
  height: 100%;
  background: #fafafa;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.mini-topbar {
  height: 20px;
  opacity: 0.3;
  flex-shrink: 0;
}
.mini-content {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}
.mini-kpis {
  display: flex;
  gap: 4px;
}
.mini-kpi-bar {
  flex: 1;
  height: 16px;
  border-radius: 3px;
}
.mini-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 50px;
}
.mini-chart-bar {
  flex: 1;
  border-radius: 2px 2px 0 0;
}
.mini-table {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}
.mini-table-row {
  display: flex;
  gap: 4px;
  flex: 1;
}
.mini-cell {
  flex: 1;
  border-radius: 2px;
}

/* Preview Theme Variations */
.preview-cockpit .preview-mini { background: linear-gradient(135deg, #4a9b8c10, #2a6b6010); }
.preview-enterprise .preview-mini { background: #f7f8fa; }
.preview-tencent .preview-mini { background: #fafafa; }
.preview-saas .preview-mini { background: linear-gradient(135deg, #e6f4ff, #f0f5ff); }
.preview-datav .preview-mini { background: linear-gradient(135deg, #0a1628, #0d1f3c); }
.preview-datav .mini-topbar { opacity: 0.5; }
.preview-datav .mini-kpi-bar { opacity: 0.4 !important; }
.preview-datav .mini-cell { opacity: 0.15 !important; }

/* -- Card Info -- */
.card-info {
  padding: 20px 24px 24px;
}
.card-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}
.card-index {
  font-size: 28px;
  font-weight: 800;
  color: #e8e8e8;
  line-height: 1;
}
.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}
.card-desc {
  margin: 0 0 14px;
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.6;
}
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}
.card-ref {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.ref-label {
  color: #bfbfbf;
}
.ref-name {
  color: #595959;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 800px) {
  .template-gallery { padding: 24px 16px; }
  .gallery-title { font-size: 28px; }
  .gallery-grid { grid-template-columns: 1fr; }
}
</style>
