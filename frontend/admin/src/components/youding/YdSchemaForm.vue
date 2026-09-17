/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-form layout="vertical" class="yd-schema-form">
    <a-form-item
      v-for="field in fields"
      :key="field.key"
      :label="field.label"
      :required="field.required"
    >
      <a-input
        v-if="field.type === 'string'"
        v-model:value="model[field.key]"
        :placeholder="field.placeholder"
      />
      <a-textarea
        v-else-if="field.type === 'textarea'"
        v-model:value="model[field.key]"
        :rows="field.rows ?? 3"
        :placeholder="field.placeholder"
      />
      <a-input-number
        v-else-if="field.type === 'number'"
        v-model:value="model[field.key]"
        class="yd-schema-form__number"
        :min="field.min"
        :max="field.max"
      />
      <a-select
        v-else-if="field.type === 'select'"
        v-model:value="model[field.key]"
        :options="field.options"
        :placeholder="field.placeholder"
      />
      <a-switch v-else-if="field.type === 'boolean'" v-model:checked="model[field.key]" />
    </a-form-item>
    <slot name="actions" />
  </a-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue';

import type { YdSchemaField } from './types';

const props = defineProps<{
  fields: YdSchemaField[];
  modelValue?: Record<string, unknown>;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>];
}>();

function buildDefaults(): Record<string, unknown> {
  const base: Record<string, unknown> = {};
  for (const f of props.fields) {
    if (f.default !== undefined) base[f.key] = f.default;
    else if (f.type === 'boolean') base[f.key] = false;
    else if (f.type === 'number') base[f.key] = 0;
    else base[f.key] = '';
  }
  return { ...base, ...props.modelValue };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic schema keys
const model = reactive(buildDefaults()) as Record<string, any>;

watch(
  () => props.modelValue,
  (v) => {
    if (v) Object.assign(model, v);
  },
  { deep: true },
);

watch(
  model,
  () => emit('update:modelValue', { ...model }),
  { deep: true },
);
</script>

<style scoped>
.yd-schema-form__number {
  width: 100%;
}
</style>
