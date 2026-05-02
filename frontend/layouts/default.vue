<template>
  <div class="min-h-screen flex flex-col">
    <Header />

    <main class="flex-1">
      <slot />
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import Header from '~/components/common/Header.vue'
import Footer from '~/components/common/Footer.vue'
</script>