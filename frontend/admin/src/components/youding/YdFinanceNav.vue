/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>

  <nav class="yd-finance-nav" aria-label="财务子模块导航">

    <button

      v-for="item in items"

      :key="item.path"

      type="button"

      class="yd-finance-nav__btn"

      :class="{ active: isActive(item.path) }"

      @click="go(item.path)"

    >

      {{ item.label }}

    </button>

  </nav>

</template>



<script setup lang="ts">

import { useRoute, useRouter } from 'vue-router';



const items = [

  { path: '/admin/finance', label: '财务概览' },

  { path: '/admin/finance/payment-ops', label: '支付码与接口' },

  { path: '/admin/finance/payment-orders', label: '租户支付订单' },

  { path: '/admin/finance/ip-pool', label: '静态 IP 池' },

  { path: '/admin/finance/invoices', label: '开票审核' },

  { path: '/admin/finance/commissions', label: '分润结算' },

  { path: '/admin/finance/commission-rules', label: '分润规则' },

] as const;



const router = useRouter();

const route = useRoute();



function isActive(path: string) {

  if (path === '/admin/finance') {

    return route.path === path;

  }

  return route.path === path || route.path.startsWith(`${path}/`);

}



function go(path: string) {

  void router.push(path);

}

</script>



<style scoped>

.yd-finance-nav {

  display: flex;

  flex-wrap: wrap;

  gap: 8px;

  margin: 0 0 16px;

  padding: 10px 12px;

  border-radius: 14px;

  background: rgb(255 255 255 / 0.92);

  border: 1px solid rgb(203 213 225 / 0.9);

}



.yd-finance-nav__btn {

  appearance: none;

  border: 1px solid #cbd5e1;

  background: #fff;

  color: #334155;

  font-size: 13px;

  font-weight: 600;

  line-height: 1.2;

  padding: 6px 12px;

  border-radius: 999px;

  cursor: pointer;

  transition:

    background 0.15s,

    border-color 0.15s,

    color 0.15s,

    box-shadow 0.15s;

}



.yd-finance-nav__btn:hover {

  border-color: var(--uj-brand, #4a9b8c);

  color: #1e4d44;

  background: #f0faf7;

}



.yd-finance-nav__btn.active {

  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #3d8f7a);

  border-color: #3d8f7a;

  color: #fff;

  box-shadow: 0 4px 12px rgb(74 155 140 / 0.25);

}



.yd-finance-nav__btn:focus-visible {

  outline: 2px solid var(--uj-brand, #4a9b8c);

  outline-offset: 2px;

}

</style>


