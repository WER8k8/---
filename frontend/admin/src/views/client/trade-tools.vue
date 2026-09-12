<template>
  <YdPage
    title="外贸工具指南"
    :subtitle="pageSubtitle"
    surface="elevated"
  >
    <div class="trade-tools-page">
      <!-- 搜索框 -->
      <div class="search-section">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索工具名称或功能..."
          style="width: 320px"
          allow-clear
          @search="onSearch"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input-search>
        <span class="result-count" v-if="searchKeyword">
          找到 {{ filteredTools.length }} 个相关工具
        </span>
      </div>

      <!-- 分类标签 -->
      <div class="category-tabs">
        <a-radio-group v-model:value="activeCategory" button-style="solid" size="large">
          <a-radio-button value="all">全部工具</a-radio-button>
          <a-radio-button value="communication">客户沟通</a-radio-button>
          <a-radio-button value="market">市场分析</a-radio-button>
          <a-radio-button value="data">数据挖掘</a-radio-button>
          <a-radio-button value="crm">CRM与销售</a-radio-button>
          <a-radio-button value="social">社媒营销</a-radio-button>
          <a-radio-button value="logistics">物流追踪</a-radio-button>
          <a-radio-button value="learning">学习资源</a-radio-button>
        </a-radio-group>
      </div>

      <!-- 工具卡片网格 -->
      <div class="tools-grid">
        <div
          v-for="tool in filteredTools"
          :key="tool.id"
          class="tool-card"
          :class="`tool-card--${tool.category}`"
        >
          <div class="tool-header">
            <div class="tool-icon">
              <component :is="tool.icon" />
            </div>
            <div class="tool-badges">
              <div class="tool-badge" :class="`badge--${tool.tier}`">
                {{ tool.tierLabel }}
              </div>
              <div class="tool-price" v-if="tool.price">
                {{ tool.price }}
              </div>
            </div>
          </div>

          <h3 class="tool-name">{{ tool.name }}</h3>
          <p class="tool-core">{{ tool.coreRole }}</p>

          <!-- 使用状态标记 -->
          <div class="tool-status" v-if="tool.usageStatus">
            <a-tag :color="getStatusColor(tool.usageStatus)">
              {{ getStatusLabel(tool.usageStatus) }}
            </a-tag>
          </div>

          <div class="tool-stats" v-if="tool.stats">
            <div class="stat-item" v-for="(stat, key) in tool.stats" :key="key">
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </div>
          </div>

          <div class="tool-section">
            <h4 class="section-title">实战用法</h4>
            <ul class="usage-list">
              <li v-for="(usage, idx) in tool.usageList" :key="idx">{{ usage }}</li>
            </ul>
          </div>

          <div class="tool-actions">
            <a-button type="primary" @click="openToolGuide(tool)">
              <BookOutlined /> 使用指南
            </a-button>
            <a-tooltip :title="isFavorited(tool.id) ? '取消收藏' : '收藏工具'">
              <a-button @click="toggleFavorite(tool.id)">
                <StarFilled v-if="isFavorited(tool.id)" style="color: #faad14" />
                <StarOutlined v-else />
              </a-button>
            </a-tooltip>
            <a-tooltip :title="compareList.includes(tool.id) ? '已添加' : '添加到对比'">
              <a-button :disabled="compareList.length >= 4 && !compareList.includes(tool.id)" @click="addToCompare(tool.id)">
                <DiffOutlined /> 对比
              </a-button>
            </a-tooltip>
            <a-button v-if="tool.externalUrl" @click="openExternal(tool.externalUrl)">
              <ExportOutlined /> 官网
            </a-button>
          </div>
        </div>
      </div>

      <!-- 使用指南弹窗 -->
      <a-modal
        v-model:open="guideVisible"
        :title="`${currentTool?.name} - 使用指南`"
        width="720px"
        :footer="null"
      >
        <div v-if="currentTool" class="guide-content">
          <a-alert type="info" show-icon class="mb-4">
            <template #message>
              <strong>核心价值：</strong>{{ currentTool.coreRole }}
            </template>
          </a-alert>

          <div class="guide-meta">
            <a-tag :color="getCategoryColor(currentTool.category)">
              {{ getCategoryLabel(currentTool.category) }}
            </a-tag>
            <a-tag :class="`badge--${currentTool.tier}`">
              {{ currentTool.tierLabel }}
            </a-tag>
            <a-tag color="orange" v-if="currentTool.price">
              💰 {{ currentTool.price }}
            </a-tag>
          </div>

          <h4>一、工具定位</h4>
          <p>{{ currentTool.coreRole }}</p>

          <h4>二、实战应用场景</h4>
          <ol>
            <li v-for="(usage, idx) in currentTool.usageList" :key="idx">{{ usage }}</li>
          </ol>

          <h4 v-if="currentTool.bestPractices">三、最佳实践建议</h4>
          <ul v-if="currentTool.bestPractices">
            <li v-for="(bp, idx) in currentTool.bestPractices" :key="idx">{{ bp }}</li>
          </ul>

          <h4 v-if="currentTool.tips">四、使用技巧</h4>
          <ul v-if="currentTool.tips">
            <li v-for="(tip, idx) in currentTool.tips" :key="idx">{{ tip }}</li>
          </ul>

          <div class="guide-footer">
            <a-space>
              <a-button v-if="currentTool.externalUrl" type="primary" @click="openExternal(currentTool.externalUrl)">
                立即访问 {{ currentTool.name }}
              </a-button>
              <a-button v-if="currentTool.relatedTools?.length" @click="openRelatedTools">
                查看相关工具 ({{ currentTool.relatedTools.length }})
              </a-button>
            </a-space>
          </div>
        </div>
      </a-modal>

      <!-- 工具对比功能 -->
      <div class="compare-section" v-if="compareList.length > 0">
        <div class="compare-header">
          <span class="compare-title">工具对比 ({{ compareList.length }}/4)</span>
          <a-space>
            <a-button size="small" @click="clearCompare">清空</a-button>
            <a-button type="primary" size="small" @click="showCompareModal = true">
              开始对比
            </a-button>
          </a-space>
        </div>
        <div class="compare-items">
          <div
            v-for="toolId in compareList"
            :key="toolId"
            class="compare-item"
            @click="removeFromCompare(toolId)"
          >
            <span>{{ getToolById(toolId)?.name }}</span>
            <CloseOutlined />
          </div>
        </div>
      </div>

      <!-- 工具对比弹窗 -->
      <a-modal
        v-model:open="showCompareModal"
        title="工具对比"
        width="900px"
        :footer="null"
      >
        <div class="compare-table-wrapper">
          <table class="compare-table">
            <thead>
              <tr>
                <th>对比项</th>
                <th v-for="toolId in compareList" :key="toolId">
                  {{ getToolById(toolId)?.name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>类型</td>
                <td v-for="toolId in compareList" :key="toolId">
                  {{ getToolById(toolId)?.tierLabel }}
                </td>
              </tr>
              <tr>
                <td>价格</td>
                <td v-for="toolId in compareList" :key="toolId">
                  {{ getToolById(toolId)?.price || '免费' }}
                </td>
              </tr>
              <tr>
                <td>分类</td>
                <td v-for="toolId in compareList" :key="toolId">
                  {{ getCategoryLabel(getToolById(toolId)?.category) }}
                </td>
              </tr>
              <tr>
                <td>核心功能</td>
                <td v-for="toolId in compareList" :key="toolId" class="cell-left">
                  {{ getToolById(toolId)?.coreRole }}
                </td>
              </tr>
              <tr>
                <td>适用场景</td>
                <td v-for="toolId in compareList" :key="toolId" class="cell-left">
                  <ul class="compare-usage">
                    <li v-for="(usage, idx) in getToolById(toolId)?.usageList?.slice(0, 3)" :key="idx">
                      {{ usage }}
                    </li>
                  </ul>
                </td>
              </tr>
              <tr v-if="hasStats(compareList)">
                <td>数据规模</td>
                <td v-for="toolId in compareList" :key="toolId">
                  <template v-if="getToolById(toolId)?.stats">
                    <div v-for="(stat, key) in getToolById(toolId)?.stats" :key="key">
                      {{ stat.value }} {{ stat.label }}
                    </div>
                  </template>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr>
                <td>操作</td>
                <td v-for="toolId in compareList" :key="toolId">
                  <a-button
                    type="link"
                    v-if="getToolById(toolId)?.externalUrl"
                    @click="openExternal(getToolById(toolId)?.externalUrl || '')"
                  >
                    访问官网
                  </a-button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </a-modal>

      <!-- 关联推荐弹窗 -->
      <a-modal
        v-model:open="showRelatedModal"
        title="相关工具推荐"
        width="600px"
        :footer="null"
      >
        <div class="related-tools" v-if="relatedTools.length > 0">
          <div
            v-for="tool in relatedTools"
            :key="tool.id"
            class="related-tool-card"
          >
            <div class="related-tool-header">
              <component :is="tool.icon" style="font-size: 24px; color: #1890ff" />
              <span class="related-tool-name">{{ tool.name }}</span>
              <a-tag :color="getCategoryColor(tool.category)">
                {{ getCategoryLabel(tool.category) }}
              </a-tag>
            </div>
            <p class="related-tool-desc">{{ tool.coreRole }}</p>
            <div class="related-tool-tags">
              <span v-for="(tag, idx) in tool.usageList?.slice(0, 2)" :key="idx" class="related-tag">
                {{ tag }}
              </span>
            </div>
            <a-button type="link" @click="openToolGuide(tool)">查看详情</a-button>
          </div>
        </div>
        <a-empty v-else description="暂无相关推荐" />
      </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { YdPage } from '@/components/youding';
import { apiGet } from '@/utils/api';
import {
  BookOutlined,
  DiffOutlined,
  ExportOutlined,
  MessageOutlined,
  LineChartOutlined,
  DatabaseOutlined,
  TeamOutlined,
  FileTextOutlined,
  SearchOutlined,
  StarOutlined,
  StarFilled,
  GlobalOutlined,
  ShoppingOutlined,
  RocketOutlined,
  CloseOutlined,
  EnvironmentOutlined,
  CrownOutlined,
  ToolOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';

// ============================================================================
// 租户上下文（套餐决定推荐侧重）
// ============================================================================
const tenantPlanName = ref('');

const pageSubtitle = computed(() => {
  const base = '客户开发 · 市场分析 · 数据挖掘 · 实战英语';
  return tenantPlanName.value ? `${base} · 当前套餐：${tenantPlanName.value}` : base;
});

async function loadTenantContext() {
  try {
    const current = await apiGet<{ plan_name?: string; name?: string }>('/tenants/current');
    tenantPlanName.value = String(current?.plan_name || current?.name || '').trim();
  } catch {
    tenantPlanName.value = '';
  }
}

// ============================================================================
// 工具数据
// ============================================================================
interface TradeTool {
  id: string;
  name: string;
  category: string;
  tier: string;
  tierLabel: string;
  icon: any;
  coreRole: string;
  usageList: string[];
  stats?: Record<string, { value: string; label: string }>;
  bestPractices?: string[];
  tips?: string[];
  externalUrl?: string;
  price?: string;
  usageStatus?: 'unfamiliar' | 'learning' | 'proficient';
  relatedTools?: string[];
}

const TOOLS: TradeTool[] = [
  // 客户沟通类
  {
    id: 'whatsapp',
    name: 'WhatsApp',
    category: 'communication',
    tier: 'core',
    tierLabel: '核心工具',
    icon: MessageOutlined,
    coreRole: '海外客户即时沟通的主流工具，消息打开率高达98%，远高于邮件，适合快速确认订单细节、发送报价单、售后跟进等场景。',
    usageList: [
      '产品展示：发送产品图片、视频，直观展示产品细节',
      '文件传输：发送报价单、合同、发票等PDF文件',
      '客户分组运营：按地区、产品类型分组，精准推送信息',
      '私域成交：建立长期客户关系，提升复购率',
    ],
    stats: {
      openRate: { value: '98%', label: '消息打开率' },
      users: { value: '20亿+', label: '全球用户' },
    },
    bestPractices: [
      '保持专业形象：使用企业头像和规范签名',
      '及时响应：争取在24小时内回复客户消息',
      '善用标签功能：为客户添加标签，便于后续跟进',
    ],
    tips: [
      '可创建群组进行多人沟通',
      '支持语音通话和视频通话',
      '注意各国时差，避免非工作时间打扰',
    ],
    externalUrl: 'https://www.whatsapp.com',
    price: '免费',
    relatedTools: ['linkedin', 'email'],
  },
  {
    id: 'email',
    name: '企业邮箱',
    category: 'communication',
    tier: 'core',
    tierLabel: '核心工具',
    icon: FileTextOutlined,
    coreRole: '外贸商务沟通的正式渠道，用于发送正式报价单、合同、发票等重要文件，是建立专业形象和留存记录的关键工具。',
    usageList: [
      '正式报价：发送带附件的正式报价单',
      '合同往来：发送和签署正式合同',
      '邮件营销：定期发送产品更新和促销信息',
      '客户管理：记录完整沟通历史',
    ],
    stats: {
      deliverability: { value: '95%+', label: '送达率' },
      archive: { value: '永久', label: '存档记录' },
    },
    bestPractices: [
      '使用企业域名邮箱，提升专业度',
      '规范邮件签名，包含联系方式',
      '设置邮件模板，提高效率',
    ],
    tips: [
      '跟进邮件应在48小时内发送',
      '重要邮件使用回执功能',
      '善用邮件分类和标签管理',
    ],
    price: '¥200-2000/年',
    relatedTools: ['whatsapp', 'linkedin'],
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    category: 'communication',
    tier: 'pro',
    tierLabel: '专业社交',
    icon: TeamOutlined,
    coreRole: '全球最大的职业社交平台，是开发B2B客户、建立专业人脉、进行内容营销的重要渠道，尤其适合开发欧美客户。',
    usageList: [
      '客户开发：通过搜索找到目标客户的采购负责人',
      '人脉拓展：加入行业群组，参与讨论',
      '内容营销：发布专业内容，建立行业影响力',
      '品牌建设：优化公司主页，展示企业实力',
    ],
    stats: {
      users: { value: '9亿+', label: '全球用户' },
      decisionMakers: { value: '65%', label: '决策层用户' },
    },
    bestPractices: [
      '完善个人档案，突出专业背景',
      '定期发布行业相关内容',
      '主动添加潜在客户并个性化消息',
    ],
    tips: [
      'Sales Navigator可精准定位目标客户',
      'InMail可触达非联系人决策层',
      '关注竞争对手动态，分析市场策略',
    ],
    externalUrl: 'https://www.linkedin.com',
    price: '¥800-2400/月（Sales Navigator）',
    relatedTools: ['whatsapp', 'zoominfo'],
  },
  // 市场分析类
  {
    id: 'google-trends',
    name: 'Google Trends',
    category: 'market',
    tier: 'free',
    tierLabel: '免费工具',
    icon: LineChartOutlined,
    coreRole: '谷歌官方免费工具，通过全球搜索数据，分析关键词在不同地区、不同时间段的热度变化，帮助判断市场需求、产品淡旺季、区域市场潜力。',
    usageList: [
      '输入产品关键词，查看全球各国家/地区的搜索热度排名',
      '对比多个产品的市场趋势，选择热门产品方向',
      '分析搜索热度的时间变化，判断产品淡旺季',
      '锁定高潜力目标市场，精准投放资源',
    ],
    bestPractices: [
      '选择合适的时间范围：短期看趋势变化，长期看市场稳定性',
      '对比相关关键词：发现更多市场需求',
      '关注季节性波动：提前备货或调整营销策略',
    ],
    tips: [
      '可下载CSV数据进行深度分析',
      '支持设置地区筛选，聚焦目标市场',
      '结合Google Ads数据制定投放策略',
    ],
    externalUrl: 'https://trends.google.com',
    price: '免费',
    relatedTools: ['semrush', 'ahrefs'],
  },
  {
    id: 'semrush',
    name: 'SEMrush',
    category: 'market',
    tier: 'enterprise',
    tierLabel: '企业级',
    icon: GlobalOutlined,
    coreRole: '全球领先的SEO和竞争情报平台，提供关键词研究、竞争对手分析、网站审计、反向链接分析等功能，帮助提升网站搜索排名和流量。',
    usageList: [
      '关键词研究：发现高搜索量、低竞争度的关键词',
      '竞争对手分析：了解竞争对手的SEO策略和流量来源',
      '网站审计：发现技术SEO问题并提供修复建议',
      '内容营销：优化内容以提升搜索排名',
    ],
    stats: {
      keywords: { value: '200亿+', label: '关键词数据库' },
      domains: { value: '8000万+', label: '分析域名' },
    },
    bestPractices: [
      '定期监控关键词排名变化',
      '分析竞争对手的内容策略',
      '利用反向链接分析发现外链机会',
    ],
    tips: [
      'Traffic Analytics可估算竞争对手流量',
      'Organic Research发现竞争对手排名关键词',
      'Market Explorer分析行业整体趋势',
    ],
    externalUrl: 'https://www.semrush.com',
    price: '$119.95-449.95/月',
    relatedTools: ['ahrefs', 'google-trends'],
  },
  {
    id: 'ahrefs',
    name: 'Ahrefs',
    category: 'market',
    tier: 'enterprise',
    tierLabel: '企业级',
    icon: ThunderboltOutlined,
    coreRole: '专业的SEO工具套件，以反向链接分析著称，同时提供关键词研究、内容分析、站点审计等功能，适合外贸网站SEO优化。',
    usageList: [
      '反向链接分析：发现高质量外链机会',
      '关键词探索：发现长尾关键词机会',
      '竞争对手外链：复制竞争对手成功的外链策略',
      '站点审计：发现技术SEO问题',
    ],
    stats: {
      backlinks: { value: '16万亿+', label: '反向链接' },
      keywords: { value: '70亿+', label: '关键词' },
    },
    bestPractices: [
      '利用Content Explorer发现热门内容话题',
      '定期检查外链变化，防止外链丢失',
      '对比多个竞争对手的外链策略',
    ],
    tips: [
      'Link Intersect发现竞争对手有而你没有的外链',
      'Alert功能监控外链变化',
      'Batch Analysis批量分析多个域名',
    ],
    externalUrl: 'https://www.ahrefs.com',
    price: '$99-999/月',
    relatedTools: ['semrush', 'google-trends'],
  },
  // 数据挖掘类
  {
    id: 'panjiva',
    name: 'Panjiva',
    category: 'data',
    tier: 'pro',
    tierLabel: '专业数据',
    icon: DatabaseOutlined,
    coreRole: '全球供应链情报平台，覆盖22个国家、900万+企业的20亿+条贸易记录，可查询真实的提单数据、进出口记录、供应商/采购商信息、物流动态。',
    usageList: [
      '跟踪客户采购轨迹：了解客户的历史采购记录和偏好',
      '分析供应链关系：发现客户的供应商分布和替代选择',
      '挖掘潜在供应商/采购商：发现新的合作机会',
      '提升拓客精准度：基于真实贸易数据定向开发客户',
    ],
    stats: {
      countries: { value: '22', label: '覆盖国家' },
      companies: { value: '900万+', label: '企业数量' },
      records: { value: '20亿+', label: '贸易记录' },
    },
    bestPractices: [
      '定期监控目标客户的采购动态',
      '分析竞争对手的供应链策略',
      '结合海关数据验证客户真实性',
    ],
    externalUrl: 'https://www.panjiva.com',
    price: '联系定价（企业定制）',
    relatedTools: ['importgenius', 'cnab'],
  },
  {
    id: 'importgenius',
    name: 'ImportGenius',
    category: 'data',
    tier: 'pro',
    tierLabel: '专业数据',
    icon: DatabaseOutlined,
    coreRole: '覆盖美国、印度、俄罗斯等21+国家的海关提单数据，可查询企业的进出口明细、采购价格、供应商信息、港口运输记录，被业内称为"海关数据核武器"。',
    usageList: [
      '精准定位目标客户的采购来源',
      '分析竞争对手的供应链',
      '挖掘新的采购商线索',
      '查询采购价格，掌握市场行情',
    ],
    stats: {
      countries: { value: '21+', label: '覆盖国家' },
      dataDepth: { value: '深度', label: '数据深度' },
    },
    bestPractices: [
      '重点关注美国市场数据（数据最全面）',
      '追踪高频采购客户，优先开发',
      '分析采购周期，把握最佳触达时机',
    ],
    externalUrl: 'https://www.importgenius.com',
    price: '联系定价（企业定制）',
    relatedTools: ['panjiva', 'cnab'],
  },
  {
    id: 'cnab',
    name: '海关数据（国内平台）',
    category: 'data',
    tier: 'pro',
    tierLabel: '专业数据',
    icon: ShoppingOutlined,
    coreRole: '国内海关数据服务商，提供中国进出口贸易数据，支持按产品、企业 HS 编码等维度查询，是开发国内外贸客户的重要数据来源。',
    usageList: [
      '查询同行出口记录，分析竞争对手',
      '发现采购我司产品的海外采购商',
      '分析产品进出口趋势，把握市场机会',
      '验证潜在客户规模和真实性',
    ],
    stats: {
      dataSource: { value: '中国海关', label: '数据来源' },
      coverage: { value: '100%', label: '覆盖率' },
    },
    bestPractices: [
      '按产品HS编码精确查询',
      '定期更新目标客户采购动态',
      '结合Panjiva数据交叉验证',
    ],
    tips: [
      '国内平台数据更新更快',
      '可查询提单详细货物描述',
      '支持企业进出口信用查询',
    ],
    price: '¥5000-30000/年',
    relatedTools: ['panjiva', 'importgenius'],
  },
  {
    id: 'zoominfo',
    name: 'ZoomInfo',
    category: 'data',
    tier: 'enterprise',
    tierLabel: '企业级',
    icon: CrownOutlined,
    coreRole: '企业级客户数据平台，可查询海外公司的组织架构、决策人联系方式、采购意图信号，支持按行业、规模、地域筛选潜在客户。',
    usageList: [
      '绕过基层对接人，直接触达采购决策层',
      '按行业、规模、地域筛选潜在客户',
      '获取决策人邮箱、电话等直接联系方式',
      '识别采购意图信号，精准时机触达',
    ],
    stats: {
      companies: { value: '百万级', label: '企业数据库' },
      contacts: { value: '千万级', label: '联系人' },
    },
    bestPractices: [
      '优先开发有采购意图信号的企业',
      '结合LinkedIn验证联系人信息',
      '制定分层触达策略：高管→中层→执行',
    ],
    tips: [
      '适合大客户销售场景',
      '可导出数据用于CRM管理',
      '定期更新联系人信息',
    ],
    externalUrl: 'https://www.zoominfo.com',
    price: '联系定价（企业定制）',
    relatedTools: ['linkedin', 'hunter'],
  },
  // CRM与销售
  {
    id: 'hubspot',
    name: 'HubSpot CRM',
    category: 'crm',
    tier: 'pro',
    tierLabel: 'CRM工具',
    icon: ToolOutlined,
    coreRole: '免费开源的CRM系统，提供营销自动化、销售管道、客户服务等功能，帮助外贸企业高效管理客户关系和跟进流程。',
    usageList: [
      '客户信息管理：集中存储客户资料和沟通记录',
      '销售管道：可视化跟进销售进度',
      '邮件自动化：定时发送跟进邮件',
      '数据分析：生成销售报表和分析',
    ],
    stats: {
      freeContacts: { value: '100万', label: '免费联系人' },
      users: { value: '15万+', label: '企业用户' },
    },
    bestPractices: [
      '规范录入客户信息，保持数据完整',
      '设置自动化工作流，提升效率',
      '定期清理无效线索',
    ],
    tips: [
      '免费版已包含核心CRM功能',
      '配合Marketing Hub实现营销自动化',
      '支持与WhatsApp等工具集成',
    ],
    externalUrl: 'https://www.hubspot.com',
    price: '免费基础版 / Pro版$800+/月',
    relatedTools: ['whatsapp', 'email'],
  },
  {
    id: 'pipedrive',
    name: 'Pipedrive',
    category: 'crm',
    tier: 'pro',
    tierLabel: 'CRM工具',
    icon: RocketOutlined,
    coreRole: '以销售管道管理见长的CRM工具，界面直观、操作简单，适合外贸团队快速上手，提升销售效率和转化率。',
    usageList: [
      '可视化销售管道：直观管理每个商机',
      '自动化任务：自动创建跟进任务提醒',
      '邮件集成：追踪邮件打开和点击',
      'AI销售助手：提供智能建议和预测',
    ],
    stats: {
      companies: { value: '10万+', label: '使用企业' },
      deals: { value: '600万+', label: '管理交易' },
    },
    bestPractices: [
      '保持管道阶段定义清晰',
      '设置关键里程碑提醒',
      '利用AI建议优先处理高价值商机',
    ],
    tips: [
      '移动端体验优秀',
      '与Google Workspace深度集成',
      '支持定制化字段和视图',
    ],
    externalUrl: 'https://www.pipedrive.com',
    price: '$15-49/用户/月',
    relatedTools: ['hubspot', 'hunter'],
  },
  // 社媒营销类
  {
    id: 'facebook-business',
    name: 'Facebook Business',
    category: 'social',
    tier: 'free',
    tierLabel: '社交营销',
    icon: GlobalOutlined,
    coreRole: '全球最大的社交媒体营销平台，支持创建商业主页、投放广告、管理客户互动，是开发欧美消费者市场和B2B客户的重要渠道。',
    usageList: [
      '商业主页：展示产品和企业信息',
      '广告投放：精准投放吸引潜在客户',
      '客户互动：回复评论和私信',
      '数据分析：分析帖文表现和受众',
    ],
    stats: {
      users: { value: '29亿+', label: '月活用户' },
      advertisers: { value: '1000万+', label: '广告主' },
    },
    bestPractices: [
      '定期发布高质量内容',
      '利用Facebook Pixel追踪转化',
      'A/B测试广告创意',
    ],
    tips: [
      'Instagram与Facebook广告后台互通',
      '利用Lookalike Audience发现相似客户',
      ' Messenger用于客服和转化',
    ],
    externalUrl: 'https://www.facebook.com/business',
    price: '免费（广告费另计）',
    relatedTools: ['instagram', 'tiktok'],
  },
  {
    id: 'instagram',
    name: 'Instagram',
    category: 'social',
    tier: 'free',
    tierLabel: '社交营销',
    icon: RocketOutlined,
    coreRole: '以图片和短视频为主的社交平台，适合B2C品牌建设和产品展示，通过视觉内容吸引年轻消费群体，尤其适合消费品外贸。',
    usageList: [
      '产品展示：通过高质量图片展示产品',
      'Stories：发布日常内容，增加互动',
      'Reels：发布短视频，扩大曝光',
      '购物功能：直接链接产品购买',
    ],
    stats: {
      users: { value: '20亿+', label: '月活用户' },
      engagement: { value: '3.5%', label: '平均互动率' },
    },
    bestPractices: [
      '保持视觉风格统一',
      '利用标签增加发现',
      '与KOL合作推广',
    ],
    tips: [
      'Reels是当前增长最快的流量来源',
      '定期举办互动活动',
      '善用Highlights展示精选内容',
    ],
    externalUrl: 'https://www.instagram.com',
    price: '免费（合作费用另计）',
    relatedTools: ['facebook-business', 'tiktok'],
  },
  {
    id: 'tiktok',
    name: 'TikTok Business',
    category: 'social',
    tier: 'free',
    tierLabel: '短视频营销',
    icon: RocketOutlined,
    coreRole: '全球增长最快的短视频社交平台，是开发Z世代和千禧一代消费者的重要渠道，支持跨境电商推广和品牌曝光。',
    usageList: [
      '短视频营销：发布产品视频吸引关注',
      'TikTok Ads：投放信息流广告',
      '红人营销：与平台达人合作',
      '直播带货：进行实时产品展示和销售',
    ],
    stats: {
      users: { value: '15亿+', label: '月活用户' },
      watchTime: { value: '90分钟+', label: '日均使用' },
    },
    bestPractices: [
      '内容要原生、有趣、符合平台调性',
      '把握热点话题和音乐',
      '保持发布频率，建立粉丝粘性',
    ],
    tips: [
      'TikTok Shop适合电商转化',
      '利用TikTok Creative Center发现热门内容',
      'A/B测试不同内容形式',
    ],
    externalUrl: 'https://www.tiktok.com/business',
    price: '免费（广告费另计）',
    relatedTools: ['instagram', 'facebook-business'],
  },
  // 物流类
  {
    id: 'tracking',
    name: '17TRACK',
    category: 'logistics',
    tier: 'free',
    tierLabel: '物流追踪',
    icon: EnvironmentOutlined,
    coreRole: '全球物流追踪平台，支持200+家物流公司的包裹追踪，帮助外贸企业实时查询发货状态，提升客户体验和物流透明度。',
    usageList: [
      '批量追踪：同时查询多个包裹状态',
      '异常提醒：包裹异常时自动通知',
      '数据统计：分析物流时效和签收率',
      '页面嵌入：嵌入网站供客户查询',
    ],
    stats: {
      carriers: { value: '200+', label: '支持物流商' },
      daily: { value: '1000万+', label: '日查询量' },
    },
    bestPractices: [
      '批量追踪提升效率',
      '设置异常预警及时处理问题',
      '提供追踪页面给客户自助查询',
    ],
    tips: [
      'API接口支持批量查询',
      '可定制品牌追踪页面',
      '历史数据用于分析物流表现',
    ],
    externalUrl: 'https://www.17track.net',
    price: '免费基础版 / API付费版',
    relatedTools: ['dhl', 'flexport'],
  },
  {
    id: 'dhl',
    name: 'DHL Express',
    category: 'logistics',
    tier: 'free',
    tierLabel: '国际快递',
    icon: RocketOutlined,
    coreRole: '全球领先的国际快递服务，覆盖220个国家地区，提供门到门的快递服务，是外贸发样的首选渠道之一，时效快、服务稳定。',
    usageList: [
      '国际快递：发样和小件货物到全球',
      '空运服务：大宗货物空运',
      '报关服务：协助清关文件准备',
      '仓储物流：一站式供应链解决方案',
    ],
    stats: {
      countries: { value: '220+', label: '覆盖国家' },
      transit: { value: '2-5天', label: '主要国家时效' },
    },
    bestPractices: [
      '提前准备商业发票，避免清关延误',
      '利用DHL账户折扣节省成本',
      '了解各国进口限制和关税政策',
    ],
    tips: [
      'MyDHL+在线管理寄件',
      'DHL Express Faster Banner快速寄件',
      '利用DHL跨境电商解决方案',
    ],
    externalUrl: 'https://www.dhl.com',
    price: '按实际重量和地区计费',
    relatedTools: ['tracking', 'flexport'],
  },
  {
    id: 'flexport',
    name: 'Flexport',
    category: 'logistics',
    tier: 'enterprise',
    tierLabel: '数字化货代',
    icon: GlobalOutlined,
    coreRole: '新型数字化货代平台，提供海运、空运、卡车等一站式物流服务，以可视化和数据化著称，帮助企业优化供应链管理。',
    usageList: [
      '海运/空运订舱：在线预订舱位',
      '报关服务：数字化报关流程',
      '供应链金融：提供货物融资服务',
      '数据分析：追踪和分析物流数据',
    ],
    stats: {
      freight: { value: '110+', label: '覆盖国家' },
      clients: { value: '10000+', label: '服务企业' },
    },
    bestPractices: [
      '提前订舱避免旺季爆仓',
      '利用平台数据分析优化物流成本',
      '善用供应链金融服务缓解资金压力',
    ],
    tips: [
      '平台透明报价，无隐藏费用',
      '专属客服提供全程支持',
      '可集成ERP和CRM系统',
    ],
    externalUrl: 'https://www.flexport.com',
    price: '按服务类型和货量定价',
    relatedTools: ['dhl', 'tracking'],
  },
  // 学习资源类
  {
    id: 'trade-english',
    name: '外贸实战英语900句',
    category: 'learning',
    tier: 'free',
    tierLabel: '免费资源',
    icon: FileTextOutlined,
    coreRole: '涵盖外贸全流程的实用英语表达，包括建立业务关系、询盘报价、合同谈判、支付结算、售后争议等场景的标准话术，配有中文翻译，适合快速提升商务英语沟通能力。',
    usageList: [
      '学习询盘回复的标准表达',
      '掌握报价和谈判的常用句式',
      '处理售后问题和争议沟通',
      '提升邮件和即时沟通的专业度',
    ],
    bestPractices: [
      '按场景分类学习，针对性提升',
      '结合实际沟通场景反复练习',
      '记录常用表达，形成个人话术库',
    ],
    tips: [
      '可作为团队培训材料',
      '建议每天学习10-15句',
      '关注行业特定术语表达',
    ],
    price: '免费',
  },
  {
    id: 'customs-knowledge',
    name: '海关归类与合规',
    category: 'learning',
    tier: 'free',
    tierLabel: '合规知识',
    icon: FileTextOutlined,
    coreRole: '外贸进出口必备的HS编码归类、原产地规则、进出口许可证等合规知识，帮助企业避免清关问题和合规风险。',
    usageList: [
      'HS编码查询：确定产品正确编码',
      '原产地规则：申请优惠关税待遇',
      '许可证管理：了解产品进出口要求',
      '合规培训：提升团队合规意识',
    ],
    bestPractices: [
      '定期更新目标市场的法规变化',
      '咨询专业报关行确保归类准确',
      '保留完整的合规文件记录',
    ],
    tips: [
      '中国海关官网提供HS编码查询',
      '贸促会提供原产地证书服务',
      '关注各国进口限制和禁令',
    ],
    price: '免费',
    relatedTools: ['cnab', 'dhl'],
  },
];

// ============================================================================
// 状态与过滤
// ============================================================================
const activeCategory = ref('all');
const searchKeyword = ref('');
const guideVisible = ref(false);
const currentTool = ref<TradeTool | null>(null);

// 收藏功能
const FAVORITES_KEY = 'uj-trade-tool-favorites';
const favoritedIds = ref<Set<string>>(new Set());

function loadLocalFavorites() {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    if (!raw) return;
    const ids = JSON.parse(raw) as string[];
    if (Array.isArray(ids)) {
      favoritedIds.value = new Set(ids.filter((id) => typeof id === 'string'));
    }
  } catch {
    favoritedIds.value = new Set();
  }
}

function persistFavorites() {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favoritedIds.value]));
}

