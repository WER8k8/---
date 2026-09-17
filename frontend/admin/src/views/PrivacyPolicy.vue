/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="privacy-wrap">
    <a class="skip-link" href="#privacy-main">跳到主要内容</a>
    <main id="privacy-main" class="privacy-page" tabindex="-1">
      <header class="privacy-header">
        <h1 class="privacy-title">隐私政策</h1>
        <p class="privacy-meta">
          最后更新:<time datetime="2026-06-10">2026-06-10</time>
          | 版本:v3.0
        </p>
      </header>

      <section class="privacy-section" aria-labelledby="s-collect">
        <h2 id="s-collect">1. 我们收集什么</h2>
        <p>
          优丁(以下简称"我们")是面向建材外贸卖家的 AI 卖货操作系统。
          为提供核心服务,我们在您使用过程中收集以下信息:
        </p>
        <ul>
          <li><strong>账户信息</strong>:邮箱、手机号、企业名称(用于登录和身份验证)</li>
          <li><strong>业务数据</strong>:产品、询盘、订单、客户(由您主动录入)</li>
          <li><strong>设备信息</strong>:浏览器类型、操作系统、IP(用于安全和审计)</li>
          <li><strong>使用日志</strong>:功能点击、API 调用、性能埋点(用于产品改进)</li>
        </ul>
      </section>

      <section class="privacy-section" aria-labelledby="s-use">
        <h2 id="s-use">2. 怎么使用</h2>
        <ul>
          <li>提供、维护、改进和推广我们的服务</li>
          <li>处理您的请求、订单和支付</li>
          <li>发送服务通知(可关闭营销类)</li>
          <li>检测并防止欺诈、滥用和安全事件</li>
          <li>遵守法律法规要求</li>
        </ul>
      </section>

      <section class="privacy-section" aria-labelledby="s-share">
        <h2 id="s-share">3. 会不会共享给第三方</h2>
        <p>
          <strong>不会出售您的个人数据。</strong>仅在以下情况共享:
        </p>
        <ul>
          <li>经您明示同意的第三方服务(如您绑定的海关数据、IM 平台)</li>
          <li>我们的关联方(集团内部必要的数据处理)</li>
          <li>法律法规要求或政府主管部门</li>
        </ul>
      </section>

      <section class="privacy-section" aria-labelledby="s-cookie">
        <h2 id="s-cookie">4. Cookie 使用</h2>
        <table class="privacy-table" aria-label="Cookie 分类说明">
          <thead>
            <tr><th>分类</th><th>用途</th><th>可否关闭</th></tr>
          </thead>
          <tbody>
            <tr><td>必要</td><td>登录会话、防 CSRF</td><td>不可</td></tr>
            <tr><td>偏好</td><td>主题/语言/布局</td><td>可</td></tr>
            <tr><td>分析</td><td>页面访问统计(匿名)</td><td>可</td></tr>
            <tr><td>营销</td><td>推荐与广告</td><td>可</td></tr>
          </tbody>
        </table>
        <p>
          您可以随时通过页面底部的"Cookie 设置"或
          <router-link to="/privacy/cookies">Cookie 偏好</router-link>
          调整。
        </p>
      </section>

      <section class="privacy-section" aria-labelledby="s-rights">
        <h2 id="s-rights">5. 您的权利</h2>
        <p>依据《个人信息保护法》及 GDPR,您拥有:</p>
        <ul>
          <li><strong>知情权</strong>:本政策即是</li>
          <li><strong>访问权</strong>:可导出账户全部数据</li>
          <li><strong>更正权</strong>:可修改或删除</li>
          <li><strong>删除权</strong>:可申请账户注销(15 个工作日)</li>
          <li><strong>撤回同意</strong>:随时撤回,不影响已发生处理</li>
        </ul>
        <p>联系 DPO:<a href="mailto:dpo@youding.com">dpo@youding.com</a></p>
      </section>

      <section class="privacy-section" aria-labelledby="s-retention">
        <h2 id="s-retention">6. 保留期限</h2>
        <p>
          业务数据(询盘/订单/产品)在您账户有效期内保留;
          账户注销后 30 天内物理删除,30-90 天备份保留用于合规审计。
        </p>
      </section>

      <section class="privacy-section" aria-labelledby="s-contact">
        <h2 id="s-contact">7. 联系我们</h2>
        <address class="privacy-address">
          优丁(上海)数据科技有限公司<br />
          数据保护官(DPO):王先生<br />
          邮箱:<a href="mailto:dpo@youding.com">dpo@youding.com</a><br />
          电话:021-XXXX-XXXX<br />
          注册地:上海市浦东新区
        </address>
      </section>

      <footer class="privacy-footer">
        <router-link to="/terms">服务条款</router-link>
        <span class="divider">·</span>
        <router-link to="/privacy/cookies">Cookie 偏好</router-link>
        <span class="divider">·</span>
        <router-link to="/">返回首页</router-link>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
