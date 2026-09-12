<template>
  <div class="page-container">
    <div class="page-header">
      <h2>行业关键词库与AI组词</h2>
      <p>管理行业关键词，AI智能生成长尾词</p>
    </div>

    <el-card>
      <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
        <el-tab-pane label="行业关键词" name="industry">
          <div class="tab-toolbar">
            <el-input
              v-model="searchQuery"
              placeholder="搜索关键词"
              class="search-input"
              prefix-icon="Search"
            />
            <el-select v-model="categoryFilter" placeholder="分类筛选">
              <el-option label="全部" value="" />
              <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
            </el-select>
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              新增关键词
            </el-button>
          </div>

          <el-table v-loading="loading" :data="keywords" stripe>
            <el-table-column type="selection" width="55" />
            <el-table-column prop="keyword" label="关键词" width="200" />
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag size="small">
                  {{ row.category }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="searchVolume" label="搜索量" width="100" />
            <el-table-column prop="competition" label="竞争度" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="
                    row.competition === '高'
                      ? 'danger'
                      : row.competition === '中'
                        ? 'warning'
                        : 'success'
                  "
                >
                  {{ row.competition }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'danger'">
                  {{ row.status === 1 ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="添加时间" width="150" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
        </el-tab-pane>

        <el-tab-pane label="AI组词" name="generate">
          <div class="ai-generate-panel">
            <el-form :model="generateForm" label-width="120px" class="generate-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="选择县域">
                    <el-select
                      v-model="generateForm.regions"
                      multiple
                      style="width: 100%"
                      placeholder="请选择县域（多选）"
                    >
                      <el-option label="全部县域" value="all" />
                      <el-option
                        v-for="region in regionOptions"
                        :key="region.id"
                        :label="region.name"
                        :value="region.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="关键词分类">
                    <el-select v-model="generateForm.category" style="width: 100%">
                      <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="组词模板">
                <el-select
                  v-model="generateForm.template"
                  style="width: 100%"
                  @change="() => {}"
                >
                  <el-option label="模板1: {县域}+{产品}+厂家" value="region+product+factory" />
                  <el-option label="模板2: {产品}+价格+{县域}" value="product+price+region" />
                  <el-option label="模板3: {县域}+{产品}+哪家好" value="region+product+best" />
                  <el-option label="模板4: {县域}+{产品}+多少钱" value="region+product+price" />
                  <el-option label="自定义模板" value="custom" />
                </el-select>
              </el-form-item>

              <el-form-item label="模板内容">
                <el-input
                  v-model="generateForm.customTemplate"
                  type="textarea"
                  :rows="3"
                  :disabled="generateForm.template !== 'custom'"
                  placeholder="输入自定义模板，如：{县城}+{产品}+厂家"
                />
                <div v-if="generateForm.template !== 'custom'" class="template-preview">
                  <span class="preview-label">生成预览：</span>
                  <span class="preview-value">{{ templatePreview }}</span>
                </div>
              </el-form-item>

              <el-form-item label="生成数量">
                <el-slider
                  v-model="generateForm.count"
                  :min="10"
                  :max="200"
                  :step="10"
                  show-input
                />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="generating" @click="generateKeywords">
                  <el-icon><MagicStick /></el-icon>
                  {{ generating ? 'AI生成中...' : '开始生成' }}
                </el-button>
                <el-button @click="handleBatchAdd">批量添加</el-button>
              </el-form-item>
            </el-form>

            <div v-if="generatedKeywords.length > 0" class="generate-result">
              <div class="result-header">
                <span>生成结果（{{ generatedKeywords.length }}条）</span>
                <el-button size="small" type="success" @click="saveGenerated">保存全部</el-button>
              </div>
              <el-table :data="generatedKeywords" max-height="300">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="keyword" label="生成关键词" />
                <el-table-column prop="region" label="所属县域" width="120" />
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="showAddDialog" title="新增/编辑关键词" width="450px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="关键词" prop="keyword">
          <el-input v-model="editForm.keyword" placeholder="请输入关键词" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="editForm.category">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索量" prop="searchVolume">
          <el-input v-model.number="editForm.searchVolume" type="number" placeholder="预估搜索量" />
        </el-form-item>
        <el-form-item label="竞争度" prop="competition">
          <el-select v-model="editForm.competition">
            <el-option label="低" value="低" />
            <el-option label="中" value="中" />
            <el-option label="高" value="高" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editForm.status" active-value="1" inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { Plus, MagicStick } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '@/api';

const activeTab = ref('industry');
const keywords = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const categoryFilter = ref('');
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const categories = ['保温材料', '防水材料', '涂料', '石材', '管材', '五金配件'];
const regionOptions = ref([]);

const showAddDialog = ref(false);
const editForm = reactive({
  id: null,
  keyword: '',
  category: '保温材料',
  searchVolume: 0,
  competition: '中',
  status: '1',
});

const generateForm = reactive({
  regions: [],
  category: '保温材料',
  template: 'region+product+factory',
  customTemplate: '',
  count: 50,
});

const generating = ref(false);
const generatedKeywords = ref([]);

const templatePreview = computed(() => {
  const templates = {
    'region+product+factory': '如：北京+保温板+厂家',
    'product+price+region': '如：保温板+价格+北京',
    'region+product+best': '如：北京+保温板+哪家好',
    'region+product+price': '如：北京+保温板+多少钱',
  };
  return templates[generateForm.template] || '';
});


const fetchKeywords = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/v1/keywords', {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        keyword: searchQuery.value,
        category: categoryFilter.value,
      },
    });
    keywords.value = res.data.list || [];
    total.value = res.data.total || 0;
  } catch (e) {
    console.error('获取关键词失败:', e);
  } finally {
    loading.value = false;
  }
};

