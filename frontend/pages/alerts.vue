/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="alerts-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-gradient">预警中心</span>
      </h1>
      <div class="header-actions">
        <Button 
          variant="secondary" 
          size="small"
          @click="refreshData"
          :loading="store.loading"
        >
          刷新
        </Button>
        <Button 
          variant="primary" 
          size="small"
          @click="showCreateAlert = true"
        >
          创建预警
        </Button>
      </div>
    </div>

    <div class="stats-grid">
      <Card
        class="stat-card"
        variant="elevated"
      >
        <div class="stat-content">
          <div class="stat-icon critical">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
              />
              <line
                x1="12"
                y1="8"
                x2="12"
                y2="12"
              />
              <line
                x1="12"
                y1="16"
                x2="12.01"
                y2="16"
              />
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ store.statistics?.active_alerts || 0 }}
            </div>
            <div class="stat-label">
              活动预警
            </div>
          </div>
        </div>
      </Card>
      
      <Card
        class="stat-card"
        variant="elevated"
      >
        <div class="stat-content">
          <div class="stat-icon error">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ store.statistics?.total_alerts || 0 }}
            </div>
            <div class="stat-label">
              总预警数
            </div>
          </div>
        </div>
      </Card>
      
      <Card
        class="stat-card"
        variant="elevated"
      >
        <div class="stat-content">
          <div class="stat-icon success">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ store.statistics?.resolved_today || 0 }}
            </div>
            <div class="stat-label">
              今日解决
            </div>
          </div>
        </div>
      </Card>
      
      <Card
        class="stat-card"
        variant="elevated"
      >
        <div class="stat-content">
          <div class="stat-icon info">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
              />
              <line
                x1="12"
                y1="16"
                x2="12"
                y2="12"
              />
              <line
                x1="12"
                y1="8"
                x2="12.01"
                y2="8"
              />
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ store.rules.length }}
            </div>
            <div class="stat-label">
              预警规则
            </div>
          </div>
        </div>
      </Card>
    </div>

    <div class="tabs-container">
      <div class="tabs">
        <button 
          :class="['tab', { active: activeTab === 'alerts' }]"
          @click="activeTab = 'alerts'"
        >
          预警列表
          <span
            v-if="store.activeAlerts.length > 0"
            class="tab-badge"
          >
            {{ store.activeAlerts.length }}
          </span>
        </button>
        <button 
          :class="['tab', { active: activeTab === 'rules' }]"
          @click="activeTab = 'rules'"
        >
          预警规则
        </button>
      </div>

      <div class="filter-bar">
        <div class="filter-group">
          <select 
            v-model="filters.status" 
            class="filter-select"
            @change="fetchData"
          >
            <option value="">
              全部状态
            </option>
            <option value="active">
              活动
            </option>
            <option value="acknowledged">
              已确认
            </option>
            <option value="resolved">
              已解决
            </option>
            <option value="dismissed">
              已忽略
            </option>
          </select>
          
          <select 
            v-model="filters.severity" 
            class="filter-select"
            @change="fetchData"
          >
            <option value="">
              全部级别
            </option>
            <option value="info">
              信息
            </option>
            <option value="warning">
              警告
            </option>
            <option value="error">
              错误
            </option>
            <option value="critical">
              严重
            </option>
          </select>
        </div>
      </div>

      <div
        v-if="activeTab === 'alerts'"
        class="alerts-content"
      >
        <div
          v-if="store.loading"
          class="loading-state"
        >
          <Skeleton
            height="60px"
            count="5"
          />
        </div>
        
        <div
          v-else-if="store.alerts.length === 0"
          class="empty-state"
        >
          <EmptyState 
            title="暂无预警"
            description="系统运行正常，没有触发任何预警"
          />
        </div>
        
        <div
          v-else
          class="alerts-list"
        >
          <div 
            v-for="alert in store.alerts" 
            :key="alert.id"
            :class="['alert-item', alert.severity]"
            @click="viewAlert(alert)"
          >
            <div class="alert-icon">
              <svg
                v-if="alert.severity === 'critical'"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                />
                <line
                  x1="12"
                  y1="8"
                  x2="12"
                  y2="12"
                />
                <line
                  x1="12"
                  y1="16"
                  x2="12.01"
                  y2="16"
                />
              </svg>
              <svg
                v-else-if="alert.severity === 'error'"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <svg
                v-else-if="alert.severity === 'warning'"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                <line
                  x1="12"
                  y1="9"
                  x2="12"
                  y2="13"
                />
                <line
                  x1="12"
                  y1="17"
                  x2="12.01"
                  y2="17"
                />
              </svg>
              <svg
                v-else
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                />
                <line
                  x1="12"
                  y1="16"
                  x2="12"
                  y2="12"
                />
                <line
                  x1="12"
                  y1="8"
                  x2="12.01"
                  y2="8"
                />
              </svg>
            </div>
            
            <div class="alert-content">
              <div class="alert-header">
                <h3 class="alert-title">
                  {{ alert.title }}
                </h3>
                <span :class="['alert-status', alert.status]">
                  {{ getStatusLabel(alert.status) }}
                </span>
              </div>
              <p class="alert-description">
                {{ alert.description }}
              </p>
              <div class="alert-meta">
                <span class="alert-type">{{ getTypeLabel(alert.alert_type) }}</span>
                <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
              </div>
            </div>
            
            <div class="alert-arrow">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="rules-content"
      >
        <div
          v-if="store.loading"
          class="loading-state"
        >
          <Skeleton
            height="60px"
            count="5"
          />
        </div>
        
        <div
          v-else-if="store.rules.length === 0"
          class="empty-state"
        >
          <EmptyState 
            title="暂无预警规则"
            description="创建一些预警规则来监控系统状态"
          >
            <Button @click="showCreateRule = true">
              创建规则
            </Button>
          </EmptyState>
        </div>
        
        <div
          v-else
          class="rules-list"
        >
          <div 
            v-for="rule in store.rules" 
            :key="rule.id"
            :class="['rule-item', { disabled: !rule.enabled }]"
            @click="viewRule(rule)"
          >
            <div class="rule-status">
              <span :class="['status-dot', rule.enabled ? 'active' : 'inactive']" />
            </div>
            
            <div class="rule-content">
              <div class="rule-header">
                <h3 class="rule-title">
                  {{ rule.name }}
                </h3>
                <div class="rule-badges">
                  <span :class="['rule-severity', rule.severity]">
                    {{ getSeverityLabel(rule.severity) }}
                  </span>
                </div>
              </div>
              <p
                v-if="rule.description"
                class="rule-description"
              >
                {{ rule.description }}
              </p>
              <div class="rule-meta">
                <span class="rule-type">{{ getTypeLabel(rule.alert_type) }}</span>
                <span class="rule-trigger-count">触发 {{ rule.trigger_count || 0 }} 次</span>
              </div>
            </div>
            
            <div class="rule-arrow">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Modal 
      v-model:open="showCreateAlert"
      title="创建预警"
      size="medium"
    >
      <form
        @submit.prevent="handleCreateAlert"
        class="alert-form"
      >
        <div class="form-group">
          <label class="form-label">预警类型</label>
          <select
            v-model="newAlert.alert_type"
            class="form-select"
            required
          >
            <option value="system">
              系统
            </option>
            <option value="performance">
              性能
            </option>
            <option value="availability">
              可用性
            </option>
            <option value="data_quality">
              数据质量
            </option>
            <option value="user_behavior">
              用户行为
            </option>
            <option value="business">
              业务
            </option>
            <option value="security">
              安全
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">严重程度</label>
          <select
            v-model="newAlert.severity"
            class="form-select"
            required
          >
            <option value="info">
              信息
            </option>
            <option value="warning">
              警告
            </option>
            <option value="error">
              错误
            </option>
            <option value="critical">
              严重
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">标题</label>
          <input 
            v-model="newAlert.title" 
            type="text" 
            class="form-input" 
            placeholder="输入预警标题"
            required
          >
        </div>
        
        <div class="form-group">
          <label class="form-label">描述</label>
          <textarea 
            v-model="newAlert.description" 
            class="form-textarea" 
            placeholder="输入预警描述"
            rows="4"
            required
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">影响范围</label>
          <input 
            v-model="newAlert.impact_scope" 
            type="text" 
            class="form-input" 
            placeholder="描述影响范围"
          >
        </div>
        
        <div class="form-group">
          <label class="form-label">建议解决方案</label>
          <textarea 
            v-model="newAlert.proposed_solution" 
            class="form-textarea" 
            placeholder="输入建议的解决方案"
            rows="3"
          />
        </div>
        
        <div class="form-actions">
          <Button
            type="button"
            variant="secondary"
            @click="showCreateAlert = false"
          >
            取消
          </Button>
          <Button
            type="submit"
            variant="primary"
          >
            创建
          </Button>
        </div>
      </form>
    </Modal>

    <Modal 
      v-model:open="showCreateRule"
      title="创建预警规则"
      size="medium"
    >
      <form
        @submit.prevent="handleCreateRule"
        class="rule-form"
      >
        <div class="form-group">
          <label class="form-label">规则名称</label>
          <input 
            v-model="newRule.name" 
            type="text" 
            class="form-input" 
            placeholder="输入规则名称"
            required
          >
        </div>
        
        <div class="form-group">
          <label class="form-label">描述</label>
          <textarea 
            v-model="newRule.description" 
            class="form-textarea" 
            placeholder="输入规则描述"
            rows="3"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">预警类型</label>
          <select
            v-model="newRule.alert_type"
            class="form-select"
            required
          >
            <option value="system">
              系统
            </option>
            <option value="performance">
              性能
            </option>
            <option value="availability">
              可用性
            </option>
            <option value="data_quality">
              数据质量
            </option>
            <option value="user_behavior">
              用户行为
            </option>
            <option value="business">
              业务
            </option>
            <option value="security">
              安全
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">严重程度</label>
          <select
            v-model="newRule.severity"
            class="form-select"
            required
          >
            <option value="info">
              信息
            </option>
            <option value="warning">
              警告
            </option>
            <option value="error">
              错误
            </option>
            <option value="critical">
              严重
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">检查间隔（秒）</label>
          <input 
            v-model.number="newRule.check_interval_seconds" 
            type="number" 
            class="form-input" 
            :min="10"
            required
          >
        </div>
        
        <div class="form-group">
          <label class="form-label">启用规则</label>
          <label class="form-toggle">
            <input
              type="checkbox"
              v-model="newRule.enabled"
            >
            <span class="toggle-slider" />
          </label>
        </div>
        
        <div class="form-actions">
          <Button
            type="button"
            variant="secondary"
            @click="showCreateRule = false"
          >
            取消
          </Button>
          <Button
            type="submit"
            variant="primary"
          >
            创建
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAlertsStore } from "~/stores/alerts";
import { useToast } from "~/composables/useToast";
import { useRouter } from "vue-router";

