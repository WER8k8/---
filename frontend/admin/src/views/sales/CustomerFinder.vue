<template>
  <YdPage surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showSearchModal = true">
        <SearchOutlined />
        开始搜索
      </a-button>
      <a-button @click="exportCustomers">
        <ExportOutlined />
        导出客户
      </a-button>
    </template>
  <div class="customer-finder">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <a-card class="stat-card">
          <a-statistic
            title="总客户数"
            :value="stats.totalCustomers"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><UserOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="今日新增"
            :value="stats.todayNew"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix><RiseOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="高价值客户"
            :value="stats.highValue"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix><StarOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="已联系"
            :value="stats.contacted"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix><MailOutlined /></template>
          </a-statistic>
        </a-card>
      </div>

      <a-alert
        v-if="sidecarBanner"
        class="sidecar-banner"
        :type="sidecarBanner.type"
        show-icon
        :message="sidecarBanner.title"
        :description="sidecarBanner.description"
      />

      <a-collapse v-model:activeKey="intelPanels" ghost class="intel-panels mb-4">
        <a-collapse-panel key="customs" header="海关买家反查（受限 · 须授权）">
          <CustomsBuyerResearchPanel />
        </a-collapse-panel>
      </a-collapse>

      <!-- 筛选器 -->
      <a-card class="filter-card">
        <a-form layout="inline" :model="filters">
          <a-form-item label="关键词">
            <a-select
              v-model:value="filters.keywords"
              mode="tags"
              placeholder="输入关键词"
              style="width: 300px"
            />
          </a-form-item>
          <a-form-item label="国家">
            <a-select
              v-model:value="filters.countries"
              mode="multiple"
              placeholder="选择国家"
              style="width: 200px"
              :options="countryOptions"
            />
          </a-form-item>
          <a-form-item label="评分">
            <a-slider
              v-model:value="filters.minScore"
              :min="0"
              :max="100"
              :marks="{ 0: '0', 50: '50', 80: '80', 100: '100' }"
              style="width: 200px"
            />
          </a-form-item>
          <a-form-item label="状态">
            <a-select
              v-model:value="filters.status"
              placeholder="选择状态"
              style="width: 150px"
              :options="statusOptions"
            />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="applyFilters">
              <FilterOutlined />
              筛选
            </a-button>
            <a-button @click="resetFilters" style="margin-left: 8px">
              重置
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>

      <!-- 客户列表 -->
      <a-card class="customer-list-card">
        <a-table
          :columns="columns"
          :data-source="customers"
          :loading="loading"
          :pagination="pagination"
          :row-selection="rowSelection"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="customer-name">
                <a-avatar :style="{ backgroundColor: getAvatarColor(record.score) }">
                  {{ record.name.charAt(0) }}
                </a-avatar>
                <div class="name-info">
                  <div class="name">{{ record.name }}</div>
                  <div class="company">{{ record.company }}</div>
                </div>
              </div>
            </template>
            <template v-else-if="column.key === 'contact'">
              <div class="contact-cell">
                <span v-if="record.email" class="email-line">{{ record.email }}</span>
                <span v-else class="text-muted">暂无邮箱</span>
                <a-tag v-if="record.emailEnrichment" size="small" color="blue">Sidecar 补全</a-tag>
                <a
                  v-if="record.evidenceUrl"
                  :href="record.evidenceUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="evidence-link"
                >
                  证据链
                </a>
              </div>
            </template>
            <template v-else-if="column.key === 'score'">
              <a-progress
                :percent="record.score"
                :stroke-color="getScoreColor(record.score)"
                :show-info="false"
                size="small"
                style="width: 80px"
              />
              <span class="score-text">{{ record.score }}分</span>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="viewCustomer(record)">
                  查看
                </a-button>
                <a-button type="link" size="small" @click="sendEmail(record)">
                  发邮件
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多 <DownOutlined />
                  </a-button>
                  <template #overlay>
                    <a-menu @click="({ key }) => handleMoreAction(key, record)">
                      <a-menu-item key="edit">编辑</a-menu-item>
                      <a-menu-item key="addNote">添加备注</a-menu-item>
                      <a-menu-item key="markContacted">标记已联系</a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" danger>删除</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 搜索弹窗 -->
      <a-modal
        v-model:open="showSearchModal"
        title="客户搜索设置"
        width="700px"
        @ok="startSearch"
        @cancel="showSearchModal = false"
      >
        <a-form :model="searchForm" layout="vertical">
          <a-form-item label="搜索关键词" required>
            <a-select
              v-model:value="searchForm.keywords"
              mode="tags"
              placeholder="输入产品关键词，如：insulation, rock wool, building materials"
              :options="keywordSuggestions"
            />
            <div class="form-help">支持多个关键词，系统将自动组合搜索</div>
          </a-form-item>
          <a-form-item label="搜索来源">
            <a-select
              v-model:value="searchForm.searchSource"
              placeholder="选择搜索渠道"
              :options="searchSourceOptions"
            />
            <div class="form-help">选择特定渠道或使用「全部渠道」进行综合搜索</div>
          </a-form-item>
          <a-form-item label="目标国家/地区">
            <a-select
              v-model:value="searchForm.countries"
              mode="multiple"
              placeholder="选择目标市场"
              :options="countryOptions"
            />
          </a-form-item>
          <a-form-item label="行业筛选">
            <a-select
              v-model:value="searchForm.industry"
              placeholder="选择行业"
              :options="industryOptions"
            />
          </a-form-item>
          <a-form-item label="最大结果数">
            <a-input-number
              v-model:value="searchForm.maxResults"
              :min="10"
              :max="500"
              style="width: 200px"
            />
          </a-form-item>
        </a-form>

        <!-- 搜索语法实时预览 -->
        <div style="margin-top: 16px;">
          <SearchSyntaxPreview
            :keywords="searchForm.keywords"
            :countries="searchForm.countries"
            :customer-type="searchForm.customerType"
            :search-source="searchForm.searchSource"
            @syntax-generated="onSyntaxGenerated"
          />
        </div>
      </a-modal>

      <!-- 客户详情抽屉 -->
      <a-drawer
        v-model:open="showDetailDrawer"
        title="客户详情"
        width="600"
        placement="right"
      >
        <CustomerDetail
          v-if="selectedCustomer"
          :customer="selectedCustomer"
          @send-email="sendEmail"
          @update-status="updateCustomerStatus"
        />
      </a-drawer>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  SearchOutlined,
  ExportOutlined,
  UserOutlined,
  RiseOutlined,
  StarOutlined,
  MailOutlined,
  FilterOutlined,
  DownOutlined,
} from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';
import CustomerDetail from '@/components/sales/CustomerDetail.vue';
import CustomsBuyerResearchPanel from '@/components/sales/CustomsBuyerResearchPanel.vue';
import SearchSyntaxPreview from '@/components/whatsfinds/SearchSyntaxPreview.vue';
import type { Customer, CustomerFilters, SearchCriteria } from '@/types/sales';
import { apiPut, apiGet, apiPost, authHeaders } from '@/utils/api';

