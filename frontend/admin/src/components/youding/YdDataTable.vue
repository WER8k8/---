<template>

  <a-table

    v-bind="mergedProps"

    :columns="columns"

    :data-source="dataSource"

    :loading="loading"

    :pagination="tablePagination"

    row-key="id"

    @change="onChange"

  >

    <template v-for="(_, name) in $slots" #[name]="slotData">

      <slot :name="name" v-bind="slotData" />

    </template>

  </a-table>

</template>



<script setup lang="ts">

import { computed } from 'vue';
import type { TablePaginationConfig, TableProps } from 'ant-design-vue';

import type { YdTablePagination } from '@/composables/useYdTable';
import { useUiPreferencesStore } from '@/stores/uiPreferences';



/** PAGE-01 · 统一表格壳 + 分页事件 */

const props = withDefaults(

  defineProps<{

    columns: TableProps['columns'];

    dataSource: TableProps['dataSource'];

    loading?: boolean;

    pagination?: false | YdTablePagination;

    tableProps?: Partial<TableProps>;

  }>(),

  { loading: false, tableProps: () => ({ size: 'middle' }) },

);



const emit = defineEmits<{
  'page-change': [pag: { current: number; pageSize: number }];
}>();

const ui = useUiPreferencesStore();

const mergedProps = computed(() => ({
  size: ui.antTableSize,
  ...(props.tableProps ?? {}),
}));



const tablePagination = computed<false | TablePaginationConfig>(() => {

  if (props.pagination === false) return false;

  if (!props.pagination) {

    return { pageSize: 20, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` };

  }

  return {

    current: props.pagination.current,

    pageSize: props.pagination.pageSize,

    total: props.pagination.total,

    showSizeChanger: true,

    showTotal: (t: number) => `共 ${t} 条`,

  };

});



function onChange(pag: TablePaginationConfig) {

  emit('page-change', {

    current: pag.current ?? 1,

    pageSize: pag.pageSize ?? 20,

  });

}

</script>

