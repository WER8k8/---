/**
 * 附属执行台（TradeAI / GoodJob）入口可见性回归
 *
 * 守护两条曾断裂的链路：
 * 1) embed 地址必须走 VITE_ 前缀（否则 Vite 不注入，页面永远报「未部署」）
 * 2) annex 菜单不得被实验室过滤剥掉（SYSTEM-LOCK-02 子系统常态必须有入口）
 * 3) 菜单声明的路径必须在真实路由表中解析得到。曾发生 adminPath 写成
 *    /admin/annex/*，而路由实际嵌在 system 子级下（/admin/system/annex/*），
 *    菜单点进去渲染 NotFound「无入口」；静态的 check-nav-routes.mjs 用前缀
 *    匹配判定，父级 /admin 存在即放行，所以一直是假绿。这里改用 vue-router
 *    自己 resolve，漂移会被立刻抓住。
 */
import { beforeEach, describe, expect, it } from 'vitest';

import router from '@/router';
import { ANNEX_MODULES } from '@/constants/annexModules';
import { PLATFORM_SHELL_MENU } from '@/constants/platformShellMenu';
import { CLIENT_SHELL_MENU, getClientMoreShellMenu } from '@/constants/proShellMenus';
import {
  isPlatformLabPath,
  setPlatformLabEnabled,
  stripPlatformLabMenuItems,
  type PlatformMenuNavItem,
} from '@/constants/stubVisibility';

const ANNEX_KEYS = Object.keys(ANNEX_MODULES);

function annexPaths(items: Array<{ path: string; children?: unknown[] }>): string[] {
  return ANNEX_KEYS.map((key) => ANNEX_MODULES[key].adminPath).filter((p) =>
    items.some((item) => item.path === p),
  );
}

describe('annex 执行台入口', () => {
  beforeEach(() => {
    setPlatformLabEnabled(false);
    localStorage.removeItem('admin_cert_mode');
  });

  it('注册表齐全，且 embed 变量键带 VITE_ 前缀', () => {
    expect(ANNEX_KEYS).toEqual(['trade-ai', 'goodjob']);
    ANNEX_KEYS.forEach((key) => {
      const meta = ANNEX_MODULES[key];
      expect(meta.envKey.startsWith('VITE_')).toBe(true);
      expect(meta.label).toBeTruthy();
      expect(meta.adminPath.startsWith('/admin/annex/')).toBe(true);
      expect(meta.clientPath.startsWith('/client/annex/')).toBe(true);
    });
  });

  it('实验室模式关闭时，超管侧栏仍保留附属执行台菜单', () => {
    ANNEX_KEYS.forEach((key) => {
      expect(isPlatformLabPath(ANNEX_MODULES[key].adminPath)).toBe(false);
    });

    const group = PLATFORM_SHELL_MENU.find((g) => g.title === '附属执行台');
    expect(group).toBeTruthy();
    const stripped = stripPlatformLabMenuItems(group?.children as PlatformMenuNavItem[]);
    expect(annexPaths(stripped)).toHaveLength(ANNEX_KEYS.length);
  });

  it('租户「更多功能」抽屉暴露附属执行台分组', () => {
    const group = CLIENT_SHELL_MENU.find((g) => g.title === '附属执行台');
    expect(group).toBeTruthy();

    const drawer = getClientMoreShellMenu();
    const drawerGroup = drawer.find((g) => g.title === '附属执行台');
    expect(drawerGroup?.children.map((c) => c.path)).toEqual(
      ANNEX_KEYS.map((key) => ANNEX_MODULES[key].clientPath),
    );
  });

  it('菜单与注册表声明的入口路径，在真实路由表中可解析且命中 annex 壳页', () => {
    // 注册表声明的路径 + 两套侧栏菜单实际渲染出来的路径，一起送进真实路由表裁决。
    const declared = [...new Set([...annexRegistryPaths(), ...annexMenuPaths()])];
    expect(declared.length).toBeGreaterThanOrEqual(4);

    declared.forEach((path) => {
      const resolved = router.resolve(path);
      const tail = resolved.matched[resolved.matched.length - 1];
      const landedOnNotFound = !tail || String(tail.name ?? '') === 'NotFound';
      expect(landedOnNotFound, `${path} 未注册为真实路由，菜单点进去会是 404`).toBe(false);

      const owner = ANNEX_KEYS.find((key) =>
        resolved.matched.some((record) => record.meta?.annexKey === key),
      );
      expect(owner, `${path} 未绑定任何 annexKey`).toBeTruthy();
      // 归属须与注册表一致，防止菜单把 GoodJob 指到 TradeAI 的壳页
      expect([ANNEX_MODULES[owner as string].adminPath, ANNEX_MODULES[owner as string].clientPath]).toContain(path);
    });

    // 反向控制：未注册路径必须落到 NotFound，证明上面的判定不是空转。
    expect(router.resolve('/admin/annex/not-a-real-module').matched.at(-1)?.name).toBe('NotFound');
  });
});

/** 注册表（单一真源）声明的入口路径 */
function annexRegistryPaths(): string[] {
  return ANNEX_KEYS.flatMap((key) => [
    ANNEX_MODULES[key].adminPath,
    ANNEX_MODULES[key].clientPath,
  ]);
}

/** 两套侧栏菜单里「附属执行台」分组声明的入口路径 */
function annexMenuPaths(): string[] {
  const groups = [
    PLATFORM_SHELL_MENU.find((g) => g.title === '附属执行台'),
    CLIENT_SHELL_MENU.find((g) => g.title === '附属执行台'),
    getClientMoreShellMenu().find((g) => g.title === '附属执行台'),
  ];
  return groups.flatMap((g) => (g?.children ?? []).map((item) => item.path));
}
