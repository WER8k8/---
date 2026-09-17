/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 企业站共用样式（buildPageHtml + GrapesJS 区块） */

export interface SiteThemePack {
  primary: string;
  heroBg: string;
  headerBg: string;
  footerBg: string;
  accent: string;
}

export function buildEnterpriseSiteCss(theme: SiteThemePack): string {
  return `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&display=swap');

.sb-page{
  font-family:"DM Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  color:#0f172a;line-height:1.55;font-size:15px;
  -webkit-font-smoothing:antialiased;
}
.sb-container{max-width:1200px;margin:0 auto;padding:0 24px}
.sb-topbar{background:#0f172a;color:rgba(255,255,255,.88);font-size:12px;padding:8px 0}
.sb-topbar-inner{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.sb-topbar a{color:inherit;text-decoration:none;opacity:.92}
.sb-topbar a:hover{opacity:1;text-decoration:underline}
.sb-topbar-contacts{display:flex;gap:16px;flex-wrap:wrap}
.sb-header{color:#fff;padding:0;position:sticky;top:0;z-index:40;box-shadow:0 4px 24px rgb(15 23 42 / 0.12)}
.sb-header-inner{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;padding:14px 0}
.sb-brand{min-width:0}
.sb-logo{font-size:21px;font-weight:800;letter-spacing:-.02em;line-height:1.2}
.sb-tag{font-size:12px;opacity:.82;margin-top:3px;max-width:280px}
.sb-nav{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.sb-nav a{color:#fff;text-decoration:none;font-size:14px;font-weight:500;padding:8px 12px;border-radius:8px;opacity:.92}
.sb-nav-link{color:#fff;text-decoration:none;font-size:14px;font-weight:500;padding:8px 12px;border-radius:8px;opacity:.92;display:inline-block}
.sb-nav a:hover,.sb-nav-link:hover{background:rgba(255,255,255,.1);opacity:1}
.sb-nav-link--active{background:rgba(255,255,255,.14);opacity:1;font-weight:700}
.sb-logo-link{color:inherit;text-decoration:none}
.sb-header-cta{display:inline-flex;align-items:center;padding:9px 18px;border-radius:8px;background:${theme.accent};color:#fff;text-decoration:none;font-size:14px;font-weight:700;white-space:nowrap}
.sb-header-cta:hover{filter:brightness(1.06)}
.sb-hero{padding:56px 0 64px}
.sb-hero--banner{padding:0;min-height:420px;display:flex;align-items:stretch;background-size:cover;background-position:center;position:relative}
.sb-hero--banner .sb-hero-overlay{flex:1;background:linear-gradient(105deg,rgb(15 23 42 / .88) 0%,rgb(15 23 42 / .55) 55%,rgb(15 23 42 / .35) 100%);display:flex;align-items:center;padding:72px 0}
.sb-hero--banner .sb-hero-title,.sb-hero--banner .sb-hero-desc{color:#fff}
.sb-hero--banner .sb-kicker{color:${theme.accent}}
.sb-hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:40px;align-items:center}
.sb-kicker{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:${theme.accent};margin:0 0 10px}
.sb-hero-title{font-size:clamp(28px,4vw,44px);font-weight:800;margin:0 0 14px;color:${theme.primary};letter-spacing:-.03em;line-height:1.12}
.sb-hero-desc{font-size:17px;color:#475569;margin:0 0 22px;max-width:560px}
.sb-hero-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.sb-cta{display:inline-flex;align-items:center;padding:12px 24px;border-radius:10px;color:#fff;text-decoration:none;font-weight:700;font-size:14px;box-shadow:0 8px 24px rgb(37 99 235 / .22)}
.sb-cta--ghost{background:transparent;border:2px solid ${theme.primary};color:${theme.primary};box-shadow:none}
.sb-hero--banner .sb-cta--ghost{border-color:rgba(255,255,255,.65);color:#fff}
.sb-hero-visual{min-height:280px;border-radius:16px;overflow:hidden;border:1px solid #e2e8f0;background:linear-gradient(145deg,${theme.heroBg},#fff);box-shadow:0 20px 50px rgb(15 23 42 / .08)}
.sb-hero-visual img{width:100%;height:100%;min-height:280px;object-fit:cover;display:block}
.sb-hero-visual--placeholder{display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:13px;font-weight:600;background:linear-gradient(135deg,#f1f5f9,#e2e8f0)}
.sb-trust-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.sb-trust-pill{font-size:11px;font-weight:700;padding:5px 12px;border-radius:999px;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;letter-spacing:.02em}
.sb-cert-strip{display:flex;flex-wrap:wrap;gap:12px;padding:20px 0;border-bottom:1px solid #e2e8f0}
.sb-cert-item{flex:1;min-width:130px;text-align:center;padding:14px 10px;border:1px solid #e2e8f0;border-radius:12px;font-size:12px;font-weight:700;color:#334155;background:#fff;letter-spacing:.04em;text-transform:uppercase}
.sb-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;padding:28px 24px;margin:-36px auto 0;position:relative;z-index:2}
.sb-stats--flat{margin:0;padding:28px 24px;background:#f8fafc;border-radius:16px}
.sb-stat{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px 14px;text-align:center;box-shadow:0 8px 24px rgb(15 23 42 / .04)}
.sb-stat-val{font-size:26px;font-weight:800;color:${theme.primary};letter-spacing:-.02em;line-height:1.1}
.sb-stat-lbl{font-size:12px;color:#64748b;margin-top:6px;font-weight:500}
.sb-section{padding:56px 0}
.sb-section--alt{background:#f8fafc}
.sb-section-head{margin-bottom:28px;max-width:640px}
.sb-section-eyebrow{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:${theme.accent};margin:0 0 8px}
.sb-section-title{font-size:clamp(22px,2.5vw,30px);font-weight:800;margin:0 0 10px;color:${theme.primary};letter-spacing:-.02em;line-height:1.2}
.sb-section-desc{margin:0;font-size:15px;color:#64748b;line-height:1.6}
.sb-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.sb-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.sb-grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.sb-card,.sb-prod,.sb-solution,.sb-app{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;transition:box-shadow .2s,border-color .2s,transform .2s}
.sb-card:hover,.sb-prod:hover,.sb-solution:hover,.sb-app:hover{box-shadow:0 12px 32px rgb(15 23 42 / .08);border-color:#cbd5e1;transform:translateY(-2px)}
.sb-card h4,.sb-prod h4,.sb-solution h4,.sb-app h4{margin:0 0 8px;font-size:16px;font-weight:700;color:#0f172a}
.sb-card p,.sb-prod p,.sb-solution p,.sb-app p{margin:0;font-size:14px;color:#64748b;line-height:1.55}
.sb-solution-seg{font-size:11px;font-weight:700;color:${theme.accent};text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
.sb-prod-img{width:100%;height:160px;object-fit:cover;border-radius:10px;margin-bottom:12px}
.sb-prod-ph{height:160px;background:linear-gradient(135deg,#f1f5f9,#e2e8f0);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:12px;font-weight:600;margin-bottom:12px}
.sb-prod-link{display:inline-block;margin-top:10px;font-size:13px;font-weight:700;color:${theme.accent};text-decoration:none}
.sb-about-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:32px;align-items:start}
.sb-about{font-size:16px;color:#334155;line-height:1.75;margin:0}
.sb-about-side{display:flex;flex-direction:column;gap:12px}
.sb-mv-card{padding:16px;border-radius:12px;background:#fff;border:1px solid #e2e8f0}
.sb-mv-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:${theme.accent};margin-bottom:6px}
.sb-mv-text{margin:0;font-size:14px;color:#475569;line-height:1.55}
.sb-cta-band{padding:48px 0;background:linear-gradient(135deg,${theme.headerBg},${theme.footerBg});color:#fff;text-align:center}
.sb-cta-band h2{margin:0 0 10px;font-size:clamp(22px,3vw,32px);font-weight:800;letter-spacing:-.02em}
.sb-cta-band p{margin:0 0 20px;font-size:16px;opacity:.9;max-width:560px;margin-left:auto;margin-right:auto}
.sb-cta-band .sb-cta{box-shadow:0 12px 32px rgb(0 0 0 / .25)}
.sb-contact-grid{display:grid;grid-template-columns:1fr 1.05fr;gap:32px;align-items:start}
.sb-contact-info{padding:20px;border-radius:14px;background:#f8fafc;border:1px solid #e2e8f0}
.sb-contact-info h3{margin:0 0 12px;font-size:18px;font-weight:700;color:${theme.primary}}
.sb-contact-info p{margin:8px 0;color:#334155;font-size:14px}
.sb-wa-btn{display:inline-flex;align-items:center;margin-top:14px;padding:10px 18px;background:#25d366;color:#fff;border-radius:10px;text-decoration:none;font-size:14px;font-weight:700}
.sb-inquiry-form{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;display:flex;flex-direction:column;gap:10px;box-shadow:0 12px 40px rgb(15 23 42 / .06)}
.sb-inquiry-title{margin:0 0 4px;font-size:17px;font-weight:800;color:${theme.primary}}
.sb-inquiry-sub{margin:0 0 8px;font-size:13px;color:#64748b}
.sb-inquiry-input{width:100%;padding:11px 13px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;box-sizing:border-box;font-family:inherit}
.sb-inquiry-input:focus{outline:2px solid color-mix(in srgb,${theme.accent} 35%,transparent);border-color:${theme.accent}}
.sb-inquiry-submit{color:#fff;border:none;border-radius:10px;padding:12px 18px;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit}
.sb-inquiry-msg{margin:8px 0 0;font-size:13px}
.sb-inquiry-msg--error{color:#b91c1c}
.sb-inquiry-msg--success{color:#047857}
.sb-process{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.sb-process-step{text-align:center;padding:16px 10px}
.sb-process-num{width:36px;height:36px;border-radius:50%;background:${theme.accent};color:#fff;font-weight:800;display:inline-flex;align-items:center;justify-content:center;margin-bottom:10px;font-size:14px}
.sb-process-step h4{margin:0 0 4px;font-size:14px;font-weight:700}
.sb-process-step p{margin:0;font-size:12px;color:#64748b}
.sb-promise-band{margin:0 auto;padding:18px 24px 0;text-align:center;max-width:880px}
.sb-promise-label{margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:${theme.accent}}
.sb-promise-text{margin:0;font-size:clamp(16px,2vw,20px);font-weight:700;color:${theme.primary};line-height:1.45}
.sb-knowledge-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:8px;min-height:100%}
.sb-knowledge-card h4{margin:0;font-size:16px;font-weight:700;color:#0f172a;line-height:1.35}
.sb-knowledge-card p{margin:0;font-size:14px;color:#64748b;line-height:1.55;flex:1}
.sb-partners{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;align-items:center;padding:8px 0}
.sb-partner-pill{padding:10px 20px;border:1px dashed #cbd5e1;border-radius:10px;font-size:13px;font-weight:600;color:#64748b;background:#fff}
.sb-footer{color:rgba(255,255,255,.88);padding:48px 0 24px;font-size:14px}
.sb-footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:32px;margin-bottom:28px;text-align:left}
.sb-footer-brand .sb-logo{font-size:18px;margin-bottom:8px}
.sb-footer-brand p{margin:0;font-size:13px;opacity:.78;line-height:1.6;max-width:280px}
.sb-footer-col h4{margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;opacity:.95}
.sb-footer-col a,.sb-footer-col p{display:block;margin:0 0 8px;color:inherit;text-decoration:none;font-size:13px;opacity:.78}
.sb-footer-col a:hover{opacity:1;text-decoration:underline}
.sb-footer-copy{border-top:1px solid rgba(255,255,255,.12);padding-top:20px;text-align:center;font-size:12px;opacity:.65}
@media(max-width:960px){
  .sb-hero-grid,.sb-grid-3,.sb-grid-2,.sb-grid-4,.sb-stats,.sb-contact-grid,.sb-about-grid,.sb-footer-grid,.sb-process{grid-template-columns:1fr}
  .sb-nav{display:none}
  .sb-stats{margin-top:0}
  .sb-header-cta{padding:8px 14px;font-size:13px}
}
@media(max-width:768px){
  .sb-hero{padding:40px 0}
  .sb-hero--banner .sb-hero-overlay{padding:48px 0}
  .sb-section{padding:40px 0}
}

/* ══════════════════════════════════════════════════════════════
   UI PRO MAX: React Bits + Animata + Vengeance UI 极客动效体系
   让客户网站瞬间呈现出数十万定制级的高级感与商业转化吸引力
   ══════════════════════════════════════════════════════════════ */

/* 1. Vengeance UI: Aurora Mesh Hero 极光呼吸动效背景 */
.sb-hero-aurora {
  position: relative;
  overflow: hidden;
  background: radial-gradient(circle at 10% 20%, rgba(74, 155, 140, 0.08) 0%, transparent 40%),
              radial-gradient(circle at 90% 80%, rgba(14, 165, 233, 0.08) 0%, transparent 40%),
              radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 60%);
}
.sb-hero-aurora::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, rgba(74, 155, 140, 0.12) 0%, rgba(14, 165, 233, 0.06) 35%, transparent 70%);
  animation: sb-aurora-spin 28s linear infinite;
  pointer-events: none;
  z-index: 0;
}
@keyframes sb-aurora-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 2. React Bits: Spotlight Card & 3D Hover 聚光灯流光卡片 */
.sb-card, .sb-stat, .sb-prod, .sb-solution, .sb-knowledge-card {
  position: relative;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.35s ease;
  overflow: hidden;
}
.sb-card:hover, .sb-stat:hover, .sb-prod:hover, .sb-solution:hover, .sb-knowledge-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.1), 0 0 20px rgba(74, 155, 140, 0.12);
  border-color: rgba(74, 155, 140, 0.4);
}
.sb-card::after, .sb-stat::after, .sb-prod::after, .sb-solution::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(74, 155, 140, 0.06), transparent 40%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.sb-card:hover::after, .sb-stat:hover::after, .sb-prod:hover::after {
  opacity: 1;
}

/* 3. Animata: 微交互浮光按钮 (Shine & Water Ripple Effect) */
.sb-cta {
  position: relative;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.sb-cta::before {
  content: '';
  position: absolute;
  top: 0;
  left: -120%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transition: all 0.6s ease;
  transform: skewX(-20deg);
}
.sb-cta:hover::before {
  left: 140%;
}
.sb-cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(74, 155, 140, 0.4);
  filter: brightness(1.05);
}
.sb-cta:active {
  transform: translateY(0);
}

/* 4. React Bits: Floating Badges (微浮动信任胶囊) */
.sb-trust-pill, .sb-cert-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.sb-trust-pill:hover, .sb-cert-item:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  border-color: rgba(74, 155, 140, 0.4);
}

/* 5. Vengeance UI: 闪耀发光标题 (Text Gradient Shimmer) */
.sb-hero-title {
  background: linear-gradient(135deg, ${theme.primary} 0%, color-mix(in srgb, ${theme.primary} 75%, ${theme.accent}) 50%, ${theme.accent} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
`.trim();
}
