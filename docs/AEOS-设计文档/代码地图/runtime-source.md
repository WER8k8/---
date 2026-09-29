# 3000 官网运行源 主要备份/上线网站/frontend

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\主要备份\上线网站\frontend` · **296 个文件** · 3000 官网运行源（Vite 暖白+砖橙）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `app.config.ts` | 34 |  |
| `app.vue` | 30 | 组件:app · 根:router-view · 定义:route,RTL_LANGS,isRtl |
| `components.d.ts` | 22 | 定义:GlobalComponents |
| `components/FloatingContact.vue` | 299 | 组件:FloatingContact · 根:div · 定义:isZh,showWechatCard,copied,showBackTop,handleScroll,scrollToTop,prefersReduced,WHATSAPP_NUMBER · ⚑MOCK |
| `components/LanguageSwitcher.vue` | 159 | 组件:LanguageSwitcher · 根:div · 定义:switchLocalePath,locales,setLocale,isOpen,dropdownRef,currentLocale,currentLocaleName,found |
| `components/MobileExpandable.vue` | 48 | 组件:MobileExpandable · 根:div · props · 定义:Props,props,isExpanded,toggle |
| `components/MobileNavbar.vue` | 53 | 组件:MobileNavbar · 根:header · props · 定义:Props,props,scrollY,isVisible,lastScrollY,handleScroll,currentScrollY |
| `components/MobilePerformanceLayer.vue` | 112 | 组件:MobilePerformanceLayer · 根:div · props · emits · 定义:Props,props,emit,containerRef,isRefreshing,startY,handleTouchStart,handleTouchEnd |
| `components/MobileScrollReveal.vue` | 55 | 组件:MobileScrollReveal · 根:div · props · 定义:Props,props,containerRef,isInView,observer,animationClass |
| `components/MobileSwipeGesture.vue` | 83 | 组件:MobileSwipeGesture · 根:div · props · 定义:SwipeResult,Props,props,startX,startY,isSwiping,handleTouchStart,touch |
| `components/MobileTabBar.vue` | 118 | 组件:MobileTabBar · 根:nav · props · 定义:Props,route,HomeIcon,ProductIcon,CaseIcon,NewsIcon,navItems,isActive |
| `components/OptimizedImage.vue` | 167 | 组件:OptimizedImage · 根:div · props · 定义:LazyImageProps,props,containerRef,imageRef,isLoaded,hasError,isVisible,loadingStrategy · ⚑MOCK/DEGRADED |
| `components/PerformanceMonitor.vue` | 126 | 组件:PerformanceMonitor · 根:div · props · 定义:props,isDev,fps,memoryUsage,loadTime,calculateFPS,now,delta |
| `components/PerformanceOptimizer.vue` | 5 | 组件:PerformanceOptimizer · 根:div |
| `components/ProductSpecAccordion.vue` | 94 | 组件:ProductSpecAccordion · 根:div · props · 定义:props,isOpen,currentUnit,toggleUnit |
| `components/ResponsiveCard.vue` | 229 | 组件:ResponsiveCard · 根:div · props · emits · 定义:MetaItem |
| `components/ResponsiveGrid.vue` | 73 | 组件:ResponsiveGrid · 根:div · props · 定义:Columns,GridProps,props,gridClass,gapClasses,defaultCols |
| `components/ResponsiveNavbar.vue` | 201 | 组件:ResponsiveNavbar · 根:nav · emits · 定义:navItems,route,isMobileMenuOpen,isActive,toggleMobileMenu,closeMobileMenu,emit,toggleSearch |
| `components/SEOHead.vue` | 242 | 组件:SEOHead · 根:div · props · 定义:SEOProps,props,config,route,baseUrl,fullUrl,defaultOgImage,defaultTwitterImage |
| `components/ShippingTimeline.vue` | 110 | 组件:ShippingTimeline · 根:div · props · 定义:route,props,timeline,fetchTimeline,res |
| `components/StickyImBar.vue` | 286 | 组件:StickyImBar · 根:div · 定义:$fetch,route,showBar,showForm,MappedChannel,imChannels,channelIndex,form · ⚑MOCK |
| `components/ai/AiProviderGuide.vue` | 280 | 组件:AiProviderGuide · 根:teleport · props · emits · 定义:props,emit,router,recommendPlatforms,handleSetup,handleLater |
| `components/business/FreightCalculator.vue` | 111 | 组件:FreightCalculator · 根:Card · props · emits · 定义:props,emit,localDistance,localQuantity,estimatedPrice,hasDiscount,distanceHint,freight · ⚑MOCK |
| `components/business/LeadItem.vue` | 99 | 组件:LeadItem · 根:article · props · 定义:Lead,props,displayTime,statusLabel,badgeClass,calculateTimeAgo,now,created |
| `components/business/RegionHeatmap.vue` | 46 | 组件:RegionHeatmap · 根:Card · props · 定义:RegionItem,props,maxCount,barWidth |
| `components/business/RegionSelector.vue` | 88 | 组件:RegionSelector · 根:div · props · emits · 定义:props,emit,showPicker,selectedProvince,selectedLabel,provinces,selectProvince,selectCity · ⚑MOCK |
| `components/business/SchemaMarkup.vue` | 28 | 组件:SchemaMarkup · 根:Head · props · 定义:props,schemaData,schemaString |
| `components/business/StatCard.vue` | 25 | 组件:StatCard · 根:Card · props |
| `components/common/AnimatedSection.vue` | 125 | 组件:AnimatedSection · 根:div · props · 定义:props,target,isVisible,isMounted,animationStyle |
| `components/common/EmptyState.vue` | 66 | 组件:EmptyState · 根:div · props · 定义:Props |
| `components/common/ErrorBoundary.vue` | 112 | 组件:ErrorBoundary · 根:div · props · emits · 定义:Props,props,emit,hasError,error,resetError |
| `components/common/Footer.vue` | 333 | 组件:Footer · 定义:isZhLocale,phone,email,address,currentYear,showWechatId,productLinks,quickLinks |
| `components/common/Header.vue` | 453 | 组件:Header · 根:header · 定义:route,phone,isScrolled,isHidden,isMobileMenuOpen,lastScrollTop,scrollThreshold,mobileOpenGroup |
| `components/common/LoadingState.vue` | 116 | 组件:LoadingState · 根:div · props · 定义:Props,props,getLineWidth |
| `components/common/ParallaxContainer.vue` | 70 | 组件:ParallaxContainer · 根:div · props · 定义:props,container,scrollY,containerStyle,offset,transforms,handleScroll |
| `components/common/ParticleBackground.vue` | 125 | 组件:ParticleBackground · 根:canvas · props · 定义:props,canvas,resizeCanvas,initParticles,drawParticles,dx,dy,distance |
| `components/common/ScrollProgress.vue` | 52 | 组件:ScrollProgress · 根:div · 定义:container,progress,handleScroll,scrollTop,docHeight |
| `components/icons/AwardIcon.vue` | 17 | 组件:AwardIcon · 根:svg |
| `components/icons/BrickIcon.vue` | 17 | 组件:BrickIcon · 根:svg |
| `components/icons/DropletsIcon.vue` | 17 | 组件:DropletsIcon · 根:svg |
| `components/icons/FactoryIcon.vue` | 17 | 组件:FactoryIcon · 根:svg |
| `components/icons/ShieldIcon.vue` | 17 | 组件:ShieldIcon · 根:svg |
| `components/icons/ThermometerIcon.vue` | 17 | 组件:ThermometerIcon · 根:svg |
| `components/onboarding/OnboardingGuide.vue` | 151 | 组件:OnboardingGuide · 根:Teleport · props · emits · 定义:Props,props,emit,steps,currentStep,totalSteps,next,prev · ⚑MOCK |
| `components/procurement/ProcurementFaq.vue` | 118 | 组件:ProcurementFaq · props · emits · 定义:ProcurementFaqItem,emit |
| `components/procurement/ProcurementHero.vue` | 156 | 组件:ProcurementHero · emits · 定义:emit |
| `components/procurement/ProcurementLeadForm.vue` | 319 | 组件:ProcurementLeadForm · props · emits · 定义:ProcurementFormData,ProcurementFormErrors,emit · ⚑MOCK/DEGRADED |
| `components/procurement/ProcurementProducts.vue` | 145 | 组件:ProcurementProducts · props · emits · 定义:ProcurementProductItem,emit |
| `components/procurement/ProcurementSchema.vue` | 38 | 组件:ProcurementSchema · props |
| `components/procurement/ProcurementStickyCta.vue` | 57 | 组件:ProcurementStickyCta · emits · 定义:emit |
| `components/procurement/ProcurementTestimonial.vue` | 124 | 组件:ProcurementTestimonial |
| `components/procurement/ProcurementValueProps.vue` | 90 | 组件:ProcurementValueProps · props · 定义:ProcurementValueItem |
| `components/seo/ContentOptimizer.vue` | 278 | 组件:ContentOptimizer · 根:div · 定义:seo,optType,keywordsRaw,content,model,optimizing,error,result · ⚑MOCK |
| `components/seo/LLMSTxtGenerator.vue` | 206 | 组件:LLMSTxtGenerator · 根:div · 定义:seo,SectionTemplate,sectionLabels,availableSections,selectedSectionTypes,includeAiInstructions,generating,error |
| `components/seo/SchemaMarkupGenerator.vue` | 445 | 组件:SchemaMarkupGenerator · 根:div · 定义:schemaTypes,isGenerating,copied,generatedSchema,validationResult,form,templateFields,fields · ⚑MOCK |
| `components/seo/SiteAudit.vue` | 294 | 组件:SiteAudit · 根:div · 定义:seo,auditType,targetUrl,auditing,error,AuditIssue,AuditRecommendation,AuditResult · ⚑MOCK |
| `components/tenant/TenantInquiryForm.vue` | 214 | 组件:TenantInquiryForm · 根:form · props · 定义:props,form,next,submitting,errorText,successText,phoneLabel,onSubmit · 依赖:../../utils/submitPublicInquiry · ⚑MOCK |
| `components/tenant/TenantSite.vue` | 857 | 组件:TenantSite · 根:div · props · 定义:TenantMobileQuickAction,props,loading,error,tenant,visualHtmlRef,activeNav,mobileMenuOpen · 依赖:../../composables/useTenantMediaUrl,../../composables/useTenantVisitorContacts,../../composables/useVisitorLocale,../../composables/useVisualSiteInquiryBinder,../../composables/useVisualSiteNavBinder · ⚑MOCK/DEGRADED |
| `components/tenant/TenantSiteAbout.vue` | 173 | 组件:TenantSiteAbout · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteAdvantages.vue` | 63 | 组件:TenantSiteAdvantages · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteApplications.vue` | 25 | 组件:TenantSiteApplications · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteCategories.vue` | 28 | 组件:TenantSiteCategories · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteCompanion.vue` | 643 | 组件:TenantSiteCompanion · 根:div · props · 定义:props,accentColor,accentDeep,accentMid,accentLight,isRtl,FALLBACK_UI,ui · 依赖:../../composables/useTenantVisitorContacts,./TenantSiteCompanionBubble.vue,./TenantSiteCompanionChat.vue,./TenantSiteCompanionContactList.vue,./TenantSiteCompanionMascot.vue · ⚑MOCK/DEGRADED |
| `components/tenant/TenantSiteCompanionBubble.vue` | 59 | 组件:TenantSiteCompanionBubble · 根:div · props · emits · 定义:emit |
| `components/tenant/TenantSiteCompanionChat.vue` | 199 | 组件:TenantSiteCompanionChat · 根:div · props · emits · 定义:CompanionChatMessage,CompanionQuickPrompt,props,emit,askValue,chatScroll · ⚑MOCK |
| `components/tenant/TenantSiteCompanionContactList.vue` | 111 | 组件:TenantSiteCompanionContactList · 根:div · props · emits · 定义:emit · 依赖:../../composables/useVisitorLocale,./tenant-site-types |
| `components/tenant/TenantSiteCompanionMascot.vue` | 135 | 组件:TenantSiteCompanionMascot · 根:button · props · emits · 定义:emit |
| `components/tenant/TenantSiteCompanionPanelHead.vue` | 55 | 组件:TenantSiteCompanionPanelHead · 根:div · props · emits · 定义:emit |
| `components/tenant/TenantSiteCompanionPanelTabs.vue` | 63 | 组件:TenantSiteCompanionPanelTabs · 根:div · props · emits · 定义:CompanionPanelTab,emit |
| `components/tenant/TenantSiteContactPanel.vue` | 99 | 组件:TenantSiteContactPanel · 根:section · props · 依赖:../../composables/useVisitorLocale,./tenant-site-types |
| `components/tenant/TenantSiteFooter.vue` | 75 | 组件:TenantSiteFooter · 根:footer · props · 依赖:../../composables/useVisitorLocale,./tenant-site-types |
| `components/tenant/TenantSiteForum.vue` | 36 | 组件:TenantSiteForum · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteGateway.vue` | 44 | 组件:TenantSiteGateway · 根:TenantSite · props · 定义:props,legacyPage,lProComponent · 依赖:../../composables/useTenantSiteBootstrap,./premium/TenantLProAbout.vue,./premium/TenantLProContact.vue,./premium/TenantLProDownloads.vue,./premium/TenantLProHome.vue |
| `components/tenant/TenantSiteHeader.vue` | 264 | 组件:TenantSiteHeader · 根:header · props · emits · 定义:emit · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteHero.vue` | 274 | 组件:TenantSiteHero · 根:section · props · 依赖:./tenant-site-types · ⚑MOCK |
| `components/tenant/TenantSiteKnowledgeTopics.vue` | 34 | 组件:TenantSiteKnowledgeTopics · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteMobileActionBar.vue` | 85 | 组件:TenantSiteMobileActionBar · 根:nav · props · emits · 定义:emit · 依赖:../../composables/useTenantVisitorContacts |
| `components/tenant/TenantSiteProductGrid.vue` | 62 | 组件:TenantSiteProductGrid · 根:section · props · 依赖:./tenant-site-types · ⚑DEGRADED |
| `components/tenant/TenantSiteServiceStages.vue` | 71 | 组件:TenantSiteServiceStages · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteSolutions.vue` | 73 | 组件:TenantSiteSolutions · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteStats.vue` | 75 | 组件:TenantSiteStats · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/TenantSiteTopbar.vue` | 72 | 组件:TenantSiteTopbar · 根:div · props · 依赖:../../composables/useVisitorLocale,./tenant-site-types |
| `components/tenant/TenantSiteVideos.vue` | 32 | 组件:TenantSiteVideos · 根:section · props · 依赖:./tenant-site-types |
| `components/tenant/premium/LProLanguagePicker.vue` | 272 | 组件:LProLanguagePicker · 根:div · props · 定义:CheckIcon,props,open,rootRef,tier1Languages,fromApi,tier2Languages,currentLanguageName · 依赖:../../../composables/useTenantLanguagePicker |
| `components/tenant/premium/PremiumB2bShell.vue` | 418 | 组件:PremiumB2bShell · 根:div · props · 定义:props,menuOpen,bootstrap,overlay,companyName,brandTagline,themePrimary,establishedYear · 依赖:../../../composables/useTenantGeoJsonLd,../../../composables/useTenantLProNav,../../../composables/useTenantLProSeoHead,../../../composables/useTenantLanguagePicker,../../../composables/useTenantSiteBootstrap |
| `components/tenant/premium/TenantLProAbout.vue` | 85 | 组件:TenantLProAbout · 根:PremiumB2bShell · 定义:overlay,companyName,aboutText,mission,vision,capacitySummary,milestones,raw · 依赖:../../../composables/useTenantSiteBootstrap,../../../utils/tenant-site-i18n,./PremiumB2bShell.vue |
| `components/tenant/premium/TenantLProContact.vue` | 130 | 组件:TenantLProContact · 根:PremiumB2bShell · 定义:route,contactPhone,contactEmail,contactWhatsapp,contactWechat,contactQq,factoryAddress,ctaPrimary · 依赖:../../../composables/useSiteAnalytics,../../../composables/useTenantSiteBootstrap,../../../composables/useTenantVisitorContacts,../../../utils/contact-inquiry-cta,../TenantInquiryForm.vue · ⚑MOCK |
| `components/tenant/premium/TenantLProDownloads.vue` | 53 | 组件:TenantLProDownloads · 根:PremiumB2bShell · 定义:items,raw,o,title,url · 依赖:../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,./PremiumB2bShell.vue |
| `components/tenant/premium/TenantLProHome.vue` | 798 | 组件:TenantLProHome · 根:PremiumB2bShell · 定义:overlay,establishedYear,primaryPromise,heroTitle,heroDescription,ctaPrimary,inquiryHook,productsTitle · 依赖:../../../composables/useSiteAnalytics,../../../composables/useTenantLProNav,../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,../../../utils/contact-inquiry-cta |
| `components/tenant/premium/TenantLProProductDetail.vue` | 188 | 组件:TenantLProProductDetail · 根:PremiumB2bShell · 定义:route,slug,product,documentTitle,documentDescription,prefillProduct,contactWithProductHref,siteOrigin · 依赖:../../../composables/useTenantMediaUrl,../../../composables/useTenantSiteBootstrap,../../../utils/contact-inquiry-cta,../../../utils/tenant-product-slug,../TenantInquiryForm.vue · ⚑MOCK |
| `components/tenant/premium/TenantLProProducts.vue` | 149 | 组件:TenantLProProducts · 根:PremiumB2bShell · 定义:route,overlay,productsTitle,productsDescription,activeCategory,q · 依赖:../../../composables/useTenantLProNav,../../../composables/useTenantMediaUrl,../../../composables/useTenantProductFilter,../../../composables/useTenantSiteBootstrap,../../../utils/tenant-product-slug · ⚑MOCK |
| `components/tenant/premium/TenantLProSolutions.vue` | 60 | 组件:TenantLProSolutions · 根:PremiumB2bShell · 定义:overlay,solutions,raw,solutionLabel,solutionContactHref,onSolutionCta · 依赖:../../../composables/useSiteAnalytics,../../../composables/useTenantSiteBootstrap,../../../utils/contact-inquiry-cta,./PremiumB2bShell.vue |
| `components/tenant/tenant-site-types.ts` | 115 | 定义:BrandColors,SiteCategory,SiteApplication,SiteAdvantage,SiteStat,SiteMilestone,SiteSolution,SiteServiceStage |
| `components/ui/Badge.vue` | 26 | 组件:Badge · 根:span · props · 定义:Props,variantClasses |
| `components/ui/Button.vue` | 41 | 组件:Button · 根:button · props · 定义:Props,props,variantClasses,sizeClasses |
| `components/ui/Card.vue` | 20 | 组件:Card · 根:div · props · 定义:Props |
| `components/ui/EmptyState.vue` | 20 | 组件:EmptyState · 根:div · props |
| `components/ui/ErrorBoundary.vue` | 78 | 组件:ErrorBoundary · 根:template · props · 定义:Props,props,error,errorInfo,resetError · ⚑DEGRADED |
| `components/ui/Input.vue` | 29 | 组件:Input · 根:input · props · emits · 定义:Props,emit,handleInput,target · ⚑MOCK |
| `components/ui/Label.vue` | 17 | 组件:Label · 根:label · props · 定义:Props |
| `components/ui/LazyImage.vue` | 115 | 组件:LazyImage · 根:div · props · 定义:Props,props,isLoaded,hasError,imgRef,observer,loadImage,img · ⚑MOCK |
| `components/ui/Modal.vue` | 71 | 组件:Modal · 根:Teleport · props · emits · 定义:props,emit,close,handleOverlayClick |
| `components/ui/PriceDisplay.vue` | 29 | 组件:PriceDisplay · 根:span · props · 定义:props,formattedAmount |
| `components/ui/Select.vue` | 27 | 组件:Select · 根:select · props · emits · 定义:Props,emit,handleChange,target |
| `components/ui/Skeleton.vue` | 61 | 组件:Skeleton · 根:div · props · 定义:Props,props,skeletonLines,lines |
| `components/ui/ToastRenderer.vue` | 60 | 组件:ToastRenderer · 根:ClientOnly · 定义:appStore,iconMap,typeClass,map · ⚑DEGRADED |
| `components/ui/VirtualList.vue` | 79 | 组件:VirtualList · 根:div · props · 定义:Props,props,containerRef,scrollTop,visibleStart,visibleCount,containerHeight,visibleEnd |
| `composables/_h3-shim.ts` | 26 | 定义:getHeader,setHeader,setResponseStatus,createError,H3Event,EventHandler,defineEventHandler |
| `composables/_nuxt-app-module.ts` | 71 |  |
| `composables/_nuxt-shims.ts` | 562 | 定义:VueAPIs,RouterAPIs,PiniaAPIs,I18nAPIs,navigateTo,router,HeadInput,_headState · 依赖:../stores/app |
| `composables/useAdminAppUrl.ts` | 32 | 定义:useAdminAppUrl,config,base,loginUrl,login,root |
| `composables/useApi.ts` | 183 | 定义:ApiState,RequestOptions,getAuthToken,cookies,localStorageToken,setAuthToken,useApi,apiBase |
| `composables/useApiBase.ts` | 24 | 定义:useApiRoot,config,apiHost,apiBase,root,apiUrl,p,base |
| `composables/useApiV1.ts` | 18 | 定义:useApiV1Base,config,apiHost,apiBase,useApiV1Url,base,p |
| `composables/useAppScroll.ts` | 33 | 定义:getAppScrollY,app,scrollAppToTop,app,onAppScroll,app |
| `composables/useGEOContent.ts` | 220 | 定义:FAQ,geoFAQs,useGEOContent,featuredFAQs,faqsByCategory,grouped,getFAQById,searchFAQs |
| `composables/useGEOFAQsMultilingual.ts` | 211 | 定义:GeoFAQ,geoFAQsMultilingual,useGEOFAQsMultilingual,featuredFAQs,faqsByCategory,grouped,getFAQByLocale,faq |
| `composables/useGEOProducts.ts` | 148 | 定义:Product,ProductFeature,ProductSpecification,geoProducts,useGEOProducts,featuredProducts,productsByCategory,grouped · ⚑MOCK/DEGRADED |
| `composables/useImRouting.ts` | 70 | 定义:ImChannel,useImRouting,config,route,merchantId,fromQuery,pub,countryCode · ⚑DEGRADED |
| `composables/useLazyLoad.ts` | 226 | 定义:createLazyComponent,lazyComponent,usePrefetch,prefetch,useLinkPrefetch,prefetchedUrls,prefetchLink,conn |
| `composables/useLocalized.ts` | 66 | 定义:HAN_RE,parseTranslations,raw,parsed,_is_clean_non_zh,useLocalized,isZh,pick · ⚑DEGRADED |
| `composables/useMarketingAnalytics.ts` | 90 | 定义:SESSION_KEY,LANDING_KEY,LAST_CLICK_KEY,AB_KEY,newSessionId,PlatformAbVariant,useMarketingAnalytics,route |
| `composables/useMobileInteractions.ts` | 429 | 定义:useMobileInteractions,touchStartX,touchStartY,touchStartTime,isSwiping,swipeDirection,swipeDistance,minSwipeDistance |
| `composables/useOfflineCache.ts` | 553 | 定义:OfflineQueueItem,CacheStatusEntry,SyncResult,FetchWithCacheOptions,FetchResult,SW_PATH,SW_SCOPE,useOfflineCache · ⚑DEGRADED |
| `composables/usePerformance.ts` | 183 | 定义:useLazyImage,imageRef,isLoaded,isInView,loadImage,img,observer,useDebounce |
| `composables/useResponsive.ts` | 225 | 定义:Breakpoint,BreakpointConfig,defaultBreakpoints,useResponsive,getWindowWidth,windowWidth,handleResize,isBreakpoint |
| `composables/useSEOHead.ts` | 228 | 定义:SEOMetadata,generateOrganizationSchema,generateProductSchema,generateArticleSchema,generateCaseSchema,generateFAQSchema,generateLocalBusinessSchema,useSEOHead · 依赖:./useTenantGeoJsonLd |
| `composables/useSEOMeta.ts` | 109 | 定义:SEOMeta,useSEOMeta,config,route,defaultMeta,generateTitle,generateCanonicalUrl,baseUrl |
| `composables/useSanitize.ts` | 47 | 定义:PURIFY_CONFIG,useSanitize,sanitizeHtml · ⚑DEGRADED |
| `composables/useSeo.ts` | 180 | 定义:DashboardData,KeywordRanking,OptimizeRequest,OptimizeResponse,ValidateContentResponse,ExtractParamsResponse,LlmsGenerateRequest,LlmsGenerateResponse · 依赖:./useApi |
| `composables/useSiteAnalytics.ts` | 130 | 定义:$fetch,SESSION_KEY,LANDING_KEY,LAST_CLICK_KEY,isClient,newSessionId,useSiteAnalytics,route |
| `composables/useTenantGeoJsonLd.ts` | 264 | 定义:TenantGeoJsonLdInput,useTenantGeoJsonLd,jsonLdGraph,origin,graph,org,addr,items · 依赖:../utils/tenant-product-slug |
| `composables/useTenantLProNav.ts` | 51 | 定义:TenantLProNavKey,TENANT_L_PRO_PATHS,tenantProductDetailPath,tenantProductsCategoryQuery,TenantLProNavItem,buildTenantLProNavItems,items |
| `composables/useTenantLProSeoHead.ts` | 149 | 定义:TenantSeoPrimaryMarket,TenantLProSeoHeadInput,useTenantLProSeoHead,route,config,requestHeaders,primaryMarket,previewQuery · 依赖:../utils/tenant-seo-url,./useTenantLProNav |
| `composables/useTenantLanguagePicker.ts` | 65 | 定义:TenantLanguageOption,TIER1_LANGUAGES,TIER2_LANGUAGES,tenantLanguageStorageKey,readStoredTenantLanguage,writeStoredTenantLanguage,googleTranslatePageUrl,url |
| `composables/useTenantMediaUrl.ts` | 28 | 定义:useTenantMediaUrl,config,apiHost,resolveMediaUrl,path,host |
| `composables/useTenantProductFilter.ts` | 99 | 定义:TenantProductListItem,ProductSortKey,useTenantProductFilter,searchQuery,sortBy,specFilter,catalogWithSlugs,specFilterOptions · 依赖:../utils/tenant-product-slug |
| `composables/useTenantSiteBootstrap.ts` | 169 | 定义:TenantCatalogProduct,TenantSiteBrand,TenantSiteInfo,siteContentOf,sc,isLProSiteContent,visual,tid · 依赖:../utils/tenant-product-slug,./useApiBase,./useVisitorLocale |
| `composables/useTenantSiteContext.ts` | 69 | 定义:useTenantSiteContext,config,resolvedTenantId,resolvedMerchantId,loading,ensureTenantContext,envTid,attempted |
| `composables/useTenantVisitorContacts.ts` | 170 | 定义:CN_CHANNEL_TYPES,DEFAULT_ORDER,CN_ORDER,TOPBAR_TYPES,CHANNEL_LABELS,TenantMobileQuickAction,channelLabel,pack · 依赖:./useVisitorLocale · ⚑DEGRADED |
| `composables/useToast.ts` | 32 | 定义:useToast,appStore,show,success,error,warning,info |
| `composables/useVisitorLocale.ts` | 402 | 定义:VisitorContactChannel,VisitorContext,FALLBACK_SITE_UI,FALLBACK_WANGCAI_UI,applyContext,buildFallbackContext,resolveFetchLanguage,explicit · 依赖:../utils/tenant-preview-domain,../utils/visitorContextCache,../utils/visitorContextFetch,./useTenantLanguagePicker · ⚑MOCK/DEGRADED |
| `composables/useVisualSiteInquiryBinder.ts` | 133 | 定义:VisualInquiryBinderOptions,readForm,fd,showFormMessage,bindVisualSiteInquiryForms,handlers,form,fn · 依赖:../utils/submitPublicInquiry |
| `composables/useVisualSiteNavBinder.ts` | 25 | 定义:bindVisualSiteNavLinks,handlers,tenantParam,el,fn,url |
| `config/modules.ts` | 191 | 定义:ModuleConfig,ADMIN_MODULES,ROLE_LABELS,getUserModules,hasAccessToModule,module |
| `config/plan-catalog.ts` | 251 | 定义:PLAN_ORDER,PlanId,PLAN_REGISTER_CODE,REGISTER_CODE_TO_PLAN,PLAN_CATALOG,FEATURE_LABELS,MatrixCell,PricingMatrixRow |
| `config/platform-marketing-content.ts` | 189 | 定义:MatrixCell,PLATFORM_COPY,NAV_LINKS,TRUST_PROOF,INTEGRATIONS,PRICING_MATRIX,PLAN_FEATURE_BULLETS,LANDING_HERO_PREVIEW · 依赖:./plan-catalog |
| `config/public-sites.ts` | 66 | 定义:PublicSiteId,PublicSiteDefinition,PUBLIC_SITES,getPublicSite |
| `config/site-navigation.ts` | 73 | 定义:SiteNavLink,SiteNavItem,siteMainNavigation,navKey |
| `config/site.ts` | 52 | 定义:env,v,SITE_CONFIG,API_CONFIG,SEO_CONFIG · ⚑DEGRADED |
| `config/tenant-site-defaults.ts` | 20 | 定义:TenantProofCase,DEFAULT_TENANT_PROOF_CASES,DEFAULT_EXPORT_BADGES |
| `data/comparison.ts` | 98 | 定义:CompareField,CompareColumn,CompareRow,compareColumns,compareRows,compareAdvice |
| `data/finder.ts` | 166 | 定义:FinderField,FinderPriority,FinderOption,FinderStep,productProfiles,finderSteps,FinderAnswers,FinderRank |
| `data/markets.ts` | 175 | 定义:MarketField,MarketFaq,Market,FAQ_SPEC,FAQ_DELIVERY,markets,getMarket |
| `data/partner.ts` | 159 | 定义:PartnerField,PartnerCard,PartnerStep,PartnerFaq,pickPartner,distributorBenefits,distributorSteps,distributorFaqs |
| `data/solutions.ts` | 359 | 定义:SolutionField,SolutionFaq,SolutionSpecRow,Solution,solutions,getSolution,pick · ⚑DEGRADED |
| `data/technical.ts` | 133 | 定义:TechField,TechCertificate,TechStandard,TechGuide,TechFaq,certificates,standards,guides · ⚑STUB |
| `env.d.ts` | 1 |  |
| `layouts/default.vue` | 55 | 组件:default · 根:div · 定义:isZh,focusMain |
| `layouts/marketing.vue` | 14 | 组件:marketing · 根:div |
| `layouts/tenant-blank.vue` | 56 | 组件:tenant-blank · 根:div · 定义:booting |
| `main.ts` | 70 | 定义:i18n,app,pinia · 依赖:./App.vue,./composables/_nuxt-shims,./locales/ar-SA.json,./locales/de-DE.json,./locales/en-US.json · ⚑DEGRADED |
| `middleware/auth.global.ts` | 66 | 定义:PUBLIC_EXACT,PUBLIC_PREFIXES,STATIC_PREFIXES,isPublicPath,token |
| `middleware/error-handler.global.ts` | 9 |  |
| `middleware/geo-routing.ts` | 22 | 定义:countryCode,langMap,htmlLang |
| `middleware/tenant.global.ts` | 91 | 定义:MAIN_SITE_PATTERNS,normalizeHost,isMainSiteHost,escaped,dynamic,resolveRequestHost,headers,raw · 依赖:../utils/tenant-preview-domain · ⚑STUB |
| `pages/[lang]/index.vue` | 170 | 组件:index · 根:div · 定义:route,router,products,buyerCountry,showForm,form,imLink,fetchProducts · ⚑MOCK |
| `pages/[lang]/product/[id].vue` | 209 | 组件:[id] · 根:div · 定义:route,router,product,imChannels,sanitizedDescription,buyerCountry,showForm,form · ⚑MOCK |
| `pages/about.vue` | 291 | 组件:about · 根:div · 定义:stats,milestones,msg,certifications |
| `pages/calculator.vue` | 440 | 组件:calculator · 定义:SURFACE_R,CalcMode,mode,modes,modeKey,markCalcStart,setMode,trackComplete · ⚑MOCK |
| `pages/calculators.vue` | 143 | 组件:calculators · 根:div · 定义:api,activeTab,loading,thermal,fire,quantity,thermalResult,fireResult |
| `pages/cases/[slug].vue` | 365 | 组件:[slug] · 根:div · 定义:route,caseStore,contactPhone,caseItem,loading,error,relatedCases,quoteLink · ⚑DEGRADED |
| `pages/cases/index.vue` | 316 | 组件:index · 根:div · 定义:caseStore,contactPhone,selectedFilter,searchQuery,currentPage,pageSize,loading,filters · ⚑MOCK |
| `pages/certifications.vue` | 129 | 组件:certifications · 定义:groups,activeGroup,CertEntry,certs,visibleCerts |
| `pages/compare.vue` | 113 | 组件:compare · 定义:pickField |
| `pages/contact.vue` | 541 | 组件:contact · 根:div · 定义:contactInfo,items,form,formErrors,submitting,submitSuccess,submitError,validateForm · ⚑MOCK/DEGRADED |
| `pages/distributor.vue` | 132 | 组件:distributor |
| `pages/error.vue` | 64 | 组件:error · 根:div · props · 定义:props,goHome,reloadPage |
| `pages/factory.vue` | 144 | 组件:factory · 定义:statItems,sectionItems,labItems |
| `pages/finder.vue` | 309 | 组件:finder · 定义:FinderField,FinderOption,FinderAnswers,FinderRank,productStore,stepIndex,answers,finished |
| `pages/index.vue` | 559 | 组件:index · 根:div · 定义:trustBadges,stats,hotProducts,zh,solutions,applications,standards,cases · ⚑MOCK/STUB |
| `pages/industries/index.vue` | 198 | 组件:index · 根:div · 定义:IndustryEntry,router,industries,goToIndustry,goToCases · ⚑STUB |
| `pages/industry/[tenantSlug]/[contentId].vue` | 142 | 组件:[contentId] · 根:div · 定义:HubPageData,HubApiResponse,route,config,tenantSlug,contentId,tenantLabel,hubUrl |
| `pages/industry/[tenantSlug]/index.vue` | 76 | 组件:index · 根:div · 定义:route,config,tenantSlug,tenantLabel,hasTenantUrl,tenantSiteUrl,fromQuery,hubIntro |
| `pages/inquiries/index.vue` | 230 | 组件:index · 根:div · 定义:route,router,product,submitting,form,fetchProduct,response,data · ⚑MOCK |
| `pages/leads.vue` | 174 | 组件:leads · 根:div · 定义:Lead,Summary,fallbackSummary,allLeads,limit,hasMore,loadingMore,refreshing · ⚑DEGRADED |
| `pages/logistics/index.vue` | 287 | 组件:index · 根:div · 定义:trackingNumber,carrier,trackingResult,trackingLoading,trackingError,trackLogistics,params,url · ⚑MOCK |
| `pages/markets/[slug].vue` | 238 | 组件:[slug] · 定义:route,productStore,slug,market,solutions,pick · ⚑DEGRADED |
| `pages/markets/index.vue` | 80 | 组件:index · 定义:pickMarket |
| `pages/mobile/about.vue` | 195 | 组件:about · 根:div · 定义:advantages,contactItems |
| `pages/mobile/cases.vue` | 150 | 组件:cases · 根:div · 定义:caseList · ⚑MOCK |
| `pages/mobile/cases/[slug].vue` | 158 | 组件:[slug] · 根:div · 定义:route,caseStore,contactPhone,caseItem,loading,error · ⚑DEGRADED |
| `pages/mobile/contact.vue` | 243 | 组件:contact · 根:div · 定义:contactInfo,form,formErrors,submitting,submitSuccess,submitError,copied,validateForm · ⚑MOCK/DEGRADED |
| `pages/mobile/index.vue` | 395 | 组件:index · 根:div · 定义:isSearchOpen,searchQuery,categories,products,cases,hotKeywords,toggleSearch,handleSearch · ⚑MOCK |
| `pages/mobile/inquiries/index.vue` | 115 | 组件:index · 根:div · 定义:InquiryItem |
| `pages/mobile/leads.vue` | 193 | 组件:leads · 根:div · 定义:Lead,router,activeFilter,filterTabs,filteredLeads,showAddModal,newLead,addLead |
| `pages/mobile/logistics/index.vue` | 182 | 组件:index · 根:div · 定义:TrackingEvent,TrackingResult,router,trackingNumber,trackingResult,trackingSearched,pending,trackOrder · ⚑MOCK |
| `pages/mobile/news.vue` | 218 | 组件:news · 根:div · 定义:selectedCategory,categories,newsList,filteredNews,tagClass,map |
| `pages/mobile/news/[slug].vue` | 135 | 组件:[slug] · 根:div · 定义:route,newsStore,newsItem,loading,error,sanitizedContent,formatDate,date · ⚑DEGRADED |
| `pages/mobile/orders/[id].vue` | 305 | 组件:[id] · 根:div · 定义:OrderDetail,route,router,orderStatusTimeline,statuses,statusOrder,currentIdx,getStatusText · ⚑MOCK |
| `pages/mobile/orders/index.vue` | 118 | 组件:index · 根:div · 定义:route,router · ⚑MOCK |
| `pages/mobile/payment/callback.vue` | 114 | 组件:callback · 根:div · 定义:route,status,verifying,result,retryPayment |
| `pages/mobile/products.vue` | 182 | 组件:products · 根:div · 定义:productStore,selectedCategory,searchQuery,isSearchOpen,loading,categories,products,query · ⚑MOCK |
| `pages/mobile/products/[id].vue` | 167 | 组件:[id] · 根:div · 定义:ProductDetail,route,router,selectedImageIndex,openInquiry,openQuote |
| `pages/mobile/products/[id]/reviews.vue` | 512 | 组件:reviews · 根:div · 定义:route,router,Review,reviews,totalReviews,averageRating,ratingDistribution,currentPage · ⚑MOCK |
| `pages/mobile/user/address.vue` | 384 | 组件:address · 根:div · 定义:router,addresses,loading,error,showForm,isEditing,saving,editingId · ⚑MOCK |
| `pages/mobile/user/favorites.vue` | 161 | 组件:favorites · 根:div · 定义:router,favorites,loading,error,fetchFavorites,response,data,removeFavorite · ⚑MOCK |
| `pages/mobile/user/index.vue` | 119 | 组件:index · 根:div · 定义:router,menuItems,logout |
| `pages/mobile/user/notifications.vue` | 155 | 组件:notifications · 根:div · 定义:notificationStore,notifications,loading,error,fetchNotifications,markAllRead,openNotification,getNotificationIcon |
| `pages/mobile/user/orders.vue` | 121 | 组件:orders · 根:div · 定义:router · ⚑MOCK |
| `pages/mobile/user/settings.vue` | 254 | 组件:settings · 根:div · 定义:router,currentLocale,profileForm,profileUpdating,passwordForm,passwordUpdating,languages,user |
| `pages/news/[slug].vue` | 374 | 组件:[slug] · 根:div · 定义:route,newsStore,contactPhone,article,loading,error,sanitizedContent,relatedArticles · ⚑DEGRADED |
| `pages/news/index.vue` | 283 | 组件:index · 根:div · 定义:newsStore,contactPhone,selectedCategory,loading,categories,categoryLabels,categoryIcons,filteredArticles |
| `pages/oem.vue` | 132 | 组件:oem |
| `pages/orders/[id].vue` | 418 | 组件:[id] · 根:div · 定义:route,router,order,loading,error,orderStatusTimeline,statuses,statusOrder · ⚑MOCK |
| `pages/orders/index.vue` | 401 | 组件:index · 根:div · 定义:OrderStatus,OrderItem,Order,orders,loading,selectedStatus,showDetail,selectedOrder · ⚑MOCK |
| `pages/payment/callback.vue` | 276 | 组件:callback · 根:div · 定义:route,router,verifying,paymentStatus,order,orderId,paymentTime,errorMessage |
| `pages/platform/index.vue` | 868 | 组件:index · 根:div · 定义:PlanId,PlanColumnKey,copy,mock,navLinks,trustProof,integrations,pricingMatrix · ⚑MOCK |
| `pages/privacy.vue` | 166 | 组件:privacy · 根:div |
| `pages/procurement.vue` | 360 | 组件:procurement · 根:div · 定义:appStore,organizationSchemaZh,organizationSchemaEn,webSiteSchema,faqPageSchema,formData,errors,isSubmitting |
| `pages/products/[id].vue` | 360 | 组件:[id] · 根:div · 定义:route,product,relatedProducts,merchantIM,loading,error,quoteLink,heroImage · ⚑MOCK/DEGRADED |
| `pages/products/[id]/reviews.vue` | 546 | 组件:reviews · 根:div · 定义:route,router,loading,error,productId,productName,reviews,totalReviews · ⚑MOCK |
| `pages/products/[slug].vue` | 942 | 组件:[slug] · 根:div · 定义:route,productStore,product,loading,error,contactPhone,faqs,caseStudies · ⚑MOCK |
| `pages/products/index.vue` | 429 | 组件:index · 根:div · 定义:productStore,contactPhone,selectedCategory,searchQuery,currentPage,pageSize,loading,categories · ⚑MOCK |
| `pages/projects/index.vue` | 254 | 组件:index · 根:div · 定义:ProjectEntry,router,filterType,filterRegion,filterProduct,typeOptions,regionOptions,productOptions · ⚑MOCK/STUB |
| `pages/publish/[id].vue` | 178 | 组件:[id] · 根:div · 定义:router,route,task,pending,statusClass,map,formatDate,fetchTask |
| `pages/publish/create.vue` | 174 | 组件:create · 根:div · 定义:router,platforms,selectedPlatform,pending,form,fetchPlatforms,api,data · ⚑MOCK |
| `pages/publish/index.vue` | 139 | 组件:index · 根:div · 定义:router,tasks,activeFilter,pending,filterTabs,filteredTasks,statusClass,map |
| `pages/quality.vue` | 111 | 组件:quality · 定义:steps |
| `pages/quote.vue` | 561 | 组件:quote · 根:div · 定义:route,salesPhone,productId,docParam,materialParam,finderParam,calculatorParam,programParam · ⚑MOCK/STUB |
| `pages/request-quote.vue` | 388 | 组件:request-quote · 根:div · 定义:RFQItem,RFQRequirement,api,form,loading,apiError,success,onSubmit · ⚑MOCK |
| `pages/resources/index.vue` | 227 | 组件:index · 根:div · 定义:ResourceEntry,searchQuery,filterCategory,filterFormat,categoryOptions,formatOptions,categoryMap,categoryLabel · ⚑MOCK |
| `pages/solutions/[slug].vue` | 359 | 组件:[slug] · 定义:route,productStore,slug,solution,recommendedProducts,slugs,productSpecs,zh |
| `pages/solutions/index.vue` | 97 | 组件:index |
| `pages/standards/index.vue` | 248 | 组件:index · 根:div · 定义:StandardStatus,StandardEntry,filterType,filterRegion,filterIndustry,typeOptions,regionOptions,industryOptions · ⚑MOCK |
| `pages/technical.vue` | 380 | 组件:technical · 定义:productStore,searchQuery,TechHitType,TechHit,HIT_ORDER,searchHits,q,hits · ⚑MOCK |
| `pages/tenant/about.vue` | 7 | 组件:about · 根:TenantSiteGateway |
| `pages/tenant/contact.vue` | 7 | 组件:contact · 根:TenantSiteGateway |
| `pages/tenant/downloads.vue` | 7 | 组件:downloads · 根:TenantSiteGateway |
| `pages/tenant/index.vue` | 7 | 组件:index · 根:TenantSiteGateway |
| `pages/tenant/products/[slug].vue` | 14 | 组件:[slug] · 根:TenantLProProductDetail · 依赖:../../../components/tenant/premium/TenantLProProductDetail.vue,../../../composables/useTenantSiteBootstrap |
| `pages/tenant/products/index.vue` | 7 | 组件:index · 根:TenantSiteGateway |
| `pages/tenant/solutions.vue` | 7 | 组件:solutions · 根:TenantSiteGateway |
| `pages/terms.vue` | 199 | 组件:terms · 根:div |
| `pages/test.vue` | 10 | 组件:test · 根:div |
| `pages/user/address.vue` | 402 | 组件:address · 根:div · 定义:addresses,loading,showDialog,isEditing,saving,editingId,addressForm,fetchAddresses · ⚑MOCK |
| `pages/user/favorites.vue` | 252 | 组件:favorites · 根:div · 定义:router,favorites,loading,currentPage,pageSize,total,totalPages,displayedPages · ⚑MOCK |
| `pages/user/index.vue` | 262 | 组件:index · 根:div · 定义:router,user,activeTab,profileForm,userOrders,userInquiries,navItems,fetchUser |
| `pages/user/notifications.vue` | 419 | 组件:notifications · 根:div · 定义:notifications,loading,currentPage,pageSize,total,stats,activeFilter,filters |
| `pages/user/orders.vue` | 302 | 组件:orders · 根:div · 定义:router,orders,loading,currentPage,pageSize,total,activeStatus,statusFilters · ⚑MOCK |
| `pages/user/settings.vue` | 447 | 组件:settings · 根:div · 定义:api,successMessage,errorMessage,profileLoading,passwordLoading,languageLoading,notifLoading,avatarInput · ⚑MOCK |
| `prettier.config.js` | 25 |  |
| `public/service-worker.js` | 552 | 定义:CACHE_VERSION,STATIC_CACHE,DYNAMIC_CACHE,API_CACHE,IMAGE_CACHE,FONT_CACHE,ALL_CACHES,PRECACHE_ASSETS · ⚑STUB/DEGRADED |
| `public/sw.js` | 139 | 定义:CACHE_NAME,STATIC_CACHE,DYNAMIC_CACHE,STATIC_ASSETS,API_CACHE,url,responseClone,responseClone |
| `router/index.ts` | 78 | 定义:routes,router,el,y · 依赖:../layouts/default.vue |
| `shared/auth-helpers.ts` | 59 | 定义:KNOWN_JWT_ROLES,decodeJwtPayload,parts,base64,padded,json,jwtRoleFromPayload,scopes |
| `shared/geo.ts` | 58 | 定义:GeoResult,COUNTRY_TO_LANG,COUNTRY_TO_IM,getLanguageByCountry,getImToolsByCountry,getWhatsAppLink,cleanPhone,getTelegramLink |
| `shared/index.ts` | 4 | 依赖:./auth-helpers,./geo |
| `stores/aiConfig.ts` | 93 | 定义:AIProvider,AIQuota,AIConfigData,useAiConfigStore,provider |
| `stores/analytics.ts` | 79 | 定义:AnalyticsData,useAnalyticsStore,response,response,result |
| `stores/app.ts` | 80 | 定义:useAppStore,globalLoading,loadingCount,startLoading,stopLoading,toasts,showToast,id |
| `stores/auth.ts` | 67 | 定义:useAuthStore,res,accessToken,savedToken,cookies |
| `stores/case.ts` | 105 | 定义:CaseStudy,useCaseStore,response |
| `stores/inquiry.ts` | 100 | 定义:Inquiry,useInquiryStore,response |
| `stores/leads.ts` | 56 | 定义:LeadDraft,useLeadsStore,draft,saveDraft,clearDraft,lastSubmittedId,lastSubmittedPrice,recordSubmission |
| `stores/news.ts` | 108 | 定义:News,useNewsStore,response |
| `stores/notification.ts` | 76 | 定义:Notification,useNotificationStore,api,notifications,unreadCount,loading,error,fetchNotifications |
| `stores/product.ts` | 127 | 定义:ProductCategory,Product,useProductStore,map,res,res,unwrap,r |
| `stores/seo.ts` | 96 | 定义:SEOData,useSeoStore,response,result,result |
| `stores/settings.ts` | 91 | 定义:SettingsData,useSettingsStore |
| `stores/system.ts` | 107 | 定义:SystemInfo,SystemStats,useSystemStore,response |
| `tailwind.config.ts` | 191 |  |
| `tests/stores/app.test.ts` | 37 | 定义:store,store,keys |
| `tests/stores/auth.test.ts` | 101 | 定义:mockRequest,mockSetAuthToken,mockGetAuthToken,store,store,store,store · ⚑MOCK |
| `types/index.ts` | 153 | 定义:Product,ProductCategory,Case,News,Inquiry,User,SeoConfig,ApiResponse |
| `types/nuxt-compat.d.ts` | 174 | 定义:ref,ref,reactive,computed,watch,watchEffect,toRef,toRefs |
| `utils/contact-inquiry-cta.ts` | 52 | 定义:ContactInquiryQuery,slugifyClickLabel,s,buildContactInquiryPath,params,product,sku,last · ⚑DEGRADED |
| `utils/geo.ts` | 32 | 定义:detectBuyerCountry,cached,res,data,code · ⚑DEGRADED |
| `utils/l-pro-publish-gate.ts` | 178 | 定义:LProPublishIssue,LProPublishGate,L_PRO_TEMPLATE_ID,MIN_PRODUCTS,MIN_SPECS,productItems,pages,products |
| `utils/localeOverlayPick.ts` | 30 | 定义:overlayArrayField,overlayVal,lang,baseVal,overlayStringField,lang |
| `utils/regions.ts` | 148 | 定义:City,Province,regions |
| `utils/submitPublicInquiry.ts` | 40 | 定义:PublicInquiryPayload,submitPublicInquiry,body,res,result |
| `utils/tenant-preview-domain.ts` | 71 | 定义:readTenantFromQueryRecord,direct,first,domain,readTenantFromSearch,m,resolveTenantPreviewDomain,resolveDevTenantPreviewHost |
| `utils/tenant-product-slug.ts` | 92 | 定义:TenantCatalogProduct,slugifyTenantSegment,base,productSlug,categorySlug,normalizeCatalogProducts,items,o |
| `utils/tenant-seo-url.ts` | 89 | 定义:TENANT_SEO_HREFLANG_LOCALES,TenantSeoPrimaryMarket,TENANT_SEO_WEBMASTER_HINTS,PRESERVED_QUERY_KEYS,preservedTenantPreviewQuery,out,raw,buildTenantLanguagePath |
| `utils/tenant-site-i18n.ts` | 54 | 定义:mergeSiteI18nBlock,out,i18n,overlay,localizedSiteString,fromOverlay,root,pages · ⚑DEGRADED |
| `utils/tradeKnowledgeLocale.ts` | 84 | 定义:EN_TOPIC_TITLES,EN_FAQ_QUESTIONS,ZH_TOPICS,ZH_FAQS,looksLikeEnTopics,titles,hits,looksLikeEnFaqs |
| `utils/visitorContextCache.ts` | 59 | 定义:CACHE_TTL_MS,CachedPayload,visitorContextCacheKey,lang,readRaw,raw,parsed,wrapped · 依赖:../composables/useVisitorLocale |
| `utils/visitorContextFetch.ts` | 76 | 定义:VisitorContextFetchResult,TIMEOUT_MS,MAX_RETRIES,cancelVisitorContextFetch,fetchVisitorContextPayload,controller,timeout,res |
| `vite.config.ts` | 72 |  |
| `youding-admin-kit/components/YdSearchBar.vue` | 42 | 组件:YdSearchBar · 根:div · emits |
| `youding-admin-kit/components/YdStatsCard.vue` | 58 | 组件:YdStatsCard · 根:div · props · 定义:props,displayValue |
| `youding-admin-kit/composables/useYoudingColumnLayout.ts` | 115 | 定义:loadColumnOrder,defaults,raw,saved,valid,missing,loadHiddenKeys,raw · 依赖:./useYoudingTable |
| `youding-admin-kit/composables/useYoudingTable.ts` | 143 | 定义:YoudingTableFetcher,YoudingTableColumn,UseYoudingTableOptions,useYoudingTable,loading,items,total,page · 依赖:./useYoudingColumnLayout · ⚑STUB |
| `youding-admin-kit/env.d.ts` | 1 |  |
| `youding-admin-kit/types/uac.d.ts` | 76 | 定义:AdminShell,UacAuthMark,UacRouteMeta,UacMenuRoute,UacUserInfo,UacPermissionBundle,UacLoginResult,UacTableQuery |