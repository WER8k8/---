/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="代码审查" subtitle="代码质量检查和安全审计" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="startAudit">
        <SecurityScanOutlined />
        安全审计
      </a-button>
    </template>
  <div class="review-page">
    <a-alert
      v-if="!auditStarted"
      type="info"
      show-icon
      class="mb-4"
      message="尚未执行审查"
      description="本页不预置示例漏洞。点击「安全审计」后将接入真实扫描结果；当前无记录时统计为 0。"
    />

    <div class="audit-summary">
      <div class="summary-card critical">
        <div class="summary-icon">
          <WarningOutlined />
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ criticalCount }}</span>
          <span class="summary-label">严重问题</span>
        </div>
      </div>
      <div class="summary-card warning">
        <div class="summary-icon">
          <WarningOutlined />
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ warningCount }}</span>
          <span class="summary-label">警告</span>
        </div>
      </div>
      <div class="summary-card info">
        <div class="summary-icon">
          <InfoCircleOutlined />
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ infoCount }}</span>
          <span class="summary-label">建议</span>
        </div>
      </div>
      <div class="summary-card success">
        <div class="summary-icon">
          <CheckCircleOutlined />
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ passedCount }}</span>
          <span class="summary-label">通过</span>
        </div>
      </div>
    </div>

    <div class="audit-results">
      <div class="results-tabs">
        <a-tabs v-model:active-key="activeTab">
          <a-tab-pane
            key="critical"
            tab="严重问题"
          >
            <div class="issue-list">
              <div
                class="issue-item"
                v-for="issue in criticalIssues"
                :key="issue.id"
              >
                <div class="issue-header">
                  <span class="issue-tag critical">{{ issue.severity }}</span>
                  <span class="issue-file">{{ issue.file }}</span>
                </div>
                <h4 class="issue-title">
                  {{ issue.title }}
                </h4>
                <p class="issue-desc">
                  {{ issue.description }}
                </p>
                <div class="issue-code">
                  <pre>{{ issue.code }}</pre>
                </div>
                <div class="issue-footer">
                  <span class="issue-line">第 {{ issue.line }} 行</span>
                  <button
                    class="fix-btn"
                    @click="fixIssue(issue)"
                  >
                    自动修复
                  </button>
                </div>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane
            key="warning"
            tab="警告"
          >
            <div class="issue-list">
              <div
                class="issue-item"
                v-for="issue in warningIssues"
                :key="issue.id"
              >
                <div class="issue-header">
                  <span class="issue-tag warning">{{ issue.severity }}</span>
                  <span class="issue-file">{{ issue.file }}</span>
                </div>
                <h4 class="issue-title">
                  {{ issue.title }}
                </h4>
                <p class="issue-desc">
                  {{ issue.description }}
                </p>
                <div class="issue-code">
                  <pre>{{ issue.code }}</pre>
                </div>
                <div class="issue-footer">
                  <span class="issue-line">第 {{ issue.line }} 行</span>
                  <button
                    class="fix-btn"
                    @click="fixIssue(issue)"
                  >
                    自动修复
                  </button>
                </div>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane
            key="info"
            tab="建议"
          >
            <div class="issue-list">
              <div
                class="issue-item"
                v-for="issue in infoIssues"
                :key="issue.id"
              >
                <div class="issue-header">
                  <span class="issue-tag info">{{ issue.severity }}</span>
                  <span class="issue-file">{{ issue.file }}</span>
                </div>
                <h4 class="issue-title">
                  {{ issue.title }}
                </h4>
                <p class="issue-desc">
                  {{ issue.description }}
                </p>
                <div class="issue-code">
                  <pre>{{ issue.code }}</pre>
                </div>
                <div class="issue-footer">
                  <span class="issue-line">第 {{ issue.line }} 行</span>
                  <button
                    class="fix-btn"
                    @click="fixIssue(issue)"
                  >
                    自动修复
                  </button>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
  CheckCircleOutlined,
  SecurityScanOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue';

