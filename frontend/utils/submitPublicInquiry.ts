export interface PublicInquiryPayload {
  name: string;
  email?: string;
  phone?: string;
  product?: string;
  message: string;
  source_channel?: string;
  tenant_id?: string;
  session_id?: string;
  landing_path?: string;
  last_click_label?: string;
  // P0-5：UTM 透传字段，优先由调用方显式传入，否则由落地页 URL 解析兜底
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
}

export async function submitPublicInquiry(
  apiBase: string,
  payload: PublicInquiryPayload,
): Promise<void> {
  // UTM 透传：调用方显式传入优先；未传时从落地页 URL 查询参数解析（P0-5）
  const urlParams =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search)
      : new URLSearchParams();
  const utmSource = payload.utm_source ?? urlParams.get('utm_source') ?? undefined;
  const utmMedium = payload.utm_medium ?? urlParams.get('utm_medium') ?? undefined;
  const utmCampaign = payload.utm_campaign ?? urlParams.get('utm_campaign') ?? undefined;
  const utmContent = payload.utm_content ?? urlParams.get('utm_content') ?? undefined;
  const utmTerm = payload.utm_term ?? urlParams.get('utm_term') ?? undefined;

  const body: Record<string, string> = {
    name: payload.name,
    message: payload.message,
  };
  if (payload.email?.trim()) body.email = payload.email.trim();
  if (payload.phone?.trim()) body.phone = payload.phone.trim();
  if (payload.product?.trim()) body.product = payload.product.trim();
  if (payload.source_channel) body.source_channel = payload.source_channel;
  if (payload.tenant_id) body.tenant_id = payload.tenant_id;
  if (payload.session_id) body.session_id = payload.session_id;
  if (payload.landing_path) body.landing_path = payload.landing_path;
  if (payload.last_click_label) body.last_click_label = payload.last_click_label;
  if (utmSource) body.utm_source = utmSource;
  if (utmMedium) body.utm_medium = utmMedium;
  if (utmCampaign) body.utm_campaign = utmCampaign;
  if (utmContent) body.utm_content = utmContent;
  if (utmTerm) body.utm_term = utmTerm;

  const res = await fetch(`${apiBase.replace(/\/$/, '')}/inquiries/public`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const result = await res.json().catch(() => ({}));
  if (!res.ok || (result.code !== undefined && result.code !== 0)) {
    throw new Error(result.message || '询盘提交失败，请稍后重试');
  }
}
