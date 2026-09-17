/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated" title="审批管理" subtitle="Agent 操作审批 · 批准 / 拒绝 · 审批历史">
    <template #actions>
      <a-button :loading="loading" @click="loadApprovals">刷新</a-button>
    </template>

    <!-- 待审批列表 -->
    <a-card title="待审批" size="small">
      <template v-if="loading">
        <SkeletonCard variant="table" :rows="4" />
      </template>
      <template v-else>
        <div v-if="pendingList.length" class="approval-grid">
          <div v-for="item in pendingList" :key="item.id" class="approval-card">
            <div class="approval-header">
              <a-tag color="processing">{{ actionTypeLabel(item.action_type) }}</a-tag>
              <span class="approval-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="approval-agent">
              <span class="agent-icon">🤖</span>
              <span class="agent-name">{{ item.agent_name }}</span>
            </div>
            <div class="approval-content">
              {{ item.content }}
            </div>
            <div class="approval-actions">
              <a-button
                type="primary"
                size="small"
                :loading="approvingId === item.id"
                @click="handleApprove(item.id)"
              >
                批准
              </a-button>
              <a-button
                danger
                size="small"
                :loading="rejectingId === item.id"
                @click="openRejectModal(item)"
              >
                拒绝
              </a-button>
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无待审批项" />
      </template>
    </a-card>

    <!-- 已审批历史 -->
    <a-card title="审批历史" size="small" class="mt-4">
      <a-table
        :columns="historyColumns"
        :data-source="historyList"
        :loading="historyLoading"
        :pagination="{ pageSize: 20, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id"
        size="middle"
        :locale="{ emptyText: '暂无审批历史' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action_type'">
            <a-tag color="default">{{ actionTypeLabel(record.action_type) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === 'approved' ? 'success' : 'error'">
              {{ record.status === 'approved' ? '已批准' : '已拒绝' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'reviewer_comment'">
            <span class="comment-text">{{ record.reviewer_comment || '--' }}</span>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'reviewed_at'">
            {{ record.reviewed_at ? formatTime(record.reviewed_at) : '--' }}
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 拒绝评论弹窗 -->
    <a-modal
      v-model:open="rejectModalVisible"
      title="拒绝审批"
      :confirm-loading="rejectingId !== null"
      @ok="handleReject"
      @cancel="resetRejectModal"
      :width="420"
    >
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 17 }">
        <a-form-item label="申请 Agent">
          <span>{{ rejectTarget?.agent_name }}</span>
        </a-form-item>
        <a-form-item label="操作类型">
          <a-tag>{{ actionTypeLabel(rejectTarget?.action_type || '') }}</a-tag>
        </a-form-item>
        <a-form-item label="拒绝原因" required>
          <a-textarea
            v-model:value="rejectComment"
            placeholder="请输入拒绝原因"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { approvalAPI, myPaperclipAPI, type Approval } from '@/api/paperclip'

const loading = ref(false)
const historyLoading = ref(false)
const approvingId = ref<string | null>(null)
const rejectingId = ref<string | null>(null)
const companyId = ref('')

const pendingList = ref<Approval[]>([])
const historyList = ref<Approval[]>([])

const rejectModalVisible = ref(false)
const rejectTarget = ref<Approval | null>(null)
const rejectComment = ref('')

const historyColumns = [
  { title: 'Agent', dataIndex: 'agent_name', key: 'agent_name', width: 120 },
  { title: '操作类型', key: 'action_type', width: 120 },
  { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
  { title: '状态', key: 'status', width: 80 },
  { title: '审批意见', key: 'reviewer_comment', width: 160, ellipsis: true },
  { title: '申请时间', key: 'created_at', width: 160 },
  { title: '审批时间', key: 'reviewed_at', width: 160 },
]

function actionTypeLabel(type: string) {
  const map: Record<string, string> = {
    budget_adjust: '预算调整',
    task_execute: '任务执行',
    agent_create: '创建 Agent',
    agent_delete: '删除 Agent',
    goal_create: '创建目标',
    tool_call: '工具调用',
    external_api: '外部 API 调用',
  }
  return map[type] || type
}

function formatTime(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

async function loadApprovals() {
  loading.value = true
  try {
    if (!companyId.value) {
      const company = await myPaperclipAPI.getCompany()
      if (company?.id) companyId.value = company.id
    }
    if (!companyId.value) return
    pendingList.value = (await approvalAPI.list(companyId.value, { status: 'pending' })) || []
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载待审批列表失败')
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    if (!companyId.value) return
    const all = (await approvalAPI.list(companyId.value)) || []
    historyList.value = all.filter((a) => a.status !== 'pending')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载审批历史失败')
  } finally {
    historyLoading.value = false
  }
}

async function handleApprove(id: string) {
  approvingId.value = id
  try {
    await approvalAPI.approve(id)
    message.success('已批准')
    await Promise.all([loadApprovals(), loadHistory()])
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '批准失败')
  } finally {
    approvingId.value = null
  }
}

function openRejectModal(item: Approval) {
  rejectTarget.value = item
  rejectComment.value = ''
  rejectModalVisible.value = true
}

function resetRejectModal() {
  rejectModalVisible.value = false
  rejectTarget.value = null
  rejectComment.value = ''
}

async function handleReject() {
  if (!rejectComment.value.trim()) {
    message.warning('请输入拒绝原因')
    return
  }
  if (!rejectTarget.value) return
  rejectingId.value = rejectTarget.value.id
  try {
    await approvalAPI.reject(rejectTarget.value.id, rejectComment.value.trim())
    message.success('已拒绝')
    rejectModalVisible.value = false
    await Promise.all([loadApprovals(), loadHistory()])
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '拒绝失败')
  } finally {
    rejectingId.value = null
  }
}

onMounted(async () => {
  await loadApprovals()
  await loadHistory()
})
</script>

<style scoped lang="scss">
.approval-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.approval-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;

  &:hover {
    border-color: #4F6AFF;
    box-shadow: 0 2px 12px rgba(79, 106, 255, 0.08);
  }
}
.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.approval-time {
  font-size: 11px;
  color: #94a3b8;
}
.approval-agent {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.agent-icon {
  font-size: 18px;
}
.agent-name {
  font-weight: 600;
  font-size: 14px;
}
.approval-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
}
.approval-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.mt-4 {
  margin-top: 16px;
}
.comment-text {
  font-size: 12px;
  color: #64748b;
}
</style>
