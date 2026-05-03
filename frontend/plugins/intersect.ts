import { DirectiveBinding } from 'vue'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.directive('intersect', {
    mounted(el: HTMLElement, binding: DirectiveBinding) {
      if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
        const callback = binding.value
        
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                callback(true)
              }
            })
          },
          {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
          }
        )
        
        observer.observe(el)
        
        el._observer = observer
      } else {
        binding.value(true)
      }
    },
    unmounted(el: HTMLElement) {
      if (el._observer) {
        el._observer.disconnect()
      }
    }
  })
})
