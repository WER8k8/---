/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import type { Editor } from 'grapesjs';

import { buildEnterpriseSiteCss } from './enterpriseSiteStyles';

const BLOCK_CATEGORY = '优丁外贸';

const INQUIRY_FORM = `
<form class="sb-inquiry-form" data-yd-block="inquiry">
  <h3 class="sb-inquiry-title">在线询盘</h3>
  <p class="sb-inquiry-sub">欢迎填写起订量、目的港与交期需求。</p>
  <input type="text" name="name" placeholder="您的姓名 *" class="sb-inquiry-input"/>
  <input type="email" name="email" placeholder="邮箱" class="sb-inquiry-input"/>
  <input type="text" name="phone" placeholder="电话 / WhatsApp *" class="sb-inquiry-input"/>
  <input type="text" name="product" placeholder="产品 / 规格" class="sb-inquiry-input"/>
  <textarea name="message" placeholder="数量、目的港、其他要求…" rows="4" class="sb-inquiry-input"></textarea>
  <button type="submit" class="sb-inquiry-submit">提交询盘</button>
</form>`;

const WHATSAPP_CTA = `
<a class="sb-wa-btn" href="https://wa.me/8613800000000" target="_blank" rel="noopener" data-yd-block="whatsapp">
  WhatsApp 咨询
</a>`;

const TRUST_BADGES = `
<div class="sb-trust-row" data-yd-block="trust">
  <span class="sb-trust-pill">15+ 年行业经验</span>
  <span class="sb-trust-pill">OEM / ODM</span>
  <span class="sb-trust-pill">ISO 9001</span>
  <span class="sb-trust-pill">全球出口</span>
</div>`;

const STATS_ROW = `
<section class="sb-stats sb-container sb-stats--flat" data-yd-block="stats">
  <div class="sb-stat"><div class="sb-stat-val">50,000+</div><div class="sb-stat-lbl">年产能</div></div>
  <div class="sb-stat"><div class="sb-stat-val">40+</div><div class="sb-stat-lbl">出口国家</div></div>
  <div class="sb-stat"><div class="sb-stat-val">1,000+</div><div class="sb-stat-lbl">B2B 客户</div></div>
  <div class="sb-stat"><div class="sb-stat-val">100+</div><div class="sb-stat-lbl">产品 SKU</div></div>
</section>`;

const CERT_STRIP = `
<div class="sb-cert-strip" data-yd-block="certs">
  <div class="sb-cert-item">ISO 9001</div>
  <div class="sb-cert-item">CE 认证</div>
  <div class="sb-cert-item">验厂报告</div>
  <div class="sb-cert-item">SGS 检测</div>
</div>`;

const SECTION_HEAD = `
<div class="sb-section-head" data-yd-block="section-head">
  <p class="sb-section-eyebrow">核心优势</p>
  <h2 class="sb-section-title">为什么选择我们</h2>
  <p class="sb-section-desc">工厂直供，配套出口单证与质检服务。</p>
</div>`;

const CTA_BAND = `
<section class="sb-cta-band" data-yd-block="cta-band">
  <div class="sb-container">
    <h2>准备启动您的项目？</h2>
    <p>预约验厂、索取数据表与 FOB 报价，24 小时内回复。</p>
    <a class="sb-cta" href="#contact">立即询盘</a>
  </div>
</section>`;

const PROCESS_STEPS = `
<section class="sb-section sb-container" data-yd-block="process">
  <div class="sb-section-head">
    <p class="sb-section-eyebrow">合作流程</p>
    <h2 class="sb-section-title">我们如何合作</h2>
  </div>
  <div class="sb-process">
    <div class="sb-process-step"><div class="sb-process-num">1</div><h4>询盘</h4><p>提供规格与数量</p></div>
    <div class="sb-process-step"><div class="sb-process-num">2</div><h4>报价</h4><p>24h 内 FOB/CIF</p></div>
    <div class="sb-process-step"><div class="sb-process-num">3</div><h4>打样</h4><p>检测报告与包装</p></div>
    <div class="sb-process-step"><div class="sb-process-num">4</div><h4>生产</h4><p>质检与出货单证</p></div>
  </div>
</section>`;

const JTBD_SERVICE_STAGES = `
<section class="sb-section sb-section--alt sb-container" data-yd-block="service-stages">
  <div class="sb-section-head">
    <p class="sb-section-eyebrow">项目阶段</p>
    <h2 class="sb-section-title">这单你现在处于哪一步？</h2>
    <p class="sb-section-desc">按客户决策链展示：询盘 → 打样 → 小批 → 量产，不按车间分区陈列。</p>
  </div>
  <div class="sb-process">
    <div class="sb-process-step" data-yd-block="service-stage"><div class="sb-process-num">01</div><h4>询盘与可行性</h4><p>图纸、材料、公差与 MOQ 评估</p></div>
    <div class="sb-process-step" data-yd-block="service-stage"><div class="sb-process-num">02</div><h4>打样 / 首件</h4><p>首件报告、包装确认</p></div>
    <div class="sb-process-step" data-yd-block="service-stage"><div class="sb-process-num">03</div><h4>小批试产</h4><p>量产前验证节拍与良率</p></div>
    <div class="sb-process-step" data-yd-block="service-stage"><div class="sb-process-num">04</div><h4>批量生产</h4><p>稳定质检与出货单证</p></div>
  </div>
</section>`;

