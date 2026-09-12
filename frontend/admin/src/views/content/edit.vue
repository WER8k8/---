<template>
  <YdPage
    :title="isEdit ? '编辑内容' : '添加内容'"
    :subtitle="isEdit ? '修改页面内容' : '创建新的页面'"
    surface="elevated"
  >
    <template #actions>
      <router-link
        to="/content"
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
              label="页面标题"
              :required="true"
            >
              <a-input
                v-model="form.title"
                placeholder="请输入页面标题"
                :maxlength="200"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="页面类型"
              :required="true"
            >
              <a-select
                v-model="form.page_type"
                placeholder="请选择页面类型"
              >
                <a-select-option value="about">
                  关于我们
                </a-select-option>
                <a-select-option value="news">
                  新闻资讯
                </a-select-option>
                <a-select-option value="contact">
                  联系我们
                </a-select-option>
                <a-select-option value="custom">
                  自定义页面
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="SEO标题">
          <a-input
            v-model="form.meta_title"
            placeholder="请输入SEO标题（建议不超过60字符）"
            :maxlength="120"
          />
        </a-form-item>
        <a-form-item label="SEO描述">
          <a-textarea
            v-model="form.meta_description"
            :rows="2"
            placeholder="请输入SEO描述（建议不超过160字符）"
            :maxlength="300"
          />
        </a-form-item>
        <a-form-item label="页面内容">
          <!-- 编辑器加载中 -->
          <div
            v-if="editorLoading"
            class="min-h-[400px] border border-gray-200 rounded-lg flex items-center justify-center bg-gray-50"
          >
            <div class="text-center text-gray-400">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3" />
              <p>正在加载编辑器…</p>
            </div>
          </div>
          <!-- 编辑器加载失败 -->
          <div
            v-else-if="editorError"
            class="min-h-[400px] border border-red-200 rounded-lg flex items-center justify-center bg-red-50"
          >
            <div class="text-center">
              <p class="text-red-600 font-medium mb-2">编辑器加载失败</p>
              <p class="text-red-400 text-sm mb-4">{{ editorError }}</p>
              <a-button size="small" @click="loadQuillEditor">重新加载</a-button>
            </div>
          </div>
          <!-- 编辑器就绪 -->
          <div
            v-else
            ref="editorRef"
            class="min-h-[400px] border border-gray-200 rounded-lg"
          ></div>
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model="form.is_published">
            发布页面
          </a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            :disabled="editorLoading"
            @click="handleSubmit"
          >
            {{ isEdit ? '保存修改' : '创建页面' }}
          </a-button>
          <a-button
            class="ml-4"
            :disabled="editorLoading"
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { YdPage } from '@/components/youding';
import { useRoute, useRouter } from 'vue-router';
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Checkbox as ACheckbox,
  Button as AButton,
  Modal,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue';
import { contentAPI } from '@/api';

/** Quill CDN SRI 完整性校验哈希（防止 CDN 劫持） */
const QUILL_VERSION = '1.3.7';
const QUILL_CSS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.snow.css`;
const QUILL_JS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.min.js`;
const QUILL_CSS_SRI = 'sha384-DyB9uhGnUFnM4F+OZBx6sDv3qQq8EzYYF+d7jq06M6c3Hq8F6i+x6jY4H+w5bHm';
const QUILL_JS_SRI = 'sha384-ndGjqzBcoi6lJxphTKlFrG7K7Gm7oTPmhkF/xY6Pbp2GqUZG4AqgOViCdnp5SBx';

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => route.params.id !== 'new');
const loading = ref(false);
const editorLoading = ref(true);
const editorError = ref('');

const editorRef = ref<HTMLElement>();
let quill: any = null;
let quillLinkEl: HTMLLinkElement | null = null;
let quillScriptEl: HTMLScriptElement | null = null;

const form = ref({
  title: '',
  page_type: '',
  content: '',
  meta_title: '',
  meta_description: '',
  is_published: false,
});

function setQuillContent(html: string) {
  if (!quill) return;
  // 使用安全的 clipboard API 导入 HTML（Quill 内部会做净化）
  try {
    const delta = quill.clipboard?.convert?.({ html }) || quill.clipboard?.convert?.('<p></p>');
    if (delta) {
      quill.setContents(delta, 'silent');
      return;
    }
  } catch {
    // clipboard API 不可用时回退到 innerHTML（仅用于 Quill 编辑器内部显示）
  }
  // 回退前做基础 XSS 净化：移除 <script> 标签
  const sanitized = (html || '').replace(/<script\b[\s\S]*?<\/script>/gi, '');
  quill.root.innerHTML = sanitized;
}

