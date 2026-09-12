<template>
  <YdPage surface="elevated">
  <div class="showcase-page">
    <!-- ==================== HERO ==================== -->
    <section class="hero-section">
      <div class="hero-bg-pattern"></div>
      <div class="hero-content">
        <div class="hero-badge">AI 驱动 · 建材行业专精</div>
        <h1 class="hero-title">优丁 AI SaaS</h1>
        <p class="hero-subtitle">建材行业数字化营销平台 — 从搜索引擎到国际询盘，一站式智能解决方案</p>
        <div class="hero-actions">
          <a-button type="primary" size="large" class="hero-btn-primary" @click="scrollToSection('pricing')">立即购买</a-button>
          <a-button size="large" ghost class="hero-btn-ghost" @click="scrollToSection('features')">查看功能</a-button>
        </div>
        <div class="hero-stats">
          <div class="hero-stat"><span class="hero-stat-num">200+</span><span class="hero-stat-label">服务企业</span></div>
          <div class="hero-stat"><span class="hero-stat-num">31</span><span class="hero-stat-label">支持语言</span></div>
          <div class="hero-stat"><span class="hero-stat-num">98.6%</span><span class="hero-stat-label">客户续费率</span></div>
        </div>
      </div>
    </section>

    <!-- ==================== FEATURES ==================== -->
    <section id="features" class="features-section">
      <div class="section-header">
        <h2 class="section-title">六大核心功能</h2>
        <p class="section-desc">全链路数字化营销，覆盖获客、转化到管理每一环节</p>
      </div>
      <div class="features-grid">
        <div v-for="(feat, i) in features" :key="i" class="feature-card" @mouseenter="hoveredFeat = i" @mouseleave="hoveredFeat = -1" :class="{ active: hoveredFeat === i }">
          <div class="feat-icon-wrap" :style="{ background: feat.bg }">
            <component :is="feat.icon" class="feat-icon" />
          </div>
          <h3 class="feat-title">{{ feat.title }}</h3>
          <p class="feat-desc">{{ feat.desc }}</p>
          <div class="feat-tags">
            <span v-for="tag in feat.tags" :key="tag" class="feat-tag">{{ tag }}</span>
          </div>
          <div class="feat-preview">
            <div class="feat-preview-bar">
              <span class="feat-preview-dot"></span>
              <span class="feat-preview-dot"></span>
              <span class="feat-preview-dot"></span>
            </div>
            <div class="feat-preview-body">
              <div class="feat-preview-line" v-for="n in 3" :key="n" :style="{ width: (80 - n * 15) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== PRICING TABLE ==================== -->
    <section id="pricing" class="pricing-section">
      <div class="section-header">
        <h2 class="section-title">灵活套餐，按需选择</h2>
        <p class="section-desc">从小微企业到跨国集团，总有一款适合你</p>
      </div>
      <div class="pricing-grid">
        <div v-for="(plan, i) in pricingPlans" :key="i" class="pricing-card" :class="{ highlighted: plan.highlighted }">
          <div v-if="plan.badge" class="pricing-badge">{{ plan.badge }}</div>
          <div class="pricing-header">
            <h3 class="pricing-name">{{ plan.name }}</h3>
            <p class="pricing-slogan">{{ plan.slogan }}</p>
          </div>
          <div class="pricing-amount">
            <span class="pricing-currency">¥</span>
            <span class="pricing-price">{{ plan.price }}</span>
            <span class="pricing-unit">/月</span>
          </div>
          <p class="pricing-annual">年付 {{ plan.annualPrice }} 元/月 · 省 {{ plan.annualSave }}</p>
          <ul class="pricing-features">
            <li v-for="(f, fi) in plan.features" :key="fi" class="pricing-feat-item" :class="{ included: f.included }">
              <CheckOutlined v-if="f.included" class="pricing-feat-icon" />
              <CloseOutlined v-else class="pricing-feat-icon excluded" />
              <span>{{ f.label }}</span>
            </li>
          </ul>
          <a-button :type="plan.highlighted ? 'primary' : 'default'" block size="large" class="pricing-btn" @click="scrollToSection('pricing')">
            {{ plan.highlighted ? '立即购买' : '了解详情' }}
          </a-button>
        </div>
      </div>
    </section>

    <!-- ==================== CASE STUDIES ==================== -->
    <section class="cases-section">
      <div class="section-header">
        <h2 class="section-title">客户成功案例</h2>
        <p class="section-desc">看看同行为什么选择优丁 AI SaaS</p>
      </div>
      <div class="cases-grid">
        <div v-for="(c, i) in cases" :key="i" class="case-card">
          <div class="case-avatar-wrap" :style="{ background: c.color }">
            <span class="case-avatar-text">{{ c.abbr }}</span>
          </div>
          <div class="case-body">
            <h3 class="case-company">{{ c.company }}</h3>
            <p class="case-industry">{{ c.industry }}</p>
            <div class="case-results">
              <div v-for="(r, ri) in c.results" :key="ri" class="case-result">
                <span class="case-result-num">{{ r.num }}</span>
                <span class="case-result-label">{{ r.label }}</span>
              </div>
            </div>
            <p class="case-quote">"{{ c.quote }}"</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== FAQ ==================== -->
    <section class="faq-section">
      <div class="section-header">
        <h2 class="section-title">常见问题</h2>
        <p class="section-desc">关于优丁 AI SaaS 的常见疑问</p>
      </div>
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
    </section>

    <!-- ==================== CTA ==================== -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">立即开始免费试用</h2>
        <p class="cta-desc">无需信用卡，14 天全功能试用，让您的业务即刻迈向数字化</p>
        <div class="cta-actions">
          <a-button type="primary" size="large" class="cta-btn" @click="scrollToSection('pricing')">免费开始使用</a-button>
          <a-button size="large" class="cta-btn-secondary" @click="bookDemo">预约演示</a-button>
        </div>
      </div>
    </section>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  CheckOutlined, CloseOutlined, DownOutlined,
  SearchOutlined, TranslationOutlined, GlobalOutlined,
  FileTextOutlined, MessageOutlined, ShopOutlined,
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/tenants') } catch { /* 空状态 */ }
})

