<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统日志</h2>
      <p>查看操作日志和登录日志</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="操作日志" name="operations">
        <div class="page-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索操作人、模块或描述"
            class="search-input"
            prefix-icon="Search"
          />
          <el-select v-model="moduleFilter" placeholder="模块">
            <el-option label="全部" value="" />
            <el-option label="文章管理" value="articles" />
            <el-option label="关键词" value="keywords" />
            <el-option label="模板管理" value="templates" />
            <el-option label="平台管理" value="platforms" />
            <el-option label="系统设置" value="settings" />
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="yyyy-MM-dd"
          />
          <el-button type="primary" @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-card>
          <el-table v-loading="loading" :data="operationLogs" stripe :row-key="row => row.id">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="操作人" width="120" />
            <el-table-column prop="module" label="模块" width="120">
              <template #default="{ row }">
                <el-tag size="small">
                  {{ getModuleLabel(row.module) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="操作" width="100">
              <template #default="{ row }">
                <el-tag :type="getActionType(row.action)" size="small">
                  {{ getActionLabel(row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="250" />
            <el-table-column prop="ipAddress" label="IP地址" width="150" />
            <el-table-column prop="userAgent" label="设备" width="180" />
            <el-table-column prop="createdAt" label="时间" width="180" />
          </el-table>

          <el-pagination
            v-if="operationTotal > 0"
            :total="operationTotal"
            :page-size="pageSize"
            :current-page="currentPage"
            layout="prev, pager, next, jumper, ->, total"
            class="pagination"
            @current-change="handlePageChange"
          />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="登录日志" name="logins">
        <div class="page-toolbar">
          <el-input
            v-model="loginSearchQuery"
            placeholder="搜索用户名或IP"
            class="search-input"
            prefix-icon="Search"
          />
          <el-select v-model="loginResultFilter" placeholder="登录结果">
            <el-option label="全部" value="" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-date-picker
            v-model="loginDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="yyyy-MM-dd"
          />
          <el-button type="primary" @click="refreshLoginLogs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-card>
          <el-table v-loading="loginLoading" :data="loginLogs" stripe :row-key="row => row.id">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="ipAddress" label="IP地址" width="150" />
            <el-table-column prop="device" label="设备" width="200" />
            <el-table-column prop="location" label="位置" width="120" />
            <el-table-column prop="loginResult" label="结果" width="100">
              <template #default="{ row }">
                <el-tag :type="row.loginResult ? 'success' : 'danger'">
                  {{ row.loginResult ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="failReason" label="失败原因" min-width="150">
              <template #default="{ row }">
                <span v-if="row.failReason" class="fail-reason">{{ row.failReason }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="时间" width="180" />
          </el-table>

          <el-pagination
            v-if="loginTotal > 0"
            :total="loginTotal"
            :page-size="loginPageSize"
            :current-page="loginCurrentPage"
            layout="prev, pager, next, jumper, ->, total"
            class="pagination"
            @current-change="handleLoginPageChange"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Refresh } from '@element-plus/icons-vue';
import api from '@/api';

const activeTab = ref('operations');
const loading = ref(false);
const loginLoading = ref(false);

const searchQuery = ref('');
const moduleFilter = ref('');
const dateRange = ref([]);
const currentPage = ref(1);
const pageSize = ref(20);
const operationTotal = ref(0);

const loginSearchQuery = ref('');
const loginResultFilter = ref('');
const loginDateRange = ref([]);
const loginCurrentPage = ref(1);
const loginPageSize = ref(20);
const loginTotal = ref(0);

const operationLogs = ref([]);
const loginLogs = ref([]);

const getModuleLabel = module => {
  const labels = {
    articles: '文章管理',
    keywords: '关键词',
    templates: '模板管理',
    platforms: '平台管理',
    settings: '系统设置',
    regions: '地域管理',
    tasks: '任务管理',
  };
  return labels[module] || module;
};

const getActionType = action => {
  const types = {
    create: 'success',
    update: 'warning',
    delete: 'danger',
    view: 'info',
    import: 'success',
    export: 'info',
  };
  return types[action] || 'info';
};

const getActionLabel = action => {
  const labels = {
    create: '新增',
    update: '修改',
    delete: '删除',
    view: '查看',
    import: '导入',
    export: '导出',
    publish: '发布',
    generate: '生成',
  };
  return labels[action] || action;
};

const fetchOperationLogs = async () => {
  loading.value = true;
  try {
    const data = await api.get('/api/v1/logs/operations');
    operationLogs.value = data.list || [];
    operationTotal.value = data.total || 0;
  } catch (e) {
    console.error('获取操作日志失败:', e);
    operationLogs.value = [];
    operationTotal.value = 0;
  } finally {
    loading.value = false;
  }
};

const fetchLoginLogs = async () => {
  loginLoading.value = true;
  try {
    const data = await api.get('/api/v1/logs/logins');
    loginLogs.value = data.list || [];
    loginTotal.value = data.total || 0;
  } catch (e) {
    console.error('获取登录日志失败:', e);
    loginLogs.value = [];
    loginTotal.value = 0;
  } finally {
    loginLoading.value = false;
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchOperationLogs();
};

const handleLoginPageChange = page => {
  loginCurrentPage.value = page;
  fetchLoginLogs();
};

const handleRefresh = () => {
  fetchOperationLogs();
};

const refreshLoginLogs = () => {
  fetchLoginLogs();
};

onMounted(() => {
  fetchOperationLogs();
  fetchLoginLogs();
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

.fail-reason {
  color: #f56c6c;
  font-size: 12px;
}
</style>
