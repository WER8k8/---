<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        {{ isNew ? '新建案例' : '编辑案例' }}
      </h1>
      <div class="flex gap-3">
        <button
          class="px-4 py-2.5 border border-border text-text-secondary rounded-xl hover:bg-surface-hover text-sm font-medium transition-colors"
          @click="saveDraft"
        >
          保存草稿
        </button>
        <button
          class="px-4 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
          @click="publish"
        >
          发布
        </button>
      </div>
    </div>

    <div class="space-y-6">
      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          基本信息
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">项目名称 *</label>
            <input
              v-model="form.project_name"
              type="text"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              @input="autoSlug"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">URL 标识 (slug) *</label>
            <input
              v-model="form.slug"
              type="text"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">客户名称</label>
            <input
              v-model="form.client_name"
              type="text"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">施工面积</label>
            <input
              v-model="form.construction_area"
              type="text"
              placeholder="如: 5000m²"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">使用材料</label>
            <input
              v-model="form.materials_used"
              type="text"
              placeholder="如: EPS聚苯板、岩棉板"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">项目地点</label>
            <input
              v-model="form.location"
              type="text"
              placeholder="如: 河北省石家庄市"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">项目日期</label>
            <input
              v-model="form.project_date"
              type="text"
              placeholder="如: 2025-03"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">排序权重</label>
            <input
              v-model.number="form.sort_order"
              type="number"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
          </div>
        </div>
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          封面图片
        </h2>
        <div
          v-if="form.cover_image"
          class="mb-3"
        >
          <img
            :src="form.cover_image"
            class="w-48 h-32 object-cover rounded-xl border border-border"
          >
          <button
            class="text-danger text-sm mt-1 font-medium"
            @click="form.cover_image = ''"
          >
            移除
          </button>
        </div>
        <FileUploader
          accept="image/*"
          :api-endpoint="'/api/v1/system/upload'"
          @uploaded="onCoverUploaded"
        />
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          项目详情
        </h2>
        <RichTextEditor v-model="form.description" />
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          施工现场图集
        </h2>
        <div
          v-if="images.length"
          class="grid grid-cols-4 gap-3 mb-4"
        >
          <div
            v-for="(img, idx) in images"
            :key="idx"
            class="relative group"
          >
            <img
              :src="img.image_url"
              class="w-full h-32 object-cover rounded-xl border border-border"
            >
            <button
              class="absolute top-1 right-1 bg-danger text-white w-6 h-6 rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
              @click="removeImage(idx)"
            >
              x
            </button>
            <input
              v-model="img.image_alt"
              type="text"
              placeholder="图片描述"
              class="w-full mt-1 px-2 py-1 text-xs border border-border rounded-lg text-primary-900"
            >
          </div>
        </div>
        <FileUploader
          accept="image/*"
          :api-endpoint="'/api/v1/system/upload'"
          @uploaded="onImageUploaded"
        />
      </div>

      <SeoPanel v-model="seo" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from '#app'
import RichTextEditor from '~/components/admin/RichTextEditor.vue'
import FileUploader from '~/components/admin/FileUploader.vue'
import SeoPanel from '~/components/admin/SeoPanel.vue'

definePageMeta({
  layout: "admin",
  title: "案例编辑",
});

const route = useRoute();
const router = useRouter();
const isNew = computed(() => route.params.id === "new");

const form = ref({
  project_name: "",
  slug: "",
  client_name: "",
  materials_used: "",
  construction_area: "",
  project_date: "",
  location: "",
  description: "",
  cover_image: "",
  status: "draft",
  sort_order: 0,
});
const images = ref<{ image_url: string; image_alt: string; sort_order: number }[]>([]);
const seo = ref({
  meta_title: "",
  meta_description: "",
  meta_keywords: "",
});

function autoSlug() {
  if (isNew.value && !form.value.slug) {
    form.value.slug = form.value.project_name.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, "-").replace(/-+/g, "-").toLowerCase();
  }
}

function onCoverUploaded(data: { url: string }) {
  form.value.cover_image = data.url;
}

function onImageUploaded(data: { url: string }) {
  images.value.push({ image_url: data.url, image_alt: "", sort_order: images.value.length });
}

function removeImage(idx: number) {
  images.value.splice(idx, 1);
}

async function saveDraft() {
  form.value.status = "draft";
  await save();
}

async function publish() {
  if (!form.value.project_name) { alert("请输入项目名称"); return; }
  if (!form.value.slug) { alert("请输入 URL 标识"); return; }
  form.value.status = "published";
  await save();
}

async function save() {
  try {
    if (isNew.value) {
      await $fetch("/api/v1/cases", {
        method: "POST",
        body: JSON.stringify(form.value),
      });
    } else {
      await $fetch(`/api/v1/cases/${route.params.id}`, {
        method: "PUT",
        body: JSON.stringify(form.value),
      });
    }
    await saveImages();
    await saveSeo();
    router.push("/admin/cases");
  } catch (e: any) {
    alert(e?.data?.detail || "保存失败");
  }
}

async function saveImages() {
  const caseId = isNew.value ? "" : route.params.id as string;
  if (!caseId) return;
  for (const img of images.value) {
    if (!img.image_url.startsWith("/api/")) {
      await $fetch(`/api/v1/cases/${caseId}/images`, {
        method: "POST",
        body: JSON.stringify(img),
      });
    }
  }
}

async function saveSeo() {
  const caseId = isNew.value ? "" : route.params.id as string;
  if (!caseId) return;
  try {
    await $fetch(`/api/v1/content/seo/case_study/${caseId}`, {
      method: "PUT",
      body: JSON.stringify(seo.value),
    });
  } catch {
  }
}

if (!isNew.value) {
  const { data } = await useFetch(`/api/v1/cases/${route.params.id}`);
  if (data.value) {
    const d = data.value as any;
    form.value = {
      project_name: d.project_name || "",
      slug: d.slug || "",
      client_name: d.client_name || "",
      materials_used: d.materials_used || "",
      construction_area: d.construction_area || "",
      project_date: d.project_date || "",
      location: d.location || "",
      description: d.description || "",
      cover_image: d.cover_image || "",
      status: d.status || "draft",
      sort_order: d.sort_order || 0,
    };
    images.value = (d.images || []).map((img: any) => ({
      image_url: img.image_url,
      image_alt: img.image_alt || "",
      sort_order: img.sort_order || 0,
    }));
  }
  const { data: seoData } = await useFetch(`/api/v1/content/seo/case_study/${route.params.id}`);
  if (seoData.value) {
    const s = seoData.value as any;
    seo.value = {
      meta_title: s.meta_title || "",
      meta_description: s.meta_description || "",
      meta_keywords: s.meta_keywords || "",
    };
  }
}
</script>