const hoveredFeat = ref(-1)
const openFaq = ref(-1)

function scrollToSection(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function bookDemo() {
  scrollToSection('pricing')
}

const features = [
  {
    icon: SearchOutlined,
    bg: 'linear-gradient(135deg, var(--uj-brand, #4a9b8c) 0%, #2a6b60 100%)',
    title: 'SEO 智能优化',
    desc: 'AI 驱动关键词排名、内容优化与 Schema 标记，全面提升搜索引擎可见度与自然流量。',
    tags: ['关键词排名', '内容优化', 'Schema标记', '站点审计'],
  },
  {
    icon: TranslationOutlined,
    bg: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    title: '多语言全球化',
    desc: '支持 31 种语言的智能翻译与本地化适配，让您的产品信息精准触达全球买家。',
    tags: ['31种语言', '术语库', '文化适配', '自动翻译'],
  },
  {
    icon: GlobalOutlined,
    bg: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    title: '国际询盘采集',
    desc: '智能爬虫从海外 B2B 平台采集客户询盘，NLP 自动提取关键信息并入库管理。',
    tags: ['海外爬虫', 'NLP提取', '自动入库', '多平台'],
  },
  {
    icon: FileTextOutlined,
    bg: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    title: 'AI 内容生成',
    desc: '智能文案撰写、批量内容生产、多平台一键发布，大幅提升内容运营效率。',
    tags: ['智能文案', '批量生成', '多平台发布', '模板库'],
  },
  {
    icon: MessageOutlined,
    bg: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
    title: '客户询盘管理',
    desc: '全链路线索跟踪、状态自动流转、转化数据分析，不遗漏每一个潜在商机。',
    tags: ['线索跟踪', '状态管理', '转化分析', '自动提醒'],
  },
  {
    icon: ShopOutlined,
    bg: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    title: '产品展示官网',
    desc: '多语言响应式官网、产品目录管理、案例展示，打造专业的品牌线上门面。',
    tags: ['多语言官网', '产品目录', '案例展示', '响应式'],
  },
]

const pricingPlans = [
  {
    name: '免费版',
    slogan: '适合个人体验',
    price: '0',
    annualPrice: '0',
    annualSave: '—',
    badge: '',
    highlighted: false,
    features: [
      { label: '1 个站点', included: true },
      { label: '基础 SEO 优化', included: true },
      { label: '5 篇/月 AI 内容生成', included: true },
      { label: '1 种语言', included: true },
      { label: '询盘管理（50条/月）', included: true },
      { label: '多语言翻译', included: false },
      { label: '国际询盘采集', included: false },
      { label: '批量内容生成', included: false },
      { label: '高级数据分析', included: false },
      { label: '白标品牌', included: false },
    ],
  },
  {
    name: '基础版',
    slogan: '适合创业团队',
    price: '299',
    annualPrice: '249',
    annualSave: '600',
    badge: '',
    highlighted: false,
    features: [
      { label: '3 个站点', included: true },
      { label: '高级 SEO 优化', included: true },
      { label: '50 篇/月 AI 内容生成', included: true },
      { label: '5 种语言', included: true },
      { label: '询盘管理（500条/月）', included: true },
      { label: '多语言翻译', included: true },
      { label: '国际询盘采集（1平台）', included: true },
      { label: '批量内容生成', included: false },
      { label: '高级数据分析', included: false },
      { label: '白标品牌', included: false },
    ],
  },
  {
    name: '专业版',
    slogan: '最受欢迎 · 中小企业首选',
    price: '899',
    annualPrice: '749',
    annualSave: '1,800',
    badge: '热销推荐',
    highlighted: true,
    features: [
      { label: '10 个站点', included: true },
      { label: '全功能 SEO 套件', included: true },
      { label: '200 篇/月 AI 内容生成', included: true },
      { label: '15 种语言', included: true },
      { label: '询盘管理（2000条/月）', included: true },
      { label: '多语言翻译', included: true },
      { label: '国际询盘采集（3平台）', included: true },
      { label: '批量内容生成', included: true },
      { label: '高级数据分析', included: true },
      { label: '白标品牌', included: false },
    ],
  },
  {
    name: '企业版',
    slogan: '适合中型企业',
    price: '2,999',
    annualPrice: '2,499',
    annualSave: '6,000',
    badge: '',
    highlighted: false,
    features: [
      { label: '30 个站点', included: true },
      { label: '全功能 SEO 套件 + API', included: true },
      { label: '1,000 篇/月 AI 内容生成', included: true },
      { label: '31 种语言', included: true },
      { label: '询盘管理（无限）', included: true },
      { label: '多语言翻译', included: true },
      { label: '国际询盘采集（全部平台）', included: true },
      { label: '批量内容生成', included: true },
      { label: '高级数据分析 + 看板', included: true },
      { label: '白标品牌', included: true },
    ],
  },
  {
    name: '旗舰版',
    slogan: '集团级定制方案',
    price: '定制',
    annualPrice: '定制',
    annualSave: '—',
    badge: '尊享',
    highlighted: false,
    features: [
      { label: '无限站点', included: true },
      { label: '私有化部署', included: true },
      { label: '无限 AI 内容生成', included: true },
      { label: '31 种语言 + 专业人工翻译', included: true },
      { label: '询盘管理（无限 + API）', included: true },
      { label: '专属客户成功经理', included: true },
      { label: 'SLA 99.99% 保障', included: true },
      { label: '定制开发', included: true },
      { label: '多级权限管理', included: true },
      { label: '专属 AI 模型微调', included: true },
    ],
  },
]

const cases = [
  {
    company: '佛山宏远陶瓷',
    industry: '建筑陶瓷 · 出口型企业',
    abbr: '宏',
    color: 'linear-gradient(135deg, var(--uj-brand, #4a9b8c) 0%, #2a6b60 100%)',
    results: [
      { num: '+340%', label: '询盘增长' },
      { num: '28', label: '覆盖语言' },
      { num: 'Top 3', label: 'Google排名' },
    ],
    quote: '使用优丁 AI SaaS 后，我们的海外询盘量翻了 3 倍多，28 种语言的官网让东南亚和中东客户可以母语浏览，大大降低了沟通门槛。',
  },
  {
    company: '鼎盛钢材集团',
    industry: '钢铁加工 · 跨国贸易',
    abbr: '鼎',
    color: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    results: [
      { num: '+280%', label: '自然流量' },
      { num: '15', label: '高排名关键词' },
      { num: '-60%', label: '获客成本' },
    ],
    quote: 'SEO 智能优化功能让我们的核心关键词全部进入 Google 首页，内容生成加多平台发布节省了 80% 的内容团队人力。',
  },
  {
    company: '北欧卫浴科技',
    industry: '卫浴洁具 · 品牌出海',
    abbr: '北',
    color: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    results: [
      { num: '+460%', label: '有效询盘' },
      { num: '€2.3M', label: '成交额' },
      { num: '12', label: '开拓国家' },
    ],
    quote: '国际询盘采集系统每天自动从多个 B2B 平台抓取精准采购线索，NLP 自动分类后直接推送到我们的 CRM，转化率显著提升。',
  },
  {
    company: '鑫海建材连锁',
    industry: '建材贸易 · 国内分销',
    abbr: '鑫',
    color: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    results: [
      { num: '+190%', label: '官网转化率' },
      { num: '2,400+', label: '产品上线' },
      { num: '85%', label: '客户满意度' },
    ],
    quote: '多语言官网和产品展示系统帮我们快速搭建了面向不同市场的线上展厅，客户可以自助浏览产品目录和下载资料，大大减少了销售团队的基础咨询工作量。',
  },
]

const faqs = [
  { q: '优丁 AI SaaS 支持哪些第三方平台集成？', a: '我们支持主流 B2B 平台（阿里巴巴国际站、中国制造网、GlobalSources 等）、社交媒体（LinkedIn、Facebook、Instagram）、搜索引擎（Google、Bing、Yandex）以及 CRM 系统（Salesforce、HubSpot、纷享销客等）。API 接口开放，支持自定义集成开发。' },
  { q: '多语言翻译的准确性如何？', a: '我们采用 AI + 专业术语库双引擎翻译机制。AI 完成初稿翻译，结合建材行业专业术语库进行优化，企业版及以上客户还可配置专属术语表。对于旗舰版客户，我们提供专业人工译审服务，确保翻译质量达到出版级标准。' },
  { q: 'SEO 优化的效果多久能看到？', a: '一般情况下，基础优化（标题、描述、Schema 标记）在 2-4 周内可以看到排名变化；内容策略优化需要 1-3 个月见效；长期的链接建设和品牌词积累需要 3-6 个月。我们的系统提供实时排名监控和月度效果报告，让您清晰看到每一步的投入产出。' },
  { q: '是否支持私有化部署？', a: '旗舰版支持完全私有化部署，包括本地服务器或专属云环境。系统架构支持高可用集群部署，数据完全由客户掌控。企业版及以上客户可选择 SaaS 专属实例（独享资源池），数据隔离级别达到金融级标准。' },
  { q: '如何保障数据安全？', a: '我们采用银行级数据加密传输（TLS 1.3）和存储（AES-256），所有数据按租户严格隔离。系统通过 ISO 27001 信息安全认证，定期进行渗透测试和安全审计。企业版及以上客户可选择数据存储地域，旗舰版支持私有化部署。' },
  { q: '是否支持多用户协作？', a: '所有付费版本均支持多用户协作，但权限管理粒度不同。基础版支持管理员和编辑两种角色；专业版支持自定义角色权限；企业版及以上支持多级审批流、部门隔离和操作审计日志。' },
  { q: '可以免费试用吗？需要绑定信用卡吗？', a: '我们提供 14 天全功能免费试用，无需绑定信用卡。试用期间享有专业版所有功能，到期后可选择购买任意套餐或自动降级为免费版（数据保留）。我们建议您在试用期间联系客户成功经理，以获得最佳体验。' },
  { q: '套餐可以随时升级或降级吗？', a: '是的，您可以随时升级套餐，升级后新功能立即生效，差价按剩余天数折算。降级操作将在当前计费周期结束后生效，数据不会丢失，但超出新套餐限制的功能将被暂停使用，直到您再次升级。' },
]
</script>

<style scoped>
/* ===== 全局 ===== */
.showcase-page {
  max-width: 1280px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.section-header {
  text-align: center;
  margin-bottom: 3rem;
}
.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.section-desc {
  font-size: 1rem;
  color: #64748b;
  margin-top: 0.5rem;
}

/* ===== HERO ===== */
.hero-section {
  position: relative;
  text-align: center;
  padding: 5rem 2rem 4rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  border-radius: 24px;
  overflow: hidden;
  margin-bottom: 4rem;
}
.hero-bg-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(59,130,246,0.1) 1px, transparent 1px);
  background-size: 30px 30px;
  opacity: 0.5;
}
.hero-content {
  position: relative;
  z-index: 1;
}
.hero-badge {
  display: inline-block;
  padding: 0.35rem 1rem;
  border-radius: 20px;
  background: rgba(59,130,246,0.15);
  border: 1px solid rgba(59,130,246,0.3);
  color: #93c5fd;
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}
.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.03em;
  line-height: 1.1;
}
.hero-subtitle {
  font-size: 1.1rem;
  color: #94a3b8;
  max-width: 560px;
  margin: 1rem auto 2rem;
  line-height: 1.6;
}
.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}
.hero-btn-primary {
  height: 48px;
  padding: 0 2rem;
  font-size: 1rem;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), var(--uj-brand, #4a9b8c));
  border: none;
  box-shadow: 0 4px 14px rgba(59,130,246,0.35);
}
.hero-btn-primary:hover {
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60);
  box-shadow: 0 6px 20px rgba(59,130,246,0.45);
}
.hero-btn-ghost {
  height: 48px;
  padding: 0 2rem;
  font-size: 1rem;
  border-radius: 12px;
  border-color: rgba(255,255,255,0.2);
  color: #e2e8f0;
}
.hero-btn-ghost:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: #93c5fd;
}
.hero-stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.hero-stat-num {
  font-size: 1.8rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
}
.hero-stat-label {
  font-size: 0.78rem;
  color: #64748b;
  margin-top: 0.2rem;
}

