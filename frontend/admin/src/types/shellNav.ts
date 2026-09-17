/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** YoudingProLayout 导航契约 — Platform / Client / Agent 共用 */

export interface ShellNavItem {
  name: string;
  path: string;
  title: string;
  icon: string;
  group?: string;
  children?: ShellNavItem[];
}

export interface ShellMenuGroup {
  title: string;
  children: ShellNavItem[];
}
