/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="询盘队列" subtitle="待处理询盘 · 今日优先跟进" surface="elevated">
    <div v-if="pipelineSummary?.stages?.length" class="yd-panel p-3 mb-3 flex flex-wrap gap-2 items-center">
      <span class="text-xs text-gray-500 mr-1">管道 GW-L-PL-01</span>
      <a-tag
        v-for="st in pipelineSummary.stages"
        :key="st.id"
        :color="query.pipeline_stage === st.id ? 'blue' : 'default'"
        class="cursor-pointer"
        @click="filterPipeline(st.id)"
      >
        {{ st.label_zh }} {{ pipelineSummary.counts?.[st.id] ?? 0 }}
      </a-tag>
      <a-button size="small" type="link" @click="clearPipelineFilter">清除阶段筛选</a-button>
    </div>
    <YdSearchBar @search="onSearch" @reset="onReset">
      <a-input v-model:value="query.search" placeholder="联系人/电话" allow-clear style="width: 180px" />
      <a-radio-group v-model:value="query.status" button-style="solid">
        <a-radio-button value="">全部</a-radio-button>
        <a-radio-button value="pending">待处理</a-radio-button>
        <a-radio-button value="quoted">处理中</a-radio-button>
      </a-radio-group>
      <template #extra>
        <a-button :loading="imapPolling" @click="imapModalOpen = true">
          拉取邮箱询盘
        </a-button>
        <YdTableColumnSettings
          :columns="orderedColumns"
          :hidden-keys="hiddenColumnKeys"
          @toggle="toggleColumnVisibility"
          @move-up="moveColumnUp"
          @move-down="moveColumnDown"
          @reset="resetColumnLayout"
        />
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          show-export
          @refresh="reload"
          @export="exportCsv"
        />
      </template>
    </YdSearchBar>

    <YdEmptyState
      v-if="!loading && !items.length"
      variant="inquiry"
      @action="router.push('/client/inquiries')"
    />

    <SkeletonCard v-else-if="loading && !items.length" variant="table" :rows="6" />

    <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="visibleColumns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        @page-change="(p) => onPageChange(p.current, p.pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="openDetail(record)">详情</a-button>
          </template>
        </template>
      </YdDataTable>
    </div>

    <a-drawer v-model:open="detailOpen" title="询盘详情" width="480">
      <template v-if="detailRow">
        <p class="text-sm"><strong>联系人：</strong>{{ detailRow.name || '—' }}</p>
        <p class="text-sm"><strong>电话：</strong>{{ detailRow.phone || '—' }}</p>
        <p class="text-sm"><strong>邮箱：</strong>{{ detailRow.email || '—' }}</p>
        <p class="text-sm"><strong>意向：</strong>{{ detailRow.intent_label || '—' }}</p>
        <div class="mt-2">
          <p class="text-sm font-medium">销售管道阶段</p>
          <a-select
            v-model:value="pipelineStage"
            size="small"
            class="w-full mt-1"
            :options="pipelineOptions"
            @change="(v) => savePipelineStage(v as string)"
          />
        </div>
        <p v-if="detailRow.intent_next_action" class="text-xs text-indigo-700 mt-1">
          建议：{{ detailRow.intent_next_action }}
        </p>
        <a-alert
          v-if="bridgeStatus?.mode === 'mock'"
          type="warning"
          show-icon
          class="mt-3"
          :message="bridgeStatus.disclaimer || '未配置 AI Key，摘要/英文草稿为开发占位，请勿直接发送'"
        />
        <div class="mt-3 flex flex-wrap gap-2">
          <a-button size="small" :loading="bridgeLoading === 'summary'" @click="runBridgeSummary">
            中文摘要
          </a-button>
          <a-button size="small" :loading="ftLoading === 'osint'" @click="runInquiryOsint">背调</a-button>
          <a-button size="small" :loading="ftLoading === 'meddpicc'" @click="runInquiryMeddpicc">MEDDPICC</a-button>
          <a-button size="small" :loading="ftLoading === 'pi'" @click="runInquiryPi">生成 PI</a-button>
          <a-button size="small" type="default" @click="router.push('/client/annex/goodjob/customers')">
            GoodJob 客户档案
          </a-button>
        </div>
        <div v-if="bridgeSummary" class="mt-3 p-2 bg-amber-50 rounded text-xs">
          <p class="font-medium text-amber-900">中文摘要（给老板看）</p>
          <p v-if="bridgeSummary.mode === 'mock'" class="text-orange-700 mt-1">
            {{ bridgeSummary.disclaimer || '开发占位摘要，请配置 AI Key 后重新生成' }}
          </p>
          <p class="text-gray-800 mt-1 whitespace-pre-wrap">{{ bridgeSummary.summary_zh }}</p>
          <p v-if="bridgeSummary.suggested_next" class="text-indigo-700 mt-1">
            建议：{{ bridgeSummary.suggested_next }}
          </p>
        </div>
        <div class="mt-3">
          <p class="text-sm font-medium">用中文写回复要点</p>
          <a-textarea v-model:value="bossReplyZh" :rows="3" placeholder="例如：有现货，MOQ 100立方，FOB 天津，可发规格表" />
          <a-button
            size="small"
            type="primary"
            class="mt-2"
            :loading="bridgeLoading === 'reply'"
            :disabled="!bossReplyZh.trim()"
            @click="runReplyDraft"
          >
            生成英文回复草稿
          </a-button>
        </div>
        <div v-if="replyDraft?.body_en" class="mt-3 p-2 bg-green-50 rounded text-xs">
          <p class="font-medium text-green-900">英文草稿（发送前请核对）</p>
          <p v-if="replyDraft.subject_en" class="text-gray-700"><strong>Subject:</strong> {{ replyDraft.subject_en }}</p>
          <pre class="whitespace-pre-wrap text-gray-800 mt-1">{{ replyDraft.body_en }}</pre>
          <p v-if="replyDraft.body_zh_backtranslation" class="text-gray-600 mt-1">
            回译：{{ replyDraft.body_zh_backtranslation }}
          </p>
          <a-button size="small" class="mt-2" @click="copyReplyDraft">复制英文</a-button>
        </div>
        <div v-if="ftResult" class="mt-3 p-2 bg-indigo-50 rounded text-xs">
          <p class="font-medium text-indigo-900">{{ ftResult.title }}</p>
          <p class="text-gray-700 mt-1 whitespace-pre-wrap">{{ ftResult.body }}</p>
          <a-button
            v-if="ftResult.markdown"
            size="small"
            type="link"
            class="mt-1 px-0"
            @click="downloadPi"
          >
            下载 PI Markdown
          </a-button>
          <a-button
            v-if="ftResult.markdown"
            size="small"
            type="link"
            class="mt-1 px-0"
            @click="downloadPiDocx"
          >
            下载 PI Word
          </a-button>
          <a-button
            v-if="ftResult.markdown"
            size="small"
            type="link"
            class="mt-1 px-0"
            @click="downloadPiPdf"
          >
            下载 PI PDF
          </a-button>
        </div>
        <div v-if="discoveryQs.length" class="mt-3">
          <p class="text-sm font-medium">Discovery 追问</p>
          <ol class="text-xs text-gray-700 pl-4 mt-1">
            <li v-for="q in discoveryQs" :key="q.id">{{ q.question }}</li>
          </ol>
          <a-button size="small" class="mt-2" @click="copyDiscovery">复制追问</a-button>
        </div>
        <p class="text-sm font-medium mt-3">留言</p>
        <p class="text-xs text-gray-600 whitespace-pre-wrap">{{ detailRow.message_clean || detailRow.message }}</p>
      </template>
    </a-drawer>

    <a-modal
      v-model:open="imapModalOpen"
      title="只读 IMAP 询盘收取"
      ok-text="开始拉取"
      :confirm-loading="imapPolling"
      @ok="runImapPoll"
    >
      <a-alert
        type="warning"
        show-icon
        class="mb-3"
        message="只读收取，禁止自动 SMTP 回复；入库后须人工核实再回邮"
      />
      <a-checkbox v-model:checked="imapConsent.tenant">已获得租户书面授权配置邮箱</a-checkbox>
      <br />
      <a-checkbox v-model:checked="imapConsent.compliance" class="mt-2">
        已确认合规（不冒充已回复/不自动群发）
      </a-checkbox>
      <a-tag v-if="bridgeStatus?.imap_inquiry?.healthy" color="green" class="mt-3">IMAP Sidecar 在线</a-tag>
      <a-tag v-else color="default" class="mt-3">IMAP Sidecar 未配置</a-tag>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import {
  YdDataTable,
  YdEmptyState,
  YdPage,
  YdSearchBar,
  YdTableColumnSettings,
  YdTableToolbar,
} from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useYoudingTable } from '@/composables/useYoudingTableBridge';
import { apiGet } from '@/utils/api';
import { downloadTableCsv } from '@/utils/exportCsv';
import { adaptPaginatedResponse } from '@/utils/ydTableUtils';
import {
  inquiryBridgeStatus,
  inquiryBridgeSummary,
  inquiryImapPoll,
  inquiryPipelineStageUpdate,
  inquiryPipelineSummary,
  inquiryReplyDraft,
  type BridgeSummary,
  type InquiryBridgeStatus,
  type PipelineSummary,
  type ReplyDraft,
} from '@/api/cross-border';
import {
  downloadMarkdown,
  exportInquiryProformaFile,
  inquiryMeddpicc,
  inquiryOsint,
  inquiryProforma,
} from '@/api/foreign-trade';

