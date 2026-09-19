/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    v-if="showBar"
    class="fixed bottom-0 left-0 right-0 z-50 bg-white shadow-[0_-2px_10px_rgba(0,0,0,0.1)] border-t border-gray-200 md:hidden pb-[env(safe-area-inset-bottom)]"
  >
    <div
      v-if="imChannels.length > 1"
      class="flex justify-center gap-1 px-2 pt-1"
    >
      <button
        v-for="(ch, idx) in imChannels"
        :key="`${ch.type}-${idx}`"
        type="button"
        class="text-[10px] px-2 py-0.5 rounded-full border"
        :class="idx === channelIndex ? 'bg-primary-100 border-primary-400 text-primary-800' : 'border-gray-200 text-gray-500'"
        @click="channelIndex = idx"
      >
        {{ channelLabel(ch) }}
      </button>
    </div>
    <div class="flex h-14">
      <a
        v-if="!isFormChannel"
        :href="imLink"
        @click="onImClick"
        class="flex-1 flex items-center justify-center font-bold text-sm text-white transition-all duration-200"
        :class="primaryBtnClass"
        target="_blank"
        rel="noopener"
      >
        <span class="mr-1.5 text-base">{{ imIcon }}</span>
        <span class="whitespace-nowrap">{{ imText }}</span>
      </a>
      <button
        v-else
        type="button"
        class="flex-1 flex items-center justify-center font-bold text-sm text-white transition-all duration-200"
        :class="primaryBtnClass"
        @click="openForm"
      >
        <span class="mr-1.5 text-base">{{ imIcon }}</span>
        <span class="whitespace-nowrap">{{ imText }}</span>
      </button>
      <button
        type="button"
        class="flex-1 flex items-center justify-center font-bold text-sm text-white bg-orange-500 hover:bg-orange-600 transition-all duration-200 active:scale-95"
        @click="openForm"
      >
        <span class="mr-1.5 text-base">🎁</span>
        <span class="whitespace-nowrap">{{ t('chat.form_submit') }}</span>
      </button>
    </div>

    <Transition name="slide-up">
      <div
        v-if="showForm"
        class="fixed inset-0 z-[60] bg-white overflow-y-auto"
      >
        <div
          class="h-1.5 w-10 bg-gray-300 rounded-full mx-auto mt-2 cursor-pointer"
          @click="closeForm"
        />
        <div class="p-6 space-y-5">
          <h3 class="text-xl font-bold text-gray-800">
            {{ t('chat.form_title') }}
          </h3>
          <form
            class="space-y-4"
            @submit.prevent="submitForm"
          >
            <input
              v-model="form.name"
              type="text"
              :placeholder="t('chat.form_name')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none"
              required
            >
            <input
              v-model="form.phone"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              placeholder="手机号（必填）"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none"
              required
            >
            <input
              v-model="form.email"
              type="email"
              :placeholder="t('chat.form_email')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none"
            >
            <textarea
              v-model="form.spec"
              :placeholder="t('chat.form_spec')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none h-32 resize-none"
              required
            />
            <p
              v-if="formError"
              class="text-sm text-red-600"
            >
              {{ formError }}
            </p>
            <button
              type="submit"
              class="w-full py-4 bg-green-500 hover:bg-green-600 text-white text-lg font-bold rounded-xl"
            >
              {{ t('chat.form_submit') }}
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { ImChannel } from '~/composables/useImRouting'

const { t } = useI18n()
const route = useRoute()
const { merchantId, fetchChannels } = useImRouting()

const showBar = ref(false)
const showForm = ref(false)
const imChannels = ref<Array<ImChannel & { type: string }>>([])
const channelIndex = ref(0)

const form = ref({ name: '', phone: '', email: '', spec: '' })
const formError = ref('')

const CN_PHONE = /^1[3-9]\d{9}$/

function normalizePhone(raw: string) {
  return (raw || '').replace(/\s|-/g, '')
}

function validateInquiryForm(): string | null {
  if (!form.value.name.trim()) return '请填写姓名'
  const phone = normalizePhone(form.value.phone)
  if (!CN_PHONE.test(phone)) return '请填写有效的 11 位中国大陆手机号'
  if (!form.value.spec.trim()) return '请填写需求说明'
  return null
}

