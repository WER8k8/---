/** 论坛 Sidecar — Apache Answer 嵌入与 Webhook */

import { apiGet, apiPost, apiPut } from '@/utils/api';

export type ForumConfig = {
  enabled?: boolean;
  embed_url?: string;
  public_path?: string;
  iframe_src?: string | null;
  tenant_id?: string;
  webhook_url?: string;
  webhook_headers?: Record<string, string>;
  honest_note?: string;
  sidecar?: { healthy?: boolean; url?: string };
};

export function fetchForumStatus() {
  return apiGet<{ healthy?: boolean; url?: string }>('/forum/status');
}

export function fetchForumConfig() {
  return apiGet<ForumConfig>('/forum/config');
}

export function updateForumConfig(body: {
  enabled?: boolean;
  embed_url?: string;
  public_path?: string;
  rotate_webhook_secret?: boolean;
}) {
  return apiPut<ForumConfig>('/forum/config', body);
}

export function fetchForumSetupGuide() {
  return apiGet<{ steps?: string[]; config?: ForumConfig }>('/forum/setup-guide');
}

export type ForumTranslateResult = {
  summary_zh?: string;
  body_en?: string;
  body_zh_backtranslation?: string;
  human_confirm_required?: boolean;
  disclaimer?: string;
  suggested_reply_points?: string[];
};

export function translateForumQa(body: {
  mode: 'question_to_zh' | 'answer_to_en';
  text: string;
  context_title?: string;
  context_body?: string;
}) {
  return apiPost<ForumTranslateResult>('/forum/translate-qa', body);
}
