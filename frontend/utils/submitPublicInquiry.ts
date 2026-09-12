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
}

export async function submitPublicInquiry(
  apiBase: string,
  payload: PublicInquiryPayload,
): Promise<void> {
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
