<template>
  <FormProvider :form="form">
    <a-form layout="vertical" class="yd-formily-form">
      <SchemaField :schema="schema" />
      <slot name="actions" />
    </a-form>
  </FormProvider>
</template>

<script setup lang="ts">
import { createForm, onFormValuesChange } from '@formily/core';
import type { ISchema } from '@formily/json-schema';
import { FormProvider, createSchemaField } from '@formily/vue';
import { watch, nextTick } from 'vue';

import {
  FormItem,
  FormilySelect,
  FormilySwitch,
  Input,
  TextArea,
} from './formily/antdv-bridge';

const { SchemaField } = createSchemaField({
  components: {
    FormItem,
    Input,
    TextArea,
    Select: FormilySelect,
    Switch: FormilySwitch,
  },
});

const props = defineProps<{
  schema: ISchema;
  modelValue?: Record<string, unknown>;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>];
}>();

const form = createForm({
  initialValues: { ...(props.modelValue ?? {}) },
  effects() {
    onFormValuesChange(() => {
      emit('update:modelValue', { ...form.values });
    });
  },
});

watch(
  () => props.modelValue,
  (v) => {
    if (!v) return;
    nextTick(() => form.setValues(v));
  },
  { deep: true },
);

defineExpose({ form });
</script>