onMounted(async () => {
  try { await apiGet('/developer'); } catch { /* 空状态 */ }
});

interface Issue {
  id: number;
  severity: string;
  file: string;
  title: string;
  description: string;
  code: string;
  line: number;
}

const activeTab = ref('critical');

const auditStarted = ref(false);

const criticalCount = ref(0);
const warningCount = ref(0);
const infoCount = ref(0);
const passedCount = ref(0);

const criticalIssues = ref<Issue[]>([]);
const warningIssues = ref<Issue[]>([]);
const infoIssues = ref<Issue[]>([]);

const startAudit = () => {
  auditStarted.value = true;
  message.info('代码审查引擎未接入，暂无扫描结果');
};

const removeIssue = (issue: Issue, bucket: 'critical' | 'warning' | 'info') => {
  const map = { critical: criticalIssues, warning: warningIssues, info: infoIssues };
  const list = map[bucket];
  const idx = list.value.findIndex((i) => i.id === issue.id);
  if (idx > -1) list.value.splice(idx, 1);
  passedCount.value += 1;
};

const fixIssue = (issue: Issue) => {
  if (issue.severity === '严重') removeIssue(issue, 'critical');
  else if (issue.severity === '警告') removeIssue(issue, 'warning');
  else removeIssue(issue, 'info');
  message.success(`已标记修复：${issue.title}`);
};
</script>

<style scoped lang="scss">
.review-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .page-desc {
      font-size: 14px;
      color: #6b7280;
      margin-top: 4px;
    }
  }

  .audit-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
}

.audit-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .summary-card {
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;

    &.critical {
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
      border: 1px solid #fecaca;

      .summary-icon {
        color: #dc2626;
      }

      .summary-value {
        color: #dc2626;
      }
    }

    &.warning {
      background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
      border: 1px solid #fde68a;

      .summary-icon {
        color: #d97706;
      }

      .summary-value {
        color: #d97706;
      }
    }

    &.info {
      background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
      border: 1px solid #bfdbfe;

      .summary-icon {
        color: var(--uj-brand, #4a9b8c);
      }

      .summary-value {
        color: var(--uj-brand, #4a9b8c);
      }
    }

    &.success {
      background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
      border: 1px solid #bbf7d0;

      .summary-icon {
        color: #059669;
      }

      .summary-value {
        color: #059669;
      }
    }

    .summary-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      background: rgba(0, 0, 0, 0.05);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }

    .summary-content {
      .summary-value {
        font-size: 28px;
        font-weight: 700;
        display: block;
      }

      .summary-label {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

.audit-results {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .results-tabs {
    .issue-list {
      padding: 20px;

      .issue-item {
        background: #f9fafb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;

        &:last-child {
          margin-bottom: 0;
        }

        .issue-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;

          .issue-tag {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;

            &.critical {
              background: #fee2e2;
              color: #dc2626;
            }
            &.warning {
              background: #fef3c7;
              color: #d97706;
            }
            &.info {
              background: #dbeafe;
              color: var(--uj-brand, #4a9b8c);
            }
          }

          .issue-file {
            font-size: 12px;
            color: #6b7280;
          }
        }

        .issue-title {
          font-size: 15px;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
          margin-bottom: 6px;
        }

        .issue-desc {
          font-size: 13px;
          color: #6b7280;
          margin: 0;
          margin-bottom: 12px;
        }

        .issue-code {
          background: #1f2937;
          border-radius: 6px;
          padding: 12px;
          margin-bottom: 12px;

          pre {
            margin: 0;
            font-size: 12px;
            color: #e5e7eb;
            overflow-x: auto;
          }
        }

        .issue-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .issue-line {
            font-size: 12px;
            color: #9ca3af;
          }

          .fix-btn {
            padding: 4px 12px;
            background: #4a9b8c;
            color: #fff;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
          }
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .audit-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .audit-summary {
    grid-template-columns: 1fr;
  }
}
</style>