const router = useRouter();
const tablePanelRef = ref<HTMLElement | null>(null);

const baseColumns = [
  { key: 'name', title: '联系人', dataIndex: 'name', align: 'center' },
  { key: 'phone', title: '电话', dataIndex: 'phone', align: 'center' },
  {
    key: 'intent_level',
    title: '意向',
    dataIndex: 'intent_label',
    align: 'center',
  },
  { key: 'status', title: '状态', dataIndex: 'status', align: 'center' },
  {
    key: 'pipeline_stage_label',
    title: '管道',
    dataIndex: 'pipeline_stage_label',
    align: 'center',
  },
  { key: 'source_channel', title: '来源', dataIndex: 'source_channel', align: 'center' },
  { key: 'created_at', title: '时间', dataIndex: 'created_at', align: 'center' },
  { key: 'action', title: '操作', align: 'center', width: 72 },
];

const detailOpen = ref(false);
const detailRow = ref<Record<string, unknown> | null>(null);
const ftLoading = ref<'osint' | 'meddpicc' | 'pi' | ''>('');
const bridgeLoading = ref<'summary' | 'reply' | ''>('');
const bridgeSummary = ref<BridgeSummary | null>(null);
const bridgeStatus = ref<InquiryBridgeStatus | null>(null);
const pipelineSummary = ref<PipelineSummary | null>(null);
const pipelineStage = ref<string>('mql');
const pipelineOptions = computed(() =>
  (pipelineSummary.value?.stages || []).map((s) => ({
    value: s.id,
    label: `${s.label_zh} (${s.label})`,
  })),
);
const imapModalOpen = ref(false);
const imapPolling = ref(false);
const imapConsent = ref({ tenant: false, compliance: false });
const replyDraft = ref<ReplyDraft | null>(null);
const bossReplyZh = ref('');
const ftResult = ref<{ title: string; body: string; markdown?: string } | null>(null);
const discoveryQs = computed(() => {
  const qs = detailRow.value?.discovery_questions;
  return Array.isArray(qs) ? (qs as Array<{ id: string; question: string }>) : [];
});