const store = useAlertsStore();
const toast = useToast();
const router = useRouter();

const activeTab = ref("alerts");
const showCreateAlert = ref(false);
const showCreateRule = ref(false);
const filters = ref({
  status: "",
  severity: "",
});

const newAlert = ref({
  alert_type: "system",
  severity: "warning",
  title: "",
  description: "",
  impact_scope: "",
  proposed_solution: "",
});

const newRule = ref({
  name: "",
  description: "",
  alert_type: "system",
  severity: "warning",
  enabled: true,
  check_interval_seconds: 60,
  rule_config: {},
});

async function fetchData() {
  await Promise.all([
    store.fetchAlerts({
      status: filters.value.status || undefined,
      severity: filters.value.severity || undefined,
    }),
    store.fetchRules(),
    store.fetchStatistics(),
  ]);
}

function refreshData() {
  fetchData();
  toast.success("数据已刷新");
}

function viewAlert(alert: any) {
  store.setCurrentAlert(alert);
  router.push(`/alerts/${alert.id}`);
}

function viewRule(rule: any) {
  store.setCurrentRule(rule);
  toast.info("规则详情功能开发中");
}

async function handleCreateAlert() {
  try {
    await store.createAlert(newAlert.value);
    showCreateAlert.value = false;
    newAlert.value = {
      alert_type: "system",
      severity: "warning",
      title: "",
      description: "",
      impact_scope: "",
      proposed_solution: "",
    };
    toast.success("预警创建成功");
  } catch (error) {
    toast.error("创建失败，请重试");
  }
}

