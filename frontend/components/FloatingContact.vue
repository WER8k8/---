<template>
  <div class="floating-contact">
    <!-- 微信悬浮窗 -->
    <div class="fc-item" @mouseenter="showWechat = true" @mouseleave="showWechat = false" @click="openWechat">
      <div class="fc-btn wechat">
        <svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22">
          <path d="M8.5 11a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm4 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm-2 7C6.478 18 3 15.09 3 11.5S6.478 5 10.5 5 18 7.91 18 11.5c0 1.105-.316 2.14-.863 3.03l.863 2.97-2.97-.863A7.437 7.437 0 0110.5 18z"/>
        </svg>
      </div>
      <span v-if="copied" class="fc-label copied">{{ t('contact.wechatCopied') }}</span>
      <transition name="fc-fade">
        <div v-if="showWechat && !copied" class="fc-popover wechat-popover">
          <div class="fc-popover-arrow" />
          <div class="fc-qr-placeholder">
            <div class="fc-qr-icon">
              <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                <path d="M8.5 11a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm4 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm-2 7C6.478 18 3 15.09 3 11.5S6.478 5 10.5 5 18 7.91 18 11.5c0 1.105-.316 2.14-.863 3.03l.863 2.97-2.97-.863A7.437 7.437 0 0110.5 18z"/>
              </svg>
            </div>
            <p class="fc-qr-text">{{ t('contact.wechatService') }}youding-builder</p>
            <p class="fc-qr-hint">{{ t('contact.wechatHint') }}</p>
          </div>
        </div>
      </transition>
    </div>

    <!-- 电话悬浮窗 -->
    <div class="fc-item" @click="callPhone">
      <div class="fc-btn phone">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22">
          <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
        </svg>
      </div>
      <span class="fc-label">{{ SITE_CONFIG.phone }}</span>
    </div>

    <!-- 留言/咨询悬浮窗 -->
    <div class="fc-item" @click="openInquiry">
      <div class="fc-btn inquiry">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
      </div>
      <span class="fc-label">{{ t('contact.onlineMessage') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();

const showWechat = ref(false);
const copied = ref(false);

function openInquiry() {
  window.location.href = '/contact';
}

function openWechat() {
  // 优先使用 weixin:// 协议尝试唤起微信
  const weixinUrl = 'weixin://';
  window.location.href = weixinUrl;

  // 同时复制微信号到剪贴板（用户可在微信中搜索添加）
  const textArea = document.createElement('textarea');
  textArea.value = 'youding-builder';
  textArea.style.position = 'fixed';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.select();

  try {
    document.execCommand('copy');
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch (e) {
    // 复制失败静默处理
  }

  document.body.removeChild(textArea);
}

function callPhone() {
  window.location.href = 'tel:' + SITE_CONFIG.phone;
}
</script>

<style scoped>
.floating-contact {
  position: fixed;
  right: 20px;
  bottom: 120px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fc-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  cursor: pointer;
}

.fc-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  flex-shrink: 0;
}

.fc-btn:hover {
  transform: scale(1.08);
}

.fc-btn.wechat { background: #07C160; }
.fc-btn.phone { background: #3b82f6; }
.fc-btn.inquiry { background: #8b5cf6; }

.fc-label {
  position: absolute;
  right: 54px;
  white-space: nowrap;
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 13px;
  opacity: 0;
  pointer-events: none;
  transition: all 0.25s ease;
  transform: translateX(8px);
}

.fc-item:hover .fc-label,
.fc-label.copied {
  opacity: 1;
  transform: translateX(0);
}

.fc-label.copied {
  background: rgba(7, 193, 96, 0.9);
}

/* WeChat popover */
.fc-popover {
  position: absolute;
  right: 54px;
  bottom: 0;
  background: white;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  width: 180px;
  z-index: 1000;
}

.fc-popover-arrow {
  position: absolute;
  right: -6px;
  bottom: 18px;
  width: 12px;
  height: 12px;
  background: white;
  transform: rotate(45deg);
  border-radius: 2px;
}

.fc-qr-placeholder {
  text-align: center;
}

.fc-qr-icon {
  width: 100px;
  height: 100px;
  background: #f0fdf4;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  color: #07C160;
}

.fc-qr-text {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px;
}

.fc-qr-hint {
  font-size: 11px;
  color: #999;
  margin: 0;
}

/* Transition */
.fc-fade-enter-active,
.fc-fade-leave-active {
  transition: all 0.25s ease;
}
.fc-fade-enter-from,
.fc-fade-leave-to {
  opacity: 0;
  transform: translateX(10px) scale(0.95);
}

/* Mobile adaptation */
@media (max-width: 768px) {
  .floating-contact {
    right: 12px;
    bottom: 100px;
    gap: 8px;
  }

  .fc-btn {
    width: 40px;
    height: 40px;
    border-radius: 10px;
  }

  .fc-label, .fc-popover {
    display: none;
  }
}
</style>
