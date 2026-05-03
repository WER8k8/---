<template>
  <div class="page-container">
    <div class="page-header">
      <h2>全国地域词库管理</h2>
      <p>管理2800+县域词库，支持批量操作和导入导出</p>
    </div>
    <el-card>
      <el-table :data="regions" v-loading="loading" stripe>
        <el-table-column prop="name" label="地域名称" />
        <el-table-column prop="code" label="行政区划代码" />
        <el-table-column prop="level" label="层级">
          <template #default="{ row }">
            <el-tag :type="row.level === 1 ? '' : row.level === 2 ? 'success' : 'warning'">
              {{ row.level === 1 ? '省' : row.level === 2 ? '市' : '县' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const regions = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/api/v1/regions/tree')
    regions.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
