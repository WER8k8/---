/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="tencent-dashboard">
    <!-- Top Navigation -->
    <div class="tnt-topnav">
      <div class="tnt-brand">
        <span class="tnt-logo">优丁建材</span>
        <span class="tnt-tag">AI SaaS</span>
      </div>
      <div class="tnt-nav-links">
        <a href="javascript:;" class="tnt-nav-item active">工作台</a>
        <a href="javascript:;" class="tnt-nav-item">产品管理</a>
        <a href="javascript:;" class="tnt-nav-item">数据分析</a>
        <a href="javascript:;" class="tnt-nav-item">客户管理</a>
      </div>
      <div class="tnt-nav-actions">
        <a-badge :count="3" :number-style="{ backgroundColor: '#0052d9' }">
          <BellOutlined class="tnt-icon-btn" />
        </a-badge>
        <a-avatar :size="32" style="background: #0052d9;">陈</a-avatar>
      </div>
    </div>

    <!-- Content with Plenty of Whitespace -->
    <div class="tnt-content">
      <!-- Page Title -->
      <div class="tnt-page-head">
        <h1 class="tnt-page-title">数据总览</h1>
        <p class="tnt-page-desc">实时追踪业务关键指标，掌握经营动态。</p>
      </div>

      <!-- Key Metrics: Ring Progress -->
      <div class="tnt-metrics-row">
        <div class="tnt-metric-card" v-for="(metric, i) in metricsData" :key="i">
          <div class="metric-ring-wrap">
            <svg viewBox="0 0 120 120" class="metric-ring">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#f3f3f3" stroke-width="8" />
              <circle
                cx="60" cy="60" r="50" fill="none"
                :stroke="metric.color" stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="metric.dashArray"
                transform="rotate(-90 60 60)"
              />
              <text x="60" y="56" text-anchor="middle" :fill="metric.color" font-size="22" font-weight="700">
                {{ metric.percent }}%
              </text>
              <text x="60" y="76" text-anchor="middle" fill="#999" font-size="11">
                {{ metric.subText }}
              </text>
            </svg>
          </div>
          <div class="metric-info">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value">{{ metric.value }}</span>
          </div>
        </div>
      </div>

      <!-- Trend Charts Row -->
      <div class="tnt-chart-row">
        <!-- Main Trend -->
        <div class="tnt-card tnt-card-large">
          <div class="tnt-card-header">
            <h3 class="tnt-card-title">询盘趋势</h3>
            <div class="tnt-card-subtitle">近30天数据</div>
          </div>
          <div class="tnt-card-body">
            <!-- CSS Sparkline Chart -->
            <div class="tnt-sparkline-grid">
              <!-- 7-Day Comparison -->
              <div class="tnt-sparkline-item" v-for="ch in sparklineChannels" :key="ch.name">
                <div class="sparkline-header">
                  <span class="sparkline-name">{{ ch.name }}</span>
                  <span class="sparkline-val" :style="{ color: ch.color }">{{ ch.total }} <small>条</small></span>
                </div>
                <div class="sparkline-chart">
                  <svg viewBox="0 0 280 60" preserveAspectRatio="none" class="sparkline-svg">
                    <defs>
                      <linearGradient :id="'grad-' + ch.name" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" :stop-color="ch.color" stop-opacity="0.15"/>
                        <stop offset="100%" :stop-color="ch.color" stop-opacity="0"/>
                      </linearGradient>
                    </defs>
                    <polygon :points="ch.areaPoints" :fill="'url(#grad-' + ch.name + ')'" />
                    <polyline :points="ch.linePoints" fill="none" :stroke="ch.color" stroke-width="2" stroke-linejoin="round" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Mini Cards -->
        <div class="tnt-card-stack">
          <div class="tnt-card">
            <div class="tnt-card-header">
              <h3 class="tnt-card-title">热门关键词</h3>
            </div>
            <div class="tnt-card-body">
              <div class="tnt-tag-cloud">
                <a-tag v-for="kw in hotKeywords" :key="kw.text"
                  :color="kw.color" class="tnt-keyword-tag">
                  {{ kw.text }}
                </a-tag>
              </div>
            </div>
          </div>
          <div class="tnt-card">
            <div class="tnt-card-header">
              <h3 class="tnt-card-title">页面分布</h3>
            </div>
            <div class="tnt-card-body">
              <div class="tnt-mini-bars">
                <div v-for="bar in pageBars" :key="bar.name" class="tnt-mini-bar-item">
                  <div class="mini-bar-label-row">
                    <span class="mini-bar-name">{{ bar.name }}</span>
                    <span class="mini-bar-val">{{ bar.count }}</span>
                  </div>
                  <div class="mini-bar-track">
                    <div class="mini-bar-fill" :style="{ width: bar.percent + '%', background: bar.color }" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline Notifications -->
      <div class="tnt-bottom-row">
        <div class="tnt-card tnt-card-timeline">
          <div class="tnt-card-header">
            <h3 class="tnt-card-title">最近动态</h3>
            <a href="javascript:;" class="tnt-link">查看全部</a>
          </div>
          <div class="tnt-card-body">
            <div class="tnt-timeline">
              <div class="tnt-timeline-item" v-for="(item, i) in timelineItems" :key="i">
                <div class="timeline-dot" :class="item.type" />
                <div class="timeline-line" v-if="i < timelineItems.length - 1" />
                <div class="timeline-content">
                  <div class="timeline-title">{{ item.title }}</div>
                  <div class="timeline-desc">{{ item.desc }}</div>
                  <div class="timeline-time">{{ item.time }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="tnt-card tnt-card-summary">
          <div class="tnt-card-header">
            <h3 class="tnt-card-title">AI 内容生成概览</h3>
          </div>
          <div class="tnt-card-body">
            <div class="tnt-summary-grid">
              <div class="tnt-summary-item" v-for="item in aiSummary" :key="item.label">
                <div class="summary-icon-box" :style="{ background: item.bg }">
                  <component :is="item.icon" class="summary-icon" :style="{ color: item.color }" />
                </div>
                <div class="summary-text">
                  <span class="summary-val">{{ item.value }}</span>
                  <span class="summary-label">{{ item.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  BellOutlined,
  RiseOutlined,
  ShoppingCartOutlined,
  TeamOutlined,
  FileTextOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  RobotOutlined,
} from '@ant-design/icons-vue';

// ── Metrics with Ring Progress ──
const metricsData = ref([
  {
    label: '月营收达成率', value: '¥48.6万', percent: 81, subText: '81%',
    color: '#0052d9', dashArray: '254 314',
  },
  {
    label: '询盘转化率', value: '1,862条', percent: 65, subText: '65%',
    color: '#29cc85', dashArray: '204 314',
  },
  {
    label: '客户活跃度', value: '2,456家', percent: 73, subText: '73%',
    color: '#e37318', dashArray: '229 314',
  },
  {
    label: 'SEO 健康度', value: '92分', percent: 92, subText: '92%',
    color: '#7b45cf', dashArray: '289 314',
  },
]);

// ── Sparkline Channels ──
const sparklineChannels = ref([
  {
    name: '网站询盘', total: 856, color: '#0052d9',
    linePoints: '0,55 20,52 40,48 60,45 80,42 100,38 120,35 140,30 160,28 180,25 200,22 220,18 240,15 260,12 280,10',
    areaPoints: '0,60 0,55 20,52 40,48 60,45 80,42 100,38 120,35 140,30 160,28 180,25 200,22 220,18 240,15 260,12 280,10 280,60',
  },
  {
    name: '电话咨询', total: 482, color: '#29cc85',
    linePoints: '0,38 20,35 40,40 60,32 80,36 100,28 120,30 140,25 160,22 180,26 200,20 220,18 240,22 260,15 280,12',
    areaPoints: '0,60 0,38 20,35 40,40 60,32 80,36 100,28 120,30 140,25 160,22 180,26 200,20 220,18 240,22 260,15 280,12 280,60',
  },
  {
    name: '微信咨询', total: 524, color: '#e37318',
    linePoints: '0,30 20,28 40,32 60,26 80,28 100,22 120,25 140,18 160,20 180,16 200,14 220,18 240,12 260,10 280,8',
    areaPoints: '0,60 0,30 20,28 40,32 60,26 80,28 100,22 120,25 140,18 160,20 180,16 200,14 220,18 240,12 260,10 280,8 280,60',
  },
]);

// ── Hot Keywords ──
const hotKeywords = ref([
  { text: '石英石台面', color: 'blue' },
  { text: '大理石背景墙', color: 'green' },
  { text: '防水材料', color: 'orange' },
  { text: '岩板定制', color: 'purple' },
  { text: '环保涂料', color: 'cyan' },
  { text: '木地板安装', color: 'geekblue' },
  { text: '水泥自流平', color: 'magenta' },
  { text: '仿古砖价格', color: 'gold' },
  { text: '建材批发', color: 'blue' },
  { text: '装修设计', color: 'green' },
  { text: '卫浴洁具', color: 'orange' },
  { text: '断桥铝门窗', color: 'purple' },
]);

// ── Page Bars ──
const pageBars = ref([
  { name: '产品详情页', count: '1,286 页', percent: 72, color: '#0052d9' },
  { name: '案例展示页', count: '458 页', percent: 45, color: '#29cc85' },
  { name: '行业方案页', count: '312 页', percent: 38, color: '#e37318' },
  { name: '关于我们', count: '86 页', percent: 22, color: '#7b45cf' },
  { name: '新闻资讯', count: '215 页', percent: 18, color: '#e34d59' },
]);

// ── Timeline ──
const timelineItems = ref([
  { type: 'order', title: '新订单生成', desc: '上海建工集团下单石英石板材A-500，金额¥48,500', time: '2分钟前' },
  { type: 'inquiry', title: '新询盘', desc: '杭州绿城装饰对大理石瓷砖M-200发起询盘', time: '15分钟前' },
  { type: 'ai', title: 'AI 内容生成完毕', desc: '成功生成5篇产品SEO优化文章，覆盖关键词：石英石、大理石、岩板', time: '1小时前' },
  { type: 'system', title: '系统更新', desc: 'AI智能匹配算法升级至v3.2版本，询盘匹配精度提升12%', time: '3小时前' },
  { type: 'notice', title: '库存预警', desc: '花岗岩台面GT-100库存不足（仅剩15件），建议补货', time: '5小时前' },
]);

// ── AI Summary ──
const aiSummary = ref([
  { label: 'AI生成内容', value: '1,286篇', icon: FileTextOutlined, bg: '#e8f3ff', color: '#0052d9' },
  { label: 'SEO优化页面', value: '856页', icon: SearchOutlined, bg: '#e6faf0', color: '#29cc85' },
  { label: '智能问答', value: '12,453次', icon: RobotOutlined, bg: '#fff3e8', color: '#e37318' },
  { label: 'API调用', value: '86.5万次', icon: ApiOutlined, bg: '#f3e8ff', color: '#7b45cf' },
]);
</script>

<style scoped>
/* ===== Tencent-Style Minimal Dashboard ===== */
.tencent-dashboard {
  min-height: 100vh;
  background: #f5f6f7;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  color: #000;
}

/* -- Top Navigation -- */
.tnt-topnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e7e7e7;
}
.tnt-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tnt-logo {
  font-size: 18px;
  font-weight: 700;
  color: #000;
  letter-spacing: 1px;
}
.tnt-tag {
  font-size: 11px;
  background: #f0f5ff;
  color: #0052d9;
  padding: 2px 8px;
  border-radius: 4px;
}
.tnt-nav-links {
  display: flex;
  gap: 36px;
}
.tnt-nav-item {
  position: relative;
  font-size: 14px;
  color: #666;
  text-decoration: none;
  padding: 17px 0;
  transition: color 0.2s;
}
.tnt-nav-item:hover { color: #000; }
.tnt-nav-item.active {
  color: #0052d9;
  font-weight: 600;
}
.tnt-nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 3px;
  background: #0052d9;
  border-radius: 2px;
}
.tnt-nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.tnt-icon-btn {
  font-size: 18px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}
.tnt-icon-btn:hover { color: #0052d9; }

/* -- Content -- */
.tnt-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 36px 48px 60px;
}

/* -- Page Head -- */
.tnt-page-head {
  margin-bottom: 40px;
}
.tnt-page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #000;
  letter-spacing: -0.5px;
}
.tnt-page-desc {
  margin: 8px 0 0;
  font-size: 14px;
  color: #999;
}

