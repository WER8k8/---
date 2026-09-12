<template>
  <YdPage :title="pageTitle" :subtitle="pageSubtitle" surface="elevated">
  <div class="fm-page p-6 space-y-6">
    <!-- 统计卡片 -->
    <a-row :gutter="[16, 16]">
      <a-col :xs="12" :sm="6">
        <a-card size="small" class="stat-card">
          <a-statistic title="全部文件" :value="stats.total_files" suffix="个" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card size="small" class="stat-card">
          <a-statistic
            :title="tenantMediaSpace?.kind === 'video' ? '视频' : tenantMediaSpace?.kind === 'image' ? '图片' : '图片'"
            :value="primaryMediaCount"
            suffix="个"
          />
        </a-card>
      </a-col>
      <a-col v-if="!tenantMediaSpace" :xs="12" :sm="6">
        <a-card size="small" class="stat-card">
          <a-statistic title="文档" :value="stats.document_count" suffix="个" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card size="small" class="stat-card">
          <a-statistic title="总大小" :value="stats.total_size_display" />
        </a-card>
      </a-col>
    </a-row>

    <a-alert
      v-if="isPlatformAdmin && !tenantScopeFilter"
      type="warning"
      show-icon
      class="mb-0"
      message="平台超管：上传前请先选择「租户分组」，否则文件会写入 platform 公共目录"
    />

    <a-alert
      v-if="storageProfile"
      type="info"
      show-icon
      class="storage-region-alert"
      :message="storageRegionMessage"
      :description="storageRegionHint"
    />

    <!-- 上传区域 -->
    <a-card size="small" :title="uploadCardTitle">
      <div
        class="dropzone"
        :class="{ 'dropzone-active': dragOver }"
        @dragenter.prevent="dragOver = true"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
        @click="triggerUpload"
      >
        <input
          ref="fileInputRef"
          type="file"
          multiple
          :accept="uploadAccept"
          style="display: none"
          @change="onFileChange"
        />
        <div class="dropzone-content">
          <cloud-upload-outlined class="dropzone-icon" />
          <p class="dropzone-text">
            拖拽文件到此处，或 <em>点击选择文件</em>
          </p>
          <p class="dropzone-hint">
            {{ dropzoneHint }}
          </p>
        </div>
      </div>

      <!-- 上传进度列表 -->
      <div v-if="uploadQueue.length > 0" class="upload-queue mt-4">
        <a-table
          :data-source="uploadQueue"
          :columns="uploadColumns"
          row-key="id"
          size="small"
          :pagination="false"
          :locale="{ emptyText: '暂无上传任务' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <span class="mono">{{ record.name }}</span>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag v-if="record.status === 'uploading'" color="processing">上传中</a-tag>
              <a-tag v-else-if="record.status === 'done'" color="success">完成</a-tag>
              <a-tag v-else-if="record.status === 'error'" color="error">失败</a-tag>
              <a-tag v-else color="default">等待</a-tag>
            </template>
            <template v-if="column.key === 'progress'">
              <a-progress
                v-if="record.status === 'uploading'"
                :percent="record.progress"
                size="small"
                style="width: 120px"
              />
              <span v-else-if="record.status === 'done'" class="text-green-600">已完成</span>
              <span v-else-if="record.status === 'error'" class="text-red-500">{{ record.error || '上传失败' }}</span>
              <span v-else class="text-gray-400">等待中</span>
            </template>
          </template>
        </a-table>
      </div>
    </a-card>

    <!-- 工具栏 -->
    <a-card size="small" :body-style="{ padding: '12px 16px' }">
      <a-row :gutter="[12, 12]" align="middle">
        <a-col :xs="24" :sm="8">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索文件名..."
            allow-clear
            @search="handleSearch"
            @press-enter="handleSearch"
          />
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-select
            v-if="isPlatformAdmin"
            v-model:value="tenantScopeFilter"
            style="width: 100%"
            placeholder="租户分组"
            allow-clear
            show-search
            option-filter-prop="label"
            @change="(v) => handleTenantScopeFilter(v as string)"
          >
            <a-select-option
              v-for="opt in tenantScopeOptions"
              :key="opt.tenant_id"
              :value="opt.tenant_id"
              :label="tenantScopeLabel(opt.tenant_id)"
            >
              {{ tenantScopeLabel(opt.tenant_id) }}（{{ opt.file_count }}）
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-select
            v-model:value="storageRegionFilter"
            style="width: 100%"
            placeholder="存储分区"
            allow-clear
            @change="(v) => handleStorageRegionFilter(v as string)"
          >
            <a-select-option value="cn">国内（七牛）</a-select-option>
            <a-select-option value="global">海外（R2）</a-select-option>
          </a-select>
        </a-col>
        <a-col v-if="!tenantMediaSpace" :xs="12" :sm="6">
          <a-select
            v-model:value="fileTypeFilter"
            style="width: 100%"
            placeholder="分类筛选"
            allow-clear
            @change="(v) => handleFilterChange(v as string)"
          >
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="4">
          <a-button-group>
            <a-button
              :type="viewMode === 'grid' ? 'primary' : 'default'"
              @click="viewMode = 'grid'"
            >
              <template #icon><appstore-outlined /></template>
            </a-button>
            <a-button
              :type="viewMode === 'list' ? 'primary' : 'default'"
              @click="viewMode = 'list'"
            >
              <template #icon><unordered-list-outlined /></template>
            </a-button>
          </a-button-group>
        </a-col>
        <a-col :xs="24" :sm="6" class="text-right">
          <a-button type="primary" ghost @click="refreshList">
            <template #icon><reload-outlined /></template>
            刷新
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 文件列表 - 网格视图 -->
    <div v-if="viewMode === 'grid'">
      <a-row :gutter="[16, 16]" v-if="fileList.length > 0">
        <a-col
          v-for="item in fileList"
          :key="item.id"
          :xs="12"
          :sm="8"
          :md="6"
          :lg="4"
        >
          <div class="file-card" @contextmenu.prevent="showContextMenu($event, item)">
            <!-- 缩略图区域 -->
            <div class="file-thumb" :class="{ 'file-thumb-doc': item.category !== 'image' && item.category !== 'video' }">
              <video
                v-if="item.category === 'video'"
                :src="resolveAssetUrl(item.url)"
                class="thumb-video"
                muted
                preload="metadata"
                @error="onVideoThumbError($event)"
              />
              <img
                v-else-if="item.category === 'image'"
                :src="resolveAssetUrl(item.url)"
                :alt="item.original_name"
                class="thumb-img"
                @error="onImgError($event)"
              />
              <div v-else class="file-type-icon">
                <file-text-outlined v-if="item.extension === 'pdf'" style="font-size: 36px; color: #f5222d" />
                <file-text-outlined v-else style="font-size: 36px; color: #1890ff" />
              </div>
            </div>
            <div class="file-info">
              <a-tooltip :title="item.original_name">
                <p class="file-name">{{ item.original_name }}</p>
              </a-tooltip>
              <p class="file-meta">{{ item.size_display }} | {{ formatTime(item.uploaded_at) }}</p>
              <a-tag v-if="isPlatformAdmin && item.tenant_id" size="small" class="mt-1">
                {{ tenantScopeLabel(item.tenant_id) }}
              </a-tag>
              <a-tag v-if="item.storage_region" size="small" class="mt-1">
                {{ item.storage_region === 'global' ? '海外 R2' : '国内' }}
              </a-tag>
            </div>
            <!-- 操作 -->
            <div class="file-actions">
              <a-tooltip title="复制链接">
                <a-button type="link" size="small" @click="copyUrl(item.url)">
                  <link-outlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button type="link" size="small" danger @click="confirmDelete(item)">
                  <delete-outlined />
                </a-button>
              </a-tooltip>
            </div>
          </div>
        </a-col>
      </a-row>
      <a-empty v-else-if="!loading" description="暂无文件" class="py-8" />
    </div>

    <!-- 文件列表 - 列表视图 -->
    <a-table
      v-if="viewMode === 'list'"
      :data-source="fileList"
      :columns="listColumns"
      row-key="id"
      size="small"
      :loading="loading"
      :pagination="false"
      :locale="{ emptyText: '暂无文件' }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'thumb'">
          <video
            v-if="record.category === 'video'"
            :src="resolveAssetUrl(record.url)"
            style="width: 48px; height: 48px; object-fit: cover; border-radius: 4px;"
            muted
            preload="metadata"
          />
          <img
            v-else-if="record.category === 'image'"
            :src="resolveAssetUrl(record.url)"
            :alt="record.original_name"
            style="width: 48px; height: 48px; object-fit: cover; border-radius: 4px;"
            @error="onImgError($event)"
          />
          <div v-else class="list-type-icon">
            <file-text-outlined v-if="record.extension === 'pdf'" style="font-size: 24px; color: #f5222d" />
            <file-text-outlined v-else style="font-size: 24px; color: #1890ff" />
          </div>
        </template>
        <template v-if="column.key === 'name'">
          <a-tooltip :title="record.original_name">
            <span class="mono">{{ record.original_name }}</span>
          </a-tooltip>
        </template>
        <template v-if="column.key === 'category'">
          <a-tag v-if="record.category === 'image'" color="blue">图片</a-tag>
          <a-tag v-else-if="record.category === 'document'" color="orange">文档</a-tag>
          <a-tag v-else>其他</a-tag>
        </template>
        <template v-if="column.key === 'tenant'">
          <span v-if="isPlatformAdmin" class="mono">{{ tenantScopeLabel(record.tenant_id) }}</span>
          <span v-else>—</span>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-tooltip title="复制链接">
              <a-button type="link" size="small" @click="copyUrl(record.url)">
                <link-outlined />
              </a-button>
            </a-tooltip>
            <a-tooltip title="删除">
              <a-button type="link" size="small" danger @click="confirmDelete(record)">
                <delete-outlined />
              </a-button>
            </a-tooltip>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 分页 -->
    <div class="text-center" v-if="total > pageSize">
      <a-pagination
        v-model:current="currentPage"
        :page-size="pageSize"
        :total="total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 条`"
        @change="loadFiles"
        @showSizeChange="onPageSizeChange"
      />
    </div>

    <!-- 预览对话框 -->
    <a-modal
      v-model:open="previewVisible"
      :title="previewItem?.original_name || '预览'"
      :footer="null"
      width="720px"
      :destroy-on-close="true"
    >
      <div class="preview-body">
        <video
          v-if="previewItem?.category === 'video'"
          :src="resolveAssetUrl(previewItem?.url || '')"
          class="preview-video"
          controls
        />
        <img
          v-else-if="previewItem?.category === 'image'"
          :src="resolveAssetUrl(previewItem?.url || '')"
          :alt="previewItem?.original_name"
          class="preview-img"
        />
        <div v-else class="preview-file-info">
          <file-text-outlined style="font-size: 64px; color: #1890ff" />
          <p class="mt-2"><strong>{{ previewItem?.original_name }}</strong></p>
          <p>大小: {{ previewItem?.size_display }}</p>
          <p>类型: {{ previewItem?.mime_type }}</p>
          <a-button type="primary" :href="previewItem?.url" target="_blank" class="mt-3">
            下载文件
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { useAuthStore } from '@/stores/auth';
import { PRODUCT_IMAGE_SPACE_SUBTITLE } from '@/constants/productImageSpace';
import { resolveTenantMediaSpaceFromRoute } from '@/constants/tenantMediaSpace';
import {
  CloudUploadOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ReloadOutlined,
  DeleteOutlined,
  LinkOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue';
import { filesAPI } from '@/api';
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

const route = useRoute();
const tenantMediaSpace = computed(() => resolveTenantMediaSpaceFromRoute(route));
const pageTitle = computed(() => tenantMediaSpace.value?.title ?? '文件管理');
const pageSubtitle = computed(() => {
  if (tenantMediaSpace.value) {
    return tenantMediaSpace.value.subtitle;
  }
  return PRODUCT_IMAGE_SPACE_SUBTITLE;
});
const uploadCardTitle = computed(
  () => tenantMediaSpace.value?.uploadCardTitle ?? '上传文件',
);
const uploadAccept = computed(
  () =>
    tenantMediaSpace.value?.uploadAccept ??
    '.jpg,.jpeg,.png,.webp,.gif,.svg,.pdf,.doc,.docx,.mp4,.webm,.mov',
);
const dropzoneHint = computed(() => {
  if (tenantMediaSpace.value) {
    return tenantMediaSpace.value.dropzoneHint;
  }
  return '支持 JPG/PNG/WebP/GIF/SVG/PDF/DOC/DOCX/MP4 等，图片最大 50MB、视频最大 500MB';
});
const allowedUploadExtensions = computed(() => {
  if (tenantMediaSpace.value) {
    return [...tenantMediaSpace.value.allowedExtensions];
  }
  return ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg', 'pdf', 'doc', 'docx', 'mp4', 'webm', 'mov', 'avi', 'mkv'];
});
const maxUploadBytes = computed(() => {
  const mb = tenantMediaSpace.value?.maxUploadMb ?? 50;
  return mb * 1024 * 1024;
});
const primaryMediaCount = computed(() => {
  if (tenantMediaSpace.value?.kind === 'video') {
    return stats.video_count;
  }
  if (tenantMediaSpace.value?.kind === 'image') {
    return stats.image_count;
  }
  return stats.image_count;
});

// ============ 类型定义 ============
interface FileItem {
  id: string;
  original_name: string;
  saved_name: string;
  size: number;
  size_display: string;
  mime_type: string;
  extension: string;
  category: string;
  url: string;
  tenant_id?: string;
  storage_region?: string;
  storage_backend?: string;
  storage_region_label?: string;
  uploaded_by: string;
  uploaded_at: string;
  updated_at: string;
}

interface StorageProfile {
  storage_region: string;
  storage_region_label: string;
  storage_backend: string;
  storage_backend_label: string;
  cloud_configured: boolean;
  cn_available: boolean;
  global_available: boolean;
}

interface UploadItem {
  id: string;
  name: string;
  status: 'pending' | 'uploading' | 'done' | 'error';
  progress: number;
  error?: string;
}

interface FileStats {
  total_files: number;
  total_size: number;
  total_size_display: string;
  image_count: number;
  document_count: number;
  video_count: number;
  other_count: number;
  tenant_scopes?: { tenant_id: string; file_count: number }[];
}

interface TenantScopeOption {
  tenant_id: string;
  file_count: number;
}

const authStore = useAuthStore();
const isPlatformAdmin = computed(() =>
  ['admin', 'super_admin'].includes(authStore.currentRole || ''),
);

// ============ 状态 ============
const loading = ref(false);
const fileList = ref<FileItem[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(24);
const viewMode = ref<'grid' | 'list'>('grid');
const searchKeyword = ref('');
const fileTypeFilter = ref<string | undefined>(
  tenantMediaSpace.value?.defaultFileType ??
    (route.meta.productImageSpaceMode || route.path.includes('/client/product-images')
      ? 'image'
      : route.meta.videoSpaceMode || route.path.includes('/client/video-space')
        ? 'video'
        : undefined),
);
const storageRegionFilter = ref<string | undefined>(undefined);
const tenantScopeFilter = ref<string | undefined>(undefined);
const tenantScopeOptions = ref<TenantScopeOption[]>([]);
const tenantNameMap = ref<Record<string, string>>({});
const storageProfile = ref<StorageProfile | null>(null);
const dragOver = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const uploadQueue = ref<UploadItem[]>([]);
let uploadSeq = 0;
const previewVisible = ref(false);
const previewItem = ref<FileItem | null>(null);

const stats = reactive<FileStats>({
  total_files: 0,
  total_size: 0,
  total_size_display: '0 B',
  image_count: 0,
  document_count: 0,
  video_count: 0,
  other_count: 0,
});

// 列表视图列定义
const listColumns = computed(() => {
  const cols = [
    { title: '预览', key: 'thumb', width: 72 },
    { title: '文件名', key: 'name', ellipsis: true },
    { title: '大小', dataIndex: 'size_display', key: 'size', width: 100 },
    { title: '类型', key: 'category', width: 80 },
  ];
  if (isPlatformAdmin.value) {
    cols.push({ title: '租户', key: 'tenant', width: 120 });
  }
  cols.push(
    { title: '上传时间', dataIndex: 'uploaded_at', key: 'time', width: 170 },
    { title: '操作', key: 'action', width: 120 },
  );
  return cols;
});

const uploadColumns = [
  { title: '文件名', key: 'name', ellipsis: true },
  { title: '状态', key: 'status', width: 90 },
  { title: '进度', key: 'progress', width: 180 },
];

const storageRegionMessage = computed(() => {
  const p = storageProfile.value;
  if (!p) return '';
  return `当前上传分区：${p.storage_region_label}`;
});

const storageRegionHint = computed(() => {
  const p = storageProfile.value;
  if (!p) return '';
  if (p.cloud_configured) {
    return `写入 ${p.storage_backend_label}；国内租户默认七牛，出海/国际化租户默认 R2。`;
  }
  return '云存储密钥未配置，文件暂存本地磁盘；请在服务器配置 QINIU_*（国内）或 MEDIA_R2_*（海外）。';
});

function resolveAssetUrl(url: string): string {
  return resolveMediaAssetUrl(url);
}

// ============ 方法 ============

function tenantScopeLabel(tenantId?: string): string {
  if (!tenantId) return '未分组';
  if (tenantId === 'platform') return '平台公共';
  const name = tenantNameMap.value[tenantId];
  if (name) return `${name}`;
  return tenantId.length > 12 ? `${tenantId.slice(0, 8)}…` : tenantId;
}

async function loadTenantNameMap() {
  if (!isPlatformAdmin.value) return;
  try {
    const res = await apiGet<{ recent_tenants?: { id: string; name: string }[] }>('/tenants', {
      page: 1,
      page_size: 200,
    });
    const rows = res?.recent_tenants ?? (res as { items?: { id: string; name: string }[] })?.items ?? [];
    const map: Record<string, string> = { platform: '平台公共' };
    for (const row of rows) {
      if (row?.id) map[row.id] = row.name || row.id;
    }
    tenantNameMap.value = map;
  } catch {
    tenantNameMap.value = { platform: '平台公共' };
  }
}

/** 加载文件列表 */
async function loadFiles() {
  loading.value = true;
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize.value,
    };
    if (fileTypeFilter.value) {
      params.file_type = fileTypeFilter.value;
    }
    if (storageRegionFilter.value) {
      params.storage_region = storageRegionFilter.value;
    }
    if (isPlatformAdmin.value && tenantScopeFilter.value) {
      params.tenant_id = tenantScopeFilter.value;
    }
    if (searchKeyword.value.trim()) {
      params.search = searchKeyword.value.trim();
    }

    const res = await filesAPI.list(params);
    const data = res.data as any;

    if (data && data.items) {
      fileList.value = data.items as FileItem[];
      total.value = data.total ?? data.items.length;
    } else if (Array.isArray(data)) {
      fileList.value = data as FileItem[];
      total.value = data.length;
    } else {
      fileList.value = [];
      total.value = 0;
    }
  } catch (e: any) {
    if (import.meta.env.DEV) console.error('加载文件列表失败:', e);
    message.error(e?.message || '加载文件列表失败');
    fileList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

/** 加载统计 */
async function loadStats() {
  try {
    const params: Record<string, unknown> = {};
    if (isPlatformAdmin.value && tenantScopeFilter.value) {
      params.tenant_id = tenantScopeFilter.value;
    }
    const res = await filesAPI.stats(params);
    const data = res.data as any;
    if (data) {
      Object.assign(stats, {
        total_files: data.total_files ?? 0,
        total_size: data.total_size ?? 0,
        total_size_display: data.total_size_display ?? '0 B',
        image_count: data.image_count ?? 0,
        document_count: data.document_count ?? 0,
        video_count: data.video_count ?? 0,
        other_count: data.other_count ?? 0,
      });
      if (Array.isArray(data.tenant_scopes)) {
        tenantScopeOptions.value = data.tenant_scopes as TenantScopeOption[];
      }
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error('加载统计失败:', e);
  }
}

/** 刷新列表 */
function refreshList() {
  currentPage.value = 1;
  loadFiles();
  loadStats();
}

/** 搜索 */
function handleSearch() {
  currentPage.value = 1;
  loadFiles();
}

/** 分类筛选 */
function handleFilterChange(value: string | undefined) {
  fileTypeFilter.value = value;
  currentPage.value = 1;
  loadFiles();
}

function handleStorageRegionFilter(value: string | undefined) {
  storageRegionFilter.value = value;
  currentPage.value = 1;
  loadFiles();
}

function handleTenantScopeFilter(value: string | undefined) {
  tenantScopeFilter.value = value;
  currentPage.value = 1;
  loadFiles();
  loadStats();
}

async function loadStorageProfile() {
  try {
    const res = await filesAPI.storageProfile();
    storageProfile.value = (res.data as StorageProfile) || null;
  } catch {
    storageProfile.value = null;
  }
}

/** 分页大小变化 */
function onPageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  currentPage.value = 1;
  loadFiles();
}

/** 触发文件选择 */
function triggerUpload() {
  fileInputRef.value?.click();
}

/** 文件选择事件 */
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    uploadFiles(Array.from(input.files));
  }
  input.value = '';
}