onMounted(() => {
  void loadTenantContext();
  loadLocalFavorites();
});

// 对比功能
const compareList = ref<string[]>([]);
const showCompareModal = ref(false);

// 关联推荐
const showRelatedModal = ref(false);
const relatedTools = ref<TradeTool[]>([]);

const filteredTools = computed(() => {
  let result = TOOLS;
  
  // 分类过滤
  if (activeCategory.value !== 'all') {
    result = result.filter(t => t.category === activeCategory.value);
  }
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(t => 
      t.name.toLowerCase().includes(keyword) ||
      t.coreRole.toLowerCase().includes(keyword) ||
      t.usageList.some(u => u.toLowerCase().includes(keyword))
    );
  }
  
  return result;
});

// 分类标签
const CATEGORY_LABELS: Record<string, string> = {
  communication: '客户沟通',
  market: '市场分析',
  data: '数据挖掘',
  crm: 'CRM与销售',
  social: '社媒营销',
  logistics: '物流追踪',
  learning: '学习资源',
};

const CATEGORY_COLORS: Record<string, string> = {
  communication: 'blue',
  market: 'purple',
  data: 'red',
  crm: 'orange',
  social: 'magenta',
  logistics: 'cyan',
  learning: 'green',
};

// 搜索
function onSearch() {
  // 搜索功能已通过computed自动过滤
}

