<template>
  <div class="page-container">
    <div class="page-header">
      <h2>AI文案模板与全自动生成</h2>
      <p>管理文案模板，AI批量生成原创文章</p>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索模板名称"
        class="search-input"
        prefix-icon="Search"
      />
      <el-select v-model="categoryFilter" placeholder="分类筛选">
        <el-option label="全部" value="" />
        <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
      </el-select>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新增模板
      </el-button>
    </div>

    <el-card>
      <el-table v-loading="loading" :data="templates" stripe>
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="模板名称" width="180" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="模板类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'article' ? 'primary' : 'success'">
              {{ row.type === 'article' ? '文章模板' : '标题模板' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="模板内容" min-width="300">
          <template #default="{ row }">
            <span class="template-content">
              {{ row.content?.substring(0, 50) }}{{ row.content?.length > 50 ? '...' : '' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="usageCount" label="使用次数" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="150" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handlePreview(row)">预览</el-button>
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
    </el-card>

    <el-dialog v-model="showAddDialog" title="新增/编辑模板" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="editForm.category">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板类型" prop="type">
          <el-select v-model="editForm.type">
            <el-option label="文章模板" value="article" />
            <el-option label="标题模板" value="title" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板内容" prop="content">
          <el-input
            v-model="editForm.content"
            type="textarea"
            :rows="8"
            placeholder="输入模板内容，支持变量替换：{region}、{keyword}、{product}、{company}"
          />
          <div class="template-variables">
            <span class="variables-label">可用变量：</span>
            <el-tag v-for="v in variables" :key="v" size="small">
              {{ v }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="2"
            placeholder="简要描述模板用途"
          />
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

    <el-dialog v-model="showPreviewDialog" title="模板预览" width="600px">
      <div class="preview-content">
        <h4>{{ previewTemplate?.name }}</h4>
        <p class="preview-category">
          {{ previewTemplate?.category }} ·
          {{ previewTemplate?.type === 'article' ? '文章模板' : '标题模板' }}
        </p>
        <div class="preview-body">
          {{ previewTemplate?.content }}
        </div>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleGenerateArticle">生成文章</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '@/api';

const templates = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const categoryFilter = ref('');
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const categories = ['保温材料', '防水材料', '涂料', '石材', '通用'];
const variables = ['{region}', '{keyword}', '{product}', '{company}', '{year}', '{month}'];

const showAddDialog = ref(false);
const showPreviewDialog = ref(false);
const previewTemplate = ref(null);

const editForm = reactive({
  id: null,
  name: '',
  category: '通用',
  type: 'article',
  content: '',
  description: '',
  status: '1',
});

const fetchTemplates = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/v1/templates', {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        keyword: searchQuery.value,
        category: categoryFilter.value,
      },
    });
    templates.value = res.data.list || [];
    total.value = res.data.total || 0;
  } catch (e) {
    console.error('获取模板失败:', e);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchTemplates();
};

const handleEdit = row => {
  editForm.id = row.id;
  editForm.name = row.name;
  editForm.category = row.category;
  editForm.type = row.type;
  editForm.content = row.content;
  editForm.description = row.description;
  editForm.status = row.status === 1 ? '1' : '0';
  showAddDialog.value = true;
};

const handlePreview = row => {
  previewTemplate.value = row;
  showPreviewDialog.value = true;
};

const handleSave = async () => {
  try {
    if (editForm.id) {
      await api.put(`/api/v1/templates/${editForm.id}`, editForm);
    } else {
      await api.post('/api/v1/templates', editForm);
    }
    ElMessage.success('保存成功');
    showAddDialog.value = false;
    fetchTemplates();
  } catch (e) {
    ElMessage.error('保存失败');
  }
};

const handleDelete = async row => {
  try {
    await ElMessageBox.confirm('确定删除该模板吗？', '提示', { type: 'warning' });
    await api.delete(`/api/v1/templates/${row.id}`);
    ElMessage.success('删除成功');
    fetchTemplates();
  } catch (e) {
    ElMessage.info('已取消删除');
  }
};

const handleGenerateArticle = () => {
  ElMessage.info('文章生成功能开发中');
  showPreviewDialog.value = false;
};

onMounted(() => {
  fetchTemplates();
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

.template-content {
  color: #606266;
  font-size: 13px;
}

.template-variables {
  margin-top: 8px;

  .variables-label {
    color: #909399;
    font-size: 12px;
    margin-right: 8px;
  }
}

.preview-content {
  padding: 16px;

  h4 {
    margin-bottom: 8px;
    color: #303133;
  }

  .preview-category {
    color: #909399;
    font-size: 13px;
    margin-bottom: 16px;
  }

  .preview-body {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 4px;
    min-height: 150px;
    white-space: pre-wrap;
    color: #606266;
  }
}
</style>
