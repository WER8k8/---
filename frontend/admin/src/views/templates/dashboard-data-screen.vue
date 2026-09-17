/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="data-screen">
    <!-- Top Header -->
    <div class="ds-header">
      <div class="ds-header-left">
        <div class="ds-corner-lines left" />
      </div>
      <div class="ds-header-center">
        <h1 class="ds-title">优丁建材 AI智能数据大屏</h1>
        <p class="ds-subtitle">YOU DING BUILDING MATERIALS — AI DATA DASHBOARD</p>
      </div>
      <div class="ds-header-right">
        <div class="ds-corner-lines right" />
        <div class="ds-clock">
          <span class="clock-time">{{ currentTime }}</span>
          <span class="clock-date">{{ currentDate }}</span>
        </div>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="ds-grid">
      <!-- Left Column -->
      <div class="ds-col ds-col-left">
        <!-- Sales Ranking -->
        <div class="ds-panel">
          <div class="ds-panel-header">
            <span class="ds-panel-icon" />
            <h3>销量排名 Top 10</h3>
          </div>
          <div class="ds-panel-body">
            <div class="ds-rank-table">
              <div class="ds-rank-header">
                <span class="rank-col rank-num-col">排名</span>
                <span class="rank-col rank-name-col">产品名称</span>
                <span class="rank-col rank-sales-col">销量</span>
                <span class="rank-col rank-rate-col">占比</span>
              </div>
              <div
                v-for="(item, idx) in salesRank"
                :key="idx"
                class="ds-rank-row"
                :class="{ 'top-row': idx < 3 }"
              >
                <span class="rank-col rank-num-col">
                  <span class="rank-badge" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
                </span>
                <span class="rank-col rank-name-col">
                  <span class="rank-dot" :style="{ background: item.color }" />
                  {{ item.name }}
                </span>
                <span class="rank-col rank-sales-col">{{ item.sales }}</span>
                <span class="rank-col rank-rate-col">
                  <div class="rank-rate-bar">
                    <div class="rank-rate-fill" :style="{ width: item.rate + '%', background: item.color }" />
                  </div>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Production Status -->
        <div class="ds-panel">
          <div class="ds-panel-header">
            <span class="ds-panel-icon" />
            <h3>产线实时状态</h3>
          </div>
          <div class="ds-panel-body">
            <div class="ds-production-list">
              <div v-for="line in productionLines" :key="line.id" class="ds-prod-item">
                <div class="prod-info">
                  <span class="prod-name">{{ line.name }}</span>
                  <span class="prod-status" :style="{ color: line.statusColor }">{{ line.status }}</span>
                </div>
                <div class="prod-bar-wrap">
                  <div class="prod-bar">
                    <div class="prod-bar-fill" :style="{ width: line.progress + '%', background: line.barColor }">
                      <span class="prod-bar-text">{{ line.progress }}%</span>
                    </div>
                  </div>
                </div>
                <div class="prod-meta">
                  <span>产出：{{ line.output }}件</span>
                  <span>目标：{{ line.target }}件</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Center Column -->
      <div class="ds-col ds-col-center">
        <!-- Glowing KPIs -->
        <div class="ds-kpi-row">
          <div class="ds-kpi-card" v-for="kpi in glowKpis" :key="kpi.label">
            <div class="ds-kpi-glow" :style="{ boxShadow: '0 0 30px ' + kpi.glow }" />
            <div class="ds-kpi-content">
              <span class="ds-kpi-label">{{ kpi.label }}</span>
              <span class="ds-kpi-value" :style="{ color: kpi.glow }">
                <span class="kpi-num" ref="kpiNumbers">{{ kpi.value }}</span>
                <span class="kpi-unit">{{ kpi.unit }}</span>
              </span>
              <span class="ds-kpi-trend" :class="kpi.trendUp ? 'up' : 'down'">
                <span class="kpi-arrow">{{ kpi.trendUp ? '&#9650;' : '&#9660;' }}</span>
                {{ kpi.change }}
              </span>
            </div>
          </div>
        </div>

        <!-- Center Chart Area -->
        <div class="ds-panel ds-panel-chart">
          <div class="ds-panel-header">
            <span class="ds-panel-icon" />
            <h3>周度询盘趋势</h3>
            <div class="ds-panel-tabs">
              <span class="ds-tab active">7天</span>
              <span class="ds-tab">30天</span>
              <span class="ds-tab">季度</span>
            </div>
          </div>
          <div class="ds-panel-body">
            <div class="ds-line-chart">
              <div class="ds-chart-grid">
                <div v-for="i in 5" :key="i" class="ds-grid-line" />
              </div>
              <svg class="ds-chart-svg" viewBox="0 0 740 260" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#00d4ff" stop-opacity="0.4"/>
                    <stop offset="100%" stop-color="#00d4ff" stop-opacity="0"/>
                  </linearGradient>
                  <filter id="glowFilter">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>
                <polygon :points="chartAreaPoints" fill="url(#lineGrad)" />
                <polyline :points="chartLinePoints" fill="none" stroke="#00d4ff" stroke-width="3"
                  stroke-linejoin="round" filter="url(#glowFilter)" />
                <!-- Data Dots -->
                <circle v-for="(dot, i) in chartDots" :key="i"
                  :cx="dot.x" :cy="dot.y" r="4" fill="#00d4ff" stroke="#0a1628" stroke-width="2"
                  :style="{ filter: 'url(#glowFilter)' }" />
              </svg>
              <div class="ds-chart-x-labels">
                <span v-for="d in chartDays" :key="d">{{ d }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom Scroll News -->
        <div class="ds-scroll-news">
          <div class="ds-scroll-label">
            <SoundOutlined /> 实时动态
          </div>
          <div class="ds-scroll-content">
            <div class="ds-scroll-inner" :style="{ animationDuration: scrollDuration + 's' }">
              <span v-for="(news, i) in realtimeNews" :key="i" class="ds-scroll-item">
                {{ news.text }}&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="ds-col ds-col-right">
        <!-- Geographic Distribution -->
        <div class="ds-panel">
          <div class="ds-panel-header">
            <span class="ds-panel-icon" />
            <h3>客户地域分布</h3>
          </div>
          <div class="ds-panel-body">
            <div class="ds-geo-bars">
              <div v-for="geo in geoData" :key="geo.region" class="ds-geo-item">
                <div class="geo-label-row">
                  <span class="geo-name">{{ geo.region }}</span>
                  <span class="geo-val">{{ geo.count }}</span>
                </div>
                <div class="geo-bar-wrap">
                  <div class="geo-bar" :style="{ width: geo.percent + '%', background: geo.color }" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Category Progress -->
        <div class="ds-panel">
          <div class="ds-panel-header">
            <span class="ds-panel-icon" />
            <h3>品类销售进度</h3>
          </div>
          <div class="ds-panel-body">
            <div class="ds-progress-list">
              <div v-for="cat in categoryProgress" :key="cat.name" class="ds-progress-item">
                <div class="prog-header">
                  <div class="prog-icon" :style="{ background: cat.color }">
                    <component :is="cat.icon" />
                  </div>
                  <div class="prog-info">
                    <span class="prog-name">{{ cat.name }}</span>
                    <span class="prog-target">目标：{{ cat.target }}</span>
                  </div>
                  <span class="prog-pct" :style="{ color: cat.color }">{{ cat.percent }}%</span>
                </div>
                <div class="prog-track">
                  <div class="prog-fill" :style="{ width: cat.percent + '%', background: cat.color }" />
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
import { ref, onMounted, onUnmounted } from 'vue';
import { SoundOutlined, ShoppingCartOutlined, HomeOutlined, ToolOutlined, ExperimentOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';

// ── Clock ──
const currentTime = ref('');
const currentDate = ref('');
let clockTimer: number;

function updateClock() {
  const now = dayjs();
  currentTime.value = now.format('HH:mm:ss');
  currentDate.value = now.format('YYYY年MM月DD日 dddd');
}

onMounted(() => {
  updateClock();
  clockTimer = window.setInterval(updateClock, 1000);
});
onUnmounted(() => {
  clearInterval(clockTimer);
});

// ── Glowing KPIs ──
const glowKpis = ref([
  { label: '总营收', value: '1,285.6', unit: '万元', trendUp: true, change: '+18.5%', glow: '#00d4ff' },
  { label: '总订单', value: '18,423', unit: '单', trendUp: true, change: '+12.3%', glow: '#00ff88' },
  { label: '活跃客户', value: '3,862', unit: '家', trendUp: true, change: '+8.7%', glow: '#ff6b9d' },
  { label: 'AI 调用', value: '865.2', unit: '万次', trendUp: false, change: '-3.2%', glow: '#ffaa00' },
]);

// ── Sales Rank ──
const salesRank = ref([
  { name: '石英石板材 A-500', sales: '2,847件', rate: 95, color: '#00d4ff' },
  { name: '大理石瓷砖 M-200', sales: '2,356件', rate: 82, color: '#00ff88' },
  { name: '防水涂料 WP-100', sales: '1,892件', rate: 65, color: '#ffaa00' },
  { name: '岩板 YB-800', sales: '1,567件', rate: 52, color: '#ff6b9d' },
  { name: '木地板 WD-300', sales: '1,203件', rate: 40, color: '#a78bfa' },
  { name: '水泥自流平 CP-50', sales: '987件', rate: 32, color: '#38bdf8' },
  { name: '仿古砖 AG-600', sales: '756件', rate: 25, color: '#fb923c' },
  { name: '花岗岩台面 GT-100', sales: '623件', rate: 20, color: '#4ade80' },
  { name: '玻璃幕墙 BL-500', sales: '489件', rate: 16, color: '#f472b6' },
  { name: '环保乳胶漆 EP-200', sales: '386件', rate: 12, color: '#818cf8' },
]);

// ── Production Lines ──
const productionLines = ref([
  { id: 1, name: '石英石产线 A线', status: '运行中', statusColor: '#00d4ff', progress: 92, barColor: 'linear-gradient(90deg, #00d4ff, #00ff88)', output: 2760, target: 3000 },
  { id: 2, name: '瓷砖产线 B线', status: '运行中', statusColor: '#00ff88', progress: 78, barColor: 'linear-gradient(90deg, #00ff88, #38bdf8)', output: 2340, target: 3000 },
  { id: 3, name: '涂料产线 C线', status: '维护中', statusColor: '#ffaa00', progress: 45, barColor: 'linear-gradient(90deg, #ffaa00, #fb923c)', output: 900, target: 2000 },
  { id: 4, name: '岩板产线 D线', status: '运行中', statusColor: '#00d4ff', progress: 61, barColor: 'linear-gradient(90deg, #a78bfa, #818cf8)', output: 1830, target: 3000 },
]);

// ── Chart Data ──
const chartDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const chartLinePoints = '20,220 140,180 260,145 380,120 500,95 620,70 720,50';
const chartAreaPoints = '20,260 20,220 140,180 260,145 380,120 500,95 620,70 720,50 720,260';

const chartDots = [
  { x: 20, y: 220 }, { x: 140, y: 180 }, { x: 260, y: 145 },
  { x: 380, y: 120 }, { x: 500, y: 95 }, { x: 620, y: 70 }, { x: 720, y: 50 },
];

// ── Scroll News ──
const scrollDuration = ref(30);
const realtimeNews = ref([
  { text: '【订单】上海建工集团采购石英石板材A-500 x200件，金额¥48,500' },
  { text: '【AI】成功生成大理石系列SEO优化文章5篇，覆盖关键词20+' },
  { text: '【询盘】杭州绿城装饰对防水涂料WP-100发起新询盘' },
  { text: '【库存】花岗岩台面GT-100库存不足15件，系统建议补货' },
  { text: '【生产】石英石产线A线今日产出2,760件，完成率92%' },
  { text: '【系统】AI智能匹配算法升级至v3.2，询盘匹配精度提升12%' },
  { text: '【客户】本月新增客户286家，活跃客户同比增长23.5%' },
  { text: '【营收】本月MRR突破¥48.6万，环比增长8.5%' },
  { text: '【通知】优丁建材3.0版本将于6月1日全量上线' },
]);

// ── Geo Data ──
const geoData = ref([
  { region: '华东地区', count: '1,286', percent: 85, color: '#00d4ff' },
  { region: '华南地区', count: '982', percent: 68, color: '#00ff88' },
  { region: '华北地区', count: '758', percent: 52, color: '#ffaa00' },
  { region: '西南地区', count: '523', percent: 36, color: '#ff6b9d' },
  { region: '华中地区', count: '312', percent: 22, color: '#a78bfa' },
]);

// ── Category Progress ──
const categoryProgress = ref([
  { name: '石材类', target: '¥300万', percent: 88, color: '#00d4ff', icon: ShoppingCartOutlined },
  { name: '瓷砖类', target: '¥250万', percent: 72, color: '#00ff88', icon: HomeOutlined },
  { name: '涂料类', target: '¥180万', percent: 65, color: '#ffaa00', icon: ExperimentOutlined },
  { name: '板材类', target: '¥200万', percent: 55, color: '#ff6b9d', icon: ToolOutlined },
]);
</script>

<style scoped>
/* ===== Data Screen — Deep Blue Sci-Fi Style ===== */
.data-screen {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a1628 0%, #0d1f3c 40%, #0a1628 100%);
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  overflow: hidden;
}

/* -- Header -- */
.ds-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 36px;
  background: linear-gradient(180deg, rgba(0,212,255,0.08) 0%, transparent 100%);
  border-bottom: 1px solid rgba(0,212,255,0.15);
  position: relative;
}
.ds-header-left, .ds-header-right {
  width: 280px;
}
.ds-corner-lines {
  width: 60px;
  height: 40px;
  position: relative;
}
.ds-corner-lines.left::before,
.ds-corner-lines.left::after {
  content: '';
  position: absolute;
  background: rgba(0,212,255,0.3);
}
.ds-corner-lines.left::before {
  top: 0; left: 0; width: 20px; height: 1px;
}
.ds-corner-lines.left::after {
  top: 0; left: 0; width: 1px; height: 20px;
}
.ds-corner-lines.right::before,
.ds-corner-lines.right::after {
  content: '';
  position: absolute;
  background: rgba(0,212,255,0.3);
}
.ds-corner-lines.right::before {
  bottom: 0; right: 0; width: 20px; height: 1px;
}
.ds-corner-lines.right::after {
  bottom: 0; right: 0; width: 1px; height: 20px;
}
.ds-header-center {
  text-align: center;
  flex: 1;
}
.ds-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 4px;
  background: linear-gradient(90deg, #00d4ff, #00ff88);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.ds-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: rgba(0,212,255,0.5);
  letter-spacing: 3px;
}
.ds-clock {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.clock-time {
  font-size: 26px;
  font-weight: 700;
  font-family: 'DIN', 'Courier New', monospace;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0,212,255,0.5);
  letter-spacing: 2px;
}
.clock-date {
  font-size: 13px;
  color: rgba(0,212,255,0.6);
  margin-top: 2px;
}

/* -- Grid -- */
.ds-grid {
  display: grid;
  grid-template-columns: 380px 1fr 380px;
  gap: 16px;
  padding: 16px 20px;
  height: calc(100vh - 98px);
}
.ds-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

/* -- Panel -- */
.ds-panel {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(0,212,255,0.1);
  border-radius: 8px;
  overflow: hidden;
  backdrop-filter: blur(10px);
}
.ds-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0,212,255,0.1);
}
.ds-panel-icon {
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, #00d4ff, #00ff88);
  border-radius: 2px;
}
.ds-panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #e0f7fa;
}
.ds-panel-tabs {
  display: flex;
  gap: 6px;
  margin-left: auto;
}
.ds-tab {
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.3s;
}
.ds-tab.active {
  color: #00d4ff;
  border-color: rgba(0,212,255,0.4);
  background: rgba(0,212,255,0.1);
}
.ds-panel-body {
  padding: 12px 18px 16px;
}

