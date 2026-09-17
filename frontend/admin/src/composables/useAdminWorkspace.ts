/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, watch } from 'vue';

const STORAGE_KEY = 'admin-workspace-v1';

export interface WorkspaceScript {
  id: string;
  name: string;
  body: string;
  updatedAt: string;
}

export interface WorkspaceWorkflow {
  id: string;
  name: string;
  steps: string;
  updatedAt: string;
}

export interface WorkspaceTicket {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'done';
  note: string;
  updatedAt: string;
}

export interface WorkspaceSnippet {
  id: string;
  title: string;
  content: string;
  kind: 'format' | 'debug' | 'refactor';
  updatedAt: string;
}

export interface WorkspaceAiTask {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'done';
  note: string;
  updatedAt: string;
}

export interface WorkspaceSchedulerSlot {
  id: string;
  name: string;
  cron: string;
  note: string;
  updatedAt: string;
}

export interface WorkspaceState {
  scripts: WorkspaceScript[];
  workflows: WorkspaceWorkflow[];
  vulnTickets: WorkspaceTicket[];
  complianceChecks: WorkspaceTicket[];
  snippets: WorkspaceSnippet[];
  aiTasks: WorkspaceAiTask[];
  scanFindings: { id: string; path: string; severity: string; note: string; updatedAt: string }[];
  schedulerSlots: WorkspaceSchedulerSlot[];
}

const defaultState = (): WorkspaceState => ({
  scripts: [],
  workflows: [],
  vulnTickets: [],
  complianceChecks: [],
  snippets: [],
  aiTasks: [],
  scanFindings: [],
  schedulerSlots: [],
});

function load(): WorkspaceState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const o = JSON.parse(raw) as Partial<WorkspaceState>;
    return { ...defaultState(), ...o };
  } catch {
    return defaultState();
  }
}

function save(s: WorkspaceState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

export function useAdminWorkspace() {
  const state = ref<WorkspaceState>(load());

  watch(state, (v) => save(v), { deep: true });

  function genId() {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }

  return { state, genId };
}