/** 拖拽释放 */
function onDrop(e: DragEvent) {
  dragOver.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    uploadFiles(Array.from(files));
  }
}

/** 上传文件 */
async function uploadFiles(files: File[]) {
  const items: UploadItem[] = files.map((f) => ({
    id: `${Date.now()}-${uploadSeq++}`,
    name: f.name,
    status: 'pending' as const,
    progress: 0,
  }));
  uploadQueue.value = [...uploadQueue.value, ...items];

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const item = items[i];

    // 文件类型验证
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!allowedUploadExtensions.value.includes(ext)) {
      item.status = 'error';
      item.error = '不支持的格式';
      uploadQueue.value = [...uploadQueue.value];
      continue;
    }

    // 大小验证
    if (file.size > maxUploadBytes.value) {
      const limitMb = Math.round(maxUploadBytes.value / (1024 * 1024));
      item.status = 'error';
      item.error = `超过 ${limitMb}MB 限制`;
      uploadQueue.value = [...uploadQueue.value];
      continue;
    }

    item.status = 'uploading';
    item.progress = 10;
    uploadQueue.value = [...uploadQueue.value];

    try {
      const uploadOpts =
        isPlatformAdmin.value && tenantScopeFilter.value
          ? { tenant_id: tenantScopeFilter.value }
          : undefined;
      await filesAPI.upload(file, uploadOpts);
      item.status = 'done';
      item.progress = 100;
      uploadQueue.value = [...uploadQueue.value];
      message.success(`${file.name} 上传成功`);
    } catch (e: any) {
      item.status = 'error';
      item.error = e?.message || '上传失败';
      uploadQueue.value = [...uploadQueue.value];
      message.error(`${file.name} 上传失败: ${item.error}`);
    }
  }

  // 上传完成后刷新列表
  setTimeout(() => {
    loadFiles();
    loadStats();
  }, 500);
}

