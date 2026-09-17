/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="pricing-page">
    <a-alert
      v-if="loadError"
      type="warning"
      show-icon
      class="mb-4"
      :message="loadError"
      closable
      @close="loadError = ''"
    />
    <!-- Header -->
    <div class="pricing-header-section">
      <h1 class="pricing-page-title">选择最适合您的方案</h1>
      <p class="pricing-page-desc">从小微企业到跨国集团，灵活匹配您的业务规模与发展阶段</p>
      <div class="billing-toggle">
        <span class="toggle-label" :class="{ active: !annual }">按月付费</span>
        <a-switch v-model:checked="annual" checked-children="年" un-checked-children="月" />
        <span class="toggle-label" :class="{ active: annual }">按年付费</span>
        <span v-if="annual" class="toggle-save">省 2 个月</span>
      </div>
    </div>

    <!-- Pricing Cards -->
    <div class="pricing-grid">
      <div v-for="(plan, i) in plans" :key="i" class="pricing-card" :class="{ featured: plan.featured }">
        <div v-if="plan.badge" class="pricing-badge">{{ plan.badge }}</div>
        <div class="pricing-card-header">
          <h3 class="plan-name">{{ plan.name }}</h3>
          <p class="plan-slogan">{{ plan.slogan }}</p>
        </div>
        <div class="plan-price-area">
          <template v-if="plan.priceMonthly !== '定制'">
            <span class="price-currency">¥</span>
            <span class="price-amount">{{ annual ? plan.priceAnnual : plan.priceMonthly }}</span>
            <span class="price-unit">/月</span>
            <div v-if="annual && plan.priceMonthly !== plan.priceAnnual" class="price-original">¥{{ plan.priceMonthly }}/月</div>
          </template>
          <template v-else>
            <span class="price-amount price-custom">联系我们</span>
            <div class="price-unit mt-1">定制方案</div>
          </template>
        </div>
        <div class="plan-suitable">适合 {{ plan.suitable }}</div>
        <a-button :type="plan.featured ? 'primary' : 'default'" block size="large" class="plan-buy-btn" @click="handleBuy(plan)">
          {{ plan.featured ? '立即购买' : '了解详情' }}
        </a-button>
        <div v-if="annual && plan.priceMonthly !== plan.priceAnnual && plan.priceMonthly !== '定制'" class="plan-save-badge">年付省 ¥{{ plan.annualSave }}</div>

        <div class="plan-features">
          <div v-for="(group, gi) in plan.featureGroups" :key="gi" class="feature-group">
            <h4 class="feature-group-title">{{ group.title }}</h4>
            <div v-for="(feat, fi) in group.items" :key="fi" class="feature-item" :class="{ included: feat.included }">
              <CheckOutlined v-if="feat.included" class="feature-icon" />
              <CloseOutlined v-else class="feature-icon excluded" />
              <div class="feature-info">
                <span class="feature-name">{{ feat.name }}</span>
                <span v-if="feat.desc" class="feature-desc">{{ feat.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enterprise CTA -->
    <div class="enterprise-cta">
      <div class="enterprise-cta-content">
        <h2>需要更灵活的方案？</h2>
        <p>旗舰版支持完全定制，包括私有化部署、专属模型微调、SLA 保障等企业级需求</p>
        <a-button ghost size="large" class="enterprise-btn" @click="contactSales">联系我们 →</a-button>
      </div>
    </div>

    <!-- Compare Table -->
    <div class="compare-section">
      <h2 class="compare-title">全部功能对比</h2>
      <div class="compare-table-wrap">
        <table class="compare-table">
          <thead>
            <tr>
              <th class="compare-th-feat">功能</th>
              <th v-for="(plan, i) in plans" :key="i" class="compare-th-plan" :class="{ featured: plan.featured }">{{ plan.name }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(group, gi) in compareData" :key="gi">
              <tr class="compare-group-row">
                <td :colspan="plans.length + 1" class="compare-group-title">{{ group.title }}</td>
              </tr>
              <tr v-for="(row, ri) in group.rows" :key="ri" class="compare-row">
                <td class="compare-feat-name">{{ row.name }}</td>
                <td v-for="(cell, ci) in row.cells" :key="ci" class="compare-cell" :class="{ featured: plans[ci].featured }">
                  <CheckOutlined v-if="cell === true" class="compare-check" />
                  <CloseOutlined v-else-if="cell === false" class="compare-close" />
                  <span v-else class="compare-text">{{ cell }}</span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- FAQ -->
    <div class="faq-section">
      <h2 class="faq-title">套餐常见问题</h2>
      <div class="faq-list">
        <div v-for="(q, i) in faqs" :key="i" class="faq-item" :class="{ open: openFaq === i }">
          <button class="faq-question" @click="openFaq = openFaq === i ? -1 : i">
            <span>{{ q.q }}</span>
            <DownOutlined class="faq-arrow" />
          </button>
          <transition name="faq">
            <div v-if="openFaq === i" class="faq-answer">{{ q.a }}</div>
          </transition>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CheckOutlined, CloseOutlined, DownOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, ApiError } from '@/utils/api'
import {
  apiPlanToDisplayPlan,
  buildCompareRows,
  type ApiTenantPlan,
  type DisplayPlan,
} from '@/utils/tenantPlanDisplay'

const annual = ref(false)
const openFaq = ref(-1)
const plans = ref<DisplayPlan[]>([])
const compareData = ref<ReturnType<typeof buildCompareRows>>([])
const apiPlans = ref<ApiTenantPlan[]>([])
const loadError = ref('')

async function loadPlans() {
  loadError.value = ''
  try {
    let rows: ApiTenantPlan[] | null = null
    try {
      rows = await apiGet<ApiTenantPlan[]>('/tenants/plans')
    } catch (primary: unknown) {
      const isPlansRouteBug =
        primary instanceof ApiError &&
        (primary.status === 404 || /租户不存在/.test(primary.message || ''))
      if (isPlansRouteBug) {
        rows = await apiGet<ApiTenantPlan[]>('/payment/plans')
      } else {
        throw primary
      }
    }
    apiPlans.value = (rows || []).filter((p) => p.is_active !== false)
    plans.value = apiPlans.value.map(apiPlanToDisplayPlan)
    compareData.value = buildCompareRows(plans.value, apiPlans.value)
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : '套餐数据加载失败，请刷新重试'
  }
}

onMounted(loadPlans)

const faqs = [
  { q: '套餐可以随时升级或降级吗？', a: '是的，升级即时生效，差价按剩余天数折抵。降级次月生效，数据保留但超出新套餐限制的功能会暂停。' },
  { q: '年付比月付省多少？', a: '年付价格按年付总额均摊到 12 个月展示；具体折扣以各套餐后台配置为准，页面价格与「套餐配置」API 同步。' },
  { q: '免费版有功能限制吗？', a: '免费版永久免费，配额（站点数、AI 调用次数、用户数等）以当前套餐配置为准，本页数据来自后台 tenant_plans。' },
  { q: '超出套餐配额怎么办？', a: '超出部分按量计费，或直接升级套餐。我们也会在接近限额时发送预警通知。' },
  { q: '企业版和旗舰版有什么区别？', a: '企业版是 SaaS 共享实例的高级套餐，功能模块完整。旗舰版在此基础上提供私有化部署、专属模型与 SLA 等企业级选项。' },
  { q: '支持哪些支付方式？', a: '支持微信支付、支付宝、银行对公转账、国际信用卡（Visa/Mastercard）和 PayPal。企业版及以上可签年度合同，月结或季结。' },
]

function handleBuy(plan: DisplayPlan) {
  const name = plan.name
  if (plan.code === 'free') {
    message.success('免费版已可使用，请直接注册！')
  } else if (plan.code === 'flagship') {
    window.open('mailto:sales@youding.com?subject=%E6%97%97%E8%88%B0%E7%89%88%E5%92%A8%E8%AF%A2', '_blank')
    message.success('已打开邮件客户端，销售团队将在 24 小时内与您联系')
  } else {
    message.success(`已为您创建 ${name} 购买订单（${annual.value ? '年付' : '月付'}），即将跳转支付...`)
  }
}

function contactSales() {
  window.open('mailto:sales@youding.com?subject=%E5%A5%97%E9%A4%90%E5%92%A8%E8%AF%A2', '_blank')
  message.success('已记录咨询意向，销售团队将在 24 小时内与您联系')
}
</script>

<style scoped>
.pricing-page {
  max-width: 1280px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== Header ===== */
.pricing-header-section {
  text-align: center;
  padding: 2rem 1rem 3rem;
}
.pricing-page-title {
  font-size: 2.2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.pricing-page-desc {
  font-size: 1rem;
  color: #64748b;
  margin-top: 0.5rem;
}
.billing-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
.toggle-label {
  font-size: 0.88rem;
  color: #94a3b8;
  font-weight: 500;
  transition: color 0.2s;
}
.toggle-label.active {
  color: #0f172a;
  font-weight: 600;
}
.toggle-save {
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  background: #dcfce7;
  color: #16a34a;
  font-size: 0.72rem;
  font-weight: 600;
}

/* ===== Pricing Cards ===== */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
  padding: 1rem 0 3rem;
}
.pricing-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex;
  flex-direction: column;
  overflow: visible;
  padding-top: 14px;
}
.pricing-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.08);
}
.pricing-card.featured {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 8px 24px rgba(59,130,246,0.15);
  z-index: 1;
}
.pricing-card.featured:hover {
  transform: translateY(-3px);
}
.pricing-badge {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 0.2rem 0.8rem;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), var(--uj-brand, #4a9b8c));
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  z-index: 2;
}

