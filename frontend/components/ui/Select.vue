<script setup lang="ts">
interface Props {
  modelValue?: string;
  disabled?: boolean;
}

defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <select
    :value="modelValue"
    :disabled="disabled"
    @change="handleChange"
    class="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
  >
    <slot />
  </select>
</template>
