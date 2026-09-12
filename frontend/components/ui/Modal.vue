<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-end justify-center z-[8000]" style="padding-bottom: env(safe-area-inset-bottom)" @click.self="handleOverlayClick">
        <Transition name="modal-slide" appear>
          <div v-if="visible" class="w-full max-w-lg max-h-[80vh] bg-white rounded-t-2xl flex flex-col overflow-hidden">
            <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
              <button v-if="closable" class="w-9 h-9 flex items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 active:bg-gray-200 text-lg" @click="close">&times;</button>
            </div>
            <div class="flex-1 overflow-y-auto p-5">
              <slot />
            </div>
            <div v-if="$slots.footer" class="px-5 py-4 border-t border-gray-100">
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  visible: boolean
  title?: string
  closable?: boolean
  closeOnOverlay?: boolean
}>(), {
  visible: false,
  title: '',
  closable: true,
  closeOnOverlay: true
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function close() {
  emit('update:visible', false)
}

function handleOverlayClick() {
  if (props.closeOnOverlay) {
    close()
  }
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-slide-enter-active {
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.modal-slide-leave-active {
  transition: transform 0.2s ease-in;
}
.modal-slide-enter-from,
.modal-slide-leave-to {
  transform: translateY(100%);
}
</style>
