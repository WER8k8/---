# P0-5 前端 UTM 透传补丁（需在独立 frontend 仓库应用）

> 本后端 worktree（`backend/`）不含 `frontend/` 目录，公开的 `submitPublicInquiry.ts`
> 位于独立的前端仓库（UJ 前端，Vue3/Nuxt3）。后端侧（`PublicInquiryCreate` 已含
> `utm_source/medium/campaign/content/term`，`attach_utm_to_inquiry` 已回写独立 UTM 列）
> 已就绪。此补丁让前端把 UTM 真正发出去，否则归因仍只能靠落地页 URL 解析。

## 目标文件
`frontend/utils/submitPublicInquiry.ts`

## 改动 1 — 扩展 Payload 接口
```ts
// 修改前
export interface PublicInquiryPayload {
  name: string
  email?: string
  phone?: string
  message: string
  product?: string
  source_channel?: string
  landing_path?: string
  session_id?: string
}

// 修改后
export interface PublicInquiryPayload {
  name: string
  email?: string
  phone?: string
  message: string
  product?: string
  source_channel?: string
  landing_path?: string
  session_id?: string
  // P0-5: 透传 UTM，供后端独立列归因
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  utm_content?: string
  utm_term?: string
}
```

## 改动 2 — 提交时填充 UTM（从落地页 URL 解析）
在构造 `payload` 处，追加：

```ts
function pickUtmFromUrl(): Record<string, string> {
  const params = new URLSearchParams(window.location.search)
  const out: Record<string, string> = {}
  for (const k of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']) {
    const v = params.get(k)
    if (v) out[k] = v
  }
  return out
}

const utm = pickUtmFromUrl()
const payload: PublicInquiryPayload = {
  name,
  email,
  phone,
  message,
  product,
  source_channel: sourceChannel,
  landing_path: window.location.pathname,
  session_id: sessionId,
  utm_source: utm.utm_source,
  utm_medium: utm.utm_medium,
  utm_campaign: utm.utm_campaign,
  utm_content: utm.utm_content,
  utm_term: utm.utm_term,
}
```

## 改动 3 — 若前端已维护全局 UTM（如矩阵投放 SDK 写入 sessionStorage），优先取之
```ts
function pickUtm(): Record<string, string> {
  const stored = JSON.parse(sessionStorage.getItem('uj_utm') || '{}')
  return { ...pickUtmFromUrl(), ...stored } // URL 优先，缺失项用 stored 兜底
}
```
并将改动 2 中的 `pickUtmFromUrl()` 替换为 `pickUtm()`。

## 验证
- 发布带 `?utm_source=linkedin&utm_campaign=b2b_q4` 的落地页，提交询盘后：
  `GET /inquiries` 返回该行 `utm_source/utm_campaign` 非空，且 `attribution_channel='social'`。
- 后端单测可加：构造 `PublicInquiryCreate(utm_source='google', ...)`，断言落库
  `inquiry.utm_source=='google'` 且 `attribution_channel=='seo'`。
