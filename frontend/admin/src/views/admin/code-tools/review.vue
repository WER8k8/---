/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="代码审查" subtitle="对接 /code-quality 规则引擎，提交代码后真实扫描" surface="elevated">
 <template #actions>
 <a-button type="primary" :loading="scanning" @click="startAudit">
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
 description="粘贴待审代码后点「安全审计」，将调用后端 /code-quality/review/file 真实扫描；未执行前统计为 0，不预置示例漏洞。"
 />
 <a-card size="small" class="mb-4" title="待审代码">
 <a-input
 v-model:value="filePath"
 placeholder="文件路径，例如 src/utils/api.ts"
 class="mb-2"
 allow-clear
 />
 <a-textarea
 v-model:value="codeContent"
 :rows="10"
 placeholder="粘贴需要审查的代码内容"
 class="mono"
 />
 </a-card>

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
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { apiPost } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
 CheckCircleOutlined,
 SecurityScanOutlined,
 WarningOutlined,
 InfoCircleOutlined,
} from '@ant-design/icons-vue';

interface Issue {
 id: number;
 severity: string;
 file: string;
 title: string;
 description: string;
 code: string;
 line: number;
}

interface ReviewIssueRaw {
 rule_id?: string;
 rule?: string;
 id?: string;
 title?: string;
 message?: string;
 description?: string;
 severity?: string;
 level?: string;
 line?: number;
 line_number?: number;
 file?: string;
 snippet?: string;
 code?: string;
}

const activeTab = ref('critical');

const auditStarted = ref(false);
const scanning = ref(false);
const filePath = ref('snippet.ts');
const codeContent = ref('');

const criticalCount = ref(0);
const warningCount = ref(0);
const infoCount = ref(0);
const passedCount = ref(0);

const criticalIssues = ref<Issue[]>([]);
const warningIssues = ref<Issue[]>([]);
const infoIssues = ref<Issue[]>([]);

function normalizeSeverity(raw: ReviewIssueRaw): 'critical' | 'warning' | 'info' {
 const s = String(raw.severity || raw.level || '').toLowerCase();
 if (s.includes('critical') || s.includes('high') || s === '严重' || s === 'error') return 'critical';
 if (s.includes('warn') || s === '警告' || s === 'medium') return 'warning';
 return 'info';
}

function severityLabel(bucket: 'critical' | 'warning' | 'info'): string {
 return bucket === 'critical' ? '严重' : bucket === 'warning' ? '警告' : '建议';
}

function mapIssues(issues: ReviewIssueRaw[], file: string): Issue[] {
 return (issues || []).map((raw, idx) => {
 const bucket = normalizeSeverity(raw);
 return {
 id: Date.now() + idx,
 severity: severityLabel(bucket),
 file: raw.file || file,
 title: raw.title || raw.rule_id || raw.rule || raw.id || '审查问题',
 description: raw.description || raw.message || '',
 code: raw.snippet || raw.code || '',
 line: Number(raw.line ?? raw.line_number ?? 0),
 };
 });
}

const startAudit = async () => {
 const content = codeContent.value.trim();
 if (!content) {
 message.warning('请先粘贴待审代码');
 return;
 }
 scanning.value = true;
 auditStarted.value = true;
 criticalIssues.value = [];
 warningIssues.value = [];
 infoIssues.value = [];
 criticalCount.value = 0;
 warningCount.value = 0;
 infoCount.value = 0;
 passedCount.value = 0;
 try {
 const data = await apiPost<{
 file?: string;
 score?: number;
 passed?: boolean;
 issues?: ReviewIssueRaw[];
 }>('/code-quality/review/file', {
 file_path: filePath.value.trim() || 'snippet.ts',
 content,
 });
 const mapped = mapIssues(data?.issues || [], data?.file || filePath.value);
 for (const issue of mapped) {
 if (issue.severity === '严重') criticalIssues.value.push(issue);
 else if (issue.severity === '警告') warningIssues.value.push(issue);
 else infoIssues.value.push(issue);
 }
 criticalCount.value = criticalIssues.value.length;
 warningCount.value = warningIssues.value.length;
 infoCount.value = infoIssues.value.length;
 passedCount.value = data?.passed ? 1 : 0;
 if (!mapped.length) {
 message.success('扫描完成：未发现规则命中问题');
 } else {
 message.success(`扫描完成：命中 ${mapped.length} 条问题`);
 }
 } catch (err: any) {
 auditStarted.value = false;
 message.error(err?.message || '代码审查引擎调用失败，请确认后端 /code-quality 可用');
 } finally {
 scanning.value = false;
 }
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
 message.info(`已本地标记处理（未改写源码）：${issue.title}`);
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
 font-weight: 500;
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
 font-weight: 500;
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
 font-weight: 500;
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
 font-weight: 500;
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
