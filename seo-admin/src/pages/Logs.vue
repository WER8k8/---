<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统日志</h2>
      <p>查看操作日志和登录日志</p>
    </div>
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="操作日志" name="operations">
          <el-table :data="operationLogs" stripe>
            <el-table-column prop="username" label="操作人" />
            <el-table-column prop="module" label="模块" />
            <el-table-column prop="action" label="操作" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="ipAddress" label="IP地址" />
            <el-table-column prop="createdAt" label="时间" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="登录日志" name="logins">
          <el-table :data="loginLogs" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="ipAddress" label="IP地址" />
            <el-table-column prop="device" label="设备" />
            <el-table-column prop="loginResult" label="结果">
              <template #default="{ row }">
                <el-tag :type="row.loginResult ? 'success' : 'danger'">{{ row.loginResult ? '成功' : '失败' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="时间" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const activeTab = ref('operations')
const operationLogs = ref([])
const loginLogs = ref([])
</script>
