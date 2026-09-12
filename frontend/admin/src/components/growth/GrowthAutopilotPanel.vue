<template>
  <div class="growth-autopilot growth-autopilot--stable">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="growth-autopilot__form bg-white rounded-2xl shadow-card p-6 space-y-4">
        <h3 class="text-lg font-semibold text-gray-900">
          一键增长诊断
        </h3>
        <p class="text-sm text-gray-500">
          自动串联热词、草稿、质检与 20+ 通道引流监测；支持多种跑盘预设。
        </p>

        <div class="flex flex-wrap gap-2">
          <a-tag
            v-for="p in presets"
            :key="p.id"
            class="cursor-pointer"
            :color="agentPresetId === p.id ? 'blue' : 'default'"
            @click="applyPreset(p)"
          >
            {{ p.label }}
          </a-tag>
        </div>

        <a-textarea v-model:value="agentGoal" :rows="2" placeholder="目标描述" />
        <a-input v-model:value="agentFocusKeyword" placeholder="主攻关键词（可选）" />
        <a-input v-model:value="agentContentTitle" placeholder="待检标题（可选）" />
        <a-textarea
          v-model:value="agentContentBody"
          :rows="5"
          placeholder="待检正文（质检模式必填；留空则自动生成模板草稿）"
        />
        <a-checkbox v-model:checked="agentSaveKeyword">
          自动选词时写入专属词库
        </a-checkbox>

        <a-button
          type="primary"
          block
          size="large"
          :loading="agentStarting"
          :disabled="agentRunning"
          @click="handleStart"
        >
          <RocketOutlined class="w-4 h-4 mr-2" />
          {{ agentRunning ? '跑盘中…' : '开始智能跑盘' }}
        </a-button>
      </div>

      <div class="bg-white rounded-2xl shadow-card p-6">
        <div v-if="!agentRun" class="text-center text-gray-400 py-16">
          选择预设或填写参数后开始跑盘
        </div>
        <template v-else>
          <AgentTaskTree
            :goal="agentRun.goal"
            :tasks="agentRun.tasks || []"
            :run-status="agentRun.status"
            :progress="agentProgress"
          />

          <div v-if="agentConclusion" class="mt-4 space-y-3">
            <a-alert type="success" show-icon :message="`主攻词：${agentConclusion.focus_keyword}`">
              <template #description>
                <ul class="list-disc pl-4 mt-1 text-sm">
                  <li v-for="(item, i) in agentConclusion.next_actions || []" :key="i">
                    {{ item }}
                  </li>
                </ul>
              </template>
            </a-alert>
            <div class="flex flex-wrap gap-2">
              <a-button size="small" @click="handleApplyInspect">
                填入质检 Tab
              </a-button>
              <a-button
                v-for="link in agentConclusion.links || []"
                :key="link.path"
                size="small"
                type="link"
                @click="goLink(link.path)"
              >
                {{ link.label }} →
              </a-button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="runHistory.length" class="mt-6 bg-white rounded-2xl shadow-card p-6">
      <h4 class="text-base font-semibold text-gray-900 mb-3">
        最近跑盘
      </h4>
      <a-table
        :data-source="runHistory"
        :pagination="false"
        size="small"
        row-key="id"
        :columns="historyColumns"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { RocketOutlined } from '@ant-design/icons-vue';
import AgentTaskTree from '@/components/agent/AgentTaskTree.vue';
import { useGrowthAgentRun, type GrowthPreset } from '@/composables/useGrowthAgentRun';

const emit = defineEmits<{
  (e: 'apply-inspect', payload: {
    draft?: { title?: string; body?: string };
    report?: Record<string, unknown>;
    focusKeyword?: string;
  }): void;
  (e: 'completed'): void;
}>();

const {
  presets,
  runHistory,
  agentGoal,
  agentPresetId,
  agentFocusKeyword,
  agentContentTitle,
  agentContentBody,
  agentSaveKeyword,
  agentStarting,
  agentRun,
  agentRunning,
  agentProgress,
  agentConclusion,
  agentDraft,
  agentInspectReport,
  fetchPresets,
  fetchRunHistory,
  applyPreset,
  fillFromKeyword,
  startRun,
  stopPoll,
  refreshRunOnce,
  goLink,
} = useGrowthAgentRun({
  onCompleted: () => emit('completed'),
});

const historyColumns = [
  { title: '目标', dataIndex: 'goal', key: 'goal', ellipsis: true },
  { title: '主攻词', dataIndex: 'focus_keyword', key: 'focus_keyword', width: 120 },
  { title: '质检', dataIndex: 'quality_grade', key: 'quality_grade', width: 70 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90 },
  { title: '进度', dataIndex: 'progress', key: 'progress', width: 70 },
];

async function handleStart() {
  await startRun();
}

function handleApplyInspect() {
  emit('apply-inspect', {
    draft: agentDraft.value || undefined,
    report: agentInspectReport.value || undefined,
    focusKeyword: agentConclusion.value?.focus_keyword,
  });
}

onMounted(() => {
  void fetchPresets();
  void fetchRunHistory();
});

defineExpose({ fillFromKeyword, applyPreset, stopPoll, refreshRunOnce });
</script>

<style scoped>
/* 智能跑盘：仅保留任务树内一条进度条，禁止表单侧重复进度与 active 条纹 */
.growth-autopilot--stable :deep(.ant-progress-status-active .ant-progress-bg::before),
.growth-autopilot--stable :deep(.ant-tag-processing),
.growth-autopilot--stable :deep(.ant-tag-processing::before) {
  animation: none !important;
}
</style>
