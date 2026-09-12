export default defineNuxtRouteMiddleware((to, from) => {
  try {
    // 可以在这里添加路由级别的错误处理
    console.debug('Navigating to:', to.path);
  } catch (error) {
    console.error('Route middleware error:', error);
    return navigateTo('/');
  }
});
