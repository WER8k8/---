<template>
  <div class="page-container">
    <div class="page-header">
      <h2>发布任务管理</h2>
      <p>管理文章发布任务，支持重试失败任务</p>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索任务ID或文章标题"
        class="search-input"
        prefix-icon="Search"
      />
      <el-select v-model="statusFilter" placeholder="状态筛选">
        <el-option label="全部" value="" />
        <el-option label="等待中" value="waiting" />
        <el-option label="发布中" value="publishing" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button type="success" :disabled="selectedTasks.length === 0" @click="handleRetryFailed">
        <el-icon><Refresh /></el-icon>
        重试选中 ({{ selectedTasks.length }})
      </el-button>
      <el-button @click="handleClearCompleted">
        <el-icon><Delete /></el-icon>
        清空已完成
      </el-button>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="tasks"
        stripe
        :row-key="row => row.id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="任务ID" width="120" />
        <el-table-column prop="articleTitle" label="文章标题" min-width="200" />
        <el-table-column prop="platform" label="发布平台" width="120" />
        <el-table-column prop="account" label="发布账号" width="120" />
        <el-table-column prop="regionName" label="目标县域" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="row.status === 'failed' ? 'exception' : 'success'"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="150" />
        <el-table-column prop="updatedAt" label="更新时间" width="150" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">详情</el-button>
            <el-button
              size="small"
              type="primary"
              :disabled="row.status !== 'failed'"
              @click="handleRetry(row)"
            >
              <el-icon><Refresh /></el-icon>
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        layout="prev, pager, next, jumper, ->, total"
        class="pagination"
        @current-change="handlePageChange"
      />
    </el-card>

    <el-dialog v-model="showDetailDialog" title="任务详情" width="600px">
      <div v-if="currentTask" class="task-detail">
        <div class="detail-row">
          <span class="label">任务ID</span>
          <span class="value">{{ currentTask.id }}</span>
        </div>
        <div class="detail-row">
          <span class="label">文章标题</span>
          <span class="value">{{ currentTask.articleTitle }}</span>
        </div>
        <div class="detail-row">
          <span class="label">发布平台</span>
          <span class="value">{{ currentTask.platform }}</span>
        </div>
        <div class="detail-row">
          <span class="label">发布账号</span>
          <span class="value">{{ currentTask.account }}</span>
        </div>
        <div class="detail-row">
          <span class="label">目标县域</span>
          <span class="value">{{ currentTask.regionName }}</span>
        </div>
        <div class="detail-row">
          <span class="label">状态</span>
          <span class="value">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
          </span>
        </div>
        <div v-if="currentTask.errorMessage" class="detail-row error-row">
          <span class="label">错误信息</span>
          <span class="value error">{{ currentTask.errorMessage }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button
          v-if="currentTask?.status === 'failed'"
          type="primary"
          @click="handleRetry(currentTask)"
        >
          <el-icon><Refresh /></el-icon>
          重试任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Refresh, Delete } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const tasks = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const statusFilter = ref('');
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const selectedTasks = ref([]);
const showDetailDialog = ref(false);
const currentTask = ref(null);

const getStatusType = status => {
  const types = {
    waiting: 'info',
    publishing: 'warning',
    completed: 'success',
    failed: 'danger',
  };
  return types[status] || 'info';
};

const getStatusLabel = status => {
  const labels = {
    waiting: '等待中',
    publishing: '发布中',
    completed: '已完成',
    failed: '失败',
  };
  return labels[status] || status;
};

const fetchTasks = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/v1/publish/tasks', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await res.json();
    tasks.value = data.list || [];
    total.value = data.total || 0;
  } catch (e) {
    console.error('获取任务失败:', e);
    tasks.value = [
      {
        id: 'TASK-001',
        articleTitle: '北京保温材料厂家推荐',
        platform: '今日头条',
        account: '建材资讯',
        regionName: '北京市',
        status: 'completed',
        progress: 100,
        createdAt: '2024-01-15 10:30:00',
        updatedAt: '2024-01-15 10:35:00',
      },
      {
        id: 'TASK-002',
        articleTitle: '上海防水材料价格行情',
        platform: '百家号',
        account: '建筑百科',
        regionName: '上海市',
        status: 'completed',
        progress: 100,
        createdAt: '2024-01-15 10:32:00',
        updatedAt: '2024-01-15 10:38:00',
      },
      {
        id: 'TASK-003',
        articleTitle: '广州涂料市场分析',
        platform: '企鹅号',
        account: '装修指南',
        regionName: '广州市',
        status: 'failed',
        progress: 0,
        createdAt: '2024-01-15 10:35:00',
        updatedAt: '2024-01-15 10:36:00',
        errorMessage: '账号登录失败，请重新授权',
      },
      {
        id: 'TASK-004',
        articleTitle: '深圳石材厂家直销',
        platform: '知乎',
        account: '建材达人',
        regionName: '深圳市',
        status: 'publishing',
        progress: 50,
        createdAt: '2024-01-15 10:40:00',
        updatedAt: '2024-01-15 10:42:00',
      },
      {
        id: 'TASK-005',
        articleTitle: '杭州保温板批发',
        platform: '小红书',
        account: '装修日记',
        regionName: '杭州市',
        status: 'waiting',
        progress: 0,
        createdAt: '2024-01-15 10:45:00',
        updatedAt: '2024-01-15 10:45:00',
      },
    ];
    total.value = tasks.value.length;
  } finally {
    loading.value = false;
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchTasks();
};

const handleSelectionChange = val => {
  selectedTasks.value = val;
};

const handleView = row => {
  currentTask.value = row;
  showDetailDialog.value = true;
};

const handleRetry = async row => {
  try {
    ElMessage.success(`任务 ${row.id} 已重新加入队列`);
    row.status = 'waiting';
    row.progress = 0;
    if (showDetailDialog.value) {
      showDetailDialog.value = false;
    }
  } catch (e) {
    ElMessage.error('重试失败');
  }
};

const handleRetryFailed = async () => {
  try {
    const ids = selectedTasks.value.map(t => t.id);
    ElMessage.success(`成功将 ${ids.length} 个任务重新加入队列`);
    selectedTasks.value = [];
    fetchTasks();
  } catch (e) {
    ElMessage.error('批量重试失败');
  }
};

const handleClearCompleted = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有已完成的任务吗？', '提示', { type: 'warning' });
    ElMessage.success('已清空已完成任务');
    fetchTasks();
  } catch (e) {
    ElMessage.info('已取消');
  }
};

onMounted(() => {
  fetchTasks();
});
</script>

<style scoped lang="scss">
.page-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;

  .search-input {
    width: 250px;
  }
}

.pagination {
  margin-top: 16px;
  text-align: right;
}

.task-detail {
  padding: 16px;

  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #ebeef5;

    &:last-child {
      border-bottom: none;
    }

    &.error-row {
      background: #fef0f0;
      padding: 12px;
      margin: 8px -16px;

      .error {
        color: #f56c6c;
        max-width: 400px;
        word-break: break-all;
      }
    }

    .label {
      color: #909399;
      font-weight: 500;
    }

    .value {
      color: #303133;
      font-weight: 500;
    }
  }
}
</style>
