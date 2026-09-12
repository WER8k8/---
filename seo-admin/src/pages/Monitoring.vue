<template>
  <div class="page-container">
    <div class="page-header">
      <h2>收录监控</h2>
      <p>监控文章在搜索引擎的收录情况和排名</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="收录检测" name="index">
        <div class="page-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索关键词或文章标题"
            class="search-input"
            prefix-icon="Search"
          />
          <el-select v-model="searchEngineFilter" placeholder="搜索引擎">
            <el-option label="全部" value="" />
            <el-option label="百度" value="baidu" />
            <el-option label="搜狗" value="sogou" />
            <el-option label="360" value="360" />
          </el-select>
          <el-select v-model="indexStatusFilter" placeholder="收录状态">
            <el-option label="全部" value="" />
            <el-option label="已收录" value="indexed" />
            <el-option label="未收录" value="not_indexed" />
          </el-select>
          <el-button type="primary" @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>

        <el-card>
          <el-table v-loading="loading" :data="indexingData" stripe :row-key="row => row.id">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="keyword" label="关键词" min-width="150" />
            <el-table-column prop="articleTitle" label="文章标题" min-width="200" />
            <el-table-column prop="platform" label="搜索引擎" width="120">
              <template #default="{ row }">
                <el-tag size="small">
                  {{ getSearchEngineLabel(row.platform) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="isIndexed" label="是否收录" width="100">
              <template #default="{ row }">
                <el-tag :type="row.isIndexed ? 'success' : 'danger'">
                  {{ row.isIndexed ? '已收录' : '未收录' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ranking" label="排名" width="80">
              <template #default="{ row }">
                <span v-if="row.ranking > 0">{{ row.ranking }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="isHomepage" label="首页" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.isHomepage" type="success">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="lastCheckTime" label="检测时间" width="150" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="handleRecheck(row)">重新检测</el-button>
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
      </el-tab-pane>

      <el-tab-pane label="异常预警" name="alerts">
        <div class="page-toolbar">
          <el-select v-model="alertLevelFilter" placeholder="预警级别">
            <el-option label="全部" value="" />
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="提示" value="info" />
          </el-select>
          <el-button type="success" @click="handleMarkAllRead">
            <el-icon><CircleCheck /></el-icon>
            全部标为已读
          </el-button>
        </div>

        <el-card>
          <div v-if="alertsData.length > 0">
            <div
              v-for="alert in alertsData"
              :key="alert.id"
              class="alert-item"
              :class="{ 'alert-read': alert.isRead }"
            >
              <div class="alert-header">
                <el-tag :type="getAlertType(alert.level)" size="small" class="alert-level">
                  {{ getAlertLevelLabel(alert.level) }}
                </el-tag>
                <span class="alert-time">{{ alert.createdAt }}</span>
              </div>
              <h4 class="alert-title">
                {{ alert.title }}
              </h4>
              <p class="alert-desc">
                {{ alert.description }}
              </p>
              <div class="alert-meta">
                <span>关键词: {{ alert.keyword }}</span>
                <span>平台: {{ getSearchEngineLabel(alert.platform) }}</span>
              </div>
              <div class="alert-actions">
                <el-button size="small" @click="handleResolve(alert)">处理</el-button>
                <el-button size="small" @click="handleIgnore(alert)">忽略</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无异常预警" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Refresh, CircleCheck } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '@/api';

const activeTab = ref('index');
const loading = ref(false);
const searchQuery = ref('');
const searchEngineFilter = ref('');
const indexStatusFilter = ref('');
const alertLevelFilter = ref('');

const indexingData = ref([]);
const alertsData = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const getSearchEngineLabel = platform => {
  const labels = {
    baidu: '百度',
    sogou: '搜狗',
    360: '360搜索',
  };
  return labels[platform] || platform;
};

const getAlertType = level => {
  const types = {
    critical: 'danger',
    warning: 'warning',
    info: 'info',
  };
  return types[level] || 'info';
};

const getAlertLevelLabel = level => {
  const labels = {
    critical: '严重',
    warning: '警告',
    info: '提示',
  };
  return labels[level] || level;
};

const fetchIndexingData = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/v1/monitoring/indexing', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    indexingData.value = data.list || [];
    total.value = data.total || 0;
  } catch (e) {
    console.error('获取收录数据失败:', e);
    indexingData.value = [
      {
        id: 1,
        keyword: '北京保温材料厂家',
        articleTitle: '北京保温材料厂家推荐',
        platform: 'baidu',
        isIndexed: true,
        ranking: 3,
        isHomepage: true,
        lastCheckTime: '2024-01-15 10:30:00',
      },
      {
        id: 2,
        keyword: '上海防水材料',
        articleTitle: '上海防水材料价格行情',
        platform: 'baidu',
        isIndexed: true,
        ranking: 8,
        isHomepage: false,
        lastCheckTime: '2024-01-15 10:25:00',
      },
      {
        id: 3,
        keyword: '广州涂料品牌',
        articleTitle: '广州涂料市场分析',
        platform: 'baidu',
        isIndexed: false,
        ranking: -1,
        isHomepage: false,
        lastCheckTime: '2024-01-15 10:20:00',
      },
      {
        id: 4,
        keyword: '深圳石材批发',
        articleTitle: '深圳石材厂家直销',
        platform: 'sogou',
        isIndexed: true,
        ranking: 12,
        isHomepage: false,
        lastCheckTime: '2024-01-15 10:15:00',
      },
      {
        id: 5,
        keyword: '杭州保温板',
        articleTitle: '杭州保温板批发',
        platform: '360',
        isIndexed: true,
        ranking: 5,
        isHomepage: true,
        lastCheckTime: '2024-01-15 10:10:00',
      },
      {
        id: 6,
        keyword: '成都聚氨酯保温',
        articleTitle: '成都聚氨酯保温材料',
        platform: 'baidu',
        isIndexed: false,
        ranking: -1,
        isHomepage: false,
        lastCheckTime: '2024-01-15 10:05:00',
      },
      {
        id: 7,
        keyword: '武汉岩棉板',
        articleTitle: '武汉岩棉板价格',
        platform: 'baidu',
        isIndexed: true,
        ranking: 15,
        isHomepage: false,
        lastCheckTime: '2024-01-15 10:00:00',
      },
      {
        id: 8,
        keyword: '南京挤塑板',
        articleTitle: '南京挤塑板厂家',
        platform: 'sogou',
        isIndexed: true,
        ranking: 7,
        isHomepage: true,
        lastCheckTime: '2024-01-14 16:30:00',
      },
    ];
    total.value = indexingData.value.length;
  } finally {
    loading.value = false;
  }
};

const fetchAlerts = async () => {
  try {
    const res = await fetch('/api/v1/monitoring/alerts', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    alertsData.value = data.list || [];
  } catch (e) {
    console.error('获取预警数据失败:', e);
    alertsData.value = [
      {
        id: 1,
        level: 'critical',
        title: '收录排名大幅下降',
        description: '关键词"北京保温材料厂家"排名从第1位下降至第3位',
        keyword: '北京保温材料厂家',
        platform: 'baidu',
        createdAt: '2024-01-15 09:30:00',
        isRead: false,
      },
      {
        id: 2,
        level: 'warning',
        title: '文章未收录',
        description: '文章"广州涂料市场分析"发布超过24小时仍未被收录',
        keyword: '广州涂料品牌',
        platform: 'baidu',
        createdAt: '2024-01-15 08:15:00',
        isRead: false,
      },
      {
        id: 3,
        level: 'info',
        title: '排名小幅波动',
        description: '关键词"上海防水材料"排名从第7位上升至第8位',
        keyword: '上海防水材料',
        platform: 'baidu',
        createdAt: '2024-01-14 18:00:00',
        isRead: true,
      },
      {
        id: 4,
        level: 'warning',
        title: '收录异常',
        description: '文章"成都聚氨酯保温材料"突然从搜索结果中消失',
        keyword: '成都聚氨酯保温',
        platform: 'baidu',
        createdAt: '2024-01-14 15:30:00',
        isRead: false,
      },
    ];
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchIndexingData();
};

const handleRefresh = () => {
  fetchIndexingData();
  fetchAlerts();
};

const handleRecheck = row => {
  ElMessage.info(`正在重新检测关键词: ${row.keyword}`);
};

const handleMarkAllRead = () => {
  alertsData.value.forEach(alert => (alert.isRead = true));
  ElMessage.success('已全部标为已读');
};

const handleResolve = alert => {
  alert.isRead = true;
  ElMessage.success('已处理预警');
};

const handleIgnore = alert => {
  const index = alertsData.value.indexOf(alert);
  if (index > -1) {
    alertsData.value.splice(index, 1);
  }
  ElMessage.info('已忽略该预警');
};

onMounted(() => {
  fetchIndexingData();
  fetchAlerts();
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

.alert-item {
  padding: 16px;
  border-left: 4px solid #e6a23c;
  background: #fefbf0;
  margin-bottom: 12px;
  transition: all 0.3s;

  &.alert-read {
    background: #f5f5f5;
    border-color: #d9d9d9;
    opacity: 0.7;
  }

  &.alert-critical {
    border-color: #f56c6c;
    background: #fef0f0;
  }

  &.alert-warning {
    border-color: #e6a23c;
    background: #fefbf0;
  }

  &.alert-info {
    border-color: #67c23a;
    background: #f0f9eb;
  }
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-level {
  font-weight: 600;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.alert-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.alert-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.alert-actions {
  display: flex;
  gap: 8px;
}
</style>
