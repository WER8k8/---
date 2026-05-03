<template>
  <div class="page-container">
    <div class="page-header">
      <h2>收录监控</h2>
      <p>监控文章在搜索引擎的收录情况和排名</p>
    </div>
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="收录检测" name="index">
          <el-table :data="indexingData" stripe>
            <el-table-column prop="keyword" label="关键词" />
            <el-table-column prop="platform" label="搜索引擎" />
            <el-table-column prop="isIndexed" label="是否收录">
              <template #default="{ row }">
                <el-tag :type="row.isIndexed ? 'success' : 'danger'">{{ row.isIndexed ? '已收录' : '未收录' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ranking" label="排名" />
            <el-table-column prop="isHomepage" label="首页">
              <template #default="{ row }">
                <el-tag v-if="row.isHomepage" type="success">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="异常预警" name="alerts">
          <el-empty description="暂无异常预警" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const activeTab = ref('index')
const indexingData = ref([])
</script>
