import { onUnmounted, type Ref } from 'vue';

import { submitPublicInquiry } from '../utils/submitPublicInquiry';

export interface VisualInquiryBinderOptions {
  tenantId: Ref<string | undefined>;
  apiBase: Ref<string>;
  getAttribution?: () => {
    session_id?: string;
    landing_path?: string;
    last_click_label?: string;
  };
  messages?: {
    requiredName?: string;
    requiredContact?: string;
    requiredMessage?: string;
    required?: string;
    success?: string;
    error?: string;
  };
}

function readForm(form: HTMLFormElement) {
  const fd = new FormData(form);
  return {
    name: String(fd.get('name') || '').trim(),
    email: String(fd.get('email') || '').trim(),
    phone: String(fd.get('phone') || '').trim(),
    product: String(fd.get('product') || '').trim(),
    message: String(fd.get('message') || '').trim(),
  };
}

function showFormMessage(form: HTMLFormElement, kind: 'error' | 'success', text: string) {
  let el = form.querySelector('.sb-inquiry-msg') as HTMLElement | null;
  if (!el) {
    el = document.createElement('p');
    el.className = 'sb-inquiry-msg';
    form.appendChild(el);
  }
  el.className = `sb-inquiry-msg sb-inquiry-msg--${kind}`;
  el.textContent = text;
}

export function bindVisualSiteInquiryForms(
  root: HTMLElement | null | undefined,
  opts: VisualInquiryBinderOptions,
): () => void {
  if (!root || typeof window === 'undefined') return () => {};

  const handlers: Array<{ form: HTMLFormElement; fn: (e: Event) => void }> = [];

  root.querySelectorAll('form[data-yd-block="inquiry"]').forEach((node) => {
    const form = node as HTMLFormElement;
    const fn = async (e: Event) => {
      e.preventDefault();
      const data = readForm(form);
      if (!data.name) {
        showFormMessage(
          form,
          'error',
          opts.messages?.requiredName || opts.messages?.required || '请填写姓名',
        );
        return;
      }
      if (!data.phone && !data.email) {
        showFormMessage(
          form,
          'error',
          opts.messages?.requiredContact || opts.messages?.required || '请填写邮箱或电话',
        );
        return;
      }
      if (!data.message) {
        showFormMessage(
          form,
          'error',
          opts.messages?.requiredMessage || opts.messages?.required || '请填写询盘内容',
        );
        return;
      }
      const btn = form.querySelector('button[type="submit"]') as HTMLButtonElement | null;
      if (btn) btn.disabled = true;
      try {
        const attr = opts.getAttribution?.() || {};
        await submitPublicInquiry(opts.apiBase.value, {
          name: data.name,
          email: data.email || undefined,
          phone: data.phone || undefined,
          product: data.product || undefined,
          message: data.message,
          source_channel: 'tenant_visual_site',
          tenant_id: opts.tenantId.value || undefined,
          session_id: attr.session_id,
          landing_path: attr.landing_path || window.location.pathname,
          last_click_label: attr.last_click_label || 'visual_inquiry_form',
        });
        showFormMessage(form, 'success', opts.messages?.success || '提交成功，我们会尽快联系您');
        form.reset();
      } catch (err) {
        showFormMessage(
          form,
          'error',
          err instanceof Error ? err.message : opts.messages?.error || '提交失败',
        );
      } finally {
        if (btn) btn.disabled = false;
      }
    };
    form.addEventListener('submit', fn);
    handlers.push({ form, fn });
  });

  return () => {
    handlers.forEach(({ form, fn }) => form.removeEventListener('submit', fn));
  };
}

export function useVisualSiteInquiryBinder(
  rootRef: Ref<HTMLElement | null | undefined>,
  opts: VisualInquiryBinderOptions,
) {
  let unbind = () => {};

  const rebind = () => {
    unbind();
    unbind = bindVisualSiteInquiryForms(rootRef.value ?? null, opts);
  };

  onUnmounted(() => unbind());

  return { rebind, unbind: () => unbind() };
}
