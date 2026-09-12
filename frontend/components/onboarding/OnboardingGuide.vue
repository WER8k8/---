<script setup lang="ts">
interface Props {
  visible: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
});

const emit = defineEmits<{
  close: [];
}>();

const steps = [
  {
    title: '创建产品',
    description: '在后台添加您的轻集料混凝土产品信息，包括名称、规格、参数和图片，一键发布到企业官网。',
    icon: '📦',
  },
  {
    title: '优化SEO',
    description: '使用AI驱动的SEO工具自动优化产品标题、关键词和描述，提升搜索引擎排名，获取更多曝光。',
    icon: '🔍',
  },
  {
    title: '查看询盘',
    description: '实时接收客户询盘通知，管理潜在客户信息，快速响应商机，不错过每一笔订单。',
    icon: '📨',
  },
];

const currentStep = ref(0);
const totalSteps = steps.length;

function next() {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value++;
  }
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

function finish() {
  currentStep.value = 0;
  emit('close');
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="finish"
      >
        <div class="mx-4 w-full max-w-lg rounded-2xl bg-white shadow-2xl">
          <!-- Header -->
          <div class="relative px-6 pb-4 pt-8 text-center">
            <h2 class="text-2xl font-bold text-gray-900">
              欢迎使用优丁建材系统
            </h2>
            <p class="mt-2 text-sm text-gray-500">
              跟随三步快速上手，开启您的数字化营销之旅
            </p>
            <!-- Progress bar -->
            <div class="mx-auto mt-6 flex w-48 gap-1">
              <div
                v-for="(_, index) in steps"
                :key="index"
                class="h-1.5 flex-1 rounded-full transition-colors duration-300"
                :class="index <= currentStep ? 'bg-blue-600' : 'bg-gray-200'"
              />
            </div>
            <span class="mt-2 block text-xs text-gray-400">
              {{ currentStep + 1 }} / {{ totalSteps }}
            </span>
          </div>

          <!-- Step content -->
          <div class="px-6 pb-6">
            <div class="flex flex-col items-center text-center">
              <!-- Screenshot placeholder -->
              <div class="mb-4 flex h-40 w-full items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50">
                <span class="text-6xl">{{ steps[currentStep].icon }}</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ steps[currentStep].title }}
              </h3>
              <p class="mt-2 text-sm leading-relaxed text-gray-500">
                {{ steps[currentStep].description }}
              </p>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between border-t px-6 py-4">
            <button
              class="text-sm text-gray-400 transition-colors hover:text-gray-600 disabled:opacity-0"
              :disabled="currentStep === 0"
              @click="prev"
            >
              上一步
            </button>

            <div class="flex gap-3">
              <button
                class="rounded-lg px-4 py-2 text-sm text-gray-400 transition-colors hover:text-gray-600"
                @click="finish"
              >
                跳过
              </button>

              <button
                v-if="currentStep < totalSteps - 1"
                class="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                @click="next"
              >
                下一步
              </button>

              <button
                v-else
                class="rounded-lg bg-green-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700"
                @click="finish"
              >
                完成
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