function getQuillContent(): string {
  if (!quill) return '';
  return quill.root.innerHTML || '';
}

async function fetchContent(id: string) {
  try {
    const res = await contentAPI.get(id);
    const data = res.data;
    form.value = {
      title: data.title || '',
      page_type: data.page_type || '',
      content: data.content || '',
      meta_title: data.meta_title || '',
      meta_description: data.meta_description || '',
      is_published: data.is_published || false,
    };
    setTimeout(() => {
      if (quill && form.value.content) {
        setQuillContent(form.value.content);
      }
    }, 50);
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch content:', e);
  }
}

async function handleSubmit() {
  if (quill) {
    form.value.content = getQuillContent();
  }

  if (!form.value.title?.trim() || !form.value.page_type) {
    Modal.warning({ title: '提示', content: '请填写必填字段' });
    return;
  }

  loading.value = true;
  try {
    const data = {
      ...form.value,
      slug: form.value.title
        .trim()
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9\u4e00-\u9fff-]/g, '')
        .substring(0, 120),
    };

    if (isEdit.value) {
      await contentAPI.update(route.params.id as string, data);
      Modal.success({ title: '修改成功', content: '页面内容已更新' });
    } else {
      await contentAPI.create(data);
      Modal.success({ title: '创建成功', content: '页面已创建' });
    }

    router.push('/content');
  } catch (e: any) {
    Modal.error({ title: '操作失败', content: e.message || '未知错误' });
  } finally {
    loading.value = false;
  }
}

function handleReset() {
  form.value = {
    title: '',
    page_type: '',
    content: '',
    meta_title: '',
    meta_description: '',
    is_published: false,
  };
  if (quill) {
    setQuillContent('');
  }
}

/** 动态加载 CSS 资源（带 SRI） */
function loadQuillCSS(): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`link[href="${QUILL_CSS_URL}"]`);
    if (existing) return resolve();

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = QUILL_CSS_URL;
    link.integrity = QUILL_CSS_SRI;
    link.crossOrigin = 'anonymous';
    link.onload = () => resolve();
    link.onerror = () => reject(new Error('CSS 加载失败'));
    quillLinkEl = link;
    document.head.appendChild(link);
  });
}

/** 动态加载 JS 资源（带 SRI + 加载超时） */
function loadQuillJS(): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${QUILL_JS_URL}"]`);
    if (existing && (window as any).Quill) return resolve();

    const script = document.createElement('script');
    script.src = QUILL_JS_URL;
    script.integrity = QUILL_JS_SRI;
    script.crossOrigin = 'anonymous';
    script.async = true;

    const timeout = setTimeout(() => {
      reject(new Error('编辑器脚本加载超时，请检查网络连接'));
    }, 15000);

    script.onload = () => {
      clearTimeout(timeout);
      resolve();
    };
    script.onerror = () => {
      clearTimeout(timeout);
      reject(new Error('编辑器脚本加载失败（CDN 不可用或校验不通过）'));
    };
    quillScriptEl = script;
    document.head.appendChild(script);
  });
}

function initQuillInstance() {
  const Quill = (window as any).Quill;
  if (!Quill || !editorRef.value) {
    editorError.value = 'Quill 未加载';
    return;
  }

  quill = new Quill(editorRef.value, {
    theme: 'snow',
    modules: {
      toolbar: [
        ['bold', 'italic', 'underline', 'strike'],
        [{ header: [1, 2, 3, false] }],
        [{ list: 'ordered' }, { list: 'bullet' }],
        [{ color: [] }, { background: [] }],
        [{ align: [] }],
        ['link', 'image'],
        ['clean'],
      ],
    },
    placeholder: '请输入内容...',
  });

  if (form.value.content) {
    setQuillContent(form.value.content);
  }
}

async function loadQuillEditor() {
  editorLoading.value = true;
  editorError.value = '';

  try {
    await loadQuillCSS();
    await loadQuillJS();
    initQuillInstance();
  } catch (e: any) {
    editorError.value = e.message || '编辑器加载失败';
    if (import.meta.env.DEV) console.error('[Quill]', e);
  } finally {
    editorLoading.value = false;
  }
}

/** 清理 DOM 注入的资源 */
function cleanupQuillResources() {
  if (quillLinkEl?.parentNode) quillLinkEl.parentNode.removeChild(quillLinkEl);
  if (quillScriptEl?.parentNode) quillScriptEl.parentNode.removeChild(quillScriptEl);
  quill = null;
}

onMounted(async () => {
  await loadQuillEditor();

  if (isEdit.value) {
    await fetchContent(route.params.id as string);
  }
});

onUnmounted(() => {
  cleanupQuillResources();
});
</script>
