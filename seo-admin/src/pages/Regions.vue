<template>
  <div class="page-container">
    <div class="page-header">
      <h2>全国地域词库管理</h2>
      <p>管理2800+县域词库，支持批量操作和导入导出</p>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索地域名称或代码"
        class="search-input"
        prefix-icon="Search"
      />
      <el-button type="primary" @click="handleExport">
        <el-icon><Download /></el-icon>
        导出词库
      </el-button>
      <el-button @click="showImportDialog = true">
        <el-icon><Upload /></el-icon>
        导入词库
      </el-button>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="regions"
        stripe
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="地域名称" width="200">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.level - 1) * 20 + 'px' }">
              <el-icon v-if="row.level === 1"><MapLocation /></el-icon>
              <el-icon v-else-if="row.level === 2"><OfficeBuilding /></el-icon>
              <el-icon v-else><HomeFilled /></el-icon>
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="行政区划代码" width="150" />
        <el-table-column prop="level" label="层级" width="80">
          <template #default="{ row }">
            <el-tag :type="row.level === 1 ? 'primary' : row.level === 2 ? 'success' : 'warning'">
              {{ row.level === 1 ? '省' : row.level === 2 ? '市' : '县' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="keywordCount" label="关键词数" width="100" />
        <el-table-column prop="articleCount" label="文章数" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              :value="row.status === 1"
              active-color="#67C23A"
              inactive-color="#F56C6C"
              @change="(val) => handleStatusChange(row)"
            />
          </template>
        </el-table-column>
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
    </el-card>

    <el-dialog v-model="showImportDialog" title="导入词库" width="500px">
      <el-form label-width="100px">
        <el-form-item label="导入文件">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            :auto-upload="false"
            :show-file-list="false"
            :before-upload="beforeUpload"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
          <p class="text-gray">支持 CSV、Excel 格式，编码 UTF-8</p>
        </el-form-item>
        <el-form-item label="更新方式">
          <el-radio-group v-model="importMode">
            <el-radio label="append">追加导入</el-radio>
            <el-radio label="replace">覆盖更新</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑地域" width="450px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="地域名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入地域名称" />
        </el-form-item>
        <el-form-item label="行政区划代码" prop="code">
          <el-input v-model="editForm.code" placeholder="请输入行政区划代码" />
        </el-form-item>
        <el-form-item label="层级" prop="level">
          <el-select v-model="editForm.level">
            <el-option :value="1" label="省" />
            <el-option :value="2" label="市" />
            <el-option :value="3" label="县" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editForm.status" active-value="1" inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import {
  Download,
  Upload,
  Search,
  MapLocation,
  OfficeBuilding,
  HomeFilled,
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '@/api';

const regions = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const showImportDialog = ref(false);
const showEditDialog = ref(false);
const importMode = ref('append');
const uploadRef = ref(null);

const editForm = reactive({
  id: null,
  name: '',
  code: '',
  level: 3,
  status: '1',
});

const fetchRegions = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/v1/regions/tree', {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        keyword: searchQuery.value,
      },
    });
    regions.value = res.data.list || [];
    total.value = res.data.total || 0;
  } catch (e) {
    console.error('获取地域列表失败:', e);
    ElMessage.error('获取地域列表失败');
  } finally {
    loading.value = false;
  }
};

const handlePageChange = page => {
  currentPage.value = page;
  fetchRegions();
};

const handleExport = async () => {
  try {
    const res = await api.get('/api/v1/regions/export', { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `regions_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    ElMessage.success('导出成功');
  } catch (e) {
    ElMessage.error('导出失败');
  }
};

const beforeUpload = file => {
  const allowedTypes = [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ];
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('请选择CSV或Excel文件');
    return false;
  }
  return false;
};

const handleImport = async () => {
  ElMessage.info('导入功能开发中，暂支持手动配置');
  showImportDialog.value = false;
};

const handleEdit = row => {
  editForm.id = row.id;
  editForm.name = row.name;
  editForm.code = row.code;
  editForm.level = row.level;
  editForm.status = row.status === 1 ? '1' : '0';
  showEditDialog.value = true;
};

const handleSave = async () => {
  try {
    if (editForm.id) {
      await api.put(`/api/v1/regions/${editForm.id}`, {
        name: editForm.name,
        code: editForm.code,
        level: parseInt(editForm.level),
        status: parseInt(editForm.status),
      });
    } else {
      await api.post('/api/v1/regions', {
        name: editForm.name,
        code: editForm.code,
        level: parseInt(editForm.level),
        status: parseInt(editForm.status),
      });
    }
    ElMessage.success('保存成功');
    showEditDialog.value = false;
    fetchRegions();
  } catch (e) {
    ElMessage.error('保存失败');
  }
};

const handleDelete = async row => {
  try {
    await ElMessageBox.confirm('确定删除该地域吗？', '提示', {
      type: 'warning',
    });
    await api.delete(`/api/v1/regions/${row.id}`);
    ElMessage.success('删除成功');
    fetchRegions();
  } catch (e) {
    ElMessage.info('已取消删除');
  }
};

const handleStatusChange = async row => {
  try {
    await api.put(`/api/v1/regions/${row.id}/status`, {
      status: row.status === 1 ? 0 : 1,
    });
    ElMessage.success('状态更新成功');
  } catch (e) {
    row.status = row.status === 1 ? 0 : 1;
    ElMessage.error('状态更新失败');
  }
};

onMounted(() => {
  fetchRegions();
});
</script>

<style scoped lang="scss">
.page-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;

  .search-input {
    width: 300px;
  }
}

.pagination {
  margin-top: 16px;
  text-align: right;
}

.text-gray {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
