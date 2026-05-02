<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          自定义特效组件
        </h1>
        <p class="text-gray-500 mt-1">
          配置页面交互动画和视觉特效
        </p>
      </div>
    </div>

    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="过渡动画">
          <div class="space-y-4">
            <div
              v-for="effect in transitionEffects"
              :key="effect.id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center gap-3">
                <div 
                  class="w-10 h-10 rounded-lg flex items-center justify-center"
                  :class="effect.active ? 'bg-primary-500' : 'bg-gray-200'"
                >
                  <component
                    :is="effect.icon"
                    class="w-5 h-5"
                    :class="effect.active ? 'text-white' : 'text-gray-400'"
                  />
                </div>
                <div>
                  <div class="font-medium text-gray-700">
                    {{ effect.name }}
                  </div>
                  <div class="text-xs text-gray-400">
                    {{ effect.description }}
                  </div>
                </div>
              </div>
              <a-switch
                v-model="effect.active"
                @change="previewEffect(effect)"
              />
            </div>
          </div>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="动画预览">
          <div class="relative h-48 bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-xl overflow-hidden">
            <!-- 背景装饰动画 -->
            <div class="absolute inset-0 overflow-hidden">
              <div class="absolute top-4 left-4 w-2 h-2 bg-primary-200 rounded-full animate-ping" />
              <div
                class="absolute bottom-8 right-8 w-3 h-3 bg-purple-200 rounded-full animate-ping"
                style="animation-delay: 0.5s"
              />
              <div
                class="absolute top-1/2 left-1/4 w-1.5 h-1.5 bg-blue-200 rounded-full animate-ping"
                style="animation-delay: 1s"
              />
            </div>
            
            <!-- 主预览区域 -->
            <transition
              :name="currentEffect"
              mode="out-in"
            >
              <div
                v-if="showPreview"
                :key="currentEffect"
                class="absolute inset-0 flex flex-col items-center justify-center"
              >
                <div class="w-24 h-24 bg-gradient-to-br from-primary-500 to-indigo-600 rounded-2xl shadow-xl flex items-center justify-center transform hover:scale-105 transition-transform cursor-pointer">
                  <PictureOutlined class="w-10 h-10 text-white" />
                </div>
                <div class="mt-4 text-center">
                  <p class="text-sm font-medium text-gray-700 animate-pulse">
                    {{ currentEffectName }}
                  </p>
                  <p class="text-xs text-gray-400 mt-1">
                    {{ currentEffectDesc }}
                  </p>
                </div>
              </div>
            </transition>
            
            <!-- 未选择状态 -->
            <div
              v-if="!showPreview"
              class="absolute inset-0 flex flex-col items-center justify-center"
            >
              <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-3 animate-bounce">
                <PictureOutlined class="w-8 h-8 text-gray-300" />
              </div>
              <p class="text-gray-400 text-sm">
                点击上方开关查看预览
              </p>
              <p class="text-gray-300 text-xs mt-1">
                🎨 选择动画效果体验动态美
              </p>
            </div>
            
            <!-- 动态提示气泡 -->
            <transition name="fade">
              <div 
                v-if="showTip" 
                class="absolute top-3 right-3 px-3 py-1.5 bg-primary-500 text-white text-xs rounded-lg shadow-lg flex items-center gap-1"
              >
                <span class="animate-ping">✨</span>
                {{ tipText }}
              </div>
            </transition>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card
      title="特效参数设置"
      class="mt-6"
    >
      <a-form
        :model="effectSettings"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="动画时长 (ms)">
              <a-input-number 
                v-model="effectSettings.duration" 
                :min="100" 
                :max="3000" 
                :step="100"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="缓动函数">
              <a-select v-model="effectSettings.easing">
                <a-select-option value="ease">
                  ease
                </a-select-option>
                <a-select-option value="linear">
                  linear
                </a-select-option>
                <a-select-option value="ease-in">
                  ease-in
                </a-select-option>
                <a-select-option value="ease-out">
                  ease-out
                </a-select-option>
                <a-select-option value="ease-in-out">
                  ease-in-out
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="延迟时间 (ms)">
              <a-input-number 
                v-model="effectSettings.delay" 
                :min="0" 
                :max="1000" 
                :step="50"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="全局动画开关">
              <a-switch v-model="effectSettings.globalEnabled" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="启用悬停效果">
              <a-switch v-model="effectSettings.hoverEffects" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-button
            type="primary"
            @click="saveEffectSettings"
          >
            保存设置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card
      title="粒子特效"
      class="mt-6"
    >
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="启用粒子效果">
            <a-switch v-model="particleSettings.enabled" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="粒子数量">
            <a-input-number
              v-model="particleSettings.count"
              :min="10"
              :max="200"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="粒子大小 (px)">
            <a-input-number
              v-model="particleSettings.size"
              :min="1"
              :max="20"
            />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="粒子颜色">
            <a-input
              type="color"
              v-model="particleSettings.color"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="运动速度">
            <a-input-number
              v-model="particleSettings.speed"
              :min="0.1"
              :max="5"
              :step="0.1"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="粒子形状">
            <a-select v-model="particleSettings.shape">
              <a-select-option value="circle">
                圆形
              </a-select-option>
              <a-select-option value="square">
                方形
              </a-select-option>
              <a-select-option value="triangle">
                三角形
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <div class="mt-4 p-4 bg-gray-50 rounded-xl">
        <div class="flex items-center gap-3">
          <PictureOutlined class="w-6 h-6 text-primary-500" />
          <div>
            <div class="font-medium text-gray-700">
              粒子效果预览
            </div>
            <div class="text-sm text-gray-400">
              开启后将在页面背景显示动态粒子效果
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  PictureOutlined,
  ZoomInOutlined,
  BarChartOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Button as AButton,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  InputNumber as AInputNumber,
  Switch as ASwitch,
  Modal,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue'