// FIX-5: 渠道状态类型
interface ChannelStatus {
  id: string;
  name: string;
  status: 'real' | 'mock' | 'coming_soon';
  reason: string;
}

const router = useRouter();

// 统计数据（由搜索结果计算）
const stats = reactive({
  totalCustomers: 0,
  todayNew: 0,
  highValue: 0,
  contacted: 0,
});

// 筛选器
const filters = reactive<CustomerFilters>({
  keywords: [],
  countries: [],
  minScore: 0,
  status: undefined,
});

// 搜索表单
const searchForm = reactive<SearchCriteria>({
  keywords: [],
  searchSource: 'all',
  countries: [],
  industry: undefined,
  maxResults: 50,
  customerType: '',
});

// 状态
const loading = ref(false);
const showSearchModal = ref(false);
const showDetailDrawer = ref(false);
const selectedCustomer = ref<Customer | null>(null);
const customers = ref<Customer[]>([]);
const customerSource = ref<Customer[]>([]);
const sidecarStatus = ref<Record<string, { healthy?: boolean | null; configured?: boolean }>>({});
const intelPanels = ref<string[]>([]);
const lastSearchMeta = ref<{ find_mode?: string; probe_mode?: string; email_enrichment?: unknown }>({});

const sidecarBanner = computed(() => {
  const st = sidecarStatus.value;
  const fc = st.ai_find_customer;
  const em = st.domain_email_extractor;
  const cu = st.customs_data_spider;
  if (!fc && !em && !cu) return null;
  const fcOk = fc?.healthy === true;
  const emOk = em?.healthy === true;
  const cuOk = cu?.healthy === true;
  if (fcOk && emOk) {
    const extra = cuOk ? '；海关反查 Sidecar 已就绪' : '';
    return {
      type: 'success' as const,
      title: '找客旁路在线',
      description: `AI 找客 + 官网邮箱 enrichment 已就绪；线索须人工核实 evidence_url，禁止未授权群发。${extra}`,
    };
  }
  const parts: string[] = [];
  if (!fcOk) parts.push('AI_FIND_CUSTOMER_URL 未配置或未健康');
  if (!emOk) parts.push('DOMAIN_EMAIL_EXTRACTOR_URL 未配置或未健康');
  return {
    type: 'warning' as const,
    title: '找客旁路未完全就绪',
    description: `${parts.join('；')}。可运行 scripts/start-p3-sidecars-dev.ps1 后重启后端。`,
  };
});

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
});

