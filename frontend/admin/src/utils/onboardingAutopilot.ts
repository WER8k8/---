/** 一键开业 — Time-to-Value 自动编排 */
import { apiPost } from '@/utils/api';

export interface AutopilotStep {
  id: string;
  label?: string;
  ok?: boolean;
  skipped?: boolean;
  error?: string;
  reply_snippet?: string;
  top_market?: {
    country_code?: string;
    country_label?: string;
    growth?: string;
    reason?: string;
  };
  detail?: string;
  home_title?: string;
  preview?: string;
  title?: string;
}

export interface AutopilotResult {
  ok?: boolean;
  headline?: string;
  product?: string;
  steps?: AutopilotStep[];
  duration_sec?: number;
  site_preview_url?: string;
  site_preview_dev_url?: string;
  publish_prefill?: { title?: string; body?: string; product?: string };
  wizard_completed?: boolean;
}

const PREFILL_KEY = 'onboarding_first_publish';

export function storePublishPrefill(draft: AutopilotResult['publish_prefill']) {
  if (!draft?.body) return;
  sessionStorage.setItem(PREFILL_KEY, JSON.stringify(draft));
}

export function consumePublishPrefill(): AutopilotResult['publish_prefill'] | null {
  const raw = sessionStorage.getItem(PREFILL_KEY);
  if (!raw) return null;
  sessionStorage.removeItem(PREFILL_KEY);
  try {
    return JSON.parse(raw) as AutopilotResult['publish_prefill'];
  } catch {
    return null;
  }
}

export async function runOnboardingAutopilot(options: {
  productName: string;
  productImages?: string[];
}): Promise<AutopilotResult> {
  const data = await apiPost<AutopilotResult>('/tenants/self/onboarding-autopilot/run', {
    product_name: options.productName.trim(),
    product_images: options.productImages || [],
  });
  if (data?.publish_prefill) {
    storePublishPrefill(data.publish_prefill);
  }
  return data || {};
}

export function sitePreviewHref(result: AutopilotResult): string {
  if (import.meta.env.DEV && result.site_preview_dev_url) {
    return result.site_preview_dev_url;
  }
  return result.site_preview_url || result.site_preview_dev_url || '#';
}
