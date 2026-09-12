<template>
  <div class="saas-dashboard">
    <!-- SaaS Top Bar: Tenant Switcher + Global Actions -->
    <div class="saas-topbar">
      <div class="saas-tenant-area">
        <div class="saas-logo">
          <AppstoreOutlined class="saas-logo-icon" />
          <span class="saas-logo-text">优丁建材</span>
        </div>
        <a-dropdown trigger="click">
          <div class="saas-tenant-switcher">
            <div class="tenant-avatar" :style="{ background: currentTenant.color }">
              {{ currentTenant.name.charAt(0) }}
            </div>
            <div class="tenant-info">
              <span class="tenant-name">{{ currentTenant.name }}</span>
              <span class="tenant-plan">{{ currentTenant.plan }}</span>
            </div>
            <SwapOutlined class="tenant-switch-icon" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="t in tenantList" :key="t.id" @click="switchTenant(t)">
                <div class="tenant-menu-item">
                  <div class="tenant-avatar-small" :style="{ background: t.color }">{{ t.name.charAt(0) }}</div>
                  <div>
                    <div>{{ t.name }}</div>
                    <div class="tenant-menu-plan">{{ t.plan }}</div>
                  </div>
                </div>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
      <div class="saas-top-actions">
        <a-badge :count="5" :number-style="{ backgroundColor: '#f5222d' }">
          <BellOutlined class="saas-icon-btn" />
        </a-badge>
        <a-badge :count="12" :number-style="{ backgroundColor: '#1890ff' }">
          <MailOutlined class="saas-icon-btn" />
        </a-badge>
        <a-avatar :size="34" style="background: #1677ff;">刘</a-avatar>
        <a-dropdown>
          <DownOutlined class="saas-icon-btn" style="font-size:12px" />
          <template #overlay>
            <a-menu>
              <a-menu-item key="account">账号管理</a-menu-item>
              <a-menu-item key="billing">计费中心</a-menu-item>
              <a-menu-item key="logout">退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- Subscription Banner -->
    <div class="saas-banner" v-if="showBanner">
      <div class="banner-icon">
        <ExclamationCircleOutlined />
      </div>
      <div class="banner-content">
        <span class="banner-title">您的{{ currentTenant.plan }}套餐即将到期</span>
        <span class="banner-desc">剩余 {{ daysUntilExpire }} 天，到期后将限制部分功能。建议续费以保持服务连续性。</span>
      </div>
      <div class="banner-actions">
        <a-button type="primary" size="small">立即续费</a-button>
        <a-button size="small" @click="showBanner = false">知道了</a-button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="saas-content">
      <!-- Left: Quick Entry Grid -->
      <div class="saas-sidebar">
        <h3 class="saas-section-title">快捷功能</h3>
        <div class="saas-quick-entries">
          <div v-for="entry in quickEntries" :key="entry.label" class="quick-entry" @click="handleQuickEntry(entry.label)">
            <div class="quick-entry-icon" :style="{ background: entry.bg, color: entry.color }">
              <component :is="entry.icon" />
            </div>
            <span class="quick-entry-label">{{ entry.label }}</span>
          </div>
        </div>

        <h3 class="saas-section-title">活动日志</h3>
        <div class="saas-activity-log">
          <div v-for="log in activityLogs" :key="log.id" class="activity-item">
            <div class="activity-dot" :style="{ background: log.color }" />
            <div class="activity-content">
              <span class="activity-text">{{ log.text }}</span>
              <span class="activity-time">{{ log.time }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Dashboard Area -->
      <div class="saas-main">
        <!-- SaaS Metrics: MRR / ARR / Churn / Retention -->
        <div class="saas-metrics-row">
          <div class="saas-metric-card" v-for="m in saasMetrics" :key="m.label">
            <div class="saas-metric-label">{{ m.label }}</div>
            <div class="saas-metric-value">
              {{ m.value }}
              <span class="saas-metric-trend" :class="m.trendUp ? 'up' : 'down'">
                <component :is="m.trendUp ? ArrowUpOutlined : ArrowDownOutlined" />
                {{ m.change }}
              </span>
            </div>
            <div class="saas-metric-sub">{{ m.sub }}</div>
          </div>
        </div>

        <!-- Charts Row -->
        <div class="saas-chart-row">
          <div class="saas-card chart-main">
            <div class="saas-card-header">
              <h3>收入趋势</h3>
              <a-segmented v-model:value="revenuePeriod" :options="revenuePeriods" size="small" />
            </div>
            <div class="saas-card-body">
              <div class="saas-bar-chart">
                <div class="saas-bar-grid">
                  <div class="saas-bar-y">
                    <span v-for="y in ['¥50万','¥40万','¥30万','¥20万','¥10万','0']" :key="y">{{ y }}</span>
                  </div>
                  <div class="saas-bar-plot">
                    <div class="saas-bar-group" v-for="(bar, i) in revenueBars" :key="i">
                      <div class="saas-bar-pair">
                        <div class="saas-bar mrr" :style="{ height: bar.mrrH + '%' }">
                          <span class="saas-bar-tip">¥{{ bar.mrr }}</span>
                        </div>
                        <div class="saas-bar arr" :style="{ height: bar.arrH + '%' }">
                          <span class="saas-bar-tip">¥{{ bar.arr }}</span>
                        </div>
                      </div>
                      <span class="saas-bar-label">{{ bar.label }}</span>
                    </div>
                  </div>
                </div>
                <div class="saas-bar-legend">
                  <span><span class="legend-color" style="background:#1677ff" /> MRR</span>
                  <span><span class="legend-color" style="background:#52c41a" /> ARR</span>
                </div>
              </div>
            </div>
          </div>

          <div class="saas-card chart-side">
            <div class="saas-card-header">
              <h3>客户分布</h3>
            </div>
            <div class="saas-card-body">
              <div class="saas-donut">
                <svg viewBox="0 0 160 160" class="donut-svg">
                  <circle cx="80" cy="80" r="56" fill="none" stroke="#f0f0f0" stroke-width="18" />
                  <circle cx="80" cy="80" r="56" fill="none" stroke="#1677ff" stroke-width="18"
                    stroke-dasharray="140 352" stroke-linecap="round" transform="rotate(-90 80 80)" />
                  <circle cx="80" cy="80" r="56" fill="none" stroke="#52c41a" stroke-width="18"
                    stroke-dasharray="95 352" stroke-linecap="round" transform="rotate(50 80 80)" />
                  <circle cx="80" cy="80" r="56" fill="none" stroke="#faad14" stroke-width="18"
                    stroke-dasharray="65 352" stroke-linecap="round" transform="rotate(145 80 80)" />
                  <circle cx="80" cy="80" r="56" fill="none" stroke="#ff4d4f" stroke-width="18"
                    stroke-dasharray="52 352" stroke-linecap="round" transform="rotate(210 80 80)" />
                  <text x="80" y="76" text-anchor="middle" font-size="22" font-weight="700" fill="#262626">3,862</text>
                  <text x="80" y="95" text-anchor="middle" font-size="12" fill="#8c8c8c">总客户</text>
                </svg>
                <div class="donut-legend">
                  <div v-for="item in customerSegments" :key="item.name" class="donut-legend-item">
                    <span class="legend-color" :style="{ background: item.color }" />
                    <span>{{ item.name }}</span>
                    <span class="legend-pct">{{ item.percent }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Customer Table -->
        <div class="saas-card table-card">
          <div class="saas-card-header">
            <h3>客户列表</h3>
            <div class="saas-card-tools">
              <a-input-search v-model:value="customerSearch" placeholder="搜索客户" style="width:200px" />
              <a-button type="primary" size="small"><PlusOutlined /> 新增</a-button>
            </div>
          </div>
          <div class="saas-card-body">
            <a-table
              :columns="customerColumns"
              :data-source="customerData"
              :pagination="{ pageSize: 5, showSizeChanger: true }"
              :row-key="(r: any) => r.id"
              size="middle"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'name'">
                  <div class="customer-cell">
                    <a-avatar :size="32" :style="{ background: record.avatarColor }">{{ record.name.charAt(0) }}</a-avatar>
                    <div>
                      <div class="cust-name">{{ record.name }}</div>
                      <div class="cust-company">{{ record.company }}</div>
                    </div>
                  </div>
                </template>
                <template v-if="column.key === 'plan'">
                  <a-tag :color="record.planColor">{{ record.plan }}</a-tag>
                </template>
                <template v-if="column.key === 'status'">
                  <a-badge :status="record.status === 'active' ? 'success' : 'error'"
                    :text="record.status === 'active' ? '活跃' : '流失'" />
                </template>
                <template v-if="column.key === 'mrr'">
                  <span class="mrr-cell">¥{{ record.mrr.toLocaleString() }}</span>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  AppstoreOutlined,
  SwapOutlined,
  BellOutlined,
  MailOutlined,
  DownOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ShoppingCartOutlined,
  TeamOutlined,
  FileTextOutlined,
  SettingOutlined,
  BarChartOutlined,
  SafetyOutlined,
  RobotOutlined,
  ApiOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';

// ── Tenant ──
const currentTenant = ref({ id: 1, name: '优丁建材总部', plan: '企业版', color: '#1677ff' });
const daysUntilExpire = ref(28);
const showBanner = ref(true);

const tenantList = ref([
  { id: 1, name: '优丁建材总部', plan: '企业版', color: '#1677ff' },
  { id: 2, name: '华南分公司', plan: '专业版', color: '#52c41a' },
  { id: 3, name: '华东分公司', plan: '专业版', color: '#faad14' },
  { id: 4, name: '优丁建材国际', plan: '旗舰版', color: '#722ed1' },
]);

function switchTenant(t: typeof currentTenant.value) {
  currentTenant.value = t;
}

// ── Quick Entries ──
const quickEntries = ref([
  { label: '产品管理', icon: ShoppingCartOutlined, bg: '#e6f4ff', color: '#1677ff' },
  { label: '客户管理', icon: TeamOutlined, bg: '#f6ffed', color: '#52c41a' },
  { label: '内容中心', icon: FileTextOutlined, bg: '#fff7e6', color: '#faad14' },
  { label: '系统设置', icon: SettingOutlined, bg: '#f9f0ff', color: '#722ed1' },
  { label: '数据报表', icon: BarChartOutlined, bg: '#fff1f0', color: '#ff4d4f' },
  { label: '安全中心', icon: SafetyOutlined, bg: '#e6fffb', color: '#13c2c2' },
  { label: 'AI 助手', icon: RobotOutlined, bg: '#f0f5ff', color: '#2f54eb' },
  { label: 'API 管理', icon: ApiOutlined, bg: '#fff0f6', color: '#eb2f96' },
  { label: '营销工具', icon: ThunderboltOutlined, bg: '#fcffe6', color: '#7cb305' },
]);

function handleQuickEntry(label: string) {
  // Placeholder for navigation
}

// ── Activity Logs ──
const activityLogs = ref([
  { id: 1, text: '张三 新增产品「岩板 YB-900」', time: '2分钟前', color: '#1677ff' },
  { id: 2, text: 'AI 完成 5 篇产品文案生成', time: '15分钟前', color: '#52c41a' },
  { id: 3, text: '李四 导出了月度销售报表', time: '1小时前', color: '#faad14' },
  { id: 4, text: '王五 更新了客户跟进记录', time: '2小时前', color: '#722ed1' },
  { id: 5, text: '系统自动备份数据库完成', time: '4小时前', color: '#8c8c8c' },
  { id: 6, text: '新客户「杭州绿城装饰」注册', time: '5小时前', color: '#ff4d4f' },
  { id: 7, text: '赵六 提交了询盘处理结果', time: '6小时前', color: '#13c2c2' },
]);

// ── SaaS Metrics ──
const saasMetrics = ref([
  { label: 'MRR (月经常性收入)', value: '¥486,500', trendUp: true, change: '8.5%', sub: '较上月' },
  { label: 'ARR (年经常性收入)', value: '¥5,838,000', trendUp: true, change: '12.3%', sub: '较去年' },
  { label: '客户流失率', value: '2.4%', trendUp: false, change: '0.3%', sub: '较上月' },
  { label: '客户续费率', value: '94.8%', trendUp: true, change: '1.2%', sub: '较上月' },
]);

// ── Revenue Bars ──
const revenuePeriod = ref('monthly');
const revenuePeriods = ref(['月度', '季度', '年度']);
const revenueBars = ref([
  { label: '1月', mrr: '38.6万', arr: '463万', mrrH: 72, arrH: 85 },
  { label: '2月', mrr: '35.2万', arr: '422万', mrrH: 66, arrH: 78 },
  { label: '3月', mrr: '42.8万', arr: '514万', mrrH: 80, arrH: 88 },
  { label: '4月', mrr: '46.5万', arr: '558万', mrrH: 88, arrH: 92 },
  { label: '5月', mrr: '48.6万', arr: '584万', mrrH: 91, arrH: 95 },
  { label: '6月', mrr: '52.0万', arr: '624万', mrrH: 98, arrH: 100 },
]);

// ── Customer Segments ──
const customerSegments = ref([
  { name: '大型企业', percent: 40, color: '#1677ff' },
  { name: '中小企业', percent: 27, color: '#52c41a' },
  { name: '个体商户', percent: 18, color: '#faad14' },
  { name: '个人用户', percent: 15, color: '#ff4d4f' },
]);

// ── Customer Table ──
const customerSearch = ref('');
const customerColumns = [
  { title: '客户名称', dataIndex: 'name', key: 'name', width: 220 },
  { title: '套餐', dataIndex: 'plan', key: 'plan', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: 'MRR', dataIndex: 'mrr', key: 'mrr', width: 120 },
  { title: '到期日期', dataIndex: 'expireDate', key: 'expireDate', width: 120 },
  { title: '联系人', dataIndex: 'contact', key: 'contact', width: 100 },
];

const customerData = ref([
  { id: 1, name: '上海建工集团', company: '建筑行业', plan: '企业版', planColor: 'blue', status: 'active', mrr: 9800, expireDate: '2025-05-21', contact: '张三', avatarColor: '#1677ff' },
  { id: 2, name: '杭州绿城装饰', company: '装修行业', plan: '专业版', planColor: 'green', status: 'active', mrr: 4800, expireDate: '2024-12-15', contact: '李四', avatarColor: '#52c41a' },
  { id: 3, name: '广州建筑设计院', company: '设计行业', plan: '企业版', planColor: 'blue', status: 'active', mrr: 12600, expireDate: '2025-08-03', contact: '王五', avatarColor: '#722ed1' },
  { id: 4, name: '北京金隅集团', company: '建材行业', plan: '旗舰版', planColor: 'purple', status: 'active', mrr: 25800, expireDate: '2026-01-12', contact: '赵六', avatarColor: '#faad14' },
  { id: 5, name: '深圳万科地产', company: '地产行业', plan: '企业版', planColor: 'blue', status: 'active', mrr: 15000, expireDate: '2025-03-28', contact: '孙七', avatarColor: '#ff4d4f' },
  { id: 6, name: '成都兴城集团', company: '建筑行业', plan: '专业版', planColor: 'green', status: 'churned', mrr: 0, expireDate: '2024-06-30', contact: '周八', avatarColor: '#8c8c8c' },
  { id: 7, name: '武汉城建集团', company: '建筑行业', plan: '基础版', planColor: 'orange', status: 'active', mrr: 2400, expireDate: '2024-11-20', contact: '吴九', avatarColor: '#13c2c2' },
]);
</script>

<style scoped>
/* ===== SaaS Dashboard Style ===== */
.saas-dashboard {
  min-height: 100vh;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* -- Top Bar -- */
.saas-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.saas-tenant-area {
  display: flex;
  align-items: center;
  gap: 16px;
}
.saas-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}
.saas-logo-icon {
  font-size: 22px;
  color: #1677ff;
}
.saas-logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #262626;
}
.saas-tenant-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}
.saas-tenant-switcher:hover {
  border-color: #1677ff;
  background: #e6f4ff;
}
.tenant-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}
.tenant-info {
  display: flex;
  flex-direction: column;
}
.tenant-name {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}
.tenant-plan {
  font-size: 12px;
  color: #8c8c8c;
}
.tenant-switch-icon {
  font-size: 13px;
  color: #8c8c8c;
}
.tenant-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tenant-avatar-small {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}
.tenant-menu-plan {
  font-size: 12px;
  color: #8c8c8c;
}
.saas-top-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}
.saas-icon-btn {
  font-size: 17px;
  color: #595959;
  cursor: pointer;
  transition: color 0.2s;
}
.saas-icon-btn:hover { color: #1677ff; }

/* -- Banner -- */
.saas-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 16px 24px 0;
  padding: 14px 20px;
  background: linear-gradient(135deg, #fff7e6, #fffbe6);
  border: 1px solid #ffe58f;
  border-radius: 12px;
}
.banner-icon {
  font-size: 22px;
  color: #faad14;
}
.banner-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.banner-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}
.banner-desc {
  font-size: 13px;
  color: #8c8c8c;
  margin-top: 2px;
}
.banner-actions {
  display: flex;
  gap: 8px;
}