// 行选择
const rowSelection = reactive({
  selectedRowKeys: [] as string[],
  onChange: (selectedRowKeys: (string | number)[]) => {
    rowSelection.selectedRowKeys = selectedRowKeys as string[];
  },
});

// 表格列定义
const columns = [
  {
    title: '客户信息',
    key: 'name',
    width: 250,
  },
  {
    title: '国家',
    dataIndex: 'country',
    key: 'country',
    width: 100,
  },
  {
    title: '联系 / 证据',
    key: 'contact',
    width: 220,
  },
  {
    title: '行业',
    dataIndex: 'industry',
    key: 'industry',
    width: 150,
  },
  {
    title: '评分',
    key: 'score',
    width: 150,
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
  },
  {
    title: '最后联系',
    dataIndex: 'lastContact',
    key: 'lastContact',
    width: 120,
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right' as const,
  },
];

// 选项数据
const countryOptions = [
  { label: '美国', value: 'USA' },
  { label: '德国', value: 'Germany' },
  { label: '英国', value: 'UK' },
  { label: '法国', value: 'France' },
  { label: '意大利', value: 'Italy' },
  { label: '西班牙', value: 'Spain' },
  { label: '加拿大', value: 'Canada' },
  { label: '澳大利亚', value: 'Australia' },
  { label: '日本', value: 'Japan' },
  { label: '韩国', value: 'Korea' },
];

const statusOptions = [
  { label: '全部', value: undefined },
  { label: '新客户', value: 'new' },
  { label: '已联系', value: 'contacted' },
  { label: '已认证', value: 'qualified' },
  { label: '已转化', value: 'converted' },
];

const industryOptions = [
  { label: '建筑材料', value: 'construction' },
  { label: '装饰材料', value: 'decoration' },
  { label: '保温材料', value: 'insulation' },
  { label: '防水材料', value: 'waterproofing' },
  { label: '五金配件', value: 'hardware' },
];

const keywordSuggestions = [
  { label: 'insulation', value: 'insulation' },
  { label: 'rock wool', value: 'rock wool' },
  { label: 'glass wool', value: 'glass wool' },
  { label: 'building materials', value: 'building materials' },
  { label: 'construction materials', value: 'construction materials' },
];

// FIX-5: 渠道状态 — 从后端获取真实可用性
const channelStatusMap = ref<Record<string, ChannelStatus>>({});
const channelStatusLoaded = ref(false);

async function loadChannelStatuses() {
  try {
    const res = await apiGet('/super-agent/sales/channels');
    const channels: ChannelStatus[] = res?.data ?? [];
    const map: Record<string, ChannelStatus> = {};
    for (const ch of channels) map[ch.id] = ch;
    channelStatusMap.value = map;
    channelStatusLoaded.value = true;
  } catch {
    // 静默失败，不影响页面正常使用
    channelStatusLoaded.value = true;
  }
}