/* Card header */
.pricing-card-header {
  padding: 1.5rem 1.25rem 0;
  text-align: center;
}
.plan-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}
.plan-slogan {
  font-size: 0.72rem;
  color: #64748b;
  margin-top: 0.25rem;
}

/* Price */
.plan-price-area {
  text-align: center;
  padding: 1rem 1.25rem;
}
.price-currency {
  font-size: 0.9rem;
  color: #64748b;
  vertical-align: top;
}
.price-amount {
  font-size: 2.2rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.price-custom {
  font-size: 1.4rem;
}
.price-unit {
  font-size: 0.8rem;
  color: #94a3b8;
}
.price-original {
  font-size: 0.78rem;
  color: #94a3b8;
  text-decoration: line-through;
  margin-top: 0.2rem;
}
.plan-suitable {
  text-align: center;
  font-size: 0.72rem;
  color: #64748b;
  padding: 0 1.25rem;
  margin-bottom: 0.75rem;
}
.plan-buy-btn {
  margin: 0 1rem 0.75rem;
  width: auto;
  border-radius: 10px;
  height: 42px;
  font-size: 0.9rem;
}
.plan-save-badge {
  text-align: center;
  font-size: 0.7rem;
  color: #16a34a;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

/* Features */
.plan-features {
  padding: 0 1rem 1.5rem;
  flex: 1;
}
.feature-group {
  margin-bottom: 1rem;
}
.feature-group-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #f1f5f9;
}
.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  padding: 0.3rem 0;
}
.feature-icon {
  font-size: 0.7rem;
  color: #10b981;
  margin-top: 0.1rem;
  flex-shrink: 0;
}
.feature-icon.excluded {
  color: #cbd5e1;
}
.feature-info {
  min-width: 0;
}
.feature-name {
  font-size: 0.78rem;
  color: #475569;
  font-weight: 500;
}
.feature-item.included .feature-name {
  color: #0f172a;
}
.feature-desc {
  display: block;
  font-size: 0.65rem;
  color: #94a3b8;
  margin-top: 0.05rem;
}

