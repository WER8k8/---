/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="data-cockpit">
    <!-- Top Bar: Search + Actions -->
    <div class="cockpit-topbar">
      <div class="cockpit-search">
        <SearchOutlined class="search-icon" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="全局搜索产品、订单、客户..."
          class="search-input"
          @keyup.enter="handleSearch"
        />
        <span class="search-shortcut">Ctrl+K</span>
      </div>
      <div class="cockpit-actions">
        <a-tooltip title="刷新数据">
          <a-button shape="circle" :icon="h(ReloadOutlined)" @click="refreshAll" />
        </a-tooltip>
        <a-tooltip title="全屏">
          <a-button shape="circle" :icon="h(ExpandOutlined)" />
        </a-tooltip>
        <a-tooltip title="导出报表">
          <a-button shape="circle" :icon="h(DownloadOutlined)" />
        </a-tooltip>
        <a-badge :count="notificationCount" :overflow-count="99">
          <a-button shape="circle" :icon="h(BellOutlined)" />
        </a-badge>
        <a-avatar :size="36" style="background-color: #7265e6; cursor: pointer">
          <template #icon><UserOutlined /></template>
        </a-avatar>
      </div>
    </div>

    <!-- Breadcrumb + Time Range -->
    <div class="cockpit-header">
      <div class="header-left">
        <h1 class="cockpit-title">数据驾驶舱</h1>
        <a-breadcrumb>
          <a-breadcrumb-item>首页</a-breadcrumb-item>
          <a-breadcrumb-item>数据驾驶舱</a-breadcrumb-item>
        </a-breadcrumb>
      </div>
      <div class="header-right">
        <a-range-picker
          v-model:value="dateRange"
          :placeholder="['开始日期', '结束日期']"
          @change="refreshAll"
          style="width: 260px"
        />
        <a-select v-model:value="timeGranularity" style="width: 120px" @change="refreshAll">
          <a-select-option value="hour">按小时</a-select-option>
          <a-select-option value="day">按天</a-select-option>
          <a-select-option value="week">按周</a-select-option>
          <a-select-option value="month">按月</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- KPI Cards Row -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="(kpi, idx) in kpiCards" :key="idx">
        <div class="kpi-bg-decor" :style="{ background: kpi.gradient }" />
        <div class="kpi-content">
          <div class="kpi-info">
            <span class="kpi-label">{{ kpi.label }}</span>
            <span class="kpi-value">
              <span class="kpi-number">{{ kpi.value }}</span>
              <span v-if="kpi.unit" class="kpi-unit">{{ kpi.unit }}</span>
            </span>
            <span class="kpi-sub">{{ kpi.sub }}</span>
          </div>
          <div class="kpi-icon-box" :style="{ background: kpi.iconBg }">
            <component :is="kpi.icon" class="kpi-icon" />
          </div>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" :class="kpi.trendUp ? 'trend-up' : 'trend-down'">
            <component :is="kpi.trendUp ? ArrowUpOutlined : ArrowDownOutlined" />
            {{ kpi.trendPercent }}%
          </span>
          <span class="kpi-compare">较昨日</span>
        </div>
      </div>
    </div>

    <!-- Main Content: 70% Chart / 30% Side -->
    <div class="cockpit-body">
      <div class="cockpit-main">
        <!-- Multi-Chart Grid -->
        <div class="chart-section">
          <div class="chart-card chart-large">
            <div class="chart-card-header">
              <h3>营收趋势</h3>
              <div class="chart-tabs">
                <span
                  v-for="tab in revenueTabs"
                  :key="tab.key"
                  class="chart-tab"
                  :class="{ active: activeRevenueTab === tab.key }"
                  @click="activeRevenueTab = tab.key"
                >{{ tab.label }}</span>
              </div>
            </div>
            <div class="chart-body">
              <div class="revenue-summary">
                <div class="summary-item">
                  <span class="summary-label">总营收</span>
                  <span class="summary-val">¥{{ formatMoney(totalRevenue) }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">环比增长</span>
                  <span class="summary-val trend-up">+{{ revenueGrowthRate }}%</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">订单数</span>
                  <span class="summary-val">{{ totalOrders }}</span>
                </div>
              </div>
              <div class="chart-canvas">
                <!-- CSS Trend Chart -->
                <div class="trend-chart">
                  <div class="trend-y-axis">
                    <span v-for="y in yLabels" :key="y">{{ y }}</span>
                  </div>
                  <div class="trend-plot">
                    <div class="trend-grid">
                      <div v-for="i in 4" :key="i" class="grid-line" />
                    </div>
                    <svg class="trend-line" viewBox="0 0 600 180" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stop-color="#7265e6" stop-opacity="0.3"/>
                          <stop offset="100%" stop-color="#7265e6" stop-opacity="0"/>
                        </linearGradient>
                        <linearGradient id="orderGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stop-color="#22c55e" stop-opacity="0.3"/>
                          <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
                        </linearGradient>
                      </defs>
                      <polygon :points="revenueAreaPoints" fill="url(#revenueGrad)" />
                      <polyline :points="revenueLinePoints" fill="none" stroke="#7265e6" stroke-width="2.5" stroke-linejoin="round"/>
                      <polyline :points="orderLinePoints" fill="none" stroke="#22c55e" stroke-width="2" stroke-linejoin="round" stroke-dasharray="6,3"/>
                    </svg>
                    <div class="trend-x-axis">
                      <span v-for="label in xAxisLabels" :key="label">{{ label }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card chart-medium">
            <div class="chart-card-header">
              <h3>产品销量排行</h3>
              <a href="javascript:;" class="chart-link">查看全部</a>
            </div>
            <div class="chart-body">
              <div class="rank-list">
                <div
                  v-for="(item, idx) in productRank"
                  :key="idx"
                  class="rank-item"
                >
                  <span class="rank-num" :class="idx < 3 ? `top-${idx + 1}` : ''">{{ idx + 1 }}</span>
                  <span class="rank-name">{{ item.name }}</span>
                  <div class="rank-bar-wrap">
                    <div class="rank-bar" :style="{ width: item.percent + '%', background: item.color }" />
                  </div>
                  <span class="rank-val">{{ item.sales }}件</span>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card chart-medium">
            <div class="chart-card-header">
              <h3>客户转化漏斗</h3>
            </div>
            <div class="chart-body">
              <div class="funnel">
                <div v-for="(stage, idx) in funnelStages" :key="idx" class="funnel-stage">
                  <div class="funnel-bar" :style="{ width: stage.rate + '%', background: funnelColors[idx] }">
                    <span class="funnel-name">{{ stage.name }}</span>
                    <span class="funnel-val">{{ stage.value }}</span>
                  </div>
                  <span class="funnel-rate">{{ stage.rate }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Table Section -->
        <div class="chart-card chart-full">
          <div class="chart-card-header">
            <h3>最新订单</h3>
            <div class="chart-card-actions">
              <a-input-search
                v-model:value="orderSearch"
                placeholder="搜索订单号"
                style="width: 200px"
                @search="handleOrderSearch"
              />
              <a-button type="primary" size="small">
                <template #icon><PlusOutlined /></template>
                新增订单
              </a-button>
            </div>
          </div>
          <div class="chart-body">
            <a-table
              :columns="orderColumns"
              :data-source="orderData"
              :pagination="{ pageSize: 5, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
              :row-key="(r: any) => r.id"
              size="middle"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
                </template>
                <template v-if="column.key === 'amount'">
                  <span class="amount-cell">¥{{ formatMoney(record.amount) }}</span>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </div>

      <!-- Right Sidebar: 30% -->
      <div class="cockpit-sidebar">
        <!-- Today's KPIs -->
        <div class="side-card">
          <h3 class="side-title">今日概览</h3>
          <div class="today-stats">
            <div class="today-stat">
              <span class="today-val">¥{{ formatMoney(todayRevenue) }}</span>
              <span class="today-label">今日营收</span>
              <span class="today-trend trend-up">+{{ todayRevenueGrowth }}%</span>
            </div>
            <div class="today-stat">
              <span class="today-val">{{ todayOrders }}</span>
              <span class="today-label">今日订单</span>
              <span class="today-trend trend-up">+{{ todayOrderGrowth }}%</span>
            </div>
            <div class="today-stat">
              <span class="today-val">{{ todayVisitors }}</span>
              <span class="today-label">访问人数</span>
              <span class="today-trend trend-down">-{{ todayVisitorDecline }}%</span>
            </div>
          </div>
        </div>

        <!-- Pending Tasks -->
        <div class="side-card">
          <div class="side-title-row">
            <h3 class="side-title">待办事项</h3>
            <a-badge :count="pendingTasks.filter((t: any) => !t.done).length" :number-style="{ backgroundColor: '#7265e6' }" />
          </div>
          <div class="task-list">
            <div
              v-for="task in pendingTasks"
              :key="task.id"
              class="task-item"
              :class="{ done: task.done }"
              @click="task.done = !task.done"
            >
              <CheckCircleFilled v-if="task.done" class="task-check done-icon" />
              <CheckCircleOutlined v-else class="task-check" />
              <div class="task-info">
                <span class="task-title">{{ task.title }}</span>
                <span class="task-time">{{ task.time }}</span>
              </div>
              <a-tag :color="task.priority === 'high' ? '#f5222d' : task.priority === 'medium' ? '#faad14' : '#1890ff'" size="small">
                {{ task.priority === 'high' ? '紧急' : task.priority === 'medium' ? '中等' : '普通' }}
              </a-tag>
            </div>
          </div>
        </div>

        <!-- Announcements -->
        <div class="side-card">
          <div class="side-title-row">
            <h3 class="side-title">系统公告</h3>
            <a href="javascript:;" class="side-link">全部</a>
          </div>
          <div class="announce-list">
            <div v-for="ann in announcements" :key="ann.id" class="announce-item">
              <div class="announce-dot" :style="{ background: ann.color }" />
              <div class="announce-content">
                <span class="announce-text">{{ ann.text }}</span>
                <span class="announce-time">{{ ann.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h, computed } from 'vue';
import {
  SearchOutlined,
  ReloadOutlined,
  ExpandOutlined,
  DownloadOutlined,
  BellOutlined,
  UserOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  CheckCircleFilled,
  ShoppingCartOutlined,
  DollarOutlined,
  TeamOutlined,
  EyeOutlined,
  RiseOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';

// ── State ──
const searchKeyword = ref('');
const notificationCount = ref(8);
const dateRange = ref<[string, string] | undefined>(undefined);
const timeGranularity = ref('day');
const activeRevenueTab = ref('revenue');
const orderSearch = ref('');

// ── KPI Cards ──
const kpiCards = computed(() => [
  {
    label: '总营收', value: '¥12,856,420', unit: '',
    sub: '累计交易额', icon: DollarOutlined,
    gradient: 'linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: true, trendPercent: 12.5,
  },
  {
    label: '总订单', value: '18,423', unit: '单',
    sub: '累计订单数', icon: ShoppingCartOutlined,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: true, trendPercent: 8.3,
  },
  {
    label: '客户数', value: '3,862', unit: '位',
    sub: '活跃客户', icon: TeamOutlined,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: true, trendPercent: 5.7,
  },
  {
    label: '页面浏览量', value: '256,780', unit: '次',
    sub: '本月累计', icon: EyeOutlined,
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: false, trendPercent: 2.1,
  },
  {
    label: '转化率', value: '6.8', unit: '%',
    sub: '平均转化率', icon: RiseOutlined,
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: true, trendPercent: 1.2,
  },
  {
    label: '询盘数', value: '2,845', unit: '条',
    sub: '本月新询盘', icon: TrophyOutlined,
    gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
    iconBg: 'rgba(255,255,255,0.2)', trendUp: true, trendPercent: 15.8,
  },
]);

// ── Revenue Chart Data ──
const totalRevenue = ref(12856420);
const revenueGrowthRate = ref(12.5);
const totalOrders = ref(18423);

const revenueTabs = [
  { key: 'revenue', label: '营收' },
  { key: 'orders', label: '订单量' },
];

const yLabels = ['0', '5万', '10万', '15万', '20万'];
const xAxisLabels = ['01', '05', '10', '15', '20', '25', '30'];

const revenueLinePoints = '0,120 100,95 200,110 300,70 400,85 500,45 600,30';
const revenueAreaPoints = '0,180 0,120 100,95 200,110 300,70 400,85 500,45 600,30 600,180';
const orderLinePoints = '0,150 100,130 200,140 300,100 400,115 500,75 600,55';

// ── Product Rank ──
const productRank = ref([
  { name: '石英石板材 A-500', sales: 2847, percent: 95, color: '#7265e6' },
  { name: '大理石瓷砖 M-200', sales: 2356, percent: 82, color: '#4facfe' },
  { name: '防水涂料 WP-100', sales: 1892, percent: 65, color: '#43e97b' },
  { name: '岩板 YB-800', sales: 1567, percent: 52, color: '#fa709a' },
  { name: '木地板 WD-300', sales: 1203, percent: 40, color: '#f093fb' },
  { name: '水泥自流平 CP-50', sales: 987, percent: 32, color: '#a18cd1' },
  { name: '仿古砖 AG-600', sales: 756, percent: 25, color: '#4a9b8c' },
]);

// ── Funnel ──
const funnelStages = ref([
  { name: '访问', value: '256,780', rate: 100 },
  { name: '浏览产品', value: '85,432', rate: 33 },
  { name: '发起询盘', value: '12,856', rate: 5 },
  { name: '报价跟进', value: '4,892', rate: 1.9 },
  { name: '成交', value: '1,423', rate: 0.55 },
]);
const funnelColors = ['#7265e6', '#4facfe', '#43e97b', '#fa709a', '#f5576c'];

// ── Order Table ──
const orderColumns = [
  { title: '订单号', dataIndex: 'orderNo', key: 'orderNo' },
  { title: '客户', dataIndex: 'customer', key: 'customer' },
  { title: '产品', dataIndex: 'product', key: 'product' },
  { title: '金额', dataIndex: 'amount', key: 'amount' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '时间', dataIndex: 'time', key: 'time' },
];

const orderData = ref([
  { id: 1, orderNo: 'ORD-20240521-001', customer: '上海建工集团', product: '石英石板材A-500 x 200', amount: 48500, status: '已完成', time: '2024-05-21 14:30' },
  { id: 2, orderNo: 'ORD-20240521-002', customer: '杭州绿城装饰', product: '大理石瓷砖M-200 x 150', amount: 32500, status: '生产中', time: '2024-05-21 13:15' },
  { id: 3, orderNo: 'ORD-20240521-003', customer: '广州建筑设计院', product: '岩板YB-800 x 80', amount: 28000, status: '待发货', time: '2024-05-21 11:42' },
  { id: 4, orderNo: 'ORD-20240521-004', customer: '北京金隅集团', product: '防水涂料WP-100 x 500', amount: 15600, status: '已完成', time: '2024-05-21 10:08' },
  { id: 5, orderNo: 'ORD-20240521-005', customer: '深圳万科地产', product: '木地板WD-300 x 300', amount: 42000, status: '待审核', time: '2024-05-21 09:30' },
  { id: 6, orderNo: 'ORD-20240520-015', customer: '成都兴城集团', product: '仿古砖AG-600 x 120', amount: 18900, status: '已完成', time: '2024-05-20 17:20' },
  { id: 7, orderNo: 'ORD-20240520-014', customer: '武汉城建集团', product: '水泥自流平CP-50 x 400', amount: 11300, status: '已取消', time: '2024-05-20 15:45' },
]);

const statusColor = (status: string) => {
  const map: Record<string, string> = { '已完成': 'green', '生产中': 'blue', '待发货': 'orange', '待审核': 'gold', '已取消': 'red' };
  return map[status] || 'default';
};

// ── Sidebar ──
const todayRevenue = ref(186420);
const todayRevenueGrowth = ref(8.5);
const todayOrders = ref(56);
const todayOrderGrowth = ref(12.3);
const todayVisitors = ref(3245);
const todayVisitorDecline = ref(3.2);

const pendingTasks = ref([
  { id: 1, title: '审核新入驻供应商资质', time: '2小时前', priority: 'high', done: false },
  { id: 2, title: '处理客户投诉 #TKT-4582', time: '3小时前', priority: 'high', done: false },
  { id: 3, title: '更新产品页SEO信息', time: '5小时前', priority: 'medium', done: false },
  { id: 4, title: '确认下月采购计划', time: '6小时前', priority: 'medium', done: true },
  { id: 5, title: '整理本周销售周报', time: '1天前', priority: 'low', done: false },
  { id: 6, title: '备份客户数据库', time: '1天前', priority: 'low', done: true },
]);

const announcements = ref([
  { id: 1, text: '优丁建材3.0版本将于6月1日上线，新增AI智能匹配功能', time: '1小时前', color: '#f5222d' },
  { id: 2, text: '系统维护通知：5月25日凌晨2:00-4:00进行数据库升级', time: '3小时前', color: '#faad14' },
  { id: 3, text: '2024年度建材行业白皮书已发布，可前往下载', time: '5小时前', color: '#1890ff' },
]);

// ── Methods ──
function formatMoney(v: number): string {
  return v.toLocaleString('zh-CN');
}

function handleSearch() {
  if (!searchKeyword.value.trim()) {
    message.warning('请输入搜索关键词');
    return;
  }
  message.success(`已搜索：${searchKeyword.value}`);
}

function refreshAll() {
  message.success('数据已刷新');
}

function handleOrderSearch(v: string) {
  if (!v.trim()) {
    message.warning('请输入订单关键词');
    return;
  }
  message.success(`已筛选订单：${v}`);
}
</script>

<style scoped>
/* ===== Data Cockpit — KingLiu Style ===== */
.data-cockpit {
  min-height: 100vh;
  background: #f0f2f5;
  padding: 20px 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* -- Top Bar -- */
.cockpit-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.cockpit-search {
  position: relative;
  width: 420px;
}
.cockpit-search .search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #bfbfbf;
  font-size: 16px;
  z-index: 1;
}
.search-input {
  width: 100%;
  height: 42px;
  padding: 0 80px 0 42px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  background: #fff;
  font-size: 14px;
  color: #333;
  outline: none;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.search-input:focus {
  border-color: #7265e6;
  box-shadow: 0 2px 12px rgba(114,101,230,0.15);
}
.search-shortcut {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  color: #999;
}
.cockpit-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* -- Header -- */
.cockpit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.cockpit-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 4px 0;
}
.header-right {
  display: flex;
  gap: 12px;
}

/* -- KPI Row -- */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.kpi-card {
  background: #fff;
  border-radius: 16px;
  padding: 18px 16px 14px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}
.kpi-bg-decor {
  position: absolute;
  top: -30px;
  right: -30px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  opacity: 0.12;
}
.kpi-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}
.kpi-info {
  display: flex;
  flex-direction: column;
}
.kpi-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 6px;
}
.kpi-value {
  display: flex;
  align-items: baseline;
  margin-bottom: 4px;
}
.kpi-number {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
}
.kpi-unit {
  font-size: 13px;
  color: #8c8c8c;
  margin-left: 4px;
}
.kpi-sub {
  font-size: 12px;
  color: #bfbfbf;
}
.kpi-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-icon {
  font-size: 22px;
  color: #fff;
}
.kpi-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  position: relative;
  z-index: 1;
}
.kpi-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
}
.trend-up { color: #52c41a; }
.trend-down { color: #ff4d4f; }
.kpi-compare {
  font-size: 12px;
  color: #bfbfbf;
}

/* -- Main Body -- */
.cockpit-body {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.cockpit-main {
  flex: 1;
  min-width: 0;
}
.cockpit-sidebar {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* -- Chart Section -- */
.chart-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
  margin-bottom: 16px;
}
.chart-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.chart-large {
  grid-column: 1 / -1;
}
.chart-full {
  margin-bottom: 0;
}
.chart-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.chart-card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}
.chart-tabs {
  display: flex;
  gap: 4px;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 3px;
}
.chart-tab {
  padding: 4px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #8c8c8c;
  cursor: pointer;
  transition: all 0.2s;
}
.chart-tab.active {
  background: #fff;
  color: #7265e6;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.chart-link {
  font-size: 13px;
  color: #7265e6;
  text-decoration: none;
}
.chart-card-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.chart-body {
  position: relative;
}

/* -- Revenue Summary -- */
.revenue-summary {
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}
.summary-label { font-size: 13px; color: #8c8c8c; display: block; }
.summary-val { font-size: 20px; font-weight: 700; color: #1a1a2e; display: block; margin-top: 2px; }

/* -- Trend Chart (CSS) -- */
.trend-chart {
  display: flex;
  height: 200px;
}
.trend-y-axis {
  display: flex;
  flex-direction: column-reverse;
  justify-content: space-between;
  padding-right: 10px;
  font-size: 12px;
  color: #bfbfbf;
  flex-shrink: 0;
}
.trend-plot {
  flex: 1;
  position: relative;
}
.trend-grid {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.grid-line {
  height: 1px;
  background: #f0f0f0;
}
.trend-line {
  width: 100%;
  height: 100%;
}
.trend-x-axis {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #bfbfbf;
  margin-top: 4px;
}

/* -- Rank List -- */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rank-num {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #8c8c8c;
  background: #f5f5f5;
  flex-shrink: 0;
}
.rank-num.top-1 { background: #ffd700; color: #fff; }
.rank-num.top-2 { background: #c0c0c0; color: #fff; }
.rank-num.top-3 { background: #cd7f32; color: #fff; }
.rank-name {
  font-size: 13px;
  color: #333;
  flex-shrink: 0;
  width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rank-bar-wrap {
  flex: 1;
  height: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}
.rank-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
}
.rank-val {
  font-size: 13px;
  color: #8c8c8c;
  flex-shrink: 0;
}

/* -- Funnel -- */
.funnel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.funnel-stage {
  display: flex;
  align-items: center;
  gap: 8px;
}
.funnel-bar {
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  min-width: 60px;
  transition: width 0.8s ease;
}
.funnel-name { font-size: 13px; color: #fff; font-weight: 500; }
.funnel-val { font-size: 13px; color: #fff; font-weight: 600; }
.funnel-rate { font-size: 12px; color: #8c8c8c; flex-shrink: 0; }

/* -- Amount Cell -- */
.amount-cell {
  font-weight: 600;
  color: #f5576c;
}

/* -- Sidebar -- */
.side-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.side-title {
  margin: 0 0 14px 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}
.side-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.side-title-row .side-title { margin-bottom: 0; }
.side-link { font-size: 13px; color: #7265e6; text-decoration: none; }

/* -- Today Stats -- */
.today-stats {
  display: flex;
  gap: 12px;
}
.today-stat {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  background: #fafafa;
  border-radius: 12px;
}
.today-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}
.today-label {
  display: block;
  font-size: 12px;
  color: #8c8c8c;
  margin: 4px 0;
}
.today-trend {
  font-size: 12px;
  font-weight: 600;
}

/* -- Task List -- */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.task-item:hover {
  background: #fafafa;
}
.task-item.done {
  opacity: 0.5;
}
.task-check {
  font-size: 18px;
  color: #d9d9d9;
  flex-shrink: 0;
}
.done-icon { color: #52c41a; }
.task-info {
  flex: 1;
  min-width: 0;
}
.task-title {
  display: block;
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-item.done .task-title {
  text-decoration: line-through;
}
.task-time {
  font-size: 12px;
  color: #bfbfbf;
}

/* -- Announcements -- */
.announce-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.announce-item {
  display: flex;
  gap: 10px;
}
.announce-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.announce-content {
  flex: 1;
}
.announce-text {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  display: block;
}
.announce-time {
  font-size: 12px;
  color: #bfbfbf;
  margin-top: 2px;
}

/* Responsive */
@media (max-width: 1400px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .cockpit-sidebar { width: 320px; }
}
@media (max-width: 1100px) {
  .cockpit-body { flex-direction: column; }
  .cockpit-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .side-card { flex: 1; min-width: 280px; }
}
</style>
