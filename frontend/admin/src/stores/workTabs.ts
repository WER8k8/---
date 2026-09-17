/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineStore } from 'pinia';

import type { ShellMode } from '@/constants/proShellMenus';
import {
  homePathForRole,
  LEGACY_WORKTAB_STORAGE_KEY,
  resolveWorkTabNavigatePath,
  workTabStorageKeyForRole,
} from '@/constants/roleShellLock';
import { isPlatformKilledPath } from '@/constants/stubVisibility';
import { normalizeLocationPath } from '@/constants/workbenchPathCapabilities';

export interface WorkTab {
  path: string;
  title: string;
  affix?: boolean;
}

export const MAX_WORK_TABS = 12;

function tabKey(path: string): string {
  return normalizeLocationPath(path);
}

function dedupeTabs(tabs: WorkTab[]): WorkTab[] {
  const out: WorkTab[] = [];
  const seen = new Set<string>();
  for (const tab of tabs) {
    if (!tab?.path) continue;
    const key = tabKey(tab.path);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ ...tab, path: key });
  }
  return out;
}

function isPathAllowedForShell(path: string, shell: ShellMode): boolean {
  const p = normalizeLocationPath(path);
  if (isPlatformKilledPath(p)) return false;
  if (p === '/access-denied') return true;
  switch (shell) {
    case 'client':
      return p.startsWith('/client');
    case 'agent':
      return p.startsWith('/agent');
    case 'partner':
      return p.startsWith('/partner');
    default:
      return !p.startsWith('/client') && !p.startsWith('/partner');
  }
}

function isPathAllowedForRole(path: string, role: string | undefined): boolean {
  const p = normalizeLocationPath(path);
  if (isPlatformKilledPath(p)) return false;
  if (p === '/access-denied') return true;
  const r = String(role || '').toLowerCase();
  if (r === 'tenant_admin') return p.startsWith('/client');
  if (r === 'l2') return p.startsWith('/partner');
  if (r === 'l3' || r === 'agent' || r === 'sales') return p.startsWith('/agent');
  return !p.startsWith('/client') && !p.startsWith('/partner');
}

function defaultAffixTab(shell: ShellMode, role?: string): WorkTab {
  switch (shell) {
    case 'client':
      return { path: '/client/today', title: '租户工作台', affix: true };
    case 'agent':
      return { path: '/agent/performance', title: '业绩看板', affix: true };
    case 'partner':
      return { path: '/partner/performance', title: '业绩看板', affix: true };
    default:
      return { path: homePathForRole(role ?? 'admin'), title: '运营工作台', affix: true };
  }
}

function defaultAffixPath(shell: ShellMode, role?: string): string {
  return defaultAffixTab(shell, role).path;
}

function loadTabsFromKey(storageKey: string, shell: ShellMode, role?: string): WorkTab[] {
  const fallback = defaultAffixTab(shell, role);
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return [fallback];
    const tabs = dedupeTabs(
      (JSON.parse(raw) as WorkTab[]).map((t) => ({
        ...t,
        path: tabKey(t.path),
      })),
    );
    return tabs.length ? tabs : [fallback];
  } catch {
    return [fallback];
  }
}

function migrateLegacyWorktabs(targetKey: string): void {
  const legacy = localStorage.getItem(LEGACY_WORKTAB_STORAGE_KEY);
  if (!legacy || localStorage.getItem(targetKey)) return;
  localStorage.setItem(targetKey, legacy);
  localStorage.removeItem(LEGACY_WORKTAB_STORAGE_KEY);
}

