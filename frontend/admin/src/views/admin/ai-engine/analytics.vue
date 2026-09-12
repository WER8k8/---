<template>
  <YdPage title="AI 分析" subtitle="聚合全站 SEO 仪表盘指标，支持本地分析备忘" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button>调度中心</a-button>
      </router-link>
      <router-link to="/dashboard">
        <a-button type="primary">数据概览</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-alert
      v-if="dashError"
      type="warning"
      show-icon
      :message="dashError"
      closable
      @close="dashError = ''"
    />

    <template v-if="loading">
      <div class="flex flex-wrap gap-4">
        <div v-for="i in 4" :key="i" class="flex-1 min-w-[200px]">
          <SkeletonCard variant="kpi" />
        </div>
      </div>
    </template>
    <template v-else>
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="c in statCards"
          :key="c.key"
          :xs="12"
          :md="6"
        >
          <a-card size="small">
            <div class="stat-label">
              {{ c.label }}
            </div>
            <div class="stat-value">
              {{ c.value }}
            </div>
          </a-card>
        </a-col>
      </a-row>
    </template>

    <a-card
      title="分析备忘（本地）"
      size="small"
    >
      <a-textarea
        v-model:value="memo"
        :rows="4"
        placeholder="记录观察、异常与后续实验"
      />
      <a-button
        type="primary"
        style="margin-top: 8px"
        @click="saveMemo"
      >
        保存备忘
      </a-button>
      <a-divider />
      <div
        v-if="memos.length"
        class="memo-list"
      >
        <div
          v-for="m in memos"
          :key="m.id"
          class="memo-row"
        >
          <span class="memo-time">{{ m.updatedAt }}</span>
          <p>{{ m.text }}</p>
          <a-button
            type="link"
            danger
            size="small"
            @click="removeMemo(m.id)"
          >
            删除
          </a-button>
        </div>
      </div>
      <a-empty
        v-else
        description="暂无备忘"
      />
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { seoAPI, unwrapApiData } from '@/api';
import { useAdminWorkspace } from '@/composables/useAdminWorkspace';

const loading = ref(false);
const dash = ref<Record<string, any>>({});
const memo = ref('');
const { genId } = useAdminWorkspace();

const MEMO_KEY = 'admin-ai-analytics-memos';

interface MemoRow {
  id: string;
  text: string;
  updatedAt: string;
}

const memos = ref<MemoRow[]>([]);

function loadMemos() {
  try {
    const raw = localStorage.getItem(MEMO_KEY);
    memos.value = raw ? (JSON.parse(raw) as MemoRow[]) : [];
  } catch {
    memos.value = [];
  }
}

function persistMemos() {
  localStorage.setItem(MEMO_KEY, JSON.stringify(memos.value));
}

const statCards = computed(() => {
  const d = dash.value;
  return [
    { key: 'p', label: '产品总数', value: d.total_products ?? '—' },
    { key: 'i', label: '询盘', value: d.total_inquiries ?? '—' },
    { key: 'a', label: 'AI 优化页', value: d.ai_optimized_pages ?? '—' },
    { key: 'k', label: '关键词', value: d.total_keywords ?? '—' },
  ];
});

const dashError = ref('');

async function loadDash() {
  loading.value = true;
  dashError.value = '';
  try {
    const res = await seoAPI.dashboard({ range: 'week' });
    dash.value = unwrapApiData<Record<string, any>>(res) || {};
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } }; message?: string };
    dashError.value = err?.response?.data?.message || err?.message || '加载仪表盘失败';
  } finally {
    loading.value = false;
  }
}

function saveMemo() {
  const t = memo.value.trim();
  if (!t) {
    message.warning('请输入内容');
    return;
  }
  memos.value.unshift({
    id: genId(),
    text: t,
    updatedAt: new Date().toLocaleString(),
  });
  memo.value = '';
  persistMemos();
  message.success('已保存');
}

function removeMemo(id: string) {
  memos.value = memos.value.filter((m) => m.id !== id);
  persistMemos();
}

onMounted(() => {
  loadMemos();
  loadDash();
});
</script>

<style scoped>
.stat-label {
  font-size: 12px;
  color: #64748b;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin-top: 4px;
}
.memo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.memo-row {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  background: #f8fafc;
}
.memo-time {
  font-size: 12px;
  color: #94a3b8;
}
.memo-row p {
  margin: 4px 0 0;
  white-space: pre-wrap;
}
</style>
