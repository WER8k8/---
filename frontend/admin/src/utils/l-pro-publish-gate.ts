/** SITE-DESIGN-01 · L-Pro 发布门禁（前端评估，与 backend site_l_pro_service 对齐） */

export interface LProPublishIssue {
  severity: 'P0' | 'P1';
  check: string;
  detail: string;
}

export interface LProPublishGate {
  ok: boolean;
  publish_ready: boolean;
  p0: number;
  p1: number;
  issues: LProPublishIssue[];
  template_id: string;
  tier: string;
}

const L_PRO_TEMPLATE_ID = 'premium-b2b-v1';
const MIN_PRODUCTS = 3;
const MIN_SPECS = 3;

function productItems(siteContent: Record<string, unknown>): Array<Record<string, unknown>> {
  const pages = siteContent.pages as Record<string, unknown> | undefined;
  const products = pages?.products as Record<string, unknown> | undefined;
  const raw = products?.productItems;
  if (!Array.isArray(raw)) return [];
  return raw.filter((x) => x && typeof x === 'object') as Array<Record<string, unknown>>;
}

function mergeProductImages(
  siteContent: Record<string, unknown>,
): Array<Record<string, unknown>> {
  const items = productItems(siteContent).map((row) => ({ ...row }));
  const assets = siteContent.assets as { productImages?: Array<{ url?: string }> } | undefined;
  const urls = (assets?.productImages || [])
    .map((i) => String(i?.url || '').trim())
    .filter(Boolean);
  if (!items.length && urls.length) {
    return urls.map((url, i) => ({
      name: `Product ${i + 1}`,
      summary: '',
      image: url,
      specs: [
        { label: 'Material', value: 'Export grade' },
        { label: 'Density', value: 'Custom available' },
        { label: 'Application', value: 'Industrial export' },
      ],
    }));
  }
  for (let i = 0; i < items.length; i += 1) {
    if (!String(items[i].image || '').trim() && urls[i]) {
      items[i].image = urls[i];
    }
  }
  if (urls.length > items.length) {
    for (let j = items.length; j < urls.length; j += 1) {
      items.push({
        name: `Product ${j + 1}`,
        summary: '',
        image: urls[j],
        specs: [
          { label: 'Material', value: 'Export grade' },
          { label: 'Density', value: 'Custom available' },
          { label: 'Application', value: 'Industrial export' },
        ],
      });
    }
  }
  return items;
}

export function evaluateLProPublishGate(siteContent: Record<string, unknown> | null | undefined): LProPublishGate {
  const issues: LProPublishIssue[] = [];
  if (!siteContent || typeof siteContent !== 'object') {
    issues.push({ severity: 'P0', check: 'site_content', detail: 'missing site_content' });
    return gateResult(issues);
  }

  const visual = siteContent.visualEditor as Record<string, unknown> | undefined;
  const templateId =
    siteContent.templateId || visual?.templateId || '';
  const tier = siteContent.templateTier;
  if (templateId !== L_PRO_TEMPLATE_ID && tier !== 'L-Pro') {
    issues.push({
      severity: 'P0',
      check: 'template',
      detail: `需选用 L-Pro 模板（${L_PRO_TEMPLATE_ID}）`,
    });
  }

  if (visual && String(visual.html || '').trim()) {
    issues.push({
      severity: 'P1',
      check: 'visual_editor_html',
      detail: '建议用 L-Pro 多页壳，勿以 Grapes 拖拽页作为默认对外脸',
    });
  }

  const items = mergeProductImages(siteContent);
  if (items.length < MIN_PRODUCTS) {
    issues.push({
      severity: 'P0',
      check: 'product_count',
      detail: `至少需要 ${MIN_PRODUCTS} 个产品，当前 ${items.length}`,
    });
  }

  const withImages = items.filter((it) => String(it.image || '').trim());
  if (withImages.length < MIN_PRODUCTS) {
    issues.push({
      severity: 'P0',
      check: 'product_images',
      detail: `至少需要 ${MIN_PRODUCTS} 个带图产品，当前 ${withImages.length}`,
    });
  }

  items.forEach((item, index) => {
    const specs = item.specs;
    const count = Array.isArray(specs) ? specs.length : 0;
    if (count < MIN_SPECS) {
      issues.push({
        severity: 'P0',
        check: 'product_specs',
        detail: `产品 ${index + 1} 至少需要 ${MIN_SPECS} 条规格，当前 ${count}`,
      });
    }
  });

  const pages = siteContent.pages as Record<string, Record<string, unknown>> | undefined;
  const about = pages?.about || {};
  if (!String(about.aboutText || '').trim()) {
    issues.push({ severity: 'P0', check: 'about', detail: '关于页正文为空' });
  }

  const contact = pages?.contact || {};
  const hasContact = ['phone', 'email', 'whatsapp', 'wechat', 'qq'].some((k) =>
    String(contact[k] || '').trim(),
  );
  if (!hasContact) {
    issues.push({
      severity: 'P0',
      check: 'contact',
      detail: '至少填写一种联系方式（电话/邮箱/WhatsApp 等）',
    });
  }

  return gateResult(issues);
}

function gateResult(issues: LProPublishIssue[]): LProPublishGate {
  const p0 = issues.filter((i) => i.severity === 'P0').length;
  const p1 = issues.filter((i) => i.severity === 'P1').length;
  const ready = p0 === 0;
  return {
    ok: ready,
    publish_ready: ready,
    p0,
    p1,
    issues,
    template_id: L_PRO_TEMPLATE_ID,
    tier: 'L-Pro',
  };
}

export function publishGateSummary(gate: LProPublishGate): { title: string; detail: string } {
  if (gate.publish_ready) {
    return {
      title: '发布就绪：L-Pro 专业站已满足上线门禁',
      detail: '产品图、规格、关于页与联系渠道已齐，可对外预览独立域。',
    };
  }
  const p0Issues = gate.issues.filter((i) => i.severity === 'P0');
  return {
    title: `还差 ${p0Issues.length} 项才能对外发布`,
    detail: p0Issues.map((i) => i.detail).join('；'),
  };
}
