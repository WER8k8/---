/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="系统配置" subtitle="配置系统参数和运行环境设置" surface="elevated">
 <template #actions>
 <a-button @click="resetConfig">重置</a-button>
 <a-button type="primary" :loading="saving" @click="saveConfig">保存配置</a-button>
 </template>
 <div class="config-page">
 <a-alert
 v-if="!backendReady"
 type="warning"
 show-icon
 message="未接后端·本机草稿"
 description="系统配置写入接口不可用，当前修改仅保存在本页内存，刷新后丢失。"
 style="margin-bottom: 16px"
 />
 <div class="config-sections">
 <div
 class="config-section"
 v-for="section in configSections"
 :key="section.name"
 >
 <div class="section-header">
 <component :is="section.icon" class="section-icon" />
 <h2 class="section-title">{{ section.name }}</h2>
 </div>
 <a-form :model="section.form" :layout="'vertical'" class="config-form">
 <a-form-item
 v-for="item in section.items"
 :key="item.key"
 :label="item.label"
 :tooltip="item.description"
 >
 <template v-if="item.type === 'switch'">
 <a-switch
 v-model:checked="section.form[item.key]"
 :disabled="!backendReady"
 />
 </template>
 <template v-else-if="item.type === 'select'">
 <a-select
 v-model:value="section.form[item.key]"
 class="config-select"
 :disabled="!backendReady"
 >
 <a-select-option
 v-for="option in item.options"
 :key="option.value"
 :value="option.value"
 >
 {{ option.label }}
 </a-select-option>
 </a-select>
 </template>
 <template v-else-if="item.type === 'textarea'">
 <a-textarea
 v-model:value="section.form[item.key]"
 :rows="3"
 class="config-textarea"
 :disabled="!backendReady"
 />
 </template>
 <template v-else>
 <a-input
 v-model:value="section.form[item.key]"
 class="config-input"
 :disabled="!backendReady"
 />
 </template>
 </a-form-item>
 </a-form>
 </div>
 </div>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiPut } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
 GlobalOutlined,
 SafetyOutlined,
 CloudOutlined,
 BellOutlined,
} from '@ant-design/icons-vue';

interface ConfigItem {
 key: string;
 label: string;
 description: string;
 type: string;
 options?: { value: string; label: string }[];
}

interface ConfigSection {
 name: string;
 icon: any;
 form: Record<string, any>;
 items: ConfigItem[];
}

const CONFIG_PREFIX = 'sys.';

function buildSections(): ConfigSection[] {
 return [
 {
 name: '基本设置',
 icon: GlobalOutlined,
 form: reactive({
 siteName: 'Trae智能开发平台',
 siteDesc: 'AI驱动的智能开发工具',
 defaultLanguage: 'zh-CN',
 }),
 items: [
 { key: 'siteName', label: '站点名称', description: '系统显示的站点名称', type: 'input' },
 { key: 'siteDesc', label: '站点描述', description: '站点的简短描述', type: 'textarea' },
 {
 key: 'defaultLanguage',
 label: '默认语言',
 description: '系统默认显示语言',
 type: 'select',
 options: [
 { value: 'zh-CN', label: '中文' },
 { value: 'en-US', label: 'English' },
 ],
 },
 ],
 },
 {
 name: '安全设置',
 icon: SafetyOutlined,
 form: reactive({
 enableCaptcha: true,
 sessionTimeout: 30,
 enableRateLimit: true,
 }),
 items: [
 { key: 'enableCaptcha', label: '启用验证码', description: '登录时启用图形验证码', type: 'switch' },
 { key: 'sessionTimeout', label: '会话超时时间', description: '用户会话超时时间（分钟）', type: 'input' },
 { key: 'enableRateLimit', label: '启用限流', description: '启用API请求限流保护', type: 'switch' },
 ],
 },
 {
 name: '存储设置',
 icon: CloudOutlined,
 form: reactive({
 storageType: 'local',
 maxUploadSize: 100,
 enableCompression: true,
 }),
 items: [
 {
 key: 'storageType',
 label: '存储类型',
 description: '文件存储方式',
 type: 'select',
 options: [
 { value: 'local', label: '本地存储' },
 { value: 'oss', label: '阿里云OSS' },
 { value: 'cos', label: '腾讯云COS' },
 ],
 },
 { key: 'maxUploadSize', label: '最大上传大小', description: '单个文件最大上传大小（MB）', type: 'input' },
 { key: 'enableCompression', label: '启用压缩', description: '上传文件自动压缩', type: 'switch' },
 ],
 },
 {
 name: '通知设置',
 icon: BellOutlined,
 form: reactive({
 enableEmailNotify: true,
 enableSmsNotify: false,
 enablePushNotify: true,
 }),
 items: [
 { key: 'enableEmailNotify', label: '启用邮件通知', description: '发送邮件通知', type: 'switch' },
 { key: 'enableSmsNotify', label: '启用短信通知', description: '发送短信通知', type: 'switch' },
 { key: 'enablePushNotify', label: '启用推送通知', description: '发送系统推送通知', type: 'switch' },
 ],
 },
 ];
}