interface Effect {
  id: string
  name: string
  description: string
  icon: any
  active: boolean
}

const showPreview = ref(false)
const currentEffect = ref('')
const showTip = ref(false)
const tipText = ref('')

const transitionEffects = reactive<Effect[]>([
  { id: 'fade', name: '淡入淡出', description: '平滑的透明度变化', icon: PictureOutlined, active: true },
  { id: 'slide-up', name: '向上滑动', description: '从下方滑入', icon: PictureOutlined, active: false },
  { id: 'slide-down', name: '向下滑动', description: '从上方滑入', icon: PictureOutlined, active: false },
  { id: 'zoom', name: '缩放效果', description: '从小到大缩放', icon: ZoomInOutlined, active: false },
  { id: 'rotate', name: '旋转效果', description: '旋转进入', icon: BarChartOutlined, active: false },
])

const currentEffectName = ref('')
const currentEffectDesc = ref('')

const effectSettings = reactive({
  duration: 500,
  easing: 'ease',
  delay: 0,
  globalEnabled: true,
  hoverEffects: true,
})

const particleSettings = reactive({
  enabled: false,
  count: 50,
  size: 3,
  color: '#6366f1',
  speed: 1,
  shape: 'circle',
})

function previewEffect(effect: Effect) {
  currentEffect.value = effect.id
  currentEffectName.value = effect.name
  currentEffectDesc.value = effect.description
  showPreview.value = false
  
  // 显示动态提示
  showTip.value = true
  tipText.value = `已切换至「${effect.name}」效果`
  
  setTimeout(() => {
    showPreview.value = true
  }, 50)
  
  // 3秒后隐藏提示
  setTimeout(() => {
    showTip.value = false
  }, 3000)
}

function saveEffectSettings() {
  Modal.success({ title: '保存成功', content: '特效设置已更新' })
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.5s ease;
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(30px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.5s ease;
}
.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-30px);
}
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.zoom-enter-active,
.zoom-leave-active {
  transition: all 0.5s ease;
}
.zoom-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
.zoom-leave-to {
  opacity: 0;
  transform: scale(1.2);
}

.rotate-enter-active,
.rotate-leave-active {
  transition: all 0.5s ease;
}
.rotate-enter-from {
  opacity: 0;
  transform: rotate(-180deg) scale(0.8);
}
.rotate-leave-to {
  opacity: 0;
  transform: rotate(180deg) scale(0.8);
}
</style>
