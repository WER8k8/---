<template>
  <div class="space-y-6">
    <Card>
      <template #default>
        <h3 class="text-lg font-semibold mb-4">
          AI 内容优化
        </h3>
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>优化类型</Label>
              <Select
                v-model="optType"
                class="mt-2"
              >
                <option value="content">
                  内容正文
                </option>
                <option value="title">
                  标题
                </option>
                <option value="description">
                  描述
                </option>
                <option value="alt_text">
                  Alt文本
                </option>
              </Select>
            </div>
            <div>
              <Label>目标关键词 (逗号分隔)</Label>
              <Input
                v-model="keywordsRaw"
                placeholder="轻集料混凝土,陶粒混凝土"
                class="mt-2"
              />
            </div>
            <div>
              <Label>AI模型</Label>
              <Select
                v-model="model"
                class="mt-2"
              >
                <option value="gpt-4o">
                  GPT-4o (推荐)
                </option>
                <option value="gpt-4o-mini">
                  GPT-4o Mini (快速)
                </option>
                <option value="claude-3-haiku">
                  Claude 3 Haiku
                </option>
              </Select>
            </div>
          </div>

          <div>
            <Label>原始内容</Label>
            <textarea
              v-model="content"
              rows="8"
              class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-primary focus:border-transparent mt-2"
              placeholder="请输入需要优化的内容..."
            />
          </div>

          <div class="flex items-center space-x-4">
            <Button
              :disabled="optimizing"
              @click="handleOptimize"
            >
              {{ optimizing ? '优化中...' : '开始优化' }}
            </Button>
            <Button
              variant="outline"
              @click="handleExtractParams"
            >
              提取技术参数
            </Button>
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

    <Card v-if="extractedParamsResult">
      <template #default>
        <h3 class="text-lg font-semibold mb-4">
          提取的技术参数
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(value, key) in extractedParamsResult.technical_params"
            :key="key"
            class="bg-gray-50 rounded-lg p-4"
          >
            <span class="text-sm text-gray-500">{{ paramLabels[key] || key }}</span>
            <div class="text-gray-900 font-medium mt-1">
              {{ value }}
            </div>
          </div>
        </div>
        <p
          v-if="!extractedParamsResult.found"
          class="text-sm text-gray-400 mt-2"
        >
          未识别到行业标准技术参数
        </p>
      </template>
    </Card>

    <div
      v-if="result"
      class="space-y-4"
    >
      <Card>
        <template #default>
          <h3 class="text-lg font-semibold mb-4">
            优化结果
          </h3>
          <div class="bg-green-50 border border-green-200 rounded-lg p-4 whitespace-pre-wrap">
            {{ result.optimized_content }}
          </div>
          <div class="flex items-center justify-between mt-4 text-sm text-gray-500">
            <span>Token用量: {{ result.token_usage }} | 费用: ¥{{ result.cost }}</span>
            <Badge :variant="result.changes.length > 0 ? 'default' : 'secondary'">
              {{ result.changes.length }} 项变更
            </Badge>
          </div>
          <div
            v-if="result.technical_params_preserved"
            class="mt-2 text-xs text-green-600"
          >
            技术参数已保留 ✓
          </div>
          <div
            v-else
            class="mt-2 text-xs text-orange-600"
          >
            技术参数可能丢失，请检查
          </div>
        </template>
      </Card>

      <Card v-if="validation">
        <template #default>
          <h3 class="text-lg font-semibold mb-4">
            合规校验
          </h3>
          <div class="flex items-center space-x-2 mb-4">
            <Badge
              :variant="validation.is_valid ? 'default' : 'outline'"
              class="text-sm"
            >
              {{ validation.is_valid ? '通过' : '存在问题' }}
            </Badge>
            <Badge :variant="validation.technical_params_preserved ? 'default' : 'outline'">
              技术参数{{ validation.technical_params_preserved ? '已保留' : '可能丢失' }}
            </Badge>
          </div>
          <ul
            v-if="validation.issues.length"
            class="space-y-2"
          >
            <li
              v-for="(issue, i) in validation.issues"
              :key="i"
              class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded"
            >
              <span
                v-if="issue.param"
                class="font-medium"
              >{{ issue.param }}: </span>{{ issue.issue }}
            </li>
          </ul>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSeo } from '~/composables/useSeo';
import Button from '~/components/ui/Button.vue';
import Input from '~/components/ui/Input.vue';
import Card from '~/components/ui/Card.vue';
import Badge from '~/components/ui/Badge.vue';
import Select from '~/components/ui/Select.vue';
import Label from '~/components/ui/Label.vue';

const seo = useSeo();

const optType = ref<'title' | 'description' | 'alt_text' | 'content'>('content');
const keywordsRaw = ref('');
const content = ref('');
const model = ref('gpt-4o');
const optimizing = ref(false);
const error = ref<string | null>(null);
const result = ref<{
  optimized_content: string;
  changes: string[];
  token_usage: number;
  cost: number;
  technical_params_preserved: boolean;
} | null>(null);
const validation = ref<{
  is_valid: boolean;
  issues: Array<{ param: string | null; issue: string }>;
  technical_params_preserved: boolean;
} | null>(null);
const extractedParamsResult = ref<{
  technical_params: Record<string, string>;
  found: boolean;
} | null>(null);

const paramLabels: Record<string, string> = {
  density: '密度',
  strength_grade: '强度等级',
  thermal_conductivity: '导热系数',
  particle_size: '粒径',
  water_absorption: '吸水率',
  specification: '规格型号',
  material: '材料类型',
};

async function handleOptimize() {
  if (!content.value || content.value.length < 10) {
    error.value = '内容至少需要10个字符';
    return;
  }
  const keywords = keywordsRaw.value
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean);
  if (!keywords.length) {
    error.value = '请至少输入一个关键词';
    return;
  }
  optimizing.value = true;
  error.value = null;
  result.value = null;
  validation.value = null;
  try {
    result.value = await seo.optimizeContent({
      content: content.value,
      opt_type: optType.value,
      keywords,
      model: model.value,
    });
    validation.value = await seo.validateContent(content.value, result.value.optimized_content);
  } catch (e: any) {
    error.value = e.message || '优化失败';
  } finally {
    optimizing.value = false;
  }
}

async function handleExtractParams() {
  if (!content.value) {
    error.value = '请输入内容';
    return;
  }
  error.value = null;
  try {
    extractedParamsResult.value = await seo.extractParams(content.value);
  } catch (e: any) {
    error.value = e.message || '参数提取失败';
  }
}
</script>