/* -- KPI Cards -- */
.ds-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.ds-kpi-card {
  position: relative;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(0,212,255,0.15);
  border-radius: 10px;
  padding: 18px 16px;
  overflow: hidden;
}
.ds-kpi-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  opacity: 0.15;
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.1; transform: scale(1); }
  50% { opacity: 0.2; transform: scale(1.1); }
}
.ds-kpi-content {
  position: relative;
  z-index: 1;
}
.ds-kpi-label {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
}
.ds-kpi-value {
  font-size: 36px;
  font-weight: 800;
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin: 6px 0;
  text-shadow: 0 0 20px currentColor;
}
.kpi-num {
  letter-spacing: 2px;
}
.kpi-unit {
  font-size: 14px;
  font-weight: 400;
  opacity: 0.7;
}
.ds-kpi-trend {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.ds-kpi-trend.up { color: #00ff88; }
.ds-kpi-trend.down { color: #ff6b9d; }

/* -- Rank Table -- */
.ds-rank-table {
  font-size: 13px;
}
.ds-rank-header {
  display: flex;
  padding: 6px 0 10px;
  border-bottom: 1px solid rgba(0,212,255,0.1);
  color: rgba(255,255,255,0.4);
  font-size: 12px;
}
.ds-rank-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.3s;
}
.ds-rank-row:hover {
  background: rgba(0,212,255,0.05);
}
.ds-rank-row.top-row {
  background: rgba(0,212,255,0.08);
}
.rank-col { flex-shrink: 0; }
.rank-num-col { width: 42px; text-align: center; }
.rank-name-col { flex: 1; display: flex; align-items: center; gap: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-sales-col { width: 70px; text-align: right; color: rgba(255,255,255,0.7); }
.rank-rate-col { width: 100px; padding-left: 10px; }
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.5);
}
.rank-badge.rank-1 { background: #ffd700; color: #000; }
.rank-badge.rank-2 { background: #c0c0c0; color: #000; }
.rank-badge.rank-3 { background: #cd7f32; color: #000; }
.rank-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.rank-rate-bar {
  height: 4px;
  background: rgba(255,255,255,0.08);
  border-radius: 2px;
  overflow: hidden;
}
.rank-rate-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}

/* -- Production -- */
.ds-production-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.ds-prod-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.prod-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.prod-name {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
}
.prod-status {
  font-size: 12px;
  font-weight: 500;
}
.prod-bar-wrap {
  height: 22px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  overflow: hidden;
}
.prod-bar {
  height: 100%;
}
.prod-bar-fill {
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  transition: width 0.8s ease;
  position: relative;
}
.prod-bar-text {
  font-size: 11px;
  color: #fff;
  font-weight: 600;
  text-shadow: 0 0 4px rgba(0,0,0,0.5);
}
.prod-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(255,255,255,0.35);
}

/* -- Line Chart -- */
.ds-line-chart {
  height: 240px;
  position: relative;
}
.ds-chart-grid {
  position: absolute;
  inset: 0 0 24px 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.ds-grid-line {
  height: 1px;
  background: rgba(0,212,255,0.06);
}
.ds-chart-svg {
  position: absolute;
  inset: 0 0 24px 0;
  width: 100%;
  height: calc(100% - 24px);
}
.ds-chart-x-labels {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

/* -- Scroll News -- */
.ds-scroll-news {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(0,212,255,0.1);
  border-radius: 6px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  flex-shrink: 0;
}
.ds-scroll-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #00d4ff;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}
.ds-scroll-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}
.ds-scroll-inner {
  display: inline-block;
  white-space: nowrap;
  animation: scrollLeft linear infinite;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
}
@keyframes scrollLeft {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* -- Geo Bars -- */
.ds-geo-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ds-geo-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.geo-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.geo-name { color: rgba(255,255,255,0.7); }
.geo-val { color: rgba(255,255,255,0.9); font-weight: 600; }
.geo-bar-wrap {
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}
.geo-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
}

/* -- Category Progress -- */
.ds-progress-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.ds-progress-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.prog-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.prog-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 15px;
  flex-shrink: 0;
}
.prog-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.prog-name {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
}
.prog-target {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}
.prog-pct {
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}
.prog-track {
  height: 8px;
  background: rgba(255,255,255,0.06);
  border-radius: 4px;
  overflow: hidden;
}
.prog-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
  box-shadow: 0 0 8px currentColor;
}
</style>
