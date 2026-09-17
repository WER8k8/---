/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-card class="evidence-chain" size="small" :bordered="false">
    <template #title>
      <div class="chain-title">
        <FileSearchOutlined />
        <span>证据链</span>
        <a-tag color="blue" v-if="evidences.length > 0">{{ evidences.length }} 条</a-tag>
      </div>
    </template>

    <!-- 证据列表 -->
    <a-timeline v-if="evidences.length > 0" class="evidence-timeline">
      <a-timeline-item
        v-for="(evidence, index) in evidences"
        :key="evidence.sourceUrl || evidence.content || index"
        :color="getEvidenceColor(evidence.type)"
      >
        <div class="evidence-item">
          <div class="evidence-header">
            <div class="evidence-type">
              <component :is="getEvidenceIcon(evidence.type)" class="type-icon" />
              <span class="type-label">{{ getEvidenceTypeLabel(evidence.type) }}</span>
            </div>
            <div class="evidence-meta">
              <a-tag size="small" :color="getConfidenceColor(evidence.confidence)">
                {{ getConfidenceLabel(evidence.confidence) }}
              </a-tag>
              <span class="evidence-time" v-if="evidence.timestamp">
                {{ formatTime(evidence.timestamp) }}
              </span>
            </div>
          </div>

          <div class="evidence-content">
            <div class="evidence-text">{{ evidence.content }}</div>

            <div class="evidence-source" v-if="evidence.sourceUrl">
              <a
                :href="evidence.sourceUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="source-link"
              >
                <LinkOutlined />
                <span>{{ getSourceDomain(evidence.sourceUrl) }}</span>
                <ExportOutlined class="external-icon" />
              </a>
            </div>
          </div>

          <!-- 展开/收起详情 -->
          <div v-if="evidence.details" class="evidence-details">
            <a-collapse ghost>
              <a-collapse-panel key="details" header="查看详情">
                <div class="details-content">{{ evidence.details }}</div>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </div>
      </a-timeline-item>
    </a-timeline>

    <!-- 空状态 -->
    <a-empty v-else description="暂无证据" :image="null">
      <template #image>
        <FileSearchOutlined style="font-size: 48px; color: #d9d9d9" />
      </template>
    </a-empty>
  </a-card>
</template>

<script setup lang="ts">
import {
  FileSearchOutlined,
  LinkOutlined,
  ExportOutlined,
  GlobalOutlined,
  MailOutlined,
  TeamOutlined,
  ShopOutlined,
  SafetyCertificateOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'

// 证据类型定义
export interface Evidence {
  type: 'website' | 'email' | 'contact' | 'certification' | 'search' | 'linkedin'
  content: string
  sourceUrl?: string
  confidence: 'high' | 'medium' | 'low'
  timestamp?: string
  details?: string
}

// Props
interface Props {
  evidences: Evidence[]
}

defineProps<Props>()

// 获取证据颜色
function getEvidenceColor(type: string): string {
  const colors: Record<string, string> = {
    website: 'blue',
    email: 'green',
    contact: 'cyan',
    certification: 'gold',
    search: 'purple',
    linkedin: 'geekblue'
  }
  return colors[type] || 'gray'
}

// 获取证据图标
function getEvidenceIcon(type: string) {
  const icons: Record<string, any> = {
    website: GlobalOutlined,
    email: MailOutlined,
    contact: TeamOutlined,
    certification: SafetyCertificateOutlined,
    search: SearchOutlined,
    linkedin: ShopOutlined
  }
  return icons[type] || GlobalOutlined
}

// 获取证据类型标签
function getEvidenceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    website: '官网',
    email: '邮箱',
    contact: '联系人',
    certification: '认证',
    search: '搜索',
    linkedin: 'LinkedIn'
  }
  return labels[type] || type
}

// 获取置信度颜色
function getConfidenceColor(confidence: string): string {
  const colors: Record<string, string> = {
    high: 'green',
    medium: 'orange',
    low: 'red'
  }
  return colors[confidence] || 'default'
}

// 获取置信度标签
function getConfidenceLabel(confidence: string): string {
  const labels: Record<string, string> = {
    high: '高置信',
    medium: '中置信',
    low: '低置信'
  }
  return labels[confidence] || confidence
}

// 格式化时间
function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    // 小于1天
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      if (hours < 1) return '刚刚'
      return `${hours}小时前`
    }

    // 小于7天
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000)
      return `${days}天前`
    }

    // 超过7天显示日期
    return date.toLocaleDateString('zh-CN')
  } catch {
    return timestamp
  }
}

// 获取来源域名
function getSourceDomain(url: string): string {
  try {
    const domain = new URL(url).hostname
    return domain.replace('www.', '')
  } catch {
    return url
  }
}
</script>

<style scoped lang="scss">
.evidence-chain {
  .chain-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
  }

  .evidence-timeline {
    padding-left: 4px;

    .evidence-item {
      background: #fafafa;
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 8px;

      .evidence-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .evidence-type {
          display: flex;
          align-items: center;
          gap: 6px;

          .type-icon {
            font-size: 16px;
            color: #1890ff;
          }

          .type-label {
            font-weight: 500;
            font-size: 13px;
            color: #333;
          }
        }

        .evidence-meta {
          display: flex;
          align-items: center;
          gap: 8px;

          .evidence-time {
            font-size: 12px;
            color: #888;
          }
        }
      }

      .evidence-content {
        .evidence-text {
          font-size: 13px;
          color: #555;
          line-height: 1.6;
          margin-bottom: 8px;
        }

        .evidence-source {
          .source-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #1890ff;
            text-decoration: none;

            &:hover {
              text-decoration: underline;
            }

            .external-icon {
              font-size: 10px;
              color: #888;
            }
          }
        }
      }

      .evidence-details {
        margin-top: 8px;

        :deep(.ant-collapse-header) {
          font-size: 12px !important;
          padding: 4px 0 !important;
          color: #888;
        }

        :deep(.ant-collapse-content-box) {
          padding: 0 !important;
        }

        .details-content {
          font-size: 12px;
          color: #666;
          line-height: 1.6;
          background: #fff;
          padding: 8px;
          border-radius: 4px;
        }
      }
    }
  }
}
</style>