function openDetail(record: Record<string, unknown>) {
  detailRow.value = record;
  pipelineStage.value = String(record.pipeline_stage || 'mql');
  ftResult.value = null;
  bridgeSummary.value = null;
  replyDraft.value = null;
  bossReplyZh.value = '';
  detailOpen.value = true;
  void loadBridgeStatus();
}

async function loadPipelineSummary() {
  try {
    pipelineSummary.value = await inquiryPipelineSummary();
  } catch {
    pipelineSummary.value = null;
  }
}

async function savePipelineStage(stage: string) {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  try {
    const res = await inquiryPipelineStageUpdate(id, { stage });
    message.success(`已更新为 ${res.pipeline_stage_label || stage}`);
    detailRow.value = { ...detailRow.value, ...res };
    await loadPipelineSummary();
    await reload();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '阶段更新失败');
  }
}

function filterPipeline(stageId: string) {
  (query as { pipeline_stage?: string }).pipeline_stage = stageId;
  void search();
}

function clearPipelineFilter() {
  delete (query as { pipeline_stage?: string }).pipeline_stage;
  void search();
}

async function loadBridgeStatus() {
  try {
    bridgeStatus.value = await inquiryBridgeStatus();
  } catch {
    bridgeStatus.value = null;
  }
}

onMounted(() => {
  void loadBridgeStatus();
  void loadPipelineSummary();
});

