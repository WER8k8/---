# SEO 矩阵后端 seo-backend/src

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\seo-backend\src` · **73 个文件** · SEO 矩阵后端（Node/Express）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `seo-backend/src/app.js` | 129 | 定义:express,cors,helmet,compression,morgan,rateLimit,matrixDatabase,authRouter · ⚑DEGRADED |
| `seo-backend/src/config/database.js` | 114 | 定义:logger,path,dialect,sequelize,AdminUser,SystemConfig,Region,IndustryKeyword |
| `seo-backend/src/config/matrixDatabase.js` | 85 | 定义:logger,isMatrixMysqlConfigured,host,name,user,getMatrixSequelize,authenticateMatrixDb,s · ⚑DEGRADED |
| `seo-backend/src/config/sqlite3-shim.js` | 188 | 定义:BetterSqlite3,convertedSql,stmt,paramObj,paramObj,cleanKey,ctx,convertedSql · ⚑MOCK |
| `seo-backend/src/controllers/article.controller.js` | 196 | 定义:GeneratedArticle,ArticleTemplate,Region,getArticles,where,result,getArticleById,article |
| `seo-backend/src/controllers/auth.controller.js` | 62 | 定义:jwt,bcrypt,refreshToken,decoded,user,newToken,getProfile,user |
| `seo-backend/src/controllers/authUnifiedGate.controller.js` | 29 | 定义:getUnifiedLoginRedirect,base,q,back,target,postLoginForbidden,handleAuthLogin |
| `seo-backend/src/controllers/config.controller.js` | 54 | 定义:SystemConfig,getConfigs,configs,result,getConfigByGroup,configs,result,updateConfig |
| `seo-backend/src/controllers/dashboard.controller.js` | 82 | 定义:getDashboardStats,result,getTrendData,dates,generated,published,indexed,date |
| `seo-backend/src/controllers/keyword.controller.js` | 143 | 定义:IndustryKeyword,LongtailKeyword,getKeywords,where,result,getKeywordById,keyword,createKeyword |
| `seo-backend/src/controllers/log.controller.js` | 110 | 定义:OperationLog,LoginLog,getOperationLogs,where,result,getLoginLogs,where,result |
| `seo-backend/src/controllers/monitoring.controller.js` | 106 | 定义:IndexingRecord,GeneratedArticle,SystemAlert,getIndexingRecords,where,result,checkIndex,article |
| `seo-backend/src/controllers/platform.controller.js` | 102 | 定义:Platform,PlatformAccount,getPlatforms,platforms,getPlatformAccounts,result,createPlatformAccount,platform |
| `seo-backend/src/controllers/publish.controller.js` | 151 | 定义:PublishTask,GeneratedArticle,PlatformAccount,createPublishTask,article,tasks,account,task |
| `seo-backend/src/controllers/region.controller.js` | 108 | 定义:Region,getRegionsTree,tree,getRegionsList,offset,where,batchUpdateStatus,buildTree |
| `seo-backend/src/controllers/socialAuth.controller.js` | 269 | 定义:jwt,bcrypt,crypto,logger,generateVerificationCode,sendEmailVerificationCode,sendEmailCode,code |
| `seo-backend/src/controllers/template.controller.js` | 106 | 定义:ArticleTemplate,getTemplates,where,result,getTemplateById,template,createTemplate,newTemplate |
| `seo-backend/src/controllers/wechatPush.controller.js` | 184 | 定义:logger,sendWechatMessage,getWechatPushConfig,updateWechatPushConfig,getPushLogs,offset,where,sendDailyReport |
| `seo-backend/src/middleware/auth.js` | 83 | 定义:jwt,AdminUser,logger,resolveUserFromBearerToken,nodeSecret,mainSecret,decoded,py |
| `seo-backend/src/middleware/errorHandler.js` | 53 | 定义:logger,errorHandler,statusCode,message,errorResponse,asyncHandler |
| `seo-backend/src/models/AdminUser.js` | 33 |  |
| `seo-backend/src/models/ArticleTemplate.js` | 50 |  |
| `seo-backend/src/models/EmailVerification.js` | 29 |  |
| `seo-backend/src/models/GeneratedArticle.js` | 63 |  |
| `seo-backend/src/models/IndexingRecord.js` | 53 |  |
| `seo-backend/src/models/IndustryKeyword.js` | 47 |  |
| `seo-backend/src/models/LoginLog.js` | 45 |  |
| `seo-backend/src/models/LongtailKeyword.js` | 38 |  |
| `seo-backend/src/models/OperationLog.js` | 48 |  |
| `seo-backend/src/models/Platform.js` | 47 |  |
| `seo-backend/src/models/PlatformAccount.js` | 56 |  |
| `seo-backend/src/models/PublishTask.js` | 52 |  |
| `seo-backend/src/models/Region.js` | 48 |  |
| `seo-backend/src/models/SocialLogin.js` | 34 |  |
| `seo-backend/src/models/SystemAlert.js` | 41 |  |
| `seo-backend/src/models/SystemConfig.js` | 41 |  |
| `seo-backend/src/models/WechatPushConfig.js` | 30 |  |
| `seo-backend/src/models/WechatPushLog.js` | 23 |  |
| `seo-backend/src/routes/article.routes.js` | 22 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/auth.routes.js` | 12 | 定义:express,router,authController,authUnifiedGate,authMiddleware |
| `seo-backend/src/routes/config.routes.js` | 10 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/dashboard.routes.js` | 11 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/keyword.routes.js` | 20 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/log.routes.js` | 9 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/monitoring.routes.js` | 16 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/platform.routes.js` | 18 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/publish.routes.js` | 18 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/region.routes.js` | 10 | 定义:express,router,authMiddleware,regionController |
| `seo-backend/src/routes/socialAuth.routes.js` | 12 | 定义:express,router,socialAuthController,authMiddleware |
| `seo-backend/src/routes/template.routes.js` | 18 | 定义:express,router,authMiddleware |
| `seo-backend/src/routes/wechatPush.routes.js` | 11 | 定义:express,router,wechatPushController,authMiddleware |
| `seo-backend/src/scripts/createAdmin.js` | 45 | 定义:bcrypt,AdminUser,createAdmin,existingUser,password,hashedPassword,adminUser |
| `seo-backend/src/scripts/initData.js` | 242 | 定义:Platform,Region,SystemConfig,IndustryKeyword,ArticleTemplate,platforms,regions,systemConfigs |
| `seo-backend/src/services/aiGenerator.js` | 186 | 定义:ArticleTemplate,IndustryKeyword,Region,GeneratedArticle,generateArticleContent,templateContent,replacements,generateDefaultContent |
| `seo-backend/src/services/articleService.js` | 133 | 定义:GeneratedArticle,IndexingRecord,getArticles,where,result,getArticleById,article,createArticle |
| `seo-backend/src/services/configService.js` | 95 | 定义:SystemConfig,getGroups,groups,getConfig,configs,result,updateConfig,resetConfig |
| `seo-backend/src/services/dashboardService.js` | 152 | 定义:GeneratedArticle,IndexingRecord,PublishTask,Region,IndustryKeyword,getStats,totalRegions,totalKeywords |
| `seo-backend/src/services/index.js` | 14 |  |
| `seo-backend/src/services/keywordService.js` | 120 | 定义:IndustryKeyword,LongtailKeyword,getKeywords,where,result,getKeywordById,createKeyword,updateKeyword |
| `seo-backend/src/services/logService.js` | 130 | 定义:OperationLog,LoginLog,getOperationLogs,where,result,getLoginLogs,where,result |
| `seo-backend/src/services/monitoringService.js` | 168 | 定义:IndexingRecord,GeneratedArticle,SystemAlert,getRecords,where,result,getStats,total |
| `seo-backend/src/services/platformAdapter.js` | 301 | 定义:PlatformAccount,PublishTask,GeneratedArticle,PlatformAdapter,adapter,adapters,TiebaAdapter,success |
| `seo-backend/src/services/platformService.js` | 140 | 定义:Platform,PlatformAccount,getPlatforms,where,result,getPlatformById,createPlatform,updatePlatform |
| `seo-backend/src/services/publishService.js` | 155 | 定义:PublishTask,GeneratedArticle,getTasks,where,result,getTaskById,createTask,task |
| `seo-backend/src/services/regionService.js` | 125 | 定义:Region,getRegionsTree,getRegionsList,where,getRegionById,createRegion,updateRegion,region |
| `seo-backend/src/services/templateService.js` | 105 | 定义:ArticleTemplate,getTemplates,where,result,getTemplateById,createTemplate,updateTemplate,template |
| `seo-backend/src/tasks/cron.js` | 27 | 定义:cron,logger,scheduleWechatPush,startCron |
| `seo-backend/src/tasks/index.js` | 4 |  |
| `seo-backend/src/tasks/processors.js` | 88 | 定义:GeneratedArticle,IndexingRecord,article,articles,startWorkers |
| `seo-backend/src/tasks/queue.js` | 102 | 定义:Queue,REDIS_URL,publishQueue,indexingQueue,articleQueue,queues,addPublishJob,job |
| `seo-backend/src/utils/assertJwtSecrets.js` | 38 | 定义:assertJwtSecretsSafeOrThrow,main,node,a,b,err |
| `seo-backend/src/utils/logger.js` | 37 | 定义:winston,path,logDir,logger |
| `seo-backend/src/utils/startupConfigValidation.js` | 122 | 定义:logger,isProduction,parseHttpUrl,s,u,validateSeoMatrixDbEnvOrThrow,host,name |