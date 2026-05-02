<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
        <div class="text-center">
          <div class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-6">
            <span class="w-2 h-2 bg-secondary-400 rounded-full mr-2" />
            <span class="text-sm font-medium text-white">联系我们</span>
          </div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
            联系我们
          </h1>
          <p class="text-xl text-white/80">
            专业工程师为您提供产品选型和技术支持
          </p>
        </div>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div>
            <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
              <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
              <span class="text-sm font-medium text-secondary-600">联系方式</span>
            </div>
            <h2 class="text-3xl md:text-4xl font-bold text-primary-900 mb-8">
              与我们取得联系
            </h2>
            <div class="space-y-6">
              <div
                v-for="item in contactInfo"
                :key="item.label"
                class="group flex items-start space-x-4 p-5 bg-white rounded-xl border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300"
              >
                <div class="w-12 h-12 bg-gradient-to-br from-secondary-50 to-accent-50 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                  <span class="text-xl">{{ item.icon }}</span>
                </div>
                <div>
                  <h3 class="font-semibold text-primary-900">
                    {{ item.label }}
                  </h3>
                  <p class="text-text-secondary mt-1">
                    {{ item.value }}
                  </p>
                  <p
                    v-if="item.sub"
                    class="text-text-muted text-sm mt-0.5"
                  >
                    {{ item.sub }}
                  </p>
                </div>
              </div>
            </div>

            <div class="mt-12 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-2xl p-8 text-white shadow-lg shadow-secondary-200">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <svg
                    class="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 class="text-xl font-bold">
                    在线咨询
                  </h3>
                  <p class="text-white/70 text-sm">
                    专业客服随时为您解答
                  </p>
                </div>
              </div>
              <p class="text-white/80 mb-6">
                工作时间：周一至周五 9:00-17:00（节假日除外）
              </p>
              <a
                href="tel:400-888-8888"
                class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-md justify-center w-full"
              >
                <svg
                  class="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
                拨打咨询热线 400-888-8888
              </a>
            </div>
          </div>

          <div>
            <div class="inline-flex items-center px-3 py-1.5 bg-accent-50 rounded-full mb-4">
              <span class="w-1.5 h-1.5 bg-accent-500 rounded-full mr-2" />
              <span class="text-sm font-medium text-accent-600">在线留言</span>
            </div>
            <h2 class="text-3xl md:text-4xl font-bold text-primary-900 mb-8">
              发送您的需求
            </h2>
            <form
              class="bg-white rounded-2xl p-8 border border-border shadow-card"
              @submit.prevent="handleSubmit"
            >
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-semibold text-primary-900 mb-2">姓名 <span class="text-danger">*</span></label>
                  <input
                    v-model="form.name"
                    required
                    class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
                  >
                </div>
                <div>
                  <label class="block text-sm font-semibold text-primary-900 mb-2">电话 <span class="text-danger">*</span></label>
                  <input
                    v-model="form.phone"
                    required
                    type="tel"
                    class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
                  >
                </div>
              </div>
              <div>
                <label class="block text-sm font-semibold text-primary-900 mb-2">邮箱</label>
                <input
                  v-model="form.email"
                  type="email"
                  class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
                >
              </div>
              <div>
                <label class="block text-sm font-semibold text-primary-900 mb-2">产品需求</label>
                <select
                  v-model="form.product"
                  class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
                >
                  <option value="">
                    请选择
                  </option>
                  <option value="light-aggregate">
                    轻集料混凝土
                  </option>
                  <option value="ceramsite">
                    陶粒混凝土
                  </option>
                  <option value="aerated">
                    加气混凝土
                  </option>
                  <option value="mortar">
                    保温砂浆
                  </option>
                  <option value="other">
                    其他
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-semibold text-primary-900 mb-2">留言内容 <span class="text-danger">*</span></label>
                <textarea
                  v-model="form.message"
                  required
                  rows="5"
                  class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all resize-none"
                  placeholder="请描述您的需求和信息..."
                />
              </div>
              <button
                type="submit"
                :disabled="submitting"
                class="w-full px-8 py-4 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 font-semibold transition-all shadow-lg shadow-secondary-200"
              >
                {{ submitting ? '提交中...' : '提交留言' }}
              </button>
              <p
                v-if="submitSuccess"
                class="text-accent-600 text-center font-medium mt-4 flex items-center justify-center"
              >
                <svg
                  class="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                提交成功！我们将尽快与您联系。
              </p>
              <p
                v-if="submitError"
                class="text-danger text-center font-medium mt-4"
              >
                {{ submitError }}
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-primary-800 to-primary-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-8 text-center">
          <div class="flex items-center justify-center mb-4">
            <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mr-4">
              <svg
                class="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <div>
              <h3 class="text-xl font-bold text-white">
                公司地址
              </h3>
              <p class="text-white/70">
                中国建材产业园区 · 优丁建材有限公司
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useApi } from '~/composables/useApi'

useHead({
  title: '联系我们 - 优丁建材',
  meta: [
    { name: 'description', content: '联系优丁建材，获取轻集料混凝土产品选型建议和技术支持服务' },
    { name: 'keywords', content: '联系我们,优丁建材,轻集料混凝土咨询,建材采购,技术支持' },
  ],
})

const { request } = useApi()

const contactInfo = [
  { icon: '📞', label: '咨询热线', value: '400-888-8888', sub: '24小时服务' },
  { icon: '📧', label: '电子邮箱', value: 'info@youding.com', sub: '工作日24小时内回复' },
  { icon: '📍', label: '公司地址', value: '中国建材产业园区', sub: '欢迎实地考察' },
]

const form = reactive({
  name: '',
  phone: '',
  email: '',
  product: '',
  message: '',
})

const submitting = ref(false)
const submitSuccess = ref(false)
const submitError = ref('')

async function handleSubmit() {
  submitting.value = true
  submitSuccess.value = false
  submitError.value = ''
  try {
    await request('/inquiries', { method: 'POST', body: { ...form } })
    submitSuccess.value = true
    form.name = ''
    form.phone = ''
    form.email = ''
    form.product = ''
    form.message = ''
  } catch (e: any) {
    submitError.value = e.message || '提交失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>
