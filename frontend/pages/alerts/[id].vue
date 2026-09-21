/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="alert-detail-page">
    <div class="page-header">
      <button
        class="back-button"
        @click="goBack"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
        返回
      </button>
      <h1 class="page-title">
        预警详情
      </h1>
    </div>

    <div
      v-if="loading"
      class="loading-state"
    >
      <Skeleton
        height="200px"
        count="1"
      />
      <Skeleton
        height="100px"
        count="2"
        style="margin-top: 1rem;"
      />
    </div>

    <div
      v-else-if="alert"
      class="alert-content"
    >
      <Card
        class="alert-header-card"
        variant="elevated"
      >
        <div class="alert-header-top">
          <div :class="['alert-icon-big', alert.severity]">
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
          <div class="alert-info">
            <h2 class="alert-title">
              {{ alert.title }}
            </h2>
            <div class="alert-meta-line">
              <span :class="['alert-status-badge', alert.status]">
                {{ getStatusLabel(alert.status) }}
              </span>
              <span :class="['alert-severity-badge', alert.severity]">
                {{ getSeverityLabel(alert.severity) }}
              </span>
              <span class="alert-type-badge">
                {{ getTypeLabel(alert.alert_type) }}
              </span>
            </div>
            <div class="alert-time">
              创建于 {{ formatTime(alert.created_at) }}
              <span v-if="alert.updated_at && alert.updated_at !== alert.created_at">
                · 更新于 {{ formatTime(alert.updated_at) }}
              </span>
            </div>
          </div>
        </div>

        <div
          v-if="alert.status !== 'resolved'"
          class="alert-actions"
        >
          <Button 
            v-if="alert.status !== 'acknowledged'"
            variant="secondary" 
            @click="showAcknowledgeModal = true"
          >
            确认处理
          </Button>
          <Button 
            variant="primary" 
            @click="showResolveModal = true"
          >
            标记解决
          </Button>
        </div>
      </Card>

      <Card class="alert-section">
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
          预警描述
        </h3>
        <p class="alert-description">
          {{ alert.description }}
        </p>
      </Card>

      <Card
        v-if="alert.impact_scope"
        class="alert-section"
      >
        <h3 class="section-title">
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
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
          </svg>
          影响范围
        </h3>
        <p class="alert-text">
          {{ alert.impact_scope }}
        </p>
      </Card>

      <Card
        v-if="alert.proposed_solution"
        class="alert-section"
      >
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          建议解决方案
        </h3>
        <p class="alert-text">
          {{ alert.proposed_solution }}
        </p>
      </Card>

      <Card
        v-if="alert.acknowledged_at"
        class="alert-section"
      >
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
            <circle
              cx="12"
              cy="7"
              r="4"
            />
          </svg>
          确认信息
        </h3>
        <div class="info-row">
          <span class="info-label">确认人</span>
          <span class="info-value">{{ alert.acknowledged_by || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">确认时间</span>
          <span class="info-value">{{ formatTime(alert.acknowledged_at) }}</span>
        </div>
      </Card>

      <Card
        v-if="alert.resolved_at"
        class="alert-section"
      >
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
          </svg>
          解决信息
        </h3>
        <div class="info-row">
          <span class="info-label">解决人</span>
          <span class="info-value">{{ alert.resolved_by || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">解决时间</span>
          <span class="info-value">{{ formatTime(alert.resolved_at) }}</span>
        </div>
        <div
          v-if="alert.resolution_notes"
          class="info-row"
        >
          <span class="info-label">解决说明</span>
          <span class="info-value">{{ alert.resolution_notes }}</span>
        </div>
      </Card>

      <Card class="alert-section">
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle
              cx="12"
              cy="12"
              r="3"
            />
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
          </svg>
          处理历史
        </h3>
        <div
          v-if="histories.length > 0"
          class="history-list"
        >
          <div
            v-for="history in histories"
            :key="history.id"
            class="history-item"
          >
            <div class="history-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="9 11 12 14 22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
            </div>
            <div class="history-content">
              <div class="history-header">
                <span class="history-action">{{ getHistoryActionLabel(history.action_type) }}</span>
                <span class="history-time">{{ formatTime(history.created_at) }}</span>
              </div>
              <p
                v-if="history.action_notes"
                class="history-notes"
              >
                {{ history.action_notes }}
              </p>
              <div class="history-meta">
                <span
                  v-if="history.old_status"
                  class="history-status"
                >
                  {{ getStatusLabel(history.old_status) }} → {{ getStatusLabel(history.new_status) }}
                </span>
                <span
                  v-if="history.action_by"
                  class="history-actor"
                >
                  by {{ history.action_by }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <EmptyState
          v-else
          title="暂无处理记录"
          description="该预警尚未有任何处理记录"
        />
      </Card>

      <Card
        v-if="alert.metadata && Object.keys(alert.metadata).length > 0"
        class="alert-section"
      >
        <h3 class="section-title">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z" />
            <polyline points="13 2 13 9 20 9" />
          </svg>
          元数据
        </h3>
        <pre class="metadata-json">{{ JSON.stringify(alert.metadata, null, 2) }}</pre>
      </Card>
    </div>

    <div
      v-else
      class="empty-state"
    >
      <EmptyState
        title="预警不存在"
        description="找不到该预警或已被删除"
      >
        <Button @click="goBack">
          返回列表
        </Button>
      </EmptyState>
    </div>

    <Modal 
      v-model:open="showAcknowledgeModal"
      title="确认处理预警"
      size="medium"
    >
      <form
        @submit.prevent="handleAcknowledge"
        class="modal-form"
      >
        <div class="form-group">
          <label class="form-label">处理人</label>
          <input 
            v-model="acknowledgeForm.acknowledged_by" 
            type="text" 
            class="form-input" 
            placeholder="输入处理人姓名"
            required
          >
        </div>
        <div class="form-group">
          <label class="form-label">备注（可选）</label>
          <textarea 
            v-model="acknowledgeForm.notes" 
            class="form-textarea" 
            placeholder="输入备注信息"
            rows="3"
          />
        </div>
        <div class="form-actions">
          <Button
            type="button"
            variant="secondary"
            @click="showAcknowledgeModal = false"
          >
            取消
          </Button>
          <Button
            type="submit"
            variant="primary"
          >
            确认
          </Button>
        </div>
      </form>
    </Modal>

    <Modal 
      v-model:open="showResolveModal"
      title="标记预警已解决"
      size="medium"
    >
      <form
        @submit.prevent="handleResolve"
        class="modal-form"
      >
        <div class="form-group">
          <label class="form-label">解决人</label>
          <input 
            v-model="resolveForm.resolved_by" 
            type="text" 
            class="form-input" 
            placeholder="输入解决人姓名"
            required
          >
        </div>
        <div class="form-group">
          <label class="form-label">解决说明</label>
          <textarea 
            v-model="resolveForm.resolution_notes" 
            class="form-textarea" 
            placeholder="描述解决方案"
            rows="4"
            required
          />
        </div>
        <div class="form-actions">
          <Button
            type="button"
            variant="secondary"
            @click="showResolveModal = false"
          >
            取消
          </Button>
          <Button
            type="submit"
            variant="primary"
          >
            标记解决
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAlertsStore } from "~/stores/alerts";
import { useToast } from "~/composables/useToast";

const router = useRouter();
const route = useRoute();
const store = useAlertsStore();
const toast = useToast();

const loading = ref(false);
const alert = ref<any>(null);
const histories = ref<any[]>([]);
const showAcknowledgeModal = ref(false);
const showResolveModal = ref(false);

const acknowledgeForm = ref({
  acknowledged_by: "",
  notes: "",
});

const resolveForm = ref({
  resolved_by: "",
  resolution_notes: "",
});

async function fetchAlert() {
  loading.value = true;
  try {
    const id = parseInt(route.params.id as string);
    const data = await store.getAlert(id);
    alert.value = data;
    
    if (data) {
      histories.value = await store.getAlertHistories(id);
    }
  } catch (error) {
    console.error("Failed to fetch alert:", error);
    toast.error("获取预警详情失败");
  } finally {
    loading.value = false;
  }
}

async function handleAcknowledge() {
  try {
    const id = parseInt(route.params.id as string);
    await store.acknowledgeAlert(id, acknowledgeForm.value);
    showAcknowledgeModal.value = false;
    acknowledgeForm.value = { acknowledged_by: "", notes: "" };
    toast.success("预警已确认");
    await fetchAlert();
  } catch (error) {
    toast.error("确认失败，请重试");
  }
}

async function handleResolve() {
  try {
    const id = parseInt(route.params.id as string);
    await store.resolveAlert(id, resolveForm.value);
    showResolveModal.value = false;
    resolveForm.value = { resolved_by: "", resolution_notes: "" };
    toast.success("预警已解决");
    await fetchAlert();
  } catch (error) {
    toast.error("操作失败，请重试");
  }
}

function goBack() {
  router.push("/alerts");
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

function getHistoryActionLabel(action: string) {
  const labels: Record<string, string> = {
    created: "创建预警",
    acknowledged: "确认预警",
    resolved: "解决预警",
  };
  return labels[action] || action;
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(() => {
  fetchAlert();
});
</script>

<style scoped>
.alert-detail-page {
  padding: var(--space-6);
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.back-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.back-button:hover {
  background: var(--color-bg-muted);
  color: var(--color-text-primary);
}

.back-button svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
}

.loading-state {
  padding: var(--space-4);
}

.empty-state {
  padding: var(--space-8) var(--space-4);
  text-align: center;
}

.alert-header-card {
  margin-bottom: var(--space-4);
}

.alert-header-top {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.alert-icon-big {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.alert-icon-big.critical,
.alert-icon-big.error {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.alert-icon-big.warning {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.alert-icon-big.info {
  background: var(--color-glow-primary);
  color: var(--color-primary);
}

.alert-icon-big svg {
  width: 32px;
  height: 32px;
}

.alert-info {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--space-3);
  color: var(--color-text-primary);
}

.alert-meta-line {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-bottom: var(--space-2);
}

.alert-status-badge,
.alert-severity-badge,
.alert-type-badge {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.alert-status-badge.active {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.alert-status-badge.acknowledged {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.alert-status-badge.resolved {
  background: var(--color-glow-success);
  color: var(--color-success);
}

.alert-status-badge.dismissed {
  background: var(--color-bg-muted);
  color: var(--color-text-muted);
}

.alert-severity-badge.critical,
.alert-severity-badge.error {
  background: var(--color-glow-error);
  color: var(--color-error);
}

.alert-severity-badge.warning {
  background: var(--color-glow-warning);
  color: var(--color-warning);
}

.alert-severity-badge.info {
  background: var(--color-glow-primary);
  color: var(--color-primary);
}

.alert-type-badge {
  background: var(--color-bg-muted);
  color: var(--color-text-secondary);
}

.alert-time {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.alert-actions {
  display: flex;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.alert-section {
  margin-bottom: var(--space-4);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-4);
}

.section-title svg {
  width: 20px;
  height: 20px;
  color: var(--color-primary);
}

.alert-description,
.alert-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.info-row {
  display: flex;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  width: 100px;
  flex-shrink: 0;
}

.info-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  flex: 1;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.history-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.history-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

.history-icon svg {
  width: 18px;
  height: 18px;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
}

.history-action {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.history-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.history-notes {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: var(--space-1) 0;
}

.history-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.metadata-json {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  overflow-x: auto;
  margin: 0;
}

.modal-form {
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
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-glow-primary);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .alert-detail-page {
    padding: var(--space-4);
  }

  .alert-header-top {
    flex-direction: column;
    text-align: center;
  }

  .alert-actions {
    flex-direction: column;
  }

  .alert-actions button {
    width: 100%;
  }
}
</style>