async function runImapPoll() {
  if (!imapConsent.value.tenant || !imapConsent.value.compliance) {
    message.warning('须勾选租户授权与合规确认');
    throw new Error('consent_required');
  }
  imapPolling.value = true;
  try {
    const res = await inquiryImapPoll({
      tenant_consent: imapConsent.value.tenant,
      compliance_acknowledged: imapConsent.value.compliance,
      max_messages: 10,
    });
    const data = (res as { data?: typeof res })?.data ?? res;
    const ingested = Number((data as { ingested?: number }).ingested ?? 0);
    const probe = (data as { probe_mode?: string }).probe_mode;
    const hint = probe === 'stub' ? '（开发 stub）' : '';
    message.success(`已入库 ${ingested} 封邮箱询盘${hint}`);
    imapModalOpen.value = false;
    await reload();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'IMAP 拉取失败');
  } finally {
    imapPolling.value = false;
  }
}

async function runBridgeSummary() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  bridgeLoading.value = 'summary';
  try {
    const res = await inquiryBridgeSummary(id);
    bridgeSummary.value = res as BridgeSummary;
    if ((res as BridgeSummary).mode === 'mock') {
      message.warning('当前为开发占位摘要，配置 AI Key 后可生成真实翻译');
    } else {
      message.success('中文摘要已生成');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '摘要失败');
  } finally {
    bridgeLoading.value = '';
  }
}

async function runReplyDraft() {
  const id = String(detailRow.value?.id || '');
  if (!id || !bossReplyZh.value.trim()) return;
  bridgeLoading.value = 'reply';
  try {
    const res = await inquiryReplyDraft(id, bossReplyZh.value.trim());
    replyDraft.value = res as ReplyDraft;
    message.success('英文草稿已生成，请核对后再发');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '草稿失败');
  } finally {
    bridgeLoading.value = '';
  }
}

function copyReplyDraft() {
  const text = replyDraft.value?.body_en || '';
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => message.success('已复制英文'));
}

async function runInquiryOsint() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  ftLoading.value = 'osint';
  try {
    const res = await inquiryOsint(id);
    const data = (res.data || {}) as Record<string, unknown>;
    ftResult.value = {
      title: String(res.summary || '背调结果'),
      body: [
        res.summary,
        data.overall_rating ? `评级：${data.overall_rating}（${data.overall_score ?? '—'}/100）` : '',
        ...(Array.isArray(res.next_actions) ? (res.next_actions as string[]).slice(0, 3) : []),
      ].filter(Boolean).join('\n'),
    };
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '背调失败');
  } finally {
    ftLoading.value = '';
  }
}

