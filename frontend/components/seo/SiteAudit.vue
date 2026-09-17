/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="space-y-6">
    <Card>
      <template #default>
        <h3 class="text-lg font-semibold mb-4">
          站点审计
        </h3>
        <div class="space-y-4">
          <div>
            <Label>审计类型</Label>
            <div class="flex space-x-4 mt-2">
              <label class="flex items-center space-x-2 cursor-pointer">
                <input
                  v-model="auditType"
                  type="radio"
                  value="quick"
                  class="text-primary focus:ring-primary"
                >
                <span>快速审计 (基础检测)</span>
              </label>
              <label class="flex items-center space-x-2 cursor-pointer">
                <input
                  v-model="auditType"
                  type="radio"
                  value="full"
                  class="text-primary focus:ring-primary"
                >
                <span>完整审计 (11维度 + AI分析)</span>
              </label>
            </div>
          </div>
          <div>
            <Label>目标URL</Label>
            <div class="flex space-x-3 mt-2">
              <Input
                v-model="targetUrl"
                placeholder="https://youding.com"
                class="flex-1"
              />
              <Button
                :disabled="auditing"
                @click="handleRunAudit"
              >
                {{ auditing ? '审计中...' : '运行审计' }}
              </Button>
            </div>
          </div>
        </div>
      </template>
    </Card>

    <div
      v-if="error"
      class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
      role="alert"
    >
      {{ error }}
    </div>

    <div
      v-if="result"
      class="space-y-4"
    >
      <Card>
        <template #default>
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold">
              审计报告
            </h3>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">总分</span>
              <span
                :class="scoreColor"
                class="text-3xl font-bold"
              >{{ result.score }}</span>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <div
              v-for="(score, dim) in result.dimension_scores"
              :key="dim"
              class="bg-gray-50 rounded-lg p-3"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-medium text-gray-700">{{
                  dimensionLabels[dim] || dim
                }}</span>
                <span
                  :class="getScoreColor(score)"
                  class="font-bold text-sm"
                >{{ score }}</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div
                  :class="getScoreBarColor(score)"
                  class="h-1.5 rounded-full transition-all duration-500"
                  :style="{ width: score + '%' }"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card class="bg-red-50 border-red-100">
          <div class="text-center">
            <div class="text-2xl font-bold text-red-600">
              {{ result.critical_issues }}
            </div>
            <div class="text-sm text-red-700">
              严重问题
            </div>
          </div>
        </Card>
        <Card class="bg-orange-50 border-orange-100">
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">
              {{ result.warning_issues }}
            </div>
            <div class="text-sm text-orange-700">
              警告
            </div>
          </div>
        </Card>
        <Card class="bg-blue-50 border-blue-100">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary">
              {{ result.total_issues }}
            </div>
            <div class="text-sm text-blue-700">
              问题总数
            </div>
          </div>
        </Card>
      </div>

      <Card v-if="result.issues && result.issues.length">
        <h3 class="text-lg font-semibold mb-4">
          发现的问题 ({{ result.issues.length }})
        </h3>
        <div class="space-y-2">
          <div
            v-for="(issue, idx) in result.issues"
            :key="idx"
            class="flex items-start space-x-3 p-3 rounded-lg"
            :class="{
              'bg-red-50 border border-red-100': issue.severity === 'high',
              'bg-orange-50 border border-orange-100': issue.severity === 'medium',
              'bg-yellow-50 border border-yellow-100': issue.severity === 'low',
            }"
          >
            <span class="mt-0.5 text-lg">{{
              issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢'
            }}</span>
            <div>
              <Badge
                :variant="issue.severity === 'high' ? 'outline' : 'secondary'"
                class="mb-1"
              >
                {{ dimensionLabels[issue.dimension] || issue.dimension }}
              </Badge>
              <p class="text-sm text-gray-700">
                {{ issue.message }}
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card v-if="result.recommendations && result.recommendations.length">
        <h3 class="text-lg font-semibold mb-4">
          优化建议 ({{ result.recommendations.length }})
        </h3>
        <div class="space-y-2">
          <div
            v-for="(rec, idx) in result.recommendations"
            :key="idx"
            class="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-100"
          >
            <span class="text-primary mt-0.5 text-lg">💡</span>
            <span class="text-sm text-gray-700">{{ rec.issue }}</span>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSeo } from '~/composables/useSeo';
import Button from '~/components/ui/Button.vue';
import Input from '~/components/ui/Input.vue';
import Card from '~/components/ui/Card.vue';
import Badge from '~/components/ui/Badge.vue';
import Label from '~/components/ui/Label.vue';

const seo = useSeo();

const auditType = ref<'quick' | 'full'>('full');
const targetUrl = ref('https://youding.com');
const auditing = ref(false);
const error = ref<string | null>(null);

interface AuditIssue {
  severity: string;
  dimension: string;
  message: string;
}

interface AuditRecommendation {
  issue: string;
  priority: string;
}

interface AuditResult {
  score: number;
  total_issues: number;
  critical_issues: number;
  warning_issues: number;
  dimension_scores: Record<string, number>;
  issues: AuditIssue[];
  recommendations: AuditRecommendation[];
  status: string;
  url: string;
  id: string;
}

const result = ref<AuditResult | null>(null);

const dimensionLabels: Record<string, string> = {
  technical_compliance: '技术合规',
  meta_tags: '元标签',
  page_structure: '页面结构',
  security_compliance: '安全合规',
  ai_crawler_friendly: 'AI爬虫友好',
  mobile_friendly: '移动适配',
  performance: '性能',
  link_quality: '链接质量',
  content_quality: '内容质量',
  social_media: '社交媒体',
  ai_search_optimization: 'AI搜索优化',
};

const scoreColor = computed(() => {
  if (!result.value) return '';
  const s = result.value.score;
  if (s >= 80) return 'text-green-600';
  if (s >= 60) return 'text-orange-600';
  return 'text-red-600';
});

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-orange-600';
  return 'text-red-600';
}

function getScoreBarColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-orange-500';
  return 'bg-red-500';
}

async function handleRunAudit() {
  if (!targetUrl.value) {
    error.value = '请输入目标URL';
    return;
  }
  auditing.value = true;
  error.value = null;
  result.value = null;
  try {
    const res = (await seo.runAudit(targetUrl.value, auditType.value)) as any;
    result.value = {
      score: res.score,
      total_issues: res.total_issues,
      critical_issues: res.critical_issues,
      warning_issues: res.warning_issues,
      dimension_scores: res.dimension_scores || {},
      issues: res.issues || [],
      recommendations: res.recommendations || [],
      status: res.status,
      url: res.url,
      id: res.id,
    };
  } catch (e: any) {
    error.value = e.message || '审计执行失败';
  } finally {
    auditing.value = false;
  }
}
</script>
