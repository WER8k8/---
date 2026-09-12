<template>
  <div class="terms-wrap">
    <main class="terms-page" tabindex="-1">
      <header>
        <h1>服务条款</h1>
        <p class="meta">最后更新:2026-06-10</p>
      </header>

      <section>
        <h2>1. 接受条款</h2>
        <p>
          您注册或使用优丁服务即视为同意本条款。如不同意,请停止使用。
        </p>
      </section>

      <section>
        <h2>2. 账户责任</h2>
        <ul>
          <li>您须对账户下行为负责</li>
          <li>密码和 API Key 须妥善保管</li>
          <li>发现异常请立即通知我们</li>
        </ul>
      </section>

      <section>
        <h2>3. 禁止行为</h2>
        <ul>
          <li>发布违法、违规、侵权内容</li>
          <li>滥用 API、绕过限流、进行反向工程</li>
          <li>干扰系统正常运行、植入恶意代码</li>
        </ul>
      </section>

      <section>
        <h2>4. 知识产权</h2>
        <p>
          优丁平台代码、品牌、设计由我们持有;您录入的业务数据归您所有。
        </p>
      </section>

      <section>
        <h2>5. 服务变更与终止</h2>
        <p>
          我们保留随时修改或终止部分功能的权利,会提前 30 天通知付费用户。
        </p>
      </section>

      <section>
        <h2>6. 免责与责任限制</h2>
        <p>
          服务按"现状"提供;因不可抗力(网络中断、第三方服务故障)导致的中断,
          我们在合理范围内协助恢复,但不承担直接经济损失。
        </p>
      </section>

      <section>
        <h2>7. 适用法律</h2>
        <p>本条款适用中华人民共和国法律,争议由上海仲裁委员会仲裁。</p>
      </section>

      <footer>
        <router-link to="/privacy">查看隐私政策</router-link>
        <span class="divider">·</span>
        <router-link to="/">返回首页</router-link>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
// 静态页面
</script>

<style scoped lang="scss">
.terms-wrap {
  min-height: 100vh;
  background: var(--uj-bg-page, #f4f6f9);
  padding: 24px 16px 80px;
}
.terms-page {
  max-width: 760px;
  margin: 0 auto;
  background: var(--uj-bg-card, #fff);
  padding: 40px 48px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  font-family: var(--uj-font-sans);
  color: var(--uj-text, #0f172a);
  line-height: 1.7;
  &:focus { outline: none; }
  header h1 { font-size: 28px; margin: 0 0 8px; }
  .meta { color: var(--uj-text-muted); font-size: 13px; margin: 0 0 28px; }
  section { margin-bottom: 24px; }
  h2 { font-size: 18px; margin: 0 0 10px; }
  p, li { font-size: 15px; color: var(--uj-text-secondary); }
  ul { padding-left: 20px; }
  footer {
    border-top: 1px solid var(--uj-border);
    padding-top: 16px;
    margin-top: 32px;
    font-size: 13px;
    color: var(--uj-text-muted);
    a { color: var(--uj-brand); text-decoration: none; }
    a:focus-visible { outline: 2px solid var(--uj-brand); outline-offset: 2px; }
    .divider { margin: 0 8px; color: #cbd5e1; }
  }
}
@media (max-width: 600px) {
  .terms-page { padding: 24px 20px; }
  h1 { font-size: 22px; }
}
</style>