/* -- Metrics -- */
.tnt-metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}
.tnt-metric-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow 0.3s;
}
.tnt-metric-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.metric-ring-wrap {
  flex-shrink: 0;
}
.metric-ring {
  width: 100px;
  height: 100px;
}
.metric-info {
  display: flex;
  flex-direction: column;
}
.metric-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 6px;
}
.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #000;
}

/* -- Cards -- */
.tnt-chart-row {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  margin-bottom: 32px;
}
.tnt-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  overflow: hidden;
}
.tnt-card-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.tnt-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0;
}
.tnt-card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #000;
}
.tnt-card-subtitle {
  font-size: 13px;
  color: #999;
}
.tnt-card-body {
  padding: 20px 24px 24px;
}
.tnt-link {
  font-size: 13px;
  color: #0052d9;
  text-decoration: none;
}

/* -- Sparkline Grid -- */
.tnt-sparkline-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.tnt-sparkline-item {
  padding: 0;
}
.sparkline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.sparkline-name {
  font-size: 14px;
  color: #666;
}
.sparkline-val {
  font-size: 14px;
  font-weight: 600;
}
.sparkline-val small {
  font-size: 12px;
  font-weight: 400;
}
.sparkline-chart {
  width: 100%;
  height: 50px;
}
.sparkline-svg {
  width: 100%;
  height: 100%;
}

