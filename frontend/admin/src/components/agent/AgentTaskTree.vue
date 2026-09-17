/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="agent-task-tree">
    <div v-if="goal" class="agent-task-tree__goal">
      <RocketOutlined class="agent-task-tree__goal-icon" />
      <div>
        <p class="agent-task-tree__goal-label">
          目标
        </p>
        <p class="agent-task-tree__goal-text">
          {{ goal }}
        </p>
      </div>
      <a-tag v-if="runStatus" :color="runStatusColor">
        {{ runStatusLabel }}
      </a-tag>
    </div>

    <a-progress
      v-if="progress > 0 || runStatus === 'running'"
      :percent="progress"
      size="small"
      class="agent-task-tree__progress"
      :show-info="true"
      :stroke-color="progressStrokeColor"
      :status="progressBarStatus"
    />

    <a-steps
      direction="vertical"
      size="small"
      :current="currentIndex"
      :status="stepsStatus"
      class="agent-task-tree__steps agent-task-tree__steps--stable"
    >
      <a-step v-for="task in tasks" :key="task.id">
        <template #title>
          <span class="agent-task-tree__step-title">{{ task.title }}</span>
        </template>
        <template #description>
          <div class="agent-task-tree__step-body">
            <p v-if="task.summary" class="agent-task-tree__summary">
              {{ task.summary }}
            </p>
            <p v-else-if="task.status === 'running'" class="agent-task-tree__running">
              执行中…
            </p>
            <p v-else-if="task.status === 'pending'" class="agent-task-tree__pending">
              等待上一步完成
            </p>
            <a-alert
              v-if="task.error"
              type="error"
              show-icon
              :message="task.error"
              class="agent-task-tree__error"
            />
            <div
              v-if="task.output && showOutput"
              class="agent-task-tree__output"
            >
              <pre>{{ formatOutput(task.output) }}</pre>
            </div>
          </div>
        </template>
      </a-step>
    </a-steps>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RocketOutlined } from '@ant-design/icons-vue';

export interface AgentTaskItem {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  summary?: string | null;
  error?: string | null;
  output?: unknown;
}

const props = withDefaults(
  defineProps<{
    goal?: string;
    tasks: AgentTaskItem[];
    runStatus?: 'pending' | 'running' | 'completed' | 'failed';
    progress?: number;
    showOutput?: boolean;
  }>(),
  {
    goal: '',
    progress: 0,
    showOutput: false,
  },
);

const statusLabels: Record<string, string> = {
  pending: '排队中',
  running: '跑盘中',
  completed: '已完成',
  failed: '失败',
};

const runStatusLabel = computed(() => statusLabels[props.runStatus || 'pending'] || props.runStatus);

const runStatusColor = computed(() => {
  const s = props.runStatus;
  if (s === 'completed') return 'success';
  if (s === 'failed') return 'error';
  if (s === 'running') return 'blue';
  return 'default';
});

/** 不用 processing/active，避免 Ant 内置脉冲动画导致页面闪 */
const progressBarStatus = computed(() => {
  if (props.runStatus === 'failed') return 'exception' as const;
  if (props.runStatus === 'completed') return 'success' as const;
  return 'normal' as const;
});

const progressStrokeColor = computed(() => {
  if (props.runStatus === 'failed') return '#ef4444';
  if (props.runStatus === 'completed') return '#22c55e';
  return '#55778f';
});

const currentIndex = computed(() => {
  const tasks = props.tasks || [];
  const runningIdx = tasks.findIndex((t) => t.status === 'running');
  if (runningIdx >= 0) return runningIdx;
  const lastDone = tasks.reduce(
    (acc, t, i) => (t.status === 'completed' || t.status === 'failed' ? i : acc),
    -1,
  );
  if (props.runStatus === 'completed') return tasks.length;
  return Math.max(0, lastDone + 1);
});

const stepsStatus = computed(() => {
  if (props.runStatus === 'failed') return 'error';
  if (props.runStatus === 'completed') return 'finish';
  return 'process';
});

function formatOutput(output: unknown): string {
  if (typeof output === 'string') return output;
  try {
    return JSON.stringify(output, null, 2);
  } catch {
    return String(output);
  }
}
</script>

<style scoped>
.agent-task-tree__goal {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgb(239 246 255) 0%, rgb(245 243 255) 100%);
  border: 1px solid rgb(219 234 254);
}

.agent-task-tree__goal-icon {
  font-size: 20px;
  color: var(--uj-brand, #55778f);
  margin-top: 2px;
}

.agent-task-tree__goal-label {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.agent-task-tree__goal-text {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin: 4px 0 0;
}

.agent-task-tree__progress {
  margin-bottom: 16px;
}

.agent-task-tree__steps :deep(.ant-steps-item-title) {
  font-size: 14px;
}

.agent-task-tree__steps--stable :deep(.ant-steps-item-icon),
.agent-task-tree__steps--stable :deep(.ant-steps-item-content),
.agent-task-tree__steps--stable :deep(.ant-steps-item-process .ant-steps-item-icon),
.agent-task-tree__steps--stable :deep(.ant-steps-item-process .ant-steps-icon),
.agent-task-tree__steps--stable :deep(.ant-progress-bg),
.agent-task-tree__steps--stable :deep(.ant-progress-status-active .ant-progress-bg::before) {
  transition: none !important;
  animation: none !important;
}

.agent-task-tree__progress :deep(.ant-progress-bg) {
  transition: width 0.35s ease !important;
}

.agent-task-tree__progress :deep(.ant-progress-status-active .ant-progress-bg::before) {
  animation: none !important;
}

.agent-task-tree__summary {
  margin: 0;
  color: #334155;
  font-size: 13px;
}

.agent-task-tree__running {
  margin: 0;
  color: var(--uj-brand, #4a9b8c);
  font-size: 13px;
}

.agent-task-tree__pending {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
}

.agent-task-tree__error {
  margin-top: 8px;
}

.agent-task-tree__output {
  margin-top: 8px;
  max-height: 160px;
  overflow: auto;
  background: #f8fafc;
  border-radius: 8px;
  padding: 8px;
}

.agent-task-tree__output pre {
  margin: 0;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
