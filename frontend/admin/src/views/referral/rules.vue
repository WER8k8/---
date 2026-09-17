/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="referral-rules">
    <!-- ===== 顶部 ===== -->
    <div class="rr-hero">
      <h1 class="rr-hero-title">活动规则</h1>
      <p class="rr-hero-desc">呼朋唤友计划 — 推荐好友注册，双双有礼</p>
    </div>

    <div class="rr-content">
      <!-- ===== 活动说明 ===== -->
      <a-card class="rr-card" :bordered="false">
        <template #title><GiftOutlined /> 活动说明</template>
        <div class="rr-card-body">
          <p>优丁建材 AI SaaS "呼朋唤友计划"邀请有礼活动，旨在回馈广大用户。已注册用户通过专属邀请码或邀请链接，成功邀请新用户注册并开通服务后，邀请者和被邀请者均可获得相应奖励。</p>
          <p>活动长期有效，优丁建材保留在法律允许范围内对活动规则进行调整的权利。</p>
        </div>
      </a-card>

      <!-- ===== 奖励阶梯 ===== -->
      <a-card class="rr-card" :bordered="false">
        <template #title><RiseOutlined /> 三级奖励阶梯</template>
        <div class="rr-card-body">
          <p class="rr-lead">邀请越多，奖励越丰厚！累计邀请人数达到以下阶梯即可解锁对应奖励：</p>
          <div class="rr-steps">
            <div class="rr-step" v-for="(s, idx) in steps" :key="idx">
              <div class="rr-step-num">{{ s.target }}人</div>
              <div class="rr-step-body">
                <div class="rr-step-label">{{ s.label }}</div>
                <div class="rr-step-desc">{{ s.desc }}</div>
              </div>
              <div class="rr-step-reward">¥{{ s.reward }}</div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- ===== 被邀请者福利 ===== -->
      <a-card class="rr-card" :bordered="false">
        <template #title><TeamOutlined /> 被邀请者福利</template>
        <div class="rr-card-body">
          <ul class="rr-benefits">
            <li>通过邀请链接注册，可额外获得 <strong>7 天免费试用期</strong>（合计 21 天）</li>
            <li>首次充值享受 <strong>9 折优惠</strong></li>
            <li>专属客服一对一 <strong>入门指导服务</strong></li>
          </ul>
        </div>
      </a-card>

      <!-- ===== 详细规则 ===== -->
      <a-card class="rr-card" :bordered="false">
        <template #title><FileTextOutlined /> 详细规则条款</template>
        <div class="rr-card-body">
          <ol class="rr-terms">
            <li><strong>邀请资格：</strong>所有已注册并登录的优丁建材 AI SaaS 正式用户均可参与。</li>
            <li><strong>邀请方式：</strong>通过个人专属邀请码或邀请链接分享给好友。系统将自动记录邀请关系。</li>
            <li><strong>有效邀请：</strong>被邀请者须通过邀请链接或填写邀请码完成注册，且注册后 <strong>7 天内</strong>完成 SaaS 套餐开通（含免费套餐），方视为有效邀请。</li>
            <li><strong>奖励发放：</strong>奖励在有效邀请确认后的 <strong>3 个工作日内</strong>发放至邀请者账户。奖励以平台余额形式发放，可用于续费、升级套餐等消费。</li>
            <li><strong>禁止行为：</strong>不得通过虚假注册、机器批量注册、恶意刷量等违反公平原则的方式获取奖励。一经发现，优丁建材有权取消奖励资格并保留追究法律责任的权利。</li>
            <li><strong>同一用户：</strong>同一公司主体、同一手机号、同一设备、同一 IP 地址等，均视为同一用户。同一用户仅能被邀请一次。</li>
            <li><strong>活动调整：</strong>优丁建材有权根据运营情况对本活动规则进行调整，调整后的规则自公布之日起生效。</li>
            <li><strong>争议解决：</strong>如对本活动规则有任何疑问，请联系客服邮箱 <a href="mailto:support@youding-builder.com">support@youding-builder.com</a> 或致电客服热线。</li>
          </ol>
        </div>
      </a-card>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { YdPage } from '@/components/youding';
import { GiftOutlined, RiseOutlined, TeamOutlined, FileTextOutlined } from '@ant-design/icons-vue';
import { apiGet } from '@/utils/api';

onMounted(async () => {
  try { await apiGet('/referral') } catch { /* 空状态 */ }
});

const steps = [
  { target: 1, label: '入门级', desc: '邀请 1 位好友完成注册开通', reward: 30 },
  { target: 3, label: '进阶级', desc: '累计邀请 3 位好友完成注册开通', reward: 60 },
  { target: 5, label: '高手级', desc: '累计邀请 5 位好友完成注册开通', reward: 100 },
]
</script>

<style scoped>
.referral-rules {
  max-width: 800px;
  margin: 0 auto;
}

.rr-hero {
  text-align: center;
  padding: 32px 20px 24px;
}
.rr-hero-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 6px;
}
.rr-hero-desc {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0;
}

.rr-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rr-card {
  border-radius: 12px;
}
.rr-card :deep(.ant-card-head) {
  border-bottom: 1px solid #f1f5f9;
  min-height: unset;
  padding: 14px 20px;
}
.rr-card :deep(.ant-card-head-title) {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
  padding: 0;
}
.rr-card :deep(.ant-card-head-title .anticon) {
  margin-right: 8px;
  color: var(--uj-brand, #4a9b8c);
}
.rr-card :deep(.ant-card-body) {
  padding: 20px;
}
.rr-card-body p {
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.8;
  margin: 0 0 8px;
}
.rr-card-body p:last-child {
  margin-bottom: 0;
}

.rr-lead {
  font-weight: 500;
  margin-bottom: 16px !important;
}

/* 奖励阶梯 */
.rr-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rr-step {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}
.rr-step:hover {
  border-color: #93c5fd;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.08);
}
.rr-step:nth-child(1) {
  border-left: 4px solid #22c55e;
}
.rr-step:nth-child(2) {
  border-left: 4px solid var(--uj-brand, #4a9b8c);
}
.rr-step:nth-child(3) {
  border-left: 4px solid #8b5cf6;
}
.rr-step-num {
  font-size: 1.5rem;
  font-weight: 800;
  color: #1e293b;
  min-width: 52px;
  text-align: center;
}
.rr-step-body {
  flex: 1;
}
.rr-step-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}
.rr-step-desc {
  font-size: 0.78rem;
  color: #64748b;
}
.rr-step-reward {
  font-size: 1.25rem;
  font-weight: 800;
  color: #d97706;
  flex-shrink: 0;
}

/* 被邀请者福利 */
.rr-benefits {
  list-style: none;
  padding: 0;
  margin: 0;
}
.rr-benefits li {
  position: relative;
  padding: 8px 0 8px 24px;
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.6;
}
.rr-benefits li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  color: #22c55e;
  font-weight: 800;
  font-size: 0.9rem;
}
.rr-benefits li strong {
  color: #1e40af;
}

/* 详细规则 */
.rr-terms {
  padding-left: 20px;
  margin: 0;
}
.rr-terms li {
  padding: 6px 0;
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.7;
}
.rr-terms li strong {
  color: #1e293b;
}
.rr-terms li a {
  color: var(--uj-brand, #4a9b8c);
  text-decoration: none;
}
.rr-terms li a:hover {
  text-decoration: underline;
}
</style>
