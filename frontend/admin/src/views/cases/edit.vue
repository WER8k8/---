/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    :title="isEdit ? '编辑案例' : '添加案例'"
    :subtitle="isEdit ? '修改案例信息' : '创建新的案例'"
    surface="elevated"
  >
    <template #actions>
      <router-link
        to="/cases"
        class="px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50 text-sm font-medium transition-colors"
      >
        返回列表
      </router-link>
    </template>

    <a-card>
      <a-form
        :model="form"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="案例标题"
              :required="true"
            >
              <a-input
                v-model="form.title"
                placeholder="请输入案例标题"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="项目类型"
              :required="true"
            >
              <a-select
                v-model="form.project_type"
                placeholder="请选择项目类型"
              >
                <a-select-option value="residential">
                  住宅项目
                </a-select-option>
                <a-select-option value="commercial">
                  商业项目
                </a-select-option>
                <a-select-option value="industrial">
                  工业项目
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="项目地点">
              <a-input
                v-model="form.location"
                placeholder="请输入项目地点"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="建筑面积 (㎡)">
              <a-input-number
                v-model="form.area"
                :min="0"
                placeholder="建筑面积"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="项目描述">
          <a-textarea
            v-model="form.description"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </a-form-item>
        <a-form-item label="案例详情">
          <a-textarea
            v-model="form.content"
            :rows="8"
            placeholder="请输入案例详情（支持HTML）"
          />
        </a-form-item>
        <a-form-item label="SEO标题">
          <a-input
            v-model="form.meta_title"
            placeholder="请输入SEO标题"
          />
        </a-form-item>
        <a-form-item label="SEO描述">
          <a-textarea
            v-model="form.meta_description"
            :rows="2"
            placeholder="请输入SEO描述"
          />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model="form.is_published">
            发布案例
          </a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isEdit ? '保存修改' : '创建案例' }}
          </a-button>
          <a-button
            class="ml-4"
            @click="handleReset"
          >
            重置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/content') } catch { /* 空状态 */ }
})
import { ref, computed, onMounted } from 'vue';
import { YdPage } from '@/components/youding';
import { useRoute, useRouter } from 'vue-router';
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputNumber as AInputNumber,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Checkbox as ACheckbox,
  Button as AButton,
  Modal,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue';
import { casesAPI } from '@/api';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => route.params.id !== 'new');
const loading = ref(false);

const form = ref({
  title: '',
  project_type: '',
  location: '',
  area: null,
  description: '',
  content: '',
  meta_title: '',
  meta_description: '',
  is_published: false,
});

async function fetchCase(id: string) {
  try {
    const res = await casesAPI.get(id);
    const data = res.data;
    form.value = {
      title: data.title || '',
      project_type: data.project_type || '',
      location: data.location || '',
      area: data.area || null,
      description: data.description || '',
      content: data.content || '',
      meta_title: data.meta_title || '',
      meta_description: data.meta_description || '',
      is_published: data.is_published || false,
    };
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch case:', e);
  }
}

async function handleSubmit() {
  if (!form.value.title || !form.value.project_type) {
    Modal.warning({ title: '提示', content: '请填写必填字段' });
    return;
  }

  loading.value = true;
  try {
    const data = {
      ...form.value,
      slug: form.value.title
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, ''),
    };

    if (isEdit.value) {
      await casesAPI.update(route.params.id as string, data);
      Modal.success({ title: '修改成功', content: '案例信息已更新' });
    } else {
      await casesAPI.create(data);
      Modal.success({ title: '创建成功', content: '案例已创建' });
    }

    router.push('/cases');
  } catch (e: any) {
    Modal.error({ title: '操作失败', content: e.message });
  } finally {
    loading.value = false;
  }
}

function handleReset() {
  form.value = {
    title: '',
    project_type: '',
    location: '',
    area: null,
    description: '',
    content: '',
    meta_title: '',
    meta_description: '',
    is_published: false,
  };
}

onMounted(async () => {
  if (isEdit.value) {
    await fetchCase(route.params.id as string);
  }
});
</script>
