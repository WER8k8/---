/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 谷歌外贸高价值事件营销打点与服务端收集器 (useMarketingBeacon)。
 * 
 * 专为 Google Ads 价值出价 (Value-Based Bidding / tROAS) 与 GA4 转化漏斗设计：
 * - trackLeadSubmitted: 询盘提交成功
 * - trackWhatsAppClick: WhatsApp 沟通点击
 * - trackBOQCalculation: BOQ 22 参数工业配载测算（高意向 EPC 信号）
 * - trackDocumentDownloaded: 下载检测报告/CAD（专业采购商信号）
 * - trackViewItem: 查看高净值产品详情
 */

import { useRuntimeConfig } from '#imports';

export interface LeadEventPayload {
  inquiryId?: string;
  name?: string;
  phone?: string;
  email?: string;
  productSlug?: string;
  estimatedValue?: number;
}

export interface WhatsAppEventPayload {
  productSlug?: string;
  productName?: string;
  sourceUrl?: string;
}

export interface BOQEventPayload {
  productSlug?: string;
  volumeM3?: number;
  containerType?: '20GP' | '40HQ';
  estimatedFobPrice?: number;
}

export interface DocEventPayload {
  productSlug?: string;
  fileName: string;
  docType: string;
}

export function useMarketingBeacon() {
  const config = useRuntimeConfig();
  const apiBase = config.public?.apiBase || '/api/v1';

  const sendToServer = async (eventName: string, payload: Record<string, any>) => {
    try {
      if (typeof window !== 'undefined') {
        const fullUrl = `${apiBase}/marketing/events`;
        fetch(fullUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event_name: eventName,
            product_slug: payload.productSlug || '',
            properties: payload,
            page_url: window.location.href,
          }),
        }).catch(() => {});
      }
    } catch {
      // 静默处理，不阻塞主业务逻辑
    }
  };

  const sendToGtag = (eventName: string, params: Record<string, any>) => {
    if (typeof window !== 'undefined' && (window as any).gtag) {
      try {
        (window as any).gtag('event', eventName, params);
      } catch {
        // ignore
      }
    }
  };

  const trackLeadSubmitted = (payload: LeadEventPayload) => {
    sendToGtag('generate_lead', {
      event_category: 'engagement',
      event_label: payload.productSlug || 'general_inquiry',
      value: payload.estimatedValue || 1000,
      currency: 'USD',
    });
    sendToServer('generate_lead', payload);
  };

  const trackWhatsAppClick = (payload: WhatsAppEventPayload) => {
    sendToGtag('contact_whatsapp', {
      event_category: 'direct_outreach',
      event_label: payload.productSlug || payload.productName || 'floating_button',
    });
    sendToServer('whatsapp_click', payload);
  };

  const trackBOQCalculation = (payload: BOQEventPayload) => {
    sendToGtag('calculate_boq', {
      event_category: 'high_intent_tool',
      event_label: payload.productSlug || 'boq_tool',
      container_type: payload.containerType,
      volume: payload.volumeM3,
    });
    sendToServer('boq_calculated', payload);
  };

  const trackDocumentDownloaded = (payload: DocEventPayload) => {
    sendToGtag('download_spec_doc', {
      event_category: 'research',
      event_label: payload.fileName,
      doc_type: payload.docType,
    });
    sendToServer('doc_downloaded', payload);
  };

  const trackViewItem = (productId: string, productName: string, price: number = 55) => {
    sendToGtag('view_item', {
      currency: 'USD',
      value: price,
      items: [{ item_id: productId, item_name: productName }],
    });
    sendToServer('view_item', { productId, productName, price });
  };

  return {
    trackLeadSubmitted,
    trackWhatsAppClick,
    trackBOQCalculation,
    trackDocumentDownloaded,
    trackViewItem,
  };
}
