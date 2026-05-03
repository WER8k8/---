<template>
  <div class="page-container">
    <div class="page-header">
      <h2>AI文案模板与全自动生成</h2>
      <p>管理文案模板，AI批量生成原创文章</p>
    </div>
    <el-card>
      <el-table :data="templates" stripe>
        <el-table-column prop="name" label="模板名称" />
        <el-table-column prop="category" label="分类" />
        <el-table-column prop="usageCount" label="使用次数" />
        <el-table-column prop="status" label="状态" />
        <el-table-column label="操作">
          <template #default>
            <el-button size="small">编辑</el-button>
            <el-button size="small" type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const templates = ref([])
</script>