// 收藏功能
function isFavorited(id: string): boolean {
  return favoritedIds.value.has(id);
}

function toggleFavorite(id: string) {
  if (favoritedIds.value.has(id)) {
    favoritedIds.value.delete(id);
  } else {
    favoritedIds.value.add(id);
  }
  persistFavorites();
}

// 对比功能
function getToolById(id: string): TradeTool | undefined {
  return TOOLS.find(t => t.id === id);
}

function addToCompare(id: string) {
  if (!compareList.value.includes(id) && compareList.value.length < 4) {
    compareList.value.push(id);
  }
}

function removeFromCompare(id: string) {
  compareList.value = compareList.value.filter(i => i !== id);
}

function clearCompare() {
  compareList.value = [];
}

function hasStats(ids: string[]): boolean {
  return ids.some(id => getToolById(id)?.stats !== undefined);
}

function getCategoryLabel(category?: string): string {
  return category ? CATEGORY_LABELS[category] || category : '';
}

function getCategoryColor(category?: string): string {
  return category ? CATEGORY_COLORS[category] || 'default' : 'default';
}

// 使用状态
function getStatusColor(status?: string): string {
  switch (status) {
    case 'unfamiliar': return 'default';
    case 'learning': return 'processing';
    case 'proficient': return 'success';
    default: return 'default';
  }
}