/* ===== FEATURES ===== */
.features-section {
  padding: 2rem 0 4rem;
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
.feature-card {
  background: white;
  border-radius: 16px;
  padding: 1.75rem;
  border: 1px solid #f1f5f9;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  cursor: default;
}
.feature-card:hover,
.feature-card.active {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.08);
  border-color: #e2e8f0;
}
.feat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}
.feat-icon {
  font-size: 1.4rem;
  color: white;
}
.feat-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.5rem;
}
.feat-desc {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}
.feat-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 1rem;
}
.feat-tag {
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.7rem;
  font-weight: 500;
}
.feat-preview {
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  overflow: hidden;
}
.feat-preview-bar {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  background: #f1f5f9;
}
.feat-preview-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
}
.feat-preview-body {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.feat-preview-line {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

/* ===== PRICING ===== */
.pricing-section {
  padding: 4rem 0;
}
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}
.pricing-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem 1.25rem;
  border: 1px solid #f1f5f9;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex;
  flex-direction: column;
}
.pricing-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.08);
}
.pricing-card.highlighted {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: 0 8px 24px rgba(59,130,246,0.15);
  transform: scale(1.04);
  z-index: 1;
}
.pricing-card.highlighted:hover {
  transform: scale(1.04) translateY(-3px);
}
.pricing-badge {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.2rem 0.8rem;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), var(--uj-brand, #4a9b8c));
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}
.pricing-header {
  text-align: center;
  margin-bottom: 1rem;
}
.pricing-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}
.pricing-slogan {
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 0.2rem;
}
.pricing-amount {
  text-align: center;
  margin-bottom: 0.5rem;
}
.pricing-currency {
  font-size: 0.9rem;
  color: #64748b;
  vertical-align: top;
}
.pricing-price {
  font-size: 2rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.pricing-unit {
  font-size: 0.8rem;
  color: #94a3b8;
}
.pricing-annual {
  text-align: center;
  font-size: 0.68rem;
  color: #10b981;
  margin-bottom: 1rem;
  font-weight: 500;
}
.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  flex: 1;
}
.pricing-feat-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0;
  font-size: 0.78rem;
  color: #475569;
}
.pricing-feat-icon {
  font-size: 0.7rem;
  color: #10b981;
  flex-shrink: 0;
}
.pricing-feat-icon.excluded {
  color: #cbd5e1;
}
.pricing-btn {
  border-radius: 10px;
  height: 42px;
  font-size: 0.9rem;
}

