<template>
  <div class="page-container">
    <div class="page-header">
      <h2>文章管理</h2>
      <p>管理AI生成的文章，支持批量发布和状态管理</p>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文章标题"
        class="search-input"
        prefix-icon="Search"
      />
      <el-select v-model="statusFilter" placeholder="状态筛选">
        <el-option label="全部" value="" />
        <el-option label="待发布" value="pending" />
        <el-option label="已发布" value="published" />
        <el-option label="发布失败" value="failed" />
      </el-select>
      <el-select v-model="regionFilter" placeholder="县域筛选">
        <el-option label="全部" value="" />
        <el-option v-for="r in regionOptions" :key="r.id" :label="r.name" :value="r.id" />
      </el-select>
      <el-button type="primary" @click="showGenerateDialog = true">
        <el-icon><MagicStick /></el-icon>
        AI生成文章
      </el-button>
      <el-button
        type="success"
        :disabled="selectedArticles.length === 0"
        @click="handleBatchPublish"
      >
        <el-icon><ArrowRightBold /></el-icon>
        批量发布 ({{ selectedArticles.length }})
      </el-button>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="articles"
        stripe
        :row-key="row => row.id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="文章标题" min-width="200">
          <template #default="{ row }">
            <a href="#" class="title-link" @click.stop="handleView(row)">{{ row.title }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="regionName" label="所属县域" width="120" />
        <el-table-column prop="keyword" label="关键词" width="120" />
        <el-table-column prop="duplicateRate" label="重复率" width="80">
          <template #default="{ row }">
            <el-tag
              :type="
                row.duplicateRate <= 10 ? 'success' : row.duplicateRate <= 30 ? 'warning' : 'danger'
              "
            >
              {{ row.duplicateRate }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="complianceStatus" label="合规状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.complianceStatus === 'pass'
                  ? 'success'
                  : row.complianceStatus === 'warning'
                    ? 'warning'
                    : 'danger'
              "
            >
              {{
                row.complianceStatus === 'pass'
                  ? '合规'
                  : row.complianceStatus === 'warning'
                    ? '待审核'
                    : '违规'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="发布状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'published'
                  ? 'success'
                  : row.status === 'pending'
                    ? 'warning'
                    : 'danger'
              "
            >
              {{
                row.status === 'published'
                  ? '已发布'
                  : row.status === 'pending'
                    ? '待发布'
                    : '发布失败'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="wordCount" label="字数" width="80" />
        <el-table-column prop="createdAt" label="创建时间" width="150" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button
              size="small"
              type="primary"
              :disabled="row.status === 'published'"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
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
    </el-card>

    <el-dialog v-model="showGenerateDialog" title="AI生成文章" width="600px">
      <el-form :model="generateForm" label-width="120px">
        <el-form-item label="选择县域">
          <el-select
            v-model="generateForm.regionIds"
            multiple
            style="width: 100%"
            placeholder="选择县域（多选）"
          >
            <el-option v-for="r in regionOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择关键词">
          <el-select
            v-model="generateForm.keywordIds"
            multiple
            style="width: 100%"
            placeholder="选择关键词（多选）"
          >
            <el-option v-for="k in keywordOptions" :key="k.id" :label="k.keyword" :value="k.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择模板">
          <el-select v-model="generateForm.templateId" style="width: 100%">
            <el-option v-for="t in templateOptions" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成数量">
          <el-slider v-model="generateForm.count" :min="1" :max="50" :step="1" show-input />
        </el-form-item>
        <el-form-item label="原创度要求">
          <el-slider v-model="generateForm.originality" :min="80" :max="100" :step="5" show-input />
          <span class="slider-label">目标原创度 ≥ {{ generateForm.originality }}%</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          {{ generating ? '生成中...' : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="文章详情" width="700px">
      <div v-if="viewArticle" class="article-detail">
        <div class="detail-header">
          <h3>{{ viewArticle.title }}</h3>
          <div class="detail-meta">
            <span>{{ viewArticle.regionName }}</span>
            <span>·</span>
            <span>{{ viewArticle.keyword }}</span>
            <span>·</span>
            <span>{{ viewArticle.wordCount }}字</span>
          </div>
        </div>
        <div class="detail-content" v-html="sanitizedContent" />
      </div>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
        <el-button
          v-if="viewArticle?.status !== 'published'"
          type="primary"
          @click="handlePublish(viewArticle)"
        >
          发布文章
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { MagicStick, ArrowRightBold } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import DOMPurify from 'dompurify';
import api from '@/api';

const articles = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const statusFilter = ref('');
const regionFilter = ref('');
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const regionOptions = ref([]);
const keywordOptions = ref([]);
const templateOptions = ref([]);

const selectedArticles = ref([]);
const showGenerateDialog = ref(false);
const showViewDialog = ref(false);
const viewArticle = ref(null);
const sanitizedContent = computed(() => {
  return viewArticle.value?.content ? DOMPurify.sanitize(viewArticle.value.content) : '';
});
const generating = ref(false);

const generateForm = reactive({
  regionIds: [],
  keywordIds: [],
  templateId: '',
  count: 10,
  originality: 90,
});

const fetchArticles = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/v1/articles', {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        keyword: searchQuery.value,
        status: statusFilter.value,
        regionId: regionFilter.value,
      },
    });
    articles.value = res.data.list || [];
    total.value = res.data.total || 0;
  } catch (e) {
    console.error('获取文章失败:', e);
  } finally {
    loading.value = false;
  }
};

const fetchOptions = async () => {
  try {
    const [regionRes, keywordRes, templateRes] = await Promise.all([
      api.get('/api/v1/regions', { params: { size: 30 } }),
      api.get('/api/v1/keywords', { params: { size: 50 } }),
      api.get('/api/v1/templates', { params: { size: 20 } }),
    ]);
    regionOptions.value = regionRes.data.list?.map(r => ({ id: r.id, name: r.name })) || [];
    keywordOptions.value = keywordRes.data.list?.map(k => ({ id: k.id, keyword: k.keyword })) || [];
    templateOptions.value = templateRes.data.list?.map(t => ({ id: t.id, name: t.name })) || [];
  } catch (e) {
    console.error('获取选项失败:', e);
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchArticles();
};

const handleSelectionChange = val => {
  selectedArticles.value = val;
};

const handleView = row => {
  viewArticle.value = row;
  showViewDialog.value = true;
};

const handlePublish = async row => {
  try {
    await api.post(`/api/v1/articles/${row.id}/publish`);
    ElMessage.success('发布成功');
    fetchArticles();
    showViewDialog.value = false;
  } catch (e) {
    ElMessage.error('发布失败');
  }
};

const handleBatchPublish = async () => {
  try {
    const ids = selectedArticles.value.map(a => a.id);
    await api.post('/api/v1/articles/batch-publish', { ids });
    ElMessage.success(`成功发布 ${ids.length} 篇文章`);
    selectedArticles.value = [];
    fetchArticles();
  } catch (e) {
    ElMessage.error('批量发布失败');
  }
};

const handleDelete = async row => {
  try {
    await ElMessageBox.confirm('确定删除该文章吗？', '提示', { type: 'warning' });
    await api.delete(`/api/v1/articles/${row.id}`);
    ElMessage.success('删除成功');
    fetchArticles();
  } catch (e) {
    ElMessage.info('已取消删除');
  }
};

const handleGenerate = async () => {
  generating.value = true;
  try {
    const res = await api.post('/api/v1/articles/generate', {
      regionIds: generateForm.regionIds,
      keywordIds: generateForm.keywordIds,
      templateId: generateForm.templateId,
      count: generateForm.count,
      originality: generateForm.originality,
    });
    ElMessage.success(`成功生成 ${res.data.count} 篇文章`);
    showGenerateDialog.value = false;
    fetchArticles();
  } catch (e) {
    ElMessage.error('生成失败');
  } finally {
    generating.value = false;
  }
};

onMounted(() => {
  fetchArticles();
  fetchOptions();
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

.title-link {
  color: #409eff;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.article-detail {
  padding: 16px;

  .detail-header {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;

    h3 {
      margin-bottom: 8px;
      color: #303133;
    }

    .detail-meta {
      color: #909399;
      font-size: 13px;
    }
  }

  .detail-content {
    max-height: 500px;
    overflow-y: auto;
    line-height: 1.8;
    color: #606266;
  }
}

.slider-label {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
</style>
