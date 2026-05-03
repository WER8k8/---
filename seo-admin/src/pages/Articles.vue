<template>
  <div class="page-container">
    <div class="page-header">
      <h2>文章管理</h2>
      <p>管理AI生成的文章，支持批量发布和状态管理</p>
    </div>
    <el-card>
      <el-table :data="articles" stripe>
        <el-table-column prop="title" label="文章标题" />
        <el-table-column prop="regionName" label="所属县域" />
        <el-table-column prop="duplicateRate" label="重复率" />
        <el-table-column prop="complianceStatus" label="合规状态" />
        <el-table-column prop="status" label="发布状态" />
        <el-table-column prop="createdAt" label="创建时间" />
        <el-table-column label="操作">
          <template #default>
            <el-button size="small">查看</el-button>
            <el-button size="small" type="primary">发布</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const articles = ref([])
</script>
