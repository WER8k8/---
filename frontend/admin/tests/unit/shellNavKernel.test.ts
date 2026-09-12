import { describe, expect, it } from 'vitest';

import type { ShellMenuGroup } from '@/types/shellNav';
import {
  collectShellMenuPaths,
  isShellNavDescendantActive,
  isShellNavItemActive,
  resolveActiveMenuPath,
  resolveNavTitleFromMenu,
} from '@/utils/shellNavKernel';

const SAMPLE: ShellMenuGroup[] = [
  {
    title: '超级管理工具',
    children: [
      { name: 'AdminHub', path: '/admin', title: '超管工作台', icon: 'CrownOutlined' },
      {
        name: 'SuiteSystem',
        path: '/admin/system',
        title: '系统管理',
        icon: 'MonitorOutlined',
      },
      {
        name: 'GreedyCumulative',
        path: '/admin/system/greedy-cumulative',
        title: '摸金累计看板',
        icon: 'FundOutlined',
      },
    ],
  },
  {
    title: '总览',
    children: [
      { name: 'Dashboard', path: '/dashboard', title: '数据看板', icon: 'DashboardOutlined' },
    ],
  },
];

describe('shellNavKernel', () => {
  it('resolveActiveMenuPath picks longest prefix', () => {
    expect(resolveActiveMenuPath('/admin/system/greedy-cumulative', SAMPLE)).toBe(
      '/admin/system/greedy-cumulative',
    );
    expect(resolveActiveMenuPath('/admin/system/greedy-cumulative', SAMPLE)).not.toBe('/admin');
    expect(resolveActiveMenuPath('/admin', SAMPLE)).toBe('/admin');
    expect(resolveActiveMenuPath('/dashboard', SAMPLE)).toBe('/dashboard');
  });

  it('only one leaf active at a time', () => {
    const active = resolveActiveMenuPath('/admin/system/greedy-cumulative', SAMPLE);
    const leaves = SAMPLE.flatMap((g) => g.children);
    const actives = leaves.filter((item) => isShellNavItemActive(item, active));
    expect(actives).toHaveLength(1);
    expect(actives[0]?.title).toBe('摸金累计看板');
  });

  it('resolveNavTitleFromMenu returns menu title not parent fallback', () => {
    expect(resolveNavTitleFromMenu('/admin/system/greedy-cumulative', SAMPLE)).toBe(
      '摸金累计看板',
    );
  });

  it('isShellNavDescendantActive marks parent branch only', () => {
    const nested: ShellMenuGroup[] = [
      {
        title: '系统',
        children: [
          {
            name: 'SuiteSystem',
            path: '/admin/system',
            title: '系统管理',
            icon: 'MonitorOutlined',
            children: [
              {
                name: 'GreedyCumulative',
                path: '/admin/system/greedy-cumulative',
                title: '摸金累计看板',
                icon: 'FundOutlined',
              },
            ],
          },
        ],
      },
    ];
    const active = resolveActiveMenuPath('/admin/system/greedy-cumulative', nested)!;
    const parent = nested[0].children[0];
    expect(isShellNavItemActive(parent, active)).toBe(false);
    expect(isShellNavDescendantActive(parent, active)).toBe(true);
  });

  it('collectShellMenuPaths dedupes normalized paths', () => {
    const paths = collectShellMenuPaths(SAMPLE);
    expect(paths).toContain('/admin');
    expect(paths).toContain('/dashboard');
    expect(paths.length).toBeGreaterThanOrEqual(4);
  });
});