function getStatusLabel(status?: string): string {
  switch (status) {
    case 'unfamiliar': return '未使用';
    case 'learning': return '学习中';
    case 'proficient': return '熟练使用';
    default: return '';
  }
}

// ============================================================================
// 操作
// ============================================================================
function openToolGuide(tool: TradeTool) {
  currentTool.value = tool;
  guideVisible.value = true;
  
  // 加载关联推荐
  if (tool.relatedTools && tool.relatedTools.length > 0) {
    relatedTools.value = tool.relatedTools
      .map(id => getToolById(id))
      .filter((t): t is TradeTool => t !== undefined);
  } else {
    relatedTools.value = [];
  }
}

function openExternal(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer');
}

function openRelatedTools() {
  showRelatedModal.value = true;
}


</script>

<style scoped>
:root {
  --color-primary: #1890ff;
  --color-primary-light: #e6f7ff;
  --color-danger: #dc2626;
  --color-danger-light: #fee2e2;
  --color-success: #059669;
  --color-success-light: #d1fae5;
  --color-success-alt: #22c55e;
  --color-warning: #f59e0b;
  --color-pro: var(--uj-brand, #4a9b8c);
  --color-pro-light: #dbeafe;
  --color-enterprise: #7c3aed;
  --color-enterprise-light: #f3e8ff;
  --color-text-dark: #1f2937;
  --color-text-medium-dark: #374151;
  --color-text-medium: #4b5563;
  --color-text-gray: #6b7280;
  --color-text-gray-light: #9ca3af;
  --color-border: #e5e7eb;
  --color-bg-light: #f9fafb;
  --color-bg-gray: #f3f4f6;
  --color-white: #fff;
}

.trade-tools-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* 搜索区域 */
.search-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.result-count {
  font-size: 14px;
  color: #666;
}

.category-tabs {
  margin-bottom: 24px;
  text-align: center;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.tool-card {
  background: var(--color-white);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.tool-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.tool-badges {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.tool-icon {
  font-size: 32px;
  color: var(--color-primary);
}

.tool-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.tool-price {
  font-size: 12px;
  color: var(--color-warning);
  font-weight: 500;
}

.badge--core {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.badge--free {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge--pro {
  background: var(--color-pro-light);
  color: var(--color-pro);
}

.badge--enterprise {
  background: var(--color-enterprise-light);
  color: var(--color-enterprise);
}

.tool-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 8px;
}

.tool-core {
  font-size: 14px;
  color: var(--color-text-gray);
  line-height: 1.6;
  margin-bottom: 12px;
}

.tool-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-bg-light);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-gray-light);
}

.tool-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-medium-dark);
  margin-bottom: 8px;
}