// FIX-5: 动态渠道选项 — mock 渠道添加 "(演示数据)" 标注
// 零成本获客引擎：免费管道（Google CSE + 网站抓取 + 邮箱验证）
const searchSourceOptions = computed(() => {
  const base = [
    { label: '🔥 零成本获客引擎（推荐）', value: 'free_pipeline' },
    { label: '全部渠道（综合搜索）', value: 'all' },
    { label: 'WhatsApp 全球获客', value: 'whatsapp' },
    { label: 'Reddit 社区', value: 'reddit' },
    { label: 'LinkedIn 决策人', value: 'linkedin' },
    { label: 'TikTok 短视频', value: 'tiktok' },
    { label: 'Google 搜索', value: 'google' },
    { label: 'Quora 问答', value: 'quora' },
  ];
  const map = channelStatusMap.value;
  if (!Object.keys(map).length) return base;
  return base.map(opt => {
    // 零成本引擎始终是真实的
    if (opt.value === 'free_pipeline') return opt;
    const ch = map[opt.value];
    if (!ch || ch.status === 'real') return opt;
    return { ...opt, label: `${opt.label}（演示数据）` };
  });
});

// 方法
function getAvatarColor(score: number): string {
  if (score >= 80) return '#52c41a';
  if (score >= 60) return '#1890ff';
  if (score >= 40) return '#faad14';
  return '#d9d9d9';
}

function getScoreColor(score: number): string {
  if (score >= 80) return '#52c41a';
  if (score >= 60) return '#1890ff';
  if (score >= 40) return '#faad14';
  return '#ff4d4f';
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    new: 'blue',
    contacted: 'orange',
    qualified: 'green',
    converted: 'purple',
  };
  return colors[status] || 'default';
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    new: '新客户',
    contacted: '已联系',
    qualified: '已认证',
    converted: '已转化',
  };
  return texts[status] || status;
}

async function loadSidecarStatus() {
  try {
    const res = await apiGet<{ data?: Record<string, unknown> }>(
      '/foreign-trade/integrations/sidecars/status',
    );
    const data = (res as { data?: Record<string, unknown> })?.data ?? res;
    sidecarStatus.value = (data as typeof sidecarStatus.value) || {};
  } catch {
    sidecarStatus.value = {};
  }
}

function updateStatsFromCustomers(list: Customer[]) {
  const today = new Date().toISOString().slice(0, 10);
  stats.totalCustomers = list.length;
  stats.todayNew = list.filter((c) => c.lastContact === today).length;
  stats.highValue = list.filter((c) => c.score >= 80).length;
  stats.contacted = list.filter((c) =>
    ['contacted', 'qualified', 'converted'].includes(c.status),
  ).length;
  pagination.total = list.length;
}

function applyClientFilters() {
  let list = [...customerSource.value];
  if (filters.keywords?.length) {
    const keys = filters.keywords.map((k) => k.toLowerCase());
    list = list.filter((c) =>
      keys.some(
        (k) =>
          c.name.toLowerCase().includes(k) ||
          c.company.toLowerCase().includes(k) ||
          (c.industry || '').toLowerCase().includes(k),
      ),
    );
  }
  if (filters.countries?.length) {
    list = list.filter((c) => filters.countries!.includes(c.country));
  }
  if (filters.minScore > 0) {
    list = list.filter((c) => c.score >= filters.minScore);
  }
  if (filters.status) {
    list = list.filter((c) => c.status === filters.status);
  }
  customers.value = list;
  updateStatsFromCustomers(list);
}

async function applyFilters() {
  if (customerSource.value.length === 0) {
    message.warning('请先使用「开始搜索」获取客户列表');
    return;
  }
  applyClientFilters();
  message.success('筛选完成');
}

function resetFilters() {
  filters.keywords = [];
  filters.countries = [];
  filters.minScore = 0;
  filters.status = undefined;
}

