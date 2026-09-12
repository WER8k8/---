<template>
  <YdPage surface="default" class="today-three-page-wrap">
    <ClientTodayThreeBoard />
  </YdPage>
</template>

<script setup lang="ts">
import { YdPage } from '@/components/youding';
import ClientTodayThreeBoard from '@/components/client/ClientTodayThreeBoard.vue';
import { useClientTodayThree } from '@/composables/useClientTodayThree';

useClientTodayThree();
</script>

<style scoped lang="scss">
.today-three-page-wrap {
  width: 100%;
}

.today-three-page-wrap :deep(.yd-page-body) {
  padding: 0;
}
</style>
