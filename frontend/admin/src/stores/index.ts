/**
 * Pinia 状态管理统一导出
 *
 * 所有 store 必须通过此文件导出，组件统一从 '@/stores' import
 * FIX-3: 补齐 auth / uiPreferences / agentCapabilities / workTabs
 */

// ---- 核心 Store ----
export { useUserStore } from './user';
export { useAuthStore } from './auth';
export { useConversationStore } from './conversation';
export { useSkillStore } from './skill';
export { useTaskStore } from './task';
export { useWebSocketStore } from './websocket';

// ---- UI / 偏好 / 工作标签 ----
export { useUiPreferencesStore } from './uiPreferences';
export { useWorkTabsStore } from './workTabs';

// ---- 代理能力 ----
export { useAgentCapabilitiesStore } from './agentCapabilities';

// ---- 类型重导出 ----
export type { User, UserPreferences } from './user';
