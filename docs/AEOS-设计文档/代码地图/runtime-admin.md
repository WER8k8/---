# 运行源内嵌 admin 子应用（重复副本）

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\主要备份\上线网站\frontend\admin` · **1783 个文件** · 运行源内嵌的独立 admin 子应用（重复副本）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `admin/capacitor.config.ts` | 13 | 定义:config |
| `admin/orval.config.ts` | 66 | 定义:paths,filtered,seenOperationIds,dedupedPaths,methods,newPathItem,operation · 依赖:./src/api/naming |
| `admin/postcss.config.js` | 6 |  |
| `admin/public/sw.js` | 30 | 定义:CACHE,SHELL,url |
| `admin/src/App.vue` | 140 | 组件:App · 定义:routeReady,showSlowHint,router,ui,antTheme,role,isDark,accent · 依赖:@/components/common/CookieConsent.vue,@/composables/useRumBeacon,@/constants/brandTheme,@/stores/uiPreferences |
| `admin/src/api/__tests__/admin-bff-logout.test.ts` | 63 | 定义:post,get,responseUse,requestUse,path,config,config · ⚑MOCK |
| `admin/src/api/admin-bff.ts` | 176 | 定义:createBffClient,client,headers,method,csrf,body,code,message · 依赖:./admin-bff.types,@/api/index,@/auth/session · ⚑DEGRADED |
| `admin/src/api/admin-bff.types.ts` | 71 | 定义:UacTenantBrief,UacOnboardingStep,UacPlanUsage,UacUserInfo,UacMenuRoute,UacPermissionBundle,UacLoginResult,UacTenantSearchHit |
| `admin/src/api/agentObservability.ts` | 196 | 定义:AgentRunSummary,AgentStepDetail,IntentSpecView,AgentRunDetail,RunDetailPayload,AgentRunListResult,FunnelRunsBlock,FunnelAlignmentBlock · 依赖:@/utils/api |
| `admin/src/api/analytics.ts` | 22 | 定义:dataAnalyticsAPI,q,search,q,q · 依赖:@/utils/api |
| `admin/src/api/authPaths.ts` | 25 | 定义:apiV1Base,b,normalizeAuthLoginPath,fallback,p0,p,authLoginUrl,p · ⚑DEGRADED |
| `admin/src/api/authRefresh.ts` | 66 | 定义:baseURL,parseRefreshOk,o,REFRESH_TIMEOUT_MS,performSilentTokenRefresh,p,url,controller · 依赖:@/auth/session,@/utils/sessionKick |
| `admin/src/api/core.ts` | 230 | 定义:navigateApiForbidden,q,apiPath,API_BASE_URL,isCollectionRoute,collectionPatterns,restCollectionPattern,withCollectionTrailingSlash · 依赖:./authRefresh,./naming,@/auth/session,@/types/api,@/utils/sessionKick |
| `admin/src/api/cross-border.ts` | 685 | 定义:BridgeSummary,ReplyDraft,InquiryBridgeStatus,ImapPollResult,ExportQuote,VideoDubResult,ProductCandidate,TranscribeResult · 依赖:@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/api/emailAuth.ts` | 23 | 定义:sendEmailLoginCode,loginByEmail,data · 依赖:@/utils/api |
| `admin/src/api/foreign-trade.ts` | 202 | 定义:AgentEnvelope,B2bExpert,PreflightResult,API_BASE,osintCheck,websiteIcpProfile,proformaInvoice,inquiryOsint · 依赖:@/utils/api |
| `admin/src/api/forum.ts` | 54 | 定义:ForumConfig,fetchForumStatus,fetchForumConfig,updateForumConfig,fetchForumSetupGuide,ForumTranslateResult,translateForumQa · 依赖:@/utils/api |
| `admin/src/api/founderOps.ts` | 119 | 定义:authHeaders,token,FounderPreflight,FounderStatus,CryptoSelfTest,founderFetch,res,raw · 依赖:@/api,@/api/authPaths,@/utils/sessionAuth |
| `admin/src/api/generated/client.ts` | 16240 | 定义:getSeo,healthCheckApiV1HealthGet,dbHealthApiV1HealthDbGet,readinessApiV1HealthReadyGet,loginApiV1AuthLoginPost,refreshTokenApiV1AuthRefreshPost,logoutApiV1AuthLogoutPost,changePasswordApiV1AuthChangePasswordPost · 依赖:../core.ts,./schemas · ⚑MOCK/STUB/DEGRADED |
| `admin/src/api/generated/schemas/aBTestConversionResponse.ts` | 20 | 定义:ABTestConversionResponse · 依赖:./aBTestConversionResponseConversionData.ts |
| `admin/src/api/generated/schemas/aBTestConversionResponseConversionData.ts` | 9 | 定义:ABTestConversionResponseConversionData |
| `admin/src/api/generated/schemas/aBTestCreate.ts` | 23 | 定义:ABTestCreate · 依赖:./aBTestCreateVariantsConfig.ts |
| `admin/src/api/generated/schemas/aBTestCreateVariantsConfig.ts` | 9 | 定义:ABTestCreateVariantsConfig |
| `admin/src/api/generated/schemas/aBTestDetailResponse.ts` | 33 | 定义:ABTestDetailResponse · 依赖:./aBTestDetailResponseVariantsConfig.ts,./aBTestVariantResponse.ts |
| `admin/src/api/generated/schemas/aBTestDetailResponseVariantsConfig.ts` | 9 | 定义:ABTestDetailResponseVariantsConfig |
| `admin/src/api/generated/schemas/aBTestEventResponse.ts` | 23 | 定义:ABTestEventResponse · 依赖:./aBTestEventResponseEventData.ts |
| `admin/src/api/generated/schemas/aBTestEventResponseEventData.ts` | 9 | 定义:ABTestEventResponseEventData |
| `admin/src/api/generated/schemas/aBTestResponse.ts` | 31 | 定义:ABTestResponse · 依赖:./aBTestResponseVariantsConfig.ts |
| `admin/src/api/generated/schemas/aBTestResponseVariantsConfig.ts` | 9 | 定义:ABTestResponseVariantsConfig |
| `admin/src/api/generated/schemas/aBTestUpdate.ts` | 24 | 定义:ABTestUpdate · 依赖:./aBTestUpdateVariantsConfig.ts |
| `admin/src/api/generated/schemas/aBTestUpdateVariantsConfig.ts` | 9 | 定义:ABTestUpdateVariantsConfig |
| `admin/src/api/generated/schemas/aBTestVariantCreate.ts` | 17 | 定义:ABTestVariantCreate · 依赖:./aBTestVariantCreateContentConfig.ts |
| `admin/src/api/generated/schemas/aBTestVariantCreateContentConfig.ts` | 9 | 定义:ABTestVariantCreateContentConfig |
| `admin/src/api/generated/schemas/aBTestVariantResponse.ts` | 25 | 定义:ABTestVariantResponse · 依赖:./aBTestVariantResponseContentConfig.ts,./aBTestVariantResponseMetricsData.ts |
| `admin/src/api/generated/schemas/aBTestVariantResponseContentConfig.ts` | 9 | 定义:ABTestVariantResponseContentConfig |
| `admin/src/api/generated/schemas/aBTestVariantResponseMetricsData.ts` | 9 | 定义:ABTestVariantResponseMetricsData |
| `admin/src/api/generated/schemas/aBTestVariantUpdate.ts` | 16 | 定义:ABTestVariantUpdate · 依赖:./aBTestVariantUpdateContentConfig.ts |
| `admin/src/api/generated/schemas/aBTestVariantUpdateContentConfig.ts` | 9 | 定义:ABTestVariantUpdateContentConfig |
| `admin/src/api/generated/schemas/aIModelCreate.ts` | 19 | 定义:AIModelCreate |
| `admin/src/api/generated/schemas/aIModelPatch.ts` | 18 | 定义:AIModelPatch |
| `admin/src/api/generated/schemas/aIProviderCreate.ts` | 18 | 定义:AIProviderCreate |
| `admin/src/api/generated/schemas/aIProviderPatch.ts` | 18 | 定义:AIProviderPatch |
| `admin/src/api/generated/schemas/aITemplateCreate.ts` | 20 | 定义:AITemplateCreate |
| `admin/src/api/generated/schemas/aITemplateUpdate.ts` | 18 | 定义:AITemplateUpdate |
| `admin/src/api/generated/schemas/aPIResponse.ts` | 19 | 定义:APIResponse |
| `admin/src/api/generated/schemas/aPIResponseCategoryResponse.ts` | 17 | 定义:APIResponseCategoryResponse · 依赖:./categoryResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseContentPageListResponse.ts` | 17 | 定义:APIResponseContentPageListResponse · 依赖:./contentPageListResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseContentPageResponse.ts` | 17 | 定义:APIResponseContentPageResponse · 依赖:./contentPageResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseContentVersionResponse.ts` | 17 | 定义:APIResponseContentVersionResponse · 依赖:./contentVersionResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseDict.ts` | 17 | 定义:APIResponseDict · 依赖:./aPIResponseDictData.ts |
| `admin/src/api/generated/schemas/aPIResponseDictData.ts` | 9 | 定义:APIResponseDictData |
| `admin/src/api/generated/schemas/aPIResponseDomainBindingResponse.ts` | 17 | 定义:APIResponseDomainBindingResponse · 依赖:./domainBindingResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseDomainListResponse.ts` | 17 | 定义:APIResponseDomainListResponse · 依赖:./domainListResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseEmailVerificationResponse.ts` | 17 | 定义:APIResponseEmailVerificationResponse · 依赖:./emailVerificationResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListCategoryResponse.ts` | 17 | 定义:APIResponseListCategoryResponse · 依赖:./categoryResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListContentVersionResponse.ts` | 17 | 定义:APIResponseListContentVersionResponse · 依赖:./contentVersionResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListProductDocumentResponse.ts` | 17 | 定义:APIResponseListProductDocumentResponse · 依赖:./productDocumentResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListProductResponse.ts` | 17 | 定义:APIResponseListProductResponse · 依赖:./productResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListReviewResponse.ts` | 17 | 定义:APIResponseListReviewResponse · 依赖:./reviewResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseListTenantPlanResponse.ts` | 17 | 定义:APIResponseListTenantPlanResponse · 依赖:./tenantPlanResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseLogoutResponse.ts` | 17 | 定义:APIResponseLogoutResponse · 依赖:./logoutResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseOAuthAuthorizeResponse.ts` | 17 | 定义:APIResponseOAuthAuthorizeResponse · 依赖:./oAuthAuthorizeResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseProductDocumentResponse.ts` | 17 | 定义:APIResponseProductDocumentResponse · 依赖:./productDocumentResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseProductListResponse.ts` | 17 | 定义:APIResponseProductListResponse · 依赖:./productListResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseProductResponse.ts` | 17 | 定义:APIResponseProductResponse · 依赖:./productResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseReviewResponse.ts` | 17 | 定义:APIResponseReviewResponse · 依赖:./reviewResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseReviewStatsResponse.ts` | 17 | 定义:APIResponseReviewStatsResponse · 依赖:./reviewStatsResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseSeoMetadataResponse.ts` | 17 | 定义:APIResponseSeoMetadataResponse · 依赖:./seoMetadataResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseTenantInvoiceListResponse.ts` | 17 | 定义:APIResponseTenantInvoiceListResponse · 依赖:./tenantInvoiceListResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseTenantOverviewResponse.ts` | 17 | 定义:APIResponseTenantOverviewResponse · 依赖:./tenantOverviewResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseTenantPlanResponse.ts` | 17 | 定义:APIResponseTenantPlanResponse · 依赖:./tenantPlanResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseTenantResponse.ts` | 17 | 定义:APIResponseTenantResponse · 依赖:./tenantResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseThirdPartyLoginResponse.ts` | 17 | 定义:APIResponseThirdPartyLoginResponse · 依赖:./thirdPartyLoginResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseTokenResponse.ts` | 17 | 定义:APIResponseTokenResponse · 依赖:./tokenResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseUserListResponse.ts` | 17 | 定义:APIResponseUserListResponse · 依赖:./userListResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseUserResponse.ts` | 17 | 定义:APIResponseUserResponse · 依赖:./appSchemasUserUserResponse.ts |
| `admin/src/api/generated/schemas/aPIResponseWhiteLabelConfig.ts` | 17 | 定义:APIResponseWhiteLabelConfig · 依赖:./whiteLabelConfig.ts |
| `admin/src/api/generated/schemas/accioSkillGapStubApiV1UbrainCommercialOsGapSkillIdGetParams.ts` | 19 | 定义:AccioSkillGapStubApiV1UbrainCommercialOsGapSkillIdGetParams |
| `admin/src/api/generated/schemas/accountOpeningRequest.ts` | 29 | 定义:AccountOpeningRequest |
| `admin/src/api/generated/schemas/addArticleAuthorApiV1SeoArticlesArticleIdAuthorsPost200.ts` | 9 | 定义:AddArticleAuthorApiV1SeoArticlesArticleIdAuthorsPost200 |
| `admin/src/api/generated/schemas/addArticleAuthorApiV1SeoArticlesArticleIdAuthorsPostBody.ts` | 9 | 定义:AddArticleAuthorApiV1SeoArticlesArticleIdAuthorsPostBody |
| `admin/src/api/generated/schemas/addCertificationApiV1SeoAuthorsAuthorIdCertificationsPost200.ts` | 9 | 定义:AddCertificationApiV1SeoAuthorsAuthorIdCertificationsPost200 |
| `admin/src/api/generated/schemas/addCertificationApiV1SeoAuthorsAuthorIdCertificationsPostBody.ts` | 9 | 定义:AddCertificationApiV1SeoAuthorsAuthorIdCertificationsPostBody |
| `admin/src/api/generated/schemas/addKeywordApiV1SeoComplianceKeywordsPostBody.ts` | 9 | 定义:AddKeywordApiV1SeoComplianceKeywordsPostBody |
| `admin/src/api/generated/schemas/addKeywordRequest.ts` | 20 | 定义:AddKeywordRequest |
| `admin/src/api/generated/schemas/addMessageToSessionApiV1ChatSessionsSessionIdAddMessagePost200.ts` | 9 | 定义:AddMessageToSessionApiV1ChatSessionsSessionIdAddMessagePost200 |
| `admin/src/api/generated/schemas/addMessageToSessionApiV1ChatSessionsSessionIdAddMessagePostParams.ts` | 14 | 定义:AddMessageToSessionApiV1ChatSessionsSessionIdAddMessagePostParams |
| `admin/src/api/generated/schemas/addTrustSignalApiV1SeoContentContentIdTrustSignalsPost200.ts` | 9 | 定义:AddTrustSignalApiV1SeoContentContentIdTrustSignalsPost200 |
| `admin/src/api/generated/schemas/addTrustSignalApiV1SeoContentContentIdTrustSignalsPostBody.ts` | 9 | 定义:AddTrustSignalApiV1SeoContentContentIdTrustSignalsPostBody |
| `admin/src/api/generated/schemas/adminCreateRequest.ts` | 22 | 定义:AdminCreateRequest |
| `admin/src/api/generated/schemas/adminLoginRequest.ts` | 21 | 定义:AdminLoginRequest |
| `admin/src/api/generated/schemas/adminUserCreate.ts` | 16 | 定义:AdminUserCreate |
| `admin/src/api/generated/schemas/adminUserUpdate.ts` | 15 | 定义:AdminUserUpdate |
| `admin/src/api/generated/schemas/agentClientsApiV1AgentClientsGetParams.ts` | 21 | 定义:AgentClientsApiV1AgentClientsGetParams |
| `admin/src/api/generated/schemas/agentNodeUpdateBody.ts` | 13 | 定义:AgentNodeUpdateBody |
| `admin/src/api/generated/schemas/agentNodeWriteBody.ts` | 19 | 定义:AgentNodeWriteBody |
| `admin/src/api/generated/schemas/agentPaymentsApiV1AgentPaymentsGetParams.ts` | 19 | 定义:AgentPaymentsApiV1AgentPaymentsGetParams |
| `admin/src/api/generated/schemas/agentTrafficBoardApiV1AgentTrafficBoardGetParams.ts` | 12 | 定义:AgentTrafficBoardApiV1AgentTrafficBoardGetParams |
| `admin/src/api/generated/schemas/agentTrendsApiV1AgentTrendsGetParams.ts` | 15 | 定义:AgentTrendsApiV1AgentTrendsGetParams |
| `admin/src/api/generated/schemas/aiWriteBody.ts` | 13 | 定义:AiWriteBody |
| `admin/src/api/generated/schemas/alertAcknowledge.ts` | 20 | 定义:AlertAcknowledge |
| `admin/src/api/generated/schemas/alertResolve.ts` | 23 | 定义:AlertResolve |
| `admin/src/api/generated/schemas/alertSeverity.ts` | 20 | 定义:AlertSeverity,AlertSeverity |
| `admin/src/api/generated/schemas/alertType.ts` | 25 | 定义:AlertType,AlertType |
| `admin/src/api/generated/schemas/alipayProbeRequest.ts` | 18 | 定义:AlipayProbeRequest |
| `admin/src/api/generated/schemas/analyticsEventBody.ts` | 29 | 定义:AnalyticsEventBody · 依赖:./analyticsEventBodyMeta.ts |
| `admin/src/api/generated/schemas/analyticsEventBodyMeta.ts` | 9 | 定义:AnalyticsEventBodyMeta |
| `admin/src/api/generated/schemas/analyticsSiteContextApiV1AnalyticsSiteContextGetParams.ts` | 15 | 定义:AnalyticsSiteContextApiV1AnalyticsSiteContextGetParams |
| `admin/src/api/generated/schemas/analyzeContentRequest.ts` | 12 | 定义:AnalyzeContentRequest |
| `admin/src/api/generated/schemas/appApiV1GeoDEAnalysisRequest.ts` | 17 | 定义:AppApiV1GeoDEAnalysisRequest |
| `admin/src/api/generated/schemas/appApiV1RoutesAiGenerateGenerateRequest.ts` | 20 | 定义:AppApiV1RoutesAiGenerateGenerateRequest |
| `admin/src/api/generated/schemas/appApiV1RoutesAiGenerateOptimizeRequest.ts` | 16 | 定义:AppApiV1RoutesAiGenerateOptimizeRequest |
| `admin/src/api/generated/schemas/appApiV1RoutesBuildingWikiGenerateRequest.ts` | 12 | 定义:AppApiV1RoutesBuildingWikiGenerateRequest |
| `admin/src/api/generated/schemas/appApiV1SeoContentOptimizerOptimizeRequest.ts` | 18 | 定义:AppApiV1SeoContentOptimizerOptimizeRequest |
| `admin/src/api/generated/schemas/appApiV1SeoContentOptimizerValidateRequest.ts` | 12 | 定义:AppApiV1SeoContentOptimizerValidateRequest |
| `admin/src/api/generated/schemas/appApiV1SeoLlmsTxtGenerateRequest.ts` | 24 | 定义:AppApiV1SeoLlmsTxtGenerateRequest · 依赖:./appApiV1SeoLlmsTxtGenerateRequestSectionsItem.ts |
| `admin/src/api/generated/schemas/appApiV1SeoLlmsTxtGenerateRequestSectionsItem.ts` | 9 | 定义:AppApiV1SeoLlmsTxtGenerateRequestSectionsItem |
| `admin/src/api/generated/schemas/appApiV1SeoLlmsTxtValidateRequest.ts` | 11 | 定义:AppApiV1SeoLlmsTxtValidateRequest |
| `admin/src/api/generated/schemas/appApiV1SuperAdminAlertsAlertRuleCreate.ts` | 17 | 定义:AppApiV1SuperAdminAlertsAlertRuleCreate |
| `admin/src/api/generated/schemas/appApiV1SuperAdminGeoDEAnalysisRequest.ts` | 14 | 定义:AppApiV1SuperAdminGeoDEAnalysisRequest |
| `admin/src/api/generated/schemas/appApiV1SuperAdminGeoEngineGenerateRequest.ts` | 28 | 定义:AppApiV1SuperAdminGeoEngineGenerateRequest |
| `admin/src/api/generated/schemas/appApiV1SuperAdminGeoEngineOptimizeContentRequest1.ts` | 26 | 定义:AppApiV1SuperAdminGeoEngineOptimizeContentRequest1 · 依赖:./appApiV1SuperAdminGeoEngineOptimizeContentRequest1Context.ts |
| `admin/src/api/generated/schemas/appApiV1SuperAdminGeoEngineOptimizeContentRequest1Context.ts` | 12 | 定义:AppApiV1SuperAdminGeoEngineOptimizeContentRequest1Context |
| `admin/src/api/generated/schemas/appApiV1SuperAdminGeoEngineOptimizeContentRequest2.ts` | 12 | 定义:AppApiV1SuperAdminGeoEngineOptimizeContentRequest2 |
| `admin/src/api/generated/schemas/appChatRequest.ts` | 15 | 定义:AppChatRequest |
| `admin/src/api/generated/schemas/appInquiriesOfflineApiV1AppV1InquiriesOfflineGetParams.ts` | 11 | 定义:AppInquiriesOfflineApiV1AppV1InquiriesOfflineGetParams |
| `admin/src/api/generated/schemas/appModelsGeoAlertModelsAlertRuleCreate.ts` | 39 | 定义:AppModelsGeoAlertModelsAlertRuleCreate · 依赖:./alertSeverity.ts,./alertType.ts,./appModelsGeoAlertModelsAlertRuleCreateRuleConfig.ts |
| `admin/src/api/generated/schemas/appModelsGeoAlertModelsAlertRuleCreateRuleConfig.ts` | 12 | 定义:AppModelsGeoAlertModelsAlertRuleCreateRuleConfig |
| `admin/src/api/generated/schemas/appPushPublishFailedApiV1AppV1PushPublishFailedPostParams.ts` | 11 | 定义:AppPushPublishFailedApiV1AppV1PushPublishFailedPostParams |
| `admin/src/api/generated/schemas/appSchemasAuthLoginRequest.ts` | 14 | 定义:AppSchemasAuthLoginRequest |
| `admin/src/api/generated/schemas/appSchemasAuthUserResponse.ts` | 16 | 定义:AppSchemasAuthUserResponse |
| `admin/src/api/generated/schemas/appSchemasUserLoginRequest.ts` | 12 | 定义:AppSchemasUserLoginRequest |
| `admin/src/api/generated/schemas/appSchemasUserUserResponse.ts` | 17 | 定义:AppSchemasUserUserResponse |
| `admin/src/api/generated/schemas/articleToVideoBody.ts` | 15 | 定义:ArticleToVideoBody |
| `admin/src/api/generated/schemas/askKnowledgeApiV1AiKnowledgeKnowledgeAskPostParams.ts` | 14 | 定义:AskKnowledgeApiV1AiKnowledgeKnowledgeAskPostParams |
| `admin/src/api/generated/schemas/askKnowledgeApiV1KnowledgeKnowledgeAskPostParams.ts` | 14 | 定义:AskKnowledgeApiV1KnowledgeKnowledgeAskPostParams |
| `admin/src/api/generated/schemas/assignRequest.ts` | 11 | 定义:AssignRequest |
| `admin/src/api/generated/schemas/auditRunRequest.ts` | 14 | 定义:AuditRunRequest |
| `admin/src/api/generated/schemas/batchApplyRuleRequest.ts` | 13 | 定义:BatchApplyRuleRequest |
| `admin/src/api/generated/schemas/batchCancelRequest.ts` | 11 | 定义:BatchCancelRequest |
| `admin/src/api/generated/schemas/batchCheckRequest.ts` | 12 | 定义:BatchCheckRequest |
| `admin/src/api/generated/schemas/batchCorrectRequest.ts` | 12 | 定义:BatchCorrectRequest |
| `admin/src/api/generated/schemas/batchDeleteRequest.ts` | 11 | 定义:BatchDeleteRequest |
| `admin/src/api/generated/schemas/batchIdsBody.ts` | 12 | 定义:BatchIdsBody |
| `admin/src/api/generated/schemas/batchProductIdsBody.ts` | 12 | 定义:BatchProductIdsBody |
| `admin/src/api/generated/schemas/batchPublishBody.ts` | 13 | 定义:BatchPublishBody · 依赖:./batchPublishItem.ts |
| `admin/src/api/generated/schemas/batchPublishItem.ts` | 15 | 定义:BatchPublishItem |
| `admin/src/api/generated/schemas/batchRankCheckRequest.ts` | 26 | 定义:BatchRankCheckRequest |
| `admin/src/api/generated/schemas/batchRetryRequest.ts` | 11 | 定义:BatchRetryRequest |
| `admin/src/api/generated/schemas/batchScanApiV1SeoComplianceScanBatchPostBody.ts` | 9 | 定义:BatchScanApiV1SeoComplianceScanBatchPostBody |
| `admin/src/api/generated/schemas/batchStatusBody.ts` | 13 | 定义:BatchStatusBody |
| `admin/src/api/generated/schemas/bffTenantSearchApiV1AdminBffAuthTenantSearchGetParams.ts` | 11 | 定义:BffTenantSearchApiV1AdminBffAuthTenantSearchGetParams |
| `admin/src/api/generated/schemas/bodyDisconnectPlatformApiV1PlatformsPlatformIdDisconnectPost.ts` | 11 | 定义:BodyDisconnectPlatformApiV1PlatformsPlatformIdDisconnectPost |
| `admin/src/api/generated/schemas/bodyImportProductsCsvApiV1ProductsImportPost.ts` | 11 | 定义:BodyImportProductsCsvApiV1ProductsImportPost |
| `admin/src/api/generated/schemas/bodyImportRegionKeywordsPlaceholderApiV1SeoMatrixRegionKeywordsImportPost.ts` | 11 | 定义:BodyImportRegionKeywordsPlaceholderApiV1SeoMatrixRegionKeywordsImportPost · ⚑MOCK |
| `admin/src/api/generated/schemas/bodyUploadFileApiV1FilesFilesUploadPost.ts` | 11 | 定义:BodyUploadFileApiV1FilesFilesUploadPost |
| `admin/src/api/generated/schemas/bodyUploadFilesApiV1FilesFilesUploadMultiPost.ts` | 11 | 定义:BodyUploadFilesApiV1FilesFilesUploadMultiPost |
| `admin/src/api/generated/schemas/bodyUploadImageApiV1ContentPagesUploadImagePost.ts` | 11 | 定义:BodyUploadImageApiV1ContentPagesUploadImagePost |
| `admin/src/api/generated/schemas/bodyUploadProductDocumentApiV1ProductsProductIdDocumentsPost.ts` | 11 | 定义:BodyUploadProductDocumentApiV1ProductsProductIdDocumentsPost |
| `admin/src/api/generated/schemas/bodyUploadProductImageApiV1ProductImagesPost.ts` | 11 | 定义:BodyUploadProductImageApiV1ProductImagesPost |
| `admin/src/api/generated/schemas/boxplotDataApiV1SuperAdminGeoVisualizationBoxplotGdsIdGetParams.ts` | 15 | 定义:BoxplotDataApiV1SuperAdminGeoVisualizationBoxplotGdsIdGetParams |
| `admin/src/api/generated/schemas/cCSwitchCreate.ts` | 19 | 定义:CCSwitchCreate · 依赖:./cCSwitchCreateModelMapping.ts |
| `admin/src/api/generated/schemas/cCSwitchCreateModelMapping.ts` | 9 | 定义:CCSwitchCreateModelMapping |
| `admin/src/api/generated/schemas/cCSwitchUpdate.ts` | 18 | 定义:CCSwitchUpdate · 依赖:./cCSwitchUpdateModelMapping.ts |
| `admin/src/api/generated/schemas/cCSwitchUpdateModelMapping.ts` | 9 | 定义:CCSwitchUpdateModelMapping |
| `admin/src/api/generated/schemas/calculateEeatScoreApiV1SeoScorePost200.ts` | 9 | 定义:CalculateEeatScoreApiV1SeoScorePost200 |
| `admin/src/api/generated/schemas/calculateEeatScoreApiV1SeoScorePostBody.ts` | 9 | 定义:CalculateEeatScoreApiV1SeoScorePostBody |
| `admin/src/api/generated/schemas/caseImageCreate.ts` | 18 | 定义:CaseImageCreate |
| `admin/src/api/generated/schemas/caseStudyCreate.ts` | 18 | 定义:CaseStudyCreate |
| `admin/src/api/generated/schemas/caseStudyUpdate.ts` | 18 | 定义:CaseStudyUpdate |
| `admin/src/api/generated/schemas/categoryCreate.ts` | 15 | 定义:CategoryCreate |
| `admin/src/api/generated/schemas/categoryResponse.ts` | 18 | 定义:CategoryResponse |
| `admin/src/api/generated/schemas/categoryUpdate.ts` | 16 | 定义:CategoryUpdate |
| `admin/src/api/generated/schemas/changePasswordRequest.ts` | 12 | 定义:ChangePasswordRequest |
| `admin/src/api/generated/schemas/channelInquiryBody.ts` | 20 | 定义:ChannelInquiryBody |
| `admin/src/api/generated/schemas/chatRequest.ts` | 17 | 定义:ChatRequest |
| `admin/src/api/generated/schemas/checkAllAlertRulesApiV1SuperAdminGeoEngineAlertsCheckAllPostBody.ts` | 9 | 定义:CheckAllAlertRulesApiV1SuperAdminGeoEngineAlertsCheckAllPostBody |
| `admin/src/api/generated/schemas/checkPlanFeatureApiV1AdminBffPlanCheckGetParams.ts` | 12 | 定义:CheckPlanFeatureApiV1AdminBffPlanCheckGetParams |
| `admin/src/api/generated/schemas/checkRankApiV1RankCheckGetParams.ts` | 28 | 定义:CheckRankApiV1RankCheckGetParams |
| `admin/src/api/generated/schemas/checkRankRequest.ts` | 20 | 定义:CheckRankRequest |
| `admin/src/api/generated/schemas/checkRequest.ts` | 13 | 定义:CheckRequest |
| `admin/src/api/generated/schemas/clearAuditLogsApiV1SuperAdminAuditDeleteParams.ts` | 11 | 定义:ClearAuditLogsApiV1SuperAdminAuditDeleteParams |
| `admin/src/api/generated/schemas/clearAuditLogsApiV1SystemAuditLogsDeleteParams.ts` | 11 | 定义:ClearAuditLogsApiV1SystemAuditLogsDeleteParams |
| `admin/src/api/generated/schemas/clearCacheApiV1SuperAdminMonitorCacheClearPostParams.ts` | 11 | 定义:ClearCacheApiV1SuperAdminMonitorCacheClearPostParams |
| `admin/src/api/generated/schemas/clientListApplicationsApiV1ClientInvoiceApplicationsGetParams.ts` | 19 | 定义:ClientListApplicationsApiV1ClientInvoiceApplicationsGetParams |
| `admin/src/api/generated/schemas/clipBody.ts` | 12 | 定义:ClipBody |
| `admin/src/api/generated/schemas/clusterAnalysisApiV1SuperAdminGeoClusteringPostParams.ts` | 20 | 定义:ClusterAnalysisApiV1SuperAdminGeoClusteringPostParams |
| `admin/src/api/generated/schemas/collectPaymentRequest.ts` | 18 | 定义:CollectPaymentRequest |
| `admin/src/api/generated/schemas/commissionCreate.ts` | 19 | 定义:CommissionCreate |
| `admin/src/api/generated/schemas/commissionRuleUpdate.ts` | 13 | 定义:CommissionRuleUpdate |
| `admin/src/api/generated/schemas/companionPublishPayloadApiV1PublishCompanionPayloadGetParams.ts` | 16 | 定义:CompanionPublishPayloadApiV1PublishCompanionPayloadGetParams |
| `admin/src/api/generated/schemas/competitorCompareApiV1SuperAdminGeoEngineCompetitorPostParams.ts` | 11 | 定义:CompetitorCompareApiV1SuperAdminGeoEngineCompetitorPostParams |
| `admin/src/api/generated/schemas/confirmOutreachBody.ts` | 13 | 定义:ConfirmOutreachBody |
| `admin/src/api/generated/schemas/connectPlatformBody.ts` | 19 | 定义:ConnectPlatformBody · 依赖:./connectPlatformBodyConfigs.ts,./connectPlatformBodyTokenData.ts |
| `admin/src/api/generated/schemas/connectPlatformBodyConfigs.ts` | 9 | 定义:ConnectPlatformBodyConfigs |
| `admin/src/api/generated/schemas/connectPlatformBodyTokenData.ts` | 9 | 定义:ConnectPlatformBodyTokenData |
| `admin/src/api/generated/schemas/consumeRequest.ts` | 14 | 定义:ConsumeRequest |
| `admin/src/api/generated/schemas/contentMasterCreate.ts` | 22 | 定义:ContentMasterCreate |
| `admin/src/api/generated/schemas/contentMasterUpdate.ts` | 17 | 定义:ContentMasterUpdate |
| `admin/src/api/generated/schemas/contentPageCreate.ts` | 16 | 定义:ContentPageCreate |
| `admin/src/api/generated/schemas/contentPageListResponse.ts` | 15 | 定义:ContentPageListResponse · 依赖:./contentPageResponse.ts |
| `admin/src/api/generated/schemas/contentPageResponse.ts` | 23 | 定义:ContentPageResponse |
| `admin/src/api/generated/schemas/contentPageUpdate.ts` | 17 | 定义:ContentPageUpdate |
| `admin/src/api/generated/schemas/contentVersionResponse.ts` | 19 | 定义:ContentVersionResponse |
| `admin/src/api/generated/schemas/costByModelApiV1SuperAdminAiCostByModelGetParams.ts` | 15 | 定义:CostByModelApiV1SuperAdminAiCostByModelGetParams |
| `admin/src/api/generated/schemas/costByModelApiV1SuperAdminAiUsageByModelGetParams.ts` | 15 | 定义:CostByModelApiV1SuperAdminAiUsageByModelGetParams |
| `admin/src/api/generated/schemas/costSummaryApiV1SuperAdminAiCostSummaryGetParams.ts` | 15 | 定义:CostSummaryApiV1SuperAdminAiCostSummaryGetParams |
| `admin/src/api/generated/schemas/costSummaryApiV1SuperAdminAiUsageSummaryGetParams.ts` | 15 | 定义:CostSummaryApiV1SuperAdminAiUsageSummaryGetParams |
| `admin/src/api/generated/schemas/createAccountFrontendApiV1SeoMatrixAccountsPostBody.ts` | 9 | 定义:CreateAccountFrontendApiV1SeoMatrixAccountsPostBody |
| `admin/src/api/generated/schemas/createAiConfigApiV1SeoMatrixAiConfigPostBody.ts` | 9 | 定义:CreateAiConfigApiV1SeoMatrixAiConfigPostBody |
| `admin/src/api/generated/schemas/createAiRecommendationApiV1AiRecommendationsPost200.ts` | 9 | 定义:CreateAiRecommendationApiV1AiRecommendationsPost200 |
| `admin/src/api/generated/schemas/createAiRecommendationApiV1AiRecommendationsPostParams.ts` | 15 | 定义:CreateAiRecommendationApiV1AiRecommendationsPostParams |
| `admin/src/api/generated/schemas/createAuditLogApiV1SuperAdminAuditPostBody.ts` | 9 | 定义:CreateAuditLogApiV1SuperAdminAuditPostBody |
| `admin/src/api/generated/schemas/createAuthorApiV1SeoAuthorsPost200.ts` | 9 | 定义:CreateAuthorApiV1SeoAuthorsPost200 |
| `admin/src/api/generated/schemas/createAuthorApiV1SeoAuthorsPostBody.ts` | 9 | 定义:CreateAuthorApiV1SeoAuthorsPostBody |
| `admin/src/api/generated/schemas/createAutoAbTestApiV1AiLearningAutoAbTestPostBody.ts` | 9 | 定义:CreateAutoAbTestApiV1AiLearningAutoAbTestPostBody |
| `admin/src/api/generated/schemas/createChatSessionApiV1ChatSessionsPost200.ts` | 9 | 定义:CreateChatSessionApiV1ChatSessionsPost200 |
| `admin/src/api/generated/schemas/createChatSessionApiV1ChatSessionsPostParams.ts` | 13 | 定义:CreateChatSessionApiV1ChatSessionsPostParams |
| `admin/src/api/generated/schemas/createCombinatorialRuleApiV1SeoMatrixCombinatorialRulesPostBody.ts` | 9 | 定义:CreateCombinatorialRuleApiV1SeoMatrixCombinatorialRulesPostBody |
| `admin/src/api/generated/schemas/createContentTemplateApiV1SeoMatrixContentTemplatesPostBody.ts` | 9 | 定义:CreateContentTemplateApiV1SeoMatrixContentTemplatesPostBody |
| `admin/src/api/generated/schemas/createCustomPlatformApiV1SeoMatrixPlatformsPostBody.ts` | 9 | 定义:CreateCustomPlatformApiV1SeoMatrixPlatformsPostBody |
| `admin/src/api/generated/schemas/createEgressAddonRequest.ts` | 13 | 定义:CreateEgressAddonRequest |
| `admin/src/api/generated/schemas/createGEOInquiryRuleRequest.ts` | 12 | 定义:CreateGEOInquiryRuleRequest |
| `admin/src/api/generated/schemas/createGEORankRuleRequest.ts` | 13 | 定义:CreateGEORankRuleRequest |
| `admin/src/api/generated/schemas/createIndustryKeywordApiV1SeoMatrixIndustryKeywordsPostBody.ts` | 9 | 定义:CreateIndustryKeywordApiV1SeoMatrixIndustryKeywordsPostBody |
| `admin/src/api/generated/schemas/createNativePaymentRequest.ts` | 18 | 定义:CreateNativePaymentRequest |
| `admin/src/api/generated/schemas/createNewsApiV1NewsPostBody.ts` | 9 | 定义:CreateNewsApiV1NewsPostBody |
| `admin/src/api/generated/schemas/createOrderApiV1OrdersPost200.ts` | 9 | 定义:CreateOrderApiV1OrdersPost200 |
| `admin/src/api/generated/schemas/createOrderApiV1OrdersPostParams.ts` | 17 | 定义:CreateOrderApiV1OrdersPostParams |
| `admin/src/api/generated/schemas/createPageVersionApiV1ContentPagesPageIdVersionsPostParams.ts` | 11 | 定义:CreatePageVersionApiV1ContentPagesPageIdVersionsPostParams |
| `admin/src/api/generated/schemas/createPaymentRequest.ts` | 16 | 定义:CreatePaymentRequest |
| `admin/src/api/generated/schemas/createPlatformAccountApiV1SeoMatrixPlatformAccountsPostBody.ts` | 9 | 定义:CreatePlatformAccountApiV1SeoMatrixPlatformAccountsPostBody |
| `admin/src/api/generated/schemas/createProductCategoryApiV1ProductCategoriesPost200.ts` | 9 | 定义:CreateProductCategoryApiV1ProductCategoriesPost200 |
| `admin/src/api/generated/schemas/createProductCategoryApiV1ProductCategoriesPostParams.ts` | 19 | 定义:CreateProductCategoryApiV1ProductCategoriesPostParams |
| `admin/src/api/generated/schemas/createPublishTaskApiV1SeoMatrixPublishPostBody.ts` | 9 | 定义:CreatePublishTaskApiV1SeoMatrixPublishPostBody |
| `admin/src/api/generated/schemas/createQuotationApiV1LogisticsQuotationPostBody.ts` | 9 | 定义:CreateQuotationApiV1LogisticsQuotationPostBody |
| `admin/src/api/generated/schemas/createQuoteApiV1QuotesPost200.ts` | 9 | 定义:CreateQuoteApiV1QuotesPost200 |
| `admin/src/api/generated/schemas/createQuoteApiV1QuotesPostParams.ts` | 17 | 定义:CreateQuoteApiV1QuotesPostParams |
| `admin/src/api/generated/schemas/createSeoMetadataApiV1SeoMetadataPost200.ts` | 9 | 定义:CreateSeoMetadataApiV1SeoMetadataPost200 |
| `admin/src/api/generated/schemas/createSeoMetadataApiV1SeoMetadataPostParams.ts` | 21 | 定义:CreateSeoMetadataApiV1SeoMetadataPostParams |
| `admin/src/api/generated/schemas/createSystemConfigApiV1SystemConfigPost200.ts` | 9 | 定义:CreateSystemConfigApiV1SystemConfigPost200 |
| `admin/src/api/generated/schemas/createSystemConfigApiV1SystemConfigPostParams.ts` | 15 | 定义:CreateSystemConfigApiV1SystemConfigPostParams |
| `admin/src/api/generated/schemas/createTokenPackRequest.ts` | 21 | 定义:CreateTokenPackRequest |
| `admin/src/api/generated/schemas/deleteAuthorApiV1SeoAuthorsAuthorIdDelete200.ts` | 9 | 定义:DeleteAuthorApiV1SeoAuthorsAuthorIdDelete200 |
| `admin/src/api/generated/schemas/deleteCertificationApiV1SeoCertificationsCertIdDelete200.ts` | 9 | 定义:DeleteCertificationApiV1SeoCertificationsCertIdDelete200 |
| `admin/src/api/generated/schemas/deployEdgeNodeApiV1EdgeCdnNodesPostBody.ts` | 9 | 定义:DeployEdgeNodeApiV1EdgeCdnNodesPostBody |
| `admin/src/api/generated/schemas/deviceRegisterRequest.ts` | 18 | 定义:DeviceRegisterRequest |
| `admin/src/api/generated/schemas/diagnosisLeadBody.ts` | 25 | 定义:DiagnosisLeadBody |
| `admin/src/api/generated/schemas/domainBinding.ts` | 14 | 定义:DomainBinding |
| `admin/src/api/generated/schemas/domainBindingResponse.ts` | 17 | 定义:DomainBindingResponse |
| `admin/src/api/generated/schemas/domainListResponse.ts` | 15 | 定义:DomainListResponse · 依赖:./domainBindingResponse.ts |
| `admin/src/api/generated/schemas/egressCreate.ts` | 17 | 定义:EgressCreate |
| `admin/src/api/generated/schemas/egressTenantsApiV1EgressTenantsGetParams.ts` | 11 | 定义:EgressTenantsApiV1EgressTenantsGetParams |
| `admin/src/api/generated/schemas/emailLoginRequest.ts` | 12 | 定义:EmailLoginRequest |
| `admin/src/api/generated/schemas/emailVerificationRequest.ts` | 11 | 定义:EmailVerificationRequest |
| `admin/src/api/generated/schemas/emailVerificationResponse.ts` | 13 | 定义:EmailVerificationResponse |
| `admin/src/api/generated/schemas/enforceTenantExpiryApiV1OpsTenantsEnforceExpiryPostParams.ts` | 11 | 定义:EnforceTenantExpiryApiV1OpsTenantsEnforceExpiryPostParams |
| `admin/src/api/generated/schemas/evaluateContentRequest.ts` | 13 | 定义:EvaluateContentRequest |
| `admin/src/api/generated/schemas/executePublishTaskApiV1PublishTasksApiV1PublishTasksTaskIdExecutePost200.ts` | 9 | 定义:ExecutePublishTaskApiV1PublishTasksApiV1PublishTasksTaskIdExecutePost200 |
| `admin/src/api/generated/schemas/exportAnalyticsApiV1AnalyticsExportGetParams.ts` | 12 | 定义:ExportAnalyticsApiV1AnalyticsExportGetParams |
| `admin/src/api/generated/schemas/exportAssignmentAuditCsvApiV1InquiriesAssignmentAuditExportGetParams.ts` | 30 | 定义:ExportAssignmentAuditCsvApiV1InquiriesAssignmentAuditExportGetParams |
| `admin/src/api/generated/schemas/exportCsvApiV1SuperAdminGeoExportCsvGetParams.ts` | 15 | 定义:ExportCsvApiV1SuperAdminGeoExportCsvGetParams |
| `admin/src/api/generated/schemas/exportCsvApiV1SuperAdminReportsExportCsvGetParams.ts` | 14 | 定义:ExportCsvApiV1SuperAdminReportsExportCsvGetParams |
| `admin/src/api/generated/schemas/exportExcelReportApiV1FinanceExportExcelReportGetParams.ts` | 13 | 定义:ExportExcelReportApiV1FinanceExportExcelReportGetParams |
| `admin/src/api/generated/schemas/exportFinanceCsvApiV1FinanceExportCsvGetParams.ts` | 11 | 定义:ExportFinanceCsvApiV1FinanceExportCsvGetParams |
| `admin/src/api/generated/schemas/exportInquiriesCsvApiV1InquiriesExportGetParams.ts` | 17 | 定义:ExportInquiriesCsvApiV1InquiriesExportGetParams |
| `admin/src/api/generated/schemas/exportLedgerCsvApiV1OpsFinanceExportLedgerCsvGetParams.ts` | 11 | 定义:ExportLedgerCsvApiV1OpsFinanceExportLedgerCsvGetParams |
| `admin/src/api/generated/schemas/exportPdfApiV1SuperAdminGeoExportPdfGetParams.ts` | 11 | 定义:ExportPdfApiV1SuperAdminGeoExportPdfGetParams |
| `admin/src/api/generated/schemas/exportProductsApiV1ProductsExportGetParams.ts` | 11 | 定义:ExportProductsApiV1ProductsExportGetParams |
| `admin/src/api/generated/schemas/exportSeoReportApiV1SeoReportExportGetParams.ts` | 18 | 定义:ExportSeoReportApiV1SeoReportExportGetParams |
| `admin/src/api/generated/schemas/extractParamsRequest.ts` | 11 | 定义:ExtractParamsRequest |
| `admin/src/api/generated/schemas/financeExpiringTenantsApiV1FinanceExpiringTenantsGetParams.ts` | 15 | 定义:FinanceExpiringTenantsApiV1FinanceExpiringTenantsGetParams |
| `admin/src/api/generated/schemas/financeImportCommitBody.ts` | 13 | 定义:FinanceImportCommitBody |
| `admin/src/api/generated/schemas/financeImportValidateBody.ts` | 12 | 定义:FinanceImportValidateBody |
| `admin/src/api/generated/schemas/financeListApplicationsApiV1FinanceInvoiceApplicationsGetParams.ts` | 20 | 定义:FinanceListApplicationsApiV1FinanceInvoiceApplicationsGetParams |
| `admin/src/api/generated/schemas/findMarkersApiV1GeoAnalysisMarkersGeoIdGetParams.ts` | 15 | 定义:FindMarkersApiV1GeoAnalysisMarkersGeoIdGetParams |
| `admin/src/api/generated/schemas/flywheelRunRequest.ts` | 15 | 定义:FlywheelRunRequest |
| `admin/src/api/generated/schemas/generateComplianceReportApiV1ComplianceReportGetParams.ts` | 11 | 定义:GenerateComplianceReportApiV1ComplianceReportGetParams |
| `admin/src/api/generated/schemas/generateContentBody.ts` | 17 | 定义:GenerateContentBody |
| `admin/src/api/generated/schemas/generateContentFrontendApiV1SeoMatrixGeneratePostBody.ts` | 9 | 定义:GenerateContentFrontendApiV1SeoMatrixGeneratePostBody |
| `admin/src/api/generated/schemas/generateKeywordsBody.ts` | 16 | 定义:GenerateKeywordsBody |
| `admin/src/api/generated/schemas/generateRankReportApiV1SuperAdminGeoEngineRankMonitorReportGetParams.ts` | 24 | 定义:GenerateRankReportApiV1SuperAdminGeoEngineRankMonitorReportGetParams |
| `admin/src/api/generated/schemas/generateSchemaRequest.ts` | 18 | 定义:GenerateSchemaRequest · 依赖:./generateSchemaRequestData.ts |
| `admin/src/api/generated/schemas/generateSchemaRequestData.ts` | 9 | 定义:GenerateSchemaRequestData |
| `admin/src/api/generated/schemas/generateVideoBody.ts` | 20 | 定义:GenerateVideoBody |
| `admin/src/api/generated/schemas/geoScoreApiV1SuperAdminGeoEngineScorePostParams.ts` | 11 | 定义:GeoScoreApiV1SuperAdminGeoEngineScorePostParams |
| `admin/src/api/generated/schemas/geoTrendApiV1SuperAdminGeoEngineTrendGetParams.ts` | 16 | 定义:GeoTrendApiV1SuperAdminGeoEngineTrendGetParams |
| `admin/src/api/generated/schemas/getAiUsageDetailApiV1SuperAdminMonitorAiStatsGetParams.ts` | 15 | 定义:GetAiUsageDetailApiV1SuperAdminMonitorAiStatsGetParams |
| `admin/src/api/generated/schemas/getAiUsageLogsApiV1AiUsageLogsGetParams.ts` | 20 | 定义:GetAiUsageLogsApiV1AiUsageLogsGetParams |
| `admin/src/api/generated/schemas/getAlertsApiV1AiUsageAlertsGetParams.ts` | 16 | 定义:GetAlertsApiV1AiUsageAlertsGetParams |
| `admin/src/api/generated/schemas/getAllLevelsSummaryApiV1AgentTreeAllLevelsGetParams.ts` | 14 | 定义:GetAllLevelsSummaryApiV1AgentTreeAllLevelsGetParams |
| `admin/src/api/generated/schemas/getAuditLogsApiV1SystemAuditLogsGetParams.ts` | 24 | 定义:GetAuditLogsApiV1SystemAuditLogsGetParams |
| `admin/src/api/generated/schemas/getAuthorApiV1SeoAuthorsAuthorIdGet200.ts` | 9 | 定义:GetAuthorApiV1SeoAuthorsAuthorIdGet200 |
| `admin/src/api/generated/schemas/getAuthorsApiV1SeoAuthorsGet200.ts` | 9 | 定义:GetAuthorsApiV1SeoAuthorsGet200 |
| `admin/src/api/generated/schemas/getAuthorsApiV1SeoAuthorsGetParams.ts` | 13 | 定义:GetAuthorsApiV1SeoAuthorsGetParams |
| `admin/src/api/generated/schemas/getBehaviorAnalysisApiV1AiLearningBehaviorGetParams.ts` | 11 | 定义:GetBehaviorAnalysisApiV1AiLearningBehaviorGetParams |
| `admin/src/api/generated/schemas/getBoxplotApiV1GeoVisualizationBoxplotGeoIdGetParams.ts` | 15 | 定义:GetBoxplotApiV1GeoVisualizationBoxplotGeoIdGetParams |
| `admin/src/api/generated/schemas/getChainUpApiV1AgentTreeChainGetParams.ts` | 14 | 定义:GetChainUpApiV1AgentTreeChainGetParams |
| `admin/src/api/generated/schemas/getChatSessionApiV1ChatSessionsSessionIdGet200.ts` | 9 | 定义:GetChatSessionApiV1ChatSessionsSessionIdGet200 |
| `admin/src/api/generated/schemas/getChildrenApiV1AgentTreeChildrenGetParams.ts` | 14 | 定义:GetChildrenApiV1AgentTreeChildrenGetParams |
| `admin/src/api/generated/schemas/getContentTrustSignalsApiV1SeoContentContentIdTrustSignalsGet200.ts` | 9 | 定义:GetContentTrustSignalsApiV1SeoContentContentIdTrustSignalsGet200 |
| `admin/src/api/generated/schemas/getDailyReportHistoryApiV1DailyReportHistoryGetParams.ts` | 14 | 定义:GetDailyReportHistoryApiV1DailyReportHistoryGetParams |
| `admin/src/api/generated/schemas/getDailyUsageApiV1AiUsageDailyGetParams.ts` | 15 | 定义:GetDailyUsageApiV1AiUsageDailyGetParams |
| `admin/src/api/generated/schemas/getEdgeNodesApiV1EdgeCdnNodesGetParams.ts` | 12 | 定义:GetEdgeNodesApiV1EdgeCdnNodesGetParams |
| `admin/src/api/generated/schemas/getEeatScoreApiV1SeoScoreContentIdGet200.ts` | 9 | 定义:GetEeatScoreApiV1SeoScoreContentIdGet200 |
| `admin/src/api/generated/schemas/getEeatScoresApiV1SeoScoresGet200.ts` | 9 | 定义:GetEeatScoresApiV1SeoScoresGet200 |
| `admin/src/api/generated/schemas/getEeatScoresApiV1SeoScoresGetParams.ts` | 13 | 定义:GetEeatScoresApiV1SeoScoresGetParams |
| `admin/src/api/generated/schemas/getExecutionReviewApiV1AgentHubExecutionReviewGetParams.ts` | 12 | 定义:GetExecutionReviewApiV1AgentHubExecutionReviewGetParams |
| `admin/src/api/generated/schemas/getFreightCalculationApiV1LogisticsFreightCalcGetParams.ts` | 13 | 定义:GetFreightCalculationApiV1LogisticsFreightCalcGetParams |
| `admin/src/api/generated/schemas/getGenerateHistoryApiV1SuperAdminGeoEngineGenerateHistoryGetParams.ts` | 24 | 定义:GetGenerateHistoryApiV1SuperAdminGeoEngineGenerateHistoryGetParams |
| `admin/src/api/generated/schemas/getHistoryApiV1SuperAdminGeoEngineHistoryGetParams.ts` | 16 | 定义:GetHistoryApiV1SuperAdminGeoEngineHistoryGetParams |
| `admin/src/api/generated/schemas/getImChannelByCountryApiV1ImRoutingChannelCountryCodeGetParams.ts` | 14 | 定义:GetImChannelByCountryApiV1ImRoutingChannelCountryCodeGetParams |
| `admin/src/api/generated/schemas/getIndexCountApiV1BaiduIndexCountGetParams.ts` | 18 | 定义:GetIndexCountApiV1BaiduIndexCountGetParams |
| `admin/src/api/generated/schemas/getKeywordHistoryApiV1SeoKeywordsKeywordIdHistoryGetParams.ts` | 15 | 定义:GetKeywordHistoryApiV1SeoKeywordsKeywordIdHistoryGetParams |
| `admin/src/api/generated/schemas/getKeywordsApiV1SeoComplianceKeywordsGetParams.ts` | 12 | 定义:GetKeywordsApiV1SeoComplianceKeywordsGetParams |
| `admin/src/api/generated/schemas/getLbsRoutingApiV1LogisticsLbsRoutingGetParams.ts` | 13 | 定义:GetLbsRoutingApiV1LogisticsLbsRoutingGetParams |
| `admin/src/api/generated/schemas/getLeaderboardApiV1ReferralLeaderboardGetParams.ts` | 14 | 定义:GetLeaderboardApiV1ReferralLeaderboardGetParams |
| `admin/src/api/generated/schemas/getMenuRoutesApiV1AdminBffMenuRoutesGetParams.ts` | 14 | 定义:GetMenuRoutesApiV1AdminBffMenuRoutesGetParams |
| `admin/src/api/generated/schemas/getMessageLogsApiV1FeishuLogsGetParams.ts` | 12 | 定义:GetMessageLogsApiV1FeishuLogsGetParams |
| `admin/src/api/generated/schemas/getMessagesApiV1ChatChatMessagesPartnerIdGetParams.ts` | 12 | 定义:GetMessagesApiV1ChatChatMessagesPartnerIdGetParams |
| `admin/src/api/generated/schemas/getMyTokenLedgerApiV1TokenMyLedgerGetParams.ts` | 19 | 定义:GetMyTokenLedgerApiV1TokenMyLedgerGetParams |
| `admin/src/api/generated/schemas/getNurtureRulesApiV1SocialNurtureRulesGetParams.ts` | 12 | 定义:GetNurtureRulesApiV1SocialNurtureRulesGetParams |
| `admin/src/api/generated/schemas/getNvidiaScenarioHealthApiV1SuperAdminAiConfigNvidiaScenariosHealthGetParams.ts` | 11 | 定义:GetNvidiaScenarioHealthApiV1SuperAdminAiConfigNvidiaScenariosHealthGetParams |
| `admin/src/api/generated/schemas/getOperationLogsApiV1UsersLogsGetParams.ts` | 14 | 定义:GetOperationLogsApiV1UsersLogsGetParams |
| `admin/src/api/generated/schemas/getOrderApiV1OrdersOrderIdGet200.ts` | 9 | 定义:GetOrderApiV1OrdersOrderIdGet200 |
| `admin/src/api/generated/schemas/getPerformanceMetricsApiV1SystemPerformanceMetricsGetParams.ts` | 11 | 定义:GetPerformanceMetricsApiV1SystemPerformanceMetricsGetParams |
| `admin/src/api/generated/schemas/getPerformanceReportApiV1SystemPerformanceReportGetParams.ts` | 11 | 定义:GetPerformanceReportApiV1SystemPerformanceReportGetParams |
| `admin/src/api/generated/schemas/getPluginMarketApiV1DeveloperPluginsGetParams.ts` | 12 | 定义:GetPluginMarketApiV1DeveloperPluginsGetParams |
| `admin/src/api/generated/schemas/getPopularProductsApiV1ProductsPopularGetParams.ts` | 11 | 定义:GetPopularProductsApiV1ProductsPopularGetParams |
| `admin/src/api/generated/schemas/getProductCategoryApiV1ProductCategoriesCategoryIdGet200.ts` | 9 | 定义:GetProductCategoryApiV1ProductCategoriesCategoryIdGet200 |
| `admin/src/api/generated/schemas/getProductImageApiV1ProductImagesImageIdGet200.ts` | 9 | 定义:GetProductImageApiV1ProductImagesImageIdGet200 |
| `admin/src/api/generated/schemas/getProductReviewsApiV1ReviewsProductsProductIdReviewsGetParams.ts` | 25 | 定义:GetProductReviewsApiV1ReviewsProductsProductIdReviewsGetParams |
| `admin/src/api/generated/schemas/getPublishDashboardApiV1UnifiedPublishDashboardGetParams.ts` | 11 | 定义:GetPublishDashboardApiV1UnifiedPublishDashboardGetParams |
| `admin/src/api/generated/schemas/getQueueStatsApiV1PublishTasksApiV1PublishTasksQueueStatsGet200.ts` | 9 | 定义:GetQueueStatsApiV1PublishTasksApiV1PublishTasksQueueStatsGet200 |
| `admin/src/api/generated/schemas/getQuotationsApiV1LogisticsQuotationGetParams.ts` | 12 | 定义:GetQuotationsApiV1LogisticsQuotationGetParams |
| `admin/src/api/generated/schemas/getQuoteApiV1QuotesQuoteIdGet200.ts` | 9 | 定义:GetQuoteApiV1QuotesQuoteIdGet200 |
| `admin/src/api/generated/schemas/getRankTrendApiV1SuperAdminGeoEngineRankMonitorTrendGetParams.ts` | 24 | 定义:GetRankTrendApiV1SuperAdminGeoEngineRankMonitorTrendGetParams |
| `admin/src/api/generated/schemas/getRecommendationApiV1AiRecommendationsRecommendationIdGet200.ts` | 9 | 定义:GetRecommendationApiV1AiRecommendationsRecommendationIdGet200 |
| `admin/src/api/generated/schemas/getRecommendationsForUserApiV1AiRecommendationsForUserUserIdGet200Item.ts` | 9 | 定义:GetRecommendationsForUserApiV1AiRecommendationsForUserUserIdGet200Item |
| `admin/src/api/generated/schemas/getRecommendationsForUserApiV1AiRecommendationsForUserUserIdGetParams.ts` | 20 | 定义:GetRecommendationsForUserApiV1AiRecommendationsForUserUserIdGetParams |
| `admin/src/api/generated/schemas/getReferralRecordsApiV1ReferralRecordsGetParams.ts` | 12 | 定义:GetReferralRecordsApiV1ReferralRecordsGetParams |
| `admin/src/api/generated/schemas/getRenderQueueApiV1MediaFactoryRenderQueueGetParams.ts` | 12 | 定义:GetRenderQueueApiV1MediaFactoryRenderQueueGetParams |
| `admin/src/api/generated/schemas/getReviewStatsApiV1ReviewsStatsGetParams.ts` | 14 | 定义:GetReviewStatsApiV1ReviewsStatsGetParams |
| `admin/src/api/generated/schemas/getReviewsApiV1ReviewsGetParams.ts` | 41 | 定义:GetReviewsApiV1ReviewsGetParams |
| `admin/src/api/generated/schemas/getScanHistoryApiV1SeoComplianceScanHistoryGetParams.ts` | 12 | 定义:GetScanHistoryApiV1SeoComplianceScanHistoryGetParams |
| `admin/src/api/generated/schemas/getSearchQueriesApiV1BaiduSearchQueriesGetParams.ts` | 24 | 定义:GetSearchQueriesApiV1BaiduSearchQueriesGetParams |
| `admin/src/api/generated/schemas/getSecurityIssuesApiV1SystemPerformanceSecurityIssuesGetParams.ts` | 12 | 定义:GetSecurityIssuesApiV1SystemPerformanceSecurityIssuesGetParams |
| `admin/src/api/generated/schemas/getSeoBatchListApiV1SeoSeoBatchListGetParams.ts` | 11 | 定义:GetSeoBatchListApiV1SeoSeoBatchListGetParams |
| `admin/src/api/generated/schemas/getSeoByEntityApiV1SeoMetadataByEntityGet200.ts` | 9 | 定义:GetSeoByEntityApiV1SeoMetadataByEntityGet200 |
| `admin/src/api/generated/schemas/getSeoByEntityApiV1SeoMetadataByEntityGetParams.ts` | 12 | 定义:GetSeoByEntityApiV1SeoMetadataByEntityGetParams |
| `admin/src/api/generated/schemas/getSeoDashboardApiV1SeoDashboardGetParams.ts` | 11 | 定义:GetSeoDashboardApiV1SeoDashboardGetParams |
| `admin/src/api/generated/schemas/getSeoMetadataApiV1SeoMetadataSeoIdGet200.ts` | 9 | 定义:GetSeoMetadataApiV1SeoMetadataSeoIdGet200 |
| `admin/src/api/generated/schemas/getSeoPagesApiV1SeoPagesGetParams.ts` | 13 | 定义:GetSeoPagesApiV1SeoPagesGetParams |
| `admin/src/api/generated/schemas/getSessionMessagesApiV1ChatSessionsSessionIdMessagesGet200Item.ts` | 9 | 定义:GetSessionMessagesApiV1ChatSessionsSessionIdMessagesGet200Item |
| `admin/src/api/generated/schemas/getSessionMessagesApiV1ChatSessionsSessionIdMessagesGetParams.ts` | 19 | 定义:GetSessionMessagesApiV1ChatSessionsSessionIdMessagesGetParams |
| `admin/src/api/generated/schemas/getSubtreeStatsApiV1AgentTreeStatsGetParams.ts` | 14 | 定义:GetSubtreeStatsApiV1AgentTreeStatsGetParams |
| `admin/src/api/generated/schemas/getSystemConfigApiV1SystemConfigConfigIdGet200.ts` | 9 | 定义:GetSystemConfigApiV1SystemConfigConfigIdGet200 |
| `admin/src/api/generated/schemas/getSystemConfigByKeyApiV1SystemConfigByKeyKeyGet200.ts` | 9 | 定义:GetSystemConfigByKeyApiV1SystemConfigByKeyKeyGet200 |
| `admin/src/api/generated/schemas/getSystemLogsApiV1SystemLogsGetParams.ts` | 13 | 定义:GetSystemLogsApiV1SystemLogsGetParams |
| `admin/src/api/generated/schemas/getTenantInvoicesApiV1TenantsTenantIdInvoicesGetParams.ts` | 12 | 定义:GetTenantInvoicesApiV1TenantsTenantIdInvoicesGetParams |
| `admin/src/api/generated/schemas/getTenantsOverviewApiV1TenantsGetParams.ts` | 15 | 定义:GetTenantsOverviewApiV1TenantsGetParams |
| `admin/src/api/generated/schemas/getTrafficBoardApiV1AnalyticsTrafficBoardGetParams.ts` | 18 | 定义:GetTrafficBoardApiV1AnalyticsTrafficBoardGetParams |
| `admin/src/api/generated/schemas/getTrafficDataApiV1AnalyticsTrafficGetParams.ts` | 11 | 定义:GetTrafficDataApiV1AnalyticsTrafficGetParams |
| `admin/src/api/generated/schemas/getTrafficStatsApiV1SuperAdminV2rayTrackerTrafficGetParams.ts` | 11 | 定义:GetTrafficStatsApiV1SuperAdminV2rayTrackerTrafficGetParams |
| `admin/src/api/generated/schemas/getTrustSignalsApiV1SeoTrustSignalsGet200.ts` | 9 | 定义:GetTrustSignalsApiV1SeoTrustSignalsGet200 |
| `admin/src/api/generated/schemas/globalSearchApiV1SuperAdminSearchGetParams.ts` | 14 | 定义:GlobalSearchApiV1SuperAdminSearchGetParams |
| `admin/src/api/generated/schemas/glossaryTermCreate.ts` | 43 | 定义:GlossaryTermCreate |
| `admin/src/api/generated/schemas/glossaryTermUpdate.ts` | 44 | 定义:GlossaryTermUpdate |
| `admin/src/api/generated/schemas/hTTPValidationError.ts` | 12 | 定义:HTTPValidationError · 依赖:./validationError.ts |
| `admin/src/api/generated/schemas/handoffBody.ts` | 12 | 定义:HandoffBody |
| `admin/src/api/generated/schemas/heatmapDataApiV1SuperAdminGeoVisualizationHeatmapGetParams.ts` | 16 | 定义:HeatmapDataApiV1SuperAdminGeoVisualizationHeatmapGetParams |
| `admin/src/api/generated/schemas/hermesOpsDeerflowJobsApiV1HermesOpsDeerflowJobsGetParams.ts` | 21 | 定义:HermesOpsDeerflowJobsApiV1HermesOpsDeerflowJobsGetParams |
| `admin/src/api/generated/schemas/hermesOpsInclusionRecheckApiV1HermesOpsInclusionRecheckPostParams.ts` | 15 | 定义:HermesOpsInclusionRecheckApiV1HermesOpsInclusionRecheckPostParams |
| `admin/src/api/generated/schemas/hermesOpsMem0SyncApiV1HermesOpsIntegrationsMem0SyncPostParams.ts` | 15 | 定义:HermesOpsMem0SyncApiV1HermesOpsIntegrationsMem0SyncPostParams |
| `admin/src/api/generated/schemas/hermesOpsPublishHistoryApiV1HermesOpsPublishHistoryGetParams.ts` | 15 | 定义:HermesOpsPublishHistoryApiV1HermesOpsPublishHistoryGetParams |
| `admin/src/api/generated/schemas/hermesOpsTechRadarReportsApiV1HermesOpsTechRadarReportsGetParams.ts` | 15 | 定义:HermesOpsTechRadarReportsApiV1HermesOpsTechRadarReportsGetParams |
| `admin/src/api/generated/schemas/hermesPluginCatalogApiV1HermesPluginsCatalogGetParams.ts` | 14 | 定义:HermesPluginCatalogApiV1HermesPluginsCatalogGetParams |
| `admin/src/api/generated/schemas/hubSearchConsolePingApiV1HubSearchConsolePingPostParams.ts` | 14 | 定义:HubSearchConsolePingApiV1HubSearchConsolePingPostParams |
| `admin/src/api/generated/schemas/iMChannelResponse.ts` | 18 | 定义:IMChannelResponse |
| `admin/src/api/generated/schemas/index.ts` | 738 | 依赖:./aBTestConversionResponse.ts,./aBTestConversionResponseConversionData.ts,./aBTestCreate.ts,./aBTestCreateVariantsConfig.ts,./aBTestDetailResponse.ts · ⚑MOCK |
| `admin/src/api/generated/schemas/inquiryAssignRequest.ts` | 15 | 定义:InquiryAssignRequest |
| `admin/src/api/generated/schemas/inquiryAssignmentHistoryApiV1InquiriesInquiryIdAssignmentHistoryGetParams.ts` | 15 | 定义:InquiryAssignmentHistoryApiV1InquiriesInquiryIdAssignmentHistoryGetParams |
| `admin/src/api/generated/schemas/inquiryCreate.ts` | 16 | 定义:InquiryCreate |
| `admin/src/api/generated/schemas/inquiryStatusUpdate.ts` | 15 | 定义:InquiryStatusUpdate |
| `admin/src/api/generated/schemas/inquiryUpdate.ts` | 18 | 定义:InquiryUpdate |
| `admin/src/api/generated/schemas/installBody.ts` | 11 | 定义:InstallBody |
| `admin/src/api/generated/schemas/internationalInquiryUpdate.ts` | 15 | 定义:InternationalInquiryUpdate |
| `admin/src/api/generated/schemas/internationalTargetSiteCreate.ts` | 15 | 定义:InternationalTargetSiteCreate |
| `admin/src/api/generated/schemas/internationalTargetSiteUpdate.ts` | 16 | 定义:InternationalTargetSiteUpdate |
| `admin/src/api/generated/schemas/invoiceApplicationCreate.ts` | 30 | 定义:InvoiceApplicationCreate |
| `admin/src/api/generated/schemas/keywordCreate.ts` | 31 | 定义:KeywordCreate |
| `admin/src/api/generated/schemas/keywordResponse.ts` | 29 | 定义:KeywordResponse |
| `admin/src/api/generated/schemas/keywordUpdate.ts` | 20 | 定义:KeywordUpdate |
| `admin/src/api/generated/schemas/ledgerCreate.ts` | 18 | 定义:LedgerCreate |
| `admin/src/api/generated/schemas/listAbTestsApiV1AbTestGetParams.ts` | 13 | 定义:ListAbTestsApiV1AbTestGetParams |
| `admin/src/api/generated/schemas/listAccountsApiV1PlatformsAccountsGetParams.ts` | 11 | 定义:ListAccountsApiV1PlatformsAccountsGetParams |
| `admin/src/api/generated/schemas/listAdminUsersApiV1SuperAdminUsersGetParams.ts` | 21 | 定义:ListAdminUsersApiV1SuperAdminUsersGetParams |
| `admin/src/api/generated/schemas/listAlertRulesApiV1SuperAdminGeoEngineAlertsRulesGetParams.ts` | 14 | 定义:ListAlertRulesApiV1SuperAdminGeoEngineAlertsRulesGetParams |
| `admin/src/api/generated/schemas/listAlertsApiV1SuperAdminGeoEngineAlertsGetParams.ts` | 33 | 定义:ListAlertsApiV1SuperAdminGeoEngineAlertsGetParams |
| `admin/src/api/generated/schemas/listArticlesApiV1BuildingWikiArticlesGetParams.ts` | 20 | 定义:ListArticlesApiV1BuildingWikiArticlesGetParams |
| `admin/src/api/generated/schemas/listAssignmentAuditApiV1InquiriesAssignmentAuditGetParams.ts` | 39 | 定义:ListAssignmentAuditApiV1InquiriesAssignmentAuditGetParams |
| `admin/src/api/generated/schemas/listAuditLogsApiV1SuperAdminAuditGetParams.ts` | 24 | 定义:ListAuditLogsApiV1SuperAdminAuditGetParams |
| `admin/src/api/generated/schemas/listAuditsApiV1SeoSiteAuditGetParams.ts` | 12 | 定义:ListAuditsApiV1SeoSiteAuditGetParams |
| `admin/src/api/generated/schemas/listCacheKeysApiV1SuperAdminMonitorCacheKeysGetParams.ts` | 11 | 定义:ListCacheKeysApiV1SuperAdminMonitorCacheKeysGetParams |
| `admin/src/api/generated/schemas/listCaseStudiesApiV1CaseStudiesGetParams.ts` | 14 | 定义:ListCaseStudiesApiV1CaseStudiesGetParams |
| `admin/src/api/generated/schemas/listCommissionsApiV1FinanceCommissionsGetParams.ts` | 21 | 定义:ListCommissionsApiV1FinanceCommissionsGetParams |
| `admin/src/api/generated/schemas/listComplianceIssuesApiV1ComplianceIssuesGetParams.ts` | 13 | 定义:ListComplianceIssuesApiV1ComplianceIssuesGetParams |
| `admin/src/api/generated/schemas/listContentMastersApiV1ContentMastersGetParams.ts` | 20 | 定义:ListContentMastersApiV1ContentMastersGetParams |
| `admin/src/api/generated/schemas/listContentTemplatesApiV1SeoMatrixContentTemplatesGetParams.ts` | 11 | 定义:ListContentTemplatesApiV1SeoMatrixContentTemplatesGetParams |
| `admin/src/api/generated/schemas/listConversionsApiV1AbTestTestIdConversionsGetParams.ts` | 13 | 定义:ListConversionsApiV1AbTestTestIdConversionsGetParams |
| `admin/src/api/generated/schemas/listCrawlLogsApiV1InternationalLogsGetParams.ts` | 13 | 定义:ListCrawlLogsApiV1InternationalLogsGetParams |
| `admin/src/api/generated/schemas/listDraftsFrontendApiV1SeoMatrixDraftsGetParams.ts` | 12 | 定义:ListDraftsFrontendApiV1SeoMatrixDraftsGetParams |
| `admin/src/api/generated/schemas/listEndpointsApiV1EgressEndpointsGetParams.ts` | 12 | 定义:ListEndpointsApiV1EgressEndpointsGetParams |
| `admin/src/api/generated/schemas/listEventsApiV1AbTestTestIdEventsGetParams.ts` | 13 | 定义:ListEventsApiV1AbTestTestIdEventsGetParams |
| `admin/src/api/generated/schemas/listEventsApiV1SuperAdminAlertsEventsGetParams.ts` | 21 | 定义:ListEventsApiV1SuperAdminAlertsEventsGetParams |
| `admin/src/api/generated/schemas/listFilesApiV1FilesFilesGetParams.ts` | 27 | 定义:ListFilesApiV1FilesFilesGetParams |
| `admin/src/api/generated/schemas/listGeneratedContentsApiV1SeoMatrixGeneratedContentsGetParams.ts` | 15 | 定义:ListGeneratedContentsApiV1SeoMatrixGeneratedContentsGetParams |
| `admin/src/api/generated/schemas/listGeneratedKeywordsApiV1SeoMatrixGeneratedKeywordsGetParams.ts` | 15 | 定义:ListGeneratedKeywordsApiV1SeoMatrixGeneratedKeywordsGetParams |
| `admin/src/api/generated/schemas/listGlossaryApiV1GlobalizationGlossaryGetParams.ts` | 15 | 定义:ListGlossaryApiV1GlobalizationGlossaryGetParams |
| `admin/src/api/generated/schemas/listImRoutingsApiV1ImRoutingGetParams.ts` | 18 | 定义:ListImRoutingsApiV1ImRoutingGetParams |
| `admin/src/api/generated/schemas/listInclusionStatusApiV1SeoMatrixInclusionStatusGetParams.ts` | 19 | 定义:ListInclusionStatusApiV1SeoMatrixInclusionStatusGetParams |
| `admin/src/api/generated/schemas/listIndustryKeywordsApiV1SeoMatrixIndustryKeywordsGetParams.ts` | 13 | 定义:ListIndustryKeywordsApiV1SeoMatrixIndustryKeywordsGetParams |
| `admin/src/api/generated/schemas/listInquiriesApiV1InquiriesGetParams.ts` | 18 | 定义:ListInquiriesApiV1InquiriesGetParams |
| `admin/src/api/generated/schemas/listInquiriesApiV1InternationalInquiriesGetParams.ts` | 17 | 定义:ListInquiriesApiV1InternationalInquiriesGetParams |
| `admin/src/api/generated/schemas/listInquiriesUnifiedApiV1InquiriesUnifiedGetParams.ts` | 25 | 定义:ListInquiriesUnifiedApiV1InquiriesUnifiedGetParams |
| `admin/src/api/generated/schemas/listInquiriesV2CompatApiV1InquiriesV2GetParams.ts` | 31 | 定义:ListInquiriesV2CompatApiV1InquiriesV2GetParams |
| `admin/src/api/generated/schemas/listKeywordsApiV1SeoKeywordsGetParams.ts` | 22 | 定义:ListKeywordsApiV1SeoKeywordsGetParams |
| `admin/src/api/generated/schemas/listLedgerApiV1FinanceLedgerGetParams.ts` | 22 | 定义:ListLedgerApiV1FinanceLedgerGetParams |
| `admin/src/api/generated/schemas/listLoginLogsApiV1SuperAdminUsersLoginLogsGetParams.ts` | 20 | 定义:ListLoginLogsApiV1SuperAdminUsersLoginLogsGetParams |
| `admin/src/api/generated/schemas/listModelsApiV1SuperAdminAiConfigModelsGetParams.ts` | 15 | 定义:ListModelsApiV1SuperAdminAiConfigModelsGetParams |
| `admin/src/api/generated/schemas/listMyTenantInvoicesApiV1TenantsInvoicesGetParams.ts` | 13 | 定义:ListMyTenantInvoicesApiV1TenantsInvoicesGetParams |
| `admin/src/api/generated/schemas/listNewsApiV1NewsGetParams.ts` | 14 | 定义:ListNewsApiV1NewsGetParams |
| `admin/src/api/generated/schemas/listNotificationsApiV1NotificationsGetParams.ts` | 13 | 定义:ListNotificationsApiV1NotificationsGetParams |
| `admin/src/api/generated/schemas/listNurtureCyclesApiV1SocialNurtureCyclesGetParams.ts` | 11 | 定义:ListNurtureCyclesApiV1SocialNurtureCyclesGetParams |
| `admin/src/api/generated/schemas/listOrdersApiV1OrdersGet200Item.ts` | 9 | 定义:ListOrdersApiV1OrdersGet200Item |
| `admin/src/api/generated/schemas/listOrdersApiV1OrdersGetParams.ts` | 22 | 定义:ListOrdersApiV1OrdersGetParams |
| `admin/src/api/generated/schemas/listPagesApiV1ContentPagesGetParams.ts` | 15 | 定义:ListPagesApiV1ContentPagesGetParams |
| `admin/src/api/generated/schemas/listPaymentOrdersApiV1PaymentOrdersGetParams.ts` | 14 | 定义:ListPaymentOrdersApiV1PaymentOrdersGetParams |
| `admin/src/api/generated/schemas/listPipelinesApiV1UbrainCommercialOsPipelinesGetParams.ts` | 15 | 定义:ListPipelinesApiV1UbrainCommercialOsPipelinesGetParams |
| `admin/src/api/generated/schemas/listPlatformAccountsApiV1SeoMatrixPlatformAccountsGetParams.ts` | 11 | 定义:ListPlatformAccountsApiV1SeoMatrixPlatformAccountsGetParams |
| `admin/src/api/generated/schemas/listPlatformOriginsApiV1SuperAdminPlatformOriginsGetParams.ts` | 22 | 定义:ListPlatformOriginsApiV1SuperAdminPlatformOriginsGetParams |
| `admin/src/api/generated/schemas/listProductCategoriesApiV1ProductCategoriesGet200Item.ts` | 9 | 定义:ListProductCategoriesApiV1ProductCategoriesGet200Item |
| `admin/src/api/generated/schemas/listProductCategoriesApiV1ProductCategoriesGetParams.ts` | 21 | 定义:ListProductCategoriesApiV1ProductCategoriesGetParams |
| `admin/src/api/generated/schemas/listProductImagesApiV1ProductImagesByProductProductIdGet200Item.ts` | 9 | 定义:ListProductImagesApiV1ProductImagesByProductProductIdGet200Item |
| `admin/src/api/generated/schemas/listProductsApiV1ProductsGetParams.ts` | 15 | 定义:ListProductsApiV1ProductsGetParams |
| `admin/src/api/generated/schemas/listProfilesApiV1EgressProfilesGetParams.ts` | 11 | 定义:ListProfilesApiV1EgressProfilesGetParams |
| `admin/src/api/generated/schemas/listPublishHistoryFrontendApiV1SeoMatrixPublishHistoryGetParams.ts` | 12 | 定义:ListPublishHistoryFrontendApiV1SeoMatrixPublishHistoryGetParams |
| `admin/src/api/generated/schemas/listPublishLogsApiV1PlatformsPublishLogsGetParams.ts` | 21 | 定义:ListPublishLogsApiV1PlatformsPublishLogsGetParams |
| `admin/src/api/generated/schemas/listPublishLogsApiV1SeoMatrixPublishLogsGetParams.ts` | 14 | 定义:ListPublishLogsApiV1SeoMatrixPublishLogsGetParams |
| `admin/src/api/generated/schemas/listPublishTasksApiV1PlatformsPublishTasksGetParams.ts` | 23 | 定义:ListPublishTasksApiV1PlatformsPublishTasksGetParams |
| `admin/src/api/generated/schemas/listPublishTasksApiV1PublishTasksApiV1PublishTasksGetParams.ts` | 22 | 定义:ListPublishTasksApiV1PublishTasksApiV1PublishTasksGetParams |
| `admin/src/api/generated/schemas/listPublishTasksApiV1SeoMatrixPublishTasksGetParams.ts` | 15 | 定义:ListPublishTasksApiV1SeoMatrixPublishTasksGetParams |
| `admin/src/api/generated/schemas/listPublishTasksApiV1UnifiedPublishTasksGetParams.ts` | 22 | 定义:ListPublishTasksApiV1UnifiedPublishTasksGetParams |
| `admin/src/api/generated/schemas/listQuotesApiV1QuotesGet200Item.ts` | 9 | 定义:ListQuotesApiV1QuotesGet200Item |
| `admin/src/api/generated/schemas/listQuotesApiV1QuotesGetParams.ts` | 21 | 定义:ListQuotesApiV1QuotesGetParams |
| `admin/src/api/generated/schemas/listRecommendationsApiV1AiRecommendationsGet200Item.ts` | 9 | 定义:ListRecommendationsApiV1AiRecommendationsGet200Item |
| `admin/src/api/generated/schemas/listRecommendationsApiV1AiRecommendationsGetParams.ts` | 22 | 定义:ListRecommendationsApiV1AiRecommendationsGetParams |
| `admin/src/api/generated/schemas/listRecordsApiV1GlobalizationRecordsGetParams.ts` | 12 | 定义:ListRecordsApiV1GlobalizationRecordsGetParams |
| `admin/src/api/generated/schemas/listRegionKeywordsApiV1SeoMatrixRegionKeywordsGetParams.ts` | 16 | 定义:ListRegionKeywordsApiV1SeoMatrixRegionKeywordsGetParams |
| `admin/src/api/generated/schemas/listResearchInsightsApiV1UbrainCommercialOsInsightsGetParams.ts` | 17 | 定义:ListResearchInsightsApiV1UbrainCommercialOsInsightsGetParams |
| `admin/src/api/generated/schemas/listRulesApiV1TradeIntelRulesGetParams.ts` | 11 | 定义:ListRulesApiV1TradeIntelRulesGetParams |
| `admin/src/api/generated/schemas/listSeoMetadataApiV1SeoMetadataGet200Item.ts` | 9 | 定义:ListSeoMetadataApiV1SeoMetadataGet200Item |
| `admin/src/api/generated/schemas/listSeoMetadataApiV1SeoMetadataGetParams.ts` | 20 | 定义:ListSeoMetadataApiV1SeoMetadataGetParams |
| `admin/src/api/generated/schemas/listSitesApiV1InternationalSitesGetParams.ts` | 13 | 定义:ListSitesApiV1InternationalSitesGetParams |
| `admin/src/api/generated/schemas/listSslCertificatesApiV1SslCertificatesApiV1SslCertificatesGetParams.ts` | 21 | 定义:ListSslCertificatesApiV1SslCertificatesApiV1SslCertificatesGetParams |
| `admin/src/api/generated/schemas/listSystemConfigsApiV1SystemConfigGet200Item.ts` | 9 | 定义:ListSystemConfigsApiV1SystemConfigGet200Item |
| `admin/src/api/generated/schemas/listSystemConfigsApiV1SystemConfigGetParams.ts` | 20 | 定义:ListSystemConfigsApiV1SystemConfigGetParams |
| `admin/src/api/generated/schemas/listTasksApiV1GlobalizationTasksGetParams.ts` | 12 | 定义:ListTasksApiV1GlobalizationTasksGetParams |
| `admin/src/api/generated/schemas/listTemplatesApiV1AiTemplatesAiTemplatesGetParams.ts` | 20 | 定义:ListTemplatesApiV1AiTemplatesAiTemplatesGetParams |
| `admin/src/api/generated/schemas/listTenantsApiV1SuperAdminTenantsGetParams.ts` | 20 | 定义:ListTenantsApiV1SuperAdminTenantsGetParams |
| `admin/src/api/generated/schemas/listTokenLedgerApiV1TokenLedgerGetParams.ts` | 20 | 定义:ListTokenLedgerApiV1TokenLedgerGetParams |
| `admin/src/api/generated/schemas/listUserChatSessionsApiV1ChatSessionsByUserUserIdGet200Item.ts` | 9 | 定义:ListUserChatSessionsApiV1ChatSessionsByUserUserIdGet200Item |
| `admin/src/api/generated/schemas/listUserChatSessionsApiV1ChatSessionsByUserUserIdGetParams.ts` | 20 | 定义:ListUserChatSessionsApiV1ChatSessionsByUserUserIdGetParams |
| `admin/src/api/generated/schemas/listUsersApiV1UsersGetParams.ts` | 14 | 定义:ListUsersApiV1UsersGetParams |
| `admin/src/api/generated/schemas/listViolationsApiV1SeoComplianceViolationsGetParams.ts` | 13 | 定义:ListViolationsApiV1SeoComplianceViolationsGetParams |
| `admin/src/api/generated/schemas/llmsConfigCreate.ts` | 12 | 定义:LlmsConfigCreate |
| `admin/src/api/generated/schemas/llmsConfigResponse.ts` | 16 | 定义:LlmsConfigResponse |
| `admin/src/api/generated/schemas/llmsConfigUpdate.ts` | 13 | 定义:LlmsConfigUpdate |
| `admin/src/api/generated/schemas/logoutResponse.ts` | 11 | 定义:LogoutResponse |
| `admin/src/api/generated/schemas/mCPConfigUpdate.ts` | 16 | 定义:MCPConfigUpdate · 依赖:./mCPConfigUpdateEnv.ts |
| `admin/src/api/generated/schemas/mCPConfigUpdateEnv.ts` | 9 | 定义:MCPConfigUpdateEnv |
| `admin/src/api/generated/schemas/markIssuedBody.ts` | 21 | 定义:MarkIssuedBody |
| `admin/src/api/generated/schemas/markerGenesApiV1SuperAdminGeoMarkersGdsIdGetParams.ts` | 15 | 定义:MarkerGenesApiV1SuperAdminGeoMarkersGdsIdGetParams |
| `admin/src/api/generated/schemas/mcpBridgeHealthApiV1AgentHubMcpBridgeHealthGetParams.ts` | 11 | 定义:McpBridgeHealthApiV1AgentHubMcpBridgeHealthGetParams |
| `admin/src/api/generated/schemas/mediaPublishBody.ts` | 12 | 定义:MediaPublishBody |
| `admin/src/api/generated/schemas/mediaPublishTrafficBody.ts` | 14 | 定义:MediaPublishTrafficBody |
| `admin/src/api/generated/schemas/menuCreate.ts` | 18 | 定义:MenuCreate |
| `admin/src/api/generated/schemas/merchantIMRoutingCreate.ts` | 33 | 定义:MerchantIMRoutingCreate |
| `admin/src/api/generated/schemas/merchantIMRoutingResponse.ts` | 36 | 定义:MerchantIMRoutingResponse |
| `admin/src/api/generated/schemas/merchantIMRoutingUpdate.ts` | 18 | 定义:MerchantIMRoutingUpdate |
| `admin/src/api/generated/schemas/mobileImRoutingApiV1MobileImRoutingGetParams.ts` | 17 | 定义:MobileImRoutingApiV1MobileImRoutingGetParams |
| `admin/src/api/generated/schemas/mobileProductCanonicalApiV1MobileProductProductIdGetParams.ts` | 11 | 定义:MobileProductCanonicalApiV1MobileProductProductIdGetParams |
| `admin/src/api/generated/schemas/mobileProductLegacyApiV1MobileMobileProductProductIdGetParams.ts` | 11 | 定义:MobileProductLegacyApiV1MobileMobileProductProductIdGetParams |
| `admin/src/api/generated/schemas/mobileSitePolicyApiV1MobileSitePolicyGetParams.ts` | 18 | 定义:MobileSitePolicyApiV1MobileSitePolicyGetParams |
| `admin/src/api/generated/schemas/mockPayRequest.ts` | 11 | 定义:MockPayRequest |
| `admin/src/api/generated/schemas/monitorPlanRequest.ts` | 12 | 定义:MonitorPlanRequest |
| `admin/src/api/generated/schemas/n8nWebhookBody.ts` | 18 | 定义:N8nWebhookBody · 依赖:./n8nWebhookBodyResult.ts |
| `admin/src/api/generated/schemas/n8nWebhookBodyResult.ts` | 9 | 定义:N8nWebhookBodyResult |
| `admin/src/api/generated/schemas/notifyRequest.ts` | 15 | 定义:NotifyRequest · 依赖:./notifyRequestData.ts |
| `admin/src/api/generated/schemas/notifyRequestData.ts` | 9 | 定义:NotifyRequestData |
| `admin/src/api/generated/schemas/nurtureCreateBody.ts` | 22 | 定义:NurtureCreateBody |
| `admin/src/api/generated/schemas/nurtureTransitionBody.ts` | 12 | 定义:NurtureTransitionBody |
| `admin/src/api/generated/schemas/oAuthAuthorizeResponse.ts` | 13 | 定义:OAuthAuthorizeResponse |
| `admin/src/api/generated/schemas/oauthAuthorizeApiV1AuthOauthProviderAuthorizeGetParams.ts` | 11 | 定义:OauthAuthorizeApiV1AuthOauthProviderAuthorizeGetParams |
| `admin/src/api/generated/schemas/onboardingAutopilotRequest.ts` | 13 | 定义:OnboardingAutopilotRequest |
| `admin/src/api/generated/schemas/onboardingImContactsRequest.ts` | 17 | 定义:OnboardingImContactsRequest |
| `admin/src/api/generated/schemas/onboardingPlatformBindRequest.ts` | 20 | 定义:OnboardingPlatformBindRequest · 依赖:./onboardingPlatformBindRequestConfigs.ts,./onboardingPlatformBindRequestTokenData.ts |
| `admin/src/api/generated/schemas/onboardingPlatformBindRequestConfigs.ts` | 9 | 定义:OnboardingPlatformBindRequestConfigs |
| `admin/src/api/generated/schemas/onboardingPlatformBindRequestTokenData.ts` | 9 | 定义:OnboardingPlatformBindRequestTokenData |
| `admin/src/api/generated/schemas/onboardingWangcaiPreviewRequest.ts` | 11 | 定义:OnboardingWangcaiPreviewRequest |
| `admin/src/api/generated/schemas/onboardingWizardCompleteRequest.ts` | 11 | 定义:OnboardingWizardCompleteRequest |
| `admin/src/api/generated/schemas/operationsTrafficBoardApiV1AnalyticsOperationsTrafficBoardGetParams.ts` | 12 | 定义:OperationsTrafficBoardApiV1AnalyticsOperationsTrafficBoardGetParams |
| `admin/src/api/generated/schemas/opsHermesInstructBody.ts` | 15 | 定义:OpsHermesInstructBody |
| `admin/src/api/generated/schemas/opsInstructBody.ts` | 16 | 定义:OpsInstructBody |
| `admin/src/api/generated/schemas/opsPublishWorkerRetryFailedApiV1OpsPublishWorkerRetryFailedPostParams.ts` | 15 | 定义:OpsPublishWorkerRetryFailedApiV1OpsPublishWorkerRetryFailedPostParams |
| `admin/src/api/generated/schemas/opsPublishWorkerRunApiV1OpsPublishWorkerRunPostParams.ts` | 15 | 定义:OpsPublishWorkerRunApiV1OpsPublishWorkerRunPostParams |
| `admin/src/api/generated/schemas/opsReadinessNotifyApiV1OpsAlertsReadinessNotifyPostParams.ts` | 14 | 定义:OpsReadinessNotifyApiV1OpsAlertsReadinessNotifyPostParams |
| `admin/src/api/generated/schemas/opsRunAllJobsApiV1OpsJobsRunAllPostParams.ts` | 16 | 定义:OpsRunAllJobsApiV1OpsJobsRunAllPostParams |
| `admin/src/api/generated/schemas/opsTenantExpiryPreviewApiV1OpsTenantsExpiryPreviewGetParams.ts` | 15 | 定义:OpsTenantExpiryPreviewApiV1OpsTenantsExpiryPreviewGetParams |
| `admin/src/api/generated/schemas/optimizeContentFrontendApiV1SeoMatrixOptimizePostBody.ts` | 9 | 定义:OptimizeContentFrontendApiV1SeoMatrixOptimizePostBody |
| `admin/src/api/generated/schemas/optimizeSeoPageApiV1SeoPagesResourceIdOptimizePostParams.ts` | 11 | 定义:OptimizeSeoPageApiV1SeoPagesResourceIdOptimizePostParams |
| `admin/src/api/generated/schemas/paymentOpsAuditExportApiV1PaymentOpsAuditExportGetParams.ts` | 13 | 定义:PaymentOpsAuditExportApiV1PaymentOpsAuditExportGetParams |
| `admin/src/api/generated/schemas/paymentOpsAuditListApiV1PaymentOpsAuditGetParams.ts` | 28 | 定义:PaymentOpsAuditListApiV1PaymentOpsAuditGetParams |
| `admin/src/api/generated/schemas/paymentOpsPublicNotifyCheckApiV1PaymentOpsStagingPublicNotifyCheckPostParams.ts` | 16 | 定义:PaymentOpsPublicNotifyCheckApiV1PaymentOpsStagingPublicNotifyCheckPostParams |
| `admin/src/api/generated/schemas/paymentOpsPublicReachabilityApiV1PaymentOpsStagingPublicReachabilityGetParams.ts` | 11 | 定义:PaymentOpsPublicReachabilityApiV1PaymentOpsStagingPublicReachabilityGetParams |
| `admin/src/api/generated/schemas/paymentStatusUpdate.ts` | 13 | 定义:PaymentStatusUpdate |
| `admin/src/api/generated/schemas/pcaPlotDataApiV1SuperAdminGeoVisualizationPcaGetParams.ts` | 11 | 定义:PcaPlotDataApiV1SuperAdminGeoVisualizationPcaGetParams |
| `admin/src/api/generated/schemas/pilotDemoHttpsCheckApiV1DomainsPilotDemoHttpsGetParams.ts` | 14 | 定义:PilotDemoHttpsCheckApiV1DomainsPilotDemoHttpsGetParams |
| `admin/src/api/generated/schemas/platformConfigUpdate.ts` | 26 | 定义:PlatformConfigUpdate |
| `admin/src/api/generated/schemas/pluginRunBody.ts` | 17 | 定义:PluginRunBody · 依赖:./pluginRunBodyContext.ts |
| `admin/src/api/generated/schemas/pluginRunBodyContext.ts` | 9 | 定义:PluginRunBodyContext |
| `admin/src/api/generated/schemas/preprocessRequest.ts` | 12 | 定义:PreprocessRequest |
| `admin/src/api/generated/schemas/previewPublishLinksApiV1ContentMastersMasterIdLinkPreviewGetParams.ts` | 14 | 定义:PreviewPublishLinksApiV1ContentMastersMasterIdLinkPreviewGetParams |
| `admin/src/api/generated/schemas/probeModelsStatusApiV1SuperAdminAiConfigModelsProbePostParams.ts` | 11 | 定义:ProbeModelsStatusApiV1SuperAdminAiConfigModelsProbePostParams |
| `admin/src/api/generated/schemas/productCreate.ts` | 31 | 定义:ProductCreate · 依赖:./productCreateSpecifications.ts |
| `admin/src/api/generated/schemas/productCreateSpecifications.ts` | 9 | 定义:ProductCreateSpecifications |
| `admin/src/api/generated/schemas/productDocumentResponse.ts` | 19 | 定义:ProductDocumentResponse |
| `admin/src/api/generated/schemas/productListResponse.ts` | 15 | 定义:ProductListResponse · 依赖:./productResponse.ts |
| `admin/src/api/generated/schemas/productResponse.ts` | 34 | 定义:ProductResponse · 依赖:./productResponseSpecifications.ts |
| `admin/src/api/generated/schemas/productResponseSpecifications.ts` | 9 | 定义:ProductResponseSpecifications |
| `admin/src/api/generated/schemas/productUpdate.ts` | 31 | 定义:ProductUpdate · 依赖:./productUpdateSpecifications.ts |
| `admin/src/api/generated/schemas/productUpdateSpecifications.ts` | 9 | 定义:ProductUpdateSpecifications |
| `admin/src/api/generated/schemas/profileCreate.ts` | 16 | 定义:ProfileCreate · 依赖:./profileCreateFingerprint.ts |
| `admin/src/api/generated/schemas/profileCreateFingerprint.ts` | 9 | 定义:ProfileCreateFingerprint |
| `admin/src/api/generated/schemas/profitDashboardApiV1FinanceProfitDashboardGetParams.ts` | 11 | 定义:ProfitDashboardApiV1FinanceProfitDashboardGetParams |
| `admin/src/api/generated/schemas/publicInquiryCreate.ts` | 34 | 定义:PublicInquiryCreate |
| `admin/src/api/generated/schemas/publishContentBody.ts` | 25 | 定义:PublishContentBody |
| `admin/src/api/generated/schemas/publishFromMasterRequest.ts` | 15 | 定义:PublishFromMasterRequest |
| `admin/src/api/generated/schemas/publishTaskCreate.ts` | 22 | 定义:PublishTaskCreate · 依赖:./publishTaskCreateContentData.ts |
| `admin/src/api/generated/schemas/publishTaskCreateContentData.ts` | 9 | 定义:PublishTaskCreateContentData |
| `admin/src/api/generated/schemas/publishTaskResponse.ts` | 33 | 定义:PublishTaskResponse · 依赖:./publishTaskResponseContentData.ts |
| `admin/src/api/generated/schemas/publishTaskResponseContentData.ts` | 9 | 定义:PublishTaskResponseContentData |
| `admin/src/api/generated/schemas/publishTaskUpdate.ts` | 18 | 定义:PublishTaskUpdate · 依赖:./publishTaskUpdateContentData.ts |
| `admin/src/api/generated/schemas/publishTaskUpdateContentData.ts` | 9 | 定义:PublishTaskUpdateContentData |
| `admin/src/api/generated/schemas/quickCheckApiV1SuperAdminGeoEngineQuickCheckGetParams.ts` | 14 | 定义:QuickCheckApiV1SuperAdminGeoEngineQuickCheckGetParams |
| `admin/src/api/generated/schemas/quickPublishRequest.ts` | 13 | 定义:QuickPublishRequest |
| `admin/src/api/generated/schemas/quoteTokenPackCustomApiV1PaymentAddonTokenPackQuoteGetParams.ts` | 15 | 定义:QuoteTokenPackCustomApiV1PaymentAddonTokenPackQuoteGetParams |
| `admin/src/api/generated/schemas/rAGRequest.ts` | 13 | 定义:RAGRequest |
| `admin/src/api/generated/schemas/rankCheckResponse.ts` | 20 | 定义:RankCheckResponse · 依赖:./rankCheckResponseResultsItem.ts · ⚑MOCK |
| `admin/src/api/generated/schemas/rankCheckResponseResultsItem.ts` | 9 | 定义:RankCheckResponseResultsItem |
| `admin/src/api/generated/schemas/rankGuardCheckRequest.ts` | 19 | 定义:RankGuardCheckRequest |
| `admin/src/api/generated/schemas/rankingHistoryResponse.ts` | 15 | 定义:RankingHistoryResponse |
| `admin/src/api/generated/schemas/reRenderBody.ts` | 14 | 定义:ReRenderBody · 依赖:./reRenderBodyShots.ts |
| `admin/src/api/generated/schemas/reRenderBodyShots.ts` | 9 | 定义:ReRenderBodyShots |
| `admin/src/api/generated/schemas/redeemCashCouponAdminApiV1ReferralAdminCashCouponsRecordIdRedeemPostParams.ts` | 14 | 定义:RedeemCashCouponAdminApiV1ReferralAdminCashCouponsRecordIdRedeemPostParams |
| `admin/src/api/generated/schemas/regionKeywordCreate.ts` | 14 | 定义:RegionKeywordCreate |
| `admin/src/api/generated/schemas/removeArticleAuthorApiV1SeoArticlesArticleIdAuthorsAuthorIdDelete200.ts` | 9 | 定义:RemoveArticleAuthorApiV1SeoArticlesArticleIdAuthorsAuthorIdDelete200 |
| `admin/src/api/generated/schemas/renewSslCertificateApiV1SslCertificatesApiV1SslCertificatesCertIdRenewPost200.ts` | 9 | 定义:RenewSslCertificateApiV1SslCertificatesApiV1SslCertificatesCertIdRenewPost200 |
| `admin/src/api/generated/schemas/researchBriefRequest.ts` | 15 | 定义:ResearchBriefRequest |
| `admin/src/api/generated/schemas/resetUserPasswordApiV1SuperAdminUsersUserIdResetPasswordPostParams.ts` | 14 | 定义:ResetUserPasswordApiV1SuperAdminUsersUserIdResetPasswordPostParams |
| `admin/src/api/generated/schemas/resolveHostApiV1DomainsResolveGetParams.ts` | 14 | 定义:ResolveHostApiV1DomainsResolveGetParams |
| `admin/src/api/generated/schemas/resolveIssueApiV1ComplianceIssuesIssueIdResolvePutBody.ts` | 9 | 定义:ResolveIssueApiV1ComplianceIssuesIssueIdResolvePutBody |
| `admin/src/api/generated/schemas/resolveVisitorImChannelApiV1ImRoutingResolveGetParams.ts` | 23 | 定义:ResolveVisitorImChannelApiV1ImRoutingResolveGetParams |
| `admin/src/api/generated/schemas/resolveVisitorImChannelsApiV1ImRoutingChannelsGetParams.ts` | 23 | 定义:ResolveVisitorImChannelsApiV1ImRoutingChannelsGetParams |
| `admin/src/api/generated/schemas/restartServicesApiV1SystemRestartPostParams.ts` | 11 | 定义:RestartServicesApiV1SystemRestartPostParams |
| `admin/src/api/generated/schemas/restoreBackupApiV1SystemHealthBackupRestorePostBody.ts` | 9 | 定义:RestoreBackupApiV1SystemHealthBackupRestorePostBody |
| `admin/src/api/generated/schemas/retryPublishTaskApiV1PublishTasksApiV1PublishTasksTaskIdRetryPost200.ts` | 9 | 定义:RetryPublishTaskApiV1PublishTasksApiV1PublishTasksTaskIdRetryPost200 |
| `admin/src/api/generated/schemas/reviewBody.ts` | 14 | 定义:ReviewBody |
| `admin/src/api/generated/schemas/reviewCreate.ts` | 25 | 定义:ReviewCreate |
| `admin/src/api/generated/schemas/reviewResponse.ts` | 22 | 定义:ReviewResponse |
| `admin/src/api/generated/schemas/reviewStatsResponse.ts` | 17 | 定义:ReviewStatsResponse · 依赖:./reviewStatsResponseRatingDistribution.ts |
| `admin/src/api/generated/schemas/reviewStatsResponseRatingDistribution.ts` | 9 | 定义:ReviewStatsResponseRatingDistribution |
| `admin/src/api/generated/schemas/reviewUpdate.ts` | 21 | 定义:ReviewUpdate |
| `admin/src/api/generated/schemas/roleCreate.ts` | 13 | 定义:RoleCreate |
| `admin/src/api/generated/schemas/roleUpdate.ts` | 13 | 定义:RoleUpdate |
| `admin/src/api/generated/schemas/rumBeaconBody.ts` | 16 | 定义:RumBeaconBody |
| `admin/src/api/generated/schemas/runBody.ts` | 17 | 定义:RunBody · 依赖:./runBodyContext.ts |
| `admin/src/api/generated/schemas/runBodyContext.ts` | 9 | 定义:RunBodyContext |
| `admin/src/api/generated/schemas/runMonitorApiV1SuperAdminGeoEngineMonitorRunGetParams.ts` | 11 | 定义:RunMonitorApiV1SuperAdminGeoEngineMonitorRunGetParams |
| `admin/src/api/generated/schemas/runStressTestApiV1SystemHealthStressTestPostBody.ts` | 9 | 定义:RunStressTestApiV1SystemHealthStressTestPostBody |
| `admin/src/api/generated/schemas/runTaskOrchestratorApiV1AgentHubTaskOrchestratorRunPostBody.ts` | 9 | 定义:RunTaskOrchestratorApiV1AgentHubTaskOrchestratorRunPostBody |
| `admin/src/api/generated/schemas/sSLCertificateCreate.ts` | 17 | 定义:SSLCertificateCreate |
| `admin/src/api/generated/schemas/sSLCertificateResponse.ts` | 31 | 定义:SSLCertificateResponse |
| `admin/src/api/generated/schemas/saveAlarmConfigApiV1SuperAdminAiCostAlarmConfigPostBody.ts` | 9 | 定义:SaveAlarmConfigApiV1SuperAdminAiCostAlarmConfigPostBody |
| `admin/src/api/generated/schemas/saveAlarmConfigApiV1SuperAdminAiUsageAlarmConfigPostBody.ts` | 9 | 定义:SaveAlarmConfigApiV1SuperAdminAiUsageAlarmConfigPostBody |
| `admin/src/api/generated/schemas/saveDraftFrontendApiV1SeoMatrixDraftsPostBody.ts` | 9 | 定义:SaveDraftFrontendApiV1SeoMatrixDraftsPostBody |
| `admin/src/api/generated/schemas/saveInclusionSettingsApiV1SeoMatrixInclusionSettingsPutBody.ts` | 9 | 定义:SaveInclusionSettingsApiV1SeoMatrixInclusionSettingsPutBody |
| `admin/src/api/generated/schemas/scanContentApiV1SeoComplianceScanPostBody.ts` | 9 | 定义:ScanContentApiV1SeoComplianceScanPostBody |
| `admin/src/api/generated/schemas/schedulePublishBody.ts` | 15 | 定义:SchedulePublishBody |
| `admin/src/api/generated/schemas/schemaMarkupCreate.ts` | 15 | 定义:SchemaMarkupCreate · 依赖:./schemaMarkupCreateContent.ts |
| `admin/src/api/generated/schemas/schemaMarkupCreateContent.ts` | 9 | 定义:SchemaMarkupCreateContent |
| `admin/src/api/generated/schemas/schemaMarkupResponse.ts` | 19 | 定义:SchemaMarkupResponse · 依赖:./schemaMarkupResponseContent.ts |
| `admin/src/api/generated/schemas/schemaMarkupResponseContent.ts` | 9 | 定义:SchemaMarkupResponseContent |
| `admin/src/api/generated/schemas/schemaMarkupUpdate.ts` | 16 | 定义:SchemaMarkupUpdate · 依赖:./schemaMarkupUpdateContent.ts |
| `admin/src/api/generated/schemas/schemaMarkupUpdateContent.ts` | 9 | 定义:SchemaMarkupUpdateContent |
| `admin/src/api/generated/schemas/schemaTemplateResponse.ts` | 19 | 定义:SchemaTemplateResponse · 依赖:./schemaTemplateResponseTemplate.ts |
| `admin/src/api/generated/schemas/schemaTemplateResponseTemplate.ts` | 9 | 定义:SchemaTemplateResponseTemplate |
| `admin/src/api/generated/schemas/schemaValidationResult.ts` | 16 | 定义:SchemaValidationResult · 依赖:./schemaValidationResultErrorsItem.ts,./schemaValidationResultWarningsItem.ts |
| `admin/src/api/generated/schemas/schemaValidationResultErrorsItem.ts` | 9 | 定义:SchemaValidationResultErrorsItem |
| `admin/src/api/generated/schemas/schemaValidationResultWarningsItem.ts` | 9 | 定义:SchemaValidationResultWarningsItem |
| `admin/src/api/generated/schemas/scoreContentEndpointApiV1SuperAdminDashboardScoreContentPostBody.ts` | 9 | 定义:ScoreContentEndpointApiV1SuperAdminDashboardScoreContentPostBody |
| `admin/src/api/generated/schemas/scriptUpdateBody.ts` | 13 | 定义:ScriptUpdateBody · 依赖:./scriptUpdateBodyShots.ts |
| `admin/src/api/generated/schemas/scriptUpdateBodyShots.ts` | 9 | 定义:ScriptUpdateBodyShots |
| `admin/src/api/generated/schemas/searchDistrictsApiV1SeoMatrixDistrictsGetParams.ts` | 15 | 定义:SearchDistrictsApiV1SeoMatrixDistrictsGetParams |
| `admin/src/api/generated/schemas/searchGeoApiV1SuperAdminGeoSearchGetParams.ts` | 19 | 定义:SearchGeoApiV1SuperAdminGeoSearchGetParams |
| `admin/src/api/generated/schemas/searchGeoEndpointApiV1GeoSearchGetParams.ts` | 18 | 定义:SearchGeoEndpointApiV1GeoSearchGetParams |
| `admin/src/api/generated/schemas/searchKnowledgeApiV1AiKnowledgeKnowledgeSearchGetParams.ts` | 20 | 定义:SearchKnowledgeApiV1AiKnowledgeKnowledgeSearchGetParams |
| `admin/src/api/generated/schemas/searchKnowledgeApiV1KnowledgeKnowledgeSearchGetParams.ts` | 20 | 定义:SearchKnowledgeApiV1KnowledgeKnowledgeSearchGetParams |
| `admin/src/api/generated/schemas/searchPagesApiV1ContentPagesSearchGetParams.ts` | 13 | 定义:SearchPagesApiV1ContentPagesSearchGetParams |
| `admin/src/api/generated/schemas/searchRequest.ts` | 12 | 定义:SearchRequest |
| `admin/src/api/generated/schemas/sendInquiryNotificationApiV1FeishuSendInquiryInquiryIdPostParams.ts` | 11 | 定义:SendInquiryNotificationApiV1FeishuSendInquiryInquiryIdPostParams |
| `admin/src/api/generated/schemas/sendMessageRequest.ts` | 13 | 定义:SendMessageRequest |
| `admin/src/api/generated/schemas/sendNotificationApiV1NotificationsPostBody.ts` | 9 | 定义:SendNotificationApiV1NotificationsPostBody |
| `admin/src/api/generated/schemas/seoMetadataCreate.ts` | 22 | 定义:SeoMetadataCreate |
| `admin/src/api/generated/schemas/seoMetadataResponse.ts` | 24 | 定义:SeoMetadataResponse |
| `admin/src/api/generated/schemas/seoMetadataUpdate.ts` | 20 | 定义:SeoMetadataUpdate |
| `admin/src/api/generated/schemas/setAlertConfigApiV1AiUsageAlertsConfigPostBody.ts` | 9 | 定义:SetAlertConfigApiV1AiUsageAlertsConfigPostBody |
| `admin/src/api/generated/schemas/setDefaultModelApiV1SuperAdminAiConfigSetDefaultPostBody.ts` | 9 | 定义:SetDefaultModelApiV1SuperAdminAiConfigSetDefaultPostBody |
| `admin/src/api/generated/schemas/siteAiGenerateRequest.ts` | 17 | 定义:SiteAiGenerateRequest |
| `admin/src/api/generated/schemas/siteAuditCreate.ts` | 13 | 定义:SiteAuditCreate |
| `admin/src/api/generated/schemas/siteAuditResponse.ts` | 22 | 定义:SiteAuditResponse |
| `admin/src/api/generated/schemas/siteEditorDraftBody.ts` | 17 | 定义:SiteEditorDraftBody |
| `admin/src/api/generated/schemas/submitSitemapApiV1BaiduSitemapSubmitPostParams.ts` | 22 | 定义:SubmitSitemapApiV1BaiduSitemapSubmitPostParams |
| `admin/src/api/generated/schemas/subscriptionCreate.ts` | 15 | 定义:SubscriptionCreate |
| `admin/src/api/generated/schemas/superAdminAggregationApiV1SuperAdminAggregationGetParams.ts` | 11 | 定义:SuperAdminAggregationApiV1SuperAdminAggregationGetParams |
| `admin/src/api/generated/schemas/superAdminTrafficBoardApiV1SuperAdminTrafficBoardGetParams.ts` | 12 | 定义:SuperAdminTrafficBoardApiV1SuperAdminTrafficBoardGetParams |
| `admin/src/api/generated/schemas/syncAiCostsApiV1OpsFinanceSyncAiCostsPostParams.ts` | 15 | 定义:SyncAiCostsApiV1OpsFinanceSyncAiCostsPostParams |
| `admin/src/api/generated/schemas/syncFeedbackApiV1UbrainCommercialOsFeedbackSyncPostParams.ts` | 15 | 定义:SyncFeedbackApiV1UbrainCommercialOsFeedbackSyncPostParams |
| `admin/src/api/generated/schemas/syncOrderTrackingApiV1LogisticsOrdersOrderIdSyncTrackingPostParams.ts` | 11 | 定义:SyncOrderTrackingApiV1LogisticsOrdersOrderIdSyncTrackingPostParams |
| `admin/src/api/generated/schemas/tenantAiScenarioUpdate.ts` | 12 | 定义:TenantAiScenarioUpdate · 依赖:./tenantAiScenarioUpdateOverrides.ts |
| `admin/src/api/generated/schemas/tenantAiScenarioUpdateOverrides.ts` | 9 | 定义:TenantAiScenarioUpdateOverrides |
| `admin/src/api/generated/schemas/tenantCreate.ts` | 18 | 定义:TenantCreate |
| `admin/src/api/generated/schemas/tenantInvoiceGenerateBody.ts` | 13 | 定义:TenantInvoiceGenerateBody |
| `admin/src/api/generated/schemas/tenantInvoiceListResponse.ts` | 15 | 定义:TenantInvoiceListResponse · 依赖:./tenantInvoiceResponse.ts |
| `admin/src/api/generated/schemas/tenantInvoiceResponse.ts` | 18 | 定义:TenantInvoiceResponse |
| `admin/src/api/generated/schemas/tenantInvoiceStatusBody.ts` | 13 | 定义:TenantInvoiceStatusBody |
| `admin/src/api/generated/schemas/tenantOverviewResponse.ts` | 14 | 定义:TenantOverviewResponse · 依赖:./tenantResponse.ts,./tenantStatsResponse.ts |
| `admin/src/api/generated/schemas/tenantPlanCreate.ts` | 20 | 定义:TenantPlanCreate |
| `admin/src/api/generated/schemas/tenantPlanResponse.ts` | 22 | 定义:TenantPlanResponse |
| `admin/src/api/generated/schemas/tenantPlanUpdate.ts` | 19 | 定义:TenantPlanUpdate |
| `admin/src/api/generated/schemas/tenantRegisterSchema.ts` | 32 | 定义:TenantRegisterSchema |
| `admin/src/api/generated/schemas/tenantResponse.ts` | 30 | 定义:TenantResponse · 依赖:./tenantPlanResponse.ts |
| `admin/src/api/generated/schemas/tenantSelfUpdate.ts` | 14 | 定义:TenantSelfUpdate |
| `admin/src/api/generated/schemas/tenantStatsResponse.ts` | 16 | 定义:TenantStatsResponse |
| `admin/src/api/generated/schemas/tenantUpdate.ts` | 19 | 定义:TenantUpdate |
| `admin/src/api/generated/schemas/tenantVisitorContextApiV1PublicTenantsDomainVisitorContextGetParams.ts` | 18 | 定义:TenantVisitorContextApiV1PublicTenantsDomainVisitorContextGetParams |
| `admin/src/api/generated/schemas/testAiConnectionApiV1SuperAdminAiConfigTestPostBody.ts` | 9 | 定义:TestAiConnectionApiV1SuperAdminAiConfigTestPostBody |
| `admin/src/api/generated/schemas/thirdPartyLoginRequest.ts` | 13 | 定义:ThirdPartyLoginRequest |
| `admin/src/api/generated/schemas/thirdPartyLoginResponse.ts` | 17 | 定义:ThirdPartyLoginResponse · 依赖:./appSchemasAuthUserResponse.ts |
| `admin/src/api/generated/schemas/toggleBody.ts` | 11 | 定义:ToggleBody |
| `admin/src/api/generated/schemas/toggleProviderApiV1AiConfigProviderProviderIdTogglePostBody.ts` | 9 | 定义:ToggleProviderApiV1AiConfigProviderProviderIdTogglePostBody |
| `admin/src/api/generated/schemas/tokenRefreshRequest.ts` | 11 | 定义:TokenRefreshRequest |
| `admin/src/api/generated/schemas/tokenResponse.ts` | 19 | 定义:TokenResponse · 依赖:./appSchemasAuthUserResponse.ts,./tokenResponsePortals.ts |
| `admin/src/api/generated/schemas/tokenResponsePortals.ts` | 9 | 定义:TokenResponsePortals |
| `admin/src/api/generated/schemas/topUpRequest.ts` | 14 | 定义:TopUpRequest |
| `admin/src/api/generated/schemas/trackEventApiV1AbTestTestIdTrackEventPostBody.ts` | 9 | 定义:TrackEventApiV1AbTestTestIdTrackEventPostBody |
| `admin/src/api/generated/schemas/trackEventApiV1AbTestTestIdTrackEventPostParams.ts` | 18 | 定义:TrackEventApiV1AbTestTestIdTrackEventPostParams |
| `admin/src/api/generated/schemas/trackKeywordsRequest.ts` | 21 | 定义:TrackKeywordsRequest |
| `admin/src/api/generated/schemas/trackKeywordsResponse.ts` | 16 | 定义:TrackKeywordsResponse · 依赖:./trackKeywordsResponseResultsItem.ts |
| `admin/src/api/generated/schemas/trackKeywordsResponseResultsItem.ts` | 9 | 定义:TrackKeywordsResponseResultsItem |
| `admin/src/api/generated/schemas/trackShipmentApiV1LogisticsTrackGetParams.ts` | 19 | 定义:TrackShipmentApiV1LogisticsTrackGetParams |
| `admin/src/api/generated/schemas/trackingNumberUpdate.ts` | 16 | 定义:TrackingNumberUpdate |
| `admin/src/api/generated/schemas/tradeBlueOceanApiV1TradeIntelBlueOceanGetParams.ts` | 12 | 定义:TradeBlueOceanApiV1TradeIntelBlueOceanGetParams |
| `admin/src/api/generated/schemas/tradeCommercialStatsApiV1TradeIntelCommercialStatsGetParams.ts` | 11 | 定义:TradeCommercialStatsApiV1TradeIntelCommercialStatsGetParams |
| `admin/src/api/generated/schemas/tradeCustomsCatalogApiV1TradeIntelCustomsCatalogGetParams.ts` | 11 | 定义:TradeCustomsCatalogApiV1TradeIntelCustomsCatalogGetParams |
| `admin/src/api/generated/schemas/tradeCustomsStatsApiV1TradeIntelCustomsStatsGetParams.ts` | 11 | 定义:TradeCustomsStatsApiV1TradeIntelCustomsStatsGetParams |
| `admin/src/api/generated/schemas/tradeFeasibilityApiV1TradeIntelFeasibilityGetParams.ts` | 16 | 定义:TradeFeasibilityApiV1TradeIntelFeasibilityGetParams |
| `admin/src/api/generated/schemas/tradeHsApiV1TradeIntelHsGetParams.ts` | 14 | 定义:TradeHsApiV1TradeIntelHsGetParams |
| `admin/src/api/generated/schemas/translationTaskCreate.ts` | 13 | 定义:TranslationTaskCreate |
| `admin/src/api/generated/schemas/triggerAlertRuleApiV1SuperAdminGeoEngineAlertsRulesRuleIdTriggerPostBody.ts` | 9 | 定义:TriggerAlertRuleApiV1SuperAdminGeoEngineAlertsRulesRuleIdTriggerPostBody |
| `admin/src/api/generated/schemas/triggerAutoRenewalApiV1SslCertificatesApiV1SslCertificatesAutoRenewPost200.ts` | 9 | 定义:TriggerAutoRenewalApiV1SslCertificatesApiV1SslCertificatesAutoRenewPost200 |
| `admin/src/api/generated/schemas/triggerPreheatApiV1EdgeCdnPreheatPostBody.ts` | 9 | 定义:TriggerPreheatApiV1EdgeCdnPreheatPostBody |
| `admin/src/api/generated/schemas/uBrainChatRequest.ts` | 19 | 定义:UBrainChatRequest · 依赖:./uBrainChatRequestContext.ts |
| `admin/src/api/generated/schemas/uBrainChatRequestContext.ts` | 9 | 定义:UBrainChatRequestContext |
| `admin/src/api/generated/schemas/uBrainMemoryPatch.ts` | 16 | 定义:UBrainMemoryPatch |
| `admin/src/api/generated/schemas/uacLoginBody.ts` | 17 | 定义:UacLoginBody |
| `admin/src/api/generated/schemas/ubrainActionAuditApiV1UbrainActionAuditGetParams.ts` | 19 | 定义:UbrainActionAuditApiV1UbrainActionAuditGetParams |
| `admin/src/api/generated/schemas/ubrainListJobsApiV1UbrainJobsGetParams.ts` | 19 | 定义:UbrainListJobsApiV1UbrainJobsGetParams |
| `admin/src/api/generated/schemas/ubrainListProspectsApiV1UbrainProspectsGetParams.ts` | 15 | 定义:UbrainListProspectsApiV1UbrainProspectsGetParams |
| `admin/src/api/generated/schemas/ubrainRunPendingApiV1UbrainJobsRunPendingPostParams.ts` | 15 | 定义:UbrainRunPendingApiV1UbrainJobsRunPendingPostParams |
| `admin/src/api/generated/schemas/updateAiConfigApiV1AiConfigPutBody.ts` | 9 | 定义:UpdateAiConfigApiV1AiConfigPutBody |
| `admin/src/api/generated/schemas/updateAlertRuleApiV1SuperAdminGeoEngineAlertsRulesRuleIdPutBody.ts` | 9 | 定义:UpdateAlertRuleApiV1SuperAdminGeoEngineAlertsRulesRuleIdPutBody |
| `admin/src/api/generated/schemas/updateAuthorApiV1SeoAuthorsAuthorIdPut200.ts` | 9 | 定义:UpdateAuthorApiV1SeoAuthorsAuthorIdPut200 |
| `admin/src/api/generated/schemas/updateAuthorApiV1SeoAuthorsAuthorIdPutBody.ts` | 9 | 定义:UpdateAuthorApiV1SeoAuthorsAuthorIdPutBody |
| `admin/src/api/generated/schemas/updateChatSessionApiV1ChatSessionsSessionIdPut200.ts` | 9 | 定义:UpdateChatSessionApiV1ChatSessionsSessionIdPut200 |
| `admin/src/api/generated/schemas/updateChatSessionApiV1ChatSessionsSessionIdPutParams.ts` | 13 | 定义:UpdateChatSessionApiV1ChatSessionsSessionIdPutParams |
| `admin/src/api/generated/schemas/updateCombinatorialRuleApiV1SeoMatrixCombinatorialRulesRuleIdPutBody.ts` | 9 | 定义:UpdateCombinatorialRuleApiV1SeoMatrixCombinatorialRulesRuleIdPutBody |
| `admin/src/api/generated/schemas/updateContentTemplateApiV1SeoMatrixContentTemplatesTemplateIdPutBody.ts` | 9 | 定义:UpdateContentTemplateApiV1SeoMatrixContentTemplatesTemplateIdPutBody |
| `admin/src/api/generated/schemas/updateIndustryKeywordApiV1SeoMatrixIndustryKeywordsKeywordIdPutBody.ts` | 9 | 定义:UpdateIndustryKeywordApiV1SeoMatrixIndustryKeywordsKeywordIdPutBody |
| `admin/src/api/generated/schemas/updateKeywordApiV1SeoComplianceKeywordsKeywordIdPutBody.ts` | 9 | 定义:UpdateKeywordApiV1SeoComplianceKeywordsKeywordIdPutBody |
| `admin/src/api/generated/schemas/updateNewsApiV1NewsNewsIdPutBody.ts` | 9 | 定义:UpdateNewsApiV1NewsNewsIdPutBody |
| `admin/src/api/generated/schemas/updateNvidiaScenariosApiV1SuperAdminAiConfigNvidiaScenariosPutBody.ts` | 9 | 定义:UpdateNvidiaScenariosApiV1SuperAdminAiConfigNvidiaScenariosPutBody |
| `admin/src/api/generated/schemas/updateOrderStatusApiV1OrdersOrderIdStatusPut200.ts` | 9 | 定义:UpdateOrderStatusApiV1OrdersOrderIdStatusPut200 |
| `admin/src/api/generated/schemas/updateOrderStatusApiV1OrdersOrderIdStatusPutParams.ts` | 11 | 定义:UpdateOrderStatusApiV1OrdersOrderIdStatusPutParams |
| `admin/src/api/generated/schemas/updatePlatformAccountApiV1SeoMatrixPlatformAccountsAccountIdPutBody.ts` | 9 | 定义:UpdatePlatformAccountApiV1SeoMatrixPlatformAccountsAccountIdPutBody |
| `admin/src/api/generated/schemas/updateProductCategoryApiV1ProductCategoriesCategoryIdPut200.ts` | 9 | 定义:UpdateProductCategoryApiV1ProductCategoriesCategoryIdPut200 |
| `admin/src/api/generated/schemas/updateProductCategoryApiV1ProductCategoriesCategoryIdPutParams.ts` | 19 | 定义:UpdateProductCategoryApiV1ProductCategoriesCategoryIdPutParams |
| `admin/src/api/generated/schemas/updateProductImageApiV1ProductImagesImageIdPut200.ts` | 9 | 定义:UpdateProductImageApiV1ProductImagesImageIdPut200 |
| `admin/src/api/generated/schemas/updateProductImageApiV1ProductImagesImageIdPutParams.ts` | 13 | 定义:UpdateProductImageApiV1ProductImagesImageIdPutParams |
| `admin/src/api/generated/schemas/updateQuoteStatusApiV1QuotesQuoteIdStatusPut200.ts` | 9 | 定义:UpdateQuoteStatusApiV1QuotesQuoteIdStatusPut200 |
| `admin/src/api/generated/schemas/updateQuoteStatusApiV1QuotesQuoteIdStatusPutParams.ts` | 11 | 定义:UpdateQuoteStatusApiV1QuotesQuoteIdStatusPutParams |
| `admin/src/api/generated/schemas/updateRegionKeywordApiV1SeoMatrixRegionKeywordsRowIdPutBody.ts` | 9 | 定义:UpdateRegionKeywordApiV1SeoMatrixRegionKeywordsRowIdPutBody |
| `admin/src/api/generated/schemas/updateRequest.ts` | 13 | 定义:UpdateRequest |
| `admin/src/api/generated/schemas/updateSelfAiTrafficProviderApiV1TenantsSelfAiTrafficProviderPutBody.ts` | 9 | 定义:UpdateSelfAiTrafficProviderApiV1TenantsSelfAiTrafficProviderPutBody |
| `admin/src/api/generated/schemas/updateSeoMetadataApiV1SeoMetadataSeoIdPut200.ts` | 9 | 定义:UpdateSeoMetadataApiV1SeoMetadataSeoIdPut200 |
| `admin/src/api/generated/schemas/updateSeoMetadataApiV1SeoMetadataSeoIdPutParams.ts` | 19 | 定义:UpdateSeoMetadataApiV1SeoMetadataSeoIdPutParams |
| `admin/src/api/generated/schemas/updateSeoPageApiV1SeoPagesResourceIdPutParams.ts` | 14 | 定义:UpdateSeoPageApiV1SeoPagesResourceIdPutParams |
| `admin/src/api/generated/schemas/updateSeoSettingsApiV1SettingsSeoPutBody.ts` | 9 | 定义:UpdateSeoSettingsApiV1SettingsSeoPutBody |
| `admin/src/api/generated/schemas/updateSettingsApiV1SeoMatrixSettingsPutBody.ts` | 9 | 定义:UpdateSettingsApiV1SeoMatrixSettingsPutBody |
| `admin/src/api/generated/schemas/updateSiteSettingsApiV1SettingsSitePutBody.ts` | 9 | 定义:UpdateSiteSettingsApiV1SettingsSitePutBody |
| `admin/src/api/generated/schemas/updateStatusApiV1ChatChatStatusPutParams.ts` | 11 | 定义:UpdateStatusApiV1ChatChatStatusPutParams |
| `admin/src/api/generated/schemas/updateSystemConfigApiV1SystemConfigConfigIdPut200.ts` | 9 | 定义:UpdateSystemConfigApiV1SystemConfigConfigIdPut200 |
| `admin/src/api/generated/schemas/updateSystemConfigApiV1SystemConfigConfigIdPutParams.ts` | 14 | 定义:UpdateSystemConfigApiV1SystemConfigConfigIdPutParams |
| `admin/src/api/generated/schemas/updateSystemSettingsApiV1SettingsSystemPutBody.ts` | 9 | 定义:UpdateSystemSettingsApiV1SettingsSystemPutBody |
| `admin/src/api/generated/schemas/uploadProductDocumentApiV1ProductsProductIdDocumentsPostParams.ts` | 12 | 定义:UploadProductDocumentApiV1ProductsProductIdDocumentsPostParams |
| `admin/src/api/generated/schemas/uploadProductImageApiV1ProductImagesPost200.ts` | 9 | 定义:UploadProductImageApiV1ProductImagesPost200 |
| `admin/src/api/generated/schemas/uploadProductImageApiV1ProductImagesPostParams.ts` | 14 | 定义:UploadProductImageApiV1ProductImagesPostParams |
| `admin/src/api/generated/schemas/usageDailyApiV1SuperAdminAiCostDailyGetParams.ts` | 15 | 定义:UsageDailyApiV1SuperAdminAiCostDailyGetParams |
| `admin/src/api/generated/schemas/usageDailyApiV1SuperAdminAiUsageDailyGetParams.ts` | 15 | 定义:UsageDailyApiV1SuperAdminAiUsageDailyGetParams |
| `admin/src/api/generated/schemas/userCreate.ts` | 14 | 定义:UserCreate |
| `admin/src/api/generated/schemas/userListResponse.ts` | 15 | 定义:UserListResponse · 依赖:./appSchemasUserUserResponse.ts |
| `admin/src/api/generated/schemas/userStatusUpdate.ts` | 11 | 定义:UserStatusUpdate |
| `admin/src/api/generated/schemas/userUpdate.ts` | 14 | 定义:UserUpdate |
| `admin/src/api/generated/schemas/validateQuoteBody.ts` | 18 | 定义:ValidateQuoteBody |
| `admin/src/api/generated/schemas/validateSchemaRequest.ts` | 12 | 定义:ValidateSchemaRequest · 依赖:./validateSchemaRequestContent.ts |
| `admin/src/api/generated/schemas/validateSchemaRequestContent.ts` | 9 | 定义:ValidateSchemaRequestContent |
| `admin/src/api/generated/schemas/validationError.ts` | 13 | 定义:ValidationError |
| `admin/src/api/generated/schemas/videoDistributeBody.ts` | 16 | 定义:VideoDistributeBody |
| `admin/src/api/generated/schemas/videoMatrixHermesBody.ts` | 16 | 定义:VideoMatrixHermesBody |
| `admin/src/api/generated/schemas/voiceTranscribeRequest.ts` | 13 | 定义:VoiceTranscribeRequest |
| `admin/src/api/generated/schemas/volcanoPlotDataApiV1SuperAdminGeoVisualizationVolcanoGetParams.ts` | 11 | 定义:VolcanoPlotDataApiV1SuperAdminGeoVisualizationVolcanoGetParams |
| `admin/src/api/generated/schemas/wangcaiAskBody.ts` | 18 | 定义:WangcaiAskBody |
| `admin/src/api/generated/schemas/wangcaiBrowserCompanionsApiV1WangcaiPluginsBrowserCompanionsGetParams.ts` | 14 | 定义:WangcaiBrowserCompanionsApiV1WangcaiPluginsBrowserCompanionsGetParams |
| `admin/src/api/generated/schemas/wangcaiCustomsAllApiV1PublicTenantsDomainWangcaiCustomsGetParams.ts` | 11 | 定义:WangcaiCustomsAllApiV1PublicTenantsDomainWangcaiCustomsGetParams |
| `admin/src/api/generated/schemas/wangcaiMarketplaceApiV1WangcaiPluginsMarketplaceGetParams.ts` | 11 | 定义:WangcaiMarketplaceApiV1WangcaiPluginsMarketplaceGetParams |
| `admin/src/api/generated/schemas/wangcaiPromptsApiV1PublicTenantsDomainWangcaiPromptsGetParams.ts` | 13 | 定义:WangcaiPromptsApiV1PublicTenantsDomainWangcaiPromptsGetParams |
| `admin/src/api/generated/schemas/wechatProbeRequest.ts` | 18 | 定义:WechatProbeRequest |
| `admin/src/api/generated/schemas/whiteLabelConfig.ts` | 16 | 定义:WhiteLabelConfig |
| `admin/src/api/generated/schemas/whiteLabelUpdate.ts` | 16 | 定义:WhiteLabelUpdate |
| `admin/src/api/generated/schemas/workspaceSearchApiV1SearchWorkspaceGetParams.ts` | 20 | 定义:WorkspaceSearchApiV1SearchWorkspaceGetParams |
| `admin/src/api/hermesGreedy.ts` | 475 | 定义:GreedyPersonality,GreedyCumulative,GreedyContestRow,GreedyLeaderboard,GreedyContestRound,GreedyProjectBoardItem,GreedyProjectEmployee,GreedyLessonsDigest · 依赖:@/utils/api |
| `admin/src/api/index.ts` | 55 | 依赖:./authPaths,./authRefresh,./core,./emailAuth,./founderOps |
| `admin/src/api/modules/abTest.ts` | 13 | 定义:abTestAPI · 依赖:../core |
| `admin/src/api/modules/agentHub.ts` | 12 | 定义:agentHubAPI · 依赖:../core |
| `admin/src/api/modules/agentTree.ts` | 12 | 定义:agentTreeAPI · 依赖:../core |
| `admin/src/api/modules/aiConfig.ts` | 11 | 定义:aiConfigAPI · 依赖:../core |
| `admin/src/api/modules/aiGenerate.ts` | 8 | 定义:aiGenerateAPI · 依赖:../core |
| `admin/src/api/modules/aiLearning.ts` | 11 | 定义:aiLearningAPI · 依赖:../core |
| `admin/src/api/modules/aiProviderHealth.ts` | 10 | 定义:aiProviderHealthAPI · 依赖:../core |
| `admin/src/api/modules/aiRecommendations.ts` | 11 | 定义:aiRecommendationsAPI · 依赖:../core |
| `admin/src/api/modules/analytics.ts` | 11 | 定义:dataAnalyticsAPI · 依赖:../core |
| `admin/src/api/modules/cases.ts` | 11 | 定义:casesAPI · 依赖:../core |
| `admin/src/api/modules/chatSessions.ts` | 12 | 定义:chatSessionsAPI · 依赖:../core |
| `admin/src/api/modules/churn.ts` | 10 | 定义:churnAPI · 依赖:../core |
| `admin/src/api/modules/cognitive.ts` | 10 | 定义:cognitiveAPI · 依赖:../core |
| `admin/src/api/modules/comments.ts` | 12 | 定义:commentsAPI · 依赖:../core |
| `admin/src/api/modules/compliance.ts` | 12 | 定义:complianceHubAPI · 依赖:../core |
| `admin/src/api/modules/content.ts` | 16 | 定义:contentAPI · 依赖:../core |
| `admin/src/api/modules/contentArchive.ts` | 10 | 定义:contentArchiveAPI · 依赖:../core |
| `admin/src/api/modules/contentMaster.ts` | 11 | 定义:contentMasterAPI · 依赖:../core |
| `admin/src/api/modules/coupons.ts` | 12 | 定义:couponsAPI · 依赖:../core |
| `admin/src/api/modules/developer.ts` | 10 | 定义:developerAPI · 依赖:../core |
| `admin/src/api/modules/domain.ts` | 12 | 定义:domainAPI · 依赖:../core |
| `admin/src/api/modules/edgeCDN.ts` | 12 | 定义:edgeCDNAPI · 依赖:../core |
| `admin/src/api/modules/emailTracking.ts` | 9 | 定义:emailTrackingAPI · 依赖:../core |
| `admin/src/api/modules/emotionCrm.ts` | 10 | 定义:emotionCrmAPI · 依赖:../core |
| `admin/src/api/modules/feishu.ts` | 11 | 定义:feishuAPI · 依赖:../core |
| `admin/src/api/modules/files.ts` | 29 | 定义:filesAPI,formData,formData · 依赖:../core |
| `admin/src/api/modules/globalization.ts` | 10 | 定义:globalizationAPI · 依赖:../core |
| `admin/src/api/modules/growthTools.ts` | 33 | 定义:growthToolsAPI · 依赖:../core |
| `admin/src/api/modules/inquiries.ts` | 10 | 定义:inquiriesAPI · 依赖:../core |
| `admin/src/api/modules/international.ts` | 15 | 定义:internationalAPI · 依赖:../core |
| `admin/src/api/modules/invoices.ts` | 12 | 定义:invoicesAPI · 依赖:../core |
| `admin/src/api/modules/langchain.ts` | 12 | 定义:langchainAPI · 依赖:../core |
| `admin/src/api/modules/license.ts` | 14 | 定义:licenseAPI · 依赖:../core |
| `admin/src/api/modules/logistics.ts` | 11 | 定义:logisticsAPI · 依赖:../core |
| `admin/src/api/modules/mediaFactory.ts` | 11 | 定义:mediaFactoryAPI · 依赖:../core |
| `admin/src/api/modules/merchantProfiles.ts` | 11 | 定义:merchantProfilesAPI · 依赖:../core |
| `admin/src/api/modules/news.ts` | 11 | 定义:newsAPI · 依赖:../core |
| `admin/src/api/modules/notifications.ts` | 13 | 定义:notificationsAPI · 依赖:../core |
| `admin/src/api/modules/orders.ts` | 14 | 定义:ordersAPI · 依赖:../core |
| `admin/src/api/modules/productFaqs.ts` | 10 | 定义:productFaqsAPI · 依赖:../core |
| `admin/src/api/modules/productVariants.ts` | 9 | 定义:productVariantsAPI · 依赖:../core |
| `admin/src/api/modules/products.ts` | 22 | 定义:productsAPI · 依赖:../core |
| `admin/src/api/modules/quotes.ts` | 11 | 定义:quotesAPI · 依赖:../core |
| `admin/src/api/modules/referral.ts` | 12 | 定义:referralAPI · 依赖:../core |
| `admin/src/api/modules/refunds.ts` | 10 | 定义:refundsAPI · 依赖:../core |
| `admin/src/api/modules/reviews.ts` | 14 | 定义:reviewsAPI · 依赖:../core |
| `admin/src/api/modules/seo.ts` | 39 | 定义:seoAPI · 依赖:../core |
| `admin/src/api/modules/seoMatrix.ts` | 136 | 定义:seoMatrixAPI,p,st,scheduled · 依赖:../core |
| `admin/src/api/modules/siteSettings.ts` | 10 | 定义:siteSettingsAPI · 依赖:../core |
| `admin/src/api/modules/sslCertificates.ts` | 10 | 定义:sslCertificatesAPI · 依赖:../core |
| `admin/src/api/modules/superAgent.ts` | 18 | 定义:superAgentAPI · 依赖:../core |
| `admin/src/api/modules/system.ts` | 11 | 定义:systemAPI · 依赖:../core |
| `admin/src/api/modules/systemHealth.ts` | 13 | 定义:systemHealthAPI · 依赖:../core |
| `admin/src/api/modules/tenants.ts` | 11 | 定义:tenantsAPI · 依赖:../core |
| `admin/src/api/modules/tokenLedger.ts` | 11 | 定义:tokenLedgerAPI · 依赖:../core |
| `admin/src/api/modules/ubrain.ts` | 29 | 定义:ubrainAPI · 依赖:../core |
| `admin/src/api/modules/ubrainAnalytics.ts` | 12 | 定义:ubrainAnalyticsAPI · 依赖:../core |
| `admin/src/api/modules/ubrainCommercialOs.ts` | 26 | 定义:ubrainCommercialOsAPI · 依赖:../core |
| `admin/src/api/modules/users.ts` | 10 | 定义:usersAPI · 依赖:../core |
| `admin/src/api/modules/v2ray.ts` | 13 | 定义:v2rayAPI · 依赖:../core |
| `admin/src/api/modules/wallet.ts` | 11 | 定义:walletAPI · 依赖:../core |
| `admin/src/api/modules/withdrawals.ts` | 9 | 定义:withdrawalsAPI · 依赖:../core |
| `admin/src/api/naming.ts` | 60 | 定义:SNAKE_TO_CAMEL,CAMEL_TO_SNAKE_ACRONYM,CAMEL_TO_SNAKE,snakeCaseToCamelCase,camelCaseToSnakeCase,transformKeys,result,newKey |
| `admin/src/api/oauth.ts` | 100 | 定义:OAuthProvider,PROVIDER_LABEL,oauthProviderLabel,OAuthStatePayload,parseOAuthState,normalized,pad,resolveOAuthProvider · 依赖:@/utils/api |
| `admin/src/api/oauthBindings.ts` | 20 | 定义:OAuthBindingRow,fetchOAuthBindings,bindOAuthAccount,unbindOAuthAccount · 依赖:@/api/oauth,@/utils/api |
| `admin/src/api/paperclip.ts` | 210 | 定义:BASE,Company,CompanyDetail,Agent,Goal,Task,HeartbeatLog,Approval · 依赖:@/utils/api |
| `admin/src/api/response.ts` | 14 | 定义:unwrapFetchedJson,body |
| `admin/src/api/system.ts` | 14 | 定义:systemAPI,search,q · 依赖:@/utils/api |
| `admin/src/api/ubrain/conversation.ts` | 95 | 定义:API_BASE,getConversations,response,getConversation,response,createConversation,response,updateConversation · 依赖:@/types/conversation |
| `admin/src/api/ubrain/invitation.ts` | 121 | 定义:Invitation,InvitationStats,GenerateInvitationResponse,API_BASE,generateInvitation,response,getInvitationStats,response |
| `admin/src/api/ubrain/sales.ts` | 275 | 定义:searchCustomers,getCustomerDetail,updateCustomerStatus,exportCustomers,processInquiry,generateQuote,getNegotiations,sendNegotiationMessage · 依赖:@/types/sales,@/utils/api |
| `admin/src/api/ubrain/skill.ts` | 100 | 定义:API_BASE,getSkills,response,getSkillDetail,response,executeSkill,response,getSkillExecutions · 依赖:@/types/skill |
| `admin/src/api/ubrain/task.ts` | 110 | 定义:API_BASE,getTaskStatus,response,cancelTask,response,getTaskResult,response,getTasks · 依赖:@/types/task |
| `admin/src/auth/__tests__/session.test.ts` | 66 | 定义:assign · 依赖:@/auth/session |
| `admin/src/auth/session.ts` | 146 | 定义:AUTH_REDIRECT_GATE_KEY,AUTH_REDIRECT_DEBOUNCE_MS,AUTH_KICKED_GUARD_MS,getCsrfToken,noteCsrfFromHeaders,fromGet,asRecord,raw |
| `admin/src/components.d.ts` | 187 | 定义:GlobalComponents |
| `admin/src/components/DrawerDropdown.vue` | 131 | 组件:DrawerDropdown · props · emits · 定义:props,emit,navItemRef,menuRef,toggleMenu,items |
| `admin/src/components/ExtModulePageShell.vue` | 109 | 组件:ExtModulePageShell · 根:div · props · 定义:props,route,router,nav,hit,isActive,go · 依赖:@/constants/extModuleNav,@/constants/workbenchPathCapabilities |
| `admin/src/components/GlobalSearch.vue` | 345 | 组件:GlobalSearch · 根:Teleport · 定义:FALLBACK_MENU,router,menuIndex,q,idx,inputRef,quickNav,apiResults · 依赖:@/components/youding,@/composables/useGlobalSearch,@/constants/roleShellLock,@/stores/auth,@/utils/flattenMenuNav · ⚑MOCK/DEGRADED |
| `admin/src/components/UBrainAssistant.vue` | 526 | 组件:UBrainAssistant · 根:Teleport · 定义:Msg,router,tenantBrand,ubrainCtx,panel,open,fabPulsing,input · 依赖:@/components/assistant/AssistantMascot.vue,@/composables/useAiRequest,@/composables/useAssistantPanel,@/composables/useFloatingDrag,@/composables/useTenantBrand · ⚑MOCK |
| `admin/src/components/admin/AdminAuditLogTable.vue` | 141 | 组件:AdminAuditLogTable · 根:a-card · props · 定义:AuditRow,loading,rows,actionFilter,resourceFilter,pagination,columns,formatTime · 依赖:@/api,@/components/youding · ⚑MOCK |
| `admin/src/components/agent/AgentTaskTree.vue` | 250 | 组件:AgentTaskTree · 根:div · props · 定义:AgentTaskItem,props,statusLabels,runStatusLabel,runStatusColor,s,progressBarStatus,progressStrokeColor |
| `admin/src/components/assistant/AssistantMascot.vue` | 195 | 组件:AssistantMascot · 根:svg · props · 定义:uid |
| `admin/src/components/client/ClientTodayThreeBoard.vue` | 799 | 组件:ClientTodayThreeBoard · 根:div · 定义:router,moreMenu,openAllFeatures,salesKpi,loadSalesKpi,focusIndex,focusStep,canPrev · 依赖:@/composables/useClientMoreMenu,@/composables/useClientTodayThree,@/utils/api,@/utils/clientUiEdition |
| `admin/src/components/client/ClientTodayThreeStrip.vue` | 161 | 组件:ClientTodayThreeStrip · 根:section · 定义:router,go · 依赖:@/composables/useClientTodayThree |
| `admin/src/components/common/AiSkeleton.vue` | 73 | 组件:AiSkeleton · 根:div · props |
| `admin/src/components/common/CookieConsent.vue` | 181 | 组件:CookieConsent · 根:transition · 定义:STORAGE_KEY,visible,stored,accept,reject |
| `admin/src/components/common/ErrorMessage.vue` | 189 | 组件:ErrorMessage · 根:div · props · emits · 定义:props,emit,iconComponent,iconMap,handleRetry,handleDismiss |
| `admin/src/components/common/LoadingSpinner.vue` | 145 | 组件:LoadingSpinner · props · emits · 定义:props,emit,iconSize,sizeMap,handleCancel · 依赖:./SkeletonCard.vue · ⚑MOCK/DEGRADED |
| `admin/src/components/common/PageDataBar.vue` | 74 | 组件:PageDataBar · 根:div · props · emits · 定义:props,visible · 依赖:@/composables/usePageData |
| `admin/src/components/common/SkeletonCard.vue` | 186 | 组件:SkeletonCard · 根:div · props |
| `admin/src/components/common/TypewriterText.vue` | 136 | 组件:TypewriterText · 根:span · props · emits · 定义:props,emit,shown,typing,reducedMotion,stop,finish,tick |
| `admin/src/components/common/WebSocketStatus.vue` | 142 | 组件:WebSocketStatus · 根:div · props · 定义:props,websocketStore,statusText,statusClass,reconnectAttempts,maxReconnectAttempts,error,handleReconnect · 依赖:@/stores/websocket |
| `admin/src/components/conversation/ConversationList.vue` | 261 | 组件:ConversationList · 根:div · 定义:conversationStore,searchQuery,loading,listRef,currentConversationId,filteredConversations,query,formatTime · 依赖:@/components/common/SkeletonCard.vue,@/stores/conversation,@/utils/index · ⚑MOCK |
| `admin/src/components/conversation/MessageInput.vue` | 244 | 组件:MessageInput · 根:div · props · emits · 定义:props,emit,inputValue,showSkillBar,showEmojiPicker,charCount,canSend,handleKeydown · 依赖:./SkillQuickBar.vue · ⚑MOCK |
| `admin/src/components/conversation/MessageItem.vue` | 295 | 组件:MessageItem · 根:div · props · emits · 定义:props,emit,authStore,userAvatar,formatTime,renderContent,handleCopy,handleRetry · 依赖:@/components/skill/SkillCard.vue,@/components/task/TaskProgress.vue,@/components/task/TaskResult.vue,@/composables/useSanitize,@/stores/auth |
| `admin/src/components/conversation/MessageList.vue` | 141 | 组件:MessageList · 根:div · props · emits · 定义:props,emit,conversationStore,containerRef,listRef,scrollAnchor,loading,itemHeight · 依赖:./MessageItem.vue,@/stores/conversation |
| `admin/src/components/conversation/SkillQuickBar.vue` | 181 | 组件:SkillQuickBar · 根:div · emits · 定义:emit,router,QuickSkill,quickSkills,selectSkill,viewAllSkills |
| `admin/src/components/copilot/CopilotInputArea.vue` | 78 | 组件:CopilotInputArea · 根:form · props · emits · ⚑MOCK |
| `admin/src/components/copilot/CopilotMessageList.vue` | 69 | 组件:CopilotMessageList · 根:div · props · 定义:CopilotMsg,listEl,scrollBottom |
| `admin/src/components/growth/GrowthAutopilotPanel.vue` | 183 | 组件:GrowthAutopilotPanel · 根:div · emits · 定义:emit,historyColumns,handleStart,handleApplyInspect · 依赖:@/components/agent/AgentTaskTree.vue,@/composables/useGrowthAgentRun · ⚑MOCK |
| `admin/src/components/layout/CertWatermark.vue` | 48 | 组件:CertWatermark · 根:a-watermark · 定义:auth,enabled,watermarkLines,user · 依赖:@/constants/stubVisibility,@/stores/auth |
| `admin/src/components/layout/ThemeSettingsDrawer.vue` | 181 | 组件:ThemeSettingsDrawer · 根:a-drawer · 定义:UiAccentRole,UiRadiusScale,UiTableDensity,UiTheme,open,ui,presetColors,hexToRgb · 依赖:@/stores/uiPreferences |
| `admin/src/components/layout/YdCopilotSlot.vue` | 90 | 组件:YdCopilotSlot · 根:aside · props · emits · 定义:emit,router,goAssistant,target |
| `admin/src/components/layout/YdProParentNav.vue` | 127 | 组件:YdProParentNav · 根:nav · props · emits · 定义:props,emit,scroller,el · 依赖:@/components/youding,@/constants/proShellMenus,@/types/shellNav |
| `admin/src/components/layout/YdProSidebar.vue` | 650 | 组件:YdProSidebar · 根:aside · props · emits · 定义:collapsedSubGroups,toggleSubGroup,idx,hasGroupedChildren,groupChildren,groups,g,collapsed · 依赖:@/components/youding,@/types/shellNav |
| `admin/src/components/layout/YdProTopbar.vue` | 404 | 组件:YdProTopbar · 根:header · props · emits · 定义:props,collapsed,copilotOpen,themeDrawerOpen,emit,envMode,envLabel,mode · 依赖:@/components/layout/YdQueueEntry.vue,@/components/youding,@/composables/useGlobalSearch |
| `admin/src/components/layout/YdProWorktabs.vue` | 265 | 组件:YdProWorktabs · 根:div · props · 定义:ui,tabScroller,closableCount,el · 依赖:@/composables/useWorkTabNavigation,@/constants/proShellMenus,@/stores/uiPreferences |
| `admin/src/components/layout/YdQueueEntry.vue` | 67 | 组件:YdQueueEntry · 根:a-dropdown · 定义:router,totalBadge,onMenuClick,mode,paths,path · 依赖:@/composables/useQueueBadges,@/constants/proShellMenus,@/constants/queueEntryPaths |
| `admin/src/components/media/VideoPlayer.vue` | 484 | 组件:VideoPlayer · 根:a-modal · props · emits · 定义:props,emit,modalOpen,videoRef,wrapperRef,isPlaying,isMuted,currentTime · ⚑DEPRECATED |
| `admin/src/components/products/AicaigouCategoryCascade.vue` | 452 | 组件:AicaigouCategoryCascade · 根:div · emits · 定义:AicaigouCategoryPath,emit,tree,searchQuery,selectedL1Id,selectedL2Id,selectedL3Id,recentPaths · 依赖:@/utils/aicaigouCategoryTree · ⚑MOCK |
| `admin/src/components/sales/CustomerDetail.vue` | 313 | 组件:CustomerDetail · 根:div · props · emits · 定义:props,emit,notes,contactHistory,getAvatarColor,getStatusColor,colors,getStatusText · 依赖:@/types/sales · ⚑MOCK |
| `admin/src/components/sales/CustomsBuyerResearchPanel.vue` | 173 | 组件:CustomsBuyerResearchPanel · 根:a-card · 定义:BuyerRow,form,loading,brief,sidecarOk,buyers,rows,columns · 依赖:@/api/foreign-trade,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/components/sales/EmailDetail.vue` | 302 | 组件:EmailDetail · 根:div · props · emits · 定义:props,emit,defaultBody,trackingEvents,formatDate,getStatusColor,colors,getStatusText · 依赖:@/composables/useSanitize,@/types/sales |
| `admin/src/components/site-builder/JtbdSiteChecklist.vue` | 159 | 组件:JtbdSiteChecklist · 根:section · props · 定义:JtbdChecklistItem,props,router,doneCount |
| `admin/src/components/site-builder/SiteEditorGapPanel.vue` | 181 | 组件:SiteEditorGapPanel · 根:div · props · emits · 定义:props,emit,defaultForm,applying,saving,syncFormFromSite,buildPayload,saveDraftOnly · 依赖:@/api/admin-bff,@/components/youding,@/components/youding/formily/siteEditorSchema,@/utils/siteEditorLabSync |
| `admin/src/components/site-builder/SiteEditorLProPublishBanner.vue` | 76 | 组件:SiteEditorLProPublishBanner · 根:a-alert · props · 定义:LProPublishGate,props,gate,base,visual,summary,p0Issues,isLProTemplate · 依赖:../../../../utils/l-pro-publish-gate |
| `admin/src/components/site-builder/SiteEditorRightPanel.vue` | 68 | 组件:SiteEditorRightPanel · 根:aside · props · emits · 定义:props,emit,seoModel,tabOptions,activeTab · 依赖:./SiteEditorGapPanel.vue,./SiteEditorSeoPanel.vue,@/templates/site-builder |
| `admin/src/components/site-builder/SiteEditorSeoPanel.vue` | 228 | 组件:SiteEditorSeoPanel · 根:aside · props · emits · 定义:WEBMASTER_HINTS,props,emit,serpUrl,webmasterHint,sampleIndexedUrl,base,lang · 依赖:@/components/youding,@/components/youding/formily/siteEditorSeoSchema,@/templates/site-builder · ⚑MOCK |
| `admin/src/components/site-builder/SiteTemplatePickerModal.vue` | 377 | 组件:SiteTemplatePickerModal · 根:a-modal · emits · 定义:SiteBuilderTemplateId,SiteThemeMode,open,selectedId,accent,emit,GROUPS,templatesOf · 依赖:@/templates/site-builder |
| `admin/src/components/site-builder/YdGrapesSiteEditor.vue` | 265 | 组件:YdGrapesSiteEditor · 根:div · props · emits · 定义:props,emit,containerRef,device,onInsertBlock,onDeviceChange,syncFromStructured,applyTemplate · 依赖:@/composables/useGrapesSiteEditor,@/templates/site-builder |
| `admin/src/components/skill/SkillCard.vue` | 238 | 组件:SkillCard · 根:div · props · emits · 定义:props,emit,skillStore,isFavorited,isExecuting,skillData,skillName,skillDescription · 依赖:@/stores/skill,@/types/skill |
| `admin/src/components/skill/SkillDetail.vue` | 272 | 组件:SkillDetail · 根:div · props · emits · 定义:props,emit,executing,loadingHistory,executionHistory,formState,fileList,skillIcon · 依赖:@/composables/useSkill,@/types/skill,@/utils/index · ⚑MOCK |
| `admin/src/components/skill/SkillGrid.vue` | 219 | 组件:SkillGrid · 根:div · props · emits · 定义:props,emit,router,skillStore,searchQuery,selectedCategory,currentPage,displaySkills · 依赖:./SkillCard.vue,@/components/common/SkeletonCard.vue,@/stores/skill,@/types/skill · ⚑MOCK |
| `admin/src/components/task/TaskProgress.vue` | 208 | 组件:TaskProgress · 根:div · props · emits · 定义:props,emit,statusType,typeMap,statusText,textMap,progressStatus,statusMap |
| `admin/src/components/task/TaskResult.vue` | 397 | 组件:TaskResult · 根:div · props · emits · 定义:props,emit,resultTypeColor,colorMap,resultTypeText,textMap,customerColumns,formatExecutionTime · 依赖:@/composables/useSanitize,@/types/task |
| `admin/src/components/task/TaskStatus.vue` | 259 | 组件:TaskStatus · 根:div · props · emits · 定义:props,emit,statusIcon,iconMap,statusClass,statusTitle,titleMap,formatTime · 依赖:./TaskProgress.vue,@/types/task,@/utils/index |
| `admin/src/components/tenant/AitoearnCapabilityBar.vue` | 97 | 组件:AitoearnCapabilityBar · 根:a-alert · 定义:CapModules,loaded,enabled,platforms,modules,slotAssigned,alertType,headline · 依赖:@/utils/api |
| `admin/src/components/tenant/OnboardingAutopilotProgress.vue` | 117 | 组件:OnboardingAutopilotProgress · 根:div · props · 定义:props,displaySteps,percent,done,total,stepIcon,stepColor,stepStatus · 依赖:@/utils/onboardingAutopilot |
| `admin/src/components/tenant/OnboardingExternalAccountsPanel.vue` | 177 | 组件:OnboardingExternalAccountsPanel · 根:div · 定义:ExternalAccountItem,ExternalPhase,Preview,router,loading,phases,preview,activePhases · 依赖:@/components/common/SkeletonCard.vue,@/utils/api |
| `admin/src/components/tenant/OnboardingImContactsPanel.vue` | 222 | 组件:OnboardingImContactsPanel · 根:div · emits · 定义:ImTool,emit,tools,saving,focusField,form,guideBubble,map · 依赖:@/components/tenant/OnboardingWangcaiGuide.vue,@/utils/api · ⚑MOCK |
| `admin/src/components/tenant/OnboardingPlainRoadmap.vue` | 97 | 组件:OnboardingPlainRoadmap · 根:div · props · 定义:RoadmapChecklistItem,RoadmapPhase,router,statusKind,go · 依赖:@/components/youding |
| `admin/src/components/tenant/OnboardingPlatformBind.vue` | 156 | 组件:OnboardingPlatformBind · 根:a-modal · props · emits · 定义:PlatformSlot,props,emit,visible,saving,slot,form,loadSlot · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/components/tenant/OnboardingWangcaiGuide.vue` | 184 | 组件:OnboardingWangcaiGuide · 根:div · props · 定义:props,nodding,peeking,pointing |
| `admin/src/components/tenant/OnboardingWangcaiPanel.vue` | 170 | 组件:OnboardingWangcaiPanel · 根:div · props · emits · 定义:WangcaiPrompt,props,emit,prompts,messages,input,loading,disclaimer · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/components/tenant/PublishReadinessBar.vue` | 161 | 组件:PublishReadinessBar · 根:section · emits · 定义:ReadinessAction,PublishReadiness,emit,loading,data,egressOk,q,a · 依赖:@/components/common/SkeletonCard.vue,@/utils/api |
| `admin/src/components/tenant/TenantOnboardingChecklist.vue` | 93 | 组件:TenantOnboardingChecklist · 根:div · props · 定义:ChecklistItem,props,doneCount,statusKind,linkFor,map,linkLabel,map · 依赖:@/components/youding |
| `admin/src/components/tenant/VideoPublishBindHub.vue` | 298 | 组件:VideoPublishBindHub · 根:section · emits · 定义:SauBind,HubPlatform,BindHub,emit,hub,loading,syncing,sauChecking · 依赖:@/utils/api |
| `admin/src/components/tenants/TenantCommerceTabs.vue` | 42 | 组件:TenantCommerceTabs · 根:div · 定义:route,router,tabs,active,p,hit,onChange,path |
| `admin/src/components/tenants/TenantOnboardTabs.vue` | 60 | 组件:TenantOnboardTabs · 根:div · 定义:route,router,tabs,showTabs,pinia,active,p,onChange |
| `admin/src/components/traffic/TrafficBoardPanel.vue` | 602 | 组件:TrafficBoardPanel · 根:div · props · 定义:props,router,period,loading,error,board,detailOpen,detailKind · 依赖:@/components/youding,@/utils/api |
| `admin/src/components/whatsfinds/AppTabs.vue` | 390 | 组件:AppTabs · 根:div · props · emits · 定义:AppTab,Props,props,emit,router,tabsWrapperRef,tabsListRef,showScrollBtn |
| `admin/src/components/whatsfinds/EvidenceChain.vue` | 307 | 组件:EvidenceChain · 根:a-card · props · 定义:Evidence,Props,getEvidenceColor,colors,getEvidenceIcon,icons,getEvidenceTypeLabel,labels |
| `admin/src/components/whatsfinds/ScoreRadar.vue` | 242 | 组件:ScoreRadar · 根:a-card · props · 定义:ScoreItem,Props,props,chartRef,scoreItems,renderChart,option,esc |
| `admin/src/components/whatsfinds/SearchSyntaxPreview.vue` | 326 | 组件:SearchSyntaxPreview · 根:a-card · props · emits · 定义:Props,props,emit,copied,customerTypeMap,searchSources,generatedSyntax,parts |
| `admin/src/components/whatsfinds/TenantAiConfig.vue` | 475 | 组件:TenantAiConfig · 根:a-card · 定义:AiProviderConfig,AiProvider,loading,saving,configs,providers,showAddModal,editingConfig · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/components/youding/CoachProPageShell.vue` | 63 | 组件:CoachProPageShell · 根:YdPage · props · 定义:props,showTopbar,variantClass · 依赖:./YdPage.vue |
| `admin/src/components/youding/LoginFeatureIcon.vue` | 45 | 组件:LoginFeatureIcon · 根:span · props · 定义:props,GLYPH_PATHS,path |
| `admin/src/components/youding/LoginOAuthButtons.vue` | 164 | 组件:LoginOAuthButtons · 根:div · props · emits · 定义:props,emit,providers,isAvailable,buttonTitle · 依赖:@/api/oauth |
| `admin/src/components/youding/TenantLoginPanel.vue` | 166 | 组件:TenantLoginPanel · 根:aside · props · 依赖:./LoginFeatureIcon.vue,@/constants/loginPortalCopy |
| `admin/src/components/youding/YdCheckMark.vue` | 44 | 组件:YdCheckMark · 根:span · props |
| `admin/src/components/youding/YdClientPlanUsageBar.vue` | 111 | 组件:YdClientPlanUsageBar · 根:div · 定义:router,usageHint,goBilling · 依赖:./YdUsageMeter.vue,@/composables/useClientPlanSnapshot |
| `admin/src/components/youding/YdDataTable.vue` | 121 | 组件:YdDataTable · 根:a-table · props · emits · 定义:props,emit,ui,mergedProps,tablePagination,onChange · 依赖:@/composables/useYdTable,@/stores/uiPreferences |
| `admin/src/components/youding/YdEmptyState.vue` | 75 | 组件:YdEmptyState · 根:div · props · emits · 定义:props,presets,preset,icon,displayTitle,displayDesc,displayCta |
| `admin/src/components/youding/YdFinanceNav.vue` | 179 | 组件:YdFinanceNav · 根:nav · 定义:items,router,route,isActive,go |
| `admin/src/components/youding/YdFormilyForm.vue` | 62 | 组件:YdFormilyForm · 根:FormProvider · props · emits · 定义:props,emit,form · 依赖:./formily/antdv-bridge |
| `admin/src/components/youding/YdGreedyNav.vue` | 73 | 组件:YdGreedyNav · 根:nav · 定义:items,router,route,isActive,go |
| `admin/src/components/youding/YdHonestDataBanner.vue` | 126 | 组件:YdHonestDataBanner · 根:a-alert · props · 定义:HonestLevel,props,router,dismissed,preset,alertType,bannerTitle,bannerDescription · ⚑MOCK/DEGRADED |
| `admin/src/components/youding/YdIllustration.vue` | 39 | 组件:YdIllustration · 根:div · props · 依赖:./YdReliefIcon.vue,@/constants/antIconMap |
| `admin/src/components/youding/YdMetricCard.vue` | 83 | 组件:YdMetricCard · 根:div · props · emits · 定义:props,emit,router,isClickable,displayValue,toneColors,valueStyle,onClick |
| `admin/src/components/youding/YdNavIcon.vue` | 17 | 组件:YdNavIcon · 根:YdReliefIcon · props · 依赖:./YdReliefIcon.vue,@/constants/antIconMap |
| `admin/src/components/youding/YdOnboardingCard.vue` | 69 | 组件:YdOnboardingCard · 根:div · props · 定义:props,router,currentStep,idx,activeId,ctaRoute,goCta · 依赖:./types |
| `admin/src/components/youding/YdPage.vue` | 36 | 组件:YdPage · 根:div · props · 定义:props,pageClass · 依赖:./YdPageHeader.vue |
| `admin/src/components/youding/YdPageHeader.vue` | 54 | 组件:YdPageHeader · 根:div · props |
| `admin/src/components/youding/YdReliefIcon.vue` | 98 | 组件:YdReliefIcon · 根:span · props |
| `admin/src/components/youding/YdSchemaForm.vue` | 86 | 组件:YdSchemaForm · 根:a-form · props · emits · 定义:props,emit,buildDefaults,base,model · 依赖:./types · ⚑MOCK |
| `admin/src/components/youding/YdSearchBar.vue` | 42 | 组件:YdSearchBar · 根:div · emits |
| `admin/src/components/youding/YdStatsCard.vue` | 136 | 组件:YdStatsCard · 根:div · props · emits · 定义:props,emit,router,isClickable,handleClick,parsed,countDisplay,shownValue · 依赖:@/composables/useCountUp |
| `admin/src/components/youding/YdStatsRow.vue` | 27 | 组件:YdStatsRow · 根:div · props |
| `admin/src/components/youding/YdTableColumnSettings.vue` | 81 | 组件:YdTableColumnSettings · 根:a-popover · props · emits · 依赖:@/composables/useYoudingTableBridge |
| `admin/src/components/youding/YdTableToolbar.vue` | 88 | 组件:YdTableToolbar · 根:div · props · emits · 定义:props,ui,fullscreen,densityOptions,densityModel,onDensityChange,toggleFullscreen,el · 依赖:@/stores/uiPreferences |
| `admin/src/components/youding/YdTodayQueue.vue` | 138 | 组件:YdTodayQueue · 根:div · props · emits · 定义:props,emit,displayItems,onRowClick · 依赖:./types |
| `admin/src/components/youding/YdTodayWorkbench.vue` | 255 | 组件:YdTodayWorkbench · 根:section · props · emits · 定义:WorkbenchTile,props,emit,planTagColor,n,planExpiryLabel,d,usageHint · 依赖:./YdTodayQueue.vue,./YdUsageMeter.vue,./types |
| `admin/src/components/youding/YdUsageMeter.vue` | 84 | 组件:YdUsageMeter · 根:div · props · 定义:props,clampedPct,pctDisplay,tone |
| `admin/src/components/youding/YdWorkspaceHeader.vue` | 78 | 组件:YdWorkspaceHeader · 根:header · props · 依赖:./YdUsageMeter.vue |
| `admin/src/components/youding/formily/antdv-bridge.ts` | 52 | 定义:asField,FormItem,f,Input,TextArea,FormilySelect,f,FormilySwitch |
| `admin/src/components/youding/formily/siteEditorSchema.ts` | 196 | 定义:siteEditorFormilySchema · 依赖:@/constants/lProTier1Locales · ⚑MOCK/STUB |
| `admin/src/components/youding/formily/siteEditorSeoSchema.ts` | 95 | 定义:siteEditorSeoSchema · ⚑MOCK |
| `admin/src/components/youding/index.ts` | 30 | 依赖:./CoachProPageShell.vue,./LoginOAuthButtons.vue,./TenantLoginPanel.vue,./YdCheckMark.vue,./YdClientPlanUsageBar.vue |
| `admin/src/components/youding/types.ts` | 27 | 定义:OnboardingStep,QueueItem,YdSchemaField · ⚑MOCK |
| `admin/src/composables/__tests__/useEffectivePlatformRole.test.ts` | 101 | 依赖:../useEffectivePlatformRole · ⚑MOCK |
| `admin/src/composables/useAdminWorkspace.ts` | 99 | 定义:STORAGE_KEY,WorkspaceScript,WorkspaceWorkflow,WorkspaceTicket,WorkspaceSnippet,WorkspaceAiTask,WorkspaceSchedulerSlot,WorkspaceState |
| `admin/src/composables/useAiConnect.ts` | 91 | 定义:NvidiaProbeSummary,AiConnectStatus,FREE_NVIDIA_ALERT_TITLE,FREE_NVIDIA_NOTICE,NVIDIA_USAGE_POLICY_NOTICE,useAiConnect,aiConnect,loading · 依赖:@/utils/api · ⚑DEGRADED |
| `admin/src/composables/useAiRequest.ts` | 204 | 定义:AiPhase,AiRequestOptions,splitRevealChunks,parts,chunks,prefersReducedMotion,AiRequestHandle,defaultSseDelta |
| `admin/src/composables/useAssistantPanel.ts` | 19 | 定义:panelOpen,useAssistantPanel |
| `admin/src/composables/useBoardDetailDrawer.ts` | 64 | 定义:useBoardDetailDrawer,detailOpen,detailKind,detailRecord,detailTitleOverride,detailTitle,map,detailRows |
| `admin/src/composables/useClientMoreMenu.spec.ts` | 31 | 定义:store · 依赖:./useClientMoreMenu |
| `admin/src/composables/useClientMoreMenu.ts` | 43 | 定义:CLIENT_MORE_HINT_STORAGE_KEY,ClientMoreMenuApi,CLIENT_MORE_MENU_KEY,readMoreHintDismissed,writeMoreHintDismissed,provideClientMoreMenu,useClientMoreMenu |
| `admin/src/composables/useClientPlanSnapshot.ts` | 85 | 定义:ClientPlanSnapshot,snapshot,planTagColor,formatExpiry,d,days,useClientPlanSnapshot,aiPct |
| `admin/src/composables/useClientTodayThree.ts` | 108 | 定义:TodayThreeStep,TodayThreeWeekly,TodayThreePayload,payload,loading,error,ready,useClientTodayThree · 依赖:@/utils/api |
| `admin/src/composables/useCodeGenerator.ts` | 120 | 定义:CodeLanguage,LANGUAGE_LABEL,CodeSnippetTemplate,SNIPPETS,res,buildStub,hint,blocks · ⚑STUB |
| `admin/src/composables/useConversation.ts` | 168 | 定义:useConversation,conversationStore,loading,error,conversations,currentConversation,currentMessages,currentConversationId · 依赖:@/api/ubrain/conversation,@/stores/conversation,@/types/conversation |
| `admin/src/composables/useCountUp.ts` | 84 | 定义:UseCountUpOptions,resolveOption,easeOutCubic,useCountUp,display,duration,run,enabled · ⚑DEGRADED |
| `admin/src/composables/useDevBackendProbe.ts` | 48 | 定义:useDevBackendProbe,backendDown,lastCheckedAt,probe,seq,res,onVisibilityChange |
| `admin/src/composables/useEffectivePlatformRole.ts` | 24 | 定义:useEffectivePlatformRole,auth,role,roleLabel,workbenchTitle,needsDevRelogin · 依赖:@/constants/platformRoleDisplay,@/stores/auth |
| `admin/src/composables/useFloatingDrag.ts` | 133 | 定义:STORAGE_KEY,DRAG_THRESHOLD,Point,readSaved,raw,p,FloatingDragOptions,useFloatingDrag |
| `admin/src/composables/useGlobalSearch.ts` | 25 | 定义:paletteOpen,useGlobalSearch,openSearch,closeSearch,toggleSearch |
| `admin/src/composables/useGrapesSiteEditor.ts` | 138 | 定义:SiteBuilderTemplateId,SiteContentSnapshot,VisualEditorPayload,useGrapesSiteEditor,editor,ready,templateId,initEditor · 依赖:@/templates/site-builder,@/templates/site-builder/grapesjsLocaleZh,@/templates/site-builder/localizeGrapesEditor,@/templates/site-builder/registerYoudingBlocks · ⚑DEGRADED |
| `admin/src/composables/useGrowthAgentRun.ts` | 534 | 定义:AGENT_POLL_MS,GrowthPreset,useGrowthAgentRun,router,route,presets,runHistory,agentGoal · 依赖:@/api |
| `admin/src/composables/useModuleTabSync.ts` | 63 | 定义:useModuleTabSync,router,route,keySet,pathToTab,tail,tabToPath,tab |
| `admin/src/composables/usePageData.ts` | 45 | 定义:PageDataMode,UsePageDataResult,usePageData,data,loading,mode,error,load · 依赖:@/utils/api |
| `admin/src/composables/usePlanPayment.ts` | 217 | 定义:FEATURE_LABELS,featureList,raw,displayPlanPrice,amount,usePlanPayment,plans,plansLoading · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/composables/useQueueBadges.ts` | 72 | 定义:QueueBadgeState,useQueueBadges,badges,loadInquiryCount,raw,loadPublishCount,raw,loadFulfillmentCount · 依赖:@/utils/api,@/utils/ydTableUtils |
| `admin/src/composables/useRumBeacon.ts` | 62 | 定义:sendBeacon,body,url,useRumBeacon,po,d,flush · 依赖:@/utils/api |
| `admin/src/composables/useSanitize.ts` | 26 | 定义:useSanitize,sanitizeHtml · ⚑DEGRADED |
| `admin/src/composables/useShellNavigation.ts` | 38 | 定义:useShellNavigation,route,activeMenuPath,isNavItemActive,isNavDescendantActive,resolveNavTitle · 依赖:@/types/shellNav,@/utils/shellNavKernel |
| `admin/src/composables/useSkill.ts` | 178 | 定义:useSkill,skillStore,loading,error,skills,currentSkill,coreSkills,accioWorkSkills · 依赖:@/api/ubrain/skill,@/stores/skill,@/types/skill |
| `admin/src/composables/useTask.ts` | 212 | 定义:useTask,taskStore,loading,error,tasks,currentTask,pendingTasks,runningTasks · 依赖:@/api/ubrain/task,@/stores/task,@/types/task |
| `admin/src/composables/useTenantBrand.ts` | 172 | 定义:TenantBrandContext,TENANT_BRAND_KEY,fetchBootstrap,tk,headers,res,body,data · 依赖:@/constants/sales-assistant-brand,@/utils/api,@/utils/tenantSitePreview |
| `admin/src/composables/useUbrainChatContext.ts` | 42 | 定义:StrategyItem,useUbrainChatContext,lastStrategies,applyReply,strategies,Turn,buildBody,body |
| `admin/src/composables/useUndoDelete.ts` | 103 | 定义:UndoDeleteOptions,pendingUndos,useUndoDelete,deleteWithUndo,seconds,undoId,undoFn,key |
| `admin/src/composables/useWebSocket.ts` | 150 | 定义:useWebSocket,websocketStore,client,isConnected,messageHandlers,connect,disconnect,send · 依赖:@/stores/websocket,@/types/websocket,@/utils/websocket |
| `admin/src/composables/useWorkTabNavigation.ts` | 57 | 定义:useWorkTabNavigation,router,workTabs,go,auth,shell,target,current · 依赖:@/constants/proShellMenus,@/constants/workbenchPathCapabilities,@/stores/auth,@/stores/workTabs,@/utils/workTabPath |
| `admin/src/composables/useYdTable.ts` | 78 | 定义:YdTablePagination,UseYdTableOptions,UseYdTableReturn,useYdTable,loading,rows,filters,pagination · 依赖:@/utils/ydTableUtils |
| `admin/src/composables/useYoudingTable.spec.ts` | 43 | 定义:calls,table,table · 依赖:../../../youding-admin-kit/composables/useYoudingTable |
| `admin/src/composables/useYoudingTableBridge.ts` | 20 | 定义:UseYoudingTableOptions,YoudingTableColumn,YoudingTableFetcher · 依赖:../../../youding-admin-kit/composables/useYoudingColumnLayout,../../../youding-admin-kit/composables/useYoudingTable |
| `admin/src/constants/__tests__/proShellMenus.clientPrimary.spec.ts` | 40 | 定义:primary,morePaths,all · 依赖:@/constants/proShellMenus |
| `admin/src/constants/__tests__/queueEntryPaths.test.ts` | 20 | 定义:paths,paths · 依赖:@/constants/queueEntryPaths |
| `admin/src/constants/agentLevelBlueprint.ts` | 155 | 定义:AgentLevelBackendModule,AgentLevelBlueprint,AGENT_LEVEL_BLUEPRINTS,blueprintForLevel · 依赖:@/stores/agentCapabilities |
| `admin/src/constants/antIconMap.ts` | 305 | 定义:antIconMap,resolveAntIcon,routeIconByPath,iconNameForPath |
| `admin/src/constants/assistant-mascot.ts` | 6 | 定义:ASSISTANT_MASCOT |
| `admin/src/constants/brandTheme.ts` | 43 | 定义:BRAND,ROLE_ACCENTS,ROLE_ACCENTS_DARK,ROLE_ACCENT_HOVERS_DARK |
| `admin/src/constants/countryOptions.ts` | 22 | 定义:COUNTRY_OPTIONS |
| `admin/src/constants/designPageRouteRegistry.ts` | 115 | 定义:DESIGN_PAGE_TO_CLIENT_PATH,DESIGN_PAGE_IDS_WITHOUT_CLIENT_PATH,resolveDesignPageClientPath,normalized |
| `admin/src/constants/designPreviewPages.ts` | 187 | 定义:DesignPreviewPage,TITLE_MAP,DESIGN_PREVIEW_PAGE_IDS,humanize,listDesignPreviewPages,meta,designPreviewPageById |
| `admin/src/constants/extModuleNav.ts` | 154 | 定义:ExtModuleNavLink,ExtModuleNavConfig,COMMON_RELATED,cfg,EXT_MODULE_NAV_BY_PREFIX,resolveExtModuleNav,loc |
| `admin/src/constants/iconCatalog.ts` | 223 | 定义:ARCH_COMPONENT_ICONS,archComponentIconName,ROLE_ICONS,roleIconName,BUSINESS_MODULE_ICONS,businessModuleIconName,SYSTEM_LAYER_ICONS,systemLayerIconName |
| `admin/src/constants/lProTier1Locales.ts` | 21 | 定义:L_PRO_TIER1_LOCALES,L_PRO_TIER1_SELECT_OPTIONS |
| `admin/src/constants/loginPortalCopy.ts` | 59 | 定义:LoginPortalFeature,LoginPortalCopy,PLATFORM_LOGIN_COPY,LOGIN_PATH,loginPortalPath · 依赖:@/constants/roleShellLock |
| `admin/src/constants/navRouteRegistry.ts` | 184 | 定义:NavRoute,NAV_ROUTE_MAP,NAV_PATH_TO_KEY_MAP,getRouteFromKey,getKeyFromPath,isValidNavKey,isValidNavPath,ALL_NAV_KEYS |
| `admin/src/constants/platformRoleDisplay.ts` | 44 | 定义:PlatformJwtRole,platformRoleLabel,platformWorkbenchTitle,isDevPlatformSuperAccount,effectivePlatformRole |
| `admin/src/constants/platformShellMenu.aiGreedy.spec.ts` | 28 | 定义:Nav,walkLeaves,leaves,group,hub · 依赖:@/constants/platformShellMenu |
| `admin/src/constants/platformShellMenu.ts` | 166 | 定义:PlatformMenuNavItem,PLATFORM_SUPER_GROUP_TITLES,getPlatformOpsMenuItems,out,walk,PLATFORM_SHELL_MENU · 依赖:@/constants/stubVisibility,@/types/shellNav |
| `admin/src/constants/proShellMenus.ts` | 197 | 定义:ProShellNavItem,ProShellMenuGroup,CLIENT_SHELL_MENU,AGENT_SHELL_MENU,PARTNER_SHELL_MENU,filterHiddenClientItems,CLIENT_PRIMARY_SHELL_PATHS,CLIENT_COLLAPSED_MENU_GROUPS · 依赖:@/constants/stubVisibility |
| `admin/src/constants/productImageSpace.ts` | 21 | 定义:PRODUCT_IMAGE_SPACE_TITLE,PRODUCT_IMAGE_SPACE_SUBTITLE,PRODUCT_IMAGE_SPACE_PATH_ADMIN,PRODUCT_IMAGE_SPACE_PATH_CLIENT,productImageSpacePath · 依赖:@/constants/tenantMediaSpace |
| `admin/src/constants/queueEntryPaths.ts` | 23 | 定义:QueueEntryKey,QueueEntryPaths,resolveQueueEntryPaths · 依赖:@/constants/proShellMenus |
| `admin/src/constants/roleShellLock.ts` | 250 | 定义:ROLE_SHELL_LOCK_ID,RoleShellTier,RoleShellNavDecision,LEGACY_WORKTAB_STORAGE_KEY,WORKTAB_KEYS,TENANT_LEGACY_REDIRECTS,PLATFORM_LEGACY_REDIRECTS,PARTNER_FROM_AGENT · 依赖:@/constants/proShellMenus,@/constants/stubVisibility,@/constants/workbenchPathCapabilities,@/utils/clientUiEdition · ⚑DEGRADED |
| `admin/src/constants/sales-assistant-brand.ts` | 89 | 定义:FEATURE,DEFAULT_COMPANY,normalizeCompanyName,t,assistantIntroLine,co,assistantGreeting,co |
| `admin/src/constants/stubVisibility.labCert.spec.ts` | 80 | 定义:CERT_KEY,LAB_KEY,CERT_MIGRATED,items,items,blocked · 依赖:@/constants/stubVisibility |
| `admin/src/constants/stubVisibility.ts` | 389 | 定义:StubStrategy,shellCertMode,shellLabMode,refreshShellFlagsFromStorage,StubRouteRule,CLIENT_STUB_RULES,CLIENT_HIDDEN,CLIENT_LAB_GATED · ⚑MOCK |
| `admin/src/constants/tenantMediaSpace.ts` | 73 | 定义:TenantMediaSpaceKind,TenantMediaSpaceConfig,TENANT_IMAGE_SPACE,TENANT_VIDEO_SPACE,SPACE_BY_KIND,resolveTenantMediaSpaceFromRoute,kind,tenantMediaSpacePath |
| `admin/src/constants/workbenchCapabilityRegistry.ts` | 777 | 定义:WorkbenchTone,WorkbenchItemDef,WorkbenchSectionDef,WORKBENCH_CAPABILITY_REGISTRY,allCapabilityIds |
| `admin/src/constants/workbenchIcons.ts` | 128 | 定义:WORKBENCH_ICONS |
| `admin/src/constants/workbenchPathCapabilities.ts` | 49 | 定义:normalizeLocationPath,raw,trimmed,getWorkbenchPathCapabilityPairsSorted,pairs,resolveCapabilityIdForPath,loc,isCapabilityGuardBypassPath · 依赖:@/constants/workbenchCapabilityRegistry |
| `admin/src/data/aicaigouCategoryTree.ts` | 327 | 定义:AicaigouCategoryNode,AICAIGOU_CATEGORY_TREE |
| `admin/src/layout/ClientShellLayout.vue` | 658 | 组件:ClientShellLayout · 根:div · 定义:ClientUiEdition,router,route,auth,uiPrefs,mobileOpen,moreOpen,moreQuery · 依赖:@/components/UBrainAssistant.vue,@/components/youding,@/composables/useClientMoreMenu,@/composables/useTenantBrand,@/constants/proShellMenus · ⚑MOCK |
| `admin/src/layout/index.vue` | 870 | 组件:index · 根:CertWatermark · 定义:ShellMode,isMobile,collapsed,showThemeDrawer,copilotOpen,onResize,wasMobile,router · 依赖:@/components/GlobalSearch.vue,@/components/UBrainAssistant.vue,@/components/layout/CertWatermark.vue,@/components/layout/ThemeSettingsDrawer.vue,@/components/layout/YdCopilotSlot.vue · ⚑MOCK/STUB/DEGRADED |
| `admin/src/main.ts` | 45 | 定义:_origError,app,pinia · 依赖:./App.vue,./router,@/stores/auth,@/stores/uiPreferences |
| `admin/src/router/adminRoutes.ts` | 65 | 定义:adminRoutes,routes · 依赖:./modules/adminPanelRoutes,./modules/agentHubRoutes,./modules/agentObservabilityRoutes,./modules/aiLearningRoutes,./modules/cognitiveRoutes |
| `admin/src/router/agentRoutes.ts` | 32 | 定义:agentRoutes |
| `admin/src/router/clientRoutes.ts` | 264 | 定义:clientRoutes · 依赖:@/router/generated-crud-routes,@/utils/clientUiEdition,@/views/tenants/site-editor.vue |
| `admin/src/router/commonRoutes.ts` | 154 | 定义:commonRoutes,pm,tail · 依赖:@/constants/loginPortalCopy |
| `admin/src/router/generated-crud-routes.ts` | 77 | 定义:generatedCrudRoutes |
| `admin/src/router/index.ts` | 191 | 定义:routes,router,resolvePostLoginRedirect,auth,loc,loginPaths,role,shellDecision · 依赖:./adminRoutes,./agentRoutes,./clientRoutes,./commonRoutes,./partnerRoutes · ⚑MOCK |
| `admin/src/router/modules/adminAiRoutes.ts` | 178 | 定义:adminAiRoutes |
| `admin/src/router/modules/adminBizRoutes.ts` | 76 | 定义:adminBizRoutes |
| `admin/src/router/modules/adminFinanceRoutes.ts` | 81 | 定义:adminFinanceRoutes |
| `admin/src/router/modules/adminOpsRoutes.ts` | 117 | 定义:adminOpsRoutes |
| `admin/src/router/modules/adminOverviewRoutes.ts` | 75 | 定义:adminOverviewRoutes |
| `admin/src/router/modules/adminPanelRoutes.ts` | 51 | 定义:adminPanelRoutes · 依赖:./adminAiRoutes,./adminBizRoutes,./adminFinanceRoutes,./adminOpsRoutes,./adminOverviewRoutes |
| `admin/src/router/modules/adminSystemRoutes.ts` | 232 | 定义:adminSystemRoutes |
| `admin/src/router/modules/adminToolsRoutes.ts` | 147 | 定义:adminToolsRoutes |
| `admin/src/router/modules/agentHubRoutes.ts` | 43 | 定义:agentHubRoutes |
| `admin/src/router/modules/agentObservabilityRoutes.ts` | 16 | 定义:agentObservabilityRoutes |
| `admin/src/router/modules/aiLearningRoutes.ts` | 43 | 定义:aiLearningRoutes |
| `admin/src/router/modules/cognitiveRoutes.ts` | 43 | 定义:cognitiveRoutes |
| `admin/src/router/modules/dashboardRoutes.ts` | 52 | 定义:dashboardRoutes |
| `admin/src/router/modules/developerRoutes.ts` | 43 | 定义:developerRoutes |
| `admin/src/router/modules/edgeCdnRoutes.ts` | 43 | 定义:edgeCdnRoutes |
| `admin/src/router/modules/globalizationRoutes.ts` | 43 | 定义:globalizationRoutes |
| `admin/src/router/modules/internationalRoutes.ts` | 21 | 定义:internationalRoutes |
| `admin/src/router/modules/logisticsRoutes.ts` | 49 | 定义:logisticsRoutes |
| `admin/src/router/modules/mediaFactoryRoutes.ts` | 55 | 定义:mediaFactoryRoutes |
| `admin/src/router/modules/productRoutes.ts` | 28 | 定义:productRoutes |
| `admin/src/router/modules/referralRoutes.ts` | 36 | 定义:referralRoutes |
| `admin/src/router/modules/salesRoutes.ts` | 130 | 定义:salesRoutes |
| `admin/src/router/modules/seoMatrixRoutes.ts` | 67 | 定义:seoMatrixRoutes |
| `admin/src/router/modules/seoRoutes.ts` | 131 | 定义:seoRoutes |
| `admin/src/router/modules/seoStandaloneRoutes.ts` | 19 | 定义:seoStandaloneRoutes |
| `admin/src/router/modules/settingsRoutes.ts` | 83 | 定义:settingsRoutes |
| `admin/src/router/modules/systemHealthRoutes.ts` | 43 | 定义:systemHealthRoutes |
| `admin/src/router/modules/tenantRoutes.ts` | 72 | 定义:tenantRoutes · 依赖:@/views/tenants/site-editor.vue |
| `admin/src/router/partnerRoutes.ts` | 22 | 定义:partnerRoutes |
| `admin/src/shims-vue.d.ts` | 5 | 定义:component |
| `admin/src/stores/__tests__/auth.test.ts` | 145 | 定义:bffLoginMock,bffLogoutMock,bffUserInfoMock,auth,auth,auth,auth,auth · 依赖:../auth · ⚑MOCK |
| `admin/src/stores/agentCapabilities.ts` | 169 | 定义:AGENT_LEVEL_IDS,AgentLevelId,AGENT_LEVEL_LABELS,LS_GRANTS,LS_LEVEL,LS_SESSION_MANUAL,defaultGrants,all · 依赖:@/constants/workbenchCapabilityRegistry,@/utils/api,@/utils/jwtPayload,@/utils/sessionAuth · ⚑DEGRADED |
| `admin/src/stores/agentObservability.ts` | 146 | 定义:AgentRunSummary,RunDetailPayload,FunnelMetrics,RunQuery,FunnelQuery,DEFAULT_QUERY,useAgentObservabilityStore,runs · 依赖:@/api/agentObservability |
| `admin/src/stores/auth.ts` | 389 | 定义:User,UserPreferences,COOKIE_AUTH_SENTINEL,invalidateAuthInit,wipeJwtStorage,useAuthStore,token,refreshToken · 依赖:@/api/admin-bff,@/api/authRefresh,@/api/emailAuth,@/api/oauth,@/auth/session · ⚑DEGRADED/DEPRECATED |
| `admin/src/stores/conversation.ts` | 158 | 定义:useConversationStore,conversations,currentConversationId,messages,loading,error,currentConversation,currentMessages · 依赖:@/types/conversation |
| `admin/src/stores/index.ts` | 23 | 依赖:./agentCapabilities,./auth,./conversation,./skill,./task |
| `admin/src/stores/persistedStores.test.ts` | 242 | 定义:createStorageMock,localStorageMock,sessionStorageMock,store,store,store,persistOpt,mod · ⚑MOCK |
| `admin/src/stores/skill.ts` | 148 | 定义:useSkillStore,skills,currentSkillId,loading,error,executingSkills,currentSkill,coreSkills · 依赖:@/types/skill |
| `admin/src/stores/task.ts` | 177 | 定义:useTaskStore,tasks,currentTaskId,loading,error,currentTask,pendingTasks,runningTasks · 依赖:@/types/task |
| `admin/src/stores/uiPreferences.ts` | 197 | 定义:UiTheme,UiAccentRole,UiRadiusScale,UiTableDensity,UiPreferencesState,STORAGE_KEY,PLATFORM_BRAND_DEFAULT,LEGACY_PLATFORM_COLORS |
| `admin/src/stores/websocket.ts` | 141 | 定义:useWebSocketStore,connectionStatus,lastMessage,reconnectAttempts,maxReconnectAttempts,reconnectInterval,error,messageQueue · 依赖:@/types/websocket · ⚑DEPRECATED |
| `admin/src/stores/workTabs.ts` | 234 | 定义:WorkTab,MAX_WORK_TABS,tabKey,dedupeTabs,out,seen,key,isPathAllowedForShell · 依赖:@/constants/proShellMenus,@/constants/roleShellLock,@/constants/stubVisibility,@/constants/workbenchPathCapabilities · ⚑DEGRADED |
| `admin/src/templates/site-builder/buildPageHtml.ts` | 428 | 定义:LegacyThemeOverrides,SiteThemePack,esc,listItems,ThemePack,THEMES,sectionHead,buildHero · 依赖:./buildPageShell,./enterpriseSiteStyles,./industryPresets,./types · ⚑MOCK |
| `admin/src/templates/site-builder/buildPageShell.ts` | 105 | 定义:VisualSitePage,tenantNavHref,ShellContext,NAV_ITEMS,buildSiteChrome,nav,href,active · 依赖:./industryPresets,./types |
| `admin/src/templates/site-builder/buildVisualSiteBundle.ts` | 194 | 定义:ThemePack,VisualSubPageId,resolveTheme,buildVisualSubPage,data,theme,active,shell · 依赖:./buildPageHtml,./buildPageShell,./enterpriseSiteStyles,./industryPresets,./types |
| `admin/src/templates/site-builder/enterpriseSiteStyles.ts` | 93 | 定义:SiteThemeMode,SiteHeaderStyle,SiteRadius,SiteThemePack,ACCENT_PRESETS,DEFAULT_SITE_THEME,isPresetAccent,v · 依赖:./design-system/base.css?raw,./design-system/tokens.css?raw |
| `admin/src/templates/site-builder/grapesjsLocaleZh.ts` | 167 | 定义:traitInputAttr,grapesjsLocaleZh · ⚑MOCK |
| `admin/src/templates/site-builder/index.ts` | 75 | 定义:SITE_BUILDER_TEMPLATES,DEFAULT_TEMPLATE_ID,getTemplateMeta · 依赖:./buildPageHtml,./buildPageShell,./buildVisualSiteBundle,./enterpriseSiteStyles,./industryPresets |
| `admin/src/templates/site-builder/industryPresets.ts` | 383 | 定义:SiteLayoutKind,TEMPLATE_LAYOUT,IndustryPreset,JtbdHomePreset,GENERIC_HERO_TITLES,isGenericHeroTitle,t,mergeScalar · 依赖:./index,./types · ⚑MOCK |
| `admin/src/templates/site-builder/localizeGrapesEditor.ts` | 53 | 定义:localizeGrapesEditor,bm,blockLabels,block,categoryLabels,id,label,zh · 依赖:./grapesjsLocaleZh · ⚑STUB |
| `admin/src/templates/site-builder/parseVisualHtml.ts` | 99 | 定义:parseVisualHtmlToSnapshot,doc,out,home,brandName,tagline,promiseText,kicker · 依赖:./types |
| `admin/src/templates/site-builder/registerYoudingBlocks.ts` | 538 | 定义:BLOCK_CATEGORY,INQUIRY_FORM,WHATSAPP_CTA,TRUST_BADGES,STATS_ROW,CERT_STRIP,SECTION_HEAD,CTA_BAND · 依赖:./enterpriseSiteStyles · ⚑MOCK |
| `admin/src/templates/site-builder/seoSync.ts` | 86 | 定义:i18nHomeOverlay,home,i18n,block,resolvePrimaryMarket,snapshotToSeo,home,zh · 依赖:./types |
| `admin/src/templates/site-builder/templatePreview.ts` | 41 | 定义:TemplatePreviewColors,previewFor,theme,dark,TEMPLATE_PREVIEW_COLORS · 依赖:./buildPageHtml,./buildPageShell,./enterpriseSiteStyles,./types |
| `admin/src/templates/site-builder/types.ts` | 70 | 定义:SiteBuilderTemplateId,SiteBuilderTemplateMeta,SiteContentSnapshot,SiteSubPageId,VisualEditorPayload,SiteSeoFields |
| `admin/src/types/api.ts` | 51 | 定义:ApiResponse,PaginatedResponse,ErrorResponse,SuccessResponse,ApiError,ApiErrorCode,ValidationError |
| `admin/src/types/conversation.ts` | 54 | 定义:Conversation,Message,MessageMetadata,ConversationListResponse,MessageListResponse,CreateConversationRequest,SendMessageRequest |
| `admin/src/types/index.ts` | 9 | 依赖:./api,./conversation,./skill,./task,./websocket |
| `admin/src/types/sales.ts` | 223 | 定义:CustomerStatus,Customer,ContactHistory,CustomerFilters,SearchCriteria,NegotiationStatus,MessageSender,Quote |
| `admin/src/types/shellNav.ts` | 16 | 定义:ShellNavItem,ShellMenuGroup |
| `admin/src/types/skill.ts` | 50 | 定义:Skill,SkillParameter,SkillListResponse,SkillDetailResponse,ExecuteSkillRequest,ExecuteSkillResponse,SkillCategory,SkillExecutionResult |
| `admin/src/types/task.ts` | 57 | 定义:Task,TaskResult,TaskStatusResponse,TaskResultResponse,TaskListResponse,CancelTaskResponse,TaskStatus,TaskProgressUpdate |
| `admin/src/types/websocket.ts` | 81 | 定义:WebSocketMessage,WebSocketAuthMessage,WebSocketConversationMessage,WebSocketTaskUpdateMessage,WebSocketTaskCompleteMessage,WebSocketHeartbeatMessage,WebSocketSystemMessage,WebSocketConnectionStatus |
| `admin/src/utils/__tests__/aiScenarioLimits.test.ts` | 29 | 依赖:../aiScenarioLimits · ⚑MOCK |
| `admin/src/utils/__tests__/clearAuthSessionLocal.test.ts` | 53 | 定义:fetchMock · 依赖:@/auth/session,@/utils/clearAuthSessionLocal · ⚑MOCK |
| `admin/src/utils/__tests__/flash-sales-auth.test.ts` | 86 | 定义:auth,header,body,auth,header,body,auth · ⚑MOCK |
| `admin/src/utils/aiConfigHelpers.ts` | 48 | 定义:AiProviderRow,isProviderConfigured,providerConfiguredTagColor,providerConfiguredLabel,buildProviderStatusMap,map,apiErrorMessage,maskApiKey · 依赖:@/utils/apiError · ⚑DEGRADED |
| `admin/src/utils/aiModelCapability.ts` | 82 | 定义:AiModelStatus,AiModelEnrichedRow,modelStatusColor,endpointLabel,endpointColor,inputModesLabel,map,mergeProbeResults |
| `admin/src/utils/aiScenarioLimits.ts` | 23 | 定义:formatTokenLimit,n,parseScenarioTokenLimit,n |
| `admin/src/utils/aicaigouCategoryTree.test.ts` | 32 | 定义:l1,jiancai,l2,hunningtu,l3,hits,path · 依赖:./aicaigouCategoryTree,@/data/aicaigouCategoryTree |
| `admin/src/utils/aicaigouCategoryTree.ts` | 102 | 定义:AicaigouCategoryNode,AicaigouCategoryPath,getCategoryChildren,parent,findCategoryById,hit,findCategoryPathByLeafId,searchCategoryLeaves · 依赖:@/data/aicaigouCategoryTree |
| `admin/src/utils/api.mutationHonesty.spec.ts` | 45 | 定义:res,body · 依赖:@/utils/apiError,@/utils/apiHonesty · ⚑MOCK |
| `admin/src/utils/api.ts` | 332 | 定义:API_BASE,getAuthToken,authHeaders,authHeadersForForm,QueryParams,API_FETCH_TIMEOUT_MS,fetchWithTimeout,controller · 依赖:@/api/authRefresh,@/auth/session,@/stores/auth,@/utils/apiError,@/utils/apiHonesty · ⚑MOCK/DEGRADED |
| `admin/src/utils/api.uploadHeaders.spec.ts` | 30 | 定义:authHeadersForFormMirror,h,h · ⚑MOCK |
| `admin/src/utils/apiError.ts` | 90 | 定义:ApiError,apiErrorText,status,msg,m,isSilentApiError,apiErrorTextPrefixed,t · ⚑MOCK/DEGRADED |
| `admin/src/utils/apiHonesty.spec.ts` | 35 | 依赖:./apiHonesty · ⚑MOCK |
| `admin/src/utils/apiHonesty.ts` | 44 | 定义:assertMutationOk,code,mode,enforceMutationHonesty,msg,status · 依赖:@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/utils/clearAuthSessionLocal.ts` | 7 | 依赖:@/auth/session · ⚑DEPRECATED |
| `admin/src/utils/clientUiEdition.spec.ts` | 66 | 定义:store,list · 依赖:@/constants/designPreviewPages,@/utils/clientUiEdition |
| `admin/src/utils/clientUiEdition.ts` | 51 | 定义:CLIENT_UI_EDITION_KEY,ClientUiEdition,DESIGN_PREVIEW_BASE,DESIGN_V2_ROUTE_PREFIX,DESIGN_V2_DEFAULT_PAGE,readClientUiEdition,v,writeClientUiEdition |
| `admin/src/utils/exportCsv.ts` | 19 | 定义:downloadTableCsv,escape,s,csv,blob,url,a |
| `admin/src/utils/flattenMenuNav.ts` | 61 | 定义:SearchMenuRow,MenuNavItem,MenuGroup,walk,flattenMenuNav,out,seen,pageTitlesToSearchRows |
| `admin/src/utils/formatTenantPlanLabel.spec.ts` | 28 | 依赖:./formatTenantPlanLabel |
| `admin/src/utils/formatTenantPlanLabel.ts` | 17 | 定义:formatTenantPlanLabel,s,o,v · ⚑DEGRADED |
| `admin/src/utils/hermesSiteBuilder.ts` | 185 | 定义:SITE_DESIGN_CONTRACT,HermesSiteBuilderResult,SKILL_LABELS,EXPERT_LABELS,labelEccExpert,TRADE_SKILL_LABELS,labelDesignSkill,labelTradeSkill · 依赖:@/templates/site-builder/design-system/DESIGN-SYSTEM.md?raw,@/utils/api |
| `admin/src/utils/index.ts` | 167 | 定义:formatDate,d,year,month,day,hours,minutes,seconds · 依赖:./websocket |
| `admin/src/utils/integrationHonesty.spec.ts` | 84 | 定义:rows,byId,rows,wa,tg,rows,wa,caps · 依赖:./integrationHonesty · ⚑DEGRADED |
| `admin/src/utils/integrationHonesty.ts` | 375 | 定义:CapStatus,IntegrationHonestyStatus,IntegrationCatalogItem,IntegrationViewItem,CapabilityItem,INTEGRATION_CATALOG,FLYWHEEL_INTEGRATION_CATALOG,flywheelStatusToCapabilities · ⚑DEGRADED |
| `admin/src/utils/jwtPayload.ts` | 22 | 定义:mapJwtRoleToAgentLevelId,r,table |
| `admin/src/utils/mediaStudioHandoff.ts` | 36 | 定义:EditorHandoffParams,buildEditorHandoffQuery,q,video,abs,abs,appendHandoffToUrl,q · 依赖:@/utils/resolveMediaAssetUrl |
| `admin/src/utils/multipostBridge.ts` | 56 | 定义:MultipostResponse,randomTraceId,multipostRequest,traceId,onMessage,msg,timer,requestMultipostTrustDomain |
| `admin/src/utils/noFakeDelivery.ts` | 88 | 定义:FAKE_MESSAGE_RE,MockTaggedPayload,isPlainObject,subtreeMarkedMock,data,findClientPayloadViolations,out,walk · 依赖:@/utils/apiError · ⚑MOCK |
| `admin/src/utils/onboardingAutopilot.ts` | 72 | 定义:AutopilotStep,AutopilotResult,PREFILL_KEY,storePublishPrefill,consumePublishPrefill,raw,runOnboardingAutopilot,data · 依赖:@/utils/api |
| `admin/src/utils/pageNotify.ts` | 26 | 定义:NotifyType,lastShown,DEFAULT_DEDUP_MS,notifyOnce,k,now,prev,clearNotifyDedup |
| `admin/src/utils/postLoginNavigation.ts` | 43 | 定义:roleFromAccessToken,role,postLoginNavigatePath,postLoginShellHint · 依赖:@/constants/roleShellLock,@/utils/jwtPayload |
| `admin/src/utils/prefetchPostLoginShell.ts` | 58 | 定义:prefetchModule,prefetchLoginShellChunks,v,t,prefetchShellForRole · 依赖:@/constants/loginPortalCopy,@/constants/roleShellLock |
| `admin/src/utils/productAiPrompt.ts` | 38 | 定义:ProductAiGenerateParams,infoBlock,lines,buildProductAiPrompt,type,info,kw |
| `admin/src/utils/productSpecPresets.test.ts` | 27 | 定义:hints,hints,hints · 依赖:./productSpecPresets |
| `admin/src/utils/productSpecPresets.ts` | 121 | 定义:ProductSpecKind,ProductSpecFieldHints,LC_GRADES,FIRE_COMMON,resolveProductSpecKind,text,getProductSpecFieldHints,kind · ⚑MOCK |
| `admin/src/utils/publishTaskDisplay.spec.ts` | 55 | 定义:task,task,task,task,task · 依赖:./publishTaskDisplay |
| `admin/src/utils/publishTaskDisplay.ts` | 154 | 定义:PublishUiPhase,PublishTaskLike,normStatus,hasPublishProof,url,id,getPublishProofUrl,url |
| `admin/src/utils/resolveMediaAssetUrl.ts` | 15 | 定义:resolveMediaAssetUrl,raw,path |
| `admin/src/utils/rumBeacon.ts` | 33 | 定义:RumMetric,sendRumBeacon,endpoint,body |
| `admin/src/utils/sessionAuth.ts` | 48 | 定义:LS_TOKEN,LS_REFRESH,tokenStorage,readStoredAccessToken,t,readStoredRefreshToken,t,hasValidAccessToken |
| `admin/src/utils/sessionKick.spec.ts` | 55 | 依赖:./sessionKick |
| `admin/src/utils/sessionKick.ts` | 61 | 定义:SESSION_KICKED_FLAG,SESSION_KICKED_MESSAGE,DetailLike,readErrorCode,body,detail,nested,haystacks · 依赖:@/auth/session |
| `admin/src/utils/shellNavKernel.ts` | 100 | 定义:EXACT_ONLY_MENU_PATHS,walkShellMenuPaths,collectShellMenuPaths,paths,resolveActiveMenuPath,loc,np,prefixMatch · 依赖:@/constants/workbenchPathCapabilities,@/types/shellNav |
| `admin/src/utils/siteEditorLabSync.ts` | 222 | 定义:SiteEditorLabForm,asRecord,StageRow,KnowledgeRow,readStages,raw,stages,out · 依赖:@/api/admin-bff,@/utils/api |
| `admin/src/utils/siteProductImages.ts` | 48 | 定义:UploadedProductImage,uploadSiteProductImages,token,results,form,res,body,detail · 依赖:@/utils/api |
| `admin/src/utils/tenantPlanDisplay.ts` | 236 | 定义:ApiTenantPlan,PlanFeatureItem,DisplayPlan,PLAN_META,parseFeatures,parsed,fmtCount,yuanFromCents |
| `admin/src/utils/tenantSitePreview.ts` | 13 | 定义:resolveTenantSiteUrl,domain,fromApi · 依赖:../../../utils/tenant-preview-domain |
| `admin/src/utils/uiDisplayLabels.spec.ts` | 45 | 依赖:@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/utils/uiDisplayLabels.ts` | 166 | 定义:HEALTH_STATUS_LABELS,PROBE_MODE_LABELS,DATA_SOURCE_LABELS,METRIC_KEY_LABELS,CONTEST_TIER_LABELS,FAKE_MODES,norm,isFakeDeliveryMode · ⚑MOCK/DEGRADED |
| `admin/src/utils/visualStudioInstatic.ts` | 45 | 定义:VisualStudioStatus,fetchVisualStudioStatus,res,data,seedVisualStudio,exportVisualStudio,studioDeepLink · 依赖:@/utils/api |
| `admin/src/utils/websocket.ts` | 295 | 定义:WebSocketClient,authMessage,subscribeMessage,subscribeMessage,handler,allHandler,heartbeat,createWebSocketClient · 依赖:@/types/websocket |
| `admin/src/utils/workTabPath.ts` | 4 | 依赖:@/constants/roleShellLock |
| `admin/src/utils/ydModal.ts` | 21 | 定义:ydConfirm,ret |
| `admin/src/utils/ydTableUtils.spec.ts` | 28 | 定义:r,r,r · 依赖:@/utils/ydTableUtils |
| `admin/src/utils/ydTableUtils.ts` | 47 | 定义:YdPageResult,ROW_KEYS,TOTAL_KEYS,pickRows,val,nested,pickTotal,val · ⚑DEGRADED |
| `admin/src/views/NotFound.vue` | 39 | 组件:NotFound · 根:div · 定义:router |
| `admin/src/views/PrivacyPolicy.vue` | 248 | 组件:PrivacyPolicy · 根:div |
| `admin/src/views/TermsOfService.vue` | 112 | 组件:TermsOfService · 根:div |
| `admin/src/views/_generated/AbTestList.vue` | 75 | 组件:AbTestList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/AgentHubList.vue` | 75 | 组件:AgentHubList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/AnalyticsList.vue` | 75 | 组件:AnalyticsList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/ComplianceList.vue` | 75 | 组件:ComplianceList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/ContentList.vue` | 75 | 组件:ContentList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/InquiriesList.vue` | 75 | 组件:InquiriesList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/NewsList.vue` | 75 | 组件:NewsList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/PaymentList.vue` | 75 | 组件:PaymentList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/ProductsList.vue` | 75 | 组件:ProductsList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/SeoList.vue` | 75 | 组件:SeoList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/SettingsList.vue` | 75 | 组件:SettingsList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/_generated/UsersList.vue` | 75 | 组件:UsersList · 根:YdPage · 定义:columns,ListQuery,raw,data,rows,total · 依赖:@/components/youding,@/composables/useYoudingTableBridge,@/utils/api · ⚑MOCK |
| `admin/src/views/access-denied.vue` | 160 | 组件:access-denied · 根:div · 定义:route,router,auth,capStore,isRouteKilled,isApi403,pageTitle,fromPath · 依赖:@/constants/roleShellLock,@/stores/agentCapabilities,@/stores/auth |
| `admin/src/views/acquisition/index.vue` | 720 | 组件:index · 根:YdPage · 定义:route,VALID_TABS,syncTabFromRoute,next,tab,loadingCaps,capabilities,disclaimer · 依赖:@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/AgentFunnelCards.vue` | 186 | 组件:AgentFunnelCards · 根:div · 定义:store,runs,alignment,slowSteps,gateRejections,pct,formatNum,formatDuration · 依赖:@/stores/agentObservability |
| `admin/src/views/admin/AggLevelSummary.vue` | 56 | 组件:AggLevelSummary · 根:section · props · emits · 定义:LevelItem,emit |
| `admin/src/views/admin/AggPlatformOverview.vue` | 53 | 组件:AggPlatformOverview · 根:section · props · emits · 定义:PlatformStats,PlatformStatLink,emit |
| `admin/src/views/admin/AggProvinceSummary.vue` | 84 | 组件:AggProvinceSummary · 根:section · props · emits · 定义:ProvinceItem,emit |
| `admin/src/views/admin/AggTreeDrill.vue` | 109 | 组件:AggTreeDrill · 根:section · props · emits · 定义:TreeChild,TreeNode,emit |
| `admin/src/views/admin/AggTrendSection.vue` | 43 | 组件:AggTrendSection · 根:section · props · 定义:TrendMonth |
| `admin/src/views/admin/AuditDetailModal.vue` | 196 | 组件:AuditDetailModal · props · emits · 定义:AuditDetail,emit |
| `admin/src/views/admin/AuditStatsRow.vue` | 171 | 组件:AuditStatsRow · props |
| `admin/src/views/admin/AuditTimelinePanel.vue` | 627 | 组件:AuditTimelinePanel · props · emits · 定义:AuditRow,emit |
| `admin/src/views/admin/DashboardChartsPanel.vue` | 162 | 组件:DashboardChartsPanel · props · 依赖:@/components/common/SkeletonCard.vue |
| `admin/src/views/admin/DashboardKpiCards.vue` | 203 | 组件:DashboardKpiCards · props · 依赖:@/components/common/SkeletonCard.vue |
| `admin/src/views/admin/DashboardOpsPanel.vue` | 326 | 组件:DashboardOpsPanel · props · emits · 定义:emit · 依赖:@/components/common/SkeletonCard.vue |
| `admin/src/views/admin/DashboardTodoPanel.vue` | 224 | 组件:DashboardTodoPanel · props · emits · 定义:emit · 依赖:@/components/youding · ⚑STUB |
| `admin/src/views/admin/agent-runs.vue` | 414 | 组件:agent-runs · 根:div · 定义:store,statusFilter,orchestratorFilter,alignmentFilter,goalFilter,drawerVisible,drawerTitle,statusOptions · 依赖:./AgentFunnelCards.vue,@/api/agentObservability,@/stores/agentObservability · ⚑MOCK |
| `admin/src/views/admin/aggregation.vue` | 364 | 组件:aggregation · 根:YdPage · 定义:selectedPeriod,aggError,periodOptions,expandedProvinces,expandedTreeNodes,selectedLevel,openLevelDetail,code · 依赖:./AggLevelSummary.vue,./AggPlatformOverview.vue,./AggProvinceSummary.vue,./AggTreeDrill.vue,./AggTrendSection.vue |
| `admin/src/views/admin/ai-center/ModelAddModal.vue` | 122 | 组件:ModelAddModal · 根:a-modal · props · emits · 定义:ModelFormState,emit · ⚑MOCK |
| `admin/src/views/admin/ai-center/ModelConfigModal.vue` | 82 | 组件:ModelConfigModal · 根:a-modal · props · emits · 定义:HealthCheckResult,ConfigPlatform,emit · ⚑MOCK |
| `admin/src/views/admin/ai-center/ModelPlatformCard.vue` | 249 | 组件:ModelPlatformCard · 根:div · props · emits · 定义:HealthCheckResult,ModelPlatform,emit |
| `admin/src/views/admin/ai-center/ModelStatusBanner.vue` | 88 | 组件:ModelStatusBanner · 根:div · props |
| `admin/src/views/admin/ai-center/agent-tree.vue` | 741 | 组件:agent-tree · 根:div · 定义:loading,submitting,showCreateModal,editingId,treeForm,trees,formatTime,loadTrees · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/analytics.vue` | 230 | 组件:analytics · 根:YdPage · 定义:loading,dash,memo,MEMO_KEY,MemoRow,memos,dashError,loadMemos · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useAdminWorkspace · ⚑MOCK |
| `admin/src/views/admin/ai-center/article-generator.vue` | 888 | 组件:article-generator · 根:YdPage · 定义:router,articleModel,loadArticleScenarioModel,data,currentStep,articleConfig,wordCountMarks,generating · 依赖:@/api,@/components/youding,@/composables/useSanitize,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/article-to-video.vue` | 874 | 组件:article-to-video · 根:YdPage · 定义:router,currentStep,generatingScript,submitting,polling,mockRender,script,task · 依赖:@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/ai-center/browser-companion-bridge.vue` | 146 | 组件:browser-companion-bridge · 根:YdPage · 定义:LAUNCH_KEY,route,loading,busy,blocked,payload,companionId,mediaTaskId · 依赖:@/components/youding,@/composables/useSanitize,@/utils/api,@/utils/apiError,@/utils/multipostBridge |
| `admin/src/views/admin/ai-center/chat-sessions.vue` | 989 | 组件:chat-sessions · 根:div · 定义:loading,expandedKeys,ChatMessage,ChatSession,sessions,formatTime,onExpand,loadMessages · 依赖:@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/content.vue` | 524 | 组件:content · 根:YdPage · 定义:Prompt,Template,activeTab,showPromptModal,editingId,promptForm,promptRules,columns · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/ai-center/dashboard.vue` | 722 | 组件:dashboard · 根:YdPage · 定义:providers,models,showProvModal,editId,pf,quickKey,quickProvider,healthLoading · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/composables/useWorkTabNavigation,@/utils/aiConfigHelpers,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/ai-center/index.vue` | 14 | 组件:index · 根:div |
| `admin/src/views/admin/ai-center/knowledge.vue` | 524 | 组件:knowledge · 根:YdPage · 定义:question,lastQuestion,answer,sources,loading,activeCategory,categories,stats · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/composables/useSanitize,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/logs.vue` | 112 | 组件:logs · 根:YdPage · 定义:UsageLogRow,loading,taskFilter,logs,cols,formatTime,loadLogs,params · 依赖:@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/models.vue` | 914 | 组件:models · 根:YdPage · 定义:HealthCheckResult,ModelPlatform,showAddModal,showConfigModal,configPlatform,configApiKey,configSaving,configTesting · 依赖:./ModelAddModal.vue,./ModelConfigModal.vue,./ModelPlatformCard.vue,./ModelStatusBanner.vue,@/components/youding |
| `admin/src/views/admin/ai-center/provider-health.vue` | 715 | 组件:provider-health · 根:div · 定义:loading,batchChecking,ProviderItem,HistoryItem,providers,history,healthyCount,degradedCount · 依赖:@/utils/api,@/utils/apiError · ⚑DEGRADED |
| `admin/src/views/admin/ai-center/provider-setup.vue` | 712 | 组件:provider-setup · 根:YdPage · 定义:router,currentStep,NvidiaModel,NvidiaCategory,Platform,allPlatforms,domesticPlatforms,foreignPlatforms · 依赖:@/components/youding,@/constants/antIconMap,@/constants/iconCatalog,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-center/scenario-models.vue` | 329 | 组件:scenario-models · 根:YdPage · 定义:Candidate,ScenarioRow,ScenarioGroup,loading,saving,healthLoading,note,healthSummary · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/ai-center/super-agent.vue` | 433 | 组件:super-agent · 根:main · 定义:loading,toggling,statusInfo,metrics,capabilities,tasks,BadgeStatus,taskStatusMap · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError |
| `admin/src/views/admin/ai-center/ubrain.vue` | 25 | 组件:ubrain · 根:div · ⚑STUB |
| `admin/src/views/admin/ai-center/usage.vue` | 356 | 组件:usage · 根:YdPage · 定义:onKpi,monthlyTokens,todayTokens,estimatedCost,remainingQuota,quotaPercent,trendData,maxTrend · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError |
| `admin/src/views/admin/ai-engine/analytics.vue` | 220 | 组件:analytics · 根:YdPage · 定义:loading,dash,memo,MEMO_KEY,MemoRow,memos,loadMemos,raw · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useAdminWorkspace · ⚑MOCK |
| `admin/src/views/admin/ai-engine/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/ai-engine/models.vue` | 125 | 组件:models · 根:YdPage · 定义:ModelRow,loading,loadError,rows,togglingId,cols,unwrapList,o · 依赖:@/components/youding,@/utils/api · ⚑STUB |
| `admin/src/views/admin/ai-engine/overview.vue` | 218 | 组件:overview · 根:YdPage · 定义:providers,loading,models,showProvModal,editId,pf,quickKey,quickProvider · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/aiConfigHelpers,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-engine/prompts.vue` | 251 | 组件:prompts · 根:YdPage · 定义:Tpl,loading,saving,loadError,items,kw,filterTask,modalOpen · 依赖:@/components/youding,@/utils/api,@/utils/ydModal · ⚑MOCK/STUB |
| `admin/src/views/admin/ai-engine/tasks.vue` | 103 | 组件:tasks · 根:YdPage · 定义:Row,loading,loadError,items,kw,cols,filtered,s · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/ai-engine/templates.vue` | 241 | 组件:templates · 根:YdPage · 定义:templates,loading,saving,filterTask,showCreateModal,editing,form,stats · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-engine/token.vue` | 232 | 组件:token · 根:YdPage · 定义:tenants,selectedTenant,quotaStatus,loading,stats,topupAmount,topupReason,topupLoading · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/ai-engine/trade-intel.vue` | 234 | 组件:trade-intel · 根:YdPage · 定义:rules,BlueOceanRec,blueOceanPreview,commercialPreview,loading,message,ok,matrixStats · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/attribution/index.vue` | 542 | 组件:index · 根:YdPage · 定义:CHANNEL_LABELS,CHANNEL_COLORS,router,period,loading,reportLoaded,utmLoading,utmLoaded · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/audit-logs.vue` | 546 | 组件:audit-logs · 根:div · 定义:AuditRow,AuditDetail,ApiEnvelope,loading,error,rows,filters,timeOptions · 依赖:./AuditDetailModal.vue,./AuditStatsRow.vue,./AuditTimelinePanel.vue,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/automation/index.vue` | 4 | 组件:index · 根:router-view |
| `admin/src/views/admin/automation/overview.vue` | 130 | 组件:overview · 根:YdPage · 定义:STORAGE_KEY,STORAGE_TS,note,savedAt,persist,t · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/automation/scheduler.vue` | 143 | 组件:scheduler · 根:YdPage · 定义:JobRow,loading,loadError,rows,cols,PROBES,load,next · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/automation/scripts.vue` | 126 | 组件:scripts · 根:YdPage · 定义:name,body,editingId,cols,reloadLocal,reset,edit,r · 依赖:@/components/youding,@/composables/useAdminWorkspace · ⚑MOCK |
| `admin/src/views/admin/automation/workflows.vue` | 154 | 组件:workflows · 根:YdPage · 定义:loading,expertsDenied,experts,name,steps,editingId,expertCols,cols · 依赖:@/components/youding,@/composables/useAdminWorkspace,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/capability-hub.vue` | 226 | 组件:capability-hub · 根:YdPage · 定义:router,goAdminHome,blocks · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/code-tools/debug.vue` | 142 | 组件:debug · 根:YdPage · 定义:raw,lines,title,lineCols,snipCols,debugSnippets,reloadLocal,splitLines · 依赖:@/components/youding,@/composables/useAdminWorkspace · ⚑MOCK |
| `admin/src/views/admin/code-tools/format.vue` | 187 | 组件:format · 根:YdPage · 定义:input,output,snapTitle,snips,formatJson,raw,obj,copyOut · 依赖:@/components/youding,@/composables/useAdminWorkspace,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/code-tools/generator.vue` | 153 | 组件:generator · 根:YdPage · 定义:copyOutput · 依赖:@/components/youding,@/composables/useCodeGenerator,@/utils/api · ⚑MOCK/STUB |
| `admin/src/views/admin/code-tools/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/code-tools/overview.vue` | 288 | 组件:overview · 根:YdPage · 定义:tools,router,navigateTo · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/code-tools/refactor.vue` | 115 | 组件:refactor · 根:YdPage · 定义:title,body,snips,save,t,load,del · 依赖:@/components/youding,@/composables/useAdminWorkspace,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/code-tools/review.vue` | 494 | 组件:review · 根:YdPage · 定义:Issue,activeTab,auditStarted,criticalCount,warningCount,infoCount,passedCount,criticalIssues · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api |
| `admin/src/views/admin/code-tools/scanner.vue` | 391 | 组件:scanner · 根:YdPage · 定义:searchQuery,searchType,fileCount,codeLines,functionCount,issueCount,ScanResult,scanResults · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/comments/manage.vue` | 751 | 组件:manage · 根:div · 定义:CommentItem,loading,comments,pagination,statusFilter,totalPages,paginationInfo,start · 依赖:@/utils/api,@/utils/apiError |
| `admin/src/views/admin/components/AdminModulePlaceholder.vue` | 106 | 组件:AdminModulePlaceholder · 根:div · props · 定义:AdminPlaceholderLink,props,router,go · ⚑MOCK |
| `admin/src/views/admin/content/archive.vue` | 957 | 组件:archive · 根:div · 定义:ArchiveItem,loading,submitting,archiveList,pagination,restoreModalVisible,restoreTargetId,filterType · 依赖:@/utils/api,@/utils/apiError |
| `admin/src/views/admin/dashboard.vue` | 350 | 组件:dashboard · 根:YdPage · 定义:router,auth,loadError,loading,greeting,h,stats,tenantCols · 依赖:@/components/youding,@/stores/auth,@/utils/api |
| `admin/src/views/admin/demo-rehearsal.vue` | 782 | 组件:demo-rehearsal · 根:YdPage · 定义:LOCKED_DEMO_STEPS,DemoStep,ReadinessPayload,SevenStepRow,SevenStepAudit,router,loading,readiness · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/ecc-dashboard.vue` | 780 | 组件:ecc-dashboard · 根:YdPage · 定义:LayerHealth,Workflow,Pipeline,OverviewData,LAYER_DEFS,refreshing,healthChecking,workflowsLoading · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/file-manager/FileGridView.vue` | 187 | 组件:FileGridView · 根:div · props · emits · 定义:FileItem,emit |
| `admin/src/views/admin/file-manager/FileListTable.vue` | 99 | 组件:FileListTable · 根:a-table · props · emits · 定义:emit |
| `admin/src/views/admin/file-manager/FilePreviewModal.vue` | 90 | 组件:FilePreviewModal · 根:a-modal · props · emits · 定义:PreviewFileItem,emit |
| `admin/src/views/admin/file-manager/FileStatsRow.vue` | 57 | 组件:FileStatsRow · 根:a-row · props · emits · 定义:FileStatsLike,emit |
| `admin/src/views/admin/file-manager/FileToolbar.vue` | 136 | 组件:FileToolbar · 根:a-card · props · emits · 定义:TenantScopeOption,emit · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/admin/file-manager/FileUploadCard.vue` | 151 | 组件:FileUploadCard · 根:a-card · props · emits · 定义:UploadItem,emit |
| `admin/src/views/admin/file-manager/StorageProfileAlert.vue` | 102 | 组件:StorageProfileAlert · 根:a-alert · props · 定义:StorageProfile |
| `admin/src/views/admin/file-manager/history.vue` | 16 | 组件:history · 根:YdPage · 依赖:@/components/admin/AdminAuditLogTable.vue,@/components/youding |
| `admin/src/views/admin/file-manager/index.vue` | 6 | 组件:index · 根:router-view |
| `admin/src/views/admin/file-manager/overview.vue` | 707 | 组件:overview · 根:YdPage · 定义:route,tenantMediaSpace,pageTitle,pageSubtitle,uploadCardTitle,uploadAccept,dropzoneHint,allowedUploadExtensions · 依赖:./FileGridView.vue,./FileListTable.vue,./FilePreviewModal.vue,./FileStatsRow.vue,./FileToolbar.vue · ⚑DEGRADED |
| `admin/src/views/admin/file-manager/scan.vue` | 133 | 组件:scan · 根:YdPage · 定义:path,severity,note,cols,add,p,now,remove · 依赖:@/components/youding,@/composables/useAdminWorkspace · ⚑MOCK |
| `admin/src/views/admin/file-manager/search.vue` | 88 | 组件:search · 根:YdPage · 定义:STORAGE_KEY,q,bookmarks,loading,filtered,s,loadBookmarks,raw · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/admin/finance/commission-rules.vue` | 116 | 组件:commission-rules · 根:YdPage · 定义:Rule,tablePanelRef,loading,savingId,rules,editRates,editActive,columns · 依赖:@/api,@/components/youding,@/utils/apiError |
| `admin/src/views/admin/finance/commissions.vue` | 185 | 组件:commissions · 根:YdPage · 定义:Row,tablePanelRef,loading,kw,settlingId,items,filteredItems,s · 依赖:@/api,@/components/youding,@/utils/apiError,@/utils/exportCsv · ⚑MOCK |
| `admin/src/views/admin/finance/coupon-management.vue` | 964 | 组件:coupon-management · 根:div · 定义:CouponRow,loading,kw,loadError,items,statusFilter,statusFilterSelect,typeFilter · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/admin/finance/index.vue` | 228 | 组件:index · 根:YdPage · 定义:router,Summary,loading,loadingExpiring,summary,expiringTenants,topTableRef,expTableRef · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/apiError |
| `admin/src/views/admin/finance/invoice-applications.vue` | 408 | 组件:invoice-applications · 根:YdPage · 定义:Row,tablePanelRef,loading,kw,items,filteredItems,s,total · 依赖:@/api,@/components/youding,@/utils/apiError,@/utils/exportCsv · ⚑MOCK |
| `admin/src/views/admin/finance/ip-pool.vue` | 866 | 组件:ip-pool · 根:YdPage · 定义:RegionStats,Overview,EndpointRow,SupplierRow,SuppliersPayload,loading,loadingTable,loadingProfiles · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/components/youding/YdFinanceNav.vue,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/finance/payment-ops.vue` | 709 | 组件:payment-ops · 根:YdPage · 定义:CertRow,OpsStatus,loading,opsAuditPanelRef,certPanelRef,ui,refreshing,probing · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/stores/uiPreferences,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/finance/payment-orders.vue` | 150 | 组件:payment-orders · 根:YdPage · 定义:OrderRow,loading,items,total,statusFilter,tablePanelRef,columns,centsToYuan · 依赖:@/components/youding,@/components/youding/YdFinanceNav.vue,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/finance/refund-management.vue` | 144 | 组件:refund-management · 根:YdPage · 定义:RefundRow,router,loading,kw,loadError,items,statusFilter,stats · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/finance/wallet-management.vue` | 36 | 组件:wallet-management · 根:YdPage · 定义:router,noop · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/admin/finance/withdrawal-management.vue` | 36 | 组件:withdrawal-management · 根:YdPage · 定义:router,noop · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/admin/finance/withdrawals.vue` | 701 | 组件:withdrawals · 根:main · 定义:WithdrawalItem,StatsData,loading,submitting,list,stats,filterStatus,currentPage · 依赖:@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/founder-diagnostics.vue` | 375 | 组件:founder-diagnostics · 根:YdPage · 定义:CryptoSelfTest,FounderPreflight,FounderStatus,ProtectionSummary,SecurityEventRow,router,loading,diagLoading · 依赖:@/api/founderOps,@/api/oauth,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/api |
| `admin/src/views/admin/geo-engine/index.vue` | 730 | 组件:index · 根:YdPage · 定义:router,keyword,loading,competitors,compResults,result,geoScore,trend · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/hierarchy/index.vue` | 834 | 组件:index · 根:YdPage · 定义:router,auth,displayName,greeting,h,hierarchyLevels,HierarchyNode,treeNodes · 依赖:@/components/youding,@/stores/auth,@/utils/api,@/utils/apiError,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/admin/hub/index.vue` | 52 | 组件:index · 根:div · 定义:loading,checklist,load,copySitemap,url · 依赖:@/components/common/SkeletonCard.vue,@/utils/api |
| `admin/src/views/admin/index.vue` | 692 | 组件:index · 定义:AgentLevelId,router,auth,capStore,searchKeyword,healthOk,healthLabel,urgentTodo · 依赖:./DashboardChartsPanel.vue,./DashboardKpiCards.vue,./DashboardOpsPanel.vue,./DashboardTodoPanel.vue,@/components/common/SkeletonCard.vue · ⚑MOCK/STUB/DEGRADED |
| `admin/src/views/admin/international/AddSiteModal.vue` | 55 | 组件:AddSiteModal · 根:div · props · emits · 定义:SiteForm,emit · ⚑MOCK |
| `admin/src/views/admin/international/InquiryStatsPanel.vue` | 105 | 组件:InquiryStatsPanel · props · 定义:Stats |
| `admin/src/views/admin/international/InquiryTable.vue` | 145 | 组件:InquiryTable · 根:div · props · emits · 定义:InquiryItem,Pagination,emit,onStatusChange,value,onSourceChange,value,onPage |
| `admin/src/views/admin/international/SiteTable.vue` | 67 | 组件:SiteTable · 根:div · props · emits · 定义:SiteItem,emit |
| `admin/src/views/admin/international/inquiries.vue` | 323 | 组件:inquiries · 根:main · 定义:InquiryItem,SiteItem,Stats,loading,sitesLoading,submitting,activeTab,inquiries · 依赖:./AddSiteModal.vue,./InquiryStatsPanel.vue,./InquiryTable.vue,./SiteTable.vue,@/utils/api |
| `admin/src/views/admin/layout.vue` | 5 | 组件:layout · 根:router-view |
| `admin/src/views/admin/media-space/index.vue` | 36 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/admin/onboarding/index.vue` | 280 | 组件:index · 根:YdPage · 定义:steps,achievements,currentStep,generating,progress,loadStatus,res,data · 依赖:@/components/tenants/TenantOnboardTabs.vue,@/components/youding/YdPage.vue,@/utils/api |
| `admin/src/views/admin/ops-center.vue` | 457 | 组件:ops-center · 根:YdPage · 定义:router,loading,payLoading,hermesLoading,tipLoading,tipDenied,tipBoard,todoLoading · 依赖:@/components/youding,@/utils/api · ⚑STUB |
| `admin/src/views/admin/paperclip/approvals.vue` | 306 | 组件:approvals · 根:YdPage · 定义:loading,historyLoading,approvingId,rejectingId,companyId,pendingList,historyList,rejectModalVisible · 依赖:@/api/paperclip,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/paperclip/dashboard.vue` | 438 | 组件:dashboard · 根:YdPage · 定义:DashboardData,AgentNode,loading,syncing,triggering,companyId,data,stats · 依赖:@/api/paperclip,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/apiError |
| `admin/src/views/admin/paperclip/goals.vue` | 413 | 组件:goals · 根:YdPage · 定义:loading,saving,companyId,goals,flatGoals,agentList,filterLevel,filterStatus · 依赖:@/api/paperclip,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/paperclip/heartbeats.vue` | 310 | 组件:heartbeats · 根:YdPage · 定义:Agent,HeartbeatLog,HeartbeatEngineStatus,loading,logsLoading,engineLoading,triggering,companyId · 依赖:@/api/paperclip,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/paperclip/org-chart.vue` | 530 | 组件:org-chart · 根:YdPage · 定义:Agent,AgentNode,HeartbeatLog,Task,OrgNode,n,loading,saving · 依赖:@/api/paperclip,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/platform-registry.vue` | 146 | 组件:platform-registry · 根:YdPage · 定义:OriginRow,loading,rows,filterSource,page,pageSize,total,sourceOptions · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/platform-zones.vue` | 292 | 组件:platform-zones · 根:YdPage · 定义:activeTab,certMode,labOpen,readiness,platformAlign,pilotSummary,tabs,ZoneCard · 依赖:@/components/youding,@/constants/antIconMap,@/constants/stubVisibility,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/projects/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/projects/overview.vue` | 281 | 组件:overview · 根:YdPage · 定义:STORAGE_KEY,loading,createOpen,previewTpl,form,templates,DraftRow,drafts · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/admin/recycle-bin/index.vue` | 276 | 组件:index · 根:YdPage · 定义:TrashedItem,activeTab,searchKeyword,loading,tableData,selectedRows,pagination,tabOptions · 依赖:@/components/youding,@/utils/api,@/utils/apiError,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/admin/runtime/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/runtime/overview.vue` | 616 | 组件:overview · 根:YdPage · 定义:router,actionLoading,probeLive,probeError,activeEnv,memoryUsage,memoryUsed,memoryTotal · 依赖:@/api,@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/scheduler/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/scheduler/overview.vue` | 276 | 组件:overview · 根:YdPage · 定义:OpsJobRow,loading,acting,lastNote,jobs,readinessReady,readinessScore,smtpConfigured · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/security/audit.vue` | 28 | 组件:audit · 根:YdPage · 定义:auditTableRef,refreshAudit · 依赖:@/components/admin/AdminAuditLogTable.vue,@/components/youding |
| `admin/src/views/admin/security/compliance.vue` | 173 | 组件:compliance · 根:YdPage · 定义:Violation,loading,loadError,items,kw,severity,resolved,resolvingId · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/security/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/security/overview.vue` | 546 | 组件:overview · 根:YdPage · 定义:router,scanning,Alert,Policy,securityStats,alerts,policies,togglePolicy · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/security/vulnerability.vue` | 140 | 组件:vulnerability · 根:YdPage · 定义:Issue,loading,loadError,items,kw,severity,cols,filtered · 依赖:@/components/admin/AdminAuditLogTable.vue,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/system/account-bindings.vue` | 159 | 组件:account-bindings · 根:YdPage · 定义:OAuthBindingRow,OAuthProvider,providers,loading,actionLoading,bindings,oauthReady,oauthDevBypass · 依赖:@/api/oauth,@/api/oauthBindings,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/api |
| `admin/src/views/admin/system/agent-capabilities.vue` | 709 | 组件:agent-capabilities · 根:YdPage · 定义:AgentLevelId,router,capStore,mainTab,backendColumns,scopeLabel,map,levelLabel · 依赖:@/components/youding,@/constants/agentLevelBlueprint,@/constants/workbenchCapabilityRegistry,@/constants/workbenchIcons,@/stores/agentCapabilities |
| `admin/src/views/admin/system/command-center.vue` | 587 | 组件:command-center · 根:YdPage · 定义:Probe,Suggestion,loading,runningOps,runningDeerflow,runningRankGuard,runningInclusion,runningMem0 · 依赖:@/components/youding,@/stores/auth,@/utils/api,@/utils/uiDisplayLabels · ⚑DEGRADED |
| `admin/src/views/admin/system/config.vue` | 446 | 组件:config · 根:YdPage · 定义:ConfigItem,ConfigSection,configSections,handleConfigChange,resetConfig,saveConfig · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/system/deerflow-monitor.vue` | 131 | 组件:deerflow-monitor · 根:YdPage · 定义:Step,loading,items,SloSnapshot,slo,page,pageSize,total · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/system/domain-ssl.vue` | 975 | 组件:domain-ssl · 根:div · 定义:TenantOption,DnsRecord,DomainItem,SslItem,loading,sslLoading,submitting,activeTab · 依赖:@/utils/api,@/utils/apiError · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/system/ecc-hangar.vue` | 144 | 组件:ecc-hangar · 根:YdPage · 定义:Expert,ReviewItem,loading,runningRadar,snap,radarReports,meta,reviews · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/system/greedy-contest-leaderboard.vue` | 479 | 组件:greedy-contest-leaderboard · 根:YdPage · 定义:GreedyLeaderboard,GreedyProjectBoard,loading,boardLoading,snap,projectBoard,rows,seasonLabel · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/system/greedy-cumulative.vue` | 216 | 组件:greedy-cumulative · 根:YdPage · 定义:GreedyCumulative,GreedyDigestPreview,loading,sendingDigest,runningLoop,gateError,data,endurance · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer |
| `admin/src/views/admin/system/greedy-expert-memory.vue` | 807 | 组件:greedy-expert-memory · 根:YdPage · 定义:SampleRoleRow,InspectionData,ExecutionStep,ExecutionData,loading,memLoading,inspectionLoading,executionLoading · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/system/greedy-hub.vue` | 328 | 组件:greedy-hub · 根:YdPage · 定义:GreedyReadiness,loading,loadingReadiness,bootstrapping,runningLoop,sendingDigest,gateError,hub · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels |
| `admin/src/views/admin/system/greedy-publish-queue.vue` | 271 | 组件:greedy-publish-queue · 根:YdPage · 定义:GreedyPublishItem,GreedyPublishQueue,GreedyPublishReviewHistory,loading,tasksLoading,reviewingIndex,snap,history · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/admin/system/index.vue` | 13 | 组件:index · 根:div |
| `admin/src/views/admin/system/integrations-stack.vue` | 153 | 组件:integrations-stack · 根:YdPage · 定义:loading,status,crawlPanel,nodeColor,s,acquisitionStatusColor,panel,load · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/utils/api,@/utils/apiError · ⚑DEGRADED |
| `admin/src/views/admin/system/license.vue` | 668 | 组件:license · 根:div · 定义:LicenseItem,LicenseStatus,loading,submitting,licenseList,licenseStatus,pagination,showActivateModal · 依赖:@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/system/logs.vue` | 257 | 组件:logs · 根:YdPage · 定义:AuditRow,loading,rows,action,resourceType,keyword,dateRange,pagination · 依赖:@/api,@/components/youding,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/system/ops-wrap.vue` | 36 | 组件:ops-wrap · 根:YdPage · 定义:running,result,runAll · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/system/overview.vue` | 799 | 组件:overview · 根:YdPage · 定义:StatCard,StatusRow,ActivityRow,DataHonesty,DashboardStats,SystemStatusPayload,AuditLogRow,quickLinks · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useWorkTabNavigation,@/utils/api,@/utils/uiDisplayLabels |
| `admin/src/views/admin/system/permissions.vue` | 366 | 组件:permissions · 根:YdPage · 定义:AdminRoleRow,AdminPermissionRow,AdminMenuRow,router,activeTab,loading,saving,loadError · 依赖:@/components/youding,@/utils/api,@/utils/apiError,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/admin/system/progress-board.vue` | 265 | 组件:progress-board · 根:YdPage · 定义:Mod,SquadTask,Squad,SwarmMeta,swarmMeta,squads,squadStats,total · 依赖:@/components/youding,@/data/module-progress.json,@/utils/api |
| `admin/src/views/admin/system/publish-history.vue` | 42 | 组件:publish-history · 根:YdPage · 定义:loading,items,cols,load,data · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/admin/system/rank-scheduler.vue` | 169 | 组件:rank-scheduler · 根:YdPage · 定义:RankRow,loading,syncing,running,snap,schedulerMeta,dbKeywordCount,schedulerEnabledLabel · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api |
| `admin/src/views/admin/system/storage-provision.vue` | 214 | 组件:storage-provision · 根:YdPage · 定义:loading,verifying,trialLoading,snippetLoading,status,checklist,verifyReport,trialQiniu · 依赖:@/components/youding,@/utils/api,@/utils/apiError,@/utils/uiDisplayLabels · ⚑MOCK/DEGRADED |
| `admin/src/views/admin/system/survival-dashboard.vue` | 324 | 组件:survival-dashboard · 根:YdPage · 定义:LedgerRow,loading,wfSubmitting,genSubmitting,recordTab,snap,wfForm,genForm · 依赖:@/api/hermesGreedy,@/components/youding,@/composables/useBoardDetailDrawer · ⚑MOCK |
| `admin/src/views/admin/system/users.vue` | 409 | 组件:users · 根:YdPage · 定义:User,searchKeyword,roleFilter,showAddModal,formRef,loading,currentEditUser,formData · 依赖:@/api,@/components/youding,@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/tech-radar/index.vue` | 280 | 组件:index · 根:YdPage · 定义:RadarItem,loading,radarData,activeCategory,minRelevance,categoryOptions,filteredItems,highRelevanceCount · 依赖:@/components/common/SkeletonCard.vue,@/components/youding/YdPage.vue,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError |
| `admin/src/views/admin/tenant-list.vue` | 781 | 组件:tenant-list · 根:div · 定义:TenantRow,router,loading,rows,stats,q,statusFilter,planFilter · 依赖:@/utils/api,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/tenants/subscription-management.vue` | 186 | 组件:subscription-management · 根:YdPage · 定义:SubRow,router,loading,loadError,items,filter,stats,columns · 依赖:@/components/tenants/TenantCommerceTabs.vue,@/components/youding,@/utils/api,@/utils/uiDisplayLabels |
| `admin/src/views/admin/traffic-board.vue` | 20 | 组件:traffic-board · 根:YdPage · 依赖:@/components/traffic/TrafficBoardPanel.vue,@/components/youding,@/utils/api |
| `admin/src/views/admin/v2ray/index.vue` | 2 | 组件:index · 根:div |
| `admin/src/views/admin/v2ray/routing.vue` | 71 | 组件:routing · 根:YdPage · 定义:globalPolicy,f,c,loading,kw,rules,filteredRules,s · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/v2ray/servers.vue` | 95 | 组件:servers · 根:YdPage · 定义:loading,showAdd,form,servers,loadServers,d,items,cols · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/admin/v2ray/subscription.vue` | 184 | 组件:subscription · 根:YdPage · 定义:SubscriptionItem,showAdd,loading,kw,f,subs,filteredSubs,s · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/apiError · ⚑MOCK |
| `admin/src/views/admin/v2ray/tracker.vue` | 86 | 组件:tracker · 根:YdPage · 定义:tracker,releases,formatSize,loading,fetchData,checkNow,startTracker · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/apiError |
| `admin/src/views/admin/v2ray/traffic.vue` | 149 | 组件:traffic · 根:YdPage · 定义:period,loading,mode,loadError,stats,nodeTraffic,daily,logs · 依赖:@/components/common/PageDataBar.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/composables/usePageData,@/utils/api |
| `admin/src/views/agent-hub/dashboard.vue` | 100 | 组件:dashboard · 根:YdPage · 定义:agents,recentTasks,capabilityTags,chartBars,maxVal,loadData,d,refresh · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/agent-hub/execution-review.vue` | 198 | 组件:execution-review · 根:YdPage · 定义:searchKey,tablePanelRef,listLoading,ui,summary,columns,records,filteredRecords · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/agent-hub/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/agent-hub/mcp-bridge.vue` | 150 | 组件:mcp-bridge · 根:YdPage · 定义:showAddModal,toolsPanelRef,ui,newServer,servers,toolsModal,toolColumns,loadServers · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/agent-hub/task-orchestrator.vue` | 176 | 组件:task-orchestrator · 根:YdPage · 定义:showCreateModal,tablePanelRef,listLoading,ui,orchForm,orchColumns,orchestrations,logModal · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/agent/account-opening.vue` | 489 | 组件:account-opening · 根:YdPage · 定义:PlanOption,OpeningRecord,packages,billingCycle,form,submitting,lastTenantId,qrVisible · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/agent/churn-warning.vue` | 608 | 组件:churn-warning · 根:YdPage · 定义:scrollRisk,id,el,Tenant,Summary,Tip,TrendItem,tenants · 依赖:@/components/youding,@/utils/sessionAuth |
| `admin/src/views/agent/commission.vue` | 153 | 组件:commission · 根:YdPage · 定义:centsToYuan,commissionStats,CommissionRecord,applySettleFilter,settleFilter,columns,records,loadCommissions · 依赖:@/api/index,@/components/youding · ⚑MOCK |
| `admin/src/views/agent/daily-report.vue` | 503 | 组件:daily-report · 根:YdPage · 定义:router,route,portalPath,base,goDailyDetail,KeywordChange,ExpiringItem,DailyReport · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/sessionAuth · ⚑MOCK |
| `admin/src/views/agent/index.vue` | 670 | 组件:index · 根:div · 定义:promoLinks,clients,copyLink,btn,originalHTML · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/agent/performance.vue` | 587 | 组件:performance · 根:YdPage · 定义:DashboardStats,SubordinateItem,TrendItem,ClientRow,formatMoney,router,route,portalBase · 依赖:@/components/youding,@/stores/auth,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK/DEGRADED |
| `admin/src/views/agent/traffic-board.vue` | 118 | 组件:traffic-board · 根:YdPage · 定义:router,clientsLoading,clientRows,clientPagination,clientColumns,loadClients,data,onClientPageChange · 依赖:@/components/traffic/TrafficBoardPanel.vue,@/components/youding,@/utils/api |
| `admin/src/views/ai-center/FeaturedCollections.vue` | 152 | 组件:FeaturedCollections · 根:div · props · emits · 定义:Skill,Collection,emit |
| `admin/src/views/ai-center/SkillDetailModal.vue` | 269 | 组件:SkillDetailModal · 根:a-modal · props · emits · 定义:Skill,emit |
| `admin/src/views/ai-center/SkillGrid.vue` | 228 | 组件:SkillGrid · 根:div · props · emits · 定义:Skill,emit |
| `admin/src/views/ai-center/SkillStoreHeader.vue` | 113 | 组件:SkillStoreHeader · 根:div · props |
| `admin/src/views/ai-center/SkillStoreSidebar.vue` | 218 | 组件:SkillStoreSidebar · 根:div · props · emits · 定义:Skill,Group,emit |
| `admin/src/views/ai-center/TopRatedSkills.vue` | 182 | 组件:TopRatedSkills · 根:div · props · 定义:Skill |
| `admin/src/views/ai-center/analytics.vue` | 386 | 组件:analytics · 根:YdPage · 定义:loading,seoLoading,activeTab,period,seoPanelRef,lossPanelRef,pagePanelRef,ui · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences |
| `admin/src/views/ai-center/content.vue` | 399 | 组件:content · 根:YdPage · 定义:historyPanelRef,ui,historyPage,historyPagination,onHistoryPageChange,form,keywords,optimizedContent · 依赖:@/api,@/components/common/AiSkeleton.vue,@/components/common/TypewriterText.vue,@/components/youding,@/composables/useAiRequest · ⚑MOCK |
| `admin/src/views/ai-center/dashboard.vue` | 306 | 组件:dashboard · 根:YdPage · 定义:router,tablePanelRef,ui,loading,providers,engineHealthy,providerStatusList,names · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api,@/utils/sessionAuth · ⚑MOCK |
| `admin/src/views/ai-center/index.vue` | 14 | 组件:index · 根:div |
| `admin/src/views/ai-center/logs.vue` | 299 | 组件:logs · 根:YdPage · 定义:loading,logsPanelRef,ui,logsPage,logsPagination,onLogsPageChange,dateRange,logs · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/ai-center/models.vue` | 262 | 组件:models · 根:YdPage · 定义:modelsPanelRef,ui,providers,models,modelsLoading,showProvModal,showModelModal,editId · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/aiConfigHelpers,@/utils/api · ⚑MOCK |
| `admin/src/views/ai-center/skill-store.vue` | 245 | 组件:skill-store · 根:div · 定义:Skill,Group,Collection,skillGroups,featuredCollections,topRatedSkills,selectedGroup,selectedRisk · 依赖:./FeaturedCollections.vue,./SkillDetailModal.vue,./SkillGrid.vue,./SkillStoreHeader.vue,./SkillStoreSidebar.vue |
| `admin/src/views/ai-learning/auto-ab-test.vue` | 164 | 组件:auto-ab-test · 根:YdPage · 定义:showCreate,showResult,resultTest,loading,tablePanelRef,ui,form,tests · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/ai-learning/behavior.vue` | 176 | 组件:behavior · 根:YdPage · 定义:period,loading,loadError,tablePanelRef,ui,stats,summary,funnel · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/ai-learning/conversion-funnel.vue` | 121 | 组件:conversion-funnel · 根:YdPage · 定义:period,loading,isEmpty,disclaimer,tablePanelRef,ui,FunnelStep,funnel · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/constants/iconCatalog,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/ai-learning/dashboard.vue` | 88 | 组件:dashboard · 根:YdPage · 定义:loading,tablePanelRef,ui,cards,trend,models,logs,c · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/ai-learning/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/cases/edit.vue` | 236 | 组件:edit · 根:YdPage · 定义:route,router,isEdit,loading,form,fetchCase,res,data · 依赖:@/api,@/components/youding · ⚑MOCK |
| `admin/src/views/cases/index.vue` | 269 | 组件:index · 根:YdPage · 定义:cases,loading,tablePanelRef,ui,search,filterStatus,tablePagination,onPageChange · 依赖:@/api,@/components/youding,@/stores/uiPreferences,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/client/AiConfigDetailModal.vue` | 104 | 组件:AiConfigDetailModal · 根:a-modal · props · emits · 定义:emit |
| `admin/src/views/client/AiConfigHelpModal.vue` | 47 | 组件:AiConfigHelpModal · 根:a-modal · props · emits · 定义:emit |
| `admin/src/views/client/AiConfigModelGrid.vue` | 301 | 组件:AiConfigModelGrid · 根:div · props · emits · 定义:ModelInfo,emit · ⚑DEGRADED |
| `admin/src/views/client/AiConfigSceneTable.vue` | 173 | 组件:AiConfigSceneTable · 根:div · props · emits · 定义:SceneInfo,emit |
| `admin/src/views/client/AiConfigUsageChart.vue` | 113 | 组件:AiConfigUsageChart · 根:div · props |
| `admin/src/views/client/AiConfigUsageSummary.vue` | 111 | 组件:AiConfigUsageSummary · 根:div · props · 定义:UsageOverview |
| `admin/src/views/client/AttributionChannelCharts.vue` | 184 | 组件:AttributionChannelCharts · 根:div · props · 定义:AttributionChannelDatum |
| `admin/src/views/client/AttributionFunnelTable.vue` | 179 | 组件:AttributionFunnelTable · 根:section · props · 定义:AttributionFunnelRow |
| `admin/src/views/client/AttributionGaugeRow.vue` | 128 | 组件:AttributionGaugeRow · 根:section · props |
| `admin/src/views/client/AttributionInsightTables.vue` | 247 | 组件:AttributionInsightTables · 根:div · props · 定义:AttributionKeywordRow,AttributionAiRow |
| `admin/src/views/client/AttributionKpiRow.vue` | 147 | 组件:AttributionKpiRow · 根:section · props |
| `admin/src/views/client/ClientDashboardActivity.vue` | 126 | 组件:ClientDashboardActivity · 根:section · props · emits · 定义:DashboardRecentInquiry,emit |
| `admin/src/views/client/ClientDashboardChecklist.vue` | 219 | 组件:ClientDashboardChecklist · 根:section · props · emits · 定义:emit · 依赖:@/components/youding/types |
| `admin/src/views/client/ClientDashboardDetailModal.vue` | 91 | 组件:ClientDashboardDetailModal · 根:Teleport · props · emits · 定义:emit |
| `admin/src/views/client/ClientDashboardFocusCard.vue` | 130 | 组件:ClientDashboardFocusCard · 根:section · props · emits · 定义:DashboardFocusCard,emit |
| `admin/src/views/client/ClientDashboardGreetingStrip.vue` | 125 | 组件:ClientDashboardGreetingStrip · 根:section · props |
| `admin/src/views/client/ClientDashboardStats.vue` | 95 | 组件:ClientDashboardStats · 根:div · props · emits · 定义:DashboardStat,emit |
| `admin/src/views/client/ContentDistributeInputCard.vue` | 349 | 组件:ContentDistributeInputCard · props · emits · 定义:emit,imageInputRef · 依赖:@/utils/siteProductImages · ⚑MOCK |
| `admin/src/views/client/ContentDistributeOverseasAlerts.vue` | 111 | 组件:ContentDistributeOverseasAlerts · props · emits · 定义:emit |
| `admin/src/views/client/ContentDistributePreviewCard.vue` | 243 | 组件:ContentDistributePreviewCard · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/client/ContentDistributePublishCard.vue` | 436 | 组件:ContentDistributePublishCard · props · emits · 定义:BoundPlatform,PublishSummary,emit |
| `admin/src/views/client/ContentDistributeTopbar.vue` | 168 | 组件:ContentDistributeTopbar |
| `admin/src/views/client/CopilotActionAudits.vue` | 36 | 组件:CopilotActionAudits · 根:section · props · 定义:ActionAudit |
| `admin/src/views/client/CopilotAiAlerts.vue` | 53 | 组件:CopilotAiAlerts · 根:div · props |
| `admin/src/views/client/CopilotAuditSummary.vue` | 27 | 组件:CopilotAuditSummary · 根:section · props · 定义:AuditSummary |
| `admin/src/views/client/CopilotBriefPanel.vue` | 55 | 组件:CopilotBriefPanel · 根:section · props · emits · 定义:BriefTemplate,BriefAction,emit · ⚑MOCK |
| `admin/src/views/client/CopilotExecutionCards.vue` | 48 | 组件:CopilotExecutionCards · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/CopilotFlywheelPanel.vue` | 163 | 组件:CopilotFlywheelPanel · 根:div · props · emits · 定义:PillarKey,OpsSnapshotLike,FunnelStep,Insight,PipelineStep,Pipeline,emit |
| `admin/src/views/client/CopilotGapSkills.vue` | 32 | 组件:CopilotGapSkills · 根:section · props · emits · 定义:GapSkill,emit |
| `admin/src/views/client/CopilotKpiCards.vue` | 106 | 组件:CopilotKpiCards · 根:section · props |
| `admin/src/views/client/CopilotLastTask.vue` | 132 | 组件:CopilotLastTask · 根:section · props · emits · 定义:LastTask,JobStatus,JobStep,CommercialHook,ProspectPreview,LetterPreview,AgentPreview,emit |
| `admin/src/views/client/CopilotPartialSkills.vue` | 48 | 组件:CopilotPartialSkills · 根:section · props · emits · 定义:GapSkill,PartialFollowUp,emit |
| `admin/src/views/client/CopilotPendingConfirm.vue` | 25 | 组件:CopilotPendingConfirm · 根:section · props · emits · 定义:PendingConfirm,emit |
| `admin/src/views/client/CopilotQuickChips.vue` | 18 | 组件:CopilotQuickChips · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/CopilotRecentJobs.vue` | 28 | 组件:CopilotRecentJobs · 根:section · props · emits · 定义:RecentJob,emit |
| `admin/src/views/client/CopilotTopbar.vue` | 82 | 组件:CopilotTopbar · 根:section · props |
| `admin/src/views/client/CopilotWeeklyPanel.vue` | 34 | 组件:CopilotWeeklyPanel · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/DataExportGrid.vue` | 228 | 组件:DataExportGrid · 根:div · props · 定义:Counts |
| `admin/src/views/client/DataExportHistory.vue` | 145 | 组件:DataExportHistory · 根:div · props · 定义:ExportHistoryRow |
| `admin/src/views/client/DataExportSchedulePanel.vue` | 251 | 组件:DataExportSchedulePanel · 根:div · props · emits · 定义:props,emit,scheduledDataLocal,scheduledFormatLocal,scheduledCycleLocal,scheduledDayLocal,scheduledTimeLocal,scheduledEmailLocal · ⚑MOCK |
| `admin/src/views/client/EmailCampaignsKpiCards.vue` | 198 | 组件:EmailCampaignsKpiCards · props · 定义:KpiData |
| `admin/src/views/client/EmailCampaignsSidePanel.vue` | 282 | 组件:EmailCampaignsSidePanel · props · 定义:TimelineEvent |
| `admin/src/views/client/EmailCampaignsTable.vue` | 575 | 组件:EmailCampaignsTable · props · 定义:CampaignRow · ⚑MOCK |
| `admin/src/views/client/GeoAttribution.vue` | 118 | 组件:GeoAttribution · props · 定义:GscAdsStatus,Citations |
| `admin/src/views/client/GeoMidInsights.vue` | 159 | 组件:GeoMidInsights · 根:section · props · 定义:GeoDimension,LlmsUrls,ContentStats |
| `admin/src/views/client/GeoProbes.vue` | 73 | 组件:GeoProbes · 根:section · props · 定义:ProbeModel |
| `admin/src/views/client/GeoProductMentions.vue` | 151 | 组件:GeoProductMentions · 根:section · props · 定义:ProductMention |
| `admin/src/views/client/GeoScoreModels.vue` | 201 | 组件:GeoScoreModels · props · 定义:ProbeModel,ComponentRow,UnifiedLike |
| `admin/src/views/client/GeoSiteDiagnostics.vue` | 94 | 组件:GeoSiteDiagnostics · 根:section · props · 定义:SiteDiagnostic,DiagDimension |
| `admin/src/views/client/InvoiceApplyModal.vue` | 185 | 组件:InvoiceApplyModal · 根:a-modal · props · emits · 定义:props,emit,typeModel,titleModel,taxNoModel,amountModel,addressModel,phoneModel · ⚑MOCK |
| `admin/src/views/client/InvoiceDetailModal.vue` | 212 | 组件:InvoiceDetailModal · 根:a-modal · props · emits · 定义:InvoiceLineItem,InvoiceItem,emit |
| `admin/src/views/client/InvoicesHistoryTable.vue` | 306 | 组件:InvoicesHistoryTable · 根:div · props · emits · 定义:InvoiceLineItem,InvoiceItem,emit · ⚑MOCK |
| `admin/src/views/client/InvoicesPaymentHistory.vue` | 222 | 组件:InvoicesPaymentHistory · 根:div · props · 定义:PaymentHistoryItem |
| `admin/src/views/client/InvoicesStatsRow.vue` | 169 | 组件:InvoicesStatsRow · 根:div · props |
| `admin/src/views/client/InvoicesTrendChart.vue` | 214 | 组件:InvoicesTrendChart · 根:div · props · emits · 定义:ChartBar,emit |
| `admin/src/views/client/OnboardingStepComplete.vue` | 132 | 组件:OnboardingStepComplete · 根:div · props · emits · 定义:RoadmapPhase,ChecklistItem,emit · 依赖:@/components/tenant/OnboardingPlainRoadmap.vue,@/components/tenant/TenantOnboardingChecklist.vue |
| `admin/src/views/client/OnboardingStepFirstPublish.vue` | 95 | 组件:OnboardingStepFirstPublish · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/OnboardingStepImBinding.vue` | 52 | 组件:OnboardingStepImBinding · 根:div · emits · 定义:emit · 依赖:@/components/tenant/OnboardingImContactsPanel.vue · ⚑MOCK |
| `admin/src/views/client/OnboardingStepSiteBuilder.vue` | 156 | 组件:OnboardingStepSiteBuilder · 根:div · props · emits · 定义:productName,emit · 依赖:@/utils/siteProductImages · ⚑MOCK |
| `admin/src/views/client/OnboardingStepWangcaiPreview.vue` | 105 | 组件:OnboardingStepWangcaiPreview · 根:div · props · emits · 定义:emit · 依赖:@/components/tenant/OnboardingWangcaiPanel.vue |
| `admin/src/views/client/OnboardingStepWelcome.vue` | 187 | 组件:OnboardingStepWelcome · props · emits · 定义:RoadmapPhase,JtbdChecklistItem,productName,emit · 依赖:@/components/site-builder/JtbdSiteChecklist.vue,@/components/tenant/OnboardingAutopilotProgress.vue,@/components/tenant/OnboardingExternalAccountsPanel.vue,@/components/tenant/OnboardingPlainRoadmap.vue,@/utils/onboardingAutopilot · ⚑MOCK |
| `admin/src/views/client/OnboardingWizardStepper.vue` | 74 | 组件:OnboardingWizardStepper · props · emits · 定义:emit |
| `admin/src/views/client/ReferralProgress.vue` | 130 | 组件:ReferralProgress · 根:div |
| `admin/src/views/client/ReferralRewardGrid.vue` | 123 | 组件:ReferralRewardGrid · 根:div · props · 定义:ReferralRecord |
| `admin/src/views/client/ReferralSharePanel.vue` | 216 | 组件:ReferralSharePanel · 根:div · props · 定义:ReferralStats,LeaderboardRow |
| `admin/src/views/client/ReferralStatsRow.vue` | 140 | 组件:ReferralStatsRow · 根:div · props · 定义:ReferralStats |
| `admin/src/views/client/ReferralTableSection.vue` | 185 | 组件:ReferralTableSection · 根:div · props · 定义:ReferralRecord |
| `admin/src/views/client/SalesPipelineDetailModal.vue` | 123 | 组件:SalesPipelineDetailModal · 根:Teleport · props · emits · 定义:emit |
| `admin/src/views/client/SalesPipelineKanban.vue` | 434 | 组件:SalesPipelineKanban · 根:section · props · emits · 定义:Stage,Inquiry,StageOption,emit |
| `admin/src/views/client/SalesPipelineKpiStrip.vue` | 174 | 组件:SalesPipelineKpiStrip · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/SalesPipelinePiDrawer.vue` | 101 | 组件:SalesPipelinePiDrawer · 根:a-drawer · props · emits · 定义:emit |
| `admin/src/views/client/SalesPipelineSidebar.vue` | 313 | 组件:SalesPipelineSidebar · 根:aside · props · emits · 定义:Stage,emit |
| `admin/src/views/client/SalesPipelineTopBar.vue` | 214 | 组件:SalesPipelineTopBar · 根:section · props · emits · 定义:PeriodTab,emit · 依赖:@/components/youding |
| `admin/src/views/client/TeamActivityLog.vue` | 98 | 组件:TeamActivityLog · 根:div · props · 定义:TeamActivityItem |
| `admin/src/views/client/TeamHeader.vue` | 72 | 组件:TeamHeader · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/TeamInviteModal.vue` | 135 | 组件:TeamInviteModal · 根:div · props · emits · 定义:props,emit,emailModel,roleModel,messageModel · ⚑MOCK |
| `admin/src/views/client/TeamMemberDetailModal.vue` | 162 | 组件:TeamMemberDetailModal · 根:div · props · emits · 定义:DetailMemberRow,emit |
| `admin/src/views/client/TeamMemberTable.vue` | 297 | 组件:TeamMemberTable · 根:div · props · emits · 定义:TeamMemberRow,props,emit,keywordModel · ⚑MOCK |
| `admin/src/views/client/TeamRolesSection.vue` | 223 | 组件:TeamRolesSection · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/TeamStatsRow.vue` | 87 | 组件:TeamStatsRow · 根:div · props |
| `admin/src/views/client/TeamToast.vue` | 60 | 组件:TeamToast · 根:Transition · props |
| `admin/src/views/client/TradeToolCard.vue` | 266 | 组件:TradeToolCard · 根:div · props · emits · 定义:props,emit · 依赖:./tradeTools.data |
| `admin/src/views/client/TradeToolCompareBar.vue` | 110 | 组件:TradeToolCompareBar · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/TradeToolCompareModal.vue` | 179 | 组件:TradeToolCompareModal · 根:a-modal · props · emits · 定义:props,emit,open,ids · 依赖:./tradeTools.data |
| `admin/src/views/client/TradeToolFilterBar.vue` | 74 | 组件:TradeToolFilterBar · 根:div · props · emits · 定义:props,emit,kw,cat · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/client/TradeToolGrid.vue` | 47 | 组件:TradeToolGrid · 根:div · props · emits · 定义:props,emit · 依赖:./TradeToolCard.vue,./tradeTools.data |
| `admin/src/views/client/TradeToolGuideModal.vue` | 148 | 组件:TradeToolGuideModal · 根:a-modal · props · emits · 定义:props,emit,open · 依赖:./tradeTools.data |
| `admin/src/views/client/TradeToolRelatedModal.vue` | 127 | 组件:TradeToolRelatedModal · 根:a-modal · props · emits · 定义:props,emit,open · 依赖:./tradeTools.data |
| `admin/src/views/client/TrafficBoardChannels.vue` | 237 | 组件:TrafficBoardChannels · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardConversions.vue` | 68 | 组件:TrafficBoardConversions · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardDailyTrend.vue` | 52 | 组件:TrafficBoardDailyTrend · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardDetailDrawer.vue` | 58 | 组件:TrafficBoardDetailDrawer · 根:a-drawer · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardFunnel.vue` | 203 | 组件:TrafficBoardFunnel · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardKpiGrid.vue` | 162 | 组件:TrafficBoardKpiGrid · 根:section · props · emits · 定义:TrafficKpiCard,emit |
| `admin/src/views/client/TrafficBoardSubordinateTable.vue` | 49 | 组件:TrafficBoardSubordinateTable · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardTenantTable.vue` | 47 | 组件:TrafficBoardTenantTable · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardTopContent.vue` | 52 | 组件:TrafficBoardTopContent · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/TrafficBoardTopbar.vue` | 182 | 组件:TrafficBoardTopbar · 根:section · props · emits · 定义:emit |
| `admin/src/views/client/WalletBalanceHero.vue` | 120 | 组件:WalletBalanceHero · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/WalletDepositModal.vue` | 147 | 组件:WalletDepositModal · 根:a-modal · props · emits · 定义:props,emit,amountModel · ⚑MOCK/STUB |
| `admin/src/views/client/WalletMonthlyStats.vue` | 121 | 组件:WalletMonthlyStats · 根:div · props · 定义:WalletMonthStats |
| `admin/src/views/client/WalletTransactionCard.vue` | 341 | 组件:WalletTransactionCard · 根:div · props · emits · 定义:WalletTransactionRow,emit · ⚑MOCK |
| `admin/src/views/client/WalletWithdrawModal.vue` | 89 | 组件:WalletWithdrawModal · 根:a-modal · props · emits · 定义:props,emit,amountModel · ⚑MOCK |
| `admin/src/views/client/ai-config.vue` | 468 | 组件:ai-config · 根:div · 定义:route,activeTab,showHelp,loadingModels,loadError,needsConfigNote,quotaUsed,quotaTotal · 依赖:./AiConfigDetailModal.vue,./AiConfigHelpModal.vue,./AiConfigModelGrid.vue,./AiConfigSceneTable.vue,./AiConfigUsageChart.vue · ⚑MOCK/DEGRADED |
| `admin/src/views/client/ai-scenarios.vue` | 155 | 组件:ai-scenarios · 根:YdPage · 定义:router,Candidate,ScenarioRow,loading,saving,tenantName,scenarios,localOverrides · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/aitoearn-engage.vue` | 447 | 组件:aitoearn-engage · 根:YdPage · 定义:InteractionRow,loading,pulling,sendingId,regeneratingId,items,replyEdits,capabilityRef · 依赖:@/api,@/components/tenant/AitoearnCapabilityBar.vue,@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/client/assistant.vue` | 193 | 组件:assistant · 根:YdPage · 定义:tenantBrand,ubrainCtx,pageTitle,Msg,input,loading,listEl,samples · 依赖:@/components/youding,@/composables/useTenantBrand,@/composables/useUbrainChatContext,@/utils/api · ⚑MOCK |
| `admin/src/views/client/attribution.vue` | 580 | 组件:attribution · 根:div · 定义:period,periodOptions,primaryColor,closeRateColor,ChannelConversion,ChannelReport,KeywordItem,AiEngineItem · 依赖:./AttributionChannelCharts.vue,./AttributionFunnelTable.vue,./AttributionGaugeRow.vue,./AttributionInsightTables.vue,./AttributionKpiRow.vue · ⚑MOCK |
| `admin/src/views/client/audit-log.vue` | 248 | 组件:audit-log · 根:YdPage · 定义:AuditItem,AuditPayload,router,loading,items,total,page,pageSize · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/client/billing.vue` | 575 | 组件:billing · 根:YdPage · 定义:router,activeTab,currentPlanName,planExpiry,tenantId,orders,orderCols,openFaq · 依赖:@/components/youding,@/composables/usePlanPayment,@/utils/api · ⚑DEGRADED |
| `admin/src/views/client/chuhaiji-app.vue` | 469 | 组件:chuhaiji-app · 根:YdPage · 定义:TabId,Msg,router,auth,tab,brandName,pushMode,chatInput · 依赖:@/components/youding,@/constants/sales-assistant-brand,@/stores/auth,@/utils/api · ⚑MOCK |
| `admin/src/views/client/client-tokens-panel.vue` | 669 | 组件:client-tokens-panel · 定义:router,Provider,Pack,CustomRecharge,providers,packs,customRecharge,customAmountYuan · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useAiConnect,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/client/content-detail.vue` | 82 | 组件:content-detail · 根:YdPage · 定义:route,router,loading,error,detail,pageId,isClient,listPath · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/client/content-distribute.vue` | 433 | 组件:content-distribute · 根:div · 定义:router,route,readinessRef,bindHubRef,imageInputRef,contentKind,inputMode,briefText · 依赖:./ContentDistributeInputCard.vue,./ContentDistributeOverseasAlerts.vue,./ContentDistributePreviewCard.vue,./ContentDistributePublishCard.vue,./ContentDistributeTopbar.vue · ⚑MOCK |
| `admin/src/views/client/copilot.model.ts` | 551 | 定义:Msg,UBrainReply,BriefAction,BriefTemplate,OpsSnapshot,GapSkill,ActionAudit,AuditSummary · 依赖:@/constants/sales-assistant-brand,@/utils/api · ⚑MOCK/STUB/DEGRADED |
| `admin/src/views/client/copilot.vue` | 994 | 组件:copilot · 根:main · 定义:tenantBrand,router,route,ubrainCtx,input,loading,briefLoading,briefQuery · 依赖:./CopilotActionAudits.vue,./CopilotAiAlerts.vue,./CopilotAuditSummary.vue,./CopilotBriefPanel.vue,./CopilotExecutionCards.vue · ⚑STUB |
| `admin/src/views/client/coupons.vue` | 393 | 组件:coupons · 根:YdPage · 定义:CouponRow,CreateForm,loading,rows,stats,page,pageSize,hasMore · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/customer-detail.vue` | 339 | 组件:customer-detail · 根:YdPage · 定义:CustomerFinderRecord,route,router,loading,error,detail,customerFinder,assigneesLoading · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/customers.vue` | 693 | 组件:customers · 根:div · 定义:InquiryRow,CustomerAgg,router,loading,rows,currentPage,pageSize,totalPages · 依赖:@/utils/api |
| `admin/src/views/client/dashboard.vue` | 730 | 组件:dashboard · 根:YdPage · 定义:RoadmapPhase,JtbdChecklistItem,TenantOnboardingChecklistItem,TenantCurrentPayload,router,planSnapshot,brand,planName · 依赖:./ClientDashboardActivity.vue,./ClientDashboardChecklist.vue,./ClientDashboardDetailModal.vue,./ClientDashboardFocusCard.vue,./ClientDashboardGreetingStrip.vue |
| `admin/src/views/client/data-export.vue` | 732 | 组件:data-export · 根:div · 定义:ExportHistoryRow,ExportJobApiItem,TYPE_LABELS,STATUS_LABELS,formatFileSize,mapExportJob,rawType,rawStatus · 依赖:./DataExportGrid.vue,./DataExportHistory.vue,./DataExportSchedulePanel.vue,@/utils/api |
| `admin/src/views/client/design-v2-preview.vue` | 252 | 组件:design-v2-preview · 根:div · 定义:route,router,auth,pages,currentPage,syncFromRoute,raw,id · 依赖:@/constants/designPreviewPages,@/stores/auth,@/utils/clientUiEdition · ⚑MOCK |
| `admin/src/views/client/egress.vue` | 322 | 组件:egress · 根:YdPage · 定义:loading,requesting,buying,tenantId,pollTimer,retryingId,EgressSlot,EgressSummary · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/client/email-campaigns.vue` | 512 | 组件:email-campaigns · 根:YdPage · 定义:CampaignRow,TimelineEvent,router,loading,status,kpiData,campaigns,timelineEvents · 依赖:./EmailCampaignsKpiCards.vue,./EmailCampaignsSidePanel.vue,./EmailCampaignsTable.vue,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/email-center.vue` | 420 | 组件:email-center · 根:YdPage · 定义:tab,loading,acting,lastActionNote,stats,statsEntries,statusCount,by · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/email-tracking.vue` | 809 | 组件:email-tracking · 根:YdPage · 定义:OpenEvent,ClickEvent,TrackingStats,loading,stats,openEvents,clickEvents,openSearch · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/export-quote.vue` | 105 | 组件:export-quote · 根:YdPage · 定义:router,loading,quote,form,generate,res,copyText · 依赖:@/api/cross-border,@/components/youding · ⚑MOCK |
| `admin/src/views/client/foreign-trade-team.vue` | 137 | 组件:foreign-trade-team · 根:YdPage · 定义:router,loading,note,experts,data,PROMPTS,askExpert,q · 依赖:@/api/foreign-trade,@/components/common/SkeletonCard.vue,@/components/youding,@/constants/sales-assistant-brand |
| `admin/src/views/client/forum-qa.vue` | 179 | 组件:forum-qa · 根:YdPage · 定义:ForumConfig,loading,saving,sidecar,config,form,bridgeMode,bridgeText · 依赖:@/api/forum,@/components/youding · ⚑MOCK |
| `admin/src/views/client/geo-visibility.vue` | 651 | 组件:geo-visibility · 根:div · 定义:GeoVisibilityDashboard,UnifiedGeoScore,GscAdsStatus,ProbeModel,loading,dash,unified,gscStatus · 依赖:./GeoAttribution.vue,./GeoMidInsights.vue,./GeoProbes.vue,./GeoProductMentions.vue,./GeoScoreModels.vue |
| `admin/src/views/client/help-center.vue` | 502 | 组件:help-center · 根:YdPage · 定义:router,searchQuery,quickTags,links,categories,popularArticles · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/client/integrations.vue` | 585 | 组件:integrations · 根:div · 定义:CapabilityItem,IntegrationViewItem,router,activeTab,detailVisible,selectedIntegration,loading,loadError · 依赖:@/utils/api,@/utils/integrationHonesty · ⚑STUB |
| `admin/src/views/client/invoices.vue` | 444 | 组件:invoices · 根:div · 定义:InvoiceLineItem,InvoiceItem,MonthlyBucket,detailVisible,applyModalVisible,selectedInvoice,period,loading · 依赖:./InvoiceApplyModal.vue,./InvoiceDetailModal.vue,./InvoicesHistoryTable.vue,./InvoicesPaymentHistory.vue,./InvoicesStatsRow.vue |
| `admin/src/views/client/knowledge.vue` | 391 | 组件:knowledge · 根:div · 定义:KbFile,KbCategory,loading,error,searchQ,activeCategory,info,categories · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/layout.vue` | 997 | 组件:layout · 根:div · 定义:router,route,authStore,sidebarCollapsed,mobileSidebarOpen,searchOpen,notifOpen,userOpen · 依赖:@/layout/ClientShellLayout.vue,@/stores/auth · ⚑MOCK |
| `admin/src/views/client/merchant-profiles.vue` | 867 | 组件:merchant-profiles · 根:div · 定义:MerchantProfile,loading,submitting,profiles,pagination,drawerVisible,drawerData,modalVisible · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/messages.vue` | 406 | 组件:messages · 根:div · 定义:NotiItem,loading,items,unreadCount,load,data,markOne,markAll · 依赖:@/utils/api |
| `admin/src/views/client/nav-portal.vue` | 494 | 组件:nav-portal · 根:div · 定义:router,NavPage,NavGroup,workflowSteps,groups,adminTools,growthTools,goToday · ⚑MOCK/DEGRADED |
| `admin/src/views/client/notifications.vue` | 774 | 组件:notifications · 根:YdPage · 定义:Notification,StatsResponse,loading,markAllLoading,notifications,stats,readFilter,typeFilter · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/client/onboarding.vue` | 615 | 组件:onboarding · 根:YdPage · 定义:UploadedProductImage,AutopilotResult,AutopilotStep,ONBOARDING_PENDING_KEY,router,route,loading,currentStep · 依赖:./OnboardingStepComplete.vue,./OnboardingStepFirstPublish.vue,./OnboardingStepImBinding.vue,./OnboardingStepSiteBuilder.vue,./OnboardingStepWangcaiPreview.vue |
| `admin/src/views/client/ops-center.vue` | 693 | 组件:ops-center · 根:div · 定义:OpsDimension,OpsModule,OpsStats,OpsOverview,iconMap,getIcon,defaultStats,stats · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/order-create.vue` | 127 | 组件:order-create · 根:YdPage · 定义:QuoteRow,router,loading,convertingId,rows,columns,unwrapList,d · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/client/order-detail.vue` | 466 | 组件:order-detail · 根:YdPage · 定义:route,router,loading,saving,depositBusy,trackingBusy,error,detail · 依赖:@/components/youding,@/utils/api · ⚑MOCK/STUB |
| `admin/src/views/client/orders.vue` | 785 | 组件:orders · 根:div · 定义:router,loading,rows,page,pageSize,hasMore,statusFilter,searchNumber · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/page-flow-map.vue` | 751 | 组件:page-flow-map · 根:div · 定义:PageItem,router,activeFilter,filterOptions,journeys,groups,pages,flowRows · 依赖:@/constants/designPageRouteRegistry |
| `admin/src/views/client/plan-gate.vue` | 240 | 组件:plan-gate · 根:YdPage · 定义:route,router,featureKey,fromPath,gateInfo,PayReadiness,payProbe,readinessLabel · 依赖:@/api/admin-bff,@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/client/product-candidates.vue` | 124 | 组件:product-candidates · 根:YdPage · 定义:ProductCandidate,router,loading,importing,items,categories,total,page · 依赖:@/api/cross-border,@/components/youding · ⚑MOCK |
| `admin/src/views/client/product-detail.vue` | 529 | 组件:product-detail · 根:div · 定义:route,router,loading,error,detail,productId,isClient,listPath · 依赖:@/utils/api |
| `admin/src/views/client/product-faqs.vue` | 555 | 组件:product-faqs · 根:div · 定义:FaqItem,ProductOption,loading,submitting,faqList,products,selectedProductId,pagination · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/profile.vue` | 554 | 组件:profile · 根:YdPage · 定义:router,loading,error,profile,avatarInput,displayName,emailValue,usernameValue · 依赖:@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/client/project-architecture.vue` | 25 | 组件:project-architecture · 根:div · ⚑STUB |
| `admin/src/views/client/queues/FulfillmentDetailDrawer.vue` | 104 | 组件:FulfillmentDetailDrawer · 根:div · props · emits · 定义:props,emit,trackingNumberRef,copyBtnState,copyTrackingNumber,text |
| `admin/src/views/client/queues/FulfillmentFilterBar.vue` | 63 | 组件:FulfillmentFilterBar · 根:section · props · emits · 定义:props,emit,searchQuery,statusFilter · ⚑MOCK |
| `admin/src/views/client/queues/FulfillmentKpiStrip.vue` | 72 | 组件:FulfillmentKpiStrip · 根:section · props |
| `admin/src/views/client/queues/FulfillmentTable.vue` | 122 | 组件:FulfillmentTable · 根:section · props · emits · 定义:FqRecord,emit |
| `admin/src/views/client/queues/FulfillmentTopbar.vue` | 28 | 组件:FulfillmentTopbar · 根:header · emits · 定义:emit |
| `admin/src/views/client/queues/InquiriesDetailDrawer.vue` | 109 | 组件:InquiriesDetailDrawer · 根:div · props · emits · 定义:DetailRow,emit · 依赖:@/api/cross-border |
| `admin/src/views/client/queues/InquiriesFilterBar.vue` | 66 | 组件:InquiriesFilterBar · 根:section · props · emits · 定义:Option,emit · ⚑MOCK |
| `admin/src/views/client/queues/InquiriesHeader.vue` | 102 | 组件:InquiriesHeader · 根:header · props · emits · 定义:emit |
| `admin/src/views/client/queues/InquiriesImapModal.vue` | 63 | 组件:InquiriesImapModal · 根:div · props · emits · 定义:emit |
| `admin/src/views/client/queues/InquiriesPipelineBar.vue` | 100 | 组件:InquiriesPipelineBar · 根:section · props · emits · 定义:emit · 依赖:@/api/cross-border |
| `admin/src/views/client/queues/InquiriesTable.vue` | 98 | 组件:InquiriesTable · 根:div · props · emits · 定义:InquiryRow,Pagination,emit |
| `admin/src/views/client/queues/PublishQueueSauPanel.vue` | 246 | 组件:PublishQueueSauPanel · 根:section · props |
| `admin/src/views/client/queues/PublishQueueStats.vue` | 138 | 组件:PublishQueueStats · 根:div · props · 定义:PublishQueueStatsData |
| `admin/src/views/client/queues/PublishQueueTable.vue` | 371 | 组件:PublishQueueTable · 根:div · props · emits · 定义:PublishQueueTableRow,emit |
| `admin/src/views/client/queues/fulfillment.vue` | 326 | 组件:fulfillment · 根:div · 定义:router,loading,actionLoadingId,rows,statusFilter,searchQuery,exceptionOpenId,selectedOrder · 依赖:./FulfillmentDetailDrawer.vue,./FulfillmentFilterBar.vue,./FulfillmentKpiStrip.vue,./FulfillmentTable.vue,./FulfillmentTopbar.vue |
| `admin/src/views/client/queues/inquiries.vue` | 572 | 组件:inquiries · 根:div · 定义:BridgeSummary,InquiryBridgeStatus,PipelineSummary,ReplyDraft,router,tablePanelRef,showColumnSettings,statusOptions · 依赖:./InquiriesDetailDrawer.vue,./InquiriesFilterBar.vue,./InquiriesHeader.vue,./InquiriesImapModal.vue,./InquiriesPipelineBar.vue · ⚑MOCK/STUB |
| `admin/src/views/client/queues/publish-task-detail.vue` | 161 | 组件:publish-task-detail · 根:YdPage · 定义:PublishTaskLike,route,router,loading,retrying,error,detail,taskId · 依赖:@/components/youding,@/utils/api,@/utils/publishTaskDisplay |
| `admin/src/views/client/queues/publish.vue` | 415 | 组件:publish · 根:div · 定义:PublishTaskLike,PublishUiPhase,router,loading,retryingId,rows,scheduledItems,stats · 依赖:./PublishQueueSauPanel.vue,./PublishQueueStats.vue,./PublishQueueTable.vue,@/utils/api,@/utils/publishTaskDisplay |
| `admin/src/views/client/quote-detail.vue` | 168 | 组件:quote-detail · 根:YdPage · 定义:route,router,loading,saving,converting,error,detail,nextStatus · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/referral.vue` | 636 | 组件:referral · 根:div · 定义:ReferralStats,ReferralRecord,RewardTypeRow,LeaderboardRow,codeLoading,loading,generating,code · 依赖:./ReferralProgress.vue,./ReferralRewardGrid.vue,./ReferralSharePanel.vue,./ReferralStatsRow.vue,./ReferralTableSection.vue |
| `admin/src/views/client/refunds.vue` | 774 | 组件:refunds · 根:div · 定义:RefundRow,RefundStats,loading,rows,page,pageSize,hasMore,statusFilter · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/reviews.vue` | 688 | 组件:reviews · 根:div · 定义:ReviewItem,ReviewStats,loading,submitting,reviews,pagination,stats,statusFilter · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/sales-pipeline.vue` | 477 | 组件:sales-pipeline · 根:div · 定义:Stage,Inquiry,router,loading,listLoading,busyId,piBusyId,piOpen · 依赖:./SalesPipelineDetailModal.vue,./SalesPipelineKanban.vue,./SalesPipelineKpiStrip.vue,./SalesPipelinePiDrawer.vue,./SalesPipelineSidebar.vue |
| `admin/src/views/client/security-settings.vue` | 941 | 组件:security-settings · 根:YdPage · 定义:router,loading,saving,me,form,confirmPassword,isAdmin,role · 依赖:@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/client/seo-keywords.vue` | 90 | 组件:seo-keywords · 根:YdPage · 定义:router,loading,seeding,preview,belts,b,load,res · 依赖:@/api/cross-border,@/components/youding |
| `admin/src/views/client/shortcuts.vue` | 761 | 组件:shortcuts · 根:div · 定义:activeTab,shortcutsModalVisible,shortcutGroups,OnboardingTask,OnboardingStep,OnboardingStatus,OnboardingItem,FALLBACK_ITEMS · 依赖:@/utils/api · ⚑DEGRADED |
| `admin/src/views/client/site-editor-lab.vue` | 372 | 组件:site-editor-lab · 根:YdPage · 定义:JtbdChecklistItem,SiteSeoFields,VisualStudioStatus,router,loading,visualStudioLoading,visualStudioStatus,seoSaving · 依赖:../../../../utils/l-pro-publish-gate,@/api/admin-bff,@/components/common/SkeletonCard.vue,@/components/site-builder/JtbdSiteChecklist.vue,@/components/site-builder/SiteEditorGapPanel.vue · ⚑DEGRADED |
| `admin/src/views/client/team.vue` | 297 | 组件:team · 根:div · 定义:MemberRow,router,loading,members,keyword,inviteVisible,detailVisible,detailMember · 依赖:./TeamActivityLog.vue,./TeamHeader.vue,./TeamInviteModal.vue,./TeamMemberDetailModal.vue,./TeamMemberTable.vue |
| `admin/src/views/client/today-three.vue` | 23 | 组件:today-three · 根:YdPage · 依赖:@/components/client/ClientTodayThreeBoard.vue,@/components/youding,@/composables/useClientTodayThree |
| `admin/src/views/client/token-ledger.vue` | 908 | 组件:token-ledger · 根:div · 定义:router,BalanceData,ReportItem,TrendItem,RechargePack,balance,monthUsed,monthRecharge · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/client/tokens.vue` | 678 | 组件:tokens · 根:YdPage · 定义:router,Provider,Pack,CustomRecharge,providers,packs,customRecharge,customAmountYuan · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useAiConnect,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/client/trade-quotation.vue` | 635 | 组件:trade-quotation · 根:div · 定义:router,loading,quotes,filters,stats,list,count,filteredQuotes · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/trade-tools.vue` | 316 | 组件:trade-tools · 根:YdPage · 定义:TradeTool,tenantPlanName,pageSubtitle,base,loadTenantContext,current,activeCategory,searchKeyword · 依赖:./TradeToolCompareBar.vue,./TradeToolCompareModal.vue,./TradeToolFilterBar.vue,./TradeToolGrid.vue,./TradeToolGuideModal.vue |
| `admin/src/views/client/tradeTools.data.ts` | 677 | 定义:TradeTool,TOOLS,CATEGORY_LABELS,CATEGORY_COLORS |
| `admin/src/views/client/traffic-board.vue` | 418 | 组件:traffic-board · 根:YdPage · props · 定义:props,router,period,loading,error,board,detailOpen,detailKind · 依赖:./TrafficBoardChannels.vue,./TrafficBoardConversions.vue,./TrafficBoardDailyTrend.vue,./TrafficBoardDetailDrawer.vue,./TrafficBoardFunnel.vue |
| `admin/src/views/client/video-editor-embed.vue` | 236 | 组件:video-editor-embed · 根:YdPage · 定义:MediaStudioCapabilities,MediaStudioProject,router,route,capabilities,studioProject,handoffLoaded,editorId · 依赖:@/api/cross-border,@/components/youding,@/utils/mediaStudioHandoff,@/utils/resolveMediaAssetUrl · ⚑STUB |
| `admin/src/views/client/video-overseas.vue` | 565 | 组件:video-overseas · 根:YdPage · 定义:MediaStudioCapabilities,VideoDubResult,router,fileRef,uploading,processing,processingPremium,capabilities · 依赖:@/api/cross-border,@/components/youding,@/utils/resolveMediaAssetUrl · ⚑MOCK |
| `admin/src/views/client/video-studio-project-panel.vue` | 135 | 组件:video-studio-project-panel · 根:a-card · props · emits · 定义:props,emit,project,p,segmentCount,segs,outputVideoUrl,url · 依赖:@/api/cross-border,@/utils/resolveMediaAssetUrl |
| `admin/src/views/client/video-studio.vue` | 292 | 组件:video-studio · 根:YdPage · 定义:MediaStudioCapabilities,MediaStudioProject,router,route,loading,projectLoading,capabilities,studioProject · 依赖:@/api/cross-border,@/components/youding,@/views/client/video-studio-project-panel.vue |
| `admin/src/views/client/wallet.vue` | 441 | 组件:wallet · 根:div · 定义:TransactionRow,PayReadiness,payProbe,readinessLabel,map,readinessTagColor,map,loadPayProbe · 依赖:./WalletBalanceHero.vue,./WalletDepositModal.vue,./WalletMonthlyStats.vue,./WalletTransactionCard.vue,./WalletWithdrawModal.vue · ⚑MOCK |
| `admin/src/views/client/wangcai-embed.vue` | 872 | 组件:wangcai-embed · 根:div · 定义:ChatMsg,probeMsg,tenantDomain,draft,asking,messagesEl,messages,preBubbleText · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/client/wangcai-plugin-market.vue` | 450 | 组件:wangcai-plugin-market · 根:YdPage · 定义:route,router,CompanionInstall,PluginItem,items,meta,category,busyId · 依赖:@/components/youding,@/composables/useAiConnect,@/utils/api |
| `admin/src/views/client/workflow-automation.vue` | 1000 | 组件:workflow-automation · 根:div · 定义:WorkflowStatus,HistoryItem,ApiWorkflow,ApiTemplate,iconLucideMap,workflows,templates,loading · 依赖:@/utils/api |
| `admin/src/views/cognitive/dashboard.vue` | 55 | 组件:dashboard · 根:YdPage · 定义:stats,kb,kc,sq,qc,queries,api,doSearch · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/cognitive/expert-system.vue` | 51 | 组件:expert-system · 根:YdPage · 定义:showAdd,p,f,cols,rules,addRule,delRule,doInfer · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/cognitive/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/cognitive/qa-engine.vue` | 103 | 组件:qa-engine · 根:YdPage · 定义:question,loading,chatHistory,hotQs,ask,q,idx,token · 依赖:@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/cognitive/semantic-index.vue` | 120 | 组件:semantic-index · 根:YdPage · 定义:stats,q,df,ic,docs,loadSemanticIndex,r,matchScore · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/compliance/index.vue` | 127 | 组件:index · 根:YdPage · 定义:overview,issuesLoading,issuesTablePanelRef,ui,statCards,o,issueCols,api · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/content/edit.vue` | 400 | 组件:edit · 根:YdPage · 定义:route,router,contentListPath,isEdit,loading,editorLoading,editorError,editorRef · 依赖:@/api,@/components/youding · ⚑MOCK |
| `admin/src/views/content/index.vue` | 321 | 组件:index · 根:YdPage · 定义:route,contentBasePath,contentEditPath,contentDetailPath,contentList,loading,initialLoading,tablePanelRef · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/stores/uiPreferences,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/cross-platform/dashboard.vue` | 318 | 组件:dashboard · 根:div · 定义:loading,capabilityRef,overview,nurture,publish,showEmptyHint,platformColumns,nurtureColumns · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/tenant/AitoearnCapabilityBar.vue,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels |
| `admin/src/views/customers/detail.vue` | 345 | 组件:detail · 根:YdPage · 定义:AssigneeRecord,AssignmentHistoryRecord,CustomerDetail,route,router,loading,error,detail · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/dashboard/DashboardAlerts.vue` | 44 | 组件:DashboardAlerts · props · 定义:DataHonesty · ⚑DEGRADED |
| `admin/src/views/dashboard/DashboardChartsRow.vue` | 62 | 组件:DashboardChartsRow · 根:section · props · 定义:PieLegendItem |
| `admin/src/views/dashboard/DashboardFunnelAdmin.vue` | 107 | 组件:DashboardFunnelAdmin · 根:div · props · emits · 定义:DashboardStats,AdminStats |
| `admin/src/views/dashboard/DashboardInquiriesKeywords.vue` | 99 | 组件:DashboardInquiriesKeywords · 根:div · props · 定义:RecentInquiry,HotKeyword,formatSearchVolume |
| `admin/src/views/dashboard/DashboardKpiGrid.vue` | 28 | 组件:DashboardKpiGrid · 根:section · props · emits · 定义:KpiStat |
| `admin/src/views/dashboard/DashboardProductMySite.vue` | 130 | 组件:DashboardProductMySite · 根:div · props · 定义:ProductStat,DashboardStats |
| `admin/src/views/dashboard/DashboardTodayStrip.vue` | 25 | 组件:DashboardTodayStrip · 根:section · emits |
| `admin/src/views/dashboard/DashboardTopbar.vue` | 19 | 组件:DashboardTopbar · 根:section · props · emits |
| `admin/src/views/dashboard/DashboardWorkbench.vue` | 108 | 组件:DashboardWorkbench · 根:section · props · emits · 定义:WorkbenchTodo · ⚑STUB |
| `admin/src/views/dashboard/index.vue` | 427 | 组件:index · 根:div · 定义:router,authStore,timeRange,loadState,degradedTitle,degradedDetail,timeRanges,stats · 依赖:./DashboardAlerts.vue,./DashboardChartsRow.vue,./DashboardFunnelAdmin.vue,./DashboardInquiriesKeywords.vue,./DashboardKpiGrid.vue · ⚑DEGRADED |
| `admin/src/views/developer/dashboard.vue` | 65 | 组件:dashboard · 根:YdPage · 定义:st,ac,apis,kc,keys,x,openDocs,createKey · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/developer/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/developer/low-code.vue` | 152 | 组件:low-code · 根:YdPage · 定义:showEditor,PaletteItem,components,selectedComponents,templates,addComponent,removeComponent,useTemplate · 依赖:@/components/youding,@/constants/iconCatalog · ⚑MOCK |
| `admin/src/views/developer/plugins.vue` | 147 | 组件:plugins · 根:YdPage · 定义:keyword,cols,plugins,filteredPlugins,showForm,configOpen,configTarget,configForm · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/developer/sdk.vue` | 113 | 组件:sdk · 根:YdPage · 定义:cols,sdks,showForm,form,langColor,m,d,saveSdk · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/edge-cdn/dashboard.vue` | 97 | 组件:dashboard · 根:YdPage · 定义:stats,bandwidth,cols,nodes,loadOverview,d,payload,refresh · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/edge-cdn/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/edge-cdn/nodes.vue` | 104 | 组件:nodes · 根:YdPage · 定义:cols,nodes,showForm,editingId,form,statusColor,editNode,saveNode · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/edge-cdn/preheat.vue` | 119 | 组件:preheat · 根:YdPage · 定义:preheatUrl,nodeScope,submitting,cols,tasks,statusColor,submitPreheat,urls · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/edge-cdn/protocol.vue` | 115 | 组件:protocol · 根:YdPage · 定义:saving,config,saveConfig,d,payload · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/email/EiFolders.vue` | 48 | 组件:EiFolders · 根:aside · props · emits |
| `admin/src/views/email/EiMailDetail.vue` | 95 | 组件:EiMailDetail · 根:section · props · 定义:MailBody,Email · ⚑MOCK |
| `admin/src/views/email/EiMailList.vue` | 77 | 组件:EiMailList · 根:section · props · emits · 定义:MailListItem,MailTab · ⚑MOCK |
| `admin/src/views/email/inbox.vue` | 450 | 组件:inbox · 根:div · 定义:EmailQueueStats,InboxItem,ComposeForm,loading,sending,stats,composeVisible,composeForm · 依赖:./EiFolders.vue,./EiMailDetail.vue,./EiMailList.vue,@/utils/api · ⚑MOCK |
| `admin/src/views/error/403.vue` | 428 | 组件:403 · 根:div · 定义:router,searchQuery,handleSearch,openContactAdmin · ⚑MOCK/STUB |
| `admin/src/views/error/404.vue` | 423 | 组件:404 · 根:div · 定义:router,searchQuery,handleSearch,openFeedback · ⚑MOCK/STUB |
| `admin/src/views/error/500.vue` | 474 | 组件:500 · 根:div · 定义:router,detailsOpen,now,errorId,y,m,d,errorTime |
| `admin/src/views/error/EsEmptyStates.vue` | 59 | 组件:EsEmptyStates · 根:div |
| `admin/src/views/error/EsSkeletonTab.vue` | 76 | 组件:EsSkeletonTab · 根:div · props · emits · 定义:SkeletonCard |
| `admin/src/views/error/EsToastDemo.vue` | 41 | 组件:EsToastDemo · 根:div · props · emits · 定义:ToastDemoItem |
| `admin/src/views/error/error-states.vue` | 294 | 组件:error-states · 根:div · 定义:ToastData,activeTab,toastContainerRef,floatingDotsRef,tabs,skeletonTableRows,skeletonCards,toastDemoItems · 依赖:./EsEmptyStates.vue,./EsSkeletonTab.vue,./EsToastDemo.vue |
| `admin/src/views/experiments/AbTest.vue` | 75 | 组件:AbTest · 根:YdPage · 定义:loading,form,rows,columns,load,token,res,body · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/globalization/culture-adapt.vue` | 121 | 组件:culture-adapt · 根:YdPage · 定义:rtlEnabled,showRegionDetail,regions,fmtCols,formats,runScan,inspect,saveConfig · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/globalization/dashboard.vue` | 131 | 组件:dashboard · 根:YdPage · 定义:batching,showAddLang,nl,loadError,stats,langs,tc,tasks · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api,@/utils/exportCsv · ⚑MOCK |
| `admin/src/views/globalization/glossary.vue` | 136 | 组件:glossary · 根:YdPage · 定义:kw,f,cols,terms,filtered,openAdd,openEdit,save · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/globalization/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/globalization/translator.vue` | 56 | 组件:translator · 根:YdPage · 定义:src,srcLang,batchLoading,batchLines,history,langNames,doTranslate,prompt · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/inquiries/InquiryAuditDrawer.vue` | 117 | 组件:InquiryAuditDrawer · 根:a-drawer · props · emits · 定义:emit,onDateRangeChange,onActorChange,onToAssigneeChange,onPageChange · ⚑MOCK |
| `admin/src/views/inquiries/InquiryExpandedDetail.vue` | 539 | 组件:InquiryExpandedDetail · 根:div · props · emits · ⚑MOCK |
| `admin/src/views/inquiries/InquiryFilterBar.vue` | 233 | 组件:InquiryFilterBar · 根:section · props · emits · 定义:emit,selectTab,onSourceChange · 依赖:@/components/youding,@/composables/useYoudingTableBridge · ⚑MOCK |
| `admin/src/views/inquiries/InquiryHandleDrawer.vue` | 90 | 组件:InquiryHandleDrawer · 根:a-drawer · props · emits · ⚑MOCK |
| `admin/src/views/inquiries/InquiryKpiCards.vue` | 153 | 组件:InquiryKpiCards · 根:section · props · emits |
| `admin/src/views/inquiries/InquiryPageHeader.vue` | 158 | 组件:InquiryPageHeader · 根:section · props · emits · 依赖:@/components/youding,@/composables/useYoudingTableBridge |
| `admin/src/views/inquiries/InquiryReplyModal.vue` | 34 | 组件:InquiryReplyModal · 根:a-modal · props · emits |
| `admin/src/views/inquiries/InquiryTable.vue` | 602 | 组件:InquiryTable · 根:template · props · emits · 依赖:./InquiryExpandedDetail.vue,@/components/common/SkeletonCard.vue,@/composables/useYoudingTableBridge · ⚑MOCK |
| `admin/src/views/inquiries/im-binding.vue` | 313 | 组件:im-binding · 根:YdPage · 定义:PlatformState,platforms,findPlatform,formatTime,loadBindings,list,p,doManualBind · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/inquiries/im-routing.vue` | 622 | 组件:im-routing · 根:YdPage · 定义:router,loading,rows,webhookConfig,wecomSaving,rehearsal5aLoading,rehearsal5bLoading,wecomForm · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/inquiries/index.vue` | 869 | 组件:index · 根:YdPage · 定义:router,authStore,canAssign,list,loading,initialLoading,tablePanelRef,assignees · 依赖:./InquiryAuditDrawer.vue,./InquiryFilterBar.vue,./InquiryHandleDrawer.vue,./InquiryKpiCards.vue,./InquiryPageHeader.vue · ⚑MOCK/STUB |
| `admin/src/views/integrations/AiConfig.vue` | 576 | 组件:AiConfig · 根:YdPage · 定义:AiModelEnrichedRow,providers,models,modelsLoading,probeLoading,rankBusy,showProviderModal,showModelModal · 依赖:@/components/youding,@/utils/aiConfigHelpers,@/utils/aiModelCapability,@/utils/api · ⚑MOCK |
| `admin/src/views/integrations/Feishu.vue` | 126 | 组件:Feishu · 根:YdPage · 定义:loading,bindRaw,logsRaw,bindJson,logsJson,loadAll · 依赖:@/api,@/components/youding,@/utils/api |
| `admin/src/views/international/dashboard.vue` | 280 | 组件:dashboard · 根:YdPage · 定义:loading,tablePanelRef,ui,mode,loadError,stats,statCards,regionData · 依赖:@/components/common/PageDataBar.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/composables/usePageData,@/constants/iconCatalog |
| `admin/src/views/international/index.vue` | 3 | 组件:index · 根:router-view |
| `admin/src/views/international/inquiries.vue` | 257 | 组件:inquiries · 根:YdPage · 定义:loading,list,page,pageSize,total,tablePanelRef,ui,tablePagination · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/constants/countryOptions,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/international/sites.vue` | 376 | 组件:sites · 根:YdPage · 定义:IntlSiteRow,FREQ_TO_MINUTES,MINUTES_TO_FREQ,FREQ_LABELS,LANG_TO_CODE,CODE_TO_LANG,loading,list · 依赖:@/components/youding,@/constants/countryOptions,@/stores/uiPreferences,@/utils/aiConfigHelpers,@/utils/api · ⚑MOCK |
| `admin/src/views/landing/LandingContactSection.vue` | 130 | 组件:LandingContactSection · 根:section · props · emits · ⚑MOCK/STUB |
| `admin/src/views/landing/LandingFooter.vue` | 150 | 组件:LandingFooter · 根:footer · props · emits |
| `admin/src/views/landing/LandingHeader.vue` | 115 | 组件:LandingHeader · 根:header · emits |
| `admin/src/views/landing/LandingHeroSection.vue` | 228 | 组件:LandingHeroSection · 根:section · props · emits |
| `admin/src/views/landing/LandingPricingSection.vue` | 217 | 组件:LandingPricingSection · 根:section · props · emits |
| `admin/src/views/landing/index.vue` | 643 | 组件:index · 根:YdPage · 定义:copy,mock,router,route,UTM_QUERY_KEYS,utmCapture,captureUtmFromQuery,raw · 依赖:./LandingContactSection.vue,./LandingFooter.vue,./LandingHeader.vue,./LandingHeroSection.vue,./LandingPricingSection.vue · ⚑MOCK/DEGRADED |
| `admin/src/views/login/LoginBrandColumn.vue` | 301 | 组件:LoginBrandColumn · 根:div |
| `admin/src/views/login/LoginOAuthRow.vue` | 133 | 组件:LoginOAuthRow · 根:div · props · emits · 定义:OAuthItem · 依赖:@/api/oauth |
| `admin/src/views/login/LoginSocialButtons.vue` | 59 | 组件:LoginSocialButtons · 根:div · emits · 依赖:@/api/oauth |
| `admin/src/views/login/forgot-password.vue` | 160 | 组件:forgot-password · 根:div · 定义:router,email,code,password,sending,submitting,errorMsg,okMsg · ⚑MOCK |
| `admin/src/views/login/index.vue` | 1020 | 组件:index · 根:div · 定义:OAuthProvider,LS_LOCK,LS_FAIL,router,route,auth,portalCopy,isLoginMode · 依赖:./LoginBrandColumn.vue,./LoginOAuthRow.vue,./LoginSocialButtons.vue,@/api/emailAuth,@/api/oauth · ⚑MOCK |
| `admin/src/views/login/oauth-callback.vue` | 117 | 组件:oauth-callback · 根:div · 定义:OAuthProvider,route,router,auth,statusText,redirectTarget,parsed,raw · 依赖:@/api/oauth,@/api/oauthBindings,@/stores/auth,@/utils/postLoginNavigation · ⚑DEGRADED |
| `admin/src/views/logistics/dashboard.vue` | 135 | 组件:dashboard · 根:YdPage · 定义:router,tablePanelRef,tableLoading,ui,st,freightStats,orders,cols · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api |
| `admin/src/views/logistics/freight-calc.vue` | 101 | 组件:freight-calc · 根:YdPage · 定义:product,weight,distance,from,to,fee,priceMap,labelMap · 依赖:@/components/youding,@/utils/api · ⚑DEGRADED |
| `admin/src/views/logistics/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/logistics/lbs-routing.vue` | 126 | 组件:lbs-routing · 根:YdPage · 定义:origin,dest,weight,mode,loading,result,history,hcol · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/logistics/orders-track.vue` | 266 | 组件:orders-track · 根:YdPage · 定义:Row,loading,rows,tablePanelRef,ui,cols,route,CLOSED_STATUSES · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/logistics/quotation.vue` | 195 | 组件:quotation · 根:YdPage · 定义:showCreate,tablePanelRef,tableLoading,ui,f,previewModal,cols,quotes · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/media-factory/charts.vue` | 184 | 组件:charts · 根:YdPage · 定义:chartType,chartTitle,rawData,generating,chartData,generated,fetchCharts,data · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/media-factory/components/ChartPanel.vue` | 13 | 组件:ChartPanel · 根:div · props |
| `admin/src/views/media-factory/components/KpiStatCard.vue` | 53 | 组件:KpiStatCard · 根:div · props · emits |
| `admin/src/views/media-factory/components/MediaCard.vue` | 158 | 组件:MediaCard · 根:a-card · props · 定义:cloudLabel · 依赖:../types · ⚑MOCK |
| `admin/src/views/media-factory/components/MoneyPrinterGenModal.vue` | 207 | 组件:MoneyPrinterGenModal · 根:a-modal · emits · 定义:open,emit,step,aiWriting,gen,voiceText,map,reset · 依赖:@/utils/api · ⚑MOCK |
| `admin/src/views/media-factory/dashboard.vue` | 424 | 组件:dashboard · 根:YdPage · 定义:authStore,isPlatformAdmin,TenantScopeOption,tenantScopeFilter,tenantScopeOptions,tenantNameMap,tenantScopeLabel,name · 依赖:./components/MediaCard.vue,./components/MoneyPrinterGenModal.vue,./types,@/components/media/VideoPlayer.vue,@/components/youding · ⚑MOCK/DEGRADED |
| `admin/src/views/media-factory/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/media-factory/matrix-overview.vue` | 573 | 组件:matrix-overview · 根:YdPage · 定义:initialLoading,workerReady,caps,sauStatus,scheduled,queueStats,tasks,mediaStats · 依赖:./components/ChartPanel.vue,./components/KpiStatCard.vue,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer |
| `admin/src/views/media-factory/render-queue.vue` | 272 | 组件:render-queue · 根:YdPage · 定义:qcol,queue,fetchQueue,data,list,statusColor,formatRetention,sec · 依赖:@/components/youding,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/media-factory/task-center.vue` | 434 | 组件:task-center · 根:YdPage · 定义:refreshing,tableLoading,queuedLoading,statusFilter,current,pageSize,total,tasks · 依赖:@/components/youding,@/utils/api · ⚑DEGRADED |
| `admin/src/views/media-factory/tts.vue` | 141 | 组件:tts · 根:YdPage · 定义:text,voice,speed,volume,loading,voiceLabel,m,voiceColor · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/media-factory/types.ts` | 73 | 定义:MediaItem,KpiStats,TenantScopeOption,CapabilityPlatform,PublishTaskRow,QueueStats,CLOUD_STATUS_LABEL |
| `admin/src/views/messages/index.vue` | 488 | 组件:index · 根:YdPage · 定义:ChatSession,ChatMessage,authStore,DEFAULT_USER_ID,currentUserId,loading,messagesLoading,sendLoading · 依赖:@/components/youding,@/stores/auth,@/utils/api · ⚑MOCK/STUB |
| `admin/src/views/news/index.vue` | 369 | 组件:index · 根:YdPage · 定义:Row,loading,saving,rows,filterStatus,pagination,tablePanelRef,ui · 依赖:@/api,@/components/youding,@/stores/uiPreferences · ⚑MOCK |
| `admin/src/views/operations/traffic-board.vue` | 42 | 组件:traffic-board · 根:YdPage · 定义:auth,apiPath,title,r,subtitle · 依赖:@/components/traffic/TrafficBoardPanel.vue,@/components/youding,@/stores/auth,@/utils/api |
| `admin/src/views/partner/performance.vue` | 309 | 组件:performance · 根:YdPage · 定义:DashboardStats,SubordinateItem,TrendItem,ClientRow,formatMoney,router,route,portalBase · 依赖:@/components/youding,@/stores/auth,@/utils/api,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/products/ProductDetailModal.vue` | 126 | 组件:ProductDetailModal · 根:Teleport · props · emits · 定义:emit |
| `admin/src/views/products/ProductsGrid.vue` | 110 | 组件:ProductsGrid · 根:div · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/products/ProductsPagination.vue` | 42 | 组件:ProductsPagination · 根:div · props · emits · 定义:emit |
| `admin/src/views/products/ProductsTable.vue` | 120 | 组件:ProductsTable · 根:div · props · emits · 定义:emit |
| `admin/src/views/products/ProductsToolbar.vue` | 78 | 组件:ProductsToolbar · 根:div · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/products/categories.vue` | 390 | 组件:categories · 根:YdPage · 定义:treeRows,loading,saveLoading,loadError,expandedKeys,showAddModal,editingCategory,categoryForm · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/utils/ydModal · ⚑MOCK/DEGRADED |
| `admin/src/views/products/edit.vue` | 685 | 组件:edit · 根:YdPage · 定义:AicaigouCategoryPath,route,router,CLIENT_CONTENT_ROUTE,isEdit,isClientShell,productListPath,loading · 依赖:@/api,@/components/products/AicaigouCategoryCascade.vue,@/components/youding,@/utils/aicaigouCategoryTree,@/utils/productSpecPresets · ⚑MOCK |
| `admin/src/views/products/index.vue` | 504 | 组件:index · 根:YdPage · 定义:route,isClientShell,productBasePath,productEditPath,productDetailPath,products,categories,loading · 依赖:./ProductDetailModal.vue,./ProductsGrid.vue,./ProductsPagination.vue,./ProductsTable.vue,./ProductsToolbar.vue |
| `admin/src/views/publish/unified.vue` | 848 | 组件:unified · 根:YdPage · 定义:route,DraftRow,tenantId,form,masterId,saving,publishing,publishingVariants · 依赖:@/api/foreign-trade,@/components/youding,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/quotes/index.vue` | 515 | 组件:index · 根:YdPage · 定义:QuoteRow,CreateQuoteForm,loading,submitting,statusSubmitting,rows,page,pageSize · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/referral/dashboard.vue` | 710 | 组件:dashboard · 根:YdPage · 定义:referralCode,shareLink,base,stats,rewardSteps,progressPercent,progressGradient,columns · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/referral/index.vue` | 7 | 组件:index · 根:router-view |
| `admin/src/views/referral/redemption-admin.vue` | 100 | 组件:redemption-admin · 根:YdPage · 定义:loading,items,tablePanelRef,ui,tablePagination,columns,loadPending,data · 依赖:@/components/youding,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/referral/rules.vue` | 261 | 组件:rules · 根:YdPage · 定义:steps · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/sales/AutoNegotiator.vue` | 750 | 组件:AutoNegotiator · 根:YdPage · 定义:parseApiJson,text,stats,loading,pageLoadError,workerPulling,workerRehearsalLoading,workerConfig · 依赖:./AutoNegotiatorEmptyWorkspace.vue,./AutoNegotiatorNegotiationDetail.vue,./AutoNegotiatorNegotiationList.vue,./AutoNegotiatorQuoteModal.vue,./AutoNegotiatorSettingsModal.vue |
| `admin/src/views/sales/AutoNegotiatorEmptyWorkspace.vue` | 36 | 组件:AutoNegotiatorEmptyWorkspace · 根:div · props · emits · 定义:emit |
| `admin/src/views/sales/AutoNegotiatorNegotiationDetail.vue` | 155 | 组件:AutoNegotiatorNegotiationDetail · 根:div · props · emits · 定义:replyContent,emit · 依赖:@/types/sales · ⚑MOCK |
| `admin/src/views/sales/AutoNegotiatorNegotiationList.vue` | 99 | 组件:AutoNegotiatorNegotiationList · 根:div · props · emits · 定义:activeTab,searchQuery,emit · 依赖:@/components/youding,@/types/sales · ⚑MOCK |
| `admin/src/views/sales/AutoNegotiatorQuoteModal.vue` | 102 | 组件:AutoNegotiatorQuoteModal · 根:a-modal · props · emits · 定义:OptionItem,open,emit · 依赖:@/types/sales |
| `admin/src/views/sales/AutoNegotiatorSettingsModal.vue` | 44 | 组件:AutoNegotiatorSettingsModal · 根:a-modal · props · emits · 定义:open,emit · 依赖:@/types/sales |
| `admin/src/views/sales/AutoNegotiatorStats.vue` | 51 | 组件:AutoNegotiatorStats · props · emits · 定义:emit · 依赖:./autoNegotiatorTypes,@/components/youding |
| `admin/src/views/sales/AutoNegotiatorWebhookDrawer.vue` | 71 | 组件:AutoNegotiatorWebhookDrawer · 根:a-drawer · props · emits · 定义:emit · 依赖:./autoNegotiatorTypes |
| `admin/src/views/sales/AutoNegotiatorWorkerCard.vue` | 45 | 组件:AutoNegotiatorWorkerCard · 根:a-card · props · emits · 定义:emit · 依赖:./autoNegotiatorTypes |
| `admin/src/views/sales/CompanyAccount360.vue` | 50 | 组件:CompanyAccount360 · 根:YdPage · 定义:authHeaders,items,showCreate,columns,fetchData,r,j,handleTableChange · 依赖:@/components/youding |
| `admin/src/views/sales/CustomerFinder.vue` | 746 | 组件:CustomerFinder · 根:YdPage · 定义:ChannelStatus,router,stats,filters,searchForm,loading,showSearchModal,showDetailDrawer · 依赖:./CustomerFinderCharts.vue,./CustomerFinderDetailDrawer.vue,./CustomerFinderFilterPanel.vue,./CustomerFinderIntelPanel.vue,./CustomerFinderKpiDrawer.vue · ⚑MOCK/DEGRADED |
| `admin/src/views/sales/CustomerFinderCharts.vue` | 30 | 组件:CustomerFinderCharts · 根:div · ⚑MOCK |
| `admin/src/views/sales/CustomerFinderDetailDrawer.vue` | 37 | 组件:CustomerFinderDetailDrawer · 根:Teleport · props · emits · 定义:emit · 依赖:@/components/sales/CustomerDetail.vue,@/types/sales |
| `admin/src/views/sales/CustomerFinderFilterPanel.vue` | 82 | 组件:CustomerFinderFilterPanel · 根:section · props · 定义:OptionItem · 依赖:@/types/sales · ⚑MOCK |
| `admin/src/views/sales/CustomerFinderIntelPanel.vue` | 27 | 组件:CustomerFinderIntelPanel · 根:section · props · emits · 定义:emit · 依赖:@/components/sales/CustomsBuyerResearchPanel.vue |
| `admin/src/views/sales/CustomerFinderKpiDrawer.vue` | 22 | 组件:CustomerFinderKpiDrawer · 根:a-drawer · props · 定义:DetailRow,open |
| `admin/src/views/sales/CustomerFinderKpiGrid.vue` | 48 | 组件:CustomerFinderKpiGrid · 根:section · props · 定义:KpiStats |
| `admin/src/views/sales/CustomerFinderSearchModal.vue` | 96 | 组件:CustomerFinderSearchModal · 根:Teleport · props · emits · 定义:OptionItem,emit · 依赖:@/components/whatsfinds/SearchSyntaxPreview.vue,@/types/sales · ⚑MOCK |
| `admin/src/views/sales/CustomerFinderSidecarBanner.vue` | 24 | 组件:CustomerFinderSidecarBanner · 根:div · props · 定义:CfSidecarBanner |
| `admin/src/views/sales/CustomerFinderTable.vue` | 116 | 组件:CustomerFinderTable · 根:section · props · 依赖:@/types/sales |
| `admin/src/views/sales/CustomerFinderTopbar.vue` | 13 | 组件:CustomerFinderTopbar · 根:section |
| `admin/src/views/sales/EmailAnalyticsPanels.vue` | 53 | 组件:EmailAnalyticsPanels · 根:a-row |
| `admin/src/views/sales/EmailAutomation.vue` | 717 | 组件:EmailAutomation · 根:YdPage · 定义:stats,activeTab,loadingCampaigns,loadingEmails,sending,showComposeModal,showCampaignModal,showEmailDrawer · 依赖:./EmailAnalyticsPanels.vue,./EmailCampaignModal.vue,./EmailCampaignTable.vue,./EmailComposeModal.vue,./EmailListTable.vue |
| `admin/src/views/sales/EmailCampaignModal.vue` | 133 | 组件:EmailCampaignModal · 根:a-modal · props · emits · 定义:CampaignForm,emit · ⚑MOCK |
| `admin/src/views/sales/EmailCampaignTable.vue` | 120 | 组件:EmailCampaignTable · 根:a-card · props · emits · 定义:emit |
| `admin/src/views/sales/EmailComposeModal.vue` | 103 | 组件:EmailComposeModal · 根:a-modal · props · emits · 定义:ComposeForm,emit · ⚑MOCK |
| `admin/src/views/sales/EmailListTable.vue` | 113 | 组件:EmailListTable · 根:a-card · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/sales/EmailStatsCards.vue` | 89 | 组件:EmailStatsCards · 根:div · props · emits · 定义:emit |
| `admin/src/views/sales/EmailTemplateGrid.vue` | 125 | 组件:EmailTemplateGrid · 根:div · props · emits · 定义:emit · 依赖:@/types/sales |
| `admin/src/views/sales/OpportunityBoard.vue` | 105 | 组件:OpportunityBoard · 根:YdPage · 定义:stages,stageColor,authHeaders,opportunities,total,page,loading,filterStage · 依赖:@/components/youding · ⚑MOCK/STUB |
| `admin/src/views/sales/QuotesPanel.vue` | 52 | 组件:QuotesPanel · 根:YdPage · 定义:authHeaders,items,columns,fetchData,r,j,approve,r · 依赖:@/components/youding |
| `admin/src/views/sales/RfqPanel.vue` | 91 | 组件:RfqPanel · 根:YdPage · 定义:authHeaders,items,total,page,columns,fetchData,params,l · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/sales/SalesDealsTable.vue` | 199 | 组件:SalesDealsTable · 根:section · props · emits · 定义:Deal,emit |
| `admin/src/views/sales/SalesFollowUpsPanel.vue` | 269 | 组件:SalesFollowUpsPanel · 根:section · props · emits · 定义:Lead,emit |
| `admin/src/views/sales/SalesKpiStrip.vue` | 202 | 组件:SalesKpiStrip · 根:section · props · emits · 定义:emit |
| `admin/src/views/sales/SalesPerformancePanel.vue` | 244 | 组件:SalesPerformancePanel · 根:section · props · emits · 定义:emit |
| `admin/src/views/sales/SalesTaskCenter.vue` | 60 | 组件:SalesTaskCenter · 根:YdPage · 定义:authHeaders,items,columns,fetchData,params,r,j,updateStatus · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/sales/SalesTopbar.vue` | 129 | 组件:SalesTopbar · 根:section · emits · 定义:emit |
| `admin/src/views/sales/autoNegotiatorTypes.ts` | 18 | 定义:NegotiatorWorkerConfig,NegotiatorStats,NegotiatorStatFilter |
| `admin/src/views/sales/dashboard.vue` | 411 | 组件:dashboard · 根:YdPage · 定义:router,goSalesDetail,Lead,tk,authHeaders,currentMonth,stats,monthlyProcessPercent · 依赖:./SalesDealsTable.vue,./SalesFollowUpsPanel.vue,./SalesKpiStrip.vue,./SalesPerformancePanel.vue,./SalesTopbar.vue |
| `admin/src/views/sales/index.vue` | 30 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/seo-matrix/PublishAiGeneratorPanel.vue` | 235 | 组件:PublishAiGeneratorPanel · 根:div · props · emits · 定义:props,emit,contentTypeModel,styleModel,languageModel,wordCountModel,topicModel,generatedContentModel · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/seo-matrix/PublishConnectModal.vue` | 233 | 组件:PublishConnectModal · 根:a-modal · props · emits · 定义:props,emit,openModel,connectTabModel,formField,nurtureField,username,password · 依赖:./PublishTypes · ⚑MOCK |
| `admin/src/views/seo-matrix/PublishDetailModal.vue` | 39 | 组件:PublishDetailModal · 根:a-modal · props · emits · 定义:props,emit,openModel · 依赖:./PublishTypes |
| `admin/src/views/seo-matrix/PublishDraftModal.vue` | 41 | 组件:PublishDraftModal · 根:a-modal · props · emits · 定义:props,emit,openModel · 依赖:./PublishTypes |
| `admin/src/views/seo-matrix/PublishHistoryPanel.vue` | 96 | 组件:PublishHistoryPanel · 根:div · props · emits · 定义:emit · 依赖:./PublishTypes |
| `admin/src/views/seo-matrix/PublishPlatformGroup.vue` | 131 | 组件:PublishPlatformGroup · 根:div · props · emits · 定义:emit · 依赖:./PublishTypes,@/components/youding |
| `admin/src/views/seo-matrix/PublishPlatformSelector.vue` | 218 | 组件:PublishPlatformSelector · 根:div · props · emits · 定义:props,emit,customPlatformNameModel,customPlatformRegionModel · 依赖:./PublishPlatformGroup.vue,./PublishTypes,@/components/common/SkeletonCard.vue · ⚑MOCK |
| `admin/src/views/seo-matrix/PublishTokenQuotaBar.vue` | 27 | 组件:PublishTokenQuotaBar · 根:a-alert · props · emits · 定义:emit |
| `admin/src/views/seo-matrix/PublishTypes.ts` | 97 | 定义:PlatformDef,NurtureCfg,ConnectFormState,EgressEndpoint,BrowserProfile,Draft,PubDetail,PubResult |
| `admin/src/views/seo-matrix/content.vue` | 670 | 组件:content · 根:YdPage · 定义:templates,contents,selectedTemplate,statusFilter,loading,showGenerateModal,showPreviewModal,showTemplateModal · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/composables/useSanitize · ⚑MOCK/STUB |
| `admin/src/views/seo-matrix/dashboard.vue` | 439 | 组件:dashboard · 根:YdPage · 定义:stats,hotKeywords,recentTasks,initialLoading,platformStats,keywordColumns,taskColumns,publishTrendChart · 依赖:@/api,@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/exportCsv |
| `admin/src/views/seo-matrix/growth-tools.vue` | 893 | 组件:growth-tools · 根:YdPage · 定义:activeTool,autopilotRef,dashboard,trafficFilter,wordClasses,classLabels,hotBuckets,hotTotals · 依赖:@/api,@/components/growth/GrowthAutopilotPanel.vue,@/components/youding,@/composables/useBoardDetailDrawer · ⚑MOCK |
| `admin/src/views/seo-matrix/inclusion.vue` | 580 | 组件:inclusion · 根:YdPage · 定义:inclusionList,statusFilter,keywordFilter,loading,showDetailModal,detailData,autoCheckEnabled,alertEnabled · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/seo-matrix/index.vue` | 45 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/seo-matrix/keywords.vue` | 624 | 组件:keywords · 根:YdPage · 定义:rules,generatedKeywords,selectedRule,selectedKeys,seedingBelt,loading,showGenerateModal,showRuleModal · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer · ⚑MOCK |
| `admin/src/views/seo-matrix/publish.vue` | 972 | 组件:publish · 根:YdPage · 定义:router,route,videoBindHubRef,tokenQuota,lastTokenUsage,loadTokenQuota,res,body · 依赖:./PublishAiGeneratorPanel.vue,./PublishConnectModal.vue,./PublishDetailModal.vue,./PublishDraftModal.vue,./PublishHistoryPanel.vue · ⚑DEGRADED |
| `admin/src/views/seo-matrix/regions.vue` | 524 | 组件:regions · 根:YdPage · 定义:listPayload,pagePayload,o,provinces,cities,districts,keywordGroups,keywords · 依赖:@/api,@/components/youding · ⚑MOCK |
| `admin/src/views/seo-matrix/settings.vue` | 403 | 组件:settings · 根:YdPage · 定义:toDayjsTime,settings,loading,saveSettings,payload,resetSettings,exportSettings,dataStr · 依赖:@/api,@/components/youding · ⚑MOCK |
| `admin/src/views/seo/ai-content.vue` | 36 | 组件:ai-content · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/seo/baidu-tools.vue` | 389 | 组件:baidu-tools · 根:YdPage · 定义:ui,siteToken,siteUrl,dataLevel,hasRealIndex,hasRealSearch,indexData,searchData · 依赖:@/api,@/components/youding,@/components/youding/YdHonestDataBanner.vue,@/composables/useBoardDetailDrawer,@/stores/uiPreferences · ⚑MOCK |
| `admin/src/views/seo/batch-seo.vue` | 396 | 组件:batch-seo · 根:YdPage · 定义:tablePanelRef,ui,pages,loading,search,filterStatus,selectedRows,showEditModal · 依赖:@/api,@/components/youding,@/stores/uiPreferences,@/utils/api,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/seo/building-wiki.vue` | 426 | 组件:building-wiki · 根:YdPage · 定义:basePath,tablePanelRef,ui,builtinKeywords,keyword,style,generating,previewArticle · 依赖:@/api,@/components/youding,@/stores/uiPreferences,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/seo/compliance.vue` | 447 | 组件:compliance · 根:YdPage · 定义:historyTablePanelRef,ui,scanType,scanUrl,scanContent,scanning,scanResult,activeTab · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences · ⚑MOCK |
| `admin/src/views/seo/content-optimizer.vue` | 311 | 组件:content-optimizer · 根:YdPage · 定义:form,articleModel,keywordsInput,optimizedContent,changes,tokenUsage,cost,technicalPreserved · 依赖:@/api,@/components/common/AiSkeleton.vue,@/components/common/TypewriterText.vue,@/components/youding,@/composables/useAiRequest · ⚑MOCK |
| `admin/src/views/seo/diagnostics.vue` | 51 | 组件:diagnostics · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/seo/eeat.vue` | 955 | 组件:eeat · 根:YdPage · 定义:activeTab,searchQuery,authors,showAddAuthorModal,isEditing,authorForm,scoreForm,isCalculating · 依赖:@/api,@/components/youding,@/utils/api · ⚑MOCK/DEPRECATED |
| `admin/src/views/seo/index.vue` | 661 | 组件:index · 根:main · 定义:router,route,modules,goModule,target,stats,rankedPct,t · 依赖:@/api,@/utils/api |
| `admin/src/views/seo/keyword-ranking.vue` | 840 | 组件:keyword-ranking · 根:YdPage · 定义:tablePanelRef,ui,apiBase,authHeaders,tk,formatDateTime,d,pad · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api · ⚑MOCK/DEGRADED |
| `admin/src/views/seo/llms-txt.vue` | 363 | 组件:llms-txt · 根:YdPage · 定义:form,keywordsText,generatedContent,tokenUsage,cost,version,editable,loading · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api · ⚑MOCK |
| `admin/src/views/seo/performance.vue` | 244 | 组件:performance · 根:YdPage · 定义:activeTab,dataTrust,loadError,pageSpeedScore,lcp,fid,cls,securityScore · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/seo/schema-markup.vue` | 909 | 组件:schema-markup · 根:YdPage · 定义:HonestSummary,schemaTypes,activeTab,searchQuery,isGenerating,copied,generatedSchema,honestSummary · 依赖:@/api,@/components/youding,@/components/youding/YdHonestDataBanner.vue · ⚑MOCK |
| `admin/src/views/seo/site-audit.vue` | 371 | 组件:site-audit · 根:YdPage · 定义:ui,form,auditId,auditStatus,auditResult,loading,progressPercent,progressText · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/system-health/backup.vue` | 137 | 组件:backup · 根:YdPage · 定义:loading,backupRunning,stats,columns,backups,restoreModal,refreshBackups,tk · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api |
| `admin/src/views/system-health/dashboard.vue` | 198 | 组件:dashboard · 根:YdPage · 定义:refreshing,overviewError,overviewLoaded,cpuPercent,memPercent,diskPercent,cpu,memory · 依赖:@/components/youding,@/utils/api · ⚑DEGRADED |
| `admin/src/views/system-health/index.vue` | 80 | 组件:index · 根:div · 定义:router,route,activeTab,name,tabRouteMap,handleTabChange,tk · 依赖:@/utils/api |
| `admin/src/views/system-health/resource-monitor.vue` | 137 | 组件:resource-monitor · 根:YdPage · 定义:loading,metrics,net,processColumns,processes,loadResourceMonitor,tk,r · 依赖:@/components/youding,@/composables/useBoardDetailDrawer,@/utils/api |
| `admin/src/views/system-health/stress-test.vue` | 145 | 组件:stress-test · 根:YdPage · 定义:showCreateModal,showDetailModal,detailRecord,form,runningTests,history,histColumns,loadHistory · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/system/AdvancedPanel.vue` | 117 | 组件:AdvancedPanel · 根:div · props · emits · 定义:emit |
| `admin/src/views/system/ApiKeysPanel.vue` | 86 | 组件:ApiKeysPanel · 根:div · props · emits · 定义:emit |
| `admin/src/views/system/NotificationsPanel.vue` | 101 | 组件:NotificationsPanel · 根:div · props · emits · 定义:emit |
| `admin/src/views/system/ProfilePanel.vue` | 94 | 组件:ProfilePanel · 根:div · props · emits · 定义:emit,avatarInput,triggerAvatarInput · ⚑MOCK |
| `admin/src/views/system/SecurityPanel.vue` | 182 | 组件:SecurityPanel · 根:div · props · emits · 定义:emit · ⚑MOCK/STUB |
| `admin/src/views/system/SettingsDeleteConfirmModal.vue` | 60 | 组件:SettingsDeleteConfirmModal · 根:div · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/system/SettingsNewKeyModal.vue` | 61 | 组件:SettingsNewKeyModal · 根:div · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/system/SettingsSidebar.vue` | 36 | 组件:SettingsSidebar · 根:div · props · emits · 定义:emit |
| `admin/src/views/system/analytics.vue` | 445 | 组件:analytics · 根:YdPage · 定义:logs,loading,logTablePanelRef,ui,summaryLoading,summaryError,overview,analyticsSummary · 依赖:@/api,@/components/youding,@/composables/useBoardDetailDrawer,@/stores/uiPreferences |
| `admin/src/views/system/drag-module.vue` | 375 | 组件:drag-module · 根:YdPage · 定义:Module,modules,showAddModal,editingModule,moduleForm,dragSettings,availableIcons,iconMap · 依赖:@/components/youding,@/utils/api,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/system/effects.vue` | 458 | 组件:effects · 根:YdPage · 定义:Effect,showPreview,currentEffect,showTip,tipText,transitionEffects,currentEffectName,currentEffectDesc · 依赖:@/components/youding,@/utils/api |
| `admin/src/views/system/performance.vue` | 403 | 组件:performance · 根:YdPage · 定义:activeTab,healthStatus,metrics,securityReport,securityIssues,auditing,API_BASE,loadMetrics · 依赖:@/components/youding |
| `admin/src/views/system/seoStandalone.vue` | 197 | 组件:seoStandalone · 根:div · 定义:baseUrl,readAdminToken,KEY,ss,ls,reloadKey,loading,errored |
| `admin/src/views/system/settings-main.vue` | 331 | 组件:settings-main · 根:YdPage · 定义:router,loading,loadError,savingSite,savingSeo,savingSystem,site,seo · 依赖:@/api,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/system/settings.vue` | 229 | 组件:settings · 根:div · 定义:router,route,currentSubMenu,settingsSubKey,p,rest,navigateTo,activeTab · 依赖:./AdvancedPanel.vue,./ApiKeysPanel.vue,./NotificationsPanel.vue,./ProfilePanel.vue,./SecurityPanel.vue |
| `admin/src/views/system/users.vue` | 327 | 组件:users · 根:YdPage · 定义:users,loading,tablePanelRef,ui,showAddModal,form,isEdit,pagination · 依赖:@/api,@/components/youding,@/stores/uiPreferences,@/utils/api,@/utils/ydModal · ⚑MOCK |
| `admin/src/views/team/index.vue` | 150 | 组件:index · 根:YdPage · 定义:MemberRow,loading,members,keyword,columns,roleColor,map,roleLabel · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/templates/CockpitCharts.vue` | 126 | 组件:CockpitCharts · 根:div · props · emits |
| `admin/src/views/templates/CockpitKpiCards.vue` | 35 | 组件:CockpitKpiCards · 根:div · props |
| `admin/src/views/templates/CockpitOrders.vue` | 53 | 组件:CockpitOrders · 根:div · props · emits · ⚑MOCK |
| `admin/src/views/templates/CockpitSidebar.vue` | 88 | 组件:CockpitSidebar · 根:div · props · emits |
| `admin/src/views/templates/dashboard-data-cockpit.vue` | 320 | 组件:dashboard-data-cockpit · 根:div · 定义:searchKeyword,notificationCount,dateRange,timeGranularity,activeRevenueTab,orderSearch,kpiCards,totalRevenue · 依赖:./CockpitCharts.vue,./CockpitKpiCards.vue,./CockpitOrders.vue,./CockpitSidebar.vue,@/components/youding · ⚑MOCK |
| `admin/src/views/templates/dashboard-data-screen.vue` | 829 | 组件:dashboard-data-screen · 根:div · 定义:currentTime,currentDate,updateClock,now,glowKpis,salesRank,productionLines,chartDays · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/templates/dashboard-enterprise.vue` | 725 | 组件:dashboard-enterprise · 根:div · 定义:unreadNotices,updateTime,dateRange,tableSearch,categoryFilter,statusFilter,selectedRowKeys,statsData · 依赖:@/components/youding,@/utils/uiDisplayLabels · ⚑MOCK |
| `admin/src/views/templates/dashboard-saas.vue` | 823 | 组件:dashboard-saas · 根:div · 定义:currentTenant,daysUntilExpire,showBanner,tenantList,switchTenant,quickEntries,handleQuickEntry,activityLogs · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/templates/dashboard-tencent.vue` | 668 | 组件:dashboard-tencent · 根:div · 定义:metricsData,sparklineChannels,hotKeywords,pageBars,timelineItems,aiSummary · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/templates/index.vue` | 362 | 组件:index · 根:div · 定义:router,templates,goToTemplate · 依赖:@/components/youding · ⚑MOCK |
| `admin/src/views/tenants/BillingPayModal.vue` | 249 | 组件:BillingPayModal · props · emits · ⚑MOCK |
| `admin/src/views/tenants/BillingPaymentHistory.vue` | 199 | 组件:BillingPaymentHistory · 根:section · props · emits · 定义:Bill |
| `admin/src/views/tenants/BillingPricingPlans.vue` | 346 | 组件:BillingPricingPlans · props · emits |
| `admin/src/views/tenants/SiteEditorFormPanel.vue` | 194 | 组件:SiteEditorFormPanel · 根:div · props · emits · 定义:emit,fileInput · ⚑MOCK |
| `admin/src/views/tenants/SiteEditorHeader.vue` | 105 | 组件:SiteEditorHeader · 根:div · props · emits · 定义:emit,productImagesInput · ⚑MOCK |
| `admin/src/views/tenants/SiteEditorPageTabs.vue` | 28 | 组件:SiteEditorPageTabs · 根:a-card · props · emits · 定义:emit |
| `admin/src/views/tenants/SiteEditorPreviewPanel.vue` | 162 | 组件:SiteEditorPreviewPanel · 根:div · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/tenants/billing.vue` | 719 | 组件:billing · 根:div · 定义:statusFilter,loading,plans,plansLoading,plansLoadError,selectedPlanId,billingCycle,qrVisible · 依赖:./BillingPayModal.vue,./BillingPaymentHistory.vue,./BillingPricingPlans.vue,@/components/tenants/TenantCommerceTabs.vue,@/composables/useBoardDetailDrawer · ⚑MOCK |
| `admin/src/views/tenants/dashboard.vue` | 882 | 组件:dashboard · 根:YdPage · 定义:TenantPlan,TenantStats,TenantRecord,planOptions,loadPlanOptions,data,stats,formatMonthlyRevenue · 依赖:@/components/common/SkeletonCard.vue,@/components/youding,@/composables/useYoudingTableBridge,@/stores/uiPreferences,@/utils/api · ⚑MOCK |
| `admin/src/views/tenants/domain.vue` | 312 | 组件:domain · 根:YdPage · 定义:headers,primaryDomain,newDomain,addingDomain,verifyingDns,dnsConfig,loading,domainList · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/tenants/index.vue` | 28 | 组件:index · 根:div · 依赖:@/composables/useModuleTabSync |
| `admin/src/views/tenants/plans.vue` | 503 | 组件:plans · 根:YdPage · 定义:PlanRecord,TenantRecord,cols,tenantCols,loading,planList,tablePanelRef,parseFeatures · 依赖:@/components/tenants/TenantCommerceTabs.vue,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/tenants/pricing.vue` | 607 | 组件:pricing · 根:YdPage · 定义:ApiTenantPlan,DisplayPlan,annual,openFaq,plans,compareData,apiPlans,loadError · 依赖:@/components/tenants/TenantCommerceTabs.vue,@/components/youding,@/utils/api,@/utils/tenantPlanDisplay · ⚑DEGRADED |
| `admin/src/views/tenants/product-showcase.vue` | 934 | 组件:product-showcase · 根:YdPage · 定义:hoveredFeat,openFaq,scrollToSection,el,bookDemo,features,pricingPlans,cases · 依赖:@/components/youding,@/utils/api · ⚑DEGRADED |
| `admin/src/views/tenants/register.vue` | 747 | 组件:register · 根:TenantOnboardTabs · 定义:PlanOption,plans,cat,router,route,loading,errorMsg,sendingCode · 依赖:@/api,@/components/tenants/TenantOnboardTabs.vue · ⚑MOCK |
| `admin/src/views/tenants/site-editor.vue` | 782 | 组件:site-editor · 根:YdPage · 定义:SiteBuilderTemplateId,SiteSeoFields,VisualEditorPayload,VisualStudioStatus,UploadedProductImage,route,router,rightPanelTab · 依赖:../../../../utils/tenant-preview-domain,./SiteEditorFormPanel.vue,./SiteEditorHeader.vue,./SiteEditorPageTabs.vue,./SiteEditorPreviewPanel.vue · ⚑MOCK/DEGRADED |
| `admin/src/views/tenants/white-label.vue` | 206 | 组件:white-label · 根:YdPage · 定义:TenantOption,selectForm,tenantOptions,selectedTenantId,selectedTenantName,loadingConfig,searchTenants,data · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/workspace/EmotionCrmAnalyzeModal.vue` | 107 | 组件:EmotionCrmAnalyzeModal · props · emits · 定义:emit · ⚑MOCK |
| `admin/src/views/workspace/EmotionCrmCustomerDrawer.vue` | 203 | 组件:EmotionCrmCustomerDrawer · props · emits · 定义:emit · 依赖:./emotionCrmTypes · ⚑MOCK |
| `admin/src/views/workspace/EmotionCrmDashboardTab.vue` | 81 | 组件:EmotionCrmDashboardTab · 根:div · props · emits · 定义:emit · 依赖:./emotionCrmTypes |
| `admin/src/views/workspace/EmotionCrmFollowupTab.vue` | 91 | 组件:EmotionCrmFollowupTab · 根:div · props · emits · 定义:emit · 依赖:./emotionCrmTypes |
| `admin/src/views/workspace/EmotionCrmHistoryTab.vue` | 70 | 组件:EmotionCrmHistoryTab · 根:div · props · 依赖:./emotionCrmTypes |
| `admin/src/views/workspace/EmotionCrmKpiStrip.vue` | 61 | 组件:EmotionCrmKpiStrip · props · emits · 定义:emit · 依赖:./emotionCrmTypes |
| `admin/src/views/workspace/EmotionCrmObjectionDrawer.vue` | 50 | 组件:EmotionCrmObjectionDrawer · props · emits · 定义:emit |
| `admin/src/views/workspace/EmotionCrmStrategyTab.vue` | 114 | 组件:EmotionCrmStrategyTab · 根:div · props · 依赖:./emotionCrmTypes · ⚑DEGRADED |
| `admin/src/views/workspace/EmotionCrmTierBoard.vue` | 212 | 组件:EmotionCrmTierBoard · props · emits · 定义:emit · 依赖:./emotionCrmTypes · ⚑MOCK |
| `admin/src/views/workspace/EmotionCrmTrajectoryTab.vue` | 112 | 组件:EmotionCrmTrajectoryTab · 根:div · props · emits · 定义:emit · 依赖:./emotionCrmTypes |
| `admin/src/views/workspace/EmotionCrmWorkspace.vue` | 769 | 组件:EmotionCrmWorkspace · 根:YdPage · 定义:tierOptions,activeTab,selectedTier,selectedCustomer,lifecycleItems,loading,evaluating,showAnalyzeModal · 依赖:./EmotionCrmAnalyzeModal.vue,./EmotionCrmCustomerDrawer.vue,./EmotionCrmDashboardTab.vue,./EmotionCrmFollowupTab.vue,./EmotionCrmHistoryTab.vue · ⚑DEGRADED |
| `admin/src/views/workspace/OutreachEditor.vue` | 457 | 组件:OutreachEditor · 根:YdPage · 定义:route,router,saving,sending,generating,showVariablePicker,currentVersion,previewMode · 依赖:@/components/whatsfinds/EvidenceChain.vue,@/components/whatsfinds/ScoreRadar.vue,@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/workspace/ProspectingWorkspace.vue` | 588 | 组件:ProspectingWorkspace · 根:YdPage · 定义:router,currentStep,searchForm,searching,generatedSyntax,loadingResults,leads,selectedLeads · 依赖:@/components/whatsfinds/EvidenceChain.vue,@/components/whatsfinds/ScoreRadar.vue,@/components/whatsfinds/SearchSyntaxPreview.vue,@/components/youding,@/utils/api · ⚑MOCK/STUB |
| `admin/src/views/workspace/SkillConsole.vue` | 342 | 组件:SkillConsole · 根:YdPage · 定义:Skill,skills,selectedSkill,form,executing,result,res,selectSkill · 依赖:@/components/youding,@/utils/api · ⚑MOCK |
| `admin/src/views/workspace/emotionCrmTypes.ts` | 62 | 定义:LifecycleItem,TrajectoryPoint,TrajectoryData,TierOption,KpiCard |
| `admin/src/vite-env.d.ts` | 56 | 定义:RouteMeta,AxiosRequestConfig,io,Socket,ImportMeta,SpeechRecognition,SpeechRecognitionEvent · ⚑DEGRADED |
| `admin/tailwind.config.js` | 169 |  |
| `admin/tests/unit/shellNavKernel.test.ts` | 97 | 定义:SAMPLE,active,leaves,actives,nested,active,parent,paths · 依赖:@/types/shellNav,@/utils/shellNavKernel · ⚑DEGRADED |
| `admin/vite-plugins/designPreviewStatic.ts` | 111 | 定义:injectDesignPreviewBridge,realPath,bridge,MIME,designRootFromAdmin,youdingDesignPreviewStatic,designRoot,mount · 依赖:../src/constants/designPageRouteRegistry |
| `admin/vite.config.ts` | 206 | 定义:lanHost,adminDir,backendProxyPort,rawSetCookies,otherHeaders,name,value,rewritten · 依赖:./vite-plugins/designPreviewStatic · ⚑DEPRECATED |
| `admin/vitest.config.ts` | 34 |  |