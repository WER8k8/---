<template>
  <!-- 外层导航项，position: relative 给下拉菜单做定位父级 -->
  <div
    class="nav-item"
    ref="navItemRef"
  >
    <button
      class="nav-button"
      @click="toggleMenu"
    >
      <span>分类管理</span>
    </button>

    <!-- 关键：不使用fixed/absolute定位，用正常文档流，实现向下推送 -->
    <div
      class="blinds-menu"
      ref="menuRef"
    >
      <div class="blind-item">
        <button class="add-btn">
          + 添加分类
        </button>
      </div>
      <div class="blind-item">
        测试分类1777566959
      </div>
      <div class="blind-item">
        测试分类1777566984
      </div>
      <div class="blind-item">
        压力分类1_1777566984
      </div>
      <div class="blind-item">
        压力分类3_1777566984
      </div>
      <div class="blind-item">
        压力分类21_1777566984
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  blindsAnimation: { type: Boolean, default: true }
})

const emit = defineEmits(['update:visible'])

const navItemRef = ref(null)
const menuRef = ref(null)

// 切换菜单
const toggleMenu = () => {
  emit('update:visible', !props.visible)
}

// 百叶窗动画逻辑（展开+收起）
watch(() => props.visible, (isVisible) => {
  if (!props.blindsAnimation || !menuRef.value) return

  nextTick(() => {
    const items = menuRef.value.querySelectorAll('.blind-item')
    items.forEach((item, index) => {
      if (isVisible) {
        // 展开：从上到下依次出现
        item.style.transitionDelay = `${index * 50}ms`
        item.style.maxHeight = '100px'
        item.style.opacity = '1'
      } else {
        // 收起：从下到上依次消失
        item.style.transitionDelay = `${(items.length - 1 - index) * 50}ms`
        item.style.maxHeight = '0'
        item.style.opacity = '0'
      }
    })
  })
})
</script>

<style scoped>
.nav-item {
  /* 父级设为relative，让子菜单在文档流中向下展开，不遮挡 */
  position: relative;
  width: 100%;
}

.nav-button {
  width: 100%;
  padding: 12px 16px;
  background: #409eff;
  color: white;
  border: none;
  text-align: left;
  cursor: pointer;
}

/* 关键：菜单用正常文档流，不脱离文档，所以会向下推送内容 */
.blinds-menu {
  width: 100%;
  background: white;
  border: 1px solid #eee;
}

.blind-item {
  /* 初始状态：高度0，透明，隐藏 */
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  padding: 0 16px;
  line-height: 40px;
  transition: max-height 0.3s ease, opacity 0.3s ease;
}

.add-btn {
  width: 100%;
  padding: 8px 0;
  background: #409eff;
  color: white;
  border: none;
  cursor: pointer;
}
</style>
