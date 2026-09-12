import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { allCapabilityIds } from '@/constants/workbenchCapabilityRegistry';
import { decodeJwtPayload, jwtRoleFromPayload, mapJwtRoleToAgentLevelId } from '@/utils/jwtPayload';
import { isPlatformAdminFromToken, readStoredAccessToken } from '@/utils/sessionAuth';
import { apiGet, apiPost } from '@/utils/api';

export const AGENT_LEVEL_IDS = ['L1', 'L2', 'L3', 'L4', 'L5'] as const;
export type AgentLevelId = (typeof AGENT_LEVEL_IDS)[number];

export const AGENT_LEVEL_LABELS: Record<AgentLevelId, string> = {
  L1: '一级 · 超级代理',
  L2: '二级 · 管理代理',
  L3: '三级 · 区域代理',
  L4: '四级 · 业务代理',
  L5: '五级 · 受限代理',
};

/** localStorage key 仅作缓存，真实数据源为后端 API */
const LS_GRANTS = 'admin-agent-capability-grants';
const LS_LEVEL = 'admin_agent_level';
const LS_SESSION_MANUAL = 'admin_agent_session_manual';

function defaultGrants(): Record<AgentLevelId, string[]> {
  const all = allCapabilityIds();
  const noExt = all.filter((id) => !id.startsWith('ext.'));
  const bizCore = [
    ...new Set([...all.filter((id) => /^(core|seo|matrix|system)\./.test(id)), 'suite.workbench']),
  ];
  const coreSeo = [
    ...new Set([
      ...all.filter((id) => id.startsWith('core.') || id.startsWith('seo.')),
      'suite.workbench',
    ]),
  ];
  const minimal = all.filter((id) =>
    [
      'core.dashboard',
      'core.inquiries',
      'core.products',
      'suite.workbench',
      'suite.agent-cap',
    ].includes(id)
  );
  return {
    L1: [...all],
    L2: noExt,
    L3: bizCore,
    L4: coreSeo,
    L5: minimal,
  };
}

function parseStoredLevel(raw: string | null): AgentLevelId {
  if (raw && AGENT_LEVEL_IDS.includes(raw as AgentLevelId)) return raw as AgentLevelId;
  return 'L1';
}

function loadGrants(): Record<AgentLevelId, string[]> {
  const defaults = defaultGrants();
  if (typeof localStorage === 'undefined') return defaults;
  try {
    const raw = localStorage.getItem(LS_GRANTS);
    if (!raw) return defaults;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const out: Record<AgentLevelId, string[]> = { ...defaults };
    for (const id of AGENT_LEVEL_IDS) {
      const v = parsed[id];
      if (Array.isArray(v) && v.every((x) => typeof x === 'string')) out[id] = v as string[];
    }
    return out;
  } catch {
    return defaults;
  }
}

export const useAgentCapabilitiesStore = defineStore('agentCapabilities', () => {
  const currentLevelId = ref<AgentLevelId>(
    typeof localStorage !== 'undefined' ? parseStoredLevel(localStorage.getItem(LS_LEVEL)) : 'L1'
  );
  const grants = ref<Record<AgentLevelId, string[]>>(loadGrants());

  const currentGrantSet = computed(() => {
    const list = grants.value[currentLevelId.value] ?? [];
    return new Set(list);
  });

  function persistGrants() {
    // 缓存到 localStorage（降级方案）
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LS_GRANTS, JSON.stringify(grants.value));
    }
    // 异步同步到后端 API（主数据源）
    apiPost('/super-admin/permissions/roles', { grants: grants.value }).catch(() => {});
  }

  // 深度监听 grants 变化，同步到 localStorage 和后端 API
  // TODO: 添加 debounce(300) 减少 API 调用频率
  watch(grants, persistGrants, { deep: true });

  function setCurrentLevel(id: AgentLevelId) {
    currentLevelId.value = id;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LS_LEVEL, id);
      localStorage.setItem(LS_SESSION_MANUAL, '1');
    }
  }

  /** 登录成功后：清除「手动会话级别」并按 JWT role 设置 L1–L5 */
  function resetSessionLevelFromJwt(token: string | null) {
    if (typeof localStorage !== 'undefined') localStorage.removeItem(LS_SESSION_MANUAL);
    applyJwtRoleToSessionLevel(token ? jwtRoleFromPayload(decodeJwtPayload(token)) : undefined);
  }

  /** 有 token 且用户未手动选会话级别时，用 JWT 覆盖会话级别（如刷新后 token 更新） */
  function applyJwtRoleToSessionLevel(role: unknown) {
    if (typeof localStorage !== 'undefined' && localStorage.getItem(LS_SESSION_MANUAL)) return;
    const raw = mapJwtRoleToAgentLevelId(role);
    const id = AGENT_LEVEL_IDS.includes(raw as AgentLevelId) ? (raw as AgentLevelId) : 'L1';
    currentLevelId.value = id;
    if (typeof localStorage !== 'undefined') localStorage.setItem(LS_LEVEL, id);
  }

  let cachedPlatformAdminToken: string | null | undefined;
  let cachedPlatformAdminResult = false;

  function canAccess(capabilityId: string): boolean {
    const t = readStoredAccessToken();
    if (t !== cachedPlatformAdminToken) {
      cachedPlatformAdminToken = t;
      cachedPlatformAdminResult = isPlatformAdminFromToken(t);
    }
    if (cachedPlatformAdminResult) return true;
    return currentGrantSet.value.has(capabilityId);
  }

  function setGrantsForLevel(level: AgentLevelId, ids: string[]) {
    grants.value = {
      ...grants.value,
      [level]: [...new Set(ids)],
    };
  }

  function resetAllGrantsToDefaults() {
    grants.value = defaultGrants();
  }

  function grantsForLevel(level: AgentLevelId): string[] {
    return [...(grants.value[level] ?? [])];
  }

  return {
    currentLevelId,
    grants,
    currentGrantSet,
    setCurrentLevel,
    resetSessionLevelFromJwt,
    applyJwtRoleToSessionLevel,
    canAccess,
    setGrantsForLevel,
    resetAllGrantsToDefaults,
    grantsForLevel,
  };
});
