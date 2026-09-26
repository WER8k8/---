/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="合规检查" subtitle="超管内控检查清单 + 外链站点合规工具" surface="elevated">
 <template #actions>
 <router-link to="/seo/compliance">
 <a-button type="primary">SEO 广告法合规</a-button>
 </router-link>
 <router-link to="/compliance">
 <a-button>合规治理中心</a-button>
 </router-link>
 </template>
 <div class="page p-6 space-y-4">
 <a-alert
 type="info"
 show-icon
 message="分工说明"
 description="超管侧清单走 /compliance/rules 持久化；敏感词扫描与页面合规仍以 SEO 矩阵与合规中心为准。"
 />

 <a-card title="内控检查项" size="small">
 <a-space wrap style="margin-bottom: 12px">
 <a-input
 v-model:value="title"
 placeholder="检查项标题"
 style="width: 260px"
 allow-clear
 />
 <a-button type="primary" :loading="saving" @click="add">添加</a-button>
 </a-space>
 <a-table
 :columns="cols"
 :data-source="rows"
 row-key="id"
 size="small"
 :loading="loading"
 :pagination="false"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'status'">
 <a-tag :color="record.status === 'done' ? 'green' : 'blue'">
 {{ record.status === 'done' ? '已完成' : '待办' }}
 </a-tag>
 </template>
 <template v-else-if="column.key === 'actions'">
 <a-button
 type="link"
 size="small"
 :loading="togglingId === record.id"
 @click="toggle(record as CheckRow)"
 >
 {{ record.status === 'done' ? '标为待办' : '标为完成' }}
 </a-button>
 <a-popconfirm title="确认删除该检查项？" @confirm="remove(record.id)">
 <a-button type="link" danger size="small" :loading="deletingId === record.id">
 删除
 </a-button>
 </a-popconfirm>
 </template>
 </template>
 </a-table>
 </a-card>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';

interface CheckRow {
 id: string;
 title: string;
 severity: string;
 status: 'open' | 'done';
 note: string;
 updatedAt: string;
}

const title = ref('');
const rows = ref<CheckRow[]>([]);
const loading = ref(false);
const saving = ref(false);
const togglingId = ref<string | null>(null);
const deletingId = ref<string | null>(null);

const cols: TableColumnsType = [
 { title: '检查项', dataIndex: 'title', key: 'title', ellipsis: true },
 { title: '等级', dataIndex: 'severity', key: 'severity', width: 90 },
 { title: '状态', key: 'status', width: 100 },
 { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
 { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 170 },
 { title: '操作', key: 'actions', width: 180 },
];

function mapRule(raw: any): CheckRow {
 const desc = String(raw.description ?? '');
 const done = desc.includes('[done]');
 return {
 id: String(raw.id),
 title: String(raw.rule_name ?? ''),
 severity: String(raw.severity ?? 'low'),
 status: done ? 'done' : 'open',
 note: desc.replace('[done]', '').trim(),
 updatedAt: String(raw.created_at ?? raw.updated_at ?? '').slice(0, 19).replace('T', ' ') || '-',
 };
}

async function load() {
 loading.value = true;
 try {
 const res = await apiGet<any>('/compliance/rules', { page: 1, page_size: 50, rule_type: 'internal_check' });
 const items = res?.items ?? res?.data?.items ?? (Array.isArray(res) ? res : []);
 rows.value = items.map(mapRule);
 } catch (e: any) {
 message.error(e?.message || '合规检查项加载失败');
 rows.value = [];
 } finally {
 loading.value = false;
 }
}

async function add() {
 const t = title.value.trim();
 if (!t) {
 message.warning('请输入标题');
 return;
 }
 saving.value = true;
 try {
 await apiPost('/compliance/rules', {
 rule_name: t,
 rule_type: 'internal_check',
 keywords: [t],
 severity: 'low',
 description: '',
 is_active: true,
 });
 title.value = '';
 message.success('检查项已保存');
 await load();
 } catch (e: any) {
 message.error(e?.message || '检查项保存失败');
 } finally {
 saving.value = false;
 }
}

async function toggle(row: CheckRow) {
 togglingId.value = row.id;
 const nextDone = row.status !== 'done';
 try {
 const desc = nextDone ? `[done] ${row.note}`.trim() : row.note;
 await apiPut(`/compliance/rules/${row.id}`, {
 rule_name: row.title,
 rule_type: 'internal_check',
 keywords: [row.title],
 severity: row.severity,
 description: desc,
 is_active: true,
 });
 message.success(nextDone ? '已标为完成' : '已标为待办');
 await load();
 } catch (e: any) {
 message.error(e?.message || '状态更新失败');
 } finally {
 togglingId.value = null;
 }
}

async function remove(id: string) {
 deletingId.value = id;
 try {
 await apiDelete(`/compliance/rules/${id}`);
 message.success('已删除');
 await load();
 } catch (e: any) {
 message.error(e?.message || '删除失败');
 } finally {
 deletingId.value = null;
 }
}

onMounted(() => {
 void load();
});
</script>