/* ===== Enterprise CTA ===== */
.enterprise-cta {
  padding: 0 0 3rem;
}
.enterprise-cta-content {
  text-align: center;
  padding: 3rem 2rem;
  border-radius: 20px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}
.enterprise-cta-content h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f8fafc;
}
.enterprise-cta-content p {
  font-size: 0.9rem;
  color: #94a3b8;
  max-width: 480px;
  margin: 0.5rem auto 1.5rem;
  line-height: 1.6;
}
.enterprise-btn {
  height: 44px;
  padding: 0 2rem;
  font-size: 0.95rem;
  border-radius: 12px;
  border-color: rgba(255,255,255,0.2);
  color: #e2e8f0;
}
.enterprise-btn:hover {
  border-color: var(--uj-brand, #4a9b8c) !important;
  color: #93c5fd !important;
}

/* ===== Compare Table ===== */
.compare-section {
  padding: 3rem 0;
}
.compare-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  text-align: center;
  margin-bottom: 2rem;
}
.compare-table-wrap {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
}
.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.compare-th-feat {
  text-align: left;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  font-weight: 600;
  color: #0f172a;
  border-bottom: 2px solid #e2e8f0;
  min-width: 160px;
}
.compare-th-plan {
  text-align: center;
  padding: 0.75rem 0.5rem;
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
  min-width: 100px;
}
.compare-th-plan.featured {
  background: #eff6ff;
  color: var(--uj-brand, #4a9b8c);
}
.compare-group-row td {
  padding: 0.5rem 1rem;
  background: #f8fafc;
  font-size: 0.72rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #f1f5f9;
}
.compare-feat-name {
  padding: 0.6rem 1rem;
  color: #334155;
  font-weight: 500;
  border-bottom: 1px solid #f1f5f9;
}
.compare-cell {
  text-align: center;
  padding: 0.6rem 0.5rem;
  border-bottom: 1px solid #f1f5f9;
  color: #64748b;
}
.compare-cell.featured {
  background: #fafbff;
}
.compare-check {
  color: #10b981;
  font-size: 0.9rem;
}
.compare-close {
  color: #cbd5e1;
  font-size: 0.9rem;
}
.compare-text {
  font-size: 0.78rem;
}
.compare-row:hover td {
  background: #fafbff;
}

/* ===== FAQ ===== */
.faq-section {
  padding: 3rem 0;
}
.faq-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  text-align: center;
  margin-bottom: 2rem;
}
.faq-list {
  max-width: 680px;
  margin: 0 auto;
}
.faq-item {
  border-bottom: 1px solid #f1f5f9;
}
.faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1rem 0;
  border: none;
  background: transparent;
  font-size: 0.92rem;
  font-weight: 500;
  color: #0f172a;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: color 0.15s;
}
.faq-question:hover {
  color: var(--uj-brand, #4a9b8c);
}
.faq-arrow {
  font-size: 0.75rem;
  color: #94a3b8;
  transition: transform 0.25s ease;
  flex-shrink: 0;
}
.faq-item.open .faq-arrow {
  transform: rotate(180deg);
}
.faq-answer {
  padding: 0 0 1rem;
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.7;
}
.faq-enter-active,
.faq-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.faq-enter-from,
.faq-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .pricing-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .pricing-card.featured { transform: none; }
  .pricing-card.featured:hover { transform: translateY(-3px); }
}
@media (max-width: 768px) {
  .pricing-page-title { font-size: 1.6rem; }
  .pricing-grid { grid-template-columns: 1fr; max-width: 420px; margin: 0 auto; }
  .pricing-card.featured { transform: none; }
  .pricing-card.featured:hover { transform: translateY(-3px); }
}
</style>