/* -- Content -- */
.saas-content {
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  align-items: flex-start;
}
.saas-sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.saas-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.saas-section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #595959;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* -- Quick Entries -- */
.saas-quick-entries {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 12px;
}
.quick-entry {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 6px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.quick-entry:hover {
  background: #fafafa;
}
.quick-entry-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.quick-entry-label {
  font-size: 12px;
  color: #595959;
}

/* -- Activity Log -- */
.saas-activity-log {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.activity-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.activity-content {
  flex: 1;
  min-width: 0;
}
.activity-text {
  font-size: 13px;
  color: #434343;
  line-height: 1.4;
}
.activity-time {
  font-size: 11px;
  color: #bfbfbf;
  margin-top: 2px;
  display: block;
}

/* -- SaaS Metrics -- */
.saas-metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.saas-metric-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 20px;
}
.saas-metric-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 8px;
}
.saas-metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.saas-metric-trend {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 2px;
}
.saas-metric-trend.up { color: #52c41a; }
.saas-metric-trend.down { color: #ff4d4f; }
.saas-metric-sub {
  font-size: 12px;
  color: #bfbfbf;
  margin-top: 4px;
}

/* -- Charts -- */
.saas-chart-row {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 14px;
}
.saas-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
}
.saas-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px 0;
}
.saas-card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #262626;
}
.saas-card-body {
  padding: 16px 20px 20px;
}
.saas-card-tools {
  display: flex;
  gap: 8px;
}