const fetchRegions = async () => {
  try {
    const res = await api.get('/api/v1/regions', { params: { size: 50 } });
    regionOptions.value = res.data.list?.map(r => ({ id: r.id, name: r.name })) || [];
  } catch (e) {
    console.error('获取地域失败:', e);
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchKeywords();
};

const handleTabChange = () => {
  if (activeTab.value === 'generate' && regionOptions.value.length === 0) {
    fetchRegions();
  }
};

const handleEdit = row => {
  editForm.id = row.id;
  editForm.keyword = row.keyword;
  editForm.category = row.category;
  editForm.searchVolume = row.searchVolume;
  editForm.competition = row.competition;
  editForm.status = row.status === 1 ? '1' : '0';
  showAddDialog.value = true;
};

const handleSave = async () => {
  try {
    if (editForm.id) {
      await api.put(`/api/v1/keywords/${editForm.id}`, editForm);
    } else {
      await api.post('/api/v1/keywords', editForm);
    }
    ElMessage.success('保存成功');
    showAddDialog.value = false;
    fetchKeywords();
  } catch (e) {
    ElMessage.error('保存失败');
  }
};

const handleDelete = async row => {
  try {
    await ElMessageBox.confirm('确定删除该关键词吗？', '提示', { type: 'warning' });
    await api.delete(`/api/v1/keywords/${row.id}`);
    ElMessage.success('删除成功');
    fetchKeywords();
  } catch (e) {
    ElMessage.info('已取消删除');
  }
};

const generateKeywords = async () => {
  generating.value = true;
  try {
    const res = await api.post('/api/v1/keywords/generate', {
      regions: generateForm.regions.length > 0 ? generateForm.regions : ['all'],
      category: generateForm.category,
      template:
        generateForm.template === 'custom' ? generateForm.customTemplate : generateForm.template,
      count: generateForm.count,
    });
    generatedKeywords.value = res.data.keywords || [];
    ElMessage.success(`成功生成 ${generatedKeywords.value.length} 个关键词`);
  } catch (e) {
    ElMessage.error('生成失败');
  } finally {
    generating.value = false;
  }
};

const saveGenerated = async () => {
  try {
    const keywordsToSave = generatedKeywords.value.map(k => ({
      keyword: k.keyword,
      category: generateForm.category,
      searchVolume: 0,
      competition: '中',
      status: 1,
    }));
    await api.post('/api/v1/keywords/batch', { keywords: keywordsToSave });
    ElMessage.success('批量保存成功');
    generatedKeywords.value = [];
  } catch (e) {
    ElMessage.error('批量保存失败');
  }
};

const handleBatchAdd = () => {
  ElMessage.info('批量添加功能开发中');
};

onMounted(() => {
  fetchKeywords();
});
</script>

<style scoped lang="scss">
.tab-toolbar {
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

.ai-generate-panel {
  padding: 16px;
}

.generate-form {
  margin-bottom: 20px;
}

.template-preview {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;

  .preview-label {
    color: #909399;
    font-size: 13px;
  }

  .preview-value {
    color: #409eff;
    font-size: 13px;
    margin-left: 8px;
  }
}

.generate-result {
  border: 1px solid #ebeef5;
  border-radius: 4px;

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #fafafa;
    border-bottom: 1px solid #ebeef5;
  }
}
</style>
