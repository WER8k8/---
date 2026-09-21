/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <form
    class="tenant-inquiry-form"
    @submit.prevent="onSubmit"
  >
    <div class="tenant-inquiry-form-grid">
      <label class="tenant-inquiry-field">
        <span>{{ tSite('form_name') }}</span>
        <input
          v-model="form.name"
          type="text"
          required
          maxlength="120"
          autocomplete="name"
        >
      </label>
      <label class="tenant-inquiry-field">
        <span>{{ tSite('form_email') }}</span>
        <input
          v-model="form.email"
          type="email"
          :required="!form.phone"
          maxlength="120"
          autocomplete="email"
        >
      </label>
      <label class="tenant-inquiry-field">
        <span>{{ phoneLabel }}</span>
        <input
          v-model="form.phone"
          type="tel"
          :required="!form.email"
          maxlength="30"
          autocomplete="tel"
        >
      </label>
      <label class="tenant-inquiry-field tenant-inquiry-field--full">
        <span>{{ tSite('form_product') }}</span>
        <input
          v-model="form.product"
          type="text"
          maxlength="200"
          :placeholder="productPlaceholder"
        >
      </label>
      <label class="tenant-inquiry-field tenant-inquiry-field--full">
        <span>{{ tSite('form_message') }}</span>
        <textarea
          v-model="form.message"
          required
          rows="4"
          maxlength="2000"
        />
      </label>
    </div>
    <p
      v-if="errorText"
      class="tenant-inquiry-error"
      role="alert"
    >
      {{ errorText }}
    </p>
    <p
      v-if="successText"
      class="tenant-inquiry-success"
      role="status"
    >
      {{ successText }}
    </p>
    <button
      type="submit"
      class="tenant-btn tenant-btn-primary tenant-inquiry-submit"
      :disabled="submitting"
    >
      {{ submitting ? tSite('form_submitting') : tSite('form_submit') }}
    </button>
    <p class="tenant-inquiry-hint">
      {{ tSite('form_hint') }}
    </p>
  </form>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue';

import { submitPublicInquiry } from '../../utils/submitPublicInquiry';

const props = withDefaults(
  defineProps<{
    tenantId?: string;
    tenantDomain?: string;
    apiBase?: string;
    productPlaceholder?: string;
    cnCompliantOnly?: boolean;
    tSite: (key: string, vars?: Record<string, string>) => string;
    attribution?: () => {
      session_id?: string;
      landing_path?: string;
      last_click_label?: string;
      tenant_id?: string;
    };
    onFormOpen?: () => void;
    onSubmitSuccess?: () => void;
  }>(),
  {
    tenantId: '',
    tenantDomain: '',
    apiBase: '/api/v1',
    productPlaceholder: '',
    cnCompliantOnly: false,
  },
);

const form = reactive({
  name: '',
  email: '',
  phone: '',
  product: '',
  message: '',
});

const submitting = ref(false);
const errorText = ref('');
const successText = ref('');

const phoneLabel = computed(() =>
  props.cnCompliantOnly ? props.tSite('form_phone_cn') : props.tSite('form_phone'),
);

if (import.meta.client) {
  props.onFormOpen?.();
}

async function onSubmit() {
  errorText.value = '';
  successText.value = '';
  if (!form.phone.trim() && !form.email.trim()) {
    errorText.value = props.tSite('form_required_contact');
    return;
  }
  submitting.value = true;
  const attr = props.attribution?.() || {};
  try {
    await submitPublicInquiry(props.apiBase, {
      name: form.name.trim(),
      email: form.email.trim() || undefined,
      phone: form.phone.trim() || undefined,
      product: form.product.trim() || undefined,
      message: form.message.trim(),
      source_channel: 'tenant_site_form',
      tenant_id: props.tenantId || attr.tenant_id || undefined,
      session_id: attr.session_id,
      landing_path: attr.landing_path,
      last_click_label: attr.last_click_label || 'tenant_inquiry_form',
    });
    successText.value = props.tSite('form_success');
    form.name = '';
    form.email = '';
    form.phone = '';
    form.product = '';
    form.message = '';
    props.onSubmitSuccess?.();
  } catch (e: unknown) {
    errorText.value = e instanceof Error ? e.message : props.tSite('form_error');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.tenant-inquiry-form {
  max-width: 40rem;
  margin: 0 auto;
}
.tenant-inquiry-form-grid {
  display: grid;
  gap: 1rem;
}
@media (min-width: 640px) {
  .tenant-inquiry-form-grid {
    grid-template-columns: 1fr 1fr;
  }
}
.tenant-inquiry-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.875rem;
}
.tenant-inquiry-field--full {
  grid-column: 1 / -1;
}
.tenant-inquiry-field span {
  font-weight: 600;
  color: #475569;
}
.tenant-inquiry-field input,
.tenant-inquiry-field textarea {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.65rem 0.75rem;
  font-size: 0.9375rem;
  color: #0f172a;
  background: #fff;
}
.tenant-inquiry-field input:focus,
.tenant-inquiry-field textarea:focus {
  outline: 2px solid color-mix(in srgb, var(--tenant-primary, #1e293b) 35%, transparent);
  border-color: var(--tenant-primary, #1e293b);
}
.tenant-inquiry-submit {
  width: 100%;
  margin-top: 1rem;
  min-height: 2.75rem;
  border: none;
  cursor: pointer;
}
.tenant-inquiry-submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.tenant-inquiry-error {
  margin-top: 0.75rem;
  color: #b91c1c;
  font-size: 0.875rem;
}
.tenant-inquiry-success {
  margin-top: 0.75rem;
  color: #047857;
  font-size: 0.875rem;
}
.tenant-inquiry-hint {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #94a3b8;
  text-align: center;
}
</style>