/* ===== CASES ===== */
.cases-section {
  padding: 4rem 0;
}
.cases-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}
.case-card {
  display: flex;
  gap: 1.25rem;
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #f1f5f9;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.case-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  border-color: #e2e8f0;
}
.case-avatar-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.case-avatar-text {
  font-size: 1.2rem;
  font-weight: 700;
  color: white;
}
.case-body {
  flex: 1;
  min-width: 0;
}
.case-company {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}
.case-industry {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.75rem;
}
.case-results {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.75rem;
}
.case-result {
  display: flex;
  flex-direction: column;
}
.case-result-num {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--uj-brand, #4a9b8c);
}
.case-result-label {
  font-size: 0.65rem;
  color: #94a3b8;
}
.case-quote {
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.6;
  font-style: italic;
  border-left: 2px solid #e2e8f0;
  padding-left: 0.75rem;
}

/* ===== FAQ ===== */
.faq-section {
  padding: 4rem 0;
}
.faq-list {
  max-width: 720px;
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
  font-size: 0.95rem;
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
  font-size: 0.88rem;
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

/* ===== CTA ===== */
.cta-section {
  padding: 3rem 0 4rem;
}
.cta-card {
  text-align: center;
  padding: 4rem 2rem;
  border-radius: 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}
.cta-title {
  font-size: 2rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
}
.cta-desc {
  font-size: 1rem;
  color: #94a3b8;
  max-width: 480px;
  margin: 0.75rem auto 2rem;
  line-height: 1.6;
}
.cta-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}
.cta-btn {
  height: 48px;
  padding: 0 2rem;
  font-size: 1rem;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), var(--uj-brand, #4a9b8c));
  border: none;
  box-shadow: 0 4px 14px rgba(59,130,246,0.35);
}
.cta-btn:hover {
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60);
  box-shadow: 0 6px 20px rgba(59,130,246,0.45);
}
.cta-btn-secondary {
  height: 48px;
  padding: 0 2rem;
  font-size: 1rem;
  border-radius: 12px;
  border-color: rgba(255,255,255,0.2);
  color: #e2e8f0;
}
.cta-btn-secondary:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: #93c5fd;
}

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .pricing-grid { grid-template-columns: repeat(3, 1fr); }
  .pricing-card.highlighted { transform: scale(1.02); }
}
@media (max-width: 768px) {
  .hero-title { font-size: 2.2rem; }
  .hero-subtitle { font-size: 0.95rem; }
  .hero-stats { gap: 1.5rem; }
  .hero-stat-num { font-size: 1.3rem; }
  .features-grid { grid-template-columns: 1fr; }
  .pricing-grid { grid-template-columns: 1fr; max-width: 400px; margin: 0 auto; }
  .pricing-card.highlighted { transform: none; }
  .pricing-card.highlighted:hover { transform: translateY(-3px); }
  .cases-grid { grid-template-columns: 1fr; }
  .section-title { font-size: 1.5rem; }
}
@media (max-width: 480px) {
  .hero-section { padding: 3rem 1rem 2.5rem; border-radius: 16px; }
  .hero-title { font-size: 1.8rem; }
  .hero-actions { flex-direction: column; align-items: center; }
  .cta-card { padding: 2.5rem 1rem; border-radius: 16px; }
  .cta-title { font-size: 1.4rem; }
}
</style>
