<template>
  <teleport to="body">
    <transition name="guide-fade">
      <div v-if="visible" class="guide-overlay" @click.self="handleLater">
        <transition name="guide-scale">
          <div v-if="visible" class="guide-modal">
            <button class="guide-close" @click="handleLater">
              <CloseOutlined />
            </button>

            <div class="guide-header">
              <div class="guide-icon-wrap">
                <BulbOutlined class="guide-icon" />
              </div>
              <h2 class="guide-title">欢迎使用 AI 大模型平台</h2>
              <p class="guide-subtitle">
                为充分发挥 AI 能力，建议您优先配置以下平台的 API Key，
                即可在 AI 内容助手、智能分析等功能中使用大模型服务。
              </p>
            </div>

            <div class="guide-recommend">
              <h3 class="recommend-title">
                <StarOutlined class="recommend-star" />
                推荐优先配置
              </h3>
              <div class="recommend-list">
                <div
                  v-for="item in recommendPlatforms"
                  :key="item.id"
                  class="recommend-item"
                  :class="{ configured: item.configured }"
                >
                  <span class="ri-emoji">{{ item.emoji }}</span>
                  <span class="ri-name">{{ item.name }}</span>
                  <a-tag v-if="item.configured" color="success" size="small">已配置</a-tag>
                  <a-tag v-else color="processing" size="small">推荐</a-tag>
                </div>
              </div>
            </div>

            <div class="guide-actions">
              <a-button type="primary" size="large" class="guide-btn-primary" @click="handleSetup">
                <SettingOutlined /> 立即配置
              </a-button>
              <a-button size="large" class="guide-btn-secondary" @click="handleLater">
                稍后配置
              </a-button>
            </div>

            <p class="guide-footnote">
              配置完成后即可使用 AI 内容生成、SEO 优化、智能分析等全部 AI 功能
            </p>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  CloseOutlined,
  BulbOutlined,
  StarOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'

const props = withDefaults(defineProps<{
  visible?: boolean
}>(), {
  visible: false,
})

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'close'): void
}>()

const router = useRouter()

const recommendPlatforms = [
  { id: 'deepseek', name: 'DeepSeek', emoji: '🧠', configured: false },
  { id: 'siliconflow', name: '硅基流动', emoji: '🌊', configured: false },
  { id: 'openai', name: 'OpenAI', emoji: '🤖', configured: false },
]

function handleSetup() {
  emit('update:visible', false)
  emit('close')
  router.push('/admin/ai-center/provider-setup')
}

function handleLater() {
  emit('update:visible', false)
  emit('close')
}
</script>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.guide-modal {
  position: relative;
  width: 480px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 20px;
  padding: 40px 36px 32px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.2);
  text-align: center;
}
.guide-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 0.85rem;
}
.guide-close:hover {
  background: #e5e7eb;
  color: #374151;
}

.guide-header {
  margin-bottom: 28px;
}
.guide-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.guide-icon {
  font-size: 1.6rem;
  color: #fff;
}
.guide-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}
.guide-subtitle {
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.6;
  max-width: 380px;
  margin: 0 auto;
}

.guide-recommend {
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 28px;
  text-align: left;
}
.recommend-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #5b21b6;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.recommend-star {
  color: #f59e0b;
}
.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.recommend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.recommend-item.configured {
  opacity: 0.6;
}
.ri-emoji {
  font-size: 1.3rem;
}
.ri-name {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  color: #1f2937;
}

.guide-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}
.guide-btn-primary {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3);
}
.guide-btn-primary:hover {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4) !important;
}
.guide-btn-secondary {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  font-size: 0.9rem;
  color: #6b7280;
  border-color: #d1d5db;
}
.guide-btn-secondary:hover {
  color: #374151 !important;
  border-color: #9ca3af !important;
}
.guide-footnote {
  font-size: 0.72rem;
  color: #9ca3af;
  margin: 0;
}

/* Transitions */
.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.3s ease;
}
.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
}
.guide-scale-enter-active,
.guide-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.guide-scale-enter-from,
.guide-scale-leave-to {
  opacity: 0;
  transform: scale(0.92) translateY(20px);
}
</style>