const configSections = ref<ConfigSection[]>(buildSections());
const backendReady = ref(false);
const saving = ref(false);
const idByKey = new Map<string, string>();

function valueTypeOf(raw: unknown): string {
 if (typeof raw === 'boolean') return 'boolean';
 if (typeof raw === 'number') return 'number';
 if (typeof raw === 'string') {
 const t = raw.trim();
 if (t === 'true' || t === 'false') return 'boolean';
 if (t !== '' && !Number.isNaN(Number(t))) return 'number';
 }
 return 'string';
}

function coerceValue(raw: unknown, type: string): any {
 if (type === 'boolean') return raw === true || raw === 'true';
 if (type === 'number') {
 const n = Number(raw);
 return Number.isFinite(n) ? n : 0;
 }
 return String(raw ?? '');
}

async function loadConfig() {
 try {
 const res = await apiGet<any>('/system-config/?limit=100');
 const list: any[] = Array.isArray(res) ? res : res?.data ?? res?.items ?? [];
 backendReady.value = true;
 idByKey.clear();
 for (const row of list) {
 if (!row?.key) continue;
 idByKey.set(String(row.key), String(row.id));
 const shortKey = String(row.key).startsWith(CONFIG_PREFIX)
 ? String(row.key).slice(CONFIG_PREFIX.length)
 : String(row.key);
 for (const section of configSections.value) {
 if (shortKey in section.form) {
 const type = valueTypeOf(section.form[shortKey]);
 section.form[shortKey] = coerceValue(row.value, type);
 }
 }
 }
 } catch {
 backendReady.value = false;
 }
}

async function upsertOne(key: string, value: unknown, value_type: string) {
 const fullKey = CONFIG_PREFIX + key;
 const strVal = value_type === 'boolean' ? String(!!value) : String(value ?? '');
 const existingId = idByKey.get(fullKey);
 if (existingId) {
 const q = new URLSearchParams({ value: strVal, value_type });
 await apiPut(`/system-config/${existingId}?${q.toString()}`);
 } else {
 const q = new URLSearchParams({
 key: fullKey,
 value: strVal,
 value_type,
 description: `admin-config:${key}`,
 is_public: 'false',
 });
 const created = await apiPost<any>(`/system-config/?${q.toString()}`);
 if (created?.id) idByKey.set(fullKey, String(created.id));
 }
}

async function saveConfig() {
 if (!backendReady.value) {
 message.warning('未接后端·本机草稿，无法持久化保存');
 return;
 }
 saving.value = true;
 try {
 for (const section of configSections.value) {
 for (const item of section.items) {
 const raw = section.form[item.key];
 const value_type = valueTypeOf(raw);
 await upsertOne(item.key, raw, value_type);
 }
 }
 await loadConfig();
 message.success('配置已保存并回读确认');
 } catch (e: any) {
 message.error(e?.message || '配置保存失败');
 } finally {
 saving.value = false;
 }
}

const resetConfig = () => {
 configSections.value = buildSections();
 void loadConfig();
};

onMounted(async () => {
 await loadConfig();
});
</script>

<style scoped lang="scss">
.config-page {
 padding: 24px;
}

.config-sections {
 display: grid;
 grid-template-columns: repeat(2, 1fr);
 gap: 24px;
 margin-bottom: 24px;

 .config-section {
 background: #fff;
 border-radius: 12px;
 padding: 24px;
 box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

 .section-header {
 display: flex;
 align-items: center;
 gap: 12px;
 margin-bottom: 20px;
 padding-bottom: 16px;
 border-bottom: 1px solid #f3f4f6;

 .section-icon {
 width: 32px;
 height: 32px;
 border-radius: 8px;
 background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
 display: flex;
 align-items: center;
 justify-content: center;
 font-size: 16px;
 color: #fff;
 }

 .section-title {
 font-size: 16px;
 font-weight: 500;
 color: #1f2937;
 margin: 0;
 }
 }

 .config-form {
 .config-select,
 .config-input,
 .config-textarea {
 width: 100%;
 }
 }
 }
}

@media (max-width: 1024px) {
 .config-sections {
 grid-template-columns: 1fr;
 }
}
</style>