/* -- Tag Cloud -- */
.tnt-tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tnt-keyword-tag {
  cursor: pointer;
  transition: transform 0.2s;
}
.tnt-keyword-tag:hover {
  transform: scale(1.05);
}

/* -- Mini Bars -- */
.tnt-mini-bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.tnt-mini-bar-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mini-bar-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.mini-bar-name { color: #666; }
.mini-bar-val { color: #000; font-weight: 500; }
.mini-bar-track {
  height: 6px;
  background: #f3f3f3;
  border-radius: 3px;
  overflow: hidden;
}
.mini-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
}

/* -- Bottom Row -- */
.tnt-bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.tnt-card-timeline .tnt-card-body {
  max-height: 400px;
  overflow-y: auto;
}

/* -- Timeline -- */
.tnt-timeline {
  display: flex;
  flex-direction: column;
}
.tnt-timeline-item {
  display: flex;
  gap: 14px;
  position: relative;
  padding-bottom: 18px;
}
.tnt-timeline-item:last-child {
  padding-bottom: 0;
}
.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
  position: relative;
  z-index: 1;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px;
}
.timeline-dot.order { background: #0052d9; box-shadow: 0 0 0 2px #b3cdf5; }
.timeline-dot.inquiry { background: #29cc85; box-shadow: 0 0 0 2px #a3e7c8; }
.timeline-dot.ai { background: #7b45cf; box-shadow: 0 0 0 2px #cdb5f5; }
.timeline-dot.system { background: #e37318; box-shadow: 0 0 0 2px #f5c7a3; }
.timeline-dot.notice { background: #e34d59; box-shadow: 0 0 0 2px #f5b3b8; }
.timeline-line {
  position: absolute;
  left: 5px;
  top: 18px;
  width: 1px;
  height: calc(100% - 12px);
  background: #e7e7e7;
}
.timeline-content {
  flex: 1;
  padding-bottom: 4px;
}
.timeline-title {
  font-size: 14px;
  font-weight: 600;
  color: #000;
  margin-bottom: 4px;
}
.timeline-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  line-height: 1.4;
}
.timeline-time {
  font-size: 12px;
  color: #bbb;
}

/* -- AI Summary Grid -- */
.tnt-summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.tnt-summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: #fafafa;
}
.summary-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.summary-icon {
  font-size: 22px;
}
.summary-text {
  display: flex;
  flex-direction: column;
}
.summary-val {
  font-size: 16px;
  font-weight: 600;
  color: #000;
}
.summary-label {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* Responsive */
@media (max-width: 1100px) {
  .tnt-chart-row { grid-template-columns: 1fr; }
  .tnt-bottom-row { grid-template-columns: 1fr; }
  .tnt-metrics-row { grid-template-columns: repeat(2, 1fr); }
  .tnt-content { padding: 24px 24px 48px; }
  .tnt-nav-links { gap: 18px; }
}
</style>