function mapChannel(ch: ImChannel) {
  const type = ch.channel_type || 'form'
  return {
    type,
    account: ch.account_id || '',
    text: ch.prefilled_text || '',
    display: ch.display_text || '',
    link: ch.im_link || '',
  }
}

const activeChannel = computed(() => imChannels.value[channelIndex.value] || imChannels.value[0])

const isFormChannel = computed(() => {
  const tpe = activeChannel.value?.type || 'form'
  return ['form', 'wecom_inquiry', 'douyin_inquiry', 'live_chat'].includes(tpe) || !activeChannel.value?.account
})

const imLink = computed(() => {
  const ch = activeChannel.value
  if (!ch) return '#'
  if (ch.link && ch.link !== '#') return ch.link
  if (ch.type === 'whatsapp') {
    const text = encodeURIComponent(ch.text || t('chat.welcome'))
    return `https://wa.me/${ch.account}?text=${text}`
  }
  if (ch.type === 'telegram') return `https://t.me/${ch.account}`
  if (ch.type === 'line') return `https://line.me/ti/p/~${ch.account}`
  if (ch.type === 'zalo') return `https://zalo.me/${ch.account}`
  return '#'
})

function channelLabel(ch: ImChannel & { type: string }) {
  if (ch.display_text) return ch.display_text.slice(0, 8)
  const labels: Record<string, string> = {
    whatsapp: 'WA',
    telegram: 'TG',
    form: '表单',
    wecom_inquiry: '企微',
    douyin_inquiry: '抖音',
  }
  return labels[ch.type] || ch.type
}

const imIcon = computed(() => {
  const type = activeChannel.value?.type
  if (type === 'whatsapp') return '💬'
  if (type === 'telegram') return '✈️'
  if (type === 'wecom_inquiry') return '💼'
  if (type === 'douyin_inquiry') return '🎵'
  return '📋'
})

const imText = computed(() => {
  const ch = activeChannel.value
  if (ch?.display) return ch.display
  if (ch?.type === 'whatsapp') return t('product.chat_now')
  return t('product.get_quote')
})

const primaryBtnClass = computed(() => {
  const type = activeChannel.value?.type
  if (type === 'whatsapp') return 'bg-green-500 hover:bg-green-600'
  if (type === 'telegram') return 'bg-blue-500 hover:bg-blue-600'
  if (type === 'wecom_inquiry') return 'bg-emerald-600 hover:bg-emerald-700'
  if (type === 'douyin_inquiry') return 'bg-gray-900 hover:bg-black'
  return 'bg-gray-700 hover:bg-gray-800'
})

async function loadChannels() {
  const list = await fetchChannels()
  imChannels.value = list.map((c) => ({ ...c, type: c.channel_type }))
  showBar.value = imChannels.value.length > 0
}

function onImClick() {
  if (isFormChannel.value) {
    openForm()
    return
  }
  trackClick('im_click')
}

const { track, attributionPayload } = useSiteAnalytics()

const trackClick = async (eventType: string, label?: string) => {
  await track(eventType, {
    element_label: label || eventType,
    product_id: route.params.id || '',
    merchant_id: merchantId.value,
  })
}

function openForm() {
  formError.value = ''
  showForm.value = true
  if (import.meta.client) document.body.style.overflow = 'hidden'
  trackClick('form_open')
}

function closeForm() {
  showForm.value = false
  if (import.meta.client) document.body.style.overflow = ''
}

async function submitForm() {
  const err = validateInquiryForm()
  if (err) {
    formError.value = err
    return
  }
  formError.value = ''
  const config = useRuntimeConfig()
  const apiBase = (config.public.apiBase as string) || '/api/v1'
  const ch = activeChannel.value
  const phone = normalizePhone(form.value.phone)
  try {
    await $fetch(`${apiBase}/inquiries/public`, {
      method: 'POST',
      body: {
        name: form.value.name.trim(),
        email: form.value.email,
        message: form.value.spec.trim(),
        phone,
        product: String(route.params.id || ''),
        source_channel: ch?.type || 'form',
        merchant_id: merchantId.value,
        ...attributionPayload(),
      },
    })
    await trackClick('inquiry_submit', '询盘表单提交')
    alert(t('chat.form_submit') + ' - OK')
    closeForm()
    form.value = { name: '', phone: '', email: '', spec: '' }
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; message?: string }
    alert('Error: ' + (err.data?.detail || err.message))
  }
}

onMounted(loadChannels)
</script>