/* -- Bar Chart -- */
.saas-bar-chart {
  height: 260px;
}
.saas-bar-grid {
  display: flex;
  gap: 8px;
  height: 230px;
}
.saas-bar-y {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 11px;
  color: #bfbfbf;
  padding-right: 6px;
  text-align: right;
  flex-shrink: 0;
}
.saas-bar-plot {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
}
.saas-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  position: relative;
}
.saas-bar-pair {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  position: relative;
  height: 200px;
}
.saas-bar {
  width: 28px;
  border-radius: 4px 4px 0 0;
  position: relative;
  transition: height 0.6s ease;
  display: flex;
  justify-content: center;
  cursor: pointer;
}
.saas-bar:hover .saas-bar-tip {
  opacity: 1;
}
.saas-bar.mrr { background: #1677ff; }
.saas-bar.arr { background: #52c41a; opacity: 0.6; }
.saas-bar-tip {
  position: absolute;
  top: -22px;
  font-size: 11px;
  color: #262626;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s;
  white-space: nowrap;
}
.saas-bar-label {
  font-size: 12px;
  color: #bfbfbf;
}
.saas-bar-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  font-size: 12px;
  color: #8c8c8c;
  align-items: center;
}
.legend-color {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 6px;
}

/* -- Donut -- */
.saas-donut {
  display: flex;
  align-items: center;
  gap: 20px;
}
.donut-svg {
  width: 140px;
  height: 140px;
  flex-shrink: 0;
}
.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.donut-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #595959;
}
.legend-pct {
  font-weight: 600;
  color: #262626;
}

/* -- Customer Table -- */
.table-card .saas-card-body {
  padding: 0;
}
.customer-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cust-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}
.cust-company {
  font-size: 12px;
  color: #bfbfbf;
}
.mrr-cell {
  font-weight: 600;
  color: #1677ff;
}

/* Responsive */
@media (max-width: 1300px) {
  .saas-content { flex-direction: column; }
  .saas-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .saas-quick-entries { grid-template-columns: repeat(9, 1fr); width: 100%; }
  .saas-metrics-row { grid-template-columns: repeat(2, 1fr); }
  .saas-chart-row { grid-template-columns: 1fr; }
}
</style>