async function handleCreateRule() {
  try {
    await store.createRule(newRule.value);
    showCreateRule.value = false;
    newRule.value = {
      name: "",
      description: "",
      alert_type: "system",
      severity: "warning",
      enabled: true,
      check_interval_seconds: 60,
      rule_config: {},
    };
    toast.success("规则创建成功");
  } catch (error) {
    toast.error("创建失败，请重试");
  }
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    active: "活动",
    acknowledged: "已确认",
    resolved: "已解决",
    dismissed: "已忽略",
  };
  return labels[status] || status;
}

function getTypeLabel(type: string) {
  const labels: Record<string, string> = {
    system: "系统",
    performance: "性能",
    availability: "可用性",
    data_quality: "数据质量",
    user_behavior: "用户行为",
    business: "业务",
    security: "安全",
  };
  return labels[type] || type;
}

function getSeverityLabel(severity: string) {
  const labels: Record<string, string> = {
    info: "信息",
    warning: "警告",
    error: "错误",
    critical: "严重",
  };
  return labels[severity] || severity;
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  
  return date.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.alerts-page {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
}

.title-gradient {
  background: var(--color-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: var(--space-3);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  padding: var(--space-5);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.critical {
  background: var(--color-glow-critical);
  color: var(--color-error);
}

.stat-icon.error {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.stat-icon.success {
  background: var(--color-glow-success);
  color: var(--color-success);
}

.stat-icon.info {
  background: var(--color-glow-primary);
  color: var(--color-primary);
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

.tabs-container {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  padding: 0 var(--space-4);
}

.tab {
  padding: var(--space-4) var(--space-6);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.tab:hover {
  color: var(--color-text-primary);
}

.tab.active {
  color: var(--color-primary);
}

.tab.active::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-primary);
}

.tab-badge {
  background: var(--color-error);
  color: white;
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: var(--radius-full);
}

.filter-bar {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.filter-group {
  display: flex;
  gap: var(--space-3);
}

.filter-select {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-select:hover {
  border-color: var(--color-primary);
}

.alerts-content,
.rules-content {
  padding: var(--space-4);
}

.loading-state {
  padding: var(--space-4);
}

.empty-state {
  padding: var(--space-8) var(--space-4);
  text-align: center;
}

.alerts-list,
.rules-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.alert-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.alert-item.critical {
  border-left: 4px solid var(--color-error);
}

.alert-item.error {
  border-left: 4px solid var(--color-error);
}

.alert-item.warning {
  border-left: 4px solid var(--color-warning);
}

.alert-item.info {
  border-left: 4px solid var(--color-primary);
}

.alert-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
}

.alert-item.critical .alert-icon,
.alert-item.error .alert-icon {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.alert-item.warning .alert-icon {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.alert-item.info .alert-icon {
  background: var(--color-glow-primary);
  color: var(--color-primary);
}

.alert-icon svg {
  width: 20px;
  height: 20px;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.alert-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.alert-status {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.alert-status.active {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.alert-status.acknowledged {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.alert-status.resolved {
  background: var(--color-glow-success);
  color: var(--color-success);
}

.alert-status.dismissed {
  background: var(--color-bg-muted);
  color: var(--color-text-muted);
}

.alert-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.alert-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.alert-arrow {
  flex-shrink: 0;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.alert-arrow svg {
  width: 20px;
  height: 20px;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.rule-item:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.rule-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rule-status {
  flex-shrink: 0;
  padding: var(--space-2) 0;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: block;
}

.status-dot.active {
  background: var(--color-success);
  box-shadow: 0 0 8px var(--color-success);
}

.status-dot.inactive {
  background: var(--color-text-muted);
}

.rule-content {
  flex: 1;
  min-width: 0;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.rule-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.rule-badges {
  display: flex;
  gap: var(--space-2);
}

.rule-severity {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.rule-severity.critical {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.rule-severity.error {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.rule-severity.warning {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.rule-severity.info {
  background: var(--color-glow-primary);
  color: var(--color-primary);
}

.rule-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-2);
}

.rule-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.rule-arrow {
  flex-shrink: 0;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.rule-arrow svg {
  width: 20px;
  height: 20px;
}

.alert-form,
.rule-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.form-input,
.form-select,
.form-textarea {
  padding: var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-glow-primary);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
}

.form-toggle input {
  display: none;
}

.toggle-slider {
  width: 48px;
  height: 26px;
  background: var(--color-bg-muted);
  border-radius: var(--radius-full);
  position: relative;
  transition: all var(--transition-fast);
}

.toggle-slider::before {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.form-toggle input:checked + .toggle-slider {
  background: var(--color-primary);
}

.form-toggle input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .alerts-page {
    padding: var(--space-4);
  }
  
  .page-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: flex-start;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-group {
    flex-direction: column;
  }
  
  .filter-select {
    width: 100%;
  }
}
</style>
