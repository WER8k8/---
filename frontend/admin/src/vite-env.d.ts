/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/// <reference types="vite/client" />

import 'vue-router';

declare module 'vue-router' {
  interface RouteMeta {
    /** 为 true 时不做代理能力路由守卫（如无权提示页） */
    skipCapabilityGuard?: boolean;
    /** 显式指定路由对应的工作台能力 id，优先于路径推断 */
    capabilityId?: string;
  }
}

declare module 'axios' {
  interface AxiosRequestConfig {
    /** 401 时不走静默 refresh（如登录接口） */
    skipAuthRefresh?: boolean;
    /** 内部：已因 refresh 重试过，禁止再次 refresh */
    _authRetry?: boolean;
    /**
     * 业务接口返回 401 时仅 reject，不触发清会话跳登录
     *（页面自行降级，如看板空数据）
     */
    softAuthFailure?: boolean;
  }
}

declare module 'socket.io-client' {
  export function io(url: string, opts?: Record<string, unknown>): any
  export type Socket = any
}

interface ImportMeta {
  readonly client?: boolean
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start(): void
  stop(): void
  onresult: ((ev: SpeechRecognitionEvent) => void) | null
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
}

declare var SpeechRecognition: {
  new (): SpeechRecognition
}

declare var webkitSpeechRecognition: {
  new (): SpeechRecognition
}
