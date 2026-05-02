<template>
  <div class="compliance-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">
        广告法合规审查
      </h2>
      <a-alert
        message="自动检测广告法违禁词，确保内容合规"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
    </div>

    <!-- 内容扫描 -->
    <a-card
      title="内容合规扫描"
      class="scan-card"
    >
      <a-form layout="vertical">
        <a-form-item label="扫描类型">
          <a-radio-group v-model:value="scanType">
            <a-radio value="text">
              纯文本
            </a-radio>
            <a-radio value="html">
              HTML内容
            </a-radio>
            <a-radio value="url">
              网页URL
            </a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item
          v-if="scanType === 'url'"
          label="网页URL"
        >
          <a-input
            v-model:value="scanUrl"
            placeholder="输入要扫描的网页地址"
          />
        </a-form-item>

        <a-form-item
          v-else
          label="内容"
        >
          <a-textarea
            v-model:value="scanContent"
            placeholder="输入要扫描的内容..."
            :rows="8"
          />
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            @click="startScan"
            :loading="scanning"
          >
            <template #icon>
              <SearchOutlined />
            </template>
            开始扫描
          </a-button>
          <a-button
            style="margin-left: 8px"
            @click="clearScan"
          >
            清空
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 扫描结果 -->
    <a-card
      v-if="scanResult"
      title="扫描结果"
      class="result-card"
    >
      <a-row
        :gutter="16"
        class="summary-cards"
      >
        <a-col :span="6">
          <a-statistic
            title="总检测词数"
            :value="scanResult.total_words"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="违规数量"
            :value="scanResult.violation_count"
            :value-style="{ color: scanResult.violation_count > 0 ? '#ff4d4f' : '#3f8600' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="高风险"
            :value="scanResult.high_risk_count"
            value-style="color: #ff4d4f"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="合规评分"
            :value="scanResult.compliance_score"
            suffix="分"
          />
        </a-col>
      </a-row>

      <!-- 违规列表 -->
      <a-divider />
      <h3>违规详情</h3>
      <a-empty
        v-if="scanResult.violations.length === 0"
        description="未发现违规内容"
      />
      <a-table
        v-else
        :columns="violationColumns"
        :data-source="scanResult.violations"
        :pagination="false"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <a-badge
              :status="record.severity === 'high' ? 'error' : record.severity === 'medium' ? 'warning' : 'default'"
              :text="record.severity === 'high' ? '高风险' : record.severity === 'medium' ? '中风险' : '低风险'"
            />
          </template>

          <template v-else-if="column.key === 'suggestion'">
            <a-tag color="success">
              {{ record.suggestion }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 违禁词库管理 -->
    <a-card
      title="违禁词库"
      class="wordlist-card"
    >
      <a-tabs v-model:active-key="activeTab">
        <a-tab-pane
          key="extreme"
          tab="极限词"
        >
          <a-list
            :data-source="extremeWords"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag color="red">
                  {{ item.word }}
                </a-tag>
                <span class="word-desc">{{ item.description }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>

        <a-tab-pane
          key="false"
          tab="虚假宣传"
        >
          <a-list
            :data-source="falseAds"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag color="orange">
                  {{ item.word }}
                </a-tag>
                <span class="word-desc">{{ item.description }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>

        <a-tab-pane
          key="medical"
          tab="医疗用语"
        >
          <a-list
            :data-source="medicalWords"
            item-layout="horizontal"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag color="purple">
                  {{ item.word }}
                </a-tag>
                <span class="word-desc">{{ item.description }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 扫描历史 -->
    <a-card
      title="扫描历史"
      class="history-card"
    >
      <a-table
        :columns="historyColumns"
        :data-source="scanHistory"
        :pagination="{ pageSize: 10 }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'pass' ? 'success' : 'error'"
              :text="record.status === 'pass' ? '通过' : '违规'"
            />
          </template>

          <template v-else-if="column.key === 'action'">
            <a-button
              type="link"
              size="small"
              @click="viewHistoryDetail(record)"
            >
              查看详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'

// 状态
const scanType = ref('text')
const scanUrl = ref('')
const scanContent = ref('')
const scanning = ref(false)
const scanResult = ref(null)
const activeTab = ref('extreme')
const scanHistory = ref([])

// 违禁词库示例数据
const extremeWords = [
  { word: '最', description: '最高级形容词' },
  { word: '最佳', description: '绝对化表述' },
  { word: '顶级', description: '极限词汇' },
  { word: '第一', description: '排名绝对化' },
  { word: '唯一', description: '排他性表述' },
  { word: '首选', description: '引导性词汇' },
]

const falseAds = [
  { word: '100%', description: '绝对化数据' },
  { word: '绝对', description: '绝对化承诺' },
  { word: '保证', description: '效果保证' },
  { word: '根治', description: '夸大疗效' },
  { word: '无效退款', description: '承诺性表述' },
]

const medicalWords = [
  { word: '治疗', description: '医疗术语' },
  { word: '治愈', description: '疗效承诺' },
  { word: '疗效', description: '医疗效果' },
  { word: '预防', description: '保健功效' },
]

// 表格列定义
const violationColumns = [
  { title: '违规词', dataIndex: 'word', key: 'word', width: 120 },
  { title: '位置', dataIndex: 'position', key: 'position', width: 100 },
  { title: '风险等级', key: 'severity', width: 100 },
  { title: '违规类型', dataIndex: 'category', key: 'category', width: 120 },
  { title: '上下文', dataIndex: 'context', key: 'context' },
  { title: '建议替换', key: 'suggestion', width: 120 },
]

const historyColumns = [
  { title: '扫描时间', dataIndex: 'scanned_at', key: 'scanned_at', width: 180 },
  { title: '扫描类型', dataIndex: 'scan_type', key: 'scan_type', width: 100 },
  { title: '违规数', dataIndex: 'violation_count', key: 'violation_count', width: 100 },
  { title: '合规评分', dataIndex: 'score', key: 'score', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

// 方法
const startScan = async () => {
  if (scanType.value === 'url' && !scanUrl.value) {
    message.warning('请输入URL')
    return
  }

  if (scanType.value !== 'url' && !scanContent.value) {
    message.warning('请输入内容')
    return
  }

  scanning.value = true

  try {
    const payload = scanType.value === 'url'
      ? { url: scanUrl.value, content_type: 'url' }
      : { content: scanContent.value, content_type: scanType.value }

    const response = await fetch('/api/v1/seo/compliance/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    scanResult.value = await response.json()
    message.success('扫描完成')

    // 刷新历史记录
    loadHistory()
  } catch (error) {
    message.error('扫描失败')
  } finally {
    scanning.value = false
  }
}

const clearScan = () => {
  scanContent.value = ''
  scanUrl.value = ''
  scanResult.value = null
}

const loadHistory = async () => {
  try {
    const response = await fetch('/api/v1/seo/compliance/history')
    scanHistory.value = await response.json()
  } catch (error) {
    console.error('加载历史失败', error)
  }
}

const viewHistoryDetail = (record) => {
  message.info(`查看扫描ID ${record.id} 的详情`)
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped lang="scss">
.compliance-page {
  padding: 24px;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      margin: 0 0 16px 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .scan-card,
  .result-card,
  .wordlist-card,
  .history-card {
    margin-bottom: 16px;
  }

  .summary-cards {
    margin-bottom: 16px;
  }

  .word-desc {
    margin-left: 8px;
    color: #666;
    font-size: 14px;
  }
}
</style>
