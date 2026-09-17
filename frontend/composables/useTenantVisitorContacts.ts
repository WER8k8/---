/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 租户站联系方式展示 — 与 backend visitor_locale_service 规则对齐。
 * 优先消费 visitor-context.contact_channels；缺省时按 cn_compliant_only 本地兜底。
 */

import { computed, type MaybeRefOrGetter, toValue } from 'vue';
import type { VisitorContactChannel } from './useVisitorLocale';

const CN_CHANNEL_TYPES = new Set(['wechat', 'qq', 'phone']);
const DEFAULT_ORDER = ['whatsapp', 'email', 'phone', 'wechat', 'qq'] as const;
const CN_ORDER = ['wechat', 'qq', 'phone'] as const;
const TOPBAR_TYPES = new Set(['phone', 'whatsapp', 'wechat', 'qq', 'email']);

const CHANNEL_LABELS: Record<string, Record<string, string>> = {
  wechat: { zh: '微信', en: 'WeChat' },
  qq: { zh: 'QQ', en: 'QQ' },
  phone: { zh: '电话', en: 'Tel' },
  email: { zh: '邮箱', en: 'E-mail' },
  whatsapp: { zh: 'WhatsApp', en: 'WhatsApp' },
  form: { zh: '联系表单', en: 'Contact form' },
};

export type TenantMobileQuickAction = {
  key: string;
  label: string;
  href: string;
  icon?: string;
  primary?: boolean;
  external?: boolean;
};

function channelLabel(type: string, language: string): string {
  const pack = CHANNEL_LABELS[type];
  if (!pack) return type;
  const lang = language.slice(0, 2);
  return pack[lang] || pack.en || type;
}

export function buildContactLink(channelType: string, value: string): string {
  if (channelType === 'phone') return `tel:${value}`;
  if (channelType === 'email') return `mailto:${value}`;
  if (channelType === 'whatsapp') {
    const n = value.replace(/\D/g, '');
    return n ? `https://wa.me/${n}` : '#contact';
  }
  if (channelType === 'wechat' || channelType === 'qq') return '#contact';
  if (channelType === 'form') return '#contact';
  return '#contact';
}

/** API 未返回时，按 cn_compliant_only 与 backend build_visitor_contact_channels 对齐兜底 */
export function buildFallbackContactChannels(
  contacts: Record<string, string>,
  opts: { cnCompliantOnly: boolean; language: string },
): VisitorContactChannel[] {
  const order = opts.cnCompliantOnly ? CN_ORDER : DEFAULT_ORDER;
  const items: VisitorContactChannel[] = [];

  for (const key of order) {
    if (opts.cnCompliantOnly && !CN_CHANNEL_TYPES.has(key)) continue;
    const val = (contacts[key] || '').trim();
    if (!val) continue;
    items.push({
      channel_type: key,
      value: val,
      label: channelLabel(key, opts.language),
      im_link: buildContactLink(key, val),
    });
  }

  if (!opts.cnCompliantOnly) {
    items.push({
      channel_type: 'form',
      value: '',
      label: channelLabel('form', opts.language),
      im_link: '#contact',
    });
  }

  const lang = opts.language.slice(0, 2);
  if (lang !== 'zh') {
    return items.filter((item) => item.channel_type !== 'wechat' && item.channel_type !== 'qq');
  }

  return items;
}

export function topbarContactHref(ch: VisitorContactChannel): string {
  if (ch.channel_type === 'wechat' || ch.channel_type === 'qq') return '#contact';
  return ch.im_link || '#contact';
}

export function isExternalContactChannel(ch: VisitorContactChannel): boolean {
  return ch.channel_type === 'whatsapp'
    || ch.channel_type === 'telegram'
    || ch.channel_type === 'line';
}

function actionIcon(type: string): string {
  const icons: Record<string, string> = {
    whatsapp: '💬',
    wechat: '🟢',
    qq: '🐧',
    phone: '📞',
    email: '✉️',
    form: '📋',
  };
  return icons[type] || '•';
}

export function useTenantVisitorContacts(options: {
  contactChannels: MaybeRefOrGetter<VisitorContactChannel[]>;
  cnCompliantOnly: MaybeRefOrGetter<boolean>;
  language: MaybeRefOrGetter<string>;
  rawContacts: MaybeRefOrGetter<Record<string, string>>;
  quoteLabel: MaybeRefOrGetter<string>;
}) {
  const effectiveChannels = computed(() => {
    const fromApi = toValue(options.contactChannels);
    let channels = fromApi.length
      ? fromApi
      : buildFallbackContactChannels(toValue(options.rawContacts), {
          cnCompliantOnly: toValue(options.cnCompliantOnly),
          language: toValue(options.language),
        });
    const lang = toValue(options.language).slice(0, 2);
    if (lang !== 'zh' && !toValue(options.cnCompliantOnly)) {
      channels = channels.filter(
        (c) => c.channel_type !== 'wechat' && c.channel_type !== 'qq',
      );
    }
    return channels;
  });

  const topbarChannels = computed(() =>
    effectiveChannels.value.filter((c) => TOPBAR_TYPES.has(c.channel_type) && c.value),
  );

  const contactDisplayChannels = computed(() =>
    effectiveChannels.value.filter((c) => c.channel_type !== 'form' && c.value),
  );

  const mobileQuickActions = computed<TenantMobileQuickAction[]>(() => {
    const actions: TenantMobileQuickAction[] = contactDisplayChannels.value
      .slice(0, 2)
      .map((ch) => ({
        key: ch.channel_type,
        label: ch.label,
        href: topbarContactHref(ch),
        icon: actionIcon(ch.channel_type),
        external: isExternalContactChannel(ch),
      }));

    actions.push({
      key: 'quote',
      label: toValue(options.quoteLabel),
      href: '#contact',
      primary: true,
    });

    return actions.slice(0, 3);
  });

  return {
    effectiveChannels,
    topbarChannels,
    contactDisplayChannels,
    mobileQuickActions,
  };
}