const JTBD_PROMISE_BAND = `
<section class="sb-promise-band sb-container" data-yd-block="primary-promise">
  <p class="sb-promise-label">全站主承诺</p>
  <p class="sb-promise-text">写一句买家能记住的结果 — Hero、数据条、底部 CTA 保持一致（勿写未核实的周期数字）。</p>
</section>`;

const JTBD_KNOWLEDGE_HUB = `
<section class="sb-section sb-section--alt sb-container" data-yd-block="knowledge-hub">
  <div class="sb-section-head">
    <p class="sb-section-eyebrow">技术内容</p>
    <h2 class="sb-section-title">先接住搜索意图，再导询盘</h2>
    <p class="sb-section-desc">工艺/选型干货，证明你懂行，而不是口号墙。</p>
  </div>
  <div class="sb-grid-3">
    <article class="sb-knowledge-card" data-yd-block="knowledge-topic">
      <h4>如何整理 RFQ 让报价更快</h4>
      <p>图纸、数量、目的港、认证要求清单</p>
      <a class="sb-prod-link" href="#contact">讨论规格 →</a>
    </article>
    <article class="sb-knowledge-card" data-yd-block="knowledge-topic">
      <h4>打样门槛 vs 小批试产</h4>
      <p>何时开模、何时锁工艺参数</p>
      <a class="sb-prod-link" href="#contact">讨论规格 →</a>
    </article>
    <article class="sb-knowledge-card" data-yd-block="knowledge-topic">
      <h4>出口单证买家常问什么</h4>
      <p>产地证、HS、验货预约</p>
      <a class="sb-prod-link" href="#contact">讨论规格 →</a>
    </article>
  </div>
</section>`;

const PARTNERS_ROW = `
<section class="sb-section sb-section--alt sb-container" data-yd-block="partners">
  <div class="sb-section-head" style="margin-left:auto;margin-right:auto;text-align:center">
    <p class="sb-section-eyebrow">合作伙伴</p>
    <h2 class="sb-section-title">全球客户</h2>
  </div>
  <div class="sb-partners">
    <span class="sb-partner-pill">经销商 A</span>
    <span class="sb-partner-pill">工程总包</span>
    <span class="sb-partner-pill">品牌 OEM</span>
    <span class="sb-partner-pill">区域代理</span>
  </div>
</section>`;

const FOOTER_BLOCK = `
<footer class="sb-footer" data-yd-block="footer" style="background:#1e293b">
  <div class="sb-container">
    <div class="sb-footer-grid">
      <div class="sb-footer-brand"><div class="sb-logo">公司名称</div><p>专业建材出口制造商。</p></div>
      <div class="sb-footer-col"><h4>快速链接</h4><a href="#products">产品中心</a><a href="#contact">联系我们</a></div>
      <div class="sb-footer-col"><h4>联系方式</h4><p>sales@example.com</p></div>
    </div>
    <div class="sb-footer-copy">© 公司名称 版权所有</div>
  </div>
</footer>`;

/** GrapesJS 侧栏 · 建材外贸 / 企业站区块 */
export function registerYoudingBlocks(editor: Editor): void {
  const bm = editor.BlockManager;

  bm.add('yd-inquiry-form', {
    label: '询盘表单',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-envelope' },
    content: INQUIRY_FORM,
  });

  bm.add('yd-whatsapp', {
    label: 'WhatsApp 按钮',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-comment' },
    content: WHATSAPP_CTA,
  });

  bm.add('yd-trust-badges', {
    label: '信任徽章',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-shield' },
    content: TRUST_BADGES,
  });

  bm.add('yd-stats-row', {
    label: '数据条',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-bar-chart' },
    content: STATS_ROW,
  });

  bm.add('yd-cert-strip', {
    label: '认证条',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-certificate' },
    content: CERT_STRIP,
  });

  bm.add('yd-section-head', {
    label: '区块标题',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-header' },
    content: SECTION_HEAD,
  });

  bm.add('yd-cta-band', {
    label: '全宽 CTA 条',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-bullhorn' },
    content: CTA_BAND,
  });

  bm.add('yd-process', {
    label: '合作流程',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-list-ol' },
    content: PROCESS_STEPS,
  });

  bm.add('yd-jtbd-stages', {
    label: 'JTBD · 项目阶段',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-road' },
    content: JTBD_SERVICE_STAGES,
  });

  bm.add('yd-jtbd-promise', {
    label: 'JTBD · 主承诺条',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-bullseye' },
    content: JTBD_PROMISE_BAND,
  });

  bm.add('yd-jtbd-knowledge', {
    label: 'JTBD · 技术干货',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-book' },
    content: JTBD_KNOWLEDGE_HUB,
  });

  bm.add('yd-partners', {
    label: '合作伙伴',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-handshake-o' },
    content: PARTNERS_ROW,
  });

  bm.add('yd-footer', {
    label: '企业页脚',
    category: BLOCK_CATEGORY,
    attributes: { class: 'fa fa-window-minimize' },
    content: FOOTER_BLOCK,
  });
}

export function appendBlockStyles(editor: Editor): void {
  editor.addStyle(
    buildEnterpriseSiteCss({
      primary: '#1e3a5f',
      heroBg: '#f1f5f9',
      headerBg: '#1e293b',
      footerBg: '#1e293b',
      accent: '#4a9b8c',
    }),
  );
}

export function insertBlockById(editor: Editor, blockId: string): void {
  const block = editor.BlockManager.get(blockId);
  if (!block) return;
  const content = block.get('content');
  editor.addComponents(content as string);
}
