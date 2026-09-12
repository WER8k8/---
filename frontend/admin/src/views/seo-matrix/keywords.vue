<template>
  <YdPage title="关键词管理" subtitle="AI 智能组合生成县域建材关键词" surface="elevated">
    <template #actions>
      <a-button @click="refreshData">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新
      </a-button>
      <a-button type="primary" class="gradient-primary" @click="showGenerateModal = true">
        <BulbOutlined class="w-4 h-4 mr-2" />
        AI 生成关键词
      </a-button>
      <a-button :loading="seedingBelt" @click="seedDachengKeywords">
        导入大城/河间词库
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-5">
      <div class="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-primary-100 text-sm font-medium">
              组合规则数
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ rules.length }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <TagsOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-success-500 to-success-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-success-100 text-sm font-medium">
              已生成关键词
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ generatedKeywords.length }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <KeyOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm font-medium">
              已使用关键词
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ usedCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <CheckCircleOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm font-medium">
              有效关键词
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ validCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <StarOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1">
        <div class="bg-white rounded-2xl shadow-card p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TagsOutlined class="w-5 h-5 mr-2 text-primary-500" />
            组词规则
          </h3>
          <div class="space-y-2">
            <div
              v-for="rule in rules"
              :key="rule.id"
              :class="[
                'p-3 rounded-xl cursor-pointer transition-all',
                selectedRule?.id === rule.id
                  ? 'bg-primary-50 border border-primary-200'
                  : 'hover:bg-gray-50',
              ]"
              @click="selectRule(rule)"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium text-gray-900">{{ rule.name }}</span>
                <span class="text-sm text-gray-500">{{ rule.keyword_count }}词</span>
              </div>
              <p class="text-xs text-gray-400 mt-1">
                {{ rule.pattern }}
              </p>
            </div>
          </div>
          <a-button
            block
            size="small"
            type="dashed"
            class="mt-4"
            @click="showRuleModal = true"
          >
            <PlusOutlined class="w-4 h-4 mr-2" />
            添加规则
          </a-button>
        </div>
      </div>

      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                生成的关键词
              </h3>
              <p
                v-if="selectedRule"
                class="text-sm text-gray-500 mt-1"
              >
                当前规则: {{ selectedRule.name }}
              </p>
            </div>
            <div class="flex items-center space-x-2">
              <a-button
                size="small"
                @click="batchDelete"
              >
                <DeleteOutlined class="w-4 h-4 mr-2" />
                批量删除
              </a-button>
              <a-button
                size="small"
                type="primary"
                @click="regenerate"
              >
                <UndoOutlined class="w-4 h-4 mr-2" />
                重新生成
              </a-button>
            </div>
          </div>

          <a-table
            :columns="columns"
            :data-source="generatedKeywords"
            :pagination="pagination"
            :loading="loading"
            row-key="id"
            :row-selection="{ type: 'checkbox', selectedRowKeys: selectedKeys }"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'keyword'">
                <span class="font-medium text-gray-900">{{ record.keyword }}</span>
              </template>
              <template v-if="column.key === 'region'">
                <span class="text-gray-500 text-sm">{{ record.district_name }}</span>
              </template>
              <template v-if="column.key === 'search_volume'">
                <span class="text-gray-600">{{ record.search_volume || '-' }}</span>
              </template>
              <template v-if="column.key === 'is_valid'">
                <span
                  :class="
                    record.is_valid
                      ? 'bg-success-50 text-success-600'
                      : 'bg-danger-50 text-danger-600'
                  "
                  class="px-3 py-1 rounded-full text-sm font-medium"
                >
                  {{ record.is_valid ? '有效' : '无效' }}
                </span>
              </template>
              <template v-if="column.key === 'is_used'">
                <span
                  :class="record.is_used ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-500'"
                  class="px-3 py-1 rounded-full text-sm font-medium"
                >
                  {{ record.is_used ? '已使用' : '未使用' }}
                </span>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space :size="8">
                  <a-button
                    size="small"
                    @click="editKeyword(record)"
                  >
                    编辑
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    @click="deleteKeyword(record)"
                  >
                    删除
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showGenerateModal"
      title="AI生成关键词"
      :footer="false"
    >
      <a-form
        :model="generateForm"
        layout="vertical"
      >
        <a-form-item label="选择规则">
          <a-select
            v-model:value="generateForm.rule_id"
            placeholder="选择组词规则"
            class="w-full"
          >
            <a-select-option
              v-for="rule in rules"
              :key="rule.id"
              :value="rule.id"
            >
              {{ rule.name }} - {{ rule.pattern }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="生成数量">
          <a-input-number
            v-model:value="generateForm.count"
            :min="1"
            :max="100"
            class="w-40"
          />
        </a-form-item>
        <a-form-item label="覆盖区域">
          <a-select
            v-model:value="generateForm.region_scope"
            placeholder="选择覆盖区域"
            class="w-full"
          >
            <a-select-option value="all">
              全国所有区县
            </a-select-option>
            <a-select-option value="selected">
              已选地区
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <div class="flex justify-end space-x-3 mt-6">
        <a-button @click="showGenerateModal = false">
          取消
        </a-button>
        <a-button
          type="primary"
          class="gradient-primary"
          @click="generateKeywords"
        >
          <BulbOutlined class="w-4 h-4 mr-2" />
          开始生成
        </a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showRuleModal"
      :title="editingRule ? '编辑规则' : '添加组词规则'"
      @ok="saveRule"
    >
      <a-form
        :model="ruleForm"
        layout="vertical"
      >
        <a-form-item label="规则名称">
          <a-input
            v-model:value="ruleForm.name"
            placeholder="输入规则名称"
          />
        </a-form-item>
        <a-form-item label="组词模式">
          <a-select
            v-model:value="ruleForm.pattern_type"
            placeholder="选择组词模式"
          >
            <a-select-option value="region_keyword">
              地域+关键词
            </a-select-option>
            <a-select-option value="keyword_region">
              关键词+地域
            </a-select-option>
            <a-select-option value="region_keyword_region">
              地域+关键词+地域
            </a-select-option>
            <a-select-option value="custom">
              自定义模式
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item
          label="自定义模板"
          v-if="ruleForm.pattern_type === 'custom'"
        >
          <a-input
            v-model:value="ruleForm.pattern"
            placeholder="如: {region} {keyword} 厂家"
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea
            v-model:value="ruleForm.remark"
            placeholder="备注信息"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showKeywordEditModal"
      title="编辑关键词"
      ok-text="保存"
      cancel-text="取消"
      @ok="saveGenKeywordEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="关键词">
          <a-input v-model:value="genKeywordForm.keyword" placeholder="关键词文本" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onActivated } from 'vue';
