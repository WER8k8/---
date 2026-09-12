<template>

  <a-modal

    v-model:open="open"

    title="选择建站模板"

    width="880px"

    :footer="null"

    destroy-on-close

  >

    <p class="site-template-picker__intro">

      8 套建材外贸模板 · 含行业预设文案 · 支持多页路由（Products / About / Contact）

    </p>

    <div class="site-template-picker__grid">

      <button

        v-for="tpl in SITE_BUILDER_TEMPLATES"

        :key="tpl.id"

        type="button"

        class="site-template-picker__card"

        :class="{ 'site-template-picker__card--active': tpl.id === selectedId }"

        @click="pick(tpl.id)"

      >

        <div

          class="site-template-picker__preview"

          :class="`site-template-picker__preview--${meta(tpl.id).layout}`"

          :style="previewStyle(tpl.id)"

        >

          <div class="site-template-picker__preview-topbar" />

          <div class="site-template-picker__preview-header" :style="{ background: colors(tpl.id).headerBg }" />

          <div

            class="site-template-picker__preview-hero"

            :class="{ 'site-template-picker__preview-hero--banner': meta(tpl.id).layout === 'hero-banner' }"

            :style="heroStyle(tpl.id)"

          >

            <span class="site-template-picker__preview-cta" :style="{ background: colors(tpl.id).accent }" />

          </div>

          <div v-if="meta(tpl.id).layout === 'industrial'" class="site-template-picker__preview-stats">

            <span v-for="n in 4" :key="n" />

          </div>

          <div class="site-template-picker__preview-cards">

            <span /><span /><span />

          </div>

        </div>

        <div class="site-template-picker__meta">

          <strong>{{ tpl.name }}</strong>

          <span>{{ tpl.description }}</span>

        </div>

        <a-tag class="site-template-picker__layout-tag" color="default">{{ meta(tpl.id).layoutLabel }}</a-tag>

        <a-tag v-if="tpl.id === selectedId" color="blue" class="site-template-picker__tag">当前</a-tag>

      </button>

    </div>

  </a-modal>

</template>



<script setup lang="ts">

import {

  SITE_BUILDER_TEMPLATES,

  TEMPLATE_PREVIEW_COLORS,

  type SiteBuilderTemplateId,

} from '@/templates/site-builder';



const open = defineModel<boolean>('open', { default: false });

const selectedId = defineModel<SiteBuilderTemplateId>('templateId', { required: true });



const emit = defineEmits<{

  select: [id: SiteBuilderTemplateId];

}>();



function meta(id: SiteBuilderTemplateId) {

  return TEMPLATE_PREVIEW_COLORS[id];

}



function colors(id: SiteBuilderTemplateId) {

  return TEMPLATE_PREVIEW_COLORS[id];

}



function previewStyle(id: SiteBuilderTemplateId) {

  return { borderColor: colors(id).accent };

}



function heroStyle(id: SiteBuilderTemplateId) {

  const c = colors(id);

  if (c.layout === 'hero-banner') {

    return {

      background: `linear-gradient(135deg, ${c.headerBg}, ${c.accent})`,

    };

  }

  return { background: c.heroBg };

}



function pick(id: SiteBuilderTemplateId) {

  emit('select', id);

  open.value = false;

}

</script>



<style scoped lang="scss">

.site-template-picker__intro {

  margin: 0 0 16px;

  font-size: 13px;

  color: #64748b;

}



.site-template-picker__grid {

  display: grid;

  grid-template-columns: repeat(4, minmax(0, 1fr));

  gap: 12px;

}



.site-template-picker__card {

  position: relative;

  text-align: left;

  padding: 10px;

  border: 2px solid #e2e8f0;

  border-radius: 12px;

  background: #fff;

  cursor: pointer;

  transition: border-color 0.15s, box-shadow 0.15s;



  &:hover {

    border-color: #94a3b8;

    box-shadow: 0 4px 16px rgb(15 23 42 / 0.08);

  }



  &--active {

    border-color: var(--uj-brand, #4a9b8c);

    box-shadow: 0 0 0 1px var(--uj-brand, #4a9b8c);

  }

}



.site-template-picker__preview {

  border-radius: 8px;

  overflow: hidden;

  border: 1px solid #e2e8f0;

  margin-bottom: 8px;



  &--industrial .site-template-picker__preview-header {

    height: 16px;

  }

}



.site-template-picker__preview-topbar {

  height: 6px;

  background: #0f172a;

}



.site-template-picker__preview-header {

  height: 14px;

}



.site-template-picker__preview-hero {

  height: 48px;

  padding: 8px;

  display: flex;

  align-items: flex-end;



  &--banner {

    height: 56px;

    align-items: center;

    justify-content: center;

  }

}



.site-template-picker__preview-cta {

  display: block;

  width: 36px;

  height: 8px;

  border-radius: 4px;

}



.site-template-picker__preview-stats {

  display: grid;

  grid-template-columns: repeat(4, 1fr);

  gap: 3px;

  padding: 4px 8px;

  background: #f8fafc;



  span {

    height: 10px;

    background: #fff;

    border: 1px solid #e2e8f0;

    border-radius: 3px;

  }

}



.site-template-picker__preview-cards {

  display: flex;

  gap: 4px;

  padding: 6px 8px 8px;

  background: #fff;



  span {

    flex: 1;

    height: 22px;

    background: #f1f5f9;

    border-radius: 4px;

  }

}



.site-template-picker__meta {

  display: flex;

  flex-direction: column;

  gap: 2px;



  strong {

    font-size: 13px;

    color: #1e293b;

  }



  span {

    font-size: 11px;

    color: #64748b;

    line-height: 1.35;

  }

}



.site-template-picker__layout-tag {

  position: absolute;

  top: 8px;

  left: 8px;

  margin: 0;

  font-size: 10px;

}



.site-template-picker__tag {

  position: absolute;

  top: 8px;

  right: 8px;

  margin: 0;

  font-size: 10px;

}



@media (max-width: 768px) {

  .site-template-picker__grid {

    grid-template-columns: repeat(2, minmax(0, 1fr));

  }

}

</style>


