/**
 * Admin Unified Contract (UAC) — 前端类型
 * 组装自：Vben 路由 + Art Edge authList + 四壳 shell
 */

export type AdminShell = 'client' | 'platform' | 'agent' | 'ops'

export interface UacAuthMark {
  title: string
  authMark: string
  code?: string
}

export interface UacRouteMeta {
  title: string
  icon?: string
  order?: number
  keepAlive?: boolean
  hideInMenu?: boolean
  hideInTab?: boolean
  affixTab?: boolean
  shell?: AdminShell
  roles?: string[]
  authList?: UacAuthMark[]
}

export interface UacMenuRoute {
  name: string
  path: string
  component?: string
  redirect?: string
  meta: UacRouteMeta
  children?: UacMenuRoute[]
}

export interface UacUserInfo {
  id: string
  username: string
  nickname?: string
  avatar?: string
  roles: string[]
  shell: AdminShell
  homePath: string
  tenant?: {
    id?: string
    code?: string
    name?: string
  }
}

export interface UacPermissionBundle {
  shell: AdminShell
  roles: string[]
  codes: string[]
  homePath: string
}

export interface UacLoginResult {
  access_token: string
  refresh_token: string
  expires_in?: number
  token_type?: string
}

export interface UacTableQuery {
  page?: number
  pageSize?: number
  [key: string]: unknown
}

export interface UacPageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
