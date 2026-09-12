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
