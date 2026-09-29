# Cloudflare Workers

> 根目录：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\workers` · **5 个文件** · Cloudflare Workers（爬取/提取/传输）

| 文件 | 行 | 摘要 · 符号 · 标记 |
|---|---:|---|
| `workers/crawler.ts` | 334 | 定义:CrawlResult,CrawlOptions,USER_AGENTS,REGION_LANGUAGE_MAP,REGION_ACCEPT_MAP,getRandomUserAgent,getProxyEndpoint,extractTitle |
| `workers/extractor.ts` | 490 | 定义:ExtractedEmail,ExtractedPhone,ExtractedUrl,FormField,InquiryParagraph,InquiryInfo,BUILDING_MATERIALS_KEYWORDS,INQUIRY_KEYWORDS · ⚑MOCK/STUB |
| `workers/src/index.ts` | 219 | 定义:Env,generateInquiryId,urlHash,timestamp,random,CrawlRequest,CrawlResponse,body · 依赖:../crawler,../extractor,../transmitter |
| `workers/test/test.js` | 188 | 定义:$,GREEN,pass,fail,info,detail,TEST_URLS,REGION · 依赖:../crawler.ts,../extractor.ts,../transmitter.ts |
| `workers/transmitter.ts` | 307 | 定义:TransmitPayload,TransmitResult,generateNonce,bytes,strToBytes,bytesToHex,hexToBytes,bytes |