import {
  ReloadOutlined,
  BulbOutlined,
  TagsOutlined,
  KeyOutlined,
  CheckCircleOutlined,
  StarOutlined,
  PlusOutlined,
  DeleteOutlined,
  UndoOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { seoMatrixAPI, unwrapApiData } from '@/api';

const rules = ref<any[]>([]);
const generatedKeywords = ref<any[]>([]);
const selectedRule = ref<any>(null);
const selectedKeys = ref<string[]>([]);
const seedingBelt = ref(false);

const loading = ref(false);
const showGenerateModal = ref(false);
const showRuleModal = ref(false);
const showKeywordEditModal = ref(false);
const editingRule = ref<any>(null);
const editingGenKeyword = ref<any>(null);

const genKeywordForm = reactive({
  keyword: '',
});

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const generateForm = reactive({
  rule_id: '',
  count: 20,
  region_scope: 'all',
});

const ruleForm = reactive({
  name: '',
  pattern_type: 'region_keyword',
  pattern: '',
  remark: '',
});

const columns = [
  { title: '关键词', key: 'keyword', width: 250 },
  { title: '地区', key: 'region', width: 150 },
  { title: '搜索量', key: 'search_volume', width: 100 },
  { title: '有效性', key: 'is_valid', width: 100 },
  { title: '使用状态', key: 'is_used', width: 100 },
  { title: '操作', key: 'actions', width: 150 },
];

const usedCount = computed(() => generatedKeywords.value.filter((k) => k.is_used).length);
const validCount = computed(() => generatedKeywords.value.filter((k) => k.is_valid).length);

async function fetchRules() {
  try {
    const res = await seoMatrixAPI.getCombinatorialRules();
    const raw = unwrapApiData<any>(res);
    const arr = Array.isArray(raw) ? raw : [];
    rules.value = arr.map((r: any) => ({
      ...r,
      pattern: r.pattern || r.template || '',
      keyword_count: r.keyword_count ?? '—',
    }));
    if (rules.value.length > 0) {
      selectRule(rules.value[0]);
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch rules:', e);
  }
}

async function fetchGeneratedKeywords(ruleId?: string) {
  loading.value = true;
  try {
    const params = {
      rule_id: ruleId || undefined,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    const res = await seoMatrixAPI.getGeneratedKeywords(params);
    const page = unwrapApiData<{ items?: any[]; total?: number }>(res);
    generatedKeywords.value = page?.items || [];
    pagination.value.total = page?.total || 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch generated keywords:', e);
  } finally {
    loading.value = false;
  }
}

function selectRule(rule: any) {
  selectedRule.value = rule;
  pagination.value.current = 1;
  fetchGeneratedKeywords(rule.id);
}

function handleTableChange(paginationInfo: any) {
  pagination.value.current = paginationInfo.current;
  pagination.value.pageSize = paginationInfo.pageSize;
  fetchGeneratedKeywords(selectedRule.value?.id);
}

async function generateKeywords() {
  try {
    await seoMatrixAPI.generateKeywords({
      rule_id: generateForm.rule_id,
      count: generateForm.count,
      region_scope: generateForm.region_scope,
    });
    showGenerateModal.value = false;
    fetchGeneratedKeywords(selectedRule.value?.id);
    alert('关键词生成成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to generate keywords:', e);
    alert('生成失败');
  }
}

async function saveRule() {
  try {
    if (editingRule.value) {
      await seoMatrixAPI.updateRule(editingRule.value.id, ruleForm);
    } else {
      await seoMatrixAPI.createRule(ruleForm);
    }
    showRuleModal.value = false;
    resetRuleForm();
    fetchRules();
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to save rule:', e);
    alert('保存失败');
  }
}

function resetRuleForm() {
  editingRule.value = null;
  ruleForm.name = '';
  ruleForm.pattern_type = 'region_keyword';
  ruleForm.pattern = '';
  ruleForm.remark = '';
}

function editKeyword(record: any) {
  editingGenKeyword.value = record;
  genKeywordForm.keyword = record?.keyword ?? '';
  showKeywordEditModal.value = true;
}

function saveGenKeywordEdit() {
  const text = genKeywordForm.keyword.trim();
  if (!text) {
    message.warning('请输入关键词');
    return;
  }
  if (editingGenKeyword.value) {
    editingGenKeyword.value.keyword = text;
    message.success('关键词已更新');
  }
  showKeywordEditModal.value = false;
}

async function deleteKeyword(record: any) {
  if (!confirm('确定要删除这个关键词吗？')) return;
  try {
    await seoMatrixAPI.deleteGeneratedKeyword(record.id);
    fetchGeneratedKeywords(selectedRule.value?.id);
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to delete keyword:', e);
    alert('删除失败');
  }
}

async function batchDelete() {
  if (selectedKeys.value.length === 0) {
    alert('请选择要删除的关键词');
    return;
  }
  if (!confirm(`确定要删除选中的 ${selectedKeys.value.length} 个关键词吗？`)) return;
  try {
    await seoMatrixAPI.batchDeleteKeywords(selectedKeys.value);
    selectedKeys.value = [];
    fetchGeneratedKeywords(selectedRule.value?.id);
    alert('删除成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to batch delete:', e);
    alert('删除失败');
  }
}

async function regenerate() {
  if (!selectedRule.value) {
    alert('请先选择一个规则');
    return;
  }
  try {
    await seoMatrixAPI.regenerateKeywords(selectedRule.value.id);
    fetchGeneratedKeywords(selectedRule.value.id);
    alert('重新生成成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to regenerate:', e);
    alert('重新生成失败');
  }
}

function refreshData() {
  fetchRules();
}

async function seedDachengKeywords() {
  seedingBelt.value = true;
  try {
    const res = await seoMatrixAPI.seedIndustryKeywords({
      belt_id: 'all',
      include_ranking: true,
    });
    const data = unwrapApiData<{
      matrix?: {
        generated_keywords?: number;
        districts_missing?: boolean;
        results?: Array<{ generated_keywords?: number; districts_missing?: boolean }>;
      };
      ranking?: { imported?: number };
    }>(res);
    const matrix = data?.matrix;
    const gen =
      matrix?.generated_keywords
      ?? (matrix?.results || []).reduce((s, r) => s + (r.generated_keywords ?? 0), 0)
      ?? 0;
    const rank = data?.ranking?.imported ?? 0;
    message.success(`大城+河间词库已入库：矩阵词 ${gen} 条，排名追踪 ${rank} 条`);
    if (data?.matrix?.districts_missing || data?.matrix?.results?.some?.((r) => r.districts_missing)) {
      message.warning('部分县域未匹配，请先在地域管理维护「大城县」「河间市」后再导入组合词');
    }
    fetchRules();
    if (selectedRule.value?.id) {
      fetchGeneratedKeywords(selectedRule.value.id);
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
    message.error('词库导入失败，请确认已登录');
  } finally {
    seedingBelt.value = false;
  }
}

onActivated(() => {
  refreshData();
});
</script>
