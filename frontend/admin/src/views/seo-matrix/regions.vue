/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="地域词库" subtitle="管理全国省市区三级地域数据和行业关键词" surface="elevated">
    <template #actions>
      <a-button @click="refreshData">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新
      </a-button>
      <a-button type="primary" class="gradient-primary" @click="showImportModal = true">
        <ImportOutlined class="w-4 h-4 mr-2" />
        批量导入
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1">
        <div class="bg-white rounded-2xl shadow-card p-4 sticky top-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            地域选择
          </h3>

          <div class="space-y-3">
            <a-select
              v-model:value="selectedProvince"
              placeholder="选择省份"
              class="w-full"
              @change="onProvinceChange"
            >
              <a-select-option value="">
                全部省份
              </a-select-option>
              <a-select-option
                v-for="p in provinces"
                :key="p.id"
                :value="p.id"
              >
                {{ p.name }}
              </a-select-option>
            </a-select>

            <a-select
              v-model:value="selectedCity"
              placeholder="选择城市"
              class="w-full"
              @change="onCityChange"
              :disabled="!selectedProvince"
            >
              <a-select-option value="">
                全部城市
              </a-select-option>
              <a-select-option
                v-for="c in cities"
                :key="c.id"
                :value="c.id"
              >
                {{ c.name }}
              </a-select-option>
            </a-select>

            <a-select
              v-model:value="selectedDistrict"
              placeholder="选择区县"
              class="w-full"
              :disabled="!selectedCity"
            >
              <a-select-option value="">
                全部区县
              </a-select-option>
              <a-select-option
                v-for="d in districts"
                :key="d.id"
                :value="d.id"
              >
                {{ d.name }}
              </a-select-option>
            </a-select>
          </div>

          <div class="mt-6 pt-6 border-t border-gray-100">
            <h4 class="font-medium text-gray-700 mb-3">
              关键词分组
            </h4>
            <div class="space-y-2">
              <a-checkbox-group v-model:value="selectedGroups">
                <a-checkbox
                  v-for="group in keywordGroups"
                  :key="group.id"
                  :value="group.id"
                >
                  {{ group.name }} ({{ group.count }})
                </a-checkbox>
              </a-checkbox-group>
            </div>
          </div>
        </div>
      </div>

      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-gray-900">
              地域关键词列表
            </h3>
            <a-button
              type="primary"
              size="small"
              @click="showAddModal = true"
            >
              <PlusOutlined class="w-4 h-4 mr-1" />
              添加关键词
            </a-button>
          </div>

          <a-table
            :columns="columns"
            :data-source="keywords"
            :pagination="pagination"
            :loading="loading"
            row-key="id"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'region'">
                <span class="text-gray-600">{{ record.province_name }} / {{ record.city_name }} /
                  {{ record.district_name }}</span>
              </template>
              <template v-if="column.key === 'keyword'">
                <span class="font-medium text-gray-900">{{ record.keyword }}</span>
              </template>
              <template v-if="column.key === 'group'">
                <span class="text-gray-500 text-sm">{{ record.group_name }}</span>
              </template>
              <template v-if="column.key === 'status'">
                <span
                  :class="
                    record.is_active
                      ? 'bg-success-50 text-success-600'
                      : 'bg-gray-100 text-gray-500'
                  "
                  class="px-3 py-1 rounded-full text-sm font-medium"
                >
                  {{ record.is_active ? '启用' : '禁用' }}
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
                    :type="record.is_active ? 'default' : 'primary'"
                    @click="toggleKeyword(record)"
                  >
                    {{ record.is_active ? '禁用' : '启用' }}
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
      v-model:open="showAddModal"
      :title="editingKeyword ? '编辑关键词' : '添加关键词'"
      @ok="saveKeyword"
    >
      <a-form
        :model="keywordForm"
        layout="vertical"
      >
        <a-form-item label="地域">
          <a-cascader
            v-model:value="keywordForm.region"
            :options="regionOptions"
            placeholder="选择省/市/区"
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
          />
        </a-form-item>
        <a-form-item label="关键词">
          <a-input
            v-model:value="keywordForm.keyword"
            placeholder="输入关键词"
          />
        </a-form-item>
        <a-form-item label="关键词分组">
          <a-select
            v-model:value="keywordForm.group_id"
            placeholder="选择分组"
          >
            <a-select-option
              v-for="g in keywordGroups"
              :key="g.id"
              :value="g.id"
            >
              {{ g.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea
            v-model:value="keywordForm.remark"
            placeholder="备注信息"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showImportModal"
      title="批量导入关键词"
      @ok="importKeywords"
    >
      <div class="space-y-4">
        <p class="text-gray-500">
          请上传CSV文件，格式：省份,城市,区县,关键词,分组
        </p>
        <a-upload
          :before-upload="beforeUpload"
          :show-upload-list="false"
          accept=".csv,.txt"
        >
          <a-button>
            <UploadOutlined class="w-4 h-4 mr-2" />
            选择文件
          </a-button>
        </a-upload>
        <div
          v-if="importFile"
          class="text-success-500"
        >
          已选择: {{ importFile.name }}
        </div>
      </div>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onActivated } from 'vue';
import {
  ReloadOutlined,
  ImportOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import { seoMatrixAPI, unwrapApiData } from '@/api';

function listPayload<T>(raw: unknown): T[] {
  if (Array.isArray(raw)) return raw as T[];
  if (raw && typeof raw === 'object' && Array.isArray((raw as any).items))
    return (raw as any).items as T[];
  return [];
}

function pagePayload(raw: unknown): { items: any[]; total: number } {
  if (raw && typeof raw === 'object') {
    const o = raw as Record<string, unknown>;
    return {
      items: Array.isArray(o.items) ? (o.items as any[]) : [],
      total: typeof o.total === 'number' ? o.total : 0,
    };
  }
  return { items: [], total: 0 };
}

const provinces = ref<any[]>([]);
const cities = ref<any[]>([]);
const districts = ref<any[]>([]);
const keywordGroups = ref<any[]>([]);
const keywords = ref<any[]>([]);
const selectedGroups = ref<any[]>([]);

const selectedProvince = ref('');
const selectedCity = ref('');
const selectedDistrict = ref('');

const loading = ref(false);
const showAddModal = ref(false);
const showImportModal = ref(false);
const importFile = ref<File | null>(null);

const editingKeyword = ref<any>(null);
const keywordForm = reactive({
  region: [] as (string | number)[],
  keyword: '',
  group_id: '',
  remark: '',
});

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { title: '地域', key: 'region', width: 250 },
  { title: '关键词', key: 'keyword', width: 200 },
  { title: '分组', key: 'group', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 200 },
];

const regionOptions = computed(() => {
  return provinces.value.map((p) => ({
    id: p.id,
    name: p.name,
    children: cities.value
      .filter((c) => c.province_id === p.id)
      .map((c) => ({
        id: c.id,
        name: c.name,
        children: districts.value
          .filter((d) => d.city_id === c.id)
          .map((d) => ({ id: d.id, name: d.name })),
      })),
  }));
});

async function fetchProvinces() {
  try {
    const res = await seoMatrixAPI.getProvinces();
    provinces.value = listPayload(unwrapApiData(res));
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch provinces:', e);
  }
}

async function fetchCities(provinceId: string) {
  if (!provinceId) {
    cities.value = [];
    districts.value = [];
    return;
  }
  try {
    const res = await seoMatrixAPI.getCities(provinceId);
    cities.value = listPayload(unwrapApiData(res));
    districts.value = [];
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch cities:', e);
  }
}

async function fetchDistricts(cityId: string) {
  if (!cityId) {
    districts.value = [];
    return;
  }
  try {
    const res = await seoMatrixAPI.getDistricts(cityId);
    districts.value = listPayload(unwrapApiData(res));
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch districts:', e);
  }
}

async function fetchKeywordGroups() {
  try {
    const res = await seoMatrixAPI.getKeywordGroups();
    const pg = pagePayload(unwrapApiData(res));
    keywordGroups.value = pg.items;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch keyword groups:', e);
  }
}

async function fetchKeywords() {
  loading.value = true;
  try {
    const params = {
      province_id: selectedProvince.value || undefined,
      city_id: selectedCity.value || undefined,
      district_id: selectedDistrict.value || undefined,
      group_ids: selectedGroups.value.length > 0 ? selectedGroups.value.join(',') : undefined,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    const res = await seoMatrixAPI.getKeywords(params);
    const pg = pagePayload(unwrapApiData(res));
    keywords.value = pg.items;
    pagination.value.total = pg.total;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch keywords:', e);
  } finally {
    loading.value = false;
  }
}

function onProvinceChange(value: unknown) {
  const v = value == null ? '' : String(value);
  selectedProvince.value = v;
  selectedCity.value = '';
  selectedDistrict.value = '';
  fetchCities(v);
  fetchKeywords();
}

function onCityChange(value: unknown) {
  const v = value == null ? '' : String(value);
  selectedCity.value = v;
  selectedDistrict.value = '';
  fetchDistricts(v);
  fetchKeywords();
}

function handleTableChange(paginationInfo: any) {
  pagination.value.current = paginationInfo.current;
  pagination.value.pageSize = paginationInfo.pageSize;
  fetchKeywords();
}

function editKeyword(record: any) {
  editingKeyword.value = record;
  keywordForm.region = [record.province_id, record.city_id, record.district_id];
  keywordForm.keyword = record.keyword;
  keywordForm.group_id = record.group_id;
  keywordForm.remark = record.remark || '';
  showAddModal.value = true;
}

async function saveKeyword() {
  try {
    if (editingKeyword.value) {
      await seoMatrixAPI.updateKeyword(editingKeyword.value.id, {
        district_id: keywordForm.region[2],
        keyword: keywordForm.keyword,
        group_id: keywordForm.group_id,
        remark: keywordForm.remark,
      });
    } else {
      await seoMatrixAPI.createKeyword({
        district_id: keywordForm.region[2],
        keyword: keywordForm.keyword,
        group_id: keywordForm.group_id,
        remark: keywordForm.remark,
      });
    }
    showAddModal.value = false;
    resetKeywordForm();
    fetchKeywords();
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to save keyword:', e);
    alert('保存失败');
  }
}

function resetKeywordForm() {
  editingKeyword.value = null;
  keywordForm.region = [];
  keywordForm.keyword = '';
  keywordForm.group_id = '';
  keywordForm.remark = '';
}

async function toggleKeyword(record: any) {
  try {
    await seoMatrixAPI.updateKeyword(record.id, { is_active: !record.is_active });
    fetchKeywords();
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to toggle keyword:', e);
  }
}

async function deleteKeyword(record: any) {
  if (!confirm('确定要删除这个关键词吗？')) return;
  try {
    await seoMatrixAPI.deleteKeyword(record.id);
    fetchKeywords();
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to delete keyword:', e);
    alert('删除失败');
  }
}

function beforeUpload(file: File) {
  importFile.value = file;
  return false;
}

async function importKeywords() {
  if (!importFile.value) {
    alert('请选择文件');
    return;
  }
  try {
    const formData = new FormData();
    formData.append('file', importFile.value);
    await seoMatrixAPI.importKeywords(formData);
    showImportModal.value = false;
    importFile.value = null;
    fetchKeywords();
    alert('导入成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to import keywords:', e);
    alert('导入失败');
  }
}

function refreshData() {
  fetchProvinces();
  fetchKeywordGroups();
  fetchKeywords();
}

onActivated(() => {
  refreshData();
});
</script>
