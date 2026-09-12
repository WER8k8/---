import { computed } from 'vue';

import { effectivePlatformRole, platformRoleLabel, platformWorkbenchTitle } from '@/constants/platformRoleDisplay';
import { useAuthStore } from '@/stores/auth';

/** 侧栏、顶栏、/admin 工作台统一角色（dev 账号 admin → 平台超管） */
export function useEffectivePlatformRole() {
  const auth = useAuthStore();

  const role = computed(() => effectivePlatformRole(auth.currentRole, auth.username));

  const roleLabel = computed(() => platformRoleLabel(role.value));

  const workbenchTitle = computed(() => platformWorkbenchTitle(role.value));

  const needsDevRelogin = computed(
    () =>
      import.meta.env.DEV
      && String(auth.username || '').toLowerCase() === 'admin'
      && auth.currentRole === 'admin',
  );

  return { role, roleLabel, workbenchTitle, needsDevRelogin };
}
