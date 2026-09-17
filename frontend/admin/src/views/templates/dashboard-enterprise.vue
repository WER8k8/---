/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="enterprise-dashboard">
    <!-- Breadcrumb + User -->
    <div class="ent-topbar">
      <div class="ent-breadcrumb">
        <a-breadcrumb>
          <a-breadcrumb-item>
            <HomeOutlined />
          </a-breadcrumb-item>
          <a-breadcrumb-item>工作台</a-breadcrumb-item>
          <a-breadcrumb-item>数据概览</a-breadcrumb-item>
        </a-breadcrumb>
      </div>
      <div class="ent-user-area">
        <a-badge :count="unreadNotices" :overflow-count="99" :number-style="{ backgroundColor: '#ff4d4f' }">
          <BellOutlined class="ent-icon-btn" />
        </a-badge>
        <a-badge dot :number-style="{ backgroundColor: '#52c41a' }">
          <MailOutlined class="ent-icon-btn" />
        </a-badge>
        <a-dropdown>
          <div class="ent-avatar-area">
            <a-avatar :size="36" style="background: #165dff;">王</a-avatar>
            <div class="ent-user-info">
              <span class="ent-user-name">王建国</span>
              <span class="ent-user-role">系统管理员</span>
            </div>
            <DownOutlined class="ent-drop-icon" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile"><UserOutlined /> 个人中心</a-menu-item>
              <a-menu-item key="settings"><SettingOutlined /> 账号设置</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout"><LogoutOutlined /> 退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- Welcome -->
    <div class="ent-welcome">
      <h1 class="ent-page-title">数据概览</h1>
      <p class="ent-welcome-sub">早上好，王建国。以下是您关注的业务数据汇总。</p>
      <span class="ent-update-time">数据更新于 {{ updateTime }}</span>
    </div>

    <!-- Quick Actions Float -->
    <div class="ent-quick-actions">
      <a-button type="primary" size="large">
        <template #icon><PlusOutlined /></template>
        新增产品
      </a-button>
      <a-button size="large">
        <template #icon><ImportOutlined /></template>
        批量导入
      </a-button>
      <a-button size="large">
        <template #icon><ExportOutlined /></template>
        导出报表
      </a-button>
      <div class="ent-date-picker">
        <a-range-picker
          v-model:value="dateRange"
          :placeholder="['开始日期', '结束日期']"
          size="large"
          @change="refreshAll"
        />
      </div>
    </div>

    <!-- Stats Row: 4 Columns -->
    <div class="ent-stats-row">
      <div class="ent-stat-card" v-for="(stat, idx) in statsData" :key="idx">
        <div class="ent-stat-icon" :style="{ background: stat.color }">
          <component :is="stat.icon" />
        </div>
        <div class="ent-stat-body">
          <span class="ent-stat-label">{{ stat.label }}</span>
          <span class="ent-stat-value">
            {{ stat.value }}<small v-if="stat.unit">{{ stat.unit }}</small>
          </span>
          <span class="ent-stat-desc">{{ stat.desc }}</span>
        </div>
        <div class="ent-stat-trend" :class="stat.trendUp ? 'trend-up' : 'trend-down'">
          <component :is="stat.trendUp ? ArrowUpOutlined : ArrowDownOutlined" />
          {{ stat.trend }}
        </div>
      </div>
    </div>

    <!-- Chart Row -->
    <div class="ent-chart-row">
      <div class="ent-chart-box">
        <div class="ent-chart-header">
          <h3>月度销售趋势</h3>
          <div class="ent-chart-legend">
            <span class="legend-dot" style="background: #165dff" /> 销售额
            <span class="legend-dot" style="background: #00b42a; margin-left: 16px" /> 订单数
          </div>
        </div>
        <div class="ent-chart-body">
          <div class="ent-bar-chart">
            <div class="bar-y-labels">
              <span>100万</span><span>80万</span><span>60万</span><span>40万</span><span>20万</span><span>0</span>
            </div>
            <div class="bar-grid">
              <div v-for="i in 5" :key="i" class="bar-h-line" />
              <div class="bar-columns">
                <div v-for="(bar, i) in barData" :key="i" class="bar-group">
                  <div class="bar-stack">
                    <div class="bar-revenue" :style="{ height: bar.revenueH + '%' }" />
                    <div class="bar-order" :style="{ height: bar.orderH + '%' }" />
                  </div>
                  <span class="bar-label">{{ bar.month }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="ent-chart-box ent-chart-half">
        <div class="ent-chart-header">
          <h3>渠道来源分布</h3>
        </div>
        <div class="ent-chart-body">
          <div class="ent-pie-chart">
            <svg viewBox="0 0 160 160" class="pie-ring">
              <circle cx="80" cy="80" r="60" fill="none" stroke="#f0f0f0" stroke-width="20" />
              <circle cx="80" cy="80" r="60" fill="none" stroke="#165dff" stroke-width="20"
                stroke-dasharray="150 377" stroke-linecap="round" transform="rotate(-90 80 80)" />
              <circle cx="80" cy="80" r="60" fill="none" stroke="#00b42a" stroke-width="20"
                stroke-dasharray="100 377" stroke-linecap="round" transform="rotate(60 80 80)" />
              <circle cx="80" cy="80" r="60" fill="none" stroke="#ff7d00" stroke-width="20"
                stroke-dasharray="70 377" stroke-linecap="round" transform="rotate(160 80 80)" />
              <circle cx="80" cy="80" r="60" fill="none" stroke="#c9cdd4" stroke-width="20"
                stroke-dasharray="57 377" stroke-linecap="round" transform="rotate(230 80 80)" />
              <text x="80" y="75" text-anchor="middle" font-size="22" font-weight="700" fill="#1d2129">2,845</text>
              <text x="80" y="95" text-anchor="middle" font-size="12" fill="#86909c">总询盘数</text>
            </svg>
            <div class="pie-legend">
              <div v-for="ch in channelData" :key="ch.name" class="pie-legend-item">
                <span class="legend-dot" :style="{ background: ch.color }" />
                <span class="legend-name">{{ ch.name }}</span>
                <span class="legend-val">{{ ch.value }} ({{ ch.percent }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="ent-table-section">
      <div class="ent-table-header">
        <div class="ent-table-title">
          <h3>产品管理</h3>
          <span class="ent-table-count">共 {{ productTableData.length }} 条记录</span>
        </div>
        <div class="ent-table-tools">
          <a-input-search
            v-model:value="tableSearch"
            placeholder="搜索产品名称..."
            style="width: 260px"
            @search="filterTable"
          />
          <a-select v-model:value="categoryFilter" style="width: 140px" @change="filterTable" placeholder="全部分类">
            <a-select-option value="">全部分类</a-select-option>
            <a-select-option value="石材">石材</a-select-option>
            <a-select-option value="瓷砖">瓷砖</a-select-option>
            <a-select-option value="涂料">涂料</a-select-option>
            <a-select-option value="板材">板材</a-select-option>
          </a-select>
          <a-select v-model:value="statusFilter" style="width: 120px" @change="filterTable" placeholder="全部状态">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="上架">上架</a-select-option>
            <a-select-option value="下架">下架</a-select-option>
            <a-select-option value="草稿">草稿</a-select-option>
          </a-select>
        </div>
      </div>
      <a-table
        :columns="productColumns"
        :data-source="displayedProductData"
        :pagination="{ pageSize: 8, showSizeChanger: true, showQuickJumper: true, showTotal: (t: number) => `共 ${t} 条` }"
        :row-key="(r: any) => r.id"
        size="middle"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="product-cell">
              <div class="product-avatar" :style="{ background: record.avatarBg }">{{ record.name.charAt(0) }}</div>
              <div>
                <div class="product-name">{{ record.name }}</div>
                <div class="product-code">{{ record.code }}</div>
              </div>
            </div>
          </template>
          <template v-if="column.key === 'price'">
            <span class="price-cell">¥{{ record.price.toLocaleString() }}</span>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === '上架' ? 'green' : record.status === '下架' ? 'red' : 'default'">
              {{ record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'stock'">
            <span :class="{ 'low-stock': record.stock < 50 }">{{ record.stock }}</span>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small">编辑</a-button>
              <a-button type="link" size="small" danger>下架</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  HomeOutlined,
  BellOutlined,
  MailOutlined,
  DownOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  PlusOutlined,
  ImportOutlined,
  ExportOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ShoppingCartOutlined,
  DollarOutlined,
  TeamOutlined,
  RiseOutlined,
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';

// ── State ──
const unreadNotices = ref(12);
const updateTime = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'));
const dateRange = ref<[string, string] | undefined>(undefined);
const tableSearch = ref('');
const categoryFilter = ref('');
const statusFilter = ref('');
const selectedRowKeys = ref<number[]>([]);

// ── Stats ──
const statsData = computed(() => [
  {
    label: '产品总数', value: '1,286', unit: '件',
    desc: '较上月 +32件', icon: ShoppingCartOutlined,
    color: 'linear-gradient(135deg, #165dff, #4080ff)', trendUp: true, trend: '12.5%'
  },
  {
    label: '月销售额', value: '¥486.5', unit: '万',
    desc: '已完成月目标 81%', icon: DollarOutlined,
    color: 'linear-gradient(135deg, #00b42a, #23c343)', trendUp: true, trend: '8.3%'
  },
  {
    label: '客户总数', value: '3,862', unit: '家',
    desc: '本月新增 286家', icon: TeamOutlined,
    color: 'linear-gradient(135deg, #ff7d00, #ff9a2e)', trendUp: true, trend: '18.2%'
  },
  {
    label: '询盘转化率', value: '6.8', unit: '%',
    desc: '较上月 +0.5%', icon: RiseOutlined,
    color: 'linear-gradient(135deg, #f53f3f, #f76560)', trendUp: false, trend: '2.1%'
  },
]);

// ── Bar Chart ──
const barData = ref([
  { month: '1月', revenueH: 45, orderH: 15 },
  { month: '2月', revenueH: 38, orderH: 12 },
  { month: '3月', revenueH: 52, orderH: 18 },
  { month: '4月', revenueH: 61, orderH: 22 },
  { month: '5月', revenueH: 55, orderH: 19 },
  { month: '6月', revenueH: 72, orderH: 25 },
  { month: '7月', revenueH: 68, orderH: 24 },
  { month: '8月', revenueH: 80, orderH: 28 },
  { month: '9月', revenueH: 75, orderH: 26 },
  { month: '10月', revenueH: 88, orderH: 31 },
  { month: '11月', revenueH: 82, orderH: 30 },
  { month: '12月', revenueH: 95, orderH: 35 },
]);

// ── Channel ──
const channelData = ref([
  { name: '百度搜索', value: 1150, percent: 40, color: '#165dff' },
  { name: '阿里巴巴', value: 850, percent: 30, color: '#00b42a' },
  { name: '直接访问', value: 520, percent: 18, color: '#ff7d00' },
  { name: '其他渠道', value: 325, percent: 12, color: '#c9cdd4' },
]);

// ── Product Table ──
const productColumns = [
  { title: '产品名称', dataIndex: 'name', key: 'name', width: 260 },
  { title: '分类', dataIndex: 'category', key: 'category', width: 100 },
  { title: '价格 (元)', dataIndex: 'price', key: 'price', width: 120, sorter: (a: any, b: any) => a.price - b.price },
  { title: '库存', dataIndex: 'stock', key: 'stock', width: 80, sorter: (a: any, b: any) => a.stock - b.stock },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '更新时间', dataIndex: 'updateTime', key: 'updateTime', width: 160, sorter: true },
  { title: '操作', key: 'action', width: 120 },
];

const productTableData = ref([
  { id: 1, name: '石英石板材 A-500', code: 'QS-500', category: '石材', price: 385.00, stock: 1200, status: '上架', updateTime: '2024-05-20 10:30', avatarBg: '#e8f3ff' },
  { id: 2, name: '大理石瓷砖 M-200', code: 'DL-200', category: '瓷砖', price: 218.00, stock: 850, status: '上架', updateTime: '2024-05-19 16:22', avatarBg: '#f0f5ff' },
  { id: 3, name: '防水涂料 WP-100', code: 'FS-100', category: '涂料', price: 156.00, stock: 2300, status: '上架', updateTime: '2024-05-18 14:15', avatarBg: '#e8ffea' },
  { id: 4, name: '岩板 YB-800', code: 'YB-800', category: '板材', price: 520.00, stock: 32, status: '上架', updateTime: '2024-05-17 09:40', avatarBg: '#fff7e8' },
  { id: 5, name: '木地板 WD-300', code: 'WD-300', category: '板材', price: 198.00, stock: 560, status: '上架', updateTime: '2024-05-16 11:00', avatarBg: '#f5f0e8' },
  { id: 6, name: '水泥自流平 CP-50', code: 'CP-50', category: '涂料', price: 85.00, stock: 4200, status: '上架', updateTime: '2024-05-15 15:30', avatarBg: '#f5f5f5' },
  { id: 7, name: '仿古砖 AG-600', code: 'AG-600', category: '瓷砖', price: 142.00, stock: 780, status: '上架', updateTime: '2024-05-14 13:50', avatarBg: '#fff0f0' },
  { id: 8, name: '花岗岩台面 GT-100', code: 'GT-100', category: '石材', price: 680.00, stock: 15, status: '下架', updateTime: '2024-05-13 10:00', avatarBg: '#f0f0f0' },
  { id: 9, name: '玻璃幕墙 BL-500', code: 'BL-500', category: '板材', price: 1250.00, stock: 95, status: '上架', updateTime: '2024-05-12 08:45', avatarBg: '#e8f8ff' },
  { id: 10, name: '环保乳胶漆 EP-200', code: 'EP-200', category: '涂料', price: 320.00, stock: 0, status: '草稿', updateTime: '2024-05-11 17:20', avatarBg: '#fffbe8' },
]);

const displayedProductData = computed(() => {
  let data = productTableData.value;
  if (tableSearch.value) {
    data = data.filter((p) => p.name.includes(tableSearch.value) || p.code.includes(tableSearch.value));
  }
  if (categoryFilter.value) {
    data = data.filter((p) => p.category === categoryFilter.value);
  }
  if (statusFilter.value) {
    data = data.filter((p) => p.status === statusFilter.value);
  }
  return data;
});

function filterTable() {}
function onSelectChange(keys: any[]) {
  selectedRowKeys.value = keys as number[];
}
function refreshAll() {}
</script>

<style scoped>
/* ===== Enterprise Dashboard — UI821 Style ===== */
.enterprise-dashboard {
  min-height: 100vh;
  background: #f7f8fa;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* -- Topbar -- */
.ent-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 28px;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
}
.ent-user-area {
  display: flex;
  align-items: center;
  gap: 18px;
}
.ent-icon-btn {
  font-size: 18px;
  color: #4e5969;
  cursor: pointer;
  transition: color 0.2s;
}
.ent-icon-btn:hover { color: #165dff; }
.ent-avatar-area {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}
.ent-avatar-area:hover { background: #f7f8fa; }
.ent-user-info {
  display: flex;
  flex-direction: column;
}
.ent-user-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.ent-user-role { font-size: 12px; color: #86909c; }
.ent-drop-icon { font-size: 12px; color: #86909c; }

/* -- Welcome Section -- */
.ent-welcome {
  padding: 24px 28px 0;
}
.ent-page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
}
.ent-welcome-sub {
  margin: 6px 0 0 0;
  font-size: 14px;
  color: #86909c;
}
.ent-update-time {
  display: inline-block;
  margin-top: 6px;
  font-size: 12px;
  color: #c9cdd4;
}

/* -- Quick Actions -- */
.ent-quick-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 28px;
}
.ent-date-picker {
  margin-left: auto;
}

/* -- Stats Row -- */
.ent-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 0 28px;
}
.ent-stat-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: box-shadow 0.2s;
}
.ent-stat-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.ent-stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  flex-shrink: 0;
}
.ent-stat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.ent-stat-label {
  font-size: 13px;
  color: #86909c;
}
.ent-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.2;
}
.ent-stat-value small {
  font-size: 14px;
  font-weight: 400;
  color: #86909c;
  margin-left: 4px;
}
.ent-stat-desc {
  font-size: 12px;
  color: #86909c;
  margin-top: 2px;
}
.ent-stat-trend {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}
.trend-up { color: #00b42a; }
.trend-down { color: #f53f3f; }

/* -- Chart Row -- */
.ent-chart-row {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 16px;
  padding: 16px 28px;
}
.ent-chart-box {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 20px;
}
.ent-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.ent-chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}
.ent-chart-legend {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #86909c;
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  margin-right: 6px;
}

/* -- Bar Chart -- */
.ent-bar-chart {
  display: flex;
  height: 260px;
}
.bar-y-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 12px;
  color: #c9cdd4;
  padding-right: 10px;
  text-align: right;
  flex-shrink: 0;
}
.bar-grid {
  flex: 1;
  position: relative;
  overflow: hidden;
}
.bar-h-line {
  position: absolute;
  left: 0;
  right: 0;
  border-top: 1px dashed #f2f3f5;
}
.bar-h-line:nth-child(1) { top: 0; }
.bar-h-line:nth-child(2) { top: 20%; }
.bar-h-line:nth-child(3) { top: 40%; }
.bar-h-line:nth-child(4) { top: 60%; }
.bar-h-line:nth-child(5) { top: 80%; }
.bar-columns {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 100%;
  position: relative;
  z-index: 1;
}
.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.bar-stack {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 220px;
  width: 100%;
  justify-content: center;
}
.bar-revenue {
  width: 12px;
  background: #165dff;
  border-radius: 3px 3px 0 0;
  transition: height 0.6s ease;
}
.bar-order {
  width: 12px;
  background: #00b42a;
  border-radius: 3px 3px 0 0;
  transition: height 0.6s ease;
}
.bar-label {
  font-size: 12px;
  color: #86909c;
}

/* -- Pie Chart -- */
.ent-pie-chart {
  display: flex;
  align-items: center;
  gap: 24px;
}
.pie-ring {
  width: 160px;
  height: 160px;
  flex-shrink: 0;
}
.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pie-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.legend-name {
  color: #4e5969;
  min-width: 70px;
}
.legend-val {
  color: #1d2129;
  font-weight: 600;
}

/* -- Table Section -- */
.ent-table-section {
  margin: 0 28px 28px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
}
.ent-table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid #f2f3f5;
}
.ent-table-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}
.ent-table-count {
  font-size: 13px;
  color: #86909c;
  margin-left: 10px;
}
.ent-table-tools {
  display: flex;
  gap: 10px;
}
.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.product-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #165dff;
  flex-shrink: 0;
}
.product-name {
  font-size: 14px;
  color: #1d2129;
  font-weight: 500;
}
.product-code {
  font-size: 12px;
  color: #c9cdd4;
}
.price-cell {
  font-weight: 600;
  color: #f53f3f;
}
.low-stock {
  color: #f53f3f;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 1400px) {
  .ent-chart-row { grid-template-columns: 1fr; }
  .ent-stats-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 900px) {
  .ent-stats-row { grid-template-columns: 1fr; }
  .ent-quick-actions { flex-wrap: wrap; }
}
</style>