export const useWorkTabsStore = defineStore('workTabs', {
  state: () => ({
    storageKey: LEGACY_WORKTAB_STORAGE_KEY,
    tabs: [{ path: '/admin', title: '运营工作台', affix: true }] as WorkTab[],
    activePath: '/admin',
    _lastSanitizeFp: '',
  }),
  actions: {
    /** 按 JWT 角色绑定工作标签分桶（ROLE-SHELL-LOCK-01） */
    bindRoleStorage(role?: string, shell: ShellMode = 'platform') {
      const key = workTabStorageKeyForRole(role);
      if (key === this.storageKey && this.tabs.length > 0) return;
      migrateLegacyWorktabs(key);
      this.storageKey = key;
      const loaded = loadTabsFromKey(key, shell, role);
      this.tabs = loaded;
      this.activePath = loaded[0]?.path ?? defaultAffixPath(shell, role);
      this.persist();
    },
    persist() {
      localStorage.setItem(this.storageKey, JSON.stringify(this.tabs));
    },
    ensureAffixForShell(mode: 'platform' | 'client' | 'agent', role?: string) {
      const shell: ShellMode =
        mode === 'client' ? 'client' : mode === 'agent' ? 'agent' : 'platform';
      const target = defaultAffixTab(shell, role);
      const affix = this.tabs.find((t) => t.affix);
      if (affix && affix.path === target.path && affix.title === target.title) {
        return;
      }
      if (!affix) {
        this.tabs.unshift({ ...target });
      } else {
        affix.path = target.path;
        affix.title = target.title;
      }
      this.persist();
    },
    openTab(tab: WorkTab) {
      if (!tab.path || !tab.title) return;
      const path = tabKey(tab.path);
      this.tabs = dedupeTabs(this.tabs);
      let dirty = false;
      const exists = this.tabs.find((t) => tabKey(t.path) === path);
      if (exists) {
        if (exists.title !== tab.title) {
          exists.title = tab.title;
          dirty = true;
        }
        if (exists.path !== path) {
          exists.path = path;
          dirty = true;
        }
      } else {
        this.tabs.push({ ...tab, path });
        while (this.tabs.length > MAX_WORK_TABS) {
          const dropIdx = this.tabs.findIndex((t) => !t.affix);
          if (dropIdx < 0) break;
          this.tabs.splice(dropIdx, 1);
        }
        dirty = true;
      }
      this.tabs = dedupeTabs(this.tabs);
      if (dirty) this.persist();
      this.activePath = path;
    },
    closeTab(path: string) {
      const key = tabKey(path);
      const tab = this.tabs.find((t) => tabKey(t.path) === key);
      if (tab?.affix) return this.activePath;
      const idx = this.tabs.findIndex((t) => tabKey(t.path) === key);
      if (idx < 0) return this.activePath;
      this.tabs.splice(idx, 1);
      this.persist();
      if (tabKey(this.activePath) === key) {
        const next = this.tabs[idx] ?? this.tabs[idx - 1] ?? this.tabs[0];
        this.activePath = next?.path ?? homePathForRole('admin');
        return this.activePath;
      }
      return this.activePath;
    },
    setActive(path: string) {
      this.activePath = tabKey(path);
    },
    closeOthers(path: string) {
      const key = tabKey(path);
      this.tabs = this.tabs.filter((t) => t.affix || tabKey(t.path) === key);
      this.activePath = key;
      this.persist();
    },
    sanitizeForSession(shell: ShellMode, role?: string): boolean {
      const fp = `${workTabStorageKeyForRole(role)}|${shell}|${role || ''}`;
      if (fp === this._lastSanitizeFp) {
        return false;
      }
      this._lastSanitizeFp = fp;
      this.bindRoleStorage(role, shell);
      let changed = false;
      const kept: WorkTab[] = [];
      for (const tab of this.tabs) {
        const path = resolveWorkTabNavigatePath(tab.path, shell, role);
        if (!isPathAllowedForShell(path, shell) || !isPathAllowedForRole(path, role)) {
          changed = true;
          continue;
        }
        if (path !== tab.path) changed = true;
        kept.push({ ...tab, path });
      }
      this.tabs = dedupeTabs(
        kept.length ? kept : [defaultAffixTab(shell, role)],
      );
      const remappedActive = resolveWorkTabNavigatePath(this.activePath, shell, role);
      const activeAllowed =
        isPathAllowedForShell(remappedActive, shell) &&
        isPathAllowedForRole(remappedActive, role) &&
        this.tabs.some((t) => tabKey(t.path) === tabKey(remappedActive));
      if (!activeAllowed) {
        const affix = this.tabs.find((t) => t.affix);
        this.activePath = affix?.path ?? this.tabs[0]?.path ?? defaultAffixPath(shell, role);
        changed = true;
      } else if (remappedActive !== tabKey(this.activePath)) {
        this.activePath = remappedActive;
        changed = true;
      }
      if (changed) this.persist();
      return changed;
    },
  },
});

