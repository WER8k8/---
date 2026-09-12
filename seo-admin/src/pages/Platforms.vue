<template>
  <div class="page-container">
    <div class="page-header">
      <h2>多平台账号管理与AI分发中心</h2>
      <p>管理各分发平台账号，配置AI自动分发策略</p>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索平台名称"
        class="search-input"
        prefix-icon="Search"
      />
      <el-select v-model="categoryFilter" placeholder="平台分类">
        <el-option label="全部" value="" />
        <el-option label="资讯平台" value="news" />
        <el-option label="自媒体" value="media" />
        <el-option label="论坛社区" value="forum" />
        <el-option label="问答平台" value="qa" />
      </el-select>
      <el-button type="primary" @click="showAddAccountDialog = true">
        <el-icon><Plus /></el-icon>
        添加账号
      </el-button>
    </div>

    <el-card>
      <el-table v-loading="loading" :data="platforms" stripe>
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="平台名称" width="150">
          <template #default="{ row }">
            <div class="platform-name">
              <el-icon :size="20">
                {{ getPlatformIcon(row.name) }}
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="平台分类" width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accountCount" label="账号数量" width="100" />
        <el-table-column prop="hasApi" label="API支持" width="100">
          <template #default="{ row }">
            <el-tag :type="row.hasApi ? 'success' : 'info'">
              {{ row.hasApi ? '支持' : '不支持' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dailyLimit" label="每日上限" width="100" />
        <el-table-column prop="todayPublished" label="今日发布" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'danger'">
              {{ row.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleManageAccounts(row)">管理账号</el-button>
            <el-button size="small" @click="handleConfigure(row)">配置</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddAccountDialog" title="添加平台账号" width="500px">
      <el-form :model="addAccountForm" label-width="100px">
        <el-form-item label="选择平台">
          <el-select v-model="addAccountForm.platformId" style="width: 100%">
            <el-option v-for="p in platformOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号名称">
          <el-input v-model="addAccountForm.accountName" placeholder="输入账号昵称" />
        </el-form-item>
        <el-form-item label="账号状态">
          <el-switch
            v-model="addAccountForm.status"
            active-value="enabled"
            inactive-value="disabled"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addAccountForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddAccountDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddAccount">确认添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAccountsDialog" title="账号列表" width="600px">
      <div v-if="currentPlatform">
        <h4>{{ currentPlatform.name }} - 账号管理</h4>
        <el-table :data="currentPlatform.accounts" stripe>
          <el-table-column type="selection" width="55" />
          <el-table-column prop="accountName" label="账号名称" />
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="row.status === 'enabled' ? 'success' : 'danger'">
                {{ row.status === 'enabled' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="todayCount" label="今日发布" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button size="small">编辑</el-button>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showAccountsDialog = false">关闭</el-button>
        <el-button
          type="primary"
          @click="
            showAddAccountDialog = true;
            showAccountsDialog = false;
          "
        >
          添加账号
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { Plus, MapLocation, ChatSquare, Document, Help } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const platforms = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const categoryFilter = ref('');

const platformOptions = ref([]);
const showAddAccountDialog = ref(false);
const showAccountsDialog = ref(false);
const currentPlatform = ref(null);

const addAccountForm = reactive({
  platformId: '',
  accountName: '',
  status: 'enabled',
  remark: '',
});

const getPlatformIcon = name => {
  const icons = {
    今日头条: MapLocation,
    百家号: Document,
    企鹅号: ChatSquare,
    知乎: Help,
    小红书: MapLocation,
    微信公众号: ChatSquare,
  };
  return icons[name] || MapLocation;
};

const getCategoryLabel = category => {
  const labels = {
    news: '资讯平台',
    media: '自媒体',
    forum: '论坛社区',
    qa: '问答平台',
  };
  return labels[category] || category;
};

const fetchPlatforms = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/v1/platforms');
    const data = await res.json();
    platforms.value = data.list || [];
    platformOptions.value = platforms.value.map(p => ({ id: p.id, name: p.name }));
  } catch (e) {
    console.error('获取平台失败:', e);
    platforms.value = [
      {
        id: 1,
        name: '今日头条',
        category: 'news',
        accountCount: 3,
        hasApi: true,
        dailyLimit: 50,
        todayPublished: 23,
        status: 'enabled',
        accounts: [],
      },
      {
        id: 2,
        name: '百家号',
        category: 'news',
        accountCount: 2,
        hasApi: true,
        dailyLimit: 30,
        todayPublished: 15,
        status: 'enabled',
        accounts: [],
      },
      {
        id: 3,
        name: '企鹅号',
        category: 'media',
        accountCount: 4,
        hasApi: true,
        dailyLimit: 40,
        todayPublished: 18,
        status: 'enabled',
        accounts: [],
      },
      {
        id: 4,
        name: '知乎',
        category: 'qa',
        accountCount: 2,
        hasApi: true,
        dailyLimit: 20,
        todayPublished: 8,
        status: 'enabled',
        accounts: [],
      },
      {
        id: 5,
        name: '小红书',
        category: 'media',
        accountCount: 1,
        hasApi: false,
        dailyLimit: 10,
        todayPublished: 5,
        status: 'enabled',
        accounts: [],
      },
      {
        id: 6,
        name: '微信公众号',
        category: 'media',
        accountCount: 2,
        hasApi: true,
        dailyLimit: 8,
        todayPublished: 3,
        status: 'enabled',
        accounts: [],
      },
    ];
    platformOptions.value = platforms.value.map(p => ({ id: p.id, name: p.name }));
  } finally {
    loading.value = false;
  }
};

const handleManageAccounts = row => {
  currentPlatform.value = row;
  showAccountsDialog.value = true;
};

const handleConfigure = row => {
  ElMessage.info(`配置 ${row.name} 的分发策略`);
};

const handleAddAccount = () => {
  ElMessage.success('账号添加成功');
  showAddAccountDialog.value = false;
};

onMounted(() => {
  fetchPlatforms();
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

.platform-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