async function runInquiryMeddpicc() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  ftLoading.value = 'meddpicc';
  try {
    const data = await inquiryMeddpicc(id);
    const qs = (data.next_questions as string[] | undefined) || [];
    ftResult.value = {
      title: `MEDDPICC · ${data.level || '—'} (${data.score ?? '—'}分)`,
      body: [
        `已填字段 ${data.fields_filled ?? 0} 个`,
        ...qs.slice(0, 4).map((q, i) => `${i + 1}. ${q}`),
      ].join('\n'),
    };
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'MEDDPICC 失败');
  } finally {
    ftLoading.value = '';
  }
}

async function runInquiryPi() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  ftLoading.value = 'pi';
  try {
    const res = await inquiryProforma(id);
    const doc = (res.data || {}) as Record<string, unknown>;
    ftResult.value = {
      title: String(res.summary || 'PI 草稿'),
      body: '已生成 Markdown，请核对 MOQ/单价后下载或复制发送。',
      markdown: typeof doc.markdown === 'string' ? doc.markdown : undefined,
    };
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'PI 生成失败');
  } finally {
    ftLoading.value = '';
  }
}

function downloadPi() {
  if (!ftResult.value?.markdown) return;
  downloadMarkdown(`PI_${String(detailRow.value?.id || 'inquiry').slice(0, 8)}.md`, ftResult.value.markdown);
  message.success('PI 已下载');
}

async function downloadPiDocx() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  try {
    await exportInquiryProformaFile(id, 'docx');
    message.success('PI Word 已下载');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '导出失败');
  }
}

async function downloadPiPdf() {
  const id = String(detailRow.value?.id || '');
  if (!id) return;
  try {
    await exportInquiryProformaFile(id, 'pdf');
    message.success('PI PDF 已下载');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '导出失败');
  }
}

function copyDiscovery() {
  const text = discoveryQs.value.map((q, i) => `${i + 1}. ${q.question}`).join('\n');
  navigator.clipboard.writeText(text).then(() => {
    message.success('追问话术已复制');
  }).catch(() => {
    message.warning(text || '无追问内容');
  });
}

const {
  loading,
  items,
  pagination,
  orderedColumns,
  visibleColumns,
  hiddenColumnKeys,
  query,
  search,
  reset,
  reload,
  onPageChange,
  toggleColumnVisibility,
  moveColumnUp,
  moveColumnDown,
  resetColumnLayout,
} = useYoudingTable<
  Record<string, unknown>,
  { search?: string; status?: string; pipeline_stage?: string }
>({
  columnOrderKey: 'client-inquiry-queue-cols',
  columns: baseColumns,
  defaultQuery: { status: 'pending' },
  fetcher: async (q) => {
    const raw = await apiGet('/inquiries/unified', {
      page: q.page,
      page_size: q.pageSize,
      search: q.search,
      status: q.status,
      pipeline_stage: q.pipeline_stage,
    });
    const { rows, total } = adaptPaginatedResponse<Record<string, unknown>>(raw);
    const levelLabel: Record<string, string> = {
      high: '高',
      medium: '中',
      low: '低',
    };
    const items = rows.map((r) => {
      const level = String(r.intent_level || 'low');
      const score = r.intent_score;
      return {
        ...r,
        intent_label:
          score != null ? `${levelLabel[level] || level} (${score})` : '—',
      };
    });
    return { items, total };
  },
});

function onSearch() {
  void search();
}

function onReset() {
  query.status = 'pending';
  delete query.pipeline_stage;
  void reset();
  void loadPipelineSummary();
}

function exportCsv() {
  if (!items.value.length) {
    message.warning('暂无数据可导出');
    return;
  }
  downloadTableCsv(
    `inquiry_queue_${new Date().toISOString().slice(0, 10)}.csv`,
    ['联系人', '电话', '意向', '状态', '来源', '时间'],
    items.value.map((r) => [
      String(r.name ?? ''),
      String(r.phone ?? ''),
      String(r.intent_label ?? ''),
      String(r.status ?? ''),
      String(r.source_channel ?? ''),
      String(r.created_at ?? ''),
    ]),
  );
  message.success(`已导出 ${items.value.length} 条`);
}
</script>
