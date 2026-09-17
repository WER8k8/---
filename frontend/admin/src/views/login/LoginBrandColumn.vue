/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="brand-col">
    <!-- decorative animated layers -->
    <div class="brand-mesh" />
    <div class="brand-grid" />
    <div class="brand-deco brand-deco-tr" />
    <div class="brand-deco brand-deco-bl" />
    <div class="brand-deco brand-deco-mr" />

    <div class="brand-inner">
      <div class="brand-logo">
        <div class="brand-logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
        </div>
        <span class="brand-logo-text">优丁</span>
      </div>

      <h1 class="brand-headline">智能外贸<br /><span class="brand-headline-accent">效率倍增</span></h1>
      <p class="brand-desc">一站式多租户外贸 SaaS 平台，助力企业全球化运营，让团队协作与业务增长同频加速。</p>

      <div class="brand-features">
        <div class="brand-feature">
          <div class="feature-icon-bg">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
          </div>
          <div>
            <h3 class="feature-title">多租户管理</h3>
            <p class="feature-desc">超管、租户、代理三级角色体系，权限隔离清晰可控</p>
          </div>
        </div>
        <div class="brand-feature">
          <div class="feature-icon-bg">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" /></svg>
          </div>
          <div>
            <h3 class="feature-title">智能数据分析</h3>
            <p class="feature-desc">实时数据看板，洞察业务趋势，驱动科学决策</p>
          </div>
        </div>
        <div class="brand-feature">
          <div class="feature-icon-bg">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
          </div>
          <div>
            <h3 class="feature-title">全球化运营</h3>
            <p class="feature-desc">多语言、多币种支持，助力企业拓展全球市场</p>
          </div>
        </div>
      </div>

      <div class="brand-stats">
        <div class="brand-stat">
          <span class="stat-num">5,000<span class="stat-plus">+</span></span>
          <span class="stat-label">外贸企业信赖</span>
        </div>
        <span class="stat-divider" />
        <div class="brand-stat">
          <span class="stat-num">120<span class="stat-plus">+</span></span>
          <span class="stat-label">覆盖国家地区</span>
        </div>
        <span class="stat-divider" />
        <div class="brand-stat">
          <span class="stat-num">60<span class="stat-plus">%</span></span>
          <span class="stat-label">平均效率提升</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.brand-col {
  position: relative;
  display: none;
  width: 50%;
  background: linear-gradient(155deg, #2f7d6e 0%, #4a9b8c 52%, #3a8f7e 100%);
  overflow: hidden;
  padding: 3rem;
  z-index: 1;
  color: #fff;
  isolation: isolate;
}
@media (min-width: 1024px) {
  .brand-col { display: flex; }
  .form-col { width: 50%; }
}

/* Animated soft-light mesh */
.brand-mesh {
  position: absolute;
  inset: 0;
  z-index: -2;
  background:
    radial-gradient(42rem 42rem at 88% -8%, rgba(94, 234, 212, 0.32), transparent 60%),
    radial-gradient(38rem 38rem at 6% 108%, rgba(13, 148, 136, 0.45), transparent 60%),
    radial-gradient(30rem 30rem at 50% 50%, rgba(255, 255, 255, 0.06), transparent 70%);
  animation: brand-drift 18s ease-in-out infinite alternate;
}
@keyframes brand-drift {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(-2%, 2%, 0) scale(1.06); }
}

/* Faint dot grid overlay */
.brand-grid {
  position: absolute;
  inset: 0;
  z-index: -1;
  background-image: radial-gradient(rgba(255, 255, 255, 0.13) 1px, transparent 1px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(120% 120% at 30% 20%, #000 35%, transparent 78%);
  mask-image: radial-gradient(120% 120% at 30% 20%, #000 35%, transparent 78%);
  opacity: 0.7;
}

.brand-deco {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  opacity: 0.4;
  z-index: -1;
}
.brand-deco-tr { top: -5rem; right: -5rem; width: 16rem; height: 16rem; animation: float-a 14s ease-in-out infinite; }
.brand-deco-bl { bottom: -8rem; left: -8rem; width: 24rem; height: 24rem; animation: float-b 16s ease-in-out infinite; }
.brand-deco-mr { top: 50%; right: 10%; width: 8rem; height: 8rem; animation: float-a 12s ease-in-out infinite reverse; }
@keyframes float-a {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-18px); }
}
@keyframes float-b {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(22px); }
}

.brand-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  max-width: 480px;
  margin: 0 auto;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2.25rem;
  animation: brand-rise 0.7s var(--uj-ease, ease) both;
}
.brand-logo-icon {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #fff;
}

.brand-headline {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 1rem;
  letter-spacing: -0.03em;
  color: #fff;
  animation: brand-rise 0.7s var(--uj-ease, ease) 0.08s both;
}
.brand-headline-accent {
  background: linear-gradient(90deg, #ffd9a8, #ffe9cf);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand-desc {
  font-size: 1.05rem;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.75;
  margin-bottom: 2.5rem;
  max-width: 26rem;
  animation: brand-rise 0.7s var(--uj-ease, ease) 0.16s both;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: brand-rise 0.7s var(--uj-ease, ease) 0.24s both;
}

.brand-feature {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.95rem 1.1rem;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 14px;
  backdrop-filter: blur(6px);
  transition: background 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
}
.brand-feature:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
}

.feature-icon-bg {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.14));
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.feature-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #fff;
}

.feature-desc {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.5;
}

.brand-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 2.25rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
  animation: brand-rise 0.7s var(--uj-ease, ease) 0.32s both;
}
.brand-stat {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.stat-num {
  font-size: 1.4rem;
  font-weight: 800;
  line-height: 1;
  color: #fff;
  letter-spacing: -0.02em;
}
.stat-plus {
  font-size: 0.9rem;
  font-weight: 700;
  margin-left: 1px;
  color: #ffe9cf;
}
.stat-label {
  font-size: 0.6875rem;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
}
.stat-divider {
  width: 1px;
  height: 2rem;
  background: rgba(255, 255, 255, 0.22);
}

@keyframes brand-rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .brand-mesh,
  .brand-deco,
  .brand-logo,
  .brand-headline,
  .brand-desc,
  .brand-features,
  .brand-stats {
    animation: none !important;
  }
}
</style>
