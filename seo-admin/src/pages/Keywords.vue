<template>
  <div class="page-container">
    <div class="page-header">
      <h2>行业关键词库与AI组词</h2>
      <p>管理行业关键词，AI智能生成长尾词</p>
    </div>
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="行业关键词" name="industry">
          <el-table :data="keywords" stripe>
            <el-table-column prop="keyword" label="关键词" />
            <el-table-column prop="category" label="分类" />
            <el-table-column prop="searchVolume" label="搜索量" />
            <el-table-column prop="status" label="状态" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="AI组词" name="generate">
          <el-form label-width="120px">
            <el-form-item label="选择县域">
              <el-select multiple style="width: 100%"><el-option label="全部县域" value="all" /></el-select>
            </el-form-item>
            <el-form-item label="组词模板">
              <el-input type="textarea" :rows="3" placeholder="{县城}+{产品}+厂家" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="generateKeywords">开始生成</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('industry')
const keywords = ref([])

const generateKeywords = () => {
  ElMessage.info('AI组词功能开发中')
}
</script>