// ── 零成本获客引擎（真实数据，零成本） ──
async function _searchWithFreePipeline() {
  try {
    const result = await apiPost('/lead-generation/search', {
      keywords: searchForm.keywords,
      country: searchForm.countries?.[0],
      industry: searchForm.industry,
      max_results: searchForm.maxResults,
      verify_emails: true,
      min_confidence: 0.3,
    });

    if (result.code === 0) {
      const payload = result.data || {};
      const leads = payload.leads || [];

      // 转换为 Customer 格式
      const mapped: Customer[] = leads
        .filter((lead: any) => lead.emails?.length > 0)
        .map((lead: any, idx: number) => {
          const primaryEmail = lead.emails[0];
          const allEmails = lead.emails.map((e: any) => e.email);
          // 基于验证状态计算分数
          const baseScore = primaryEmail.verified ? 85 : primaryEmail.confidence * 100;
          return {
            id: `free_${Date.now()}_${idx}`,
            name: lead.company_name || lead.domain || '未知公司',
            email: primaryEmail.email,
            allEmails,
            company: lead.company_name || lead.domain || '',
            website: lead.website,
            country: searchForm.countries?.[0] || '',
            source: 'free_pipeline',
            sourceLabel: '零成本获客引擎',
            score: Math.round(baseScore),
            status: 'new',
            verified: primaryEmail.verified === true,
            verificationStatus: primaryEmail.verification_status,
            snippet: lead.snippet,
            lastContact: '',
            tags: primaryEmail.verified
              ? ['已验证邮箱']
              : ['待验证'],
          };
        });

      customerSource.value = mapped;
      applyClientFilters();
      lastSearchMeta.value = {
        find_mode: 'free_pipeline',
        probe_mode: 'real_data',
        email_enrichment: { emails_added: payload.emails_found },
      };

      const note = payload.note ? `（${payload.note}）` : '';
      message.success(
        `找到 ${mapped.length} 个有邮箱的潜在客户（共 ${payload.total_found} 个网站）${note}`,
      );
    } else {
      message.error(result.message || '搜索失败');
    }
  } catch (error) {
    console.error('零成本获客搜索失败:', error);
    message.error('搜索失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
}

// 搜索语法预览回调
const generatedSyntax = ref('')
function onSyntaxGenerated(syntax: string) {
  generatedSyntax.value = syntax
}

async function startSearch() {
  if (searchForm.keywords.length === 0) {
    message.warning('请输入至少一个搜索关键词');
    return;
  }

  showSearchModal.value = false;
  loading.value = true;

  try {
    // 零成本获客引擎：直接调用 lead-generation API（真实数据，零成本）
    if (searchForm.searchSource === 'free_pipeline') {
      await _searchWithFreePipeline();
      return;
    }

    const result = await apiPost('/super-agent/sales/customer-finder', {
      keywords: searchForm.keywords,
      search_source: searchForm.searchSource,
      countries: searchForm.countries,
      industry: searchForm.industry,
      max_results: searchForm.maxResults,
    });

    if (result.code === 0) {
      const payload = result.data || {};
      lastSearchMeta.value = {
        find_mode: payload.find_mode || payload.mode,
        probe_mode: payload.probe_mode,
        email_enrichment: payload.email_enrichment,
      };
      const rawCustomers = payload.customers || payload.results?.customers || [];
      customerSource.value = rawCustomers.map(mapApiCustomer);
      applyClientFilters();
      const mode = payload.find_mode || payload.mode;
      const total = payload.total_found ?? customerSource.value.length;
      const modeHint =
        payload.probe_mode === 'stub'
          ? '（开发 stub，非真实爬取；须配置真实 AI_Find_Customer 上游）'
          : mode === 'ai_find_customer_sidecar'
            ? '（Sidecar 线索，须人工核实 evidence_url）'
            : mode === 'accio_buyer_discovery'
              ? '（画像模板，建议配置 AI_FIND_CUSTOMER_URL）'
              : '';
      const emailHint =
        payload.email_enrichment && typeof payload.email_enrichment === 'object'
          ? `；邮箱 enrichment：+${(payload.email_enrichment as { emails_added?: number }).emails_added ?? 0} 条`
          : '';
      message.success(`找到 ${total} 个潜在客户${modeHint}${emailHint}`);
    } else {
      message.error(result.message || '搜索失败');
    }
  } catch (error) {
    console.error('搜索失败:', error);
    message.error('搜索失败，请重试');
  } finally {
    loading.value = false;
  }
}

function fallbackCustomerId(row: Record<string, unknown>, name: string): string {
  const seed = [
    row.email,
    row.company,
    row.company_name,
    row.website,
    row.evidence_url,
    name,
  ]
    .filter(Boolean)
    .join('|');
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return `cust_${(h >>> 0).toString(36)}`;
}

function mapApiCustomer(row: Record<string, unknown>): Customer {
  const rawScore = row.score ?? row.fit_score ?? 0;
  let score = Number(rawScore);
  if (Number.isNaN(score)) score = 0;
  if (score > 0 && score <= 1) score *= 100;
  const name =
    String(row.name || row.company_name || row.title || row.company || 'Unknown');
  const today = new Date().toISOString().slice(0, 10);
  const evidenceUrl = String(
    row.evidence_url || row.website || row.linkedin_url || row.source_url || '',
  );
  return {
    id: String(row.id || row.customer_id || fallbackCustomerId(row, name)),
    name,
    company: String(row.company || row.company_name || name),
    email: String(row.email || ''),
    phone: row.phone ? String(row.phone) : undefined,
    whatsappNumber: row.whatsapp_number ? String(row.whatsapp_number) : row.phone ? String(row.phone) : undefined,
    website: String(row.website || row.evidence_url || ''),
    country: String(row.country || row.country_code || ''),
    industry: String(row.industry || searchForm.industry || ''),
    score: Math.round(score),
    status: (row.status as Customer['status']) || 'new',
    lastContact: String(row.lastContact || today),
    notes: row.notes ? String(row.notes) : undefined,
    evidenceUrl: evidenceUrl || undefined,
    emailEnrichment: row.email_enrichment ? String(row.email_enrichment) : undefined,
  };
}

function viewCustomer(customer: any) {
  selectedCustomer.value = customer;
  showDetailDrawer.value = true;
}

function sendEmail(customer: any) {
  const email = customer.email || customer.contact_email;
  if (!email) {
    message.warning('该客户暂无邮箱，请先补充联系方式');
    return;
  }
  router.push({
    name: 'EmailAutomation',
    state: {
      emailPrefill: {
        recipients: [email],
        subject: `Business inquiry — ${customer.name}`,
        type: 'cold_outreach',
      },
    },
  });
}

async function updateCustomerStatus(customer: Customer, status: string) {
  try {
    await apiPut(`/super-agent/sales/customer-finder/${customer.id}/status`, { status });
    customer.status = status as any;
    message.success(`客户状态已更新为: ${status}`);
  } catch (err: any) {
    message.error(err?.message || '状态更新失败');
  }
}

function handleMoreAction(key: string | number, customer: any) {
  const action = String(key);
  switch (action) {
    case 'edit':
      // 编辑客户
      break;
    case 'addNote':
      // 添加备注
      break;
    case 'markContacted':
      updateCustomerStatus(customer, 'contacted');
      break;
    case 'delete':
      // 删除客户
      break;
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
}

function exportCustomers() {
  if (rowSelection.selectedRowKeys.length === 0) {
    message.warning('请先选择要导出的客户');
    return;
  }
  message.success(`正在导出 ${rowSelection.selectedRowKeys.length} 个客户`);
}

onMounted(() => {
  loadChannelStatuses();
  loadSidecarStatus();
});

</script>

<style scoped>
.customer-finder {
  padding: 24px;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.sidecar-banner {
  margin-bottom: 16px;
}

.intel-panels {
  background: #fff;
  border-radius: 8px;
}

.contact-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.email-line {
  color: #1a1a1a;
}

.text-muted {
  color: #8c8c8c;
}

.evidence-link {
  font-size: 12px;
}

.stat-card {
  border-radius: 8px;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.customer-list-card {
  border-radius: 8px;
}

.customer-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.name-info {
  display: flex;
  flex-direction: column;
}

.name {
  font-weight: 500;
  color: #1a1a1a;
}

.company {
  font-size: 12px;
  color: #8c8c8c;
}

.score-text {
  margin-left: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

.form-help {
  margin-top: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .customer-finder {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .stats-cards {
    grid-template-columns: 1fr;
  }
}
</style>
