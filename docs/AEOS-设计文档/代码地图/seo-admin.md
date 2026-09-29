# SEO 矩阵后台 seo-admin/src

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\seo-admin\src` · **29 个文件** · SEO 矩阵后台（Vite+Vue3+ElementPlus）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `seo-admin/src/App.vue` | 7 | 组件:App · 根:router-view |
| `seo-admin/src/api/article.js` | 28 | 定义:articleApi · 依赖:./index |
| `seo-admin/src/api/config.js` | 28 | 定义:configApi,formData · 依赖:./index |
| `seo-admin/src/api/dashboard.js` | 22 | 定义:dashboardApi · 依赖:./index |
| `seo-admin/src/api/index.js` | 60 | 定义:api,token · 依赖:@/utils/authBridge |
| `seo-admin/src/api/keyword.js` | 28 | 定义:keywordApi · 依赖:./index |
| `seo-admin/src/api/log.js` | 23 | 定义:logApi · 依赖:./index |
| `seo-admin/src/api/monitoring.js` | 31 | 定义:monitoringApi · 依赖:./index |
| `seo-admin/src/api/platform.js` | 34 | 定义:platformApi · 依赖:./index |
| `seo-admin/src/api/publish.js` | 34 | 定义:publishApi · 依赖:./index |
| `seo-admin/src/api/region.js` | 31 | 定义:regionApi,formData · 依赖:./index |
| `seo-admin/src/api/template.js` | 28 | 定义:templateApi · 依赖:./index |
| `seo-admin/src/layouts/MainLayout.vue` | 208 | 组件:MainLayout · 根:el-container · 定义:route,router,userStore,isCollapse,activeMenu,currentTitle,toggleCollapse,handleCommand · 依赖:@/stores/user,@/utils/authBridge |
| `seo-admin/src/main.js` | 25 | 定义:app,pinia · 依赖:./App.vue,./router,./stores/user |
| `seo-admin/src/pages/Articles.vue` | 414 | 组件:Articles · 根:div · 定义:articles,loading,searchQuery,statusFilter,regionFilter,total,currentPage,pageSize · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/pages/CapabilityHub.vue` | 245 | 组件:CapabilityHub · 根:div · 定义:router,adminOrigin,adminHref,openAdmin,url,goBack,blocks |
| `seo-admin/src/pages/Dashboard.vue` | 353 | 组件:Dashboard · 根:div · 定义:stats,alerts,trendChartRef,formatNumber,fetchStats,res,fetchAlerts,res · 依赖:@/api |
| `seo-admin/src/pages/Keywords.vue` | 434 | 组件:Keywords · 根:div · 定义:activeTab,keywords,loading,searchQuery,categoryFilter,total,currentPage,pageSize · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/pages/LocalLogin.vue` | 172 | 组件:LocalLogin · 根:div · 定义:router,userStore,loginFormRef,loading,loginForm,rules,handleLogin,response · 依赖:@/stores/user · ⚑MOCK |
| `seo-admin/src/pages/Logs.vue` | 280 | 组件:Logs · 根:div · 定义:activeTab,loading,loginLoading,searchQuery,moduleFilter,dateRange,currentPage,pageSize · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/pages/Monitoring.vue` | 461 | 组件:Monitoring · 根:div · 定义:activeTab,loading,searchQuery,searchEngineFilter,indexStatusFilter,alertLevelFilter,indexingData,alertsData · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/pages/Platforms.vue` | 302 | 组件:Platforms · 根:div · 定义:platforms,loading,searchQuery,categoryFilter,platformOptions,showAddAccountDialog,showAccountsDialog,currentPlatform · ⚑MOCK |
| `seo-admin/src/pages/PublishTasks.vue` | 362 | 组件:PublishTasks · 根:div · 定义:tasks,loading,searchQuery,statusFilter,total,currentPage,pageSize,selectedTasks · ⚑MOCK |
| `seo-admin/src/pages/Regions.vue` | 318 | 组件:Regions · 根:div · 定义:regions,loading,searchQuery,total,currentPage,pageSize,showImportDialog,showEditDialog · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/pages/Settings.vue` | 324 | 组件:Settings · 根:div · 定义:activeTab,basicForm,linkForm,aiForm,riskForm,wechatForm,pushLogs,logsLoading · 依赖:@/api · ⚑MOCK/STUB |
| `seo-admin/src/pages/Templates.vue` | 309 | 组件:Templates · 根:div · 定义:templates,loading,searchQuery,categoryFilter,total,currentPage,pageSize,categories · 依赖:@/api · ⚑MOCK |
| `seo-admin/src/router/index.js` | 120 | 定义:routes,router,userStore · 依赖:@/stores/user,@/utils/authBridge |
| `seo-admin/src/stores/user.js` | 76 | 定义:useUserStore,t,response,body · 依赖:@/utils/authBridge |
| `seo-admin/src/utils/authBridge.js` | 53 | 定义:TOKEN_KEYS,getSharedBearerToken,t,persistSharedToken,v,clearSharedSession,getMainAdminOrigin,getMainAdminLoginPath |