.usage-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.usage-list li {
  font-size: 13px;
  color: var(--color-text-gray);
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
}

.usage-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 6px;
  height: 6px;
  background: var(--color-success-alt);
  border-radius: 50%;
}

.tool-status {
  margin-bottom: 12px;
}

.tool-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.tool-actions :deep(.ant-btn) {
  flex: 1;
  min-width: 80px;
}

/* 弹窗内容样式 */
.guide-content {
  padding: 8px 0;
}

.guide-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.guide-content h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-dark);
  margin: 16px 0 8px;
}

.guide-content p,
.guide-content li {
  font-size: 14px;
  color: var(--color-text-medium);
  line-height: 1.7;
}

.guide-content ol,
.guide-content ul {
  padding-left: 20px;
  margin: 0;
}

.guide-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.mb-4 {
  margin-bottom: 16px;
}

/* 工具对比功能 */
.compare-section {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-white);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  max-width: 500px;
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.compare-title {
  font-weight: 600;
  color: var(--color-text-dark);
}

.compare-items {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.compare-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--color-bg-gray);
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.compare-item:hover {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

/* 对比表格 */
.compare-table-wrapper {
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.compare-table th,
.compare-table td {
  padding: 12px;
  border: 1px solid var(--color-border);
  text-align: center;
}

.compare-table th {
  background: var(--color-bg-light);
  font-weight: 600;
  color: var(--color-text-dark);
}

.compare-table td:first-child {
  background: var(--color-bg-light);
  font-weight: 500;
  color: var(--color-text-gray);
  text-align: left;
  width: 100px;
}

.compare-table .cell-left {
  text-align: left;
}

.compare-usage {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}

.compare-usage li {
  font-size: 13px;
  color: var(--color-text-gray);
  padding: 2px 0;
}

/* 关联推荐 */
.related-tools {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-tool-card {
  padding: 12px;
  background: var(--color-bg-light);
  border-radius: 8px;
}

.related-tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.related-tool-name {
  font-weight: 600;
  color: var(--color-text-dark);
  flex: 1;
}

.related-tool-desc {
  font-size: 13px;
  color: var(--color-text-gray);
  margin-bottom: 8px;
  line-height: 1.5;
}

.related-tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.related-tag {
  font-size: 12px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  padding: 2px 6px;
  border-radius: 2px;
}
</style>