<template>
  <div class="page-container">
    <div class="page-header">
      <h2>发布任务管理</h2>
      <p>查看和管理所有发布任务状态</p>
    </div>
    <el-card>
      <el-table :data="tasks" stripe>
        <el-table-column prop="articleTitle" label="文章标题" />
        <el-table-column prop="platformName" label="发布平台" />
        <el-table-column prop="accountName" label="账号" />
        <el-table-column prop="status" label="状态" />
        <el-table-column prop="retryCount" label="重试次数" />
        <el-table-column prop="publishedAt" label="发布时间" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button v-if="row.status === 3" size="small" type="warning">重试</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const tasks = ref([])
</script>
