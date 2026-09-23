/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="AI 任务看板" subtitle="跟踪发布任务状态，与调度中心生产任务分工" surface="elevated">
 <template #actions>
 <router-link to="/admin/scheduler-hub">
 <a-button type="primary">调度中心</a-button>
 </router-link>
 <router-link to="/admin/ai-engine">
 <a-button>AI 引擎概览</a-button>
 </router-link>
 </template>
 <div class="page p-6 space-y-4">
 <a-card title="新建任务" size="small">
 <a-alert
 type="info"
 show-icon
 message="未接后端·本机草稿"
 description="发布任务创建需内容/平台/账号绑定，请到「多平台发布」发起；此处仅查看与重试已有任务。"
 style="margin-bottom: 12px"
 />
 <a-space wrap style="margin-bottom: 12px">
 <a-input v-model:value="title" placeholder="任务标题" style="width: 240px" allow-clear disabled />
 <a-select v-model:value="status" style="width: 120px" disabled>
 <a-select-option value="pending">待处理</a-select-option>
 <a-select-option value="running">进行中</a-select-option>
 <a-select-option value="done">完成</a-select-option>
 </a-select>
 <a-button type="primary" disabled>添加</a-button>
 </a-space>
 <a-input v-model:value="note" placeholder="备注（可选）" allow-clear disabled />
 </a-card>

 <a-table
 :columns="cols"
 :data-source="tasks"
 row-key="id"
 size="small"
 :loading="loading"
 :pagination="pagination"
 @change="handleTableChange"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'status'">
 <a-tag :color="tagColor(record.status)">
 {{ statusLabel(record.status) }}
 </a-tag>
 </template>
 <template v-else-if="column.key === 'actions'">
 <a-button
 type="link"
 size="small"
 :loading="retryingId === record.id"
 @click="retry(record)"
 >
 重试
 </a-button>
 <a-popconfirm title="确认删除该任务？" @confirm="remove(record.id)">
 <a-button type="link" danger size="small" :loading="deletingId === record.id">
 删除
 </a-button>
 </a-popconfirm>
 </template>
 </template>
 </a-table>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';

interface PublishTaskRow {
 id: string;
 title: string;
 status: string;
 note: string;
 updatedAt: string;
 platform: string;
}

const title = ref('');
const note = ref('');
const status = ref<'pending' | 'running' | 'done'>('pending');
const tasks = ref<PublishTaskRow[]>([]);
const loading = ref(false);
const retryingId = ref<string | null>(null);
const deletingId = ref<string | null>(null);
const pagination = reactive({ current: 1, pageSize: 20, total: 0 });

const cols: TableColumnsType = [
 { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
 { title: '平台', dataIndex: 'platform', key: 'platform', width: 120 },
 { title: '状态', key: 'status', width: 110 },
 { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
 { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 170 },
 { title: '操作', key: 'actions', width: 160 },
];

function tagColor(s: string) {
 if (s === 'success' || s === 'done') return 'green';
 if (s === 'failed') return 'red';
 if (s === 'running' || s === 'pending') return 'blue';
 return 'default';
}

function statusLabel(s: string) {
 if (s === 'success') return '成功';
 if (s === 'failed') return '失败';
 if (s === 'running') return '进行中';
 if (s === 'pending') return '待处理';
 return s || '-';
}

function mapTask(raw: any): PublishTaskRow {
 return {
 id: String(raw.id ?? ''),
 title: String(raw.title ?? raw.platform ?? '未命名任务'),
 status: String(raw.status ?? 'pending'),
 note: String(raw.message ?? raw.publish_type ?? ''),
 updatedAt: String(raw.published_at ?? raw.created_at ?? ''),
 platform: String(raw.platform ?? '-'),
 };
}

async function load() {
 loading.value = true;
 try {
 const res = await apiGet<any>('/publish-tasks', {
 page: pagination.current,
 page_size: pagination.pageSize,
 });
 const items = res?.items ?? (Array.isArray(res) ? res : []);
 tasks.value = items.map(mapTask);
 pagination.total = Number(res?.total ?? tasks.value.length);
 } catch (e: any) {
 message.error(e?.message || '发布任务加载失败');
 tasks.value = [];
 pagination.total = 0;
 } finally {
 loading.value = false;
 }
}

function handleTableChange(pag: any) {
 pagination.current = pag.current ?? 1;
 pagination.pageSize = pag.pageSize ?? 20;
 void load();
}

async function retry(row: PublishTaskRow) {
 retryingId.value = row.id;
 try {
 await apiPost(`/publish-tasks/${row.id}/retry`);
 message.success('已重新排队');
 await load();
 } catch (e: any) {
 message.error(e?.message || '重试失败');
 } finally {
 retryingId.value = null;
 }
}

async function remove(id: string) {
 deletingId.value = id;
 try {
 await apiDelete(`/publish-tasks/${id}`);
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