/** 删除确认 */
function confirmDelete(item: any) {
  const name = item.original_name || '未知文件';
  message.loading({ content: '删除中...', key: `del-${item.id}` });
  filesAPI.delete(item.id)
    .then(() => {
      message.success({ content: `${name} 已删除`, key: `del-${item.id}` });
      loadFiles();
      loadStats();
    })
    .catch((e: any) => {
      message.error({ content: `删除失败: ${e?.message || '未知错误'}`, key: `del-${item.id}` });
    });
}

/** 复制链接 */
function copyUrl(url: string) {
  const fullUrl = resolveAssetUrl(url);
  navigator.clipboard.writeText(fullUrl).then(
    () => message.success('链接已复制: ' + fullUrl),
    () => {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = fullUrl;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      message.success('链接已复制');
    },
  );
}

/** 右键菜单预览 */
function showContextMenu(_e: MouseEvent, item: FileItem) {
  previewItem.value = item;
  previewVisible.value = true;
}

/** 图片加载失败 */
function onImgError(e: Event) {
  const target = e.target as HTMLImageElement;
  target.style.display = 'none';
}

function onVideoThumbError(e: Event) {
  const target = e.target as HTMLVideoElement;
  target.style.display = 'none';
}

/** 时间格式化 */
function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${day} ${h}:${min}`;
  } catch {
    return iso;
  }
}

// ============ 初始化 ============
onMounted(() => {
  loadTenantNameMap();
  loadStorageProfile();
  loadFiles();
  loadStats();
});
</script>

<style scoped lang="scss">
/* 统计卡片 */
.stat-card {
  .ant-statistic-title {
    font-size: 13px;
    color: #64748b;
  }
}

/* 拖拽上传区域 */
.dropzone {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;

  &:hover {
    border-color: #1890ff;
    background: #f0f7ff;
  }

  &-active {
    border-color: #1890ff;
    background: #e6f7ff;
    box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.1);
  }

  &-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  &-icon {
    font-size: 48px;
    color: #1890ff;
  }

  &-text {
    font-size: 16px;
    color: #333;
    margin: 0;

    em {
      color: #1890ff;
      font-style: normal;
      text-decoration: underline;
    }
  }

  &-hint {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

/* 上传进度 */
.upload-queue {
  margin-top: 16px;
}

/* 文件卡片（网格视图） */
.file-card {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.25s ease;
  background: #fff;
  position: relative;

  &:hover {
    border-color: #1890ff;
    box-shadow: 0 4px 16px rgba(24, 144, 255, 0.12);
    transform: translateY(-2px);

    .file-actions {
      opacity: 1;
    }
  }
}

.file-thumb {
  width: 100%;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  overflow: hidden;

  &-doc {
    background: #fafafa;
  }
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #111;
}

.file-type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.file-info {
  padding: 8px 10px 4px;
}

.file-name {
  font-size: 13px;
  color: #1e293b;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 11px;
  color: #94a3b8;
  margin: 2px 0 0;
}

.file-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0;
  padding: 0 4px 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

/* 列表视图类型图标 */
.list-type-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 4px;
}

/* 预览 */
.preview-body {
  text-align: center;
  padding: 16px 0;
}

.preview-img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.preview-video {
  width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background: #111;
}

.preview-file-info {
  padding: 32px;
  color: #555;
  p {
    margin: 4px 0;
  }
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
}

.text-right {
  text-align: right;
}

.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.py-8 { padding-top: 32px; padding-bottom: 32px; }
</style>