// 静态页面,无逻辑
</script>

<style scoped lang="scss">
.privacy-wrap {
  min-height: 100vh;
  background: var(--uj-bg-page, #f4f6f9);
  padding: 24px 16px 80px;
}
.privacy-page {
  max-width: 760px;
  margin: 0 auto;
  background: var(--uj-bg-card, #fff);
  padding: 40px 48px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  font-family: var(--uj-font-sans);
  color: var(--uj-text, #0f172a);
  line-height: 1.7;
  &:focus {
    outline: none;
  }
}
.privacy-header {
  border-bottom: 1px solid var(--uj-border, #e2e8f0);
  padding-bottom: 20px;
  margin-bottom: 28px;
}
.privacy-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--uj-text, #0f172a);
}
.privacy-meta {
  font-size: 13px;
  color: var(--uj-text-muted, #64748b);
  margin: 0;
}
.privacy-section {
  margin-bottom: 28px;
  h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 12px;
    color: var(--uj-text, #0f172a);
  }
  p, li {
    font-size: 15px;
    color: var(--uj-text-secondary, #334155);
  }
  ul {
    padding-left: 20px;
    li {
      margin-bottom: 6px;
    }
  }
  a {
    color: var(--uj-brand, #4a9b8c);
    text-decoration: underline;
  }
  a:focus-visible {
    outline: 2px solid var(--uj-brand, #4a9b8c);
    outline-offset: 2px;
  }
}
.privacy-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
  th, td {
    border: 1px solid var(--uj-border, #e2e8f0);
    padding: 8px 12px;
    text-align: left;
  }
  th {
    background: #f8fafc;
    font-weight: 600;
  }
}
.privacy-address {
  font-style: normal;
  background: #f8fafc;
  border-left: 3px solid var(--uj-brand, #4a9b8c);
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
}
.privacy-footer {
  border-top: 1px solid var(--uj-border, #e2e8f0);
  padding-top: 16px;
  margin-top: 32px;
  font-size: 13px;
  color: var(--uj-text-muted, #64748b);
  a {
    color: var(--uj-brand, #4a9b8c);
    text-decoration: none;
  }
  a:focus-visible {
    outline: 2px solid var(--uj-brand, #4a9b8c);
    outline-offset: 2px;
  }
  .divider {
    margin: 0 8px;
    color: var(--uj-text-muted, #cbd5e1);
  }
}
.skip-link {
  position: fixed;
  top: -100px;
  left: 8px;
  z-index: 9999;
  padding: 10px 16px;
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  border-radius: 8px;
}
.skip-link:focus,
.skip-link:focus-visible {
  top: 8px;
  outline: 2px solid #fff;
  outline-offset: 2px;
}
@media (max-width: 600px) {
  .privacy-page {
    padding: 24px 20px;
  }
  .privacy-title {
    font-size: 22px;
  }
}
</style>
