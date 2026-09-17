/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <aside
    class="fixed bottom-6 right-6 z-50 flex items-center group select-none"
    aria-label="WhatsApp Instant Consultation"
  >
    <!-- Tooltip / Mini Badge -->
    <div
      class="hidden md:flex items-center mr-3 px-3 py-1.5 bg-gray-900/90 backdrop-blur-md text-white text-xs font-medium rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none translate-x-2 group-hover:translate-x-0"
    >
      <span>{{ labelText }}</span>
    </div>

    <!-- Floating Bubble Button -->
    <a
      :href="whatsappUrl"
      target="_blank"
      rel="noopener noreferrer"
      @click="handleClick"
      class="relative flex items-center justify-center w-14 h-14 bg-emerald-500 hover:bg-emerald-600 text-white rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-300"
      :title="labelText"
    >
      <!-- Subtle Pulse Ring -->
      <span class="absolute -inset-1 rounded-full bg-emerald-400 opacity-40 animate-ping" />

      <!-- WhatsApp SVG Icon -->
      <svg
        class="w-8 h-8 fill-current relative z-10"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M17.472 14.382c-.301-.15-1.78-.878-2.056-.979-.276-.1-.476-.15-.677.15-.2.301-.777.979-.953 1.18-.175.201-.351.226-.652.075-.3-.15-1.267-.467-2.414-1.49-1.282-1.144-1.583-1.636-1.808-2.022-.226-.386-.025-.595.125-.745.136-.135.301-.351.451-.527.15-.175.2-.301.301-.501.1-.2.05-.376-.025-.526-.075-.15-.677-1.63-928-2.232-.244-.587-.492-.507-.677-.516-.175-.01-.376-.01-.577-.01-.2 0-.526.075-.802.376-.276.301-1.053 1.029-1.053 2.509 0 1.48 1.078 2.909 1.229 3.11.15.2 2.12 3.238 5.136 4.542.717.311 1.278.497 1.714.636.721.23 1.377.197 1.895.12.577-.087 1.78-.727 2.03-1.43.251-.702.251-1.304.176-1.43-.075-.125-.276-.201-.577-.351zM12.04 2C6.516 2 2.028 6.488 2.028 12.012c0 1.954.564 3.784 1.543 5.342L2 22.062l4.856-1.53c1.5 1.054 3.327 1.668 5.184 1.668 5.524 0 10.012-4.488 10.012-10.012C22.052 6.488 17.564 2 12.04 2zm0 18.232c-1.636 0-3.237-.488-4.607-1.408l-.33-.223-2.87.904.912-2.793-.243-.362c-1.032-1.543-1.579-3.354-1.579-5.338 0-4.542 3.696-8.238 8.238-8.238 4.542 0 8.238 3.696 8.238 8.238 0 4.542-3.696 8.238-8.238 8.238z"
        />
      </svg>
    </a>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMarketingBeacon } from '~/composables/useMarketingBeacon';

interface Props {
  phone?: string;
  productName?: string;
  productSlug?: string;
  customText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  phone: '8613800000000',
  productName: 'Building Materials',
  productSlug: '',
  customText: '',
});

const { trackWhatsAppClick } = useMarketingBeacon();

const cleanPhone = computed(() => props.phone.replace(/\D/g, ''));

const labelText = computed(() => `Chat on WhatsApp for ${props.productName} quote`);

const whatsappUrl = computed(() => {
  const defaultMsg = `Hello, I'm interested in ${props.productName}. Please share your latest technical specs, container load capacity and FOB/CIF quote.`;
  const text = encodeURIComponent(props.customText || defaultMsg);
  return `https://wa.me/${cleanPhone.value}?text=${text}`;
});

function handleClick() {
  trackWhatsAppClick({
    productSlug: props.productSlug,
    productName: props.productName,
    sourceUrl: typeof window !== 'undefined' ? window.location.href : '',
  });
}
</script>

<style scoped>
@keyframes ping {
  75%, 100% {
    transform: scale(1.6);
    opacity: 0;
  }
}
</style>
