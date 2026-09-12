<template>
  <aside class="yd-copilot-slot" :class="{ open }" aria-label="AI Copilot">
    <header class="yd-copilot-slot__head">
      <div class="yd-copilot-slot__title">
        <RobotOutlined />
        <span>AI Copilot</span>
      </div>
      <button type="button" class="yd-copilot-slot__close" aria-label="关闭" @click="emit('update:open', false)">
        ×
      </button>
    </header>
    <div class="yd-copilot-slot__body">
      <slot>
        <p class="yd-copilot-slot__hint">出海运营助手 · 询盘解读、文案建议、合规提示</p>
        <a-button type="primary" block @click="goAssistant">打开完整助手</a-button>
      </slot>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { RobotOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';

defineProps<{ open: boolean }>();
const emit = defineEmits<{ 'update:open': [value: boolean] }>();

const router = useRouter();

function goAssistant() {
  const target = '/client/assistant';
  void router.push(target);
  emit('update:open', false);
}
</script>

<style scoped>
.yd-copilot-slot {
  position: fixed;
  top: 0;
  right: 0;
  width: 360px;
  max-width: 92vw;
  height: 100vh;
  background: var(--uj-bg-card, #fff);
  border-left: 1px solid var(--uj-border, #e2e8f0);
  box-shadow: -8px 0 32px rgb(15 23 42 / 0.08);
  z-index: 120;
  transform: translateX(100%);
  transition: transform 0.25s ease;
  display: flex;
  flex-direction: column;
}
.yd-copilot-slot.open {
  transform: translateX(0);
}
.yd-copilot-slot__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--uj-border, #e2e8f0);
}
.yd-copilot-slot__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}
.yd-copilot-slot__close {
  border: none;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  color: #94a3b8;
}
.yd-copilot-slot__body {
  flex: 1;
  overflow: auto;
  padding: 16px;
}
.yd-copilot-slot__hint {
  font-size: 13px;
  color: var(--uj-text-muted, #64748b);
  margin-bottom: 16px;
  line-height: 1.5;
}
</style>
