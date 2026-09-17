/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, computed, onUnmounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';
import { growthToolsAPI, unwrapApiData } from '@/api';

/** 跑盘轮询：仅在本页可见且跑盘进行中；间隔勿随意改短 */
const AGENT_POLL_MS = 8000;

export interface GrowthPreset {
  id: string;
  label: string;
  goal: string;
  hint?: string;
  mode?: string;
}

export function useGrowthAgentRun(options?: {
  onCompleted?: (run: Record<string, unknown>) => void;
}) {
  const router = useRouter();
  const route = useRoute();
  const presets = ref<GrowthPreset[]>([]);
  const runHistory = ref<any[]>([]);
  const agentGoal = ref('跑一轮增长诊断：热词→质检→引流监测');
  const agentPresetId = ref<string | undefined>(undefined);
  const agentMode = ref<string | undefined>(undefined);
  const agentFocusKeyword = ref('');
  const agentContentTitle = ref('');
  const agentContentBody = ref('');
  const agentSaveKeyword = ref(false);
  const agentStarting = ref(false);
  const agentRun = ref<any>(null);
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let pollRunId: string | null = null;
  let lastPollSnapshot = '';
  let pollArmed = false;

  function isOnGrowthToolsRoute(): boolean {
    return route.path.includes('/seo-matrix/growth-tools');
  }

  function runPollSnapshot(data: any): string {
    if (!data) return '';
    const tasks = (data.tasks || []).map((t: { id: string; status: string; summary?: string | null }) => ({
      id: t.id,
      status: t.status,
      summary: t.summary ?? null,
    }));
    return JSON.stringify({
      status: data.status,
      progress: data.progress ?? 0,
      tasks,
    });
  }

  function applyRunUpdate(data: any) {
    const snap = runPollSnapshot(data);
    if (snap === lastPollSnapshot) return;
    lastPollSnapshot = snap;
    agentRun.value = data;
  }

  const agentRunning = computed(
    () => agentRun.value?.status === 'running' || agentRun.value?.status === 'pending',
  );

  const agentProgress = computed(() => agentRun.value?.progress ?? 0);

  const agentConclusion = computed(() => agentRun.value?.artifacts?.conclusion || null);

  const agentDraft = computed(() => agentRun.value?.artifacts?.draft || null);

  const agentInspectReport = computed(() => agentRun.value?.artifacts?.inspect_report || null);

  function stopPoll() {
    pollArmed = false;
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    pollRunId = null;
    lastPollSnapshot = '';
  }

  function canPollNow(): boolean {
    return (
      pollArmed &&
      Boolean(pollRunId) &&
      isOnGrowthToolsRoute() &&
      document.visibilityState === 'visible'
    );
  }

  function startPollLoop(runId: string) {
    stopPoll();
    pollArmed = true;
    pollRunId = runId;
    const tick = () => {
      if (!canPollNow()) return;
      void pollRun(runId);
    };
    tick();
    pollTimer = setInterval(tick, AGENT_POLL_MS);
  }

  function onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      stopPoll();
    }
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', onVisibilityChange);
  }

  watch(
    () => route.path,
    () => {
      if (!isOnGrowthToolsRoute()) {
        stopPoll();
      }
    },
  );

  async function fetchPresets() {
    try {
      const res = await growthToolsAPI.getAgentPresets();
      const data = unwrapApiData<{ items?: GrowthPreset[] }>(res);
      presets.value = data?.items || [];
    } catch {
      presets.value = [];
    }
  }

  async function fetchRunHistory() {
    try {
      const res = await growthToolsAPI.listAgentRuns();
      const data = unwrapApiData<{ items?: any[] }>(res);
      runHistory.value = data?.items || [];
    } catch {
      runHistory.value = [];
    }
  }

  function applyPreset(preset: GrowthPreset) {
    agentPresetId.value = preset.id;
    agentMode.value = preset.mode;
    agentGoal.value = preset.goal;
  }

  function fillFromKeyword(keyword: string) {
    agentFocusKeyword.value = keyword;
    agentPresetId.value = 'full_diagnosis';
    agentMode.value = 'full';
  }

  async function pollRun(runId: string) {
    if (!canPollNow()) return;
    try {
      const res = await growthToolsAPI.getAgentRun(runId);
      const data = unwrapApiData<any>(res);
      applyRunUpdate(data);
      if (data?.status === 'completed') {
        stopPoll();
        message.success('智能跑盘完成');
        await fetchRunHistory();
        options?.onCompleted?.(data);
      } else if (data?.status === 'failed') {
        stopPoll();
        message.error('跑盘失败，请查看任务树');
        await fetchRunHistory();
      }
    } catch (e) {
      if (import.meta.env.DEV) console.error(e);
    }
  }

  async function refreshRunOnce() {
    const runId = agentRun.value?.id;
    if (!runId) return;
    try {
      const res = await growthToolsAPI.getAgentRun(runId);
      applyRunUpdate(unwrapApiData<any>(res));
    } catch (e) {
      if (import.meta.env.DEV) console.error(e);
    }
  }

  async function startRun() {
    agentStarting.value = true;
    stopPoll();
    try {
      const payload: Record<string, unknown> = {
        goal: agentGoal.value.trim() || '跑一轮增长诊断',
        save_focus_keyword: agentSaveKeyword.value,
      };
      if (agentPresetId.value) payload.preset_id = agentPresetId.value;
      if (agentMode.value) payload.mode = agentMode.value;
      if (agentFocusKeyword.value.trim()) payload.focus_keyword = agentFocusKeyword.value.trim();
      if (agentContentTitle.value.trim()) payload.content_title = agentContentTitle.value.trim();
      if (agentContentBody.value.trim()) payload.content_body = agentContentBody.value.trim();

      const res = await growthToolsAPI.startAgentRun(payload);
      const data = unwrapApiData<any>(res);
      lastPollSnapshot = '';
      agentRun.value = data;
      message.info('跑盘已启动');
      if (data?.id && isOnGrowthToolsRoute()) {
        startPollLoop(data.id);
      }
    } catch (e: any) {
      message.error(e?.response?.data?.message || '启动跑盘失败');
    } finally {
      agentStarting.value = false;
    }
  }

  function applyDraftToInspect(form: { title: string; body: string }, keywordsText: { value: string }) {
    const draft = agentDraft.value;
    const report = agentInspectReport.value;
    if (draft?.title) form.title = draft.title;
    if (draft?.body) form.body = draft.body;
    else if (report && agentConclusion.value?.focus_keyword) {
      keywordsText.value = agentConclusion.value.focus_keyword;
    }
    message.success('已填入质检表单');
  }

  function goLink(path: string) {
    void router.push(path);
  }

  onUnmounted(() => {
    stopPoll();
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange);
    }
  });

  return {
    presets,
    runHistory,
    agentGoal,
    agentPresetId,
    agentMode,
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
    applyDraftToInspect,
    goLink,
  };
}
