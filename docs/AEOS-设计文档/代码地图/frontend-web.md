# 官网/租户站 frontend（Nuxt3 开发版）

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\frontend` · **254 个文件** · 官网/租户站（Nuxt3 开发版）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `frontend/app.config.ts` | 8 |  |
| `frontend/app.vue` | 10 | 组件:app · 根:NuxtLayout |
| `frontend/components/FloatingContact.vue` | 239 | 组件:FloatingContact · 根:div · 定义:showWechat,copied,openInquiry,openWechat,weixinUrl,textArea,callPhone · ⚑MOCK |
| `frontend/components/LanguageSwitcher.vue` | 137 | 组件:LanguageSwitcher · 根:div · 定义:switchLocalePath,isOpen,dropdownRef,currentLocale,currentLocaleName,found,currentLocaleFlag,localeFlag |
| `frontend/components/MobileExpandable.vue` | 48 | 组件:MobileExpandable · 根:div · props · 定义:Props,props,isExpanded,toggle |
| `frontend/components/MobileNavbar.vue` | 53 | 组件:MobileNavbar · 根:header · props · 定义:Props,props,scrollY,isVisible,lastScrollY,handleScroll,currentScrollY |
| `frontend/components/MobilePerformanceLayer.vue` | 112 | 组件:MobilePerformanceLayer · 根:div · props · emits · 定义:Props,props,emit,containerRef,isRefreshing,startY,handleTouchStart,handleTouchEnd |
| `frontend/components/MobileScrollReveal.vue` | 55 | 组件:MobileScrollReveal · 根:div · props · 定义:Props,props,containerRef,isInView,observer,animationClass |
| `frontend/components/MobileSwipeGesture.vue` | 83 | 组件:MobileSwipeGesture · 根:div · props · 定义:SwipeResult,Props,props,startX,startY,isSwiping,handleTouchStart,touch |
| `frontend/components/MobileTabBar.vue` | 118 | 组件:MobileTabBar · 根:nav · props · 定义:Props,route,HomeIcon,ProductIcon,CaseIcon,NewsIcon,navItems,isActive |
| `frontend/components/OptimizedImage.vue` | 167 | 组件:OptimizedImage · 根:div · props · 定义:LazyImageProps,props,containerRef,imageRef,isLoaded,hasError,isVisible,loadingStrategy · ⚑MOCK/DEGRADED |
| `frontend/components/PerformanceMonitor.vue` | 126 | 组件:PerformanceMonitor · 根:div · props · 定义:props,isDev,fps,memoryUsage,loadTime,calculateFPS,now,delta |
| `frontend/components/PerformanceOptimizer.vue` | 5 | 组件:PerformanceOptimizer · 根:div |
| `frontend/components/ProductSpecAccordion.vue` | 94 | 组件:ProductSpecAccordion · 根:div · props · 定义:props,isOpen,currentUnit,toggleUnit |
| `frontend/components/ResponsiveCard.vue` | 229 | 组件:ResponsiveCard · 根:div · props · emits · 定义:MetaItem |
| `frontend/components/ResponsiveGrid.vue` | 73 | 组件:ResponsiveGrid · 根:div · props · 定义:Columns,GridProps,props,gridClass,gapClasses,defaultCols |
| `frontend/components/ResponsiveNavbar.vue` | 201 | 组件:ResponsiveNavbar · 根:nav · emits · 定义:navItems,route,isMobileMenuOpen,isActive,toggleMobileMenu,closeMobileMenu,emit,toggleSearch |
| `frontend/components/SEOHead.vue` | 242 | 组件:SEOHead · 根:div · props · 定义:SEOProps,props,config,route,baseUrl,fullUrl,defaultOgImage,defaultTwitterImage |
| `frontend/components/ShippingTimeline.vue` | 110 | 组件:ShippingTimeline · 根:div · props · 定义:route,props,timeline,fetchTimeline,res |
| `frontend/components/StickyImBar.vue` | 269 | 组件:StickyImBar · 根:div · 定义:route,showBar,showForm,imChannels,channelIndex,form,formError,CN_PHONE · ⚑MOCK |
| `frontend/components/ai/AiProviderGuide.vue` | 280 | 组件:AiProviderGuide · 根:teleport · props · emits · 定义:props,emit,router,recommendPlatforms,handleSetup,handleLater |
| `frontend/components/business/FreightCalculator.vue` | 111 | 组件:FreightCalculator · 根:Card · props · emits · 定义:props,emit,localDistance,localQuantity,estimatedPrice,hasDiscount,distanceHint,freight · ⚑MOCK |
| `frontend/components/business/LeadItem.vue` | 99 | 组件:LeadItem · 根:article · props · 定义:Lead,props,displayTime,statusLabel,badgeClass,calculateTimeAgo,now,created |
| `frontend/components/business/RegionHeatmap.vue` | 46 | 组件:RegionHeatmap · 根:Card · props · 定义:RegionItem,props,maxCount,barWidth |
| `frontend/components/business/RegionSelector.vue` | 88 | 组件:RegionSelector · 根:div · props · emits · 定义:props,emit,showPicker,selectedProvince,selectedLabel,provinces,selectProvince,selectCity · ⚑MOCK |
| `frontend/components/business/SchemaMarkup.vue` | 28 | 组件:SchemaMarkup · 根:Head · props · 定义:props,schemaData,schemaString |
| `frontend/components/business/StatCard.vue` | 25 | 组件:StatCard · 根:Card · props |
| `frontend/components/common/AnimatedSection.vue` | 123 | 组件:AnimatedSection · 根:div · props · 定义:props,target,isVisible,animationStyle |
| `frontend/components/common/Footer.vue` | 296 | 组件:Footer · 根:footer · 定义:hideHubBacklink,phone,email,address,currentYear,productLinks,quickLinks |
| `frontend/components/common/Header.vue` | 381 | 组件:Header · 根:header · 定义:route,phone,isScrolled,isHidden,isMobileMenuOpen,lastScrollTop,scrollThreshold,mobileOpenGroup |
| `frontend/components/common/ParallaxContainer.vue` | 70 | 组件:ParallaxContainer · 根:div · props · 定义:props,container,scrollY,containerStyle,offset,transforms,handleScroll |
| `frontend/components/common/ParticleBackground.vue` | 125 | 组件:ParticleBackground · 根:canvas · props · 定义:props,canvas,resizeCanvas,initParticles,drawParticles,dx,dy,distance |
| `frontend/components/common/ScrollProgress.vue` | 52 | 组件:ScrollProgress · 根:div · 定义:container,progress,handleScroll,scrollTop,docHeight |
| `frontend/components/icons/AwardIcon.vue` | 17 | 组件:AwardIcon · 根:svg |
| `frontend/components/icons/BrickIcon.vue` | 17 | 组件:BrickIcon · 根:svg |
| `frontend/components/icons/DropletsIcon.vue` | 17 | 组件:DropletsIcon · 根:svg |
| `frontend/components/icons/FactoryIcon.vue` | 17 | 组件:FactoryIcon · 根:svg |
| `frontend/components/icons/ShieldIcon.vue` | 17 | 组件:ShieldIcon · 根:svg |
| `frontend/components/icons/ThermometerIcon.vue` | 17 | 组件:ThermometerIcon · 根:svg |
| `frontend/components/onboarding/OnboardingGuide.vue` | 151 | 组件:OnboardingGuide · 根:Teleport · props · emits · 定义:Props,props,emit,steps,currentStep,totalSteps,next,prev · ⚑MOCK |
| `frontend/components/seo/ContentOptimizer.vue` | 278 | 组件:ContentOptimizer · 根:div · 定义:seo,optType,keywordsRaw,content,model,optimizing,error,result · ⚑MOCK |
| `frontend/components/seo/LLMSTxtGenerator.vue` | 206 | 组件:LLMSTxtGenerator · 根:div · 定义:seo,SectionTemplate,sectionLabels,availableSections,selectedSectionTypes,includeAiInstructions,generating,error |
| `frontend/components/seo/SchemaMarkupGenerator.vue` | 445 | 组件:SchemaMarkupGenerator · 根:div · 定义:schemaTypes,isGenerating,copied,generatedSchema,validationResult,form,templateFields,fields · ⚑MOCK |
| `frontend/components/seo/SiteAudit.vue` | 294 | 组件:SiteAudit · 根:div · 定义:seo,auditType,targetUrl,auditing,error,AuditIssue,AuditRecommendation,AuditResult · ⚑MOCK |
| `frontend/components/tenant/TenantInquiryForm.vue` | 202 | 组件:TenantInquiryForm · 根:form · props · 定义:props,form,submitting,errorText,successText,phoneLabel,onSubmit,attr · 依赖:../../utils/submitPublicInquiry · ⚑MOCK |
| `frontend/components/tenant/TenantSite.vue` | 1984 | 组件:TenantSite · 根:div · props · 定义:BrandColors,SiteCategory,SiteApplication,SiteAdvantage,SiteStat,SiteMilestone,SiteSolution,ProductItem · 依赖:../../composables/useTenantMediaUrl,../../composables/useTenantVisitorContacts,../../composables/useVisitorLocale,../../composables/useVisualSiteInquiryBinder,../../composables/useVisualSiteNavBinder · ⚑MOCK/DEGRADED |
| `frontend/components/tenant/TenantSiteCompanion.vue` | 1034 | 组件:TenantSiteCompanion · 根:div · props · 定义:props,accentColor,accentDeep,accentMid,accentLight,isRtl,FALLBACK_UI,ui · 依赖:../../composables/useTenantVisitorContacts · ⚑MOCK/DEGRADED |
| `frontend/components/tenant/TenantSiteGateway.vue` | 44 | 组件:TenantSiteGateway · 根:TenantSite · props · 定义:props,legacyPage,lProComponent · 依赖:../../composables/useTenantSiteBootstrap,./premium/TenantLProAbout.vue,./premium/TenantLProContact.vue,./premium/TenantLProDownloads.vue,./premium/TenantLProHome.vue |
| `frontend/components/tenant/premium/LProLanguagePicker.vue` | 272 | 组件:LProLanguagePicker · 根:div · props · 定义:CheckIcon,props,open,rootRef,tier1Languages,fromApi,tier2Languages,currentLanguageName · 依赖:../../../composables/useTenantLanguagePicker |
| `frontend/components/tenant/premium/PremiumB2bShell.vue` | 392 | 组件:PremiumB2bShell · 根:div · props · 定义:props,menuOpen,bootstrap,overlay,companyName,brandTagline,themePrimary,establishedYear · 依赖:../../../composables/useTenantGeoJsonLd,../../../composables/useTenantLProNav,../../../composables/useTenantLProSeoHead,../../../composables/useTenantLanguagePicker,../../../composables/useTenantSiteBootstrap |
| `frontend/components/tenant/premium/TenantLProAbout.vue` | 85 | 组件:TenantLProAbout · 根:PremiumB2bShell · 定义:overlay,companyName,aboutText,mission,vision,capacitySummary,milestones,raw · 依赖:../../../composables/useTenantSiteBootstrap,../../../utils/tenant-site-i18n,./PremiumB2bShell.vue |
| `frontend/components/tenant/premium/TenantLProContact.vue` | 102 | 组件:TenantLProContact · 根:PremiumB2bShell · 定义:contactPhone,contactEmail,contactWhatsapp,contactWechat,contactQq,factoryAddress,ctaPrimary,inquiryAttribution · 依赖:../../../composables/useTenantSiteBootstrap,../../../composables/useTenantVisitorContacts,../TenantInquiryForm.vue,./PremiumB2bShell.vue |
| `frontend/components/tenant/premium/TenantLProDownloads.vue` | 53 | 组件:TenantLProDownloads · 根:PremiumB2bShell · 定义:items,raw,o,title,url · 依赖:../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,./PremiumB2bShell.vue |
| `frontend/components/tenant/premium/TenantLProHome.vue` | 654 | 组件:TenantLProHome · 根:PremiumB2bShell · 定义:overlay,establishedYear,primaryPromise,heroTitle,heroDescription,ctaPrimary,inquiryHook,productsTitle · 依赖:../../../composables/useTenantLProNav,../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,../../../utils/tenant-product-slug,../../../utils/tenant-site-i18n |
| `frontend/components/tenant/premium/TenantLProProductDetail.vue` | 166 | 组件:TenantLProProductDetail · 根:PremiumB2bShell · 定义:route,slug,product,documentTitle,documentDescription,siteOrigin,productJsonLd,p · 依赖:../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,../../../utils/tenant-product-slug,../TenantInquiryForm.vue,./PremiumB2bShell.vue · ⚑MOCK |
| `frontend/components/tenant/premium/TenantLProProducts.vue` | 149 | 组件:TenantLProProducts · 根:PremiumB2bShell · 定义:route,overlay,productsTitle,productsDescription,activeCategory,q · 依赖:../../../composables/useTenantLProNav,../../../composables/useTenantMediaUrl,../../../composables/useTenantProductFilter,../../../composables/useTenantSiteBootstrap,../../../utils/tenant-product-slug · ⚑MOCK |
| `frontend/components/tenant/premium/TenantLProSolutions.vue` | 38 | 组件:TenantLProSolutions · 根:PremiumB2bShell · 定义:overlay,solutions,raw · 依赖:../../../composables/useTenantSiteBootstrap,./PremiumB2bShell.vue |
| `frontend/components/ui/Badge.vue` | 26 | 组件:Badge · 根:span · props · 定义:Props,variantClasses |
| `frontend/components/ui/Button.vue` | 41 | 组件:Button · 根:button · props · 定义:Props,props,variantClasses,sizeClasses |
| `frontend/components/ui/Card.vue` | 20 | 组件:Card · 根:div · props · 定义:Props |
| `frontend/components/ui/EmptyState.vue` | 20 | 组件:EmptyState · 根:div · props |
| `frontend/components/ui/ErrorBoundary.vue` | 78 | 组件:ErrorBoundary · 根:template · props · 定义:Props,props,error,errorInfo,resetError · ⚑DEGRADED |
| `frontend/components/ui/Input.vue` | 29 | 组件:Input · 根:input · props · emits · 定义:Props,emit,handleInput,target · ⚑MOCK |
| `frontend/components/ui/Label.vue` | 17 | 组件:Label · 根:label · props · 定义:Props |
| `frontend/components/ui/LazyImage.vue` | 115 | 组件:LazyImage · 根:div · props · 定义:Props,props,isLoaded,hasError,imgRef,observer,loadImage,img · ⚑MOCK |
| `frontend/components/ui/Modal.vue` | 71 | 组件:Modal · 根:Teleport · props · emits · 定义:props,emit,close,handleOverlayClick |
| `frontend/components/ui/PriceDisplay.vue` | 29 | 组件:PriceDisplay · 根:span · props · 定义:props,formattedAmount |
| `frontend/components/ui/Select.vue` | 27 | 组件:Select · 根:select · props · emits · 定义:Props,emit,handleChange,target |
| `frontend/components/ui/Skeleton.vue` | 61 | 组件:Skeleton · 根:div · props · 定义:Props,props,skeletonLines,lines |
| `frontend/components/ui/ToastRenderer.vue` | 60 | 组件:ToastRenderer · 根:ClientOnly · 定义:appStore,iconMap,typeClass,map · ⚑DEGRADED |
| `frontend/components/ui/VirtualList.vue` | 79 | 组件:VirtualList · 根:div · props · 定义:Props,props,containerRef,scrollTop,visibleStart,visibleCount,containerHeight,visibleEnd |
| `frontend/composables/useAdminAppUrl.ts` | 32 | 定义:useAdminAppUrl,config,base,loginUrl,login,root |
| `frontend/composables/useApi.ts` | 216 | 定义:ApiState,RequestOptions,getAuthToken,cookieToken,localStorageToken,setAuthToken,adminTokenCookie,stripApiPrefix |
| `frontend/composables/useApiBase.ts` | 24 | 定义:useApiRoot,config,apiHost,apiBase,root,apiUrl,p,base |
| `frontend/composables/useApiV1.ts` | 18 | 定义:useApiV1Base,config,apiHost,apiBase,useApiV1Url,base,p |
| `frontend/composables/useGEOContent.ts` | 220 | 定义:FAQ,geoFAQs,useGEOContent,featuredFAQs,faqsByCategory,grouped,getFAQById,searchFAQs |
| `frontend/composables/useGEOFAQsMultilingual.ts` | 211 | 定义:GeoFAQ,geoFAQsMultilingual,useGEOFAQsMultilingual,featuredFAQs,faqsByCategory,grouped,getFAQByLocale,faq |
| `frontend/composables/useGEOProducts.ts` | 374 | 定义:Product,ProductFeature,ProductSpecification,geoProducts,useGEOProducts,featuredProducts,productsByCategory,grouped · ⚑DEGRADED |
| `frontend/composables/useImRouting.ts` | 70 | 定义:ImChannel,useImRouting,config,route,merchantId,fromQuery,pub,countryCode · ⚑DEGRADED |
| `frontend/composables/useLazyLoad.ts` | 225 | 定义:createLazyComponent,lazyComponent,usePrefetch,prefetch,useLinkPrefetch,prefetchedUrls,prefetchLink,conn |
| `frontend/composables/useMarketingAnalytics.ts` | 90 | 定义:SESSION_KEY,LANDING_KEY,LAST_CLICK_KEY,AB_KEY,newSessionId,PlatformAbVariant,useMarketingAnalytics,route |
| `frontend/composables/useMobileInteractions.ts` | 429 | 定义:useMobileInteractions,touchStartX,touchStartY,touchStartTime,isSwiping,swipeDirection,swipeDistance,minSwipeDistance |
| `frontend/composables/useOfflineCache.ts` | 552 | 定义:OfflineQueueItem,CacheStatusEntry,SyncResult,FetchWithCacheOptions,FetchResult,SW_PATH,SW_SCOPE,useOfflineCache · ⚑DEGRADED |
| `frontend/composables/usePerformance.ts` | 183 | 定义:useLazyImage,imageRef,isLoaded,isInView,loadImage,img,observer,useDebounce |
| `frontend/composables/useResponsive.ts` | 225 | 定义:Breakpoint,BreakpointConfig,defaultBreakpoints,useResponsive,getWindowWidth,windowWidth,handleResize,isBreakpoint |
| `frontend/composables/useSEOHead.ts` | 241 | 定义:SEOMetadata,generateOrganizationSchema,generateProductSchema,generateArticleSchema,generateCaseSchema,generateBreadcrumbSchema,generateFAQSchema,generateLocalBusinessSchema |
| `frontend/composables/useSEOMeta.ts` | 109 | 定义:SEOMeta,useSEOMeta,config,route,defaultMeta,generateTitle,generateCanonicalUrl,baseUrl |
| `frontend/composables/useSanitize.ts` | 47 | 定义:PURIFY_CONFIG,useSanitize,sanitizeHtml · ⚑DEGRADED |
| `frontend/composables/useSeo.ts` | 180 | 定义:DashboardData,KeywordRanking,OptimizeRequest,OptimizeResponse,ValidateContentResponse,ExtractParamsResponse,LlmsGenerateRequest,LlmsGenerateResponse · 依赖:./useApi |
| `frontend/composables/useSiteAnalytics.ts` | 110 | 定义:SESSION_KEY,LANDING_KEY,LAST_CLICK_KEY,newSessionId,useSiteAnalytics,route,config,sessionId |
| `frontend/composables/useTenantGeoJsonLd.ts` | 263 | 定义:TenantGeoJsonLdInput,useTenantGeoJsonLd,jsonLdGraph,origin,graph,org,addr,items · 依赖:../utils/tenant-product-slug |
| `frontend/composables/useTenantLProNav.ts` | 51 | 定义:TenantLProNavKey,TENANT_L_PRO_PATHS,tenantProductDetailPath,tenantProductsCategoryQuery,TenantLProNavItem,buildTenantLProNavItems,items |
| `frontend/composables/useTenantLProSeoHead.ts` | 149 | 定义:TenantSeoPrimaryMarket,TenantLProSeoHeadInput,useTenantLProSeoHead,route,config,requestHeaders,primaryMarket,previewQuery · 依赖:../utils/tenant-seo-url,./useTenantLProNav |
| `frontend/composables/useTenantLanguagePicker.ts` | 65 | 定义:TenantLanguageOption,TIER1_LANGUAGES,TIER2_LANGUAGES,tenantLanguageStorageKey,readStoredTenantLanguage,writeStoredTenantLanguage,googleTranslatePageUrl,url |
| `frontend/composables/useTenantMediaUrl.ts` | 28 | 定义:useTenantMediaUrl,config,apiHost,resolveMediaUrl,path,host |
| `frontend/composables/useTenantProductFilter.ts` | 99 | 定义:TenantProductListItem,ProductSortKey,useTenantProductFilter,searchQuery,sortBy,specFilter,catalogWithSlugs,specFilterOptions · 依赖:../utils/tenant-product-slug |
| `frontend/composables/useTenantSiteBootstrap.ts` | 162 | 定义:TenantCatalogProduct,TenantSiteBrand,TenantSiteInfo,siteContentOf,sc,isLProSiteContent,visual,tid · 依赖:../utils/tenant-product-slug,./useApiBase,./useVisitorLocale |
| `frontend/composables/useTenantSiteContext.ts` | 65 | 定义:useTenantSiteContext,config,resolvedTenantId,resolvedMerchantId,loading,ensureTenantContext,envTid,apiBase |
| `frontend/composables/useTenantSitePolicy.ts` | 32 | 定义:useTenantSitePolicy,config,hideHubBacklink,load,mainHost,current,apiBase,res |
| `frontend/composables/useTenantVisitorContacts.ts` | 170 | 定义:CN_CHANNEL_TYPES,DEFAULT_ORDER,CN_ORDER,TOPBAR_TYPES,CHANNEL_LABELS,TenantMobileQuickAction,channelLabel,pack · 依赖:./useVisitorLocale · ⚑DEGRADED |
| `frontend/composables/useToast.ts` | 32 | 定义:useToast,appStore,show,success,error,warning,info |
| `frontend/composables/useVisitorLocale.ts` | 401 | 定义:VisitorContactChannel,VisitorContext,FALLBACK_SITE_UI,FALLBACK_WANGCAI_UI,applyContext,buildFallbackContext,resolveFetchLanguage,explicit · 依赖:../utils/tenant-preview-domain,../utils/visitorContextCache,../utils/visitorContextFetch,./useTenantLanguagePicker · ⚑MOCK/DEGRADED |
| `frontend/composables/useVisualSiteInquiryBinder.ts` | 133 | 定义:VisualInquiryBinderOptions,readForm,fd,showFormMessage,bindVisualSiteInquiryForms,handlers,form,fn · 依赖:../utils/submitPublicInquiry |
| `frontend/composables/useVisualSiteNavBinder.ts` | 25 | 定义:bindVisualSiteNavLinks,handlers,tenantParam,el,fn,url |
| `frontend/config/modules.ts` | 191 | 定义:ModuleConfig,ADMIN_MODULES,ROLE_LABELS,getUserModules,hasAccessToModule,module |
| `frontend/config/plan-catalog.ts` | 251 | 定义:PLAN_ORDER,PlanId,PLAN_REGISTER_CODE,REGISTER_CODE_TO_PLAN,PLAN_CATALOG,FEATURE_LABELS,MatrixCell,PricingMatrixRow |
| `frontend/config/platform-marketing-content.ts` | 189 | 定义:MatrixCell,PLATFORM_COPY,NAV_LINKS,TRUST_PROOF,INTEGRATIONS,PRICING_MATRIX,PLAN_FEATURE_BULLETS,LANDING_HERO_PREVIEW · 依赖:./plan-catalog |
| `frontend/config/public-sites.ts` | 66 | 定义:PublicSiteId,PublicSiteDefinition,PUBLIC_SITES,getPublicSite |
| `frontend/config/site-navigation.ts` | 45 | 定义:SiteNavLink,SiteNavItem,siteMainNavigation,navKey |
| `frontend/config/site.ts` | 25 | 定义:SITE_CONFIG,API_CONFIG,SEO_CONFIG |
| `frontend/config/tenant-site-defaults.ts` | 20 | 定义:TenantProofCase,DEFAULT_TENANT_PROOF_CASES,DEFAULT_EXPORT_BADGES |
| `frontend/env.d.ts` | 1 |  |
| `frontend/layouts/default.vue` | 53 | 组件:default · 根:div |
| `frontend/layouts/marketing.vue` | 14 | 组件:marketing · 根:div |
| `frontend/layouts/tenant-blank.vue` | 56 | 组件:tenant-blank · 根:div · 定义:booting |
| `frontend/middleware/auth.global.ts` | 66 | 定义:PUBLIC_EXACT,PUBLIC_PREFIXES,STATIC_PREFIXES,isPublicPath,token |
| `frontend/middleware/error-handler.global.ts` | 9 |  |
| `frontend/middleware/geo-routing.ts` | 22 | 定义:countryCode,langMap,htmlLang |
| `frontend/middleware/tenant.global.ts` | 91 | 定义:MAIN_SITE_PATTERNS,normalizeHost,isMainSiteHost,escaped,dynamic,resolveRequestHost,headers,raw · 依赖:../utils/tenant-preview-domain · ⚑STUB |
| `frontend/nuxt.config.ts` | 563 | 定义:gtag · ⚑DEGRADED |
| `frontend/pages/[lang]/index.vue` | 170 | 组件:index · 根:div · 定义:route,router,products,buyerCountry,showForm,form,imLink,fetchProducts · ⚑MOCK |
| `frontend/pages/[lang]/product/[id].vue` | 209 | 组件:[id] · 根:div · 定义:route,router,product,imChannels,sanitizedDescription,buyerCountry,showForm,form · ⚑MOCK |
| `frontend/pages/about.vue` | 299 | 组件:about · 根:div · 定义:stats,milestones,msg,certifications |
| `frontend/pages/alerts.vue` | 1153 | 组件:alerts · 根:div · 定义:store,toast,router,activeTab,showCreateAlert,showCreateRule,filters,newAlert · ⚑MOCK |
| `frontend/pages/alerts/[id].vue` | 786 | 组件:[id] · 根:div · 定义:router,route,store,toast,loading,alert,histories,showAcknowledgeModal · ⚑MOCK |
| `frontend/pages/calculators.vue` | 143 | 组件:calculators · 根:div · 定义:api,activeTab,loading,thermal,fire,quantity,thermalResult,fireResult |
| `frontend/pages/cases-example.vue` | 204 | 组件:cases-example · 根:div · 定义:caseStudy,pageTitle,pageDescription,pageKeywords,canonicalUrl,structuredData,formatNumber · ⚑MOCK |
| `frontend/pages/cases/[slug].vue` | 341 | 组件:[slug] · 根:div · 定义:route,caseStore,contactPhone,caseItem,loading,error,relatedCases · ⚑DEGRADED |
| `frontend/pages/cases/index.vue` | 402 | 组件:index · 根:div · 定义:caseStore,contactPhone,selectedFilter,searchQuery,currentPage,pageSize,loading,filters · ⚑MOCK |
| `frontend/pages/contact.vue` | 517 | 组件:contact · 根:div · 定义:contactInfo,form,formErrors,submitting,submitSuccess,submitError,validateForm,handleSubmit · ⚑MOCK/DEGRADED |
| `frontend/pages/error.vue` | 64 | 组件:error · 根:div · props · 定义:props,goHome,reloadPage |
| `frontend/pages/finder.vue` | 559 | 组件:finder · 根:div · 定义:MatchItem,RejectedItem,MatchResult,api,form,loading,apiError,result · ⚑MOCK |
| `frontend/pages/index.vue` | 256 | 组件:index · 根:div · 定义:trustBadges,stats,solutions,categories,hotProducts,advantages,applications · ⚑MOCK |
| `frontend/pages/industry/[tenantSlug]/[contentId].vue` | 140 | 组件:[contentId] · 根:div · 定义:HubPageData,HubApiResponse,route,config,tenantSlug,contentId,tenantLabel,hubUrl |
| `frontend/pages/industry/[tenantSlug]/index.vue` | 74 | 组件:index · 根:div · 定义:route,config,tenantSlug,tenantLabel,hasTenantUrl,tenantSiteUrl,fromQuery,hubIntro |
| `frontend/pages/inquiries/index.vue` | 230 | 组件:index · 根:div · 定义:route,router,product,submitting,form,fetchProduct,response,data · ⚑MOCK |
| `frontend/pages/leads.vue` | 174 | 组件:leads · 根:div · 定义:Lead,Summary,fallbackSummary,allLeads,limit,hasMore,loadingMore,refreshing · ⚑DEGRADED |
| `frontend/pages/logistics/index.vue` | 287 | 组件:index · 根:div · 定义:trackingNumber,carrier,trackingResult,trackingLoading,trackingError,trackLogistics,params,url · ⚑MOCK |
| `frontend/pages/mobile/about.vue` | 193 | 组件:about · 根:div · 定义:advantages,contactItems |
| `frontend/pages/mobile/alerts.vue` | 347 | 组件:alerts · 根:div · 定义:router,alerts,loading,error,stats,activeTab,showCreateAlert,creating · ⚑MOCK |
| `frontend/pages/mobile/alerts/[id].vue` | 447 | 组件:[id] · 根:div · 定义:route,router,alert,histories,loading,error,showAckModal,showResolveModal · ⚑MOCK |
| `frontend/pages/mobile/cases.vue` | 150 | 组件:cases · 根:div · 定义:caseList · ⚑MOCK |
| `frontend/pages/mobile/cases/[slug].vue` | 158 | 组件:[slug] · 根:div · 定义:route,caseStore,contactPhone,caseItem,loading,error · ⚑DEGRADED |
| `frontend/pages/mobile/contact.vue` | 243 | 组件:contact · 根:div · 定义:contactInfo,form,formErrors,submitting,submitSuccess,submitError,copied,validateForm · ⚑MOCK/DEGRADED |
| `frontend/pages/mobile/index.vue` | 395 | 组件:index · 根:div · 定义:isSearchOpen,searchQuery,categories,products,cases,hotKeywords,toggleSearch,handleSearch · ⚑MOCK |
| `frontend/pages/mobile/inquiries/index.vue` | 105 | 组件:index · 根:div |
| `frontend/pages/mobile/leads.vue` | 183 | 组件:leads · 根:div · 定义:router,activeFilter,filterTabs,filteredLeads,showAddModal,newLead,addLead |
| `frontend/pages/mobile/logistics/index.vue` | 168 | 组件:index · 根:div · 定义:router,trackingNumber,trackingResult,trackingSearched,pending,trackOrder,result · ⚑MOCK |
| `frontend/pages/mobile/news.vue` | 218 | 组件:news · 根:div · 定义:selectedCategory,categories,newsList,filteredNews,tagClass,map |
| `frontend/pages/mobile/news/[slug].vue` | 135 | 组件:[slug] · 根:div · 定义:route,newsStore,newsItem,loading,error,sanitizedContent,formatDate,date · ⚑DEGRADED |
| `frontend/pages/mobile/orders/[id].vue` | 277 | 组件:[id] · 根:div · 定义:route,router,orderStatusTimeline,statuses,statusOrder,currentIdx,getStatusText,map · ⚑MOCK |
| `frontend/pages/mobile/orders/index.vue` | 116 | 组件:index · 根:div · 定义:route,router · ⚑MOCK |
| `frontend/pages/mobile/payment/callback.vue` | 114 | 组件:callback · 根:div · 定义:route,status,verifying,result,retryPayment |
| `frontend/pages/mobile/products.vue` | 182 | 组件:products · 根:div · 定义:productStore,selectedCategory,searchQuery,isSearchOpen,loading,categories,products,query · ⚑MOCK |
| `frontend/pages/mobile/products/[id].vue` | 161 | 组件:[id] · 根:div · 定义:route,router,selectedImageIndex,openInquiry,openQuote |
| `frontend/pages/mobile/products/[id]/reviews.vue` | 502 | 组件:reviews · 根:div · 定义:route,router,reviews,totalReviews,averageRating,ratingDistribution,currentPage,totalPages · ⚑MOCK |
| `frontend/pages/mobile/user/address.vue` | 384 | 组件:address · 根:div · 定义:router,addresses,loading,error,showForm,isEditing,saving,editingId · ⚑MOCK |
| `frontend/pages/mobile/user/favorites.vue` | 161 | 组件:favorites · 根:div · 定义:router,favorites,loading,error,fetchFavorites,response,data,removeFavorite · ⚑MOCK |
| `frontend/pages/mobile/user/index.vue` | 119 | 组件:index · 根:div · 定义:router,menuItems,logout |
| `frontend/pages/mobile/user/notifications.vue` | 154 | 组件:notifications · 根:div · 定义:notificationStore,notifications,loading,error,fetchNotifications,markAllRead,openNotification,getNotificationIcon |
| `frontend/pages/mobile/user/orders.vue` | 119 | 组件:orders · 根:div · 定义:router · ⚑MOCK |
| `frontend/pages/mobile/user/settings.vue` | 254 | 组件:settings · 根:div · 定义:router,currentLocale,profileForm,profileUpdating,passwordForm,passwordUpdating,languages,user |
| `frontend/pages/news/[slug].vue` | 373 | 组件:[slug] · 根:div · 定义:route,newsStore,contactPhone,article,loading,error,sanitizedContent,relatedArticles · ⚑DEGRADED |
| `frontend/pages/news/index.vue` | 283 | 组件:index · 根:div · 定义:newsStore,contactPhone,selectedCategory,loading,categories,categoryLabels,categoryIcons,filteredArticles |
| `frontend/pages/offline.vue` | 101 | 组件:offline · 根:div · 定义:retry,goHome |
| `frontend/pages/orders/[id].vue` | 418 | 组件:[id] · 根:div · 定义:route,router,order,loading,error,orderStatusTimeline,statuses,statusOrder · ⚑MOCK |
| `frontend/pages/orders/index.vue` | 197 | 组件:index · 根:div · 定义:router,orders,loading,fetchOrders,response,data,cancelOrder,response · ⚑MOCK |
| `frontend/pages/payment/callback.vue` | 276 | 组件:callback · 根:div · 定义:route,router,verifying,paymentStatus,order,orderId,paymentTime,errorMessage |
| `frontend/pages/platform/index.vue` | 868 | 组件:index · 根:div · 定义:PlanId,PlanColumnKey,copy,mock,navLinks,trustProof,integrations,pricingMatrix · ⚑MOCK |
| `frontend/pages/privacy.vue` | 166 | 组件:privacy · 根:div |
| `frontend/pages/procurement.vue` | 1157 | 组件:procurement · 根:div · 定义:appStore,formData,errors,isSubmitting,showSuccess,expandedFaq,valueProps,products · ⚑MOCK/DEGRADED |
| `frontend/pages/products-example.vue` | 150 | 组件:products-example · 根:div · 定义:product,pageTitle,pageDescription,pageKeywords,canonicalUrl,structuredData · ⚑MOCK |
| `frontend/pages/products/[id].vue` | 489 | 组件:[id] · 根:div · 定义:route,router,product,relatedProducts,merchantIM,loading,error,selectedImageIndex · ⚑MOCK |
| `frontend/pages/products/[id]/reviews.vue` | 545 | 组件:reviews · 根:div · 定义:route,router,loading,error,productId,productName,reviews,totalReviews · ⚑MOCK |
| `frontend/pages/products/[slug].vue` | 805 | 组件:[slug] · 根:div · 定义:route,productStore,product,loading,error,contactPhone,currentLocale,faqs · ⚑MOCK |
| `frontend/pages/products/index.vue` | 395 | 组件:index · 根:div · 定义:productStore,contactPhone,selectedCategory,searchQuery,currentPage,pageSize,loading,categories · ⚑MOCK |
| `frontend/pages/publish/[id].vue` | 178 | 组件:[id] · 根:div · 定义:router,route,task,pending,statusClass,map,formatDate,fetchTask |
| `frontend/pages/publish/create.vue` | 174 | 组件:create · 根:div · 定义:router,platforms,selectedPlatform,pending,form,fetchPlatforms,api,data · ⚑MOCK |
| `frontend/pages/publish/index.vue` | 139 | 组件:index · 根:div · 定义:router,tasks,activeFilter,pending,filterTabs,filteredTasks,statusClass,map |
| `frontend/pages/request-quote.vue` | 388 | 组件:request-quote · 根:div · 定义:RFQItem,RFQRequirement,api,form,loading,apiError,success,onSubmit · ⚑MOCK |
| `frontend/pages/saas.vue` | 4 | 组件:saas |
| `frontend/pages/seo-demo.vue` | 187 | 组件:seo-demo · 根:div · 定义:seoConfig,structuredDataPreview,viewPageSource,testSEOTools |
| `frontend/pages/seo-diagnosis.vue` | 531 | 组件:seo-diagnosis · 根:div · 定义:urlInput,urlError,isDiagnosing,report,showLeadModal,isSubmitting,submitMessage,submitSuccess · ⚑MOCK |
| `frontend/pages/sitemap.xml.ts` | 137 | 定义:Product,escapeXml,config,apiBase,baseUrl,pages,res,data |
| `frontend/pages/tenant/about.vue` | 7 | 组件:about · 根:TenantSiteGateway |
| `frontend/pages/tenant/contact.vue` | 7 | 组件:contact · 根:TenantSiteGateway |
| `frontend/pages/tenant/downloads.vue` | 7 | 组件:downloads · 根:TenantSiteGateway |
| `frontend/pages/tenant/index.vue` | 7 | 组件:index · 根:TenantSiteGateway |
| `frontend/pages/tenant/products/[slug].vue` | 14 | 组件:[slug] · 根:TenantLProProductDetail · 依赖:../../../components/tenant/premium/TenantLProProductDetail.vue,../../../composables/useTenantSiteBootstrap |
| `frontend/pages/tenant/products/index.vue` | 7 | 组件:index · 根:TenantSiteGateway |
| `frontend/pages/tenant/solutions.vue` | 7 | 组件:solutions · 根:TenantSiteGateway |
| `frontend/pages/terms.vue` | 199 | 组件:terms · 根:div |
| `frontend/pages/user/address.vue` | 402 | 组件:address · 根:div · 定义:addresses,loading,showDialog,isEditing,saving,editingId,addressForm,fetchAddresses · ⚑MOCK |
| `frontend/pages/user/favorites.vue` | 252 | 组件:favorites · 根:div · 定义:router,favorites,loading,currentPage,pageSize,total,totalPages,displayedPages · ⚑MOCK |
| `frontend/pages/user/index.vue` | 262 | 组件:index · 根:div · 定义:router,user,activeTab,profileForm,userOrders,userInquiries,navItems,fetchUser |
| `frontend/pages/user/notifications.vue` | 419 | 组件:notifications · 根:div · 定义:notifications,loading,currentPage,pageSize,total,stats,activeFilter,filters |
| `frontend/pages/user/orders.vue` | 302 | 组件:orders · 根:div · 定义:router,orders,loading,currentPage,pageSize,total,activeStatus,statusFilters · ⚑MOCK |
| `frontend/pages/user/settings.vue` | 447 | 组件:settings · 根:div · 定义:api,successMessage,errorMessage,profileLoading,passwordLoading,languageLoading,notifLoading,avatarInput · ⚑MOCK |
| `frontend/plugins/api.ts` | 36 | 定义:api,token,tokenCookie |
| `frontend/plugins/auth.ts` | 9 | 定义:auth |
| `frontend/plugins/error-handler.ts` | 55 | 定义:safeMessage,logError,msg,onUnhandledRejection,onGlobalError |
| `frontend/plugins/i18n-rtl.ts` | 20 | 定义:rtlLocales,dir |
| `frontend/plugins/intersect.ts` | 37 | 定义:callback,observer |
| `frontend/plugins/pwa.ts` | 41 | 定义:newWorker · ⚑DEGRADED |
| `frontend/plugins/site-analytics.client.ts` | 26 | 定义:router,el,href |
| `frontend/plugins/toast.ts` | 25 | 定义:appStore,toast |
| `frontend/server/api/generate.post.ts` | 29 | 定义:body,cacheKey,cached,backendUrl,data · 依赖:../utils/redis |
| `frontend/server/api/leads.get.ts` | 14 | 定义:backendUrl,query,limit |
| `frontend/server/api/leads.post.ts` | 14 | 定义:body,backendUrl |
| `frontend/server/api/products.get.ts` | 152 | 定义:Product,mockProducts,query,category,search,searchLower · 依赖:../utils/cache · ⚑MOCK |
| `frontend/server/api/tenant-resolve.get.ts` | 25 | 定义:host,config,apiHost,target,status |
| `frontend/server/middleware/ai-crawler.ts` | 77 | 定义:url,ua,q,tenant,config,apiHost,text,products · 依赖:../utils/ai-crawler |
| `frontend/server/middleware/api-proxy.ts` | 95 | 定义:RATE_LIMIT,RATE_LIMIT_WINDOW,requestCounts,getClientIp,xForwardedFor,xRealIp,checkRateLimit,now |
| `frontend/server/middleware/geo-locale.ts` | 155 | 定义:COUNTRY_TO_LOCALE,LOCALE_PREFIXES,detectCountryByIP,controller,timeout,res,data,LOCALE_PATH_RE |
| `frontend/server/plugins/ai-crawler-semantic.ts` | 35 | 定义:text,escaped,block,ctx |
| `frontend/server/routes/llms-full.txt.get.ts` | 27 | 定义:config,apiHost,q,tenant,lang,text |
| `frontend/server/routes/llms.txt.get.ts` | 27 | 定义:config,apiHost,q,tenant,lang,text |
| `frontend/server/utils/ai-crawler.ts` | 40 | 定义:AI_CRAWLER_PATTERNS,isAiCrawlerUserAgent,detectAiCrawlerFamily,resolveTenantDomainFromEvent,raw,qIndex,qs,params |
| `frontend/server/utils/cache.ts` | 136 | 定义:CacheOptions,useAPICache,cacheStore,generateCacheKey,url,query,get,key |
| `frontend/server/utils/redis.ts` | 66 | 定义:getRedis,redisGet,redis,redisSet,redis,redisDel,redis · ⚑DEGRADED |
| `frontend/stores/aiConfig.ts` | 93 | 定义:AIProvider,AIQuota,AIConfigData,useAiConfigStore,provider |
| `frontend/stores/alerts.ts` | 144 | 定义:useAlertsStore,api,alerts,rules,statistics,loading,currentAlert,currentRule |
| `frontend/stores/analytics.ts` | 79 | 定义:AnalyticsData,useAnalyticsStore,response,response,result |
| `frontend/stores/app.ts` | 77 | 定义:useAppStore,globalLoading,loadingCount,startLoading,stopLoading,toasts,showToast,id |
| `frontend/stores/auth.ts` | 66 | 定义:useAuthStore,res,accessToken,usernameCookie,usernameCookie,savedToken,usernameCookie |
| `frontend/stores/case.ts` | 99 | 定义:CaseStudy,useCaseStore,response |
| `frontend/stores/inquiry.ts` | 94 | 定义:Inquiry,useInquiryStore,response |
| `frontend/stores/leads.ts` | 53 | 定义:LeadDraft,useLeadsStore,draft,saveDraft,clearDraft,lastSubmittedId,lastSubmittedPrice,recordSubmission |
| `frontend/stores/news.ts` | 115 | 定义:News,useNewsStore,response,article |
| `frontend/stores/notification.ts` | 58 | 定义:Notification,useNotificationStore,api,notifications,unreadCount,loading,fetchNotifications,response |
| `frontend/stores/product.ts` | 98 | 定义:ProductCategory,Product,useProductStore,map,response |
| `frontend/stores/seo.ts` | 90 | 定义:SEOData,useSeoStore,response,result,result |
| `frontend/stores/settings.ts` | 91 | 定义:SettingsData,useSettingsStore |
| `frontend/stores/system.ts` | 107 | 定义:SystemInfo,SystemStats,useSystemStore,response |
| `frontend/stores/user.ts` | 90 | 定义:User,useUserStore,response |
| `frontend/tailwind.config.ts` | 185 |  |
| `frontend/types/alert.ts` | 30 | 定义:Alert,AlertRule,AlertStatistics |
| `frontend/types/index.ts` | 121 | 定义:Product,ProductCategory,Case,News,Inquiry,User,SeoConfig,ApiResponse |
| `frontend/utils/geo.ts` | 96 | 定义:GeoResult,COUNTRY_TO_LANG,COUNTRY_TO_IM,detectCountryClient,cached,res,code,detectCountryServer |
| `frontend/utils/l-pro-publish-gate.ts` | 178 | 定义:LProPublishIssue,LProPublishGate,L_PRO_TEMPLATE_ID,MIN_PRODUCTS,MIN_SPECS,productItems,pages,products |
| `frontend/utils/regions.ts` | 148 | 定义:City,Province,regions |
| `frontend/utils/submitPublicInquiry.ts` | 40 | 定义:PublicInquiryPayload,submitPublicInquiry,body,res,result |
| `frontend/utils/tenant-preview-domain.ts` | 72 | 定义:readTenantFromQueryRecord,direct,first,domain,readTenantFromSearch,m,resolveTenantPreviewDomain,resolveDevTenantPreviewHost |
| `frontend/utils/tenant-product-slug.ts` | 85 | 定义:TenantCatalogProduct,slugifyTenantSegment,base,productSlug,categorySlug,normalizeCatalogProducts,items,o |
| `frontend/utils/tenant-seo-url.ts` | 89 | 定义:TENANT_SEO_HREFLANG_LOCALES,TenantSeoPrimaryMarket,TENANT_SEO_WEBMASTER_HINTS,PRESERVED_QUERY_KEYS,preservedTenantPreviewQuery,out,raw,buildTenantLanguagePath |
| `frontend/utils/tenant-site-i18n.ts` | 63 | 定义:mergeSiteI18nBlock,out,i18n,localizedSiteString,fromOverlay,root,pages,merged · ⚑DEGRADED |
| `frontend/utils/visitorContextCache.ts` | 59 | 定义:CACHE_TTL_MS,CachedPayload,visitorContextCacheKey,lang,readRaw,raw,parsed,wrapped · 依赖:../composables/useVisitorLocale |
| `frontend/utils/visitorContextFetch.ts` | 68 | 定义:VisitorContextFetchResult,TIMEOUT_MS,MAX_RETRIES,cancelVisitorContextFetch,fetchVisitorContextPayload,controller,timeout,res |
| `frontend/youding-admin-kit/components/YdSearchBar.vue` | 42 | 组件:YdSearchBar · 根:div · emits |
| `frontend/youding-admin-kit/components/YdStatsCard.vue` | 58 | 组件:YdStatsCard · 根:div · props · 定义:props,displayValue |
| `frontend/youding-admin-kit/composables/useYoudingColumnLayout.ts` | 115 | 定义:loadColumnOrder,defaults,raw,saved,valid,missing,loadHiddenKeys,raw · 依赖:./useYoudingTable |
| `frontend/youding-admin-kit/composables/useYoudingTable.ts` | 143 | 定义:YoudingTableFetcher,YoudingTableColumn,UseYoudingTableOptions,useYoudingTable,loading,items,total,page · 依赖:./useYoudingColumnLayout · ⚑STUB |
| `frontend/youding-admin-kit/env.d.ts` | 1 |  |
| `frontend/youding-admin-kit/types/uac.d.ts` | 76 | 定义:AdminShell,UacAuthMark,UacRouteMeta,UacMenuRoute,UacUserInfo,UacPermissionBundle,UacLoginResult,UacTableQuery |