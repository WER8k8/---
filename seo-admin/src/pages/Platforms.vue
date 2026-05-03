<template>
  <div class="page-container">
    <div class="page-header">
      <h2>多平台账号管理与AI分发中心</h2>
      <p>管理各分发平台账号，配置AI自动分发策略</p>
    </div>
    <el-card>
      <el-table :data="platforms" stripe>
        <el-table-column prop="name" label="平台名称" />
        <el-table-column prop="category" label="平台分类" />
        <el-table-column prop="hasApi" label="API支持">
          <template #default="{ row }">
            <el-tag :type="row.hasApi ? 'success' : 'info'">{{ row.hasApi ? '支持' : '不支持' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dailyLimit" label="每日上限" />
        <el-table-column prop="status" label="状态" />
        <el-table-column label="操作">
          <template #default>
            <el-button size="small">管理账号</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const platforms = ref([])
</script